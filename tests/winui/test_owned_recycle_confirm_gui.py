"""Real owned WinUI Recycle confirmation: Cancel and Escape must not delete files.

No Recycle Bin mutation: this test never approves the destructive primary action.
All files, app profiles and UI input are strictly test-owned.
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


def owned_foreground(pid):
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    owner = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    return owner.value == pid


def focus_owned(win, pid):
    win.set_focus()
    wait_until(lambda: owned_foreground(pid), "test-owned app not foreground",
               seconds=7, interval=.15)


def run(config="Debug", via_ctrl_d=False):
    assert config in ("Debug", "Release")
    exe = app_exe(config)
    assert exe.is_file()
    real_root, real_settings = snapshot_legacy_profile()
    base = ROOT / "logs" / "recycle-confirm-focused-gui"
    base.mkdir(parents=True, exist_ok=True)
    assert not base.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="recycle-owned-", dir=base))
    folder = owned / "Source"
    folder.mkdir()
    source = folder / "OwnedRecycleCancel.txt"
    other = folder / "OwnedRecycleUntouched.txt"
    first_bytes = b"synthetic recycle cancellation source"
    other_bytes = b"synthetic untouched control"
    source.write_bytes(first_bytes)
    other.write_bytes(other_bytes)

    profile = {}
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        entry = owned / key.lower()
        entry.mkdir()
        profile[key] = str(entry)
    env = {**os.environ, **profile}
    process = None
    hwnd = None
    passed = False
    try:
        process = subprocess.Popen(
            [str(exe), str(folder)], cwd=exe.parent, env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        def window():
            assert process.poll() is None, (
                "test-owned WinUI exited", process.returncode,
            )
            assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
            candidates = [
                item for item in Desktop(backend="uia").windows(process=process.pid)
                if "flyExplorer" in item.window_text()
            ]
            return (Desktop(backend="uia").window(handle=candidates[0].handle)
                    if len(candidates) == 1 else None)

        win = wait_until(
            window, "owned flyExplorer window not visible",
            seconds=22, interval=.2,
        )
        hwnd = win.handle
        assert win.element_info.process_id == process.pid
        address = win.child_window(auto_id="AddressBox")
        files = win.child_window(auto_id="LeftFiles")
        recycle = win.child_window(auto_id="RecycleButton")
        status = win.child_window(auto_id="StatusText")

        def row(label):
            hits = [
                item for item in files.descendants()
                if item.element_info.control_type == "ListItem"
                and label in item.window_text()
                and item.element_info.process_id == process.pid
            ]
            return hits[0] if len(hits) == 1 else None

        wait_until(
            lambda: str(folder).casefold() in address.get_value().casefold()
            and row(source.name) is not None
            and row(other.name) is not None,
            "owned folder not loaded", seconds=18, interval=.2,
        )

        def visible_modal_buttons(label):
            return [
                item for item in win.descendants()
                if item.element_info.control_type == "Button"
                and item.window_text().strip() == label
                and item.element_info.process_id == process.pid
                and item.is_visible()
            ]

        def cancel_button():
            # Title and primary label distinguish our app-owned modal.
            if len(visible_modal_buttons("휴지통으로 보내기")) != 1:
                return None
            matches = visible_modal_buttons("취소")
            return matches[0] if len(matches) == 1 else None

        def select_and_prompt(shortcut=False):
            item = wait_until(lambda: row(source.name),
                              "owned recycle row disappeared",
                              seconds=8, interval=.2)
            focus_owned(win, process.pid)
            item.click_input()
            item.iface_selection_item.Select()
            assert row(source.name).is_selected()
            assert recycle.is_enabled()
            assert recycle.element_info.process_id == process.pid
            focus_owned(win, process.pid)
            if shortcut:
                # Genuine file-row key route; never authorize the Recycle dialog.
                item.set_focus()
                assert owned_foreground(process.pid)
                send_keys("^d")
            else:
                recycle.iface_invoke.Invoke()
            cancel = wait_until(
                cancel_button, "owned recycle ContentDialog did not appear",
                seconds=10, interval=.2,
            )
            assert source.read_bytes() == first_bytes
            assert other.read_bytes() == other_bytes
            assert sorted(p.name for p in folder.iterdir()) == sorted([
                source.name, other.name
            ])
            return cancel

        # Explicit Cancel must fail closed without sending to global Recycle Bin.
        first = select_and_prompt(via_ctrl_d)
        first.iface_invoke.Invoke()
        wait_until(
            lambda: not bool(cancel_button()),
            "Recycle Cancel did not close the owned modal",
            seconds=8, interval=.2,
        )
        wait_until(
            lambda: "파일 작업 확인을 취소했습니다." in status.window_text(),
            "Recycle cancel was not acknowledged",
            seconds=8, interval=.2,
        )
        assert source.read_bytes() == first_bytes
        assert other.read_bytes() == other_bytes
        print("RECYCLE_DIALOG_CANCEL_PRESERVES_OWNED_FILES=PASS", flush=True)
        if via_ctrl_d:
            print("CTRL_D_OWNED_RECYCLE_PROMPT_CANCEL=PASS", flush=True)

        # After Cancel the same request must remain usable. Escape closes it
        # without authorizing any Shell file operation.
        second = select_and_prompt()
        second.set_focus()
        assert owned_foreground(process.pid)
        send_keys("{ESC}")
        wait_until(
            lambda: not bool(cancel_button()),
            "Escape did not close the owned recycle dialog",
            seconds=8, interval=.2,
        )
        for _ in range(6):
            assert process.poll() is None
            assert source.read_bytes() == first_bytes
            assert other.read_bytes() == other_bytes
            assert sorted(p.name for p in folder.iterdir()) == sorted([
                source.name, other.name
            ])
            time.sleep(.15)
        print("RECYCLE_DIALOG_ESCAPE_PRESERVES_OWNED_FILES=PASS", flush=True)
        print("RECYCLE_DIALOG_REOPEN_AFTER_CANCEL=PASS", flush=True)
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
        assert_legacy_profile_unchanged(real_root, real_settings)
        assert owned.parent == base and owned.name.startswith("recycle-owned-")
        assert not owned.is_symlink() and not base.is_symlink()
        shutil.rmtree(owned)
        print("RECYCLE_DIALOG_OWNED_FIXTURE_CLEANED=YES", flush=True)
        print("RECYCLE_DIALOG_LEGACY_PROFILE_UNCHANGED=YES", flush=True)
    assert passed
    print("RECYCLE_DIALOG_REAL_GUI_CANCEL_ESCAPE_PASS=True", flush=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "Debug")
