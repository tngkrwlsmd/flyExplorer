"""Physical flyExplorer -> fresh test-owned Windows Explorer drag acceptance.

The harness creates one owned source file and one owned destination folder.
It never interacts with pre-existing Explorer windows, the user's clipboard,
Recycle Bin, or personal files.
"""

from pathlib import Path
import ctypes as c
from ctypes import wintypes as W
import os
import subprocess
import tempfile
import time

from pywinauto import Desktop, mouse

from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until


CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
assert CONFIG in ("Debug", "Release")
EXE = app_exe(CONFIG)
assert EXE.is_file(), EXE

REAL_CONF, ORIGINAL_PROFILE = snapshot_legacy_profile()
base = ROOT / "logs" / "outbound-drag-gui"
base.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="outbound-drag-owned-", dir=base))
source_dir = owned / "source"
destination_dir = owned / "destination"
source_dir.mkdir()
destination_dir.mkdir()
source = source_dir / "외부끌기-한글.txt"
source.write_text("owned outbound drag\n", encoding="utf-8")

env = os.environ.copy()
for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
    folder = owned / key.lower()
    folder.mkdir()
    env[key] = str(folder)
env["FLY_M23_OWNED_DRAG_TRACE"] = "YES"

u = c.WinDLL("user32", use_last_error=True)
u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
u.GetWindowThreadProcessId.restype = W.DWORD
u.GetForegroundWindow.restype = W.HWND
u.GetAncestor.argtypes = [W.HWND, W.UINT]
u.GetAncestor.restype = W.HWND
u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u.PostMessageW.restype = W.BOOL
u.SetWindowPos.argtypes = [
    W.HWND, W.HWND, c.c_int, c.c_int, c.c_int, c.c_int, W.UINT
]
u.SetWindowPos.restype = W.BOOL
SWP_NOZORDER = 0x0004
SWP_SHOWWINDOW = 0x0040


def eventually(fn, label, seconds=15):
    return wait_until(fn, label, seconds=seconds, interval=.16)


def foreground_root():
    hwnd = u.GetForegroundWindow()
    return int(u.GetAncestor(hwnd, 2)) if hwnd else 0


def focus_owned(window, hwnd, allowed_pid=None):
    window.set_focus()
    eventually(lambda: foreground_root() == int(hwnd),
               "foreground ownership changed; no physical input delivered", 5)
    if allowed_pid is not None:
        pid = W.DWORD()
        u.GetWindowThreadProcessId(W.HWND(hwnd), c.byref(pid))
        assert pid.value == allowed_pid, "owned flyExplorer HWND PID mismatch"


