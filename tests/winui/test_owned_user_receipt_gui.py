"""Interactive user-session WinUI + shipping helper Known Folder receipt acceptance.

Explicitly opted-in manual gate only. Uses uniquely owned source/destination,
an owned WinUI process/window and exact new app receipts. No record removal.
Do NOT run as SYSTEM or in Session 0.
"""
from __future__ import annotations

import ctypes as c
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from pywinauto import Desktop
from paths import ROOT, app_exe
from receipt_wire_owned import matches_owned_published_target
from uia_polling import wait_until


class GUID(c.Structure):
    _fields_ = [("Data1", W.DWORD), ("Data2", W.WORD), ("Data3", W.WORD),
                ("Data4", c.c_ubyte * 8)]


def local_app_data() -> Path:
    key = uuid.UUID("f1b32785-6fba-4fcf-9d55-7b8e7f157091")
    guid = GUID.from_buffer_copy(key.bytes_le)
    value = c.c_wchar_p()
    shell = c.WinDLL("shell32", use_last_error=True)
    shell.SHGetKnownFolderPath.argtypes = [
        c.POINTER(GUID), W.DWORD, W.HANDLE, c.POINTER(c.c_wchar_p)]
    # ctypes.wintypes has LONG, but no portable HRESULT alias.
    shell.SHGetKnownFolderPath.restype = W.LONG
    hr = shell.SHGetKnownFolderPath(c.byref(guid), 0, None, c.byref(value))
    if hr != 0 or not value.value:
        raise RuntimeError("Interactive LocalAppData Known Folder unavailable")
    path = Path(value.value)
    c.windll.ole32.CoTaskMemFree(c.cast(value, c.c_void_p))
    return path


def require_logged_in_session() -> None:
    if os.environ.get("FLY_ALLOW_INTERACTIVE_RECEIPT_GUI") != "1":
        raise RuntimeError("Explicit interactive user receipt opt-in required")
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.ProcessIdToSessionId.argtypes = [W.DWORD, c.POINTER(W.DWORD)]
    session = W.DWORD()
    if not kernel.ProcessIdToSessionId(os.getpid(), c.byref(session)):
        raise RuntimeError("Cannot prove current interactive session")
    if session.value == 0:
        raise RuntimeError("Refuse SYSTEM Session 0")

    # Session presence alone is insufficient: the current process must NOT
    # have the LocalSystem SID. Fail closed if the token cannot be inspected.
    # SID bytes are ASCII even when whoami's headings use the machine
    # OEM codepage. Do NOT decode localized output as UTF-8.
    identity = subprocess.run(["whoami", "/user"], capture_output=True,
                              timeout=10, check=True)
    raw_sid_output = identity.stdout or b""
    if b"S-1-5-18" in raw_sid_output or b"S-1-5-21-" not in raw_sid_output:
        raise RuntimeError("Refuse non-user or unidentified security token")


