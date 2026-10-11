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
    shell.SHGetKnownFolderPath.restype = W.HRESULT
    hr = shell.SHGetKnownFolderPath(c.byref(guid), 0, None, c.byref(value))
    if hr != 0 or not value.value:
        raise RuntimeError("Interactive LocalAppData Known Folder unavailable")
    path = Path(value.value)
    c.windll.ole32.CoTaskMemFree(c.cast(value, c.c_void_p))
    return path


def require_logged_in_session() -> None:
    assert os.environ.get("FLY_ALLOW_INTERACTIVE_RECEIPT_GUI") == "1", (
        "Explicit interactive user receipt acceptance opt-in required")
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.ProcessIdToSessionId.argtypes = [W.DWORD, c.POINTER(W.DWORD)]
    session = W.DWORD()
    assert kernel.ProcessIdToSessionId(os.getpid(), c.byref(session))
    assert session.value > 0, "Refuse SYSTEM Session 0"

    # Session presence alone is insufficient: the current process must NOT
    # have the LocalSystem SID. Fail closed if the token cannot be inspected.
    identity = subprocess.run(["whoami", "/user"], capture_output=True,
                              text=True, timeout=10, check=True)
    assert "S-1-5-18" not in identity.stdout, "Refuse LocalSystem"


def main() -> None:
    require_logged_in_session()
    exe = app_exe("Release")
    helper = exe.with_name("FlyShellIsolationHelper.exe")
    fixture = (ROOT / "tests" / "winui" / "m22" / "bin" / "x64" /
               "Release" / "FlyM22ShellTransferContracts.exe")
    assert exe.is_file() and helper.is_file() and fixture.is_file(), (
        "Matching Release product/helper/M22 fixture required")

    store = local_app_data() / "flyExplorer-transfer-receipts-v1"
    assert not store.is_symlink(), "Refuse reparse receipt folder"
    assert not store.exists() or store.is_dir(), "Receipt store is not a folder"
    # Only snapshot file NAMES; never read or mutate older private receipts.
    older = ({p.name for p in store.glob("*.bin")} if store.exists() else set())

    log = ROOT / "logs" / "interactive-user-receipt"
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
        assert process.poll() is None, "Owned WinUI exited on launch"
        hwnd = owned_windows()[0]
        win = Desktop(backend="uia").window(handle=hwnd)

        def control(automation_id):
            return win.child_window(auto_id=automation_id)

        def focus():
            win.set_focus()
            foreground = user32.GetForegroundWindow()
            owner = W.DWORD()
            user32.GetWindowThreadProcessId(foreground, c.byref(owner))
            assert owner.value == process.pid, "Refuse input on foreign HWND"

        def eventually(predicate, description, seconds=25):
            return wait_until(predicate, description, seconds=seconds,
                              interval=.15)

        for item in ("LeftFiles", "RightFiles", "AddressBox",
                     "CopyButton", "StatusText"):
            assert control(item).exists(timeout=8), item
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
        source_row().select()
        eventually(lambda: source_row() is not None and
                   source_row().is_selected(), "Owned selection failed")
        focus()
        control("CopyButton").click_input()
        destination = right / name
        eventually(lambda: destination.is_file() and
                   destination.read_bytes() == data,
                   "Actual WinUI Copy failed exact destination bytes", 35)
        assert src.read_bytes() == data, "Owned source was modified"
        assert store.is_dir() and not store.is_symlink(), (
            "Shipping helper did not create its Known Folder receipt store")

        def new_receipts():
            return [p for p in store.glob("*.bin")
                    if p.name not in older and p.is_file()]
        eventually(lambda: bool(new_receipts()),
                   "No new shipping-helper Known Folder receipt")
        fresh = new_receipts()
        assert len(fresh) == 1, (
            "Expected only the one owned GUI Copy receipt", len(fresh))
        checked = subprocess.run(
            [str(fixture), "--receipt-inspect-state", str(fresh[0]),
             "published"], cwd=fixture.parent, capture_output=True,
            text=True, timeout=15)
        assert checked.returncode == 0 and (
            "M22_RESTART_READONLY_RECEIPT_STATE=PASS" in checked.stdout), (
            "Read-only published identity inspection failed")
        print("REAL_USER_GUI_SHIPPING_KNOWNFOLDER_RECEIPT=PASS", flush=True)
        print("REAL_USER_GUI_COPY_BYTES_PUBLISHED=PASS", flush=True)
        print("REAL_USER_GUI_EXISTING_RECEIPTS_UNTOUCHED=PASS", flush=True)
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