preview = None
winui = None
explorer = None
owned_explorer = None
owned_explorer_hwnd = None
try:
    import psutil
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("Shell.Application")
    preexisting = {int(item.HWND) for item in shell.Windows()}
    print("OUTBOUND_DRAG_PREEXISTING_EXPLORER_COUNT_ONLY",
          len(preexisting), flush=True)

    preview = subprocess.Popen(
        [str(EXE), str(source_dir)],
        cwd=EXE.parent,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def ready_winui():
        global winui
        if preview.poll() is not None:
            return False
        if Path(psutil.Process(preview.pid).exe()).resolve() != EXE.resolve():
            raise AssertionError("flyExplorer process ownership mismatch")
        candidates = [
            item for item in Desktop(backend="uia").windows(process=preview.pid)
            if "flyExplorer" in item.window_text()
        ]
        if len(candidates) != 1:
            return False
        winui = Desktop(backend="uia").window(handle=candidates[0].handle)
        return winui.child_window(auto_id="LeftFiles").exists(timeout=.2)

    eventually(ready_winui, "owned flyExplorer window not ready", 22)

    shell.Explore(str(destination_dir))
    target_url = destination_dir.resolve().as_uri().rstrip("/").casefold()

    def ready_explorer():
        global explorer, owned_explorer, owned_explorer_hwnd
        found = []
        for item in shell.Windows():
            try:
                if int(item.HWND) not in preexisting and \
                   str(item.LocationURL).rstrip("/").casefold() == target_url:
                    found.append(item)
            except Exception:
                pass
        if len(found) != 1:
            return False
        owned_explorer = found[0]
        owned_explorer_hwnd = int(owned_explorer.HWND)
        explorer = Desktop(backend="uia").window(handle=owned_explorer_hwnd)
        return explorer.exists(timeout=.2)

    eventually(
        ready_explorer,
        "no uniquely new Explorer window for owned destination", 20
    )
    assert owned_explorer_hwnd not in preexisting
    print("OUTBOUND_DRAG_FRESH_EXPLORER_IDENTIFIED", True, flush=True)

    # Keep both exact owned windows simultaneously visible for the physical drag.
    assert u.SetWindowPos(
        W.HWND(winui.handle), W.HWND(0), 18, 75, 590, 620,
        SWP_NOZORDER | SWP_SHOWWINDOW
    )
    assert u.SetWindowPos(
        W.HWND(owned_explorer_hwnd), W.HWND(0), 650, 75, 600, 620,
        SWP_NOZORDER | SWP_SHOWWINDOW
    )
    time.sleep(.5)

    left = winui.child_window(auto_id="LeftFiles")

    def source_row():
        return next(
            (
                row for row in left.descendants()
                if row.element_info.control_type == "ListItem"
                and source.name in row.window_text()
            ),
            None,
        )

    eventually(lambda: source_row() is not None,
               "owned outbound source row not rendered", 18)
    row = source_row()
    row.select()
    eventually(lambda: source_row() is not None and source_row().is_selected(),
               "owned outbound source row not selected", 6)

    origin = row.rectangle().mid_point()
    er = explorer.rectangle()
    # A blank point well inside Explorer's file-content region, away from
    # navigation pane, title/command bars and window edges.
    target = (
        er.left + int(er.width() * .72),
        er.top + int(er.height() * .62),
    )

    focus_owned(winui, winui.handle, preview.pid)
    mouse.move(coords=(origin.x, origin.y))
    mouse.press(button="left", coords=(origin.x, origin.y))
    try:
        time.sleep(.14)
        mouse.move(coords=(origin.x + 30, origin.y + 20))
        time.sleep(.26)
        mouse.move(coords=target)
        time.sleep(.55)
    finally:
        mouse.release(button="left", coords=target)

    copied = destination_dir / source.name
    eventually(lambda: copied.is_file(),
               "Explorer did not receive outbound StorageItems copy", 20)
    assert copied.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
    assert source.is_file(), "copy-only outbound drag must preserve source"

    print("REAL_OUTBOUND_STORAGEITEMS_EXPLORER_COPY", True, flush=True)
    print("REAL_OUTBOUND_DRAG_SOURCE_PRESERVED", True, flush=True)
    print("OUTBOUND_DRAG_EXPLORER_ACCEPTANCE=PASS", flush=True)
finally:
    if owned_explorer_hwnd is not None:
        assert owned_explorer_hwnd not in (
            locals().get("preexisting") or set()
        ), "refuse closing pre-existing Explorer window"
        u.PostMessageW(W.HWND(owned_explorer_hwnd), 0x10, 0, 0)
    if preview and preview.poll() is None:
        hwnd = winui.handle if winui is not None else 0
        if hwnd:
            pid = W.DWORD()
            u.GetWindowThreadProcessId(W.HWND(hwnd), c.byref(pid))
            assert pid.value == preview.pid, "refuse closing foreign window"
            assert u.PostMessageW(W.HWND(hwnd), 0x10, 0, 0)
        try:
            preview.wait(timeout=14)
        except subprocess.TimeoutExpired:
            preview.terminate()
            preview.wait(timeout=5)
            raise AssertionError("owned flyExplorer did not close normally")
    if preview:
        assert preview.returncode == 0, preview.returncode
    assert_legacy_profile_unchanged(REAL_CONF, ORIGINAL_PROFILE)
