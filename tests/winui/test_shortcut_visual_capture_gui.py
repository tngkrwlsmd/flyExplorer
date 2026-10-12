"""Capture actual test-owned WinUI shortcut editor pixels for matched visual review.

This is NOT an assertion that visual appearance is acceptable. It saves
bounded actual app-window screenshots and structured capture metadata; a human
or reviewing agent must inspect matched BEFORE and AFTER pixels.
"""
import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes as W

if os.name != "nt":
    raise SystemExit("Actual WinUI visual capture requires Windows")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    root = args.source.resolve(strict=True)
    output = args.output_dir.resolve(strict=True)
    assert (root / "app/winui/MainWindow.xaml").is_file()
    assert len(args.expected_sha) == 40 and all(ch in "0123456789abcdef" for ch in args.expected_sha)

    sys.path.insert(0, str(root / "tests/winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop
    from PIL import ImageGrab

    exe = app_exe("Release")
    assert exe.is_file(), exe
    original_path, original_values = snapshot_legacy_profile()
    owned = Path(tempfile.mkdtemp(prefix="shortcut-visual-owned-", dir=output))
    for p in ("Left", "Right", "local", "appdata", "temp"):
        (owned / p).mkdir()
    (owned / "Left" / "visual-fixture-한글.txt").write_text("owned visual capture", encoding="utf-8")

    user = c.windll.user32
    user.GetForegroundWindow.restype = W.HWND
    user.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
    user.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, c.c_int]
    user.SetWindowPos.argtypes = [W.HWND, W.HWND, c.c_int, c.c_int, c.c_int, c.c_int, W.UINT]
    user.GetDpiForWindow.argtypes = [W.HWND]
    user.GetDpiForWindow.restype = W.UINT
    user.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    cb = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    user.EnumWindows.argtypes = [cb, W.LPARAM]

    def windows_of(pid):
        found = []
        @cb
        def collect(hwnd, _):
            owner = W.DWORD()
            user.GetWindowThreadProcessId(hwnd, c.byref(owner))
            if owner.value == pid and user.IsWindowVisible(hwnd):
                buff = c.create_unicode_buffer(400)
                user.GetWindowTextW(hwnd, buff, len(buff))
                if "flyExplorer" in buff.value:
                    found.append(hwnd)
            return True
        user.EnumWindows(collect, 0)
        return found

    def ensure_own_foreground(pid):
        hwnd = user.GetForegroundWindow()
        owner = W.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd, c.byref(owner))
        assert hwnd and owner.value == pid, "Refuse screenshot/physical input without app-owned foreground"

    process = None
    hwnd = None
    failed = False
    try:
        env = dict(os.environ)
        env.update(APPDATA=str(owned / "appdata"), LOCALAPPDATA=str(owned / "local"),
                   TEMP=str(owned / "temp"), TMP=str(owned / "temp"))
        process = subprocess.Popen([str(exe), str(owned / "Left")], cwd=exe.parent,
                                   env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_until(lambda: len(windows_of(process.pid)) == 1 or process.poll() is not None,
                   "owned visual window not found", seconds=20, interval=.15)
        assert process.poll() is None
        hwnd = windows_of(process.pid)[0]
        win = Desktop(backend="uia").window(handle=hwnd)

        def focus():
            for _ in range(5):
                win.set_focus()
                time.sleep(.12)
                try:
                    ensure_own_foreground(process.pid)
                    return
                except AssertionError:
                    pass
            raise AssertionError("Owned app failed to obtain foreground")

        focus()
        width = min(1100, user.GetSystemMetrics(0) - 80)
        height = min(680, user.GetSystemMetrics(1) - 60)
        assert width >= 880 and height >= 570, "Desktop cannot fit matched visual fixture"
        assert user.SetWindowPos(hwnd, None, 40, 30, width, height, 0x0014)
        wait_until(lambda: abs(win.rectangle().width() - width) <= 3,
                   "window geometry did not settle", seconds=7, interval=.13)
        focus()
        panel = win.child_window(auto_id="WorkspacePanelButton")
        assert panel.exists(timeout=5)
        panel.click_input()
        address = win.child_window(auto_id="AddressShortcutBox")
        search = win.child_window(auto_id="SearchShortcutBox")
        wait_until(lambda: address.is_visible() and search.is_visible(),
                   "shortcut editor not visible", seconds=9, interval=.13)

        region = win.rectangle()
        dpi = int(user.GetDpiForWindow(hwnd))
        win_rect = [region.left, region.top, region.right, region.bottom]
        assert region.left >= 0 and region.top >= 0
        assert region.right <= user.GetSystemMetrics(0)
        assert region.bottom <= user.GetSystemMetrics(1)
        a = address.rectangle()
        s = search.rectangle()
        # Crop only the test-owned application's settings row and dropdown
        # region. Never include desktop pixels outside the window rectangle.
        crop_left = max(region.left, min(a.left, s.left) - 155)
        crop_top = max(region.top, min(a.top, s.top) - 58)
        crop_right = min(region.right, max(a.right, s.right) + 165)
        crop_bottom = min(region.bottom, max(a.bottom, s.bottom) + 280)
        crop_rect = [crop_left, crop_top, crop_right, crop_bottom]
        assert crop_right - crop_left >= 300 and crop_bottom - crop_top >= 190

        def capture(state):
            ensure_own_foreground(process.pid)
            full = ImageGrab.grab(bbox=tuple(win_rect), include_layered_windows=True)
            assert full.size == (win_rect[2] - win_rect[0], win_rect[3] - win_rect[1])
            full_path = output / f"{args.label}-{state}-full.png"
            full.save(full_path, "PNG", optimize=True)
            preview = full.crop((crop_left - region.left, crop_top - region.top,
                                 crop_right - region.left, crop_bottom - region.top))
            # Fixture's fixed full window also ensures previews share geometry.
            preview_path = output / f"{args.label}-{state}-preview.png"
            preview.save(preview_path, "PNG", optimize=True)
            return {"full_file": full_path.name, "full_sha256": hashlib.sha256(full_path.read_bytes()).hexdigest(),
                    "preview_file": preview_path.name, "preview_bytes": preview_path.stat().st_size}

        collapsed = capture("collapsed")
        focus()
        address.click_input()
        time.sleep(.6)
        expanded = capture("expanded")
        metadata = {
            "label": args.label, "source_sha": args.expected_sha,
            "configuration": "Release", "window_rect": win_rect,
            "control_crop_rect": crop_rect, "dpi": dpi,
            "desktop_dimensions": [user.GetSystemMetrics(0), user.GetSystemMetrics(1)],
            "fixture": "private disposable folder with one Korean filename",
            "states": {"collapsed": collapsed, "expanded": expanded},
        }
        (output / f"{args.label}-metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"VISUAL_CAPTURE_{args.label.upper()}=PASS", flush=True)
        print(f"VISUAL_CAPTURE_DPI={dpi} RECT={win_rect}", flush=True)
    except Exception:
        failed = True
        raise
    finally:
        if process is not None and process.poll() is None:
            if hwnd is not None:
                owner = W.DWORD()
                user.GetWindowThreadProcessId(hwnd, c.byref(owner))
                assert owner.value == process.pid, "refuse to close foreign window"
                assert user.PostMessageW(hwnd, 0x10, 0, 0)
            try:
                process.wait(timeout=14)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
                raise AssertionError("owned visual app did not close normally")
        if process is not None and not failed:
            assert process.returncode == 0, "owned visual app exit not clean"
        assert_legacy_profile_unchanged(original_path, original_values)
        shutil.rmtree(owned)


if __name__ == "__main__":
    main()
