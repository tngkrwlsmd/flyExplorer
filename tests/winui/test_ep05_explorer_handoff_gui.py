"""EP05: bounded owned Windows Explorer UI handoff acceptance.

Only interacts with flyExplorer's synthetic fixed-drive files and Windows
Explorer HWNDs created after each explicit app menu click. Existing user
Explorer windows are enumerated by handle/class only, never inspected,
clicked, repositioned, or closed.
"""
import ctypes
import os
from ctypes import wintypes as W
from pathlib import Path

import psutil
from pywinauto import Desktop


def run(*,win,element,focus,eventually,left,right,owned_pid):
    assert left.is_dir() and right.is_dir() and left != right
    assert left.parent == right.parent and left.parent.name.startswith("shell-owned-")
    payload = left / "복사본.txt"
    initial = payload.read_bytes()
    before_files = {p.name: p.read_bytes() for p in left.iterdir() if p.is_file()}
    u = ctypes.windll.user32
    enum_proc = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    u.EnumWindows.argtypes = [enum_proc, W.LPARAM]
    u.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
    u.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
    u.GetForegroundWindow.restype = W.HWND
    u.IsWindowVisible.argtypes = [W.HWND]
    u.IsWindowVisible.restype = W.BOOL

    def explorer_windows():
        matches = {}
        @enum_proc
        def callback(hwnd, _):
            if not u.IsWindowVisible(hwnd):
                return True
            cls = ctypes.create_unicode_buffer(80)
            if not u.GetClassNameW(hwnd, cls, len(cls)):
                return True
            if cls.value != "CabinetWClass":
                return True
            pid = W.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                exe = Path(psutil.Process(pid.value).exe()).name.casefold()
            except (psutil.Error, OSError):
                return True
            if exe == "explorer.exe":
                matches[int(hwnd)] = pid.value
            return True
        u.EnumWindows(callback, 0)
        return matches

    baseline = set(explorer_windows())
    # Handles are eligible for teardown only after the test-owned fixture
    # is visible inside that exact newly created native Explorer window.
    verified = set()

    def owned_menu(label):
        for top in Desktop(backend="uia").windows():
            if top.element_info.process_id != owned_pid:
                continue
            for peer in [top, *top.descendants()]:
                if (peer.element_info.control_type == "MenuItem" and
                    peer.element_info.name == label):
                    return peer
        return None

    def find_owned_explorer(previous, fixture):
        for handle in set(explorer_windows()) - previous:
            try:
                pane = Desktop(backend="uia").window(handle=handle)
                peers = pane.descendants()
                if any(fixture == (peer.element_info.name or "")
                       for peer in peers):
                    verified.add(handle)
                    return handle
            except (RuntimeError, ValueError, OSError):
                continue
        return None

    def menu_click(name):
        item = eventually(lambda: owned_menu(name),
                          "owned WinUI Explorer handoff menu absent", 8)
        assert item.is_enabled(), "native Explorer delegation was disabled"
        current = u.GetForegroundWindow()
        owner = W.DWORD()
        if current:
            u.GetWindowThreadProcessId(current, ctypes.byref(owner))
        assert owner.value == owned_pid, (
            "Refusing to click: a foreign window is foreground")
        item.click_input()

    try:
        def file_row():
            return next((peer for peer in element("LeftFiles").descendants()
                if peer.element_info.control_type == "ListItem" and
                   "복사본.txt" in peer.window_text()), None)
        row = eventually(file_row, "owned source file missing", 12)
        focus()
        row.click_input(button="right")
        menu_click("Windows 탐색기에서 선택 열기")
        eventually(lambda: "Windows 탐색기에서 항목을 선택했습니다" in
                   element("StatusText").window_text(),
                   "native Explorer file selection handoff failed", 14)
        first = eventually(lambda: find_owned_explorer(
            baseline, "복사본.txt"),
            "no newly created Explorer showed the owned selected file", 16)
        print("EP05_NATIVE_EXPLORER_SELECTED_OWNED_FILE=PASS", flush=True)

        # Close only the native HWND verified to contain our synthetic
        # fixture; never close preexisting user's Explorer windows.
        assert first in verified and first not in baseline
        assert first in explorer_windows()
        u.PostMessageW(first, 0x0010, 0, 0)
        eventually(lambda: first not in explorer_windows(),
                   "owned Explorer file-selection window did not close", 8)
        verified.remove(first)
        before_folder = set(explorer_windows())
        focus()
        view = element("LeftFiles").wrapper_object()
        rect = view.rectangle()
        assert rect.height() >= 280 and rect.width() >= 280
        # Rows occupy the top of the fixture list; bottom-center is a
        # blank region. Trigger the actual WinUI RightTapped background.
        view.click_input(button="right",
                         coords=(rect.width() // 2, rect.height() - 20))
        menu_click("Windows 탐색기에서 현재 폴더 열기")
        eventually(lambda: "Windows 탐색기에서 현재 폴더를 열었습니다" in
                   element("StatusText").window_text(),
                   "native Explorer folder handoff failed", 14)
        second = eventually(lambda: find_owned_explorer(
            before_folder, "복사본.txt"),
            "no new Explorer window displayed the owned folder", 16)
        assert second not in baseline and second in verified
        print("EP05_NATIVE_EXPLORER_OPENED_OWNED_FOLDER=PASS", flush=True)
        assert payload.read_bytes() == initial
        assert {p.name: p.read_bytes() for p in left.iterdir() if p.is_file()} == before_files
        print("EP05_NATIVE_EXPLORER_HANDOFF_READ_ONLY=PASS", flush=True)
    finally:
        # Fail closed if an unrelated Explorer appeared at the same time:
        # only exact new HWNDs with a verified synthetic fixture qualify.
        for handle in tuple(verified):
            if handle not in baseline and handle in explorer_windows():
                u.PostMessageW(handle, 0x0010, 0, 0)
