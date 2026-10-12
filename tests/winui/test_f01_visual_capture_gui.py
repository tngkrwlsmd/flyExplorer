"""Owned BEFORE(main) / AFTER(F01) actual WinUI view-menu pixel captures.

Capture only the launched test-owned flyExplorer HWND, never the whole desktop.
Functional UIA assertions here do not replace human/agent image inspection.
The two Release runtimes MUST be built separately with exact pinned revisions.
"""
from __future__ import annotations

import argparse
import ctypes as ct
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

if os.name != "nt":
    raise SystemExit("Windows interactive WinUI desktop is required")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--theme", choices=("light", "dark"), required=True)
    args = parser.parse_args()
    root = args.source.resolve(strict=True)
    output = args.output.resolve(strict=True)
    assert root.is_dir() and output.is_dir()
    assert len(args.source_sha) == 40 and all(c in "0123456789abcdef" for c in args.source_sha)
    assert (root / "app/winui/MainWindow.xaml").is_file()
    sys.path.insert(0, str(root / "tests/winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop
    from PIL import ImageGrab

    executable = app_exe("Release")
    assert executable.is_file(), executable
    actual_sha = subprocess.check_output(
        ["git", "-c", "safe.directory=" + str(root), "-C", str(root), "rev-parse", "HEAD"],
        text=True).strip()
    assert actual_sha == args.source_sha, (actual_sha, args.source_sha)

    legacy_location, legacy_profile = snapshot_legacy_profile()
    owned = Path(tempfile.mkdtemp(prefix="f01-visual-owned-", dir=output))
    for name in ("Left", "appdata", "localdata", "temp"):
        (owned / name).mkdir()
    for name in ("readme.txt", "report.tar.gz", "한글.문서", ".gitignore"):
        (owned / "Left" / name).write_text("synthetic F01 only", encoding="utf-8")
    preferences = owned / "localdata" / "flyExplorer"
    preferences.mkdir()
    (preferences / "ui-preferences-v1.txt").write_bytes(
        ("schema=2\r\nlanguage=ko-KR\r\ntheme=" + args.theme +
         "\r\nview=details\r\n").encode("utf-8"))

    user = ct.windll.user32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ct.POINTER(wintypes.DWORD)]
    user.GetDpiForWindow.argtypes = [wintypes.HWND]
    user.GetDpiForWindow.restype = wintypes.UINT
    user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ct.c_int,
                                  ct.c_int, ct.c_int, ct.c_int, wintypes.UINT]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ct.c_int]
    enumeration = ct.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [enumeration, wintypes.LPARAM]

    def windows_of(pid):
        found = []
        @enumeration
        def visit(hwnd, unused):
            owner = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ct.byref(owner))
            if owner.value == pid and user.IsWindowVisible(hwnd):
                buff = ct.create_unicode_buffer(256)
                user.GetWindowTextW(hwnd, buff, len(buff))
                if "flyExplorer" in buff.value:
                    found.append(hwnd)
            return True
        user.EnumWindows(visit, 0)
        return found

    process = None
    hwnd = None
    finished = False
    try:
        env = dict(os.environ)
        env.update(APPDATA=str(owned / "appdata"),
                   LOCALAPPDATA=str(owned / "localdata"),
                   TEMP=str(owned / "temp"), TMP=str(owned / "temp"))
        process = subprocess.Popen(
            [str(executable), str(owned / "Left")], cwd=executable.parent,
            env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_until(lambda: len(windows_of(process.pid)) == 1 or process.poll() is not None,
                   "test-owned F01 app window missing", seconds=24, interval=.15)
        assert process.poll() is None, ("owned app startup failed", process.returncode)
        hwnd = windows_of(process.pid)[0]
        win = Desktop(backend="uia").window(handle=hwnd)

        def focus():
            for _ in range(5):
                win.set_focus()
                time.sleep(.12)
                owner = wintypes.DWORD()
                foreground = user.GetForegroundWindow()
                if foreground:
                    user.GetWindowThreadProcessId(foreground, ct.byref(owner))
                if foreground and owner.value == process.pid:
                    return
            raise AssertionError("refuse input/screenshot: foreground not owned by test app")

        width = min(940, user.GetSystemMetrics(0)-75)
        height = min(610, user.GetSystemMetrics(1)-85)
        assert width >= 800 and height >= 550, (width, height)
        assert user.SetWindowPos(hwnd, None, 35, 35, width, height, 0x0014)
        wait_until(lambda: abs(win.rectangle().width()-width) <= 3 and
                   abs(win.rectangle().height()-height) <= 3,
                   "F01 window geometry did not stabilize", seconds=9, interval=.15)
        focus()

        def row():
            return next((r for r in win.child_window(auto_id="LeftFiles").descendants()
                         if r.element_info.control_type == "ListItem" and
                         "readme.txt" in r.window_text()), None)

        wait_until(lambda: row() is not None, "synthetic file row unavailable",
                   seconds=12, interval=.15)
        row().click_input()
        wait_until(lambda: row() is not None and row().is_selected(),
                   "synthetic row not selected", seconds=7, interval=.15)

        screen = Desktop(backend="uia")

        def choose(name, fragment):
            focus()
            win.child_window(auto_id="ViewButton").click_input()
            def find():
                own = win.child_window(auto_id=name)
                if own.exists(timeout=.1):
                    return own.wrapper_object()
                peers = [x for w in screen.windows(process=process.pid)
                         for x in w.descendants()
                         if x.element_info.automation_id == name]
                return peers[0] if len(peers) == 1 else None
            item = wait_until(find, "menu item not found " + name,
                              seconds=8, interval=.15)
            assert item.element_info.process_id == process.pid
            assert item.element_info.automation_id == name
            item.iface_toggle.Toggle()
            wait_until(lambda: fragment in win.child_window(auto_id="StatusText").window_text(),
                       "view command not delivered " + name, seconds=7, interval=.15)

        rect = win.rectangle()
        window_rect = (rect.left, rect.top, rect.right, rect.bottom)
        assert rect.left >= 0 and rect.top >= 0
        assert rect.right <= user.GetSystemMetrics(0)
        assert rect.bottom <= user.GetSystemMetrics(1)
        dpi = int(user.GetDpiForWindow(hwnd))
        assert dpi > 0
        states = {}

        def shot(state):
            focus()
            image = ImageGrab.grab(bbox=window_rect, include_layered_windows=True)
            assert image.size == (rect.width(), rect.height())
            name = f"f01-{args.theme}-{args.label}-{state}.png"
            image.save(output / name, "PNG", optimize=True)
            states[state] = {
                "file": name,
                "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
                "bytes": (output / name).stat().st_size,
                "rect": list(window_rect),
            }

        shot("default")
        if args.label == "after":
            choose("ViewCheckboxesItem", "선택 확인란")
            choose("ViewCompactRowsItem", "목록 간격")
            choose("ViewFileExtensionsItem", "파일 확장명")
            wait_until(lambda: row() is not None and row().is_selected() and
                       "실제 파일 이름: readme.txt" in row().window_text(),
                       "owned hidden extension/selection state absent",
                       seconds=9, interval=.15)
            shot("enabled")
            print("F01_VISUAL_ENABLED_UIA_FULLNAME=PASS", flush=True)
        focus()
        win.child_window(auto_id="ViewButton").click_input()
        # Capture menu while open, but verify the menu belongs to our process.
        wait_until(lambda: len([w for w in screen.windows(process=process.pid)
                                for x in w.descendants()
                                if x.element_info.automation_id == "ViewDetailsItem"]) >= 1,
                   "owned View menu not visible", seconds=7, interval=.15)
        # Refocusing can dismiss flyout; grab with a strict foreground owner check.
        owner = wintypes.DWORD()
        current = user.GetForegroundWindow()
        if current:
            user.GetWindowThreadProcessId(current, ct.byref(owner))
        assert current and owner.value == process.pid
        name = f"f01-{args.theme}-{args.label}-menu.png"
        menu_png = ImageGrab.grab(bbox=window_rect, include_layered_windows=True)
        menu_png.save(output / name, "PNG", optimize=True)
        states["menu"] = {
            "file": name,
            "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
            "bytes": (output / name).stat().st_size,
            "rect": list(window_rect),
        }

        assert process.poll() is None

        data = {
            "label": args.label, "theme": args.theme, "source_sha": args.source_sha,
            "configuration": "Release", "window_rect": list(window_rect),
            "dpi": dpi, "desktop": [user.GetSystemMetrics(0), user.GetSystemMetrics(1)],
            "fixture": "test-owned 4 synthetic names, left Details selected readme.txt",
            "states": states,
        }
        (output / f"f01-{args.theme}-{args.label}-metadata.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        finished = True
        print(f"F01_VISUAL_{args.theme.upper()}_{args.label.upper()}_CAPTURE=PASS",
              "DPI", dpi, "RECT", window_rect, flush=True)
    finally:
        if process is not None and process.poll() is None:
            if hwnd is not None:
                owner = wintypes.DWORD()
                user.GetWindowThreadProcessId(hwnd, ct.byref(owner))
                assert owner.value == process.pid
                assert user.PostMessageW(hwnd, 0x10, 0, 0)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                raise AssertionError("owned F01 visual app did not exit")
        if finished:
            assert process is not None and process.returncode == 0
        assert_legacy_profile_unchanged(legacy_location, legacy_profile)
        shutil.rmtree(owned)


if __name__ == "__main__":
    main()
