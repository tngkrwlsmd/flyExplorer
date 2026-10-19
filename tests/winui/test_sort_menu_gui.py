"""Owned Release regression: sort checks, real keys and pane/workspace scope.

Optional matched Light/Dark captures are app-window-only; capture success still
requires separate pixel inspection. No clipboard, Recycle Bin or OS settings.
Folder tabs now have independent sort modes; the newly opened tab defaults to
Name ascending, and closing it restores the prior tab's sort.
"""
import argparse
import ctypes as ct
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from paths import ROOT, app_exe
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until
from pywinauto import Desktop, keyboard
from PIL import ImageGrab

IDS = ("SortNameAscendingItem", "SortNameDescendingItem",
       "SortTypeAscendingItem", "SortTypeDescendingItem",
       "SortSizeAscendingItem", "SortSizeDescendingItem",
       "SortDateAscendingItem", "SortDateDescendingItem")
MODES = (0, 1, 4, 5, 6, 2, 7, 3)
NAMES = ("alpha.txt", "beta.md", "한글 긴 파일 이름.txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuration", nargs="?", default="Release",
                        choices=("Debug", "Release"))
    parser.add_argument("--capture-dir", type=Path)
    args = parser.parse_args()
    exe = app_exe(args.configuration)
    assert exe.is_file()
    out = args.capture_dir or ROOT / "logs" / ("sort-menu-" + str(time.time_ns()))
    out.mkdir(parents=True, exist_ok=True)
    legacy, legacy_before = snapshot_legacy_profile()
    actual_settings = Path(os.environ["LOCALAPPDATA"]) / "flyExplorer"

    def settings_hashes():
        return {str(p.relative_to(actual_settings)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in actual_settings.rglob("*") if p.is_file()} if actual_settings.exists() else {}

    settings_before = settings_hashes()
    user = ct.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.restype = w.HWND
    user.GetWindowThreadProcessId.argtypes = (w.HWND, ct.POINTER(w.DWORD))
    user.GetDpiForWindow.argtypes = (w.HWND,)
    user.GetDpiForWindow.restype = w.UINT
    user.SetWindowPos.argtypes = (w.HWND, w.HWND, ct.c_int, ct.c_int,
                                 ct.c_int, ct.c_int, w.UINT)
    evidence = {"exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
                "images": [], "runs": []}
    for theme in ("light", "dark"):
        own = Path(tempfile.mkdtemp(prefix="sort-owned-", dir=out))
        folder = own / "source"
        folder.mkdir()
        for i, name in enumerate(NAMES):
            path = folder / name
            path.write_text("synthetic sort only", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.startswith("FLY_")}
        for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
            d = own / key.lower()
            d.mkdir()
            env[key] = str(d)
        prefs = own / "localappdata" / "flyExplorer"
        prefs.mkdir()
        (prefs / "ui-preferences-v1.txt").write_bytes(
            ("schema=2\r\nlanguage=ko-KR\r\ntheme=" + theme +
             "\r\nview=details\r\n").encode("utf-8"))
        process = None
        win = None
        passed = False
        try:
            process = subprocess.Popen([str(exe), str(folder)], cwd=exe.parent, env=env)

            def ready():
                nonlocal win
                for wrapper in Desktop(backend="uia").windows(process=process.pid):
                    spec = Desktop(backend="uia").window(handle=wrapper.handle)
                    if spec.child_window(auto_id="SortButton").exists(timeout=.1):
                        win = spec
                        return True
                return False

            wait_until(ready, "owned sort window missing", seconds=25, interval=.15)
            win.set_focus()

            def guard():
                owner = w.DWORD()
                user.GetWindowThreadProcessId(user.GetForegroundWindow(), ct.byref(owner))
                assert owner.value == process.pid, "refuse input outside owned app"

            def element(key):
                return win.child_window(auto_id=key)

            def rows(side):
                return element("LeftFiles" if side == 0 else "RightFiles").descendants(control_type="ListItem")

            def filenames(side):
                return [name for row in rows(side) for name in NAMES if name in row.window_text()]

            wait_until(lambda: len(filenames(0)) == len(filenames(1)) == 3,
                       "both owned panes not ready", seconds=25, interval=.15)

            def sort_items():
                items = [item for top in Desktop(backend="uia").windows(process=process.pid)
                         for item in top.descendants(control_type="MenuItem")]
                return {item.element_info.automation_id: item for item in items
                        if item.element_info.automation_id in IDS}

            def open_sort():
                guard()
                element("SortButton").set_focus()
                keyboard.send_keys("{SPACE}", pause=.06)
                wait_until(lambda: len(sort_items()) == 8, "sort menu missing", seconds=8, interval=.15)

            def check(mode):
                found = sort_items()
                assert len(found) == 8
                states = [int(found[key].iface_toggle.CurrentToggleState) for key in IDS]
                assert states == [int(m == mode) for m in MODES], (mode, states)

            def close_menu():
                guard()
                keyboard.send_keys("{ESC}", pause=.06)

            def choose(position):
                open_sort()
                guard()
                keyboard.send_keys("{HOME}" + "{DOWN}" * position + "{ENTER}", pause=.08)
                open_sort()
                check(MODES[position])
                close_menu()

            # Eight actual key routes. The unchanged sorting engine is exercised
            # through the two name directions on this matched visual fixture.
            for position in range(8):
                choose(position)
                mode = MODES[position]
                if mode in (0, 1):
                    descending = mode == 1
                    expected = list(reversed(NAMES)) if descending else list(NAMES)
                    wait_until(lambda: filenames(0) == expected,
                               "actual file order disagrees with chosen sort", seconds=18, interval=.15)
            choose(1)  # left name descending
            guard()
            keyboard.send_keys("{F6}")
            open_sort()
            check(0)  # untouched right pane
            close_menu()
            choose(5)  # right size descending
            guard()
            keyboard.send_keys("{F6}")
            open_sort()
            check(1)
            close_menu()
            def tab_count():
                return len(element("LeftTabs").descendants(control_type="TabItem"))

            original_count = tab_count()
            element("NewTabButton").invoke()
            wait_until(lambda: tab_count() == original_count + 1,
                       "pane tab was not created", seconds=15, interval=.15)
            wait_until(lambda: len(filenames(0)) == 3, "new pane tab not ready", seconds=20, interval=.15)
            open_sort()
            check(0)  # A new PaneTab defaults to Name ascending.
            close_menu()
            choose(0)
            element("CloseTabButton").invoke()
            wait_until(lambda: tab_count() == original_count,
                       "pane tab was not closed", seconds=15, interval=.15)
            wait_until(lambda: filenames(0) == list(reversed(NAMES)),
                       "original PaneTab sort not restored after close", seconds=15, interval=.15)
            open_sort()
            check(1)
            close_menu()
            choose(1)
            # Window Tabs own independent workspaces as well as pane tabs.
            def workspace_count():
                return len(element("WindowTabStrip").descendants(control_type="TabItem"))

            guard()
            keyboard.send_keys("^t")
            wait_until(lambda: workspace_count() == 2, "workspace not created", seconds=15, interval=.15)
            guard()
            keyboard.send_keys("^l")
            wait_until(lambda: element("AddressBox").has_keyboard_focus(),
                       "new workspace address not focused", seconds=8, interval=.15)
            element("AddressBox").set_edit_text(str(folder))
            guard()
            keyboard.send_keys("{ENTER}")
            wait_until(lambda: len(filenames(0)) == 3, "owned workspace folder not ready", seconds=20, interval=.15)
            choose(2)  # new workspace type ascending
            guard()
            keyboard.send_keys("^+{TAB}")
            wait_until(lambda: filenames(0) == list(reversed(NAMES)),
                       "original workspace name order not restored", seconds=15, interval=.15)
            open_sort()
            check(1)
            close_menu()
            guard()
            keyboard.send_keys("^{TAB}")
            wait_until(lambda: len(filenames(0)) == 3,
                       "new workspace folder not restored", seconds=15, interval=.15)
            open_sort()
            check(4)
            close_menu()
            guard()
            keyboard.send_keys("^w")
            wait_until(lambda: workspace_count() == 1, "owned workspace not closed", seconds=15, interval=.15)
            open_sort()
            check(1)
            close_menu()
            # Restore the baseline's right-pane name order before pixel pairs.
            guard()
            keyboard.send_keys("{F6}")
            choose(0)
            guard()
            keyboard.send_keys("{F6}")
            for width in (960, 800):
                assert user.SetWindowPos(win.handle, None, 35, 35, width, 634, 0x0014)
                time.sleep(.4)
                open_sort()
                check(1)
                guard()
                rect = win.rectangle()
                dpi = user.GetDpiForWindow(win.handle)
                assert dpi == 96, "matched baseline is 96 DPI only"
                box = (rect.left + 12, rect.top + 8, rect.right - 12, rect.bottom - 8)
                assert box[0] >= 0 and box[1] >= 0
                assert box[2] <= user.GetSystemMetrics(0) and box[3] <= user.GetSystemMetrics(1)
                image = ImageGrab.grab(bbox=box, include_layered_windows=True)
                name = f"after-{theme}-{width}"
                path = out / (name + ".png")
                image.save(path)
                evidence["images"].append({"name": name, "dpi": dpi, "rect": list(box),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                close_menu()
            passed = True
        finally:
            if process and process.poll() is None:
                if win:
                    win.close()
                try:
                    process.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
            evidence["runs"].append({"theme": theme, "exit": None if process is None else process.poll(),
                                     "functional_pass": passed})
            assert_legacy_profile_unchanged(legacy, legacy_before)
            assert settings_hashes() == settings_before
            assert own.parent.resolve() == out.resolve() and own.name.startswith("sort-owned-")
            assert not any(p.is_symlink() or p.is_junction() for p in own.rglob("*"))
            if passed:
                shutil.rmtree(own)
        assert process.returncode == 0, "owned app did not exit normally"
    assert_legacy_profile_unchanged(legacy, legacy_before)
    assert settings_hashes() == settings_before
    evidence["settings_unchanged"] = True
    (out / "sort-menu.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SORT_MENU_FUNCTIONAL_PASS PIXEL_REVIEW_REQUIRED", flush=True)


if __name__ == "__main__":
    main()
