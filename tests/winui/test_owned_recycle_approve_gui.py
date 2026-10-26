"""Approve one GUID-named test-owned file in the real WinUI Recycle dialog.

Restore only its exact Shell Recycle Bin item and verify its original bytes.
Never empty the bin or touch another file or app process.
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
from uuid import uuid4

from win32com.client import Dispatch

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


def run(config="Debug"):
    assert config in ("Debug", "Release")
    exe = app_exe(config)
    assert exe.is_file()
    real_root, real_settings = snapshot_legacy_profile()
    base = ROOT / "logs" / "recycle-approve-focused-gui"
    base.mkdir(parents=True, exist_ok=True)
    assert not base.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="recycleapprove-owned-", dir=base))
    folder = owned / "Source"
    folder.mkdir()
    source = folder / f"OwnedRecycleApprove_{uuid4().hex}.txt"
    other = folder / "OwnedRecycleUntouched.txt"
    first_bytes = b"synthetic recycle approval restored bytes"
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
    approved = False
    restored = False

    def recycle_entries():
        bin_folder = Dispatch("Shell.Application").NameSpace(10)
        assert bin_folder is not None, "Recycle Bin namespace unavailable"
        hits = []
        for entry in bin_folder.Items():
            if str(entry.Name) != source.name:
                continue
            parent = str(entry.ExtendedProperty("System.Recycle.DeletedFrom") or "")
            hits.append((entry, parent))
        return hits

    def owned_bin_entry():
        entries = recycle_entries()
        if len(entries) != 1:
            return None
        item, parent = entries[0]
        if os.path.normcase(os.path.normpath(parent)) != (
            os.path.normcase(os.path.normpath(str(folder)))
        ):
            return None
        return item

    # Unique-name preflight before opening any file operation confirmation.
    assert not recycle_entries(), "unique synthetic name already exists in bin"
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

        def select_and_prompt():
            def selected_owned_source():
                # Shell watcher may replace the ListItem wrapper during a
                # row refresh; use the current PID-bound item each time.
                item = row(source.name)
                if item is None:
                    return False
                if item.is_selected():
                    return True
                focus_owned(win, process.pid)
                item.click_input()
                current = row(source.name)
                if current is None:
                    return False
                current.iface_selection_item.Select()
                verify = row(source.name)
                return verify is not None and verify.is_selected()

            wait_until(selected_owned_source,
                       "owned recycle source could not be selected",
                       seconds=16, interval=.25)
            assert recycle.is_enabled()
            assert recycle.element_info.process_id == process.pid
            focus_owned(win, process.pid)
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

        # Only authorize a single GUID-named source under an owned folder.
        select_and_prompt()
        assert source.read_bytes() == first_bytes
        assert other.read_bytes() == other_bytes
        assert not recycle_entries()
        primary = visible_modal_buttons("휴지통으로 보내기")
        assert len(primary) == 1
        assert primary[0].element_info.process_id == process.pid
        primary[0].iface_invoke.Invoke()
        approved = True
        wait_until(
            lambda: not source.exists(),
            "approved recycle did not remove test-owned original",
            seconds=20, interval=.25,
        )
        wait_until(
            lambda: "1개 항목의 휴지통 이동을 완료했습니다." in status.window_text(),
            "approved recycle did not report Shell success",
            seconds=18, interval=.25,
        )
        assert other.read_bytes() == other_bytes
        print("RECYCLE_APPROVAL_SOURCE_REMOVED=PASS", flush=True)

        item = wait_until(
            owned_bin_entry,
            "unique recycled item missing or original folder does not match",
            seconds=22, interval=.4,
        )
        assert len(recycle_entries()) == 1
        print("RECYCLE_APPROVAL_OWNED_SHELL_BIN_ENTRY_FOUND=PASS", flush=True)

        # RESTORE targets only that one exact GUID item and original parent.
        # No global Recycle Bin clear, deletion or destructive cleanup.
        # InvokeVerb("RESTORE") may silently do nothing on non-English
        # Windows. Use the unique localized Shell action for this exact
        # GUID-named item; never operate on any other Recycle entry.
        restore_verbs = [
            verb for verb in item.Verbs()
            if "복원" in str(verb.Name)
            or "restore" in str(verb.Name).casefold()
        ]
        assert len(restore_verbs) == 1, "owned restore verb not unique"
        restore_verbs[0].DoIt()
        wait_until(
            lambda: source.is_file(),
            "Shell restore did not recover exact owned source",
            seconds=24, interval=.35,
        )
        assert source.read_bytes() == first_bytes
        assert other.read_bytes() == other_bytes
        wait_until(
            lambda: not recycle_entries(),
            "restored test-owned item remains in bin",
            seconds=12, interval=.35,
        )
        restored = True
        print("RECYCLE_APPROVAL_EXACT_OWNED_ITEM_RESTORED=PASS", flush=True)
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
        if approved and not restored:
            try:
                recovered = owned_bin_entry()
                if recovered is not None and not source.exists():
                    verbs = [
                        verb for verb in recovered.Verbs()
                        if "복원" in str(verb.Name)
                        or "restore" in str(verb.Name).casefold()
                    ]
                    assert len(verbs) == 1
                    verbs[0].DoIt()
                    wait_until(lambda: source.is_file(),
                               "exact-item recovery restore did not finish",
                               seconds=16, interval=.35)
                restored = (source.is_file()
                            and source.read_bytes() == first_bytes
                            and not recycle_entries())
            except Exception as error:
                print(f"RECYCLE_APPROVAL_RESTORE_ERROR={error!r}", flush=True)
        assert_legacy_profile_unchanged(real_root, real_settings)
        assert owned.parent == base and owned.name.startswith(
            "recycleapprove-owned-"
        )
        assert not owned.is_symlink() and not base.is_symlink()
        if not approved or restored:
            shutil.rmtree(owned)
            print("RECYCLE_APPROVAL_OWNED_FIXTURE_CLEANED=YES", flush=True)
        else:
            print(f"RECYCLE_APPROVAL_RECOVERY_FIXTURE_RETAINED={owned}",
                  flush=True)
        print("RECYCLE_APPROVAL_LEGACY_PROFILE_UNCHANGED=YES", flush=True)
    assert passed and restored
    print("RECYCLE_APPROVAL_REAL_GUI_AND_RESTORE_PASS=True", flush=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "Debug")
