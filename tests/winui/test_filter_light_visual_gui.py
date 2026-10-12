"""Real WinUI light-theme filter palette screenshots, disposable data only.

Capture two baseline states or all four color/icon combinations in normal
and selected/focused states. Actual pixels need independent human/agent review.
"""
from __future__ import annotations
import argparse
import ctypes as c
from ctypes import wintypes as W
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
    raise SystemExit("WinUI visual inspection requires the real Windows desktop")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    parser.add_argument("--exact-sha", required=True)
    args = parser.parse_args()
    assert len(args.exact_sha) == 40 and all(x in "0123456789abcdef" for x in args.exact_sha)
    root = args.source.resolve(strict=True)
    output = args.output.resolve(strict=True)
    sys.path.insert(0, str(root / "tests" / "winui"))
    from paths import app_exe
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop
    from PIL import Image, ImageGrab

    exe = app_exe("Release")
    assert exe.is_file(), "complete exact-commit Release executable missing"
    prior_path, prior_values = snapshot_legacy_profile()
    fixture = Path(tempfile.mkdtemp(prefix="filter-light-owned-", dir=output))
    for name in ("files", "appdata", "localdata", "tmp"):
        (fixture / name).mkdir()
    profile = fixture / "localdata" / "flyExplorer"
    profile.mkdir()
    (profile / "ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=light\r\nview=details\r\n")
    for name in ("alpha.cpp", "beta.h", "notes.txt", "사진.JPG"):
        (fixture / "files" / name).write_text("disposable", encoding="utf-8")

    env = dict(os.environ)
    env.update(APPDATA=str(fixture / "appdata"),
               LOCALAPPDATA=str(fixture / "localdata"),
               TEMP=str(fixture / "tmp"), TMP=str(fixture / "tmp"))
    u = c.windll.user32
    u.GetForegroundWindow.restype = W.HWND
    u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
    u.GetDpiForWindow.argtypes = [W.HWND]
    u.GetDpiForWindow.restype = W.UINT
    u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    u.SetWindowPos.argtypes = [W.HWND, W.HWND, c.c_int, c.c_int, c.c_int, c.c_int, W.UINT]
    callback = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumWindows.argtypes = [callback, W.LPARAM]
    width = min(1060, u.GetSystemMetrics(0) - 50)
    height = min(720, u.GetSystemMetrics(1) - 45)
    assert width >= 830 and height >= 570, "real desktop too small for light-theme filter test"
    bounds = [20, 15, 20 + width, 15 + height]
    desktop = [u.GetSystemMetrics(0), u.GetSystemMetrics(1)]
    capture_height = min(680, height)
    dpi_seen = []
    binaries = hashlib.sha256(exe.read_bytes()).hexdigest()
    states = []
    palettes = [(1, "blue", "파랑", "별"),
                (2, "green", "초록", "핀"),
                (3, "amber", "주황", "깃발"),
                (4, "red", "빨강", "태그")]
    configurations = palettes  # Both revisions already support color/icon selectors
    process = None
    hwnd = None

    def owned_windows(pid):
        found = []
        @callback
        def visit(handle, _):
            owner = W.DWORD()
            u.GetWindowThreadProcessId(handle, c.byref(owner))
            if owner.value == pid and u.IsWindowVisible(handle):
                found.append(handle)
            return True
        u.EnumWindows(visit, 0)
        return found

    def require_owned_foreground(pid):
        owner = W.DWORD()
        handle = u.GetForegroundWindow()
        if handle:
            u.GetWindowThreadProcessId(handle, c.byref(owner))
        assert handle and owner.value == pid, "Refuse physical input or capture outside owned foreground"

    def stop_owned():
        nonlocal process, hwnd
        if process is not None:
            if process.poll() is None:
                if hwnd is not None:
                    owner = W.DWORD()
                    u.GetWindowThreadProcessId(hwnd, c.byref(owner))
                    assert owner.value == process.pid, "Refuse to close foreign HWND"
                    assert u.PostMessageW(hwnd, 0x10, 0, 0), "Owned WM_CLOSE failed"
                process.wait(timeout=15)
            assert process.returncode == 0, "Test-owned WinUI failed graceful shutdown"
        process = None
        hwnd = None

    try:
        for color, slug, visible_color, visible_icon in configurations:
            process = subprocess.Popen(
                [str(exe), str(fixture / "files")], cwd=exe.parent, env=env,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            wait_until(lambda: len(owned_windows(process.pid)) == 1
                       or process.poll() is not None,
                       "test-owned light WinUI HWND did not appear",
                       seconds=25, interval=.18)
            if process.poll() is not None:
                print("FILTER_LIGHT_STARTUP_EXIT", process.returncode, flush=True)
            assert process.poll() is None and len(owned_windows(process.pid)) == 1
            hwnd = owned_windows(process.pid)[0]
            win = Desktop(backend="uia").window(handle=hwnd)
            assert u.SetWindowPos(hwnd, None, bounds[0], bounds[1],
                                  width, height, 0x0014)
            wait_until(lambda: win.rectangle().width() == width
                       and win.rectangle().height() == height,
                       "light-theme owned window geometry failed", seconds=9, interval=.16)
            for _ in range(5):
                win.set_focus()
                time.sleep(.12)
                if u.GetForegroundWindow() == hwnd:
                    break
            require_owned_foreground(process.pid)
            win.child_window(auto_id="FilterRulePanelButton").click_input()
            name = win.child_window(auto_id="FilterRuleNameEdit")
            masks = win.child_window(auto_id="FilterRuleMasksEdit")
            assert name.exists(timeout=5) and masks.exists(timeout=5)
            name.set_edit_text("코드 파일")
            masks.set_edit_text("*.cpp;*.h")
            if color:
                colors = win.child_window(auto_id="FilterRuleColorBox")
                icons = win.child_window(auto_id="FilterRuleIconBox")
                assert colors.exists(timeout=5) and icons.exists(timeout=5)
                colors.select(color)
                icons.select(color)
                assert colors.selected_text() == visible_color
                assert icons.selected_text() == visible_icon
            else:
                assert not win.child_window(auto_id="FilterRuleColorBox").exists(timeout=.25)
            win.child_window(auto_id="FilterRuleSaveButton").click_input()
            store = profile / "filter-rules-v1.txt"
            expected = ("코드 파일\t*.cpp;*.h\t" + str(color) + "\t" + str(color)
                        if color else "코드 파일\t*.cpp;*.h")
            wait_until(lambda: store.is_file() and expected in
                       store.read_text(encoding="utf-8"),
                       "exact styled filter rule did not persist",
                       seconds=11, interval=.2)
            if color:
                assert "schema=2" in store.read_text(encoding="utf-8")
            else:
                assert "schema=1" in store.read_text(encoding="utf-8")
            file_list = win.child_window(auto_id="LeftFiles")
            wait_until(lambda: any("alpha.cpp" in item.window_text()
                       for item in file_list.descendants(control_type="ListItem")),
                       "visible owned alpha.cpp row missing", seconds=12, interval=.18)
            if color:
                wait_until(lambda: any(
                    "필터 분류 아이콘" in item.window_text()
                    for item in file_list.descendants()),
                    "classification icon not exposed through UIA",
                    seconds=10, interval=.2)

            def capture(state):
                require_owned_foreground(process.pid)
                rect = win.rectangle()
                assert [rect.left, rect.top, rect.right, rect.bottom] == bounds
                dpi = int(u.GetDpiForWindow(hwnd))
                dpi_seen.append(dpi)
                image = ImageGrab.grab(bbox=tuple(bounds), include_layered_windows=True)
                assert image.size == (width, height)
                preview = image.crop((0, 0, width, capture_height))
                # The bottom-right file-list area should be light for this
                # test-owned profile, not dark with white text.
                pixel = preview.convert("RGB").getpixel((width - 34, capture_height - 34))
                assert min(pixel) >= 175, ("Actual theme is not light", pixel)
                filename = args.label + "-" + slug + "-" + state + ".png"
                path = output / filename
                preview.save(path, "PNG", optimize=True)
                states.append({"filename": filename, "color": slug, "state": state,
                               "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                               "bytes": path.stat().st_size, "dpi": dpi,
                               "light_background_sample": list(pixel)})
                print("FILTER_LIGHT_CAPTURE", filename, "DPI", dpi, flush=True)

            time.sleep(.5)
            capture("normal")
            matching = [item for item in file_list.descendants(
                control_type="ListItem") if "alpha.cpp" in item.window_text()]
            assert len(matching) == 1, "Expected one selectable alpha.cpp file row"
            matching[0].click_input()
            wait_until(lambda: matching[0].is_selected(),
                       "owned file row did not enter selected state", seconds=4, interval=.12)
            require_owned_foreground(process.pid)
            # A pointer click is a real physical input that gives the row
            # keyboard focus. Record the actual state independently.
            focused = bool(matching[0].has_keyboard_focus())
            print("FILTER_LIGHT_SELECTED_ROW_FOCUSED", slug, focused, flush=True)
            if not focused:
                matching[0].set_focus()
                wait_until(lambda: matching[0].has_keyboard_focus(),
                           "matching file row did not accept keyboard focus",
                           seconds=4, interval=.12)
            time.sleep(.25)
            capture("selected-focus")
            stop_owned()

        assert len(set(dpi_seen)) == 1, ("DPI differs across palette captures", dpi_seen)
        montage_names = []
        if True:
            for state in ("normal", "selected-focus"):
                combined = Image.new("RGB", (width * 2, capture_height * 2))
                for i, (_, slug, _, _) in enumerate(palettes):
                    panel = Image.open(output / (args.label + "-" + slug + "-" + state + ".png"))
                    assert panel.size == (width, capture_height)
                    combined.paste(panel.convert("RGB"), ((i % 2) * width,
                                                          (i // 2) * capture_height))
                montage_name = args.label + "-light-" + state + "-montage.png"
                combined.save(output / montage_name, "PNG", optimize=True)
                montage_names.append(montage_name)
        metadata = {
            "revision": args.exact_sha, "role": args.label,
            "configuration": "Release", "theme": "light", "view": "details",
            "window": bounds, "desktop": desktop,
            "dpi": dpi_seen[0],
            "crop": [0, 0, width, capture_height],
            "test_owned_files": ["alpha.cpp", "beta.h", "notes.txt", "사진.JPG"],
            "binary_sha256": binaries, "images": states,
            "montages": montage_names,
        }
        (output / (args.label + "-light-metadata.json")).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print("FILTER_LIGHT_MATRIX_" + args.label.upper() + "=PASS",
              len(states), "images", flush=True)
    finally:
        if process is not None:
            stop_owned()
        assert_legacy_profile_unchanged(prior_path, prior_values)
        shutil.rmtree(fixture)


if __name__ == "__main__":
    main()
