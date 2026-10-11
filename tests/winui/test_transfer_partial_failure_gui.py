"""Owned WinUI partial-copy failure acceptance; no real user files touched."""
from pathlib import Path
import ctypes as c
from ctypes import wintypes as W
import os
import shutil
import subprocess
import tempfile
import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from paths import ROOT, app_exe
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until

CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
EXE = app_exe(CONFIG)
assert EXE.is_file(), EXE
REAL_CONF, PREVIOUS = snapshot_legacy_profile()
logs = ROOT / "logs" / "transfer-partial-failure"
logs.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="partial-owned-", dir=logs))
left, right = owned / "Left", owned / "Right"
left.mkdir()
right.mkdir()
source_first = left / "a-first.txt"
source_locked = left / "z-locked.txt"
source_first.write_bytes(b"owned-first-unaltered")
source_locked.write_bytes(b"owned-second-unaltered")
for name in ("appdata", "localdata", "tmp"):
    (owned / name).mkdir()
env = {**os.environ, "APPDATA": str(owned/"appdata"),
       "LOCALAPPDATA": str(owned/"localdata"),
       "TEMP": str(owned/"tmp"), "TMP": str(owned/"tmp")}
u = c.windll.user32
k = c.windll.kernel32
CALL = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u.EnumWindows.argtypes = [CALL, W.LPARAM]
u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
u.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, c.c_int]
u.GetForegroundWindow.restype = W.HWND
u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, c.c_void_p,
                          W.DWORD, W.DWORD, W.HANDLE]
k.CreateFileW.restype = W.HANDLE
k.CloseHandle.argtypes = [W.HANDLE]
k.CloseHandle.restype = W.BOOL
INVALID = c.c_void_p(-1).value
process = None
hwnd = None
lock = None
try:
    process = subprocess.Popen([str(EXE), str(left)], cwd=EXE.parent,
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    def windows():
        found = []
        @CALL
        def callback(handle, _):
            owner = W.DWORD()
            u.GetWindowThreadProcessId(handle, c.byref(owner))
            if owner.value == process.pid and u.IsWindowVisible(handle):
                name = c.create_unicode_buffer(300)
                u.GetWindowTextW(handle, name, len(name))
                if "flyExplorer" in name.value:
                    found.append(int(handle))
            return 1
        u.EnumWindows(callback, 0)
        return found
    def eventually(fn, label, seconds=18):
        scale = 1.5 if os.environ.get("GITHUB_ACTIONS") == "true" else 1
        return wait_until(fn, label, seconds=seconds*scale, interval=.12)
    eventually(lambda: len(windows()) == 1 or process.poll() is not None,
               "owned app not launched")
    assert process.poll() is None
    hwnd = windows()[0]
    win = Desktop(backend="uia").window(handle=hwnd)
    def element(name):
        return win.child_window(auto_id=name)
    def focus():
        for _ in range(4):
            win.set_focus()
            time.sleep(.10)
            active = u.GetForegroundWindow()
            owner = W.DWORD()
            if active:
                u.GetWindowThreadProcessId(active, c.byref(owner))
            if owner.value == process.pid:
                return
        raise AssertionError("refusing foreign-window keyboard input")
    def click(target):
        focus()
        target.click_input()
    for name in ("AddressBox", "LeftFiles", "RightFiles", "CopyButton",
                 "StatusText"):
        assert element(name).exists(timeout=6), name
    eventually(lambda: str(left).lower() in element("AddressBox").get_value().lower(),
               "left source navigation")
    def row_names(side):
        return [x.window_text() for x in element(side+"Files").descendants()
                if x.element_info.control_type == "ListItem"]
    eventually(lambda: any("a-first.txt" in name for name in row_names("Left"))
               and any("z-locked.txt" in name for name in row_names("Left")),
               "both owned source rows missing")
    right_view = element("RightFiles")
    click(right_view)
    address = element("AddressBox")
    address.set_edit_text(str(right))
    focus()
    address.type_keys("{ENTER}", set_foreground=True)
    eventually(lambda: str(right).lower() in element("AddressBox").get_value().lower(),
               "right destination navigation")
    click(element("LeftFiles"))
    focus()
    send_keys("^a")
    lock = k.CreateFileW(str(source_locked), 0x80000000, 0, None, 3, 0x80, None)
    assert lock != INVALID, ("failed to lock test-owned file", c.get_last_error())
    click(element("CopyButton"))
    eventually(lambda: (right/"a-first.txt").is_file(), "first item never copied", 22)
    assert (right/"a-first.txt").read_bytes() == b"owned-first-unaltered"
    assert source_first.read_bytes() == b"owned-first-unaltered"
    eventually(lambda: "일부 항목이 처리됐을 수 있습니다" in
               element("StatusText").window_text(),
               "partial failure warning was not projected", 18)
    assert k.CloseHandle(lock)
    lock = None
    assert source_locked.read_bytes() == b"owned-second-unaltered"
    eventually(lambda: any("a-first.txt" in name for name in row_names("Right")),
               "right pane did not show first successful item after failure", 18)
    print("REAL_PARTIAL_BATCH_FIRST_COMMITTED=PASS", flush=True)
    print("REAL_PARTIAL_BATCH_SECOND_LOCKED=PASS", flush=True)
    print("REAL_PARTIAL_BATCH_SOURCE_BYTES_PRESERVED=PASS", flush=True)
    print("REAL_PARTIAL_FAILURE_VISIBLE_WARNING=PASS", flush=True)
    print("REAL_PARTIAL_FAILURE_PANE_REFRESH=PASS", flush=True)
    screen = logs/"partial-failure-window.png"
    win.capture_as_image().save(screen)
    print("REAL_PARTIAL_FAILURE_SCREENSHOT="+str(screen), flush=True)
finally:
    if lock and lock != INVALID:
        assert k.CloseHandle(lock)
    if process and process.poll() is None:
        if hwnd:
            pid = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, c.byref(pid))
            assert pid.value == process.pid, "refuse closing foreign window"
            assert u.PostMessageW(hwnd, 0x10, 0, 0)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
            raise AssertionError("owned app did not close normally")
    if process:
        assert process.returncode == 0, process.returncode
    assert_legacy_profile_unchanged(REAL_CONF, PREVIOUS)
    shutil.rmtree(owned)
print("PARTIAL_TRANSFER_OWNED_GUI_ACCEPTANCE=PASS", flush=True)
