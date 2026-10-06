"""Focused owned GUI acceptance for more-than-32 item transfer."""

from pathlib import Path
import ctypes as c
import os
import subprocess
import tempfile
import time
from ctypes import wintypes as W

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until


CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
assert CONFIG in ("Debug", "Release")
EXE = app_exe(CONFIG)
assert EXE.exists(), EXE

REAL_CONF, ORIGINAL_PROFILE = snapshot_legacy_profile()
base = ROOT / "logs" / "transfer-budget-gui"
base.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="transfer-budget-owned-", dir=base))
left = owned / "Left"
right = owned / "Right"
left.mkdir()
right.mkdir()
for index in range(64):
    (left / f"대량-{index:03d}.txt").write_text(
        f"owned bulk transfer {index}\n", encoding="utf-8"
    )
appdata = owned / "appdata"
localdata = owned / "localdata"
temp = owned / "tmp"
for folder in (appdata, localdata, temp):
    folder.mkdir()

u = c.windll.user32
CALL = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u.EnumWindows.argtypes = [CALL, W.LPARAM]
u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
u.GetForegroundWindow.restype = W.HWND
u.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, c.c_int]
u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]


def eventually(fn, label, seconds=10):
    scale = 1.5 if os.environ.get("GITHUB_ACTIONS") == "true" else 1.0
    return wait_until(fn, label, seconds=seconds * scale, interval=.13)


def owned_windows(pid):
    found = []

    @CALL
    def cb(hwnd, _):
        process = W.DWORD()
        u.GetWindowThreadProcessId(hwnd, c.byref(process))
        if process.value == pid and u.IsWindowVisible(hwnd):
            buf = c.create_unicode_buffer(700)
            u.GetWindowTextW(hwnd, buf, len(buf))
            found.append((int(hwnd), buf.value))
        return 1

    u.EnumWindows(cb, 0)
    return found


process = None
hwnd = None
try:
    env = {
        **os.environ,
        "APPDATA": str(appdata),
        "LOCALAPPDATA": str(localdata),
        "TEMP": str(temp),
        "TMP": str(temp),
    }
    process = subprocess.Popen(
        [str(EXE), str(left)],
        cwd=EXE.parent,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def main_window():
        return [
            (handle, title)
            for handle, title in owned_windows(process.pid)
            if "flyExplorer" in title
        ]

    eventually(
        lambda: len(main_window()) == 1 or process.poll() is not None,
        "owned flyExplorer window not discovered",
        18,
    )
    assert process.poll() is None, ("owned flyExplorer exited early", process.returncode)
    hwnd = main_window()[0][0]
    win = Desktop(backend="uia").window(handle=hwnd)

    def element(name):
        return win.child_window(auto_id=name)

    def focus():
        for _ in range(4):
            win.set_focus()
            time.sleep(.12)
            foreground = u.GetForegroundWindow()
            owner = W.DWORD()
            if foreground:
                u.GetWindowThreadProcessId(foreground, c.byref(owner))
            if owner.value == process.pid:
                return
        raise AssertionError("refusing physical input to a foreign window")

    def safe_click(target):
        focus()
        target.click_input()

    for key in ("AddressBox", "LeftFiles", "RightFiles", "CopyButton", "StatusText"):
        assert element(key).exists(timeout=5), ("missing owned control", key)

    eventually(
        lambda: str(left).lower() in element("AddressBox").get_value().lower(),
        "owned left route did not load",
        18,
    )

    def rows(side):
        return [
            row
            for row in element(side + "Files").descendants()
            if row.element_info.control_type == "ListItem"
        ]

    eventually(
        lambda: len(rows("Left")) >= 64,
        "64 owned source rows did not render",
        18,
    )

    # Point the independent right pane at an empty owned destination.
    right_surface = element("RightFiles")
    right_item = next(iter(rows("Right")), None)
    safe_click(right_item or right_surface)
    address = element("AddressBox")
    address.set_edit_text(str(right))
    focus()
    address.type_keys("{ENTER}", set_foreground=True)
    eventually(
        lambda: str(right).lower() in element("AddressBox").get_value().lower(),
        "owned right route did not load",
        18,
    )

    # Return to the left pane, select all 64 files, and invoke the normal Copy command.
    safe_click(element("LeftFiles"))
    focus()
    send_keys("^a")
    eventually(
        lambda: sum(bool(row.is_selected()) for row in rows("Left")) >= 64,
        "Ctrl+A did not select the 64 owned source rows",
        12,
    )
    safe_click(element("CopyButton"))

    eventually(
        lambda: sum(1 for path in right.iterdir() if path.is_file()) == 64,
        "64-item Shell copy did not commit",
        35,
    )
    for index in range(64):
        source = left / f"대량-{index:03d}.txt"
        copied = right / source.name
        assert source.is_file()
        assert copied.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")

    print("REAL_TRANSFER_BUDGET_SELECTED_64", True, flush=True)
    print("REAL_TRANSFER_BUDGET_COPY_64_PASS", True, flush=True)
finally:
    if process and process.poll() is None:
        if hwnd:
            owner = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, c.byref(owner))
            assert owner.value == process.pid, "refuse WM_CLOSE on foreign window"
            assert u.PostMessageW(hwnd, 0x10, 0, 0), "owned WM_CLOSE failed"
        try:
            process.wait(timeout=14)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
            raise AssertionError("owned transfer-budget probe did not close normally")
    if process:
        assert process.returncode == 0, process.returncode
    assert_legacy_profile_unchanged(REAL_CONF, ORIGINAL_PROFILE)

print("TRANSFER_BUDGET_GUI_ACCEPTANCE=PASS", flush=True)