def main() -> None:
    require_logged_in_session()
    exe = app_exe("Release")
    helper = exe.with_name("FlyShellIsolationHelper.exe")
    fixture = (ROOT / "tests" / "winui" / "m22" / "bin" / "x64" /
               "Release" / "FlyM22ShellTransferContracts.exe")
    if not (exe.is_file() and helper.is_file() and fixture.is_file()):
        raise RuntimeError("Matching Release product/helper/fixture required")

    store = local_app_data() / "flyExplorer-transfer-receipts-v1"
    if store.is_symlink() or (store.exists() and not store.is_dir()):
        raise RuntimeError("Refuse non-directory or linked receipt store")
    # Only snapshot file NAMES; never read or mutate older private receipts.
    older = ({p.name for p in store.glob("*.bin")} if store.exists() else set())

    log = Path(os.environ.get(
        "FLY_INTERACTIVE_RECEIPT_LOG_ROOT",
        str(ROOT / "logs" / "interactive-user-receipt")))
    log.mkdir(parents=True, exist_ok=True)
    owned = Path(tempfile.mkdtemp(prefix="user-knownfolder-owned-", dir=log))
    left, right = owned / "Left", owned / "Right"
    left.mkdir()
    right.mkdir()
    name = "receipt-owned-" + uuid.uuid4().hex + "-한글.txt"
    src = left / name
    data = b"flyExplorer interactive owned Known Folder receipt - exact bytes"
    src.write_bytes(data)
    (owned / "appdata").mkdir()
    (owned / "temp").mkdir()
    environment = dict(os.environ)
    # Keep the REAL LocalAppData Known Folder; isolate unrelated app session
    # and temp files without changing global preferences or registry.
    environment["APPDATA"] = str(owned / "appdata")
    environment["TEMP"] = environment["TMP"] = str(owned / "temp")
    environment.pop("FLY_M22_OWNED_RECEIPT_STORE", None)
    environment.pop("FLY_M22_OWNED_HELPER", None)

    process = None
    hwnd = None
    user32 = c.windll.user32
    window_callback = c.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    user32.EnumWindows.argtypes = [window_callback, W.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
    user32.IsWindowVisible.argtypes = [W.HWND]
    user32.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    user32.GetForegroundWindow.restype = W.HWND

    try:
        process = subprocess.Popen([str(exe), str(left)], cwd=exe.parent,
            env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def owned_windows():
            result = []
            @window_callback
            def pick(handle, _):
                owner = W.DWORD()
                user32.GetWindowThreadProcessId(handle, c.byref(owner))
                if owner.value == process.pid and user32.IsWindowVisible(handle):
                    result.append(int(handle))
                return True
            user32.EnumWindows(pick, 0)
            return result

        wait_until(lambda: process.poll() is not None or
                   len(owned_windows()) == 1, "Owned WinUI did not open",
                   seconds=26, interval=.15)
        if process.poll() is not None:
            raise RuntimeError("Owned WinUI exited on launch")
        matches = owned_windows()
        if len(matches) != 1:
            raise RuntimeError("Refuse ambiguous owned WinUI window")
        hwnd = matches[0]
        win = Desktop(backend="uia").window(handle=hwnd)

        def control(automation_id):
            return win.child_window(auto_id=automation_id)

        def focus():
            win.set_focus()
            foreground = user32.GetForegroundWindow()
            owner = W.DWORD()
            user32.GetWindowThreadProcessId(foreground, c.byref(owner))
            if owner.value != process.pid:
                raise RuntimeError("Refuse input on foreign HWND")

        def eventually(predicate, description, seconds=25):
            return wait_until(predicate, description, seconds=seconds,
                              interval=.15)

        for item in ("LeftFiles", "RightFiles", "AddressBox",
                     "CopyButton", "StatusText"):
            if not control(item).exists(timeout=8):
                raise RuntimeError("Required owned WinUI control missing: " + item)
        eventually(lambda: str(left).casefold() in
                   control("AddressBox").get_value().casefold(),
                   "Owned starting source path absent")
        focus()
        control("RightFiles").click_input()
        focus()
        address = control("AddressBox")
        address.set_edit_text(str(right))
        focus()
        address.type_keys("{ENTER}", set_foreground=True)
        eventually(lambda: str(right).casefold() in
                   control("AddressBox").get_value().casefold(),
                   "Owned destination navigation failed")

        def source_row():
            return next((x for x in control("LeftFiles").descendants()
                if x.element_info.control_type == "ListItem"
                and name in x.window_text()), None)

        eventually(lambda: source_row() is not None,
                   "Owned source row did not load")
        focus()
        source_row().click_input()
        eventually(lambda: source_row() is not None and
                   source_row().is_selected(), "Owned selection failed")
        eventually(lambda: str(left).casefold() in
                   control("AddressBox").get_value().casefold(),
                   "Selected source pane is not active")
        focus()
        control("CopyButton").click_input()
        destination = right / name
        eventually(lambda: destination.is_file() and
                   destination.read_bytes() == data,
                   "Actual WinUI Copy failed exact destination bytes", 35)
        if src.read_bytes() != data:
            raise RuntimeError("Owned source was modified")
        if not store.is_dir() or store.is_symlink():
            raise RuntimeError("Shipping helper private receipt store unavailable")

        def new_receipts():
            return [p for p in store.glob("*.bin")
                    if p.name not in older and p.is_file()]
        def committed_new_receipt():
            fresh = new_receipts()
            if (len(fresh) != 1 or
                    not matches_owned_published_target(
                        fresh[0], destination)):
                return False
            checked = subprocess.run(
                [str(fixture), "--receipt-inspect-state", str(fresh[0]),
                 "published"], cwd=fixture.parent, capture_output=True,
                text=True, timeout=15)
            return checked.returncode == 0 and (
                "M22_RESTART_READONLY_RECEIPT_STATE=PASS" in checked.stdout)
        eventually(committed_new_receipt,
                   "No new fully published shipping-helper Known Folder receipt", 30)
        print("REAL_USER_GUI_SHIPPING_KNOWNFOLDER_RECEIPT=PASS", flush=True)
        print("REAL_USER_GUI_COPY_BYTES_PUBLISHED=PASS", flush=True)
        print("REAL_USER_GUI_PRIOR_RECEIPT_CONTENT_NOT_READ=PASS", flush=True)
    finally:
        if process is not None and process.poll() is None:
            if hwnd:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                # Only this fixture-spawned application process may stop.
                process.terminate()
                process.wait(timeout=7)
        print("REAL_USER_GUI_OWNED_FIXTURE_ONLY=TRUE", flush=True)


if __name__ == "__main__":
    main()
