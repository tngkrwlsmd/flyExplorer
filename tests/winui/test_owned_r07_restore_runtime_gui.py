"""R07-23E: actual owned WinUI Rename -> private restore completion.

Requires the explicitly compiled R07 owned-runtime binary. It creates one file
under the process-local TEMP directory, renames it through the real F2 UI, and
waits for the product's DispatcherQueue completion trace. No user file,
clipboard, recycle bin, external transfer, or user Undo command is touched.
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


def file_identity(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino


def run(config: str = "Release") -> None:
    assert config == "Release"
    exe = app_exe(config)
    assert exe.is_file(), f"Product app is not built: {exe}"
    original_root, original_settings = snapshot_legacy_profile()
    base = ROOT / "logs" / "r07-owned-restore-runtime"
    base.mkdir(parents=True, exist_ok=True)
    assert not base.is_symlink()
    owned = Path(tempfile.mkdtemp(prefix="r07-runtime-", dir=base)).resolve()
    profile = {}
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        directory = owned / key.lower()
        directory.mkdir()
        profile[key] = str(directory)
    fixture = Path(tempfile.mkdtemp(
        prefix="fixture-", dir=profile["TEMP"]
    )).resolve()
    original = fixture / "OwnedBefore.txt"
    target = fixture / "OwnedAfter.txt"
    trace = Path(profile["TEMP"]) / "r07-restore-trace.txt"
    delivery_trace = Path(profile["TEMP"]) / "r07-delivery-trace.txt"
    payload = b"r07 owned runtime bytes must survive rename and restore\n"
    original.write_bytes(payload)
    before_identity = file_identity(original)
    env = {
        **os.environ,
        **profile,
        "FLYEXPLORER_R07_OWNED_ORIGINAL": str(original),
        "FLYEXPLORER_R07_OWNED_TARGET": str(target),
        "FLYEXPLORER_R07_OWNED_TRACE": str(trace),
        "FLYEXPLORER_R07_OWNED_DELIVERY_TRACE": str(delivery_trace),
    }
    process = None
    hwnd = None
    passed = False
    try:
        process = subprocess.Popen(
            [str(exe), str(fixture)],
            cwd=exe.parent, env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def window():
            assert process.poll() is None, (
                "test-owned flyExplorer exited before R07 assertions",
                process.returncode,
            )
            assert Path(psutil.Process(process.pid).exe()).resolve() == exe.resolve()
            candidates = [
                item for item in Desktop(backend="uia").windows(
                    process=process.pid
                )
                if "flyExplorer" in item.window_text()
            ]
            return (Desktop(backend="uia").window(handle=candidates[0].handle)
                    if len(candidates) == 1 else None)

        view = wait_until(
            window, "one test-owned WinUI window missing",
            seconds=22, interval=.25,
        )
        hwnd = view.handle
        address = view.child_window(auto_id="AddressBox")
        wait_until(
            lambda: str(fixture).casefold() in address.get_value().casefold(),
            "test-owned startup folder was not loaded",
            seconds=18, interval=.2,
        )
        files = view.child_window(auto_id="LeftFiles")
        editor = view.child_window(auto_id="FileNameBox")

        def row(label: str):
            matches = [
                item for item in files.descendants()
                if item.element_info.control_type == "ListItem"
                and label in item.window_text()
                and item.element_info.process_id == process.pid
            ]
            return matches[0] if len(matches) == 1 else None

        wait_until(
            lambda: row(original.name) is not None,
            "owned source row is not available",
            seconds=18, interval=.2,
        )
        view.set_focus()
        wait_until(
            lambda: owned_foreground(process.pid),
            "owned app did not receive foreground",
            seconds=6, interval=.15,
        )
        row(original.name).iface_selection_item.Select()
        files.set_focus()
        send_keys("{F2}")
        wait_until(
            lambda: editor.get_value() == original.name,
            "F2 did not open the exact owned source",
            seconds=9, interval=.15,
        )
        editor.set_edit_text(target.name)
        editor.set_focus()
        assert owned_foreground(process.pid)
        send_keys("{ENTER}")

        try:
            wait_until(
                lambda: trace.is_file()
                and trace.read_text(encoding="ascii", errors="strict").endswith(
                    "COMPLETE_VERIFIED\n"
                ),
                "owned restore did not reach verified DispatcherQueue completion",
                seconds=24, interval=.2,
            )
        except AssertionError as error:
            trace_text = (
                trace.read_text(encoding="ascii", errors="replace")
                if trace.is_file() else "<missing>"
            )
            delivery_text = (
                delivery_trace.read_text(encoding="ascii", errors="replace")
                if delivery_trace.is_file() else "<missing>"
            )
            print(
                "R07_OWNED_RUNTIME_DIAGNOSTIC="
                f"trace={trace_text!r};delivery={delivery_text!r};"
                f"original={original.exists()};target={target.exists()};"
                f"editor={editor.get_value()!r}",
                flush=True,
            )
            raise AssertionError(
                "owned restore did not reach verified DispatcherQueue "
                f"completion; trace={trace_text!r};"
                f"original={original.exists()};target={target.exists()}"
            ) from error
        lines = trace.read_text(encoding="ascii", errors="strict").splitlines()
        assert lines == ["BEGIN", "STARTED", "COMPLETE_VERIFIED"], lines
        delivery_lines = delivery_trace.read_text(
            encoding="ascii", errors="strict"
        ).splitlines()
        assert delivery_lines.count("POST_CALLED") == 1, delivery_lines
        assert delivery_lines.count("POST_ACCEPTED") == 1, delivery_lines
        assert delivery_lines.count("UI_TASK_ENTERED") == 1, delivery_lines
        assert delivery_lines.count("UI_TASK_DISPATCH") == 1, delivery_lines
        assert delivery_lines.count("ON_FILE_COMPLETION") == 1, delivery_lines
        assert len(delivery_lines) == 5, delivery_lines
        assert delivery_lines[0] == "POST_CALLED", delivery_lines
        assert delivery_lines.index("UI_TASK_ENTERED") < delivery_lines.index(
            "UI_TASK_DISPATCH"
        ), delivery_lines
        assert delivery_lines.index("UI_TASK_DISPATCH") < delivery_lines.index(
            "ON_FILE_COMPLETION"
        ), delivery_lines
        wait_until(
            lambda: original.is_file() and not target.exists(),
            "owned file was not restored to the original name",
            seconds=8, interval=.2,
        )
        assert original.read_bytes() == payload
        assert file_identity(original) == before_identity
        assert not target.exists()
        print("R07_OWNED_RUNTIME_RENAME_RESTORE_VERIFIED=PASS", flush=True)
        print("R07_OWNED_RUNTIME_TRACE_EXACTLY_ONCE=PASS", flush=True)
        print("R07_OWNED_RUNTIME_DELIVERY_TRACE=PASS", flush=True)
        print("R07_OWNED_RUNTIME_FILE_ID_AND_BYTES_PRESERVED=PASS", flush=True)
        passed = True
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
        assert owned.parent == base and owned.name.startswith("r07-runtime-")
        assert not owned.is_symlink() and not base.is_symlink()
        shutil.rmtree(owned)
        print("R07_OWNED_RUNTIME_FIXTURE_CLEANED=YES", flush=True)
        print("R07_LEGACY_PROFILE_UNCHANGED=YES", flush=True)
    assert passed
    print("R07_OWNED_RUNTIME_FOCUSED_GUI_PASS=True", flush=True)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "Release")
