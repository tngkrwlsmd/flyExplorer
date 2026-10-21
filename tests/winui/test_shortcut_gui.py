"""Focused owned GUI acceptance for non-mutating F5/F6 semantics."""

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
from profile_guard import (
    assert_legacy_profile_unchanged,
    snapshot_legacy_profile,
)
from uia_polling import wait_until


CONFIG = os.environ.get("FLY_MIGRATION_CONFIGURATION", "Release")
assert CONFIG in ("Debug", "Release")
EXE = app_exe(CONFIG)
assert EXE.exists(), EXE

REAL_CONF, ORIGINAL_PROFILE = snapshot_legacy_profile()
base = ROOT / "logs" / "shortcut-gui"
base.mkdir(parents=True, exist_ok=True)
owned = Path(tempfile.mkdtemp(prefix="f5-f6-owned-", dir=base))
left = owned / "Left"
right = owned / "Right"
source = left / "F5-새로고침-원본"
secondary = right / "F6-오른쪽-표식"
for folder in (source, secondary):
    folder.mkdir(parents=True, exist_ok=True)
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
        return [(handle, title) for handle, title in owned_windows(process.pid)
                if "flyExplorer" in title]

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
                return True
        raise AssertionError("refusing physical input to a foreign window")

    def safe_click(target):
        focus()
        target.click_input()

    for key in ("AddressBox", "LeftFiles", "RightFiles", "StatusText"):
        assert element(key).exists(timeout=5), ("missing owned control", key)

    def row(side_id, expected_name):
        return next(
            (
                entry for entry in element(side_id).descendants()
                if entry.element_info.control_type == "ListItem"
                and expected_name in entry.window_text()
            ),
            None,
        )

    def visit(side_id, path, expected_name):
        safe_click(element(side_id))
        address = element("AddressBox")
        address.set_edit_text(str(path))
        focus()
        address.type_keys("{ENTER}", set_foreground=True)
        eventually(
            lambda: str(path).rstrip("\\/").casefold()
            in element("AddressBox").get_value().rstrip("\\/").casefold(),
            "owned pane route did not load: " + side_id,
            18,
        )
        eventually(
            lambda: row(side_id, expected_name) is not None,
            "owned row did not render after explicit route: " + expected_name,
            18,
        )

    # Reassert both owned routes explicitly. AddressBox navigation can replace
    # WinUI list peers, so do not rely on the startup peer or an earlier pane
    # activation when preparing the focused shortcut fixture.
    visit("LeftFiles", left, source.name)
    visit("RightFiles", right, secondary.name)
    visit("LeftFiles", left, source.name)

    # F5: return to left, select a real filesystem row and physically press F5.
    left_surface = element("LeftFiles")
    left_item = row("LeftFiles", source.name)
    assert left_item is not None
    safe_click(left_item)
    left_item.select()
    focus()
    send_keys("{F5}")
    eventually(
        lambda: "폴더 변경 알림을 반영했습니다." in
                element("StatusText").window_text(),
        "plain F5 did not complete active-pane refresh",
        15,
    )
    time.sleep(.5)
    assert source.is_dir()
    assert not (right / source.name).exists(), (
        "plain F5 must not invoke historical cross-pane copy"
    )
    print("REAL_F5_REFRESH_NO_FILE_MUTATION", True, flush=True)

    # F6: split view must traverse between panes without moving the selected item.
    safe_click(element("LeftFiles"))
    focus()
    send_keys("{F6}")
    eventually(
        lambda: str(right).lower() in element("AddressBox").get_value().lower(),
        "plain F6 did not activate the right pane",
        10,
    )
    assert source.is_dir()
    assert not (right / source.name).exists(), (
        "plain F6 must not invoke historical cross-pane move"
    )
    focus()
    send_keys("{F6}")
    eventually(
        lambda: str(left).lower() in element("AddressBox").get_value().lower(),
        "second plain F6 did not return activation to the left pane",
        10,
    )
    print("REAL_F6_DUAL_PANE_FOCUS_NO_FILE_MUTATION", True, flush=True)

    # A selected PaneTab must keep keyboard focus after the model/chrome
    # refresh. Otherwise the next Enter can activate a column sort button.
    def pane_tabs(tabs_id):
        return element(tabs_id).descendants(control_type="TabItem")

    def selected_and_focused(tabs_id, index):
        items = pane_tabs(tabs_id)
        return (len(items) == 2
                and bool(items[index].iface_selection_item.CurrentIsSelected)
                and bool(items[index].element_info.element.CurrentHasKeyboardFocus))

    for files_id, tabs_id in (("LeftFiles", "LeftTabs"), ("RightFiles", "RightTabs")):
        safe_click(element(files_id))
        safe_click(element("NewTabButton"))
        eventually(lambda: len(pane_tabs(tabs_id)) == 2,
                   "second owned folder tab missing: " + tabs_id)
        safe_click(pane_tabs(tabs_id)[1])
        for keys, index in (("{LEFT}{ENTER}", 0), ("{RIGHT}{ENTER}", 1)):
            focus()
            send_keys(keys, pause=.12)
            eventually(lambda: selected_and_focused(tabs_id, index),
                       "folder-tab activation lost keyboard focus: " + tabs_id)
            # Check again after queued Shell publications have had time to run.
            time.sleep(.35)
            assert selected_and_focused(tabs_id, index), tabs_id
        print("REAL_PANE_TAB_KEYBOARD_FOCUS_RETAINED", tabs_id, True, flush=True)

    # Ctrl+L and Ctrl+F focus the existing controls; neither opens a
    # folder, starts a search, mutates selected files or steals foreground.
    focus()
    send_keys("^l")
    eventually(
        lambda: element("AddressBox").has_keyboard_focus(),
        "Ctrl+L did not focus the existing address editor", 7,
    )
    assert source.is_dir() and secondary.is_dir()
    assert not (right / source.name).exists()
    print("REAL_CTRL_L_ADDRESS_FOCUS_NO_FILE_MUTATION", True, flush=True)

    focus()
    send_keys("^f")
    eventually(
        lambda: element("QuickSearchBox").has_keyboard_focus(),
        "Ctrl+F did not focus the existing quick search box", 7,
    )
    assert source.is_dir() and secondary.is_dir()
    assert not (right / source.name).exists()
    print("REAL_CTRL_F_QUICK_SEARCH_FOCUS_NO_FILE_MUTATION", True, flush=True)

    # User changes only a disposable private profile, never system shortcuts.
    safe_click(element("WorkspacePanelButton"))
    address_shortcut = element("AddressShortcutBox")
    search_shortcut = element("SearchShortcutBox")
    eventually(
        lambda: address_shortcut.is_visible() and search_shortcut.is_visible(),
        "bounded shortcut editor not visible", 7,
    )
    address_shortcut.select(1)  # Ctrl+E
    search_shortcut.select(3)   # Ctrl+K
    safe_click(element("ApplyShortcutButton"))
    private = localdata / "flyExplorer" / "ui-preferences-v1.txt"
    eventually(
        lambda: private.is_file() and b"address-shortcut=1" in private.read_bytes()
        and b"search-shortcut=3" in private.read_bytes(),
        "custom focus shortcuts not durably saved", 9,
    )
    focus()
    send_keys("^e")
    eventually(
        lambda: element("AddressBox").has_keyboard_focus(),
        "custom Ctrl+E did not focus address editor", 7,
    )
    focus()
    send_keys("^k")
    eventually(
        lambda: element("QuickSearchBox").has_keyboard_focus(),
        "custom Ctrl+K did not focus quick search", 7,
    )
    print("REAL_CUSTOM_FOCUS_SHORTCUTS_SAVED_APPLIED", True, flush=True)

    # A duplicate binding must fail closed and keep the last saved values.
    address_shortcut.select(4)  # new Ctrl+G
    search_shortcut.select(4)   # duplicate Ctrl+G
    safe_click(element("ApplyShortcutButton"))
    eventually(
        lambda: "서로 다른 Ctrl 단축키" in element("StatusText").window_text(),
        "duplicate Ctrl+G binding did not report a collision", 7,
    )
    assert b"address-shortcut=1" in private.read_bytes()
    assert b"search-shortcut=3" in private.read_bytes()

    # Both newly added choices must persist and dispatch from physical keys.
    search_shortcut.select(5)  # new Ctrl+J
    safe_click(element("ApplyShortcutButton"))
    eventually(
        lambda: private.is_file() and b"address-shortcut=4" in private.read_bytes()
        and b"search-shortcut=5" in private.read_bytes(),
        "extended Ctrl+G / Ctrl+J shortcuts not durably saved", 9,
    )
    focus()
    send_keys("^g")
    eventually(
        lambda: element("AddressBox").has_keyboard_focus(),
        "custom Ctrl+G did not focus address editor", 7,
    )
    focus()
    send_keys("^j")
    eventually(
        lambda: element("QuickSearchBox").has_keyboard_focus(),
        "custom Ctrl+J did not focus quick search", 7,
    )
    assert source.is_dir() and secondary.is_dir()
    assert not (right / source.name).exists()
    print("REAL_EXTENDED_FOCUS_SHORTCUTS_NO_FILE_MUTATION", True, flush=True)

    safe_click(element("ResetShortcutButton"))
    eventually(
        lambda: private.is_file() and b"address-shortcut=0" in private.read_bytes()
        and b"search-shortcut=2" in private.read_bytes(),
        "default focus shortcuts not durably restored", 9,
    )
    focus()
    send_keys("^l")
    eventually(
        lambda: element("AddressBox").has_keyboard_focus(),
        "reset Ctrl+L did not refocus address editor", 7,
    )
    focus()
    send_keys("^f")
    eventually(
        lambda: element("QuickSearchBox").has_keyboard_focus(),
        "reset Ctrl+F did not refocus quick search", 7,
    )
    assert source.is_dir() and secondary.is_dir()
    assert not (right / source.name).exists()
    print("REAL_CUSTOM_FOCUS_SHORTCUTS_RESET", True, flush=True)
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
            raise AssertionError("owned shortcut probe did not close normally")
    if process:
        assert process.returncode == 0, process.returncode
    assert_legacy_profile_unchanged(REAL_CONF, ORIGINAL_PROFILE)

print("SHORTCUT_GUI_ACCEPTANCE=PASS", flush=True)
