"""G01 native WinUI shutdown diagnostic: three owned details drags + two WindowTabs.

No cursor acceptance, screenshots or other unrelated visual tests. Each
process, input, temporary file and trace is test-owned and PID-bound.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import psutil
from pywinauto import Desktop, keyboard, mouse

from paths import APP, app_exe
from uia_polling import wait_until

USER32 = ctypes.windll.user32
USER32.GetForegroundWindow.restype = wintypes.HWND
USER32.IsWindow.argtypes = (wintypes.HWND,)
USER32.IsWindow.restype = wintypes.BOOL
USER32.GetWindowThreadProcessId.argtypes = (
    wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
)
USER32.GetWindowThreadProcessId.restype = wintypes.DWORD
USER32.PostMessageW.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
)
USER32.PostMessageW.restype = wintypes.BOOL

PHASES = {
    "APPWINDOW_CLOSING_ENTER", "APPWINDOW_CLOSING_EXIT",
    "WINDOW_CLOSED_ENTER", "WINDOW_CLOSED_EXIT",
    "PREPARE_XAML_ENTER", "PREPARE_XAML_ALREADY_CLOSING",
    "FOCUS_TRANSFER_BEGIN", "FOCUS_TRANSFER_EXCEPTION",
    "FOCUS_TRANSFER_SUCCEEDED", "FOCUS_TRANSFER_REJECTED",
    "FOCUS_TRANSFER_DONE", "PREPARE_XAML_EXIT",
    "FOCUS_BEFORE_TEXT_INPUT", "FOCUS_BEFORE_OTHER",
    "FOCUS_BEFORE_NONE", "FOCUS_BEFORE_QUERY_EXCEPTION",
    "FOCUS_AFTER_TEXT_INPUT", "FOCUS_AFTER_OTHER",
    "FOCUS_AFTER_NONE", "FOCUS_AFTER_QUERY_EXCEPTION",
    "PREPARE_CLOSE_ENTER", "PREPARE_CLOSE_ALREADY_CLOSING",
    "CURSOR_HOOKS_STOPPED", "XAML_CONTROLS_RELEASED",
    "SESSION_CLOSE_PREPARED", "CONTROLLERS_CLOSE_PREPARED",
    "WORKSPACE_ROUTES_INVALIDATED", "SHELL_NAV_SHUTDOWN_DONE",
    "PREPARE_CLOSE_EXIT", "MAINWINDOW_DESTRUCTOR_ENTER",
    "MAINWINDOW_DESTRUCTOR_EXIT", "APP_DESTRUCTOR_ENTER",
    "APP_DESTRUCTOR_BODY_EXIT",
}
LEGACY = (
    "fxfile.conf", "fxfile-main.conf", "fxfile-toolbar.dat",
    "fxfile-coolbar.dat", "fxfile-dlg_state.conf",
    "fxfile-folder_layout.conf",
)


def check(condition, description, seconds=12):
    return wait_until(condition, description, seconds=seconds, interval=.2)


def run(config="Release", scenario="full"):
    assert config in ("Release", "Debug")
    assert scenario in ("plain", "baseline", "tabs", "full")
    exe = app_exe(config)
    assert exe.is_file()
    root = APP.parents[1] / "logs" / "g01-close-focused"
    root.mkdir(parents=True, exist_ok=True)
    assert not root.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="columns-gui-owned-", dir=root))
    folder = owned / "synthetic"
    folder.mkdir()
    for name in ("alpha.txt", "beta.txt", "gamma.txt"):
        (folder / name).write_text(name, encoding="utf-8")

    profile = Path(os.environ["APPDATA"]) / "fxfile" / "conf"
    before = {
        name: hashlib.sha256((profile / name).read_bytes()).digest()
        for name in LEGACY if (profile / name).is_file()
    }
    environment = {**os.environ, "FLY_G01_OWNED_CLOSE_TRACE": "YES"}
    if scenario != "plain":
        environment["FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC"] = "1"
    else:
        environment.pop("FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC", None)
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        target = owned / key.lower()
        target.mkdir()
        environment[key] = str(target)

    proc = subprocess.Popen(
        [str(exe), str(folder)], cwd=exe.parent, env=environment,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    hwnd = None
    phase_log = []
    timed_out = False
    scenario_ready = False
    try:
        def window():
            nonlocal hwnd
            assert proc.poll() is None, "owned G01 process exited before close"
            assert Path(psutil.Process(proc.pid).exe()).resolve() == exe.resolve()
            found = [
                item for item in Desktop(backend="uia").windows(process=proc.pid)
                if "flyExplorer" in item.window_text()
            ]
            if len(found) != 1:
                return None
            hwnd = found[0].handle
            return Desktop(backend="uia").window(handle=hwnd)

        win = check(window, "owned G01 WinUI window missing", seconds=22)
        assert win.element_info.process_id == proc.pid
        win.maximize()
        check(lambda: win.rectangle().width() >= 1050,
              "owned G01 window could not maximize")
        def element(auto_id):
            return win.child_window(auto_id=auto_id)

        width = element("LeftFiles").rectangle().width()
        if width < 500:
            element("SplitButton").click_input()
            check(lambda: element("LeftFiles").rectangle().width() >= 500,
                  "details pane too narrow")
        def foreground():
            return int(USER32.GetForegroundWindow() or 0) == int(hwnd or 0)
        win.set_focus()
        check(foreground, "owned G01 app not in foreground")

        def drag(column, next_column, delta):
            grip = element(column).rectangle()
            baseline = element(next_column).rectangle().left
            assert grip.width() >= 10 and grip.height() >= 8
            x = (grip.left + grip.right) // 2
            y = (grip.top + grip.bottom) // 2
            assert foreground()
            mouse.move(coords=(x, y))
            mouse.press(button="left", coords=(x, y))
            try:
                for step in range(1, 11):
                    mouse.move(coords=(x + round(delta * step / 10), y))
                    time.sleep(.06)
            finally:
                mouse.release(button="left", coords=(x + delta, y))
            check(lambda: element(next_column).rectangle().left >= baseline + 12,
                  column + " drag did not commit")
            print("G01_OWNED_COLUMN_DRAG_PASS", column, flush=True)

        if scenario == "full":
            drag("LeftNameColumnResizeThumb", "LeftTypeSortButton", 40)
            drag("LeftTypeColumnResizeThumb", "LeftSizeSortButton", 28)
            drag("LeftSizeColumnResizeThumb", "LeftDateSortButton", 20)
        if scenario in ("tabs", "full"):
            before_return = element("LeftTypeSortButton").rectangle().left
            win.set_focus()
            assert foreground()
            keyboard.send_keys("^t")
            strip = element("WindowTabStrip")
            def tabs():
                return [
                    item for item in strip.descendants()
                    if item.element_info.control_type == "TabItem"
                    and item.element_info.process_id == proc.pid
                ]
            check(lambda: len(tabs()) == 2, "second owned WindowTab not created")
            tabs()[0].click_input()
            check(lambda: abs(element("LeftTypeSortButton").rectangle().left -
                              before_return) <= 4,
                  "column width not retained on WindowTab return")
        print("G01_OWNED_SCENARIO_PREPARED", scenario, flush=True)
        scenario_ready = True
    finally:
        if proc.poll() is None:
            assert hwnd is not None
            current = wintypes.DWORD()
            thread = USER32.GetWindowThreadProcessId(
                hwnd, ctypes.byref(current))
            assert thread and current.value == proc.pid
            posted = bool(USER32.PostMessageW(hwnd, 0x0010, 0, 0))
            print("G01_OWNED_CLOSE_POSTED", posted, flush=True)
            assert posted, "owned WM_CLOSE not posted"
            start = time.monotonic()
            for seconds in (.25, 1.0, 3.0, 7.0, 13.0):
                remaining = seconds - (time.monotonic() - start)
                if remaining > 0:
                    try:
                        proc.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        pass
                if proc.poll() is not None:
                    break
                print("G01_OWNED_CLOSE_TIMELINE_MS", int(seconds * 1000),
                      "HWND_ALIVE", bool(USER32.IsWindow(hwnd)),
                      flush=True)
            if proc.poll() is None:
                timed_out = True
                proc.terminate()
                proc.wait(timeout=5)
        assert proc.poll() is not None
        print("G01_OWNED_NATIVE_EXIT_HEX",
              hex(proc.returncode & 0xffffffff), flush=True)
        path = owned / "temp" / f"fly-g01-close-{proc.pid}.log"
        if not path.is_file():
            path = owned / "tmp" / f"fly-g01-close-{proc.pid}.log"
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= 4096:
            phase_log = path.read_text(encoding="ascii").splitlines()
            if len(phase_log) <= 64 and all(p in PHASES for p in phase_log):
                print("G01_OWNED_PHASE_TRACE", ",".join(phase_log), flush=True)
            else:
                print("G01_OWNED_PHASE_TRACE_INVALID", flush=True)
                phase_log = []
        else:
            print("G01_OWNED_PHASE_TRACE_MISSING", flush=True)
        unchanged = all(
            (profile / name).is_file()
            and hashlib.sha256((profile / name).read_bytes()).digest() == digest
            for name, digest in before.items()
        )
        print("G01_OWNED_LEGACY_PROFILE_UNCHANGED", unchanged, flush=True)
        assert owned.parent == root and owned.name.startswith(
            "columns-gui-owned-"
        ) and not owned.is_symlink()
        shutil.rmtree(owned)
        print("G01_OWNED_GUI_FIXTURE_CLEANED=YES", flush=True)
    print("G01_OWNED_SCENARIO_READY", scenario_ready, flush=True)
    print("G01_OWNED_NORMAL_CLOSE", proc.returncode == 0 and not timed_out,
          flush=True)
    return 0 if scenario_ready and proc.returncode == 0 and not timed_out else 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "Release",
                 sys.argv[2] if len(sys.argv) > 2 else "full"))
