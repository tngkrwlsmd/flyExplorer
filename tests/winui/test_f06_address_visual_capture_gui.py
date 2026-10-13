"""Capture current F06 address candidates from a test-owned WinUI window.

A capture PASS is not a pixel-review PASS. No desktop/user-owned pixels
or paths may be captured; the foreground must remain the owned HWND.
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
    raise SystemExit("Interactive Windows WinUI desktop required")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--theme", required=True, choices=("light", "dark"))
    parser.add_argument("--width", required=True, type=int, choices=(800, 940))
    args = parser.parse_args()

    root = args.source.resolve(strict=True)
    output = args.output.resolve(strict=True)
    if len(args.source_sha) != 40 or not all(
            c in "0123456789abcdef" for c in args.source_sha):
        parser.error("--source-sha must be an exact lowercase 40-hex SHA")
    actual = subprocess.check_output(
        ["git", "-c", "safe.directory=" + str(root),
         "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    assert actual == args.source_sha, (actual, args.source_sha)

    sys.path.insert(0, str(root / "tests/winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop
    from pywinauto.keyboard import send_keys
    from PIL import ImageGrab

    exe = app_exe("Release")
    assert exe.is_file()
    legacy_loc, legacy_profile = snapshot_legacy_profile()
    owned = Path(tempfile.mkdtemp(prefix="f06-visual-owned-", dir=output))
    for label in ("Left", "appdata", "localdata", "temp"):
        (owned / label).mkdir()
    (owned / "Left" / "Nested").mkdir()
    for filename in ("readme.txt", "report.tar.gz", "한글.문서"):
        (owned / "Left" / filename).write_text("owned-only", encoding="utf-8")
    prefs = owned / "localdata" / "flyExplorer"
    prefs.mkdir()
    (prefs / "ui-preferences-v1.txt").write_bytes(
        ("schema=2\r\nlanguage=ko-KR\r\ntheme=" + args.theme +
         "\r\nview=details\r\n").encode("utf-8"))

    user = ct.windll.user32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ct.POINTER(wintypes.DWORD)]
    user.GetDpiForWindow.argtypes = [wintypes.HWND]
    user.GetDpiForWindow.restype = wintypes.UINT
    user.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ct.c_int, ct.c_int, ct.c_int,
        ct.c_int, wintypes.UINT]
    user.PostMessageW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ct.c_int]
    callback = ct.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback, wintypes.LPARAM]

    process = None
    hwnd = None
    finished = False
    try:
        environment = dict(os.environ)
        environment.update(APPDATA=str(owned / "appdata"),
                           LOCALAPPDATA=str(owned / "localdata"),
                           TEMP=str(owned / "temp"), TMP=str(owned / "temp"))
        process = subprocess.Popen(
            [str(exe), str(owned / "Left")], cwd=exe.parent, env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)

        def owned_windows():
            found = []

            @callback
            def visit(candidate, unused):
                owner = wintypes.DWORD()
                user.GetWindowThreadProcessId(candidate, ct.byref(owner))
                if owner.value == process.pid and user.IsWindowVisible(candidate):
                    label = ct.create_unicode_buffer(256)
                    user.GetWindowTextW(candidate, label, len(label))
                    if "flyExplorer" in label.value:
                        found.append(candidate)
                return True

            user.EnumWindows(visit, 0)
            return found

        wait_until(lambda: len(owned_windows()) == 1 or process.poll() is not None,
                   "owned F06 window missing", seconds=24, interval=.15)
        assert process.poll() is None, process.returncode
        hwnd = owned_windows()[0]
        win = Desktop(backend="uia").window(handle=hwnd)
        height = min(610, user.GetSystemMetrics(1) - 85)
        width = min(args.width, user.GetSystemMetrics(0) - 75)
        assert width == args.width and height >= 550
        assert user.SetWindowPos(hwnd, None, 35, 35, width, height, 0x0014)
        wait_until(lambda: abs(win.rectangle().width() - width) <= 3,
                   "owned window width not stable", seconds=9, interval=.15)

        def ensure_foreground():
            owner = wintypes.DWORD()
            foreground = user.GetForegroundWindow()
            if foreground:
                user.GetWindowThreadProcessId(foreground, ct.byref(owner))
            assert foreground and owner.value == process.pid, (
                "refuse input/capture outside owned flyExplorer window")

        win.set_focus()
        wait_until(lambda: user.GetForegroundWindow() == hwnd,
                   "owned F06 window not foreground", seconds=8, interval=.2)
        ensure_foreground()
        send_keys("^l")
        address = win.child_window(auto_id="AddressBox")
        wait_until(lambda: address.has_keyboard_focus(),
                   "Ctrl+L did not focus F06 address editor",
                   seconds=9, interval=.2)
        address.set_edit_text(str(owned / "Left") + "\\N")
        expected = "주소 후보: " + str(owned / "Left" / "Nested")

        def candidate_buttons():
            return [child for child in win.descendants(control_type="Button")
                    if (child.element_info.name or "").startswith("주소 후보: ")]

        wait_until(lambda: any(btn.element_info.name == expected
                               for btn in candidate_buttons()),
                   "known owned Nested address suggestion missing",
                   seconds=12, interval=.2)
        buttons = candidate_buttons()
        assert 1 <= len(buttons) <= 8
        matched = [b for b in buttons if b.element_info.name == expected]
        assert len(matched) == 1
        assert address.has_keyboard_focus()
        ensure_foreground()
        rect = win.rectangle()
        area = (rect.left + 12, rect.top + 8,
                rect.right - 8, rect.bottom - 8)
        assert 0 <= area[0] < area[2] <= user.GetSystemMetrics(0)
        assert 0 <= area[1] < area[3] <= user.GetSystemMetrics(1)
        candidate_rect = matched[0].rectangle()
        assert rect.left <= candidate_rect.left < candidate_rect.right <= rect.right
        assert rect.top <= candidate_rect.top < candidate_rect.bottom <= rect.bottom

        shot = ImageGrab.grab(bbox=area, include_layered_windows=True)
        filename = f"f06-{args.theme}-{args.width}-suggestions.png"
        shot.save(output / filename, "PNG", optimize=True)
        result = {
            "source_sha": args.source_sha,
            "theme": args.theme,
            "width": args.width,
            "dpi": int(user.GetDpiForWindow(hwnd)),
            "window_rect": [rect.left, rect.top, rect.right, rect.bottom],
            "capture_rect": list(area),
            "owned_fixture": "synthetic Left/Nested candidate, UIA focused editor",
            "candidate_count": len(buttons),
            "candidate_rect": [candidate_rect.left, candidate_rect.top,
                               candidate_rect.right, candidate_rect.bottom],
            "file": filename,
            "sha256": hashlib.sha256((output / filename).read_bytes()).hexdigest(),
        }
        (output / f"f06-{args.theme}-{args.width}-metadata.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        ensure_foreground()
        send_keys("{ESC}")
        wait_until(lambda: len(candidate_buttons()) == 0,
                   "Escape did not dismiss owned F06 candidate panel",
                   seconds=8, interval=.2)
        print(f"F06_VISUAL_CAPTURE_{args.theme.upper()}_{args.width}=PASS "
              f"DPI={result['dpi']} CANDIDATES={len(buttons)}", flush=True)
        finished = True
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
                raise AssertionError("owned F06 app failed normal shutdown")
        if finished:
            assert process is not None and process.returncode == 0
        assert_legacy_profile_unchanged(legacy_loc, legacy_profile)
        shutil.rmtree(owned)


if __name__ == "__main__":
    main()
