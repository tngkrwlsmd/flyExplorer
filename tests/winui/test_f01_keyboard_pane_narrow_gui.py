"""F01 actual owned-HWND keyboard, pane/WindowTab isolation, narrow layout probe.

This tests an interactive Windows user session only. Every physical keystroke
is guarded against a foreign foreground process; never adjusts the OS DPI,
user preferences, active desktop, or non-test files.
"""
import ctypes as c
from ctypes import wintypes as W
from pathlib import Path
import time

from PIL import ImageGrab
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


def run(*, win, element, safe_click, focus, eventually, base, owned, left, right):
    assert Path(left).is_relative_to(owned)
    assert Path(right).is_relative_to(owned)
    pid = win.wrapper_object().element_info.process_id
    assert pid > 0
    u = c.windll.user32
    u.GetForegroundWindow.restype = W.HWND
    u.GetWindowThreadProcessId.argtypes = [W.HWND, c.POINTER(W.DWORD)]
    u.SetWindowPos.argtypes = [W.HWND, W.HWND, c.c_int, c.c_int, c.c_int,
                               c.c_int, W.UINT]
    shell = Desktop(backend="uia")

    def assert_foreground_owned():
        fg = u.GetForegroundWindow()
        owner = W.DWORD()
        if fg:
            u.GetWindowThreadProcessId(fg, c.byref(owner))
        assert fg and owner.value == pid, "refuse F01 keys/pixels to foreign HWND"

    def owned_keys(keys):
        assert_foreground_owned()
        send_keys(keys, pause=.07)
        assert_foreground_owned()

    def list_rows(side):
        key = "LeftFiles" if side == 0 else "RightFiles"
        return [r for r in element(key).descendants()
                if r.element_info.control_type == "ListItem"]

    def file_row(side):
        return next((r for r in list_rows(side)
                     if "readme.txt" in r.window_text()), None)

    def state_hidden(side):
        found = file_row(side)
        return bool(found and "실제 파일 이름: readme.txt" in found.window_text())

    def menu_peer(name):
        def find():
            target = element(name)
            if target.exists(timeout=.12):
                peer = target.wrapper_object()
                if peer.element_info.process_id == pid:
                    return peer
            matched = [x for w in shell.windows(process=pid)
                       for x in w.descendants()
                       if x.element_info.automation_id == name and
                       x.element_info.process_id == pid]
            return matched[0] if len(matched) == 1 else None
        peer = eventually(find, "F01 menu peer not found " + name, 8)
        assert peer.element_info.automation_id == name
        assert peer.element_info.process_id == pid
        return peer

    def open_menu_keyboard():
        focus()
        button = element("ViewButton").wrapper_object()
        button.set_focus()
        assert_foreground_owned()
        owned_keys("{ENTER}")
        return menu_peer("ViewFileExtensionsItem")

    def open_menu_pointer():
        safe_click(element("ViewButton"))
        return menu_peer("ViewFileExtensionsItem")

    def check_menu(checkboxes, compact, extensions):
        open_menu_pointer()
        options = (("ViewCheckboxesItem", checkboxes),
                   ("ViewCompactRowsItem", compact),
                   ("ViewFileExtensionsItem", extensions))
        observed = []
        for name, expected in options:
            peer = menu_peer(name)
            actual = int(peer.iface_toggle.CurrentToggleState)
            assert actual == int(expected), (name, expected, actual)
            observed.append(actual)
        owned_keys("{ESC}")
        return observed

    def toggle_keyboard(name, status_part):
        open_menu_keyboard()
        peer = menu_peer(name)
        peer.set_focus()
        assert_foreground_owned()
        owned_keys("{SPACE}")
        eventually(lambda: status_part in element("StatusText").window_text(),
                   "F01 keyboard Space did not dispatch " + name, 7)

    def switch_pane(side):
        key = "LeftFiles" if side == 0 else "RightFiles"
        row = eventually(lambda: file_row(side),
                         "F01 other pane owned readme row not available", 10)
        safe_click(row)
        expected = "활성: 왼쪽" if side == 0 else "활성: 오른쪽"
        eventually(lambda: expected in element("ActivePaneText").window_text(),
                   "F01 clicked pane did not become active", 8)
        assert element(key).is_visible()

    eventually(lambda: file_row(0) and file_row(1),
               "F01 owned left/right fixture not visible", 14)
    initial_row_height = file_row(0).rectangle().height()
    assert initial_row_height >= 26
    safe_click(file_row(0))
    check_menu(False, False, True)

    toggle_keyboard("ViewCheckboxesItem", "선택 확인란")
    check_menu(True, False, True)
    toggle_keyboard("ViewCompactRowsItem", "목록 간격")
    eventually(lambda: file_row(0) and
               file_row(0).rectangle().height() < initial_row_height,
               "F01 keyboard compact row did not shrink", 9)
    toggle_keyboard("ViewFileExtensionsItem", "파일 확장명")
    eventually(lambda: state_hidden(0),
               "F01 keyboard extension hide lost original UIA filename", 8)
    check_menu(True, True, False)
    print("F01_KEYBOARD_VIEW_MENU_AND_NATIVE_SELECTION=PASS", flush=True)

    switch_pane(1)
    check_menu(False, False, True)
    assert not state_hidden(1)
    assert file_row(1).rectangle().height() >= initial_row_height
    # Change only the right pane, then prove the left pane survived.
    open_menu_pointer()
    right = menu_peer("ViewCompactRowsItem")
    right.iface_toggle.Toggle()
    eventually(lambda: "목록 간격" in element("StatusText").window_text(),
               "right pane compact toggle command not dispatched", 7)
    check_menu(False, True, True)
    switch_pane(0)
    check_menu(True, True, False)
    assert state_hidden(0) and not state_hidden(1)
    print("F01_LEFT_RIGHT_PANE_DISPLAY_ISOLATION=PASS", flush=True)

    def window_tabs():
        return [t for t in element("WindowTabStrip").descendants()
                if t.element_info.control_type == "TabItem"]

    eventually(lambda: len(window_tabs()) == 1,
               "one initial window tab missing", 8)
    focus()
    safe_click(element("LeftFiles"))
    owned_keys("^t")
    eventually(lambda: len(window_tabs()) == 2,
               "Ctrl+T did not create independent window tab", 12)
    # New WindowTab defaults: both panes' F01 flags must be untouched.
    check_menu(False, False, True)
    print("F01_NEW_WINDOW_TAB_DEFAULT_DISPLAY=PASS", flush=True)
    # Modify B and return to A by keyboard to prove both directions isolate.
    open_menu_pointer()
    menu_peer("ViewCheckboxesItem").iface_toggle.Toggle()
    eventually(lambda: "선택 확인란" in element("StatusText").window_text(),
               "window tab B checkbox command did not dispatch", 7)
    check_menu(True, False, True)
    focus()
    safe_click(element("LeftFiles"))
    owned_keys("^+{TAB}")
    eventually(lambda: file_row(0) is not None and state_hidden(0),
               "Ctrl+Shift+Tab did not restore A's original filename mode", 16)
    check_menu(True, True, False)
    owned_keys("^{TAB}")
    check_menu(True, False, True)
    # Leave fixture on A to verify selected readme row under narrow width.
    focus()
    safe_click(element("LeftFiles"))
    owned_keys("^+{TAB}")
    eventually(lambda: state_hidden(0), "WindowTab A state lost on return", 12)
    print("F01_WINDOWTAB_DISPLAY_REHYDRATION=PASS", flush=True)

    focus()
    width, height = 800, 570
    assert u.GetSystemMetrics(0) >= width + 35
    assert u.GetSystemMetrics(1) >= height + 35
    hwnd = win.handle
    assert_foreground_owned()
    assert u.SetWindowPos(hwnd, None, 20, 20, width, height, 0x0014)
    eventually(lambda: abs(win.rectangle().width()-width) < 4 and
               abs(win.rectangle().height()-height) < 4,
               "F01 narrow owned window did not settle", 8)
    bounds = win.rectangle()
    for name in ("ViewButton", "SortButton", "LeftFiles", "RightFiles",
                 "StatusText", "WindowTabStrip"):
        peer = element(name).wrapper_object()
        rect = peer.rectangle()
        assert peer.is_visible(), ("narrow essential control hidden", name)
        assert rect.left >= bounds.left and rect.right <= bounds.right, (
            "narrow control clipped horizontally", name, str(rect), str(bounds))
        assert rect.top >= bounds.top and rect.bottom <= bounds.bottom, (
            "narrow control clipped vertically", name, str(rect), str(bounds))
    assert file_row(0) is not None and state_hidden(0)
    assert element("LeftFiles").rectangle().width() >= 220
    assert element("RightFiles").rectangle().width() >= 220

    # Retain only opaque app-owned pixels. The control task may export only
    # this explicit screenshot for independent narrow-layout visual review.
    focus()
    assert_foreground_owned()
    crop = (bounds.left+12, bounds.top+8, bounds.right-8, bounds.bottom-8)
    shot = base / "f01-interaction-narrow-owned.png"
    ImageGrab.grab(bbox=crop, include_layered_windows=True).save(shot, "PNG",
                                                                 optimize=True)
    print("F01_NARROW_OWNED_GUI=PASS",
          "WINDOW", width, height, "CROP", crop, "PNG", shot.name, flush=True)
