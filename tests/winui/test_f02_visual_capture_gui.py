"""Owned BEFORE(main) / AFTER(F02) actual WinUI view-menu pixel captures.

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
    parser.add_argument("--window-width", type=int, default=940,
                        help="Requested owned window width; 800-940 px")
    parser.add_argument("--window-height", type=int, default=610,
                        help="Requested owned window height; 550-610 px")
    parser.add_argument("--capture-focus", action="store_true",
                        help="Capture the focused Details toggle on the AFTER revision")
    args = parser.parse_args()
    if not 800 <= args.window_width <= 940 or not 550 <= args.window_height <= 610:
        parser.error("requested window geometry exceeds the bounded F02 fixture")
    if args.capture_focus and args.label != "after":
        parser.error("--capture-focus applies only to the AFTER revision")
    root = args.source.resolve(strict=True)
    output = args.output.resolve(strict=True)
    assert root.is_dir() and output.is_dir()
    assert len(args.source_sha) == 40 and all(c in "0123456789abcdef" for c in args.source_sha)
    assert (root / "app/winui/MainWindow.xaml").is_file()
    sys.path.insert(0, str(root / "tests/winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop, mouse
    from pywinauto.keyboard import send_keys
    from PIL import ImageGrab

    executable = app_exe("Release")
    assert executable.is_file(), executable
    actual_sha = subprocess.check_output(
        ["git", "-c", "safe.directory=" + str(root), "-C", str(root), "rev-parse", "HEAD"],
        text=True).strip()
    assert actual_sha == args.source_sha, (actual_sha, args.source_sha)

    legacy_location, legacy_profile = snapshot_legacy_profile()
    owned = Path(tempfile.mkdtemp(prefix="f02-visual-owned-", dir=output))
    for name in ("Left", "appdata", "localdata", "temp"):
        (owned / name).mkdir()
    for name in ("readme.txt", "report.tar.gz", "한글.문서", ".gitignore"):
        (owned / "Left" / name).write_text("synthetic F02 only", encoding="utf-8")
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
                   "test-owned F02 app window missing", seconds=24, interval=.15)
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

        width = min(args.window_width, user.GetSystemMetrics(0)-75)
        height = min(args.window_height, user.GetSystemMetrics(1)-85)
        assert width >= 800 and height >= 550, (width, height)
        assert user.SetWindowPos(hwnd, None, 35, 35, width, height, 0x0014)
        wait_until(lambda: abs(win.rectangle().width()-width) <= 3 and
                   abs(win.rectangle().height()-height) <= 3,
                   "F02 window geometry did not stabilize", seconds=9, interval=.15)
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

        rect = win.rectangle()
        window_rect = (rect.left, rect.top, rect.right, rect.bottom)
        # Windows' shadow/invisible frame can reveal unrelated desktop pixels
        # inside a top-level HWND bounding rectangle. Only retain the opaque,
        # test-owned application interior; keep matched crop across revisions.
        capture_rect = (rect.left + 12, rect.top + 8,
                        rect.right - 8, rect.bottom - 8)
        assert capture_rect[0] < capture_rect[2]
        assert capture_rect[1] < capture_rect[3]
        assert rect.left >= 0 and rect.top >= 0
        assert rect.right <= user.GetSystemMetrics(0)
        assert rect.bottom <= user.GetSystemMetrics(1)
        dpi = int(user.GetDpiForWindow(hwnd))
        assert dpi > 0
        states = {}

        def shot(state, expected_focus=None):
            if expected_focus is None:
                focus()
            if expected_focus is not None:
                assert expected_focus.has_keyboard_focus(), (
                    "focused control lost keyboard focus before capture", state)
            image = ImageGrab.grab(bbox=capture_rect, include_layered_windows=True)
            assert image.size == (capture_rect[2] - capture_rect[0],
                                  capture_rect[3] - capture_rect[1])
            name = f"f02-{args.theme}-{args.label}-{state}.png"
            image.save(output / name, "PNG", optimize=True)
            states[state] = {
                "file": name,
                "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
                "bytes": (output / name).stat().st_size,
                "rect": list(capture_rect),
            }

        shot("default")
        if args.label == "after":
            focus()
            button = win.child_window(auto_id="FileInfoToggleButton")
            assert button.exists(timeout=3), "F02 toggle missing on AFTER revision"
            button.click_input()
            wait_until(lambda: win.child_window(auto_id="FileInfoName").exists(timeout=.15)
                       and win.child_window(auto_id="FileInfoName").window_text()=="readme.txt",
                       "F02 selected read-only name not visible", seconds=10, interval=.15)
            wait_until(lambda: win.child_window(auto_id="FileInfoHint").exists(timeout=.15),
                       "F02 details accessibility hint absent", seconds=7, interval=.15)
            shot("enabled")
            if args.window_height <= 550:
                location = win.child_window(auto_id="FileInfoLocation")
                modified = win.child_window(auto_id="FileInfoModified")
                point = location.rectangle().mid_point()
                focus()
                mouse.scroll(wheel_dist=-5, coords=(point.x, point.y))
                wait_until(lambda: bool(modified.window_text()) and
                           modified.rectangle().bottom < win.rectangle().bottom - 20,
                           "F02 narrow modified date not reachable after scroll",
                           seconds=8, interval=.2)
                shot("scrolled")
                mouse.scroll(wheel_dist=5, coords=(point.x, point.y))
                shot("restored")
                print("F02_VISUAL_NARROW_MODIFIED_DATE_SCROLL=PASS", flush=True)
            if args.capture_focus:
                button.set_focus()
                send_keys("+{TAB}")
                wait_until(lambda: not button.has_keyboard_focus(),
                           "Shift+Tab did not move focus", seconds=5, interval=.15)
                send_keys("{TAB}")
                wait_until(lambda: button.has_keyboard_focus(),
                           "F02 Details toggle keyboard focus not exposed",
                           seconds=6, interval=.15)
                shot("focused-toggle", expected_focus=button)
                if states["focused-toggle"]["sha256"] == states.get(
                        "restored", states["enabled"])["sha256"]:
                    print("F02_FOCUS_PIXELS_IDENTICAL=REVIEW_REQUIRED", flush=True)
                else:
                    print("F02_FOCUS_PIXELS_DIFFER=PASS", flush=True)
                print("F02_VISUAL_AFTER_FOCUSED_TOGGLE=PASS", flush=True)
            print("F02_VISUAL_AFTER_GUI_DETAILS=PASS", flush=True)
        assert process.poll() is None

        data = {
            "label": args.label, "theme": args.theme, "source_sha": args.source_sha,
            "configuration": "Release",
            "requested_window": [args.window_width, args.window_height],
            "focus_probe": args.capture_focus,
            "window_rect": list(window_rect),
            "capture_rect": list(capture_rect),
            "dpi": dpi, "desktop": [user.GetSystemMetrics(0), user.GetSystemMetrics(1)],
            "fixture": "test-owned 4 synthetic names, left Details selected readme.txt",
            "states": states,
        }
        (output / f"f02-{args.theme}-{args.label}-metadata.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        finished = True
        print(f"F02_VISUAL_{args.theme.upper()}_{args.label.upper()}_CAPTURE=PASS",
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
                raise AssertionError("owned F02 visual app did not exit")
        if finished:
            assert process is not None and process.returncode == 0
        assert_legacy_profile_unchanged(legacy_location, legacy_profile)
        shutil.rmtree(owned)


if __name__ == "__main__":
    main()
