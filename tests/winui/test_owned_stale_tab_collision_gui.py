"""Prove a stale Copy-collision dialog cannot mutate a different active tab.

Exercises real WinUI tab selection while the dialog is visible, with synthetic
files and an isolated app profile. No global Recycle Bin or clipboard actions.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

import psutil
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until

user32 = ctypes.windll.user32
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowThreadProcessId.argtypes = (
    wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
)
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.PostMessageW.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
)
user32.PostMessageW.restype = wintypes.BOOL


def foreground_owned(pid):
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    owner = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    return owner.value == pid


def focus_owned(win, pid):
    win.set_focus()
    wait_until(lambda: foreground_owned(pid), "owned app not in foreground",
               seconds=7, interval=.15)


def run(config="Debug"):
    assert config in ("Debug", "Release")
    exe = app_exe(config)
    assert exe.is_file()
    real_root, original_profile = snapshot_legacy_profile()
    base = ROOT / "logs" / "collision-stale-tab-focused-gui"
    base.mkdir(parents=True, exist_ok=True)
    assert not base.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="staletab-owned-", dir=base))
    left, right, alternate = (owned / "Left", owned / "Right",
                              owned / "Alternate")
    for path in (left, right, alternate):
        path.mkdir()
    name = "OwnedCollisionCopy.txt"
    source_bytes = b"owned copy source - must remain"
    target_bytes = b"pre-existing target - never overwrite"
    source = left / name
    target = right / name
    source.write_bytes(source_bytes)
    target.write_bytes(target_bytes)
    profile = {}
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        folder = owned / key.lower()
        folder.mkdir()
        profile[key] = str(folder)
    env = {**os.environ, **profile}
    process = None
    hwnd = None
    passed = False
    try:
        process = subprocess.Popen(
            [str(exe), str(left)], cwd=exe.parent, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def main_window():
            assert process.poll() is None, (
                "test-owned WinUI exited prematurely", process.returncode,
            )
            assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
            candidates = [
                w for w in Desktop(backend="uia").windows(process=process.pid)
                if "flyExplorer" in w.window_text()
            ]
            return (Desktop(backend="uia").window(handle=candidates[0].handle)
                    if len(candidates) == 1 else None)

        win = wait_until(main_window, "test-owned flyExplorer HWND not found",
                         seconds=22, interval=.2)
        hwnd = win.handle
        assert win.element_info.process_id == process.pid
        address = win.child_window(auto_id="AddressBox")
        leftfiles = win.child_window(auto_id="LeftFiles")
        rightfiles = win.child_window(auto_id="RightFiles")
        copy_button = win.child_window(auto_id="CopyButton")
        status = win.child_window(auto_id="StatusText")
        tabs = win.child_window(auto_id="LeftTabs")
        add_tab = win.child_window(auto_id="NewTabButton")

        def row(panel, text):
            hits = [
                item for item in panel.descendants()
                if item.element_info.control_type == "ListItem"
                and text in item.window_text()
                and item.element_info.process_id == process.pid
            ]
            return hits[0] if len(hits) == 1 else None

        wait_until(
            lambda: str(left).casefold() in address.get_value().casefold()
            and row(leftfiles, name) is not None,
            "left test-owned source did not load",
            seconds=20, interval=.2,
        )
        # Route the OTHER pane explicitly; only the test-owned app gets input.
        focus_owned(win, process.pid)
        rightfiles.click_input()
        focus_owned(win, process.pid)
        send_keys("^l")
        wait_until(
            lambda: address.is_visible(),
            "address edit not visible for right pane",
            seconds=7, interval=.15,
        )
        address.set_edit_text(str(right))
        focus_owned(win, process.pid)
        address.set_focus()
        assert foreground_owned(process.pid)
        send_keys("{ENTER}")
        wait_until(
            lambda: str(right).casefold() in address.get_value().casefold()
            and row(rightfiles, name) is not None,
            "right test-owned collision folder did not load",
            seconds=18, interval=.2,
        )
        print("STALE_TAB_OWNED_DUAL_PANE_READY=PASS", flush=True)

        def choose_source():
            item = wait_until(
                lambda: row(leftfiles, name), "source row not loaded",
                seconds=9, interval=.2,
            )
            focus_owned(win, process.pid)
            item.click_input()
            item.iface_selection_item.Select()
            wait_until(
                lambda: row(leftfiles, name).is_selected(),
                "source row did not select", seconds=6, interval=.15,
            )
            assert source.read_bytes() == source_bytes
            assert target.read_bytes() == target_bytes

        def modal_button(label):
            children = win.descendants()
            matches = [
                item for item in children
                if item.element_info.control_type == "Button"
                and item.window_text().strip() == label
                and item.element_info.process_id == process.pid
                and item.is_visible()
            ]
            return matches[0] if len(matches) == 1 else None

        def collision_modal():
            # Native WinUI ContentDialog appears inside the exact owned HWND.
            visible_text = [
                item.window_text() for item in win.descendants()
                if item.element_info.process_id == process.pid
                and item.is_visible()
            ]
            if not any("동일한 이름이 이미 존재합니다" in text
                       for text in visible_text):
                return None
            return modal_button("취소")

        def start_collision():
            choose_source()
            assert copy_button.is_enabled()
            assert copy_button.element_info.process_id == process.pid
            focus_owned(win, process.pid)
            copy_button.iface_invoke.Invoke()
            return wait_until(
                collision_modal,
                "owned collision ContentDialog did not become visible",
                seconds=23, interval=.2,
            )

        # Create another *left* tab pointing at an owned empty folder before
        # showing a modal. A tab switch later must change the path AND tab ID.
        choose_source()
        focus_owned(win, process.pid)
        assert add_tab.element_info.process_id == process.pid
        add_tab.iface_invoke.Invoke()

        def tab_items():
            return [
                item for item in tabs.descendants()
                if item.element_info.control_type == "TabItem"
                and item.element_info.process_id == process.pid
            ]

        wait_until(lambda: len(tab_items()) == 2,
                   "left tab creation did not yield two owned TabItems",
                   seconds=11, interval=.2)
        focus_owned(win, process.pid)
        send_keys("^l")
        wait_until(lambda: address.is_visible(),
                   "address edit missing in second tab",
                   seconds=7, interval=.15)
        address.set_edit_text(str(alternate))
        focus_owned(win, process.pid)
        address.set_focus()
        assert foreground_owned(process.pid)
        send_keys("{ENTER}")
        wait_until(
            lambda: str(alternate).casefold() in address.get_value().casefold(),
            "second left tab did not navigate to owned alternate folder",
            seconds=15, interval=.2,
        )
        tab_items()[0].iface_selection_item.Select()
        wait_until(
            lambda: str(left).casefold() in address.get_value().casefold()
            and row(leftfiles, name) is not None,
            "first left tab did not restore owned source",
            seconds=12, interval=.2,
        )
        print("STALE_TAB_TWO_DIFFERENT_OWNED_ROUTES_READY=PASS", flush=True)

        # Start one collision on the first tab, then programmatically select
        # the second UIA TabItem while the real ContentDialog is still visible.
        # Crucially, the primary button must NEVER be invoked until the
        # underlying live address has changed to the owned alternate folder.
        start_collision()
        assert modal_button("이름 바꿔 둘 다 유지") is not None
        assert sorted(p.name for p in right.iterdir()) == [name]
        assert source.read_bytes() == source_bytes
        assert target.read_bytes() == target_bytes
        tab_items()[1].iface_selection_item.Select()
        wait_until(
            lambda: str(alternate).casefold() in address.get_value().casefold()
            and row(leftfiles, name) is None,
            "pending modal did not allow a real active-tab route change",
            seconds=10, interval=.2,
        )
        print("STALE_TAB_ROUTE_CHANGED_UNDER_VISIBLE_MODAL=PASS", flush=True)
        approve = modal_button("이름 바꿔 둘 다 유지")
        assert approve is not None, "dialog did not survive tab switch"
        approve.iface_invoke.Invoke()
        wait_until(
            lambda: "확인하는 동안 원본 또는 대상 폴더가 변경됐습니다." in
            status.window_text(),
            "stale collision approval was not rejected",
            seconds=9, interval=.2,
        )
        for _ in range(8):
            assert source.read_bytes() == source_bytes
            assert target.read_bytes() == target_bytes
            assert sorted(p.name for p in right.iterdir()) == [name]
            assert list(alternate.iterdir()) == []
            time.sleep(.15)
        print("STALE_TAB_APPROVAL_REJECTED_NO_FILE_MUTATION=PASS", flush=True)
        passed = True
    finally:
        if process is not None and process.poll() is None:
            assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
            if hwnd:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
                try:
                    process.wait(timeout=7)
                except subprocess.TimeoutExpired:
                    pass
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            assert process.poll() is not None
        assert_legacy_profile_unchanged(real_root, original_profile)
        assert owned.parent == base and owned.name.startswith("staletab-owned-")
        assert not owned.is_symlink() and not base.is_symlink()
        shutil.rmtree(owned)
        print("STALE_TAB_OWNED_FIXTURE_CLEANED=YES", flush=True)
        print("STALE_TAB_LEGACY_PROFILE_UNCHANGED=YES", flush=True)
    assert passed
    print("STALE_TAB_COLLISION_REAL_GUI_PASS=True", flush=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "Debug")
