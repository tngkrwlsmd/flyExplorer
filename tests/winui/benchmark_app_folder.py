"""PX13 owned WinUI/UIA latency samples, not pixel or whole-product acceptance.

The 8k case always follows the same 200-file lifecycle preflight. Timings include
UIA observation overhead and uncontrolled OS caches; no cold-cache claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import threading
import time

from paths import ROOT, app_exe
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(owned, count, exe, report):
    import ctypes as c
    from ctypes import wintypes as w
    import psutil
    from pywinauto import Desktop
    from uia_polling import wait_until

    folder = owned / "files"
    quick = owned / "quick"
    folder.mkdir()
    quick.mkdir()
    payload = b"owned-px13\n"
    for n in range(count):
        (folder / f"bench-{n:05d}.txt").write_bytes(payload)
    (quick / "survivor.txt").write_bytes(payload)
    env = {k: v for k, v in os.environ.items() if not k.startswith("FLY")}
    for key in ("APPDATA", "LOCALAPPDATA", "USERPROFILE", "TEMP", "TMP"):
        location = owned / key.lower()
        location.mkdir()
        env[key] = str(location)
    user = c.windll.user32
    user.GetForegroundWindow.restype = w.HWND
    user.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
    user.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
    stop = threading.Event()
    samples = []
    app = None
    hwnd = None
    sampler = None
    completed = False

    def owner():
        pid = w.DWORD()
        user.GetWindowThreadProcessId(hwnd, c.byref(pid))
        return pid.value

    def wait(fn, label, seconds=30):
        return wait_until(fn, label, seconds=seconds, interval=.1)

    started = time.perf_counter()
    try:
        app = subprocess.Popen([str(exe), str(folder)], cwd=exe.parent, env=env,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
        process = psutil.Process(app.pid)

        def memory():
            while not stop.is_set():
                try:
                    info = process.memory_info()
                    samples.append((info.rss, info.pagefile))
                except psutil.NoSuchProcess:
                    break
                stop.wait(.05)

        sampler = threading.Thread(target=memory, daemon=True)
        sampler.start()

        def window():
            nonlocal hwnd
            assert app.poll() is None, "owned app exited before measurement"
            found = [v for v in Desktop(backend="uia").windows(process=app.pid)
                     if "flyExplorer" in v.window_text()]
            if len(found) != 1:
                return None
            hwnd = found[0].handle
            assert owner() == app.pid
            assert Path(process.exe()).resolve() == exe.resolve()
            return Desktop(backend="uia").window(handle=hwnd)

        win = wait(window, "owned window unavailable")
        element = lambda name: win.child_window(auto_id=name)

        def first():
            rows = element("LeftFiles").descendants(control_type="ListItem")
            return rows[0].window_text() if rows else ""

        wait(lambda: "bench-00000.txt" in first(), "first row unavailable", 45)
        report["launch_to_first_uia_row_ms"] = round((time.perf_counter()-started)*1000, 3)
        report["window_pixels"] = [win.rectangle().width(), win.rectangle().height()]
        report["dpi"] = user.GetDpiForWindow(w.HWND(hwnd))
        report["rss_first_mib"] = round(process.memory_info().rss/1048576, 3)
        win.set_focus()
        assert owner() == app.pid and user.GetForegroundWindow() == hwnd

        # UIA Scroll observes an actual list viewport movement, not page loading.
        scroll = element("LeftFiles").iface_scroll
        before = scroll.CurrentVerticalScrollPercent
        t = time.perf_counter()
        scroll.Scroll(2, 3)  # NoAmount horizontally; LargeIncrement vertically.
        wait(lambda: scroll.CurrentVerticalScrollPercent > before,
             "list viewport did not scroll", 5)
        report["scroll_to_observed_offset_ms"] = round((time.perf_counter()-t)*1000, 3)
        scroll.SetScrollPercent(-1, 0)

        t = time.perf_counter()
        element("SortPicker").select(1)
        wait(lambda: f"bench-{count-1:05d}.txt" in first(), "global sort did not settle", 60)
        report["descending_sort_to_first_uia_row_ms"] = round((time.perf_counter()-t)*1000, 3)
        report["rss_after_sort_mib"] = round(process.memory_info().rss/1048576, 3)

        if count > 1024:
            # Cancel means supersede folder loading by navigating elsewhere.
            # This is separate from the already-accepted PX06 search Cancel.
            element("SortPicker").select(0)
            wait(lambda: "bench-00000.txt" in first(), "ascending state unavailable")
            address = element("AddressBox")
            address.set_edit_text(str(quick))
            address.type_keys("{ENTER}")
            wait(lambda: "survivor.txt" in first(), "quick folder unavailable")
            address.set_edit_text(str(folder))
            address.type_keys("{ENTER}")
            wait(lambda: "bench-00000.txt" in first() and
                 element("AddressBox").get_value().casefold() == str(folder).casefold(),
                 "fresh initial page unavailable")
            element("SortPicker").select(1)
            busy = "불러오는 중" in element("StatusText").window_text() or (
                "완성하는 중" in element("StatusText").window_text())
            report["supersede_while_busy_observed"] = busy
            if busy:
                t = time.perf_counter()
                address = element("AddressBox")
                address.set_edit_text(str(quick))
                address.type_keys("{ENTER}")
                wait(lambda: "survivor.txt" in first() and
                     element("AddressBox").get_value().casefold() == str(quick).casefold(),
                     "superseding navigation did not settle")
                report["supersede_to_new_folder_ms"] = round((time.perf_counter()-t)*1000, 3)
                time.sleep(1)
                assert "survivor.txt" in first(), "stale rows replaced new folder"
        assert len(list(folder.iterdir())) == count
        assert all(p.read_bytes() == payload for p in folder.iterdir())
        assert (quick / "survivor.txt").read_bytes() == payload
        report["owned_files_preserved"] = True
        completed = True
    finally:
        if app is not None and app.poll() is None:
            if hwnd and owner() == app.pid:
                user.PostMessageW(hwnd, 0x10, 0, 0)
                try:
                    app.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    app.terminate()
                    app.wait(timeout=6)
            else:
                app.terminate()
                app.wait(timeout=6)
        stop.set()
        if sampler:
            sampler.join(timeout=2)
        report["normal_exit"] = app is not None and app.returncode == 0
        report["memory_sample_count"] = len(samples)
        report["sampled_app_peak_rss_mib"] = round(max((s[0] for s in samples), default=0)/1048576, 3)
        report["sampled_app_peak_private_commit_mib"] = round(max((s[1] for s in samples), default=0)/1048576, 3)
        report["memory_scope"] = "main app only; 50ms samples; helper memory excluded"
    assert completed and report["normal_exit"], "benchmark or normal exit failed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, choices=(200, 8000), default=200)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("interactive Windows VM required")
    exe = app_exe("Release")
    assert exe.is_file()
    import ctypes
    assert ctypes.windll.kernel32.GetDriveTypeW(str(ROOT.resolve().anchor)) == 3
    base = ROOT / "logs" / "px13-app-benchmark"
    base.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="owned-", dir=base)).resolve()
    legacy_root, legacy = snapshot_legacy_profile()
    report = {
        "status": "FAIL", "scope": "WinUI UIA observed latency; not final pixels",
        "source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "benchmark_sha256": digest(Path(__file__)), "exe_sha256": digest(exe),
        "helper_sha256": digest(exe.parent / "FlyShellIsolationHelper.exe"),
        "configuration": "Release", "platform": platform.platform(),
        "cache": "uncontrolled OS caches; not guaranteed cold", "cases": [],
    }
    output = base / ("benchmark-" + str(time.time_ns()) + ".json")
    try:
        for count in ([200] if args.items == 200 else [200, args.items]):
            case_root = owned / str(count)
            case_root.mkdir()
            case = {"items": count}
            report["cases"].append(case)
            run_case(case_root, count, exe, case)
        assert_legacy_profile_unchanged(legacy_root, legacy)
        report["legacy_profile_unchanged"] = True
        assert owned.parent == base.resolve() and not owned.is_symlink()
        shutil.rmtree(owned)
        report["owned_fixture_profiles_removed"] = True
        report["status"] = "PASS"
    finally:
        assert_legacy_profile_unchanged(legacy_root, legacy)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"report": str(output), **report}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
