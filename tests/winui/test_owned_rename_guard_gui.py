"""Focused real WinUI rename regression against an exclusively test-owned folder.

Exercises UIA selection change while the F2 filename editor is open, followed
by one ordinary successful rename. Never operates on user files or clipboard.
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
from profile_guard import (
    assert_legacy_profile_unchanged, snapshot_legacy_profile,
)
from uia_polling import wait_until


user32 = ctypes.windll.user32
user32.GetWindowThreadProcessId.argtypes = (
    wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
)
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetForegroundWindow.restype = wintypes.HWND
user32.PostMessageW.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
)
user32.PostMessageW.restype = wintypes.BOOL


def owned_foreground(pid: int) -> bool:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    owner = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    return owner.value == pid


def require_owned_foreground(window, pid: int) -> None:
    window.set_focus()
    wait_until(
        lambda: owned_foreground(pid),
        "F2 input cannot be sent unless test-owned app has foreground",
        seconds=6, interval=.15,
    )


def run(config: str = "Debug") -> None:
    assert config in ("Debug", "Release")
    exe = app_exe(config)
    assert exe.is_file(), f"Product app is not built: {exe}"
    original_root, original_settings = snapshot_legacy_profile()
    base = ROOT / "logs" / "rename-guard-focused-gui"
    base.mkdir(parents=True, exist_ok=True)
    assert not base.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="rename-owned-", dir=base))
    folder = owned / "Original"
    folder.mkdir()
    first = folder / "OwnedRenameFirst.txt"
    second = folder / "OwnedRenameSecond.txt"
    unwanted = folder / "MustNotAppear.txt"
    wanted = folder / "OwnedRenameCompleted.txt"
    first_bytes = b"first file must remain unchanged"
    second_bytes = b"second test-only file may be renamed"
    first.write_bytes(first_bytes)
    second.write_bytes(second_bytes)
    profile = {}
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        directory = owned / key.lower()
        directory.mkdir()
        profile[key] = str(directory)
    env = {**os.environ, **profile}
    process = None
    hwnd = None
    result_ok = False
    try:
        process = subprocess.Popen(
            [str(exe), str(folder)],
            cwd=exe.parent, env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def window():
            assert process.poll() is None, (
                "test-owned flyExplorer exited before F2 UI assertions",
                process.returncode,
            )
            owned_exe = Path(psutil.Process(process.pid).exe())
            assert owned_exe.resolve() == exe.resolve()
            candidates = [
                item for item in Desktop(backend="uia").windows(
                    process=process.pid
                )
                if "flyExplorer" in item.window_text()
            ]
            # Desktop.windows yields a resolved UIAWrapper, while
            # child_window is a WindowSpecification API. Re-bind the exact
            # verified HWND before asking for its named child controls.
            return (Desktop(backend="uia").window(handle=candidates[0].handle)
                    if len(candidates) == 1 else None)

        view = wait_until(
            window, "one test-owned WinUI window missing",
            seconds=22, interval=.25,
        )
        hwnd = view.handle
        assert view.element_info.process_id == process.pid
        address = view.child_window(auto_id="AddressBox")
        wait_until(
            lambda: str(folder).casefold() in address.get_value().casefold(),
            "test-owned startup folder was not loaded",
            seconds=18, interval=.2,
        )
        files = view.child_window(auto_id="LeftFiles")
        editor = view.child_window(auto_id="FileNameBox")
        status = view.child_window(auto_id="StatusText")

        def row(label):
            matches = [
                item for item in files.descendants()
                if item.element_info.control_type == "ListItem"
                and label in item.window_text()
                and item.element_info.process_id == process.pid
            ]
            return matches[0] if len(matches) == 1 else None

        wait_until(
            lambda: row(first.name) is not None
            and row(second.name) is not None,
            "two test-owned file rows are not available",
            seconds=18, interval=.2,
        )
        assert first.read_bytes() == first_bytes
        assert second.read_bytes() == second_bytes

        # F2 binds the edit to first. Change only the UIA selection to second
        # without invoking another command or clicking on an unrelated HWND.
        require_owned_foreground(view, process.pid)
        row(first.name).iface_selection_item.Select()
        files.set_focus()
        assert owned_foreground(process.pid)
        send_keys("{F2}")
        wait_until(
            lambda: editor.get_value() == first.name,
            "F2 did not open the editor for the selected first file",
            seconds=9, interval=.15,
        )
        print("F2_OWNED_EDITOR_OPENED=PASS", flush=True)
        row(second.name).iface_selection_item.Select()
        wait_until(
            lambda: bool(row(second.name).is_selected())
            and not bool(row(first.name).is_selected()),
            "selection did not move to the second test-owned file",
            seconds=8, interval=.15,
        )
        editor.set_edit_text(unwanted.name)
        require_owned_foreground(view, process.pid)
        editor.set_focus()
        assert owned_foreground(process.pid)
        send_keys("{ENTER}")
        wait_until(
            lambda: "이름 변경 대상이 바뀌었습니다." in status.window_text(),
            "stale F2 edit did not reject changed selected source",
            seconds=8, interval=.2,
        )
        for _ in range(8):
            assert first.read_bytes() == first_bytes
            assert second.read_bytes() == second_bytes
            assert not unwanted.exists()
            time.sleep(.15)
        print("F2_CHANGED_SELECTION_REJECTED_NO_FILE_MUTATION=PASS", flush=True)

        # A fresh edit of the current same file must still succeed.
        row(second.name).iface_selection_item.Select()
        files.set_focus()
        require_owned_foreground(view, process.pid)
        send_keys("{F2}")
        wait_until(
            lambda: editor.get_value() == second.name,
            "second valid F2 edit was not opened",
            seconds=10, interval=.2,
        )
        editor.set_edit_text(wanted.name)
        require_owned_foreground(view, process.pid)
        editor.set_focus()
        assert owned_foreground(process.pid)
        send_keys("{ENTER}")
        wait_until(
            lambda: wanted.is_file() and not second.exists(),
            "confirmed same-source F2 rename did not complete",
            seconds=17, interval=.25,
        )
        assert wanted.read_bytes() == second_bytes
        assert first.read_bytes() == first_bytes
        assert not unwanted.exists()
        print("F2_VALID_RENAME_COMPLETED_AND_CONTENTS_PRESERVED=PASS", flush=True)
        result_ok = True
    finally:
        if process is not None and process.poll() is None:
            try:
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
            finally:
                assert process.poll() is not None, "owned process remained active"
        assert_legacy_profile_unchanged(original_root, original_settings)
        assert owned.parent == base and owned.name.startswith("rename-owned-")
        assert not owned.is_symlink() and not base.is_symlink()
        shutil.rmtree(owned)
        print("F2_OWNED_GUI_FIXTURE_CLEANED=YES", flush=True)
        print("F2_LEGACY_PROFILE_UNCHANGED=YES", flush=True)
    assert result_ok
    print("F2_FOCUSED_REAL_WINUI_GUI_PASS=True", flush=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "Debug")
