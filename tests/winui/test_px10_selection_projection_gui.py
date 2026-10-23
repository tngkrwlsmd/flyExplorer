"""PX10 real WinUI filter/group selection and focus acceptance; owned fixture only.

Caller (test_shell_gui.py) owns isolated APPDATA/LOCALAPPDATA, the binary,
the freshly created files, WinUI normal exit, profile sentinel and retirement.
No desktop screenshot/clipboard/network/user-file operation.
"""
import ctypes
from ctypes import wintypes
import hashlib
from pywinauto import Desktop, keyboard

def run(*, win, element, safe_click, focus, eventually, left, right):
    assert left.parent == right.parent and left.name == "Left"
    files = ("Alpha-small.txt", "Alpha-second.txt",
             "Mango-medium.md", "Zebra-large.log")
    assert all((left / name).is_file() for name in files)
    checksums = {name: hashlib.sha256((left / name).read_bytes()).digest()
                 for name in files}
    pid = win.wrapper_object().element_info.process_id
    user = ctypes.windll.user32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    def owned_foreground():
        owner = wintypes.DWORD()
        hwnd = user.GetForegroundWindow()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        return bool(hwnd and owner.value == pid)

    def row(name):
        for node in element("LeftFiles").descendants():
            if node.element_info.control_type == "ListItem" and (
                    name in node.window_text()):
                assert node.element_info.process_id == pid
                return node
        return None

    def selected():
        return {name for name in files
                if row(name) is not None and row(name).is_selected()}

    def pair():
        return selected() == set(files[:2]) and (
            "2개 선택됨" in element("SelectionCountText").window_text())

    def left_active():
        return "왼쪽" in element("ActivePaneText").window_text()

    def live_menu(*, ident=None, label=None):
        matches = []
        for popup in Desktop(backend="uia").windows(process=pid):
            for control in [popup, *popup.descendants()]:
                found = (control.element_info.automation_id == ident if ident
                         else control.window_text().replace("&", "").strip() == label)
                if not found or control.element_info.process_id != pid:
                    continue
                try:
                    rect = control.rectangle()
                    if control.is_visible() and rect.width() > 10 and rect.height() > 9:
                        matches.append(control)
                except (AttributeError, RuntimeError, ValueError):
                    continue
        return matches[0] if len(matches) == 1 else None

    eventually(lambda: all(row(name) is not None for name in files),
               "PX10 test-owned source rows absent", 14)
    focus()
    element("MoreButton").invoke()
    toggle = eventually(lambda: live_menu(label="왼쪽 이름 필터"),
                        "PX10 owned filter flyout item absent", 8)
    assert owned_foreground() and toggle.element_info.process_id == pid
    toggle.invoke()
    box = element("LeftNameFilterBox")
    eventually(lambda: box.is_visible() and box.rectangle().width() > 60,
               "PX10 filter editor did not open", 7)
    print("PX10_GUI_OWNED_FILTER_OPEN=PASS", flush=True)

    one = row(files[0])
    two = row(files[1])
    assert one is not None and two is not None
    one.select()
    two = row(files[1])
    assert two is not None
    two.iface_selection_item.AddToSelection()
    eventually(pair, "PX10 initial multi-selection absent", 10)
    row(files[0]).set_focus()
    assert owned_foreground() and row(files[0]).has_keyboard_focus()

    # ValuePattern changes the test-owned editor without physically
    # changing keyboard focus to it. The focused file should survive FillFiles.
    box.iface_value.SetValue("Alpha")
    eventually(lambda: pair() and row(files[2]) is None,
               "PX10 filter lost two matching selected files", 12)
    print("PX10_GUI_FILTER_TWO_SELECTED=PASS", flush=True)
    assert row(files[0]).has_keyboard_focus(), (
        "PX10 native focused file not restored after filter")
    print("PX10_GUI_FILTER_FOCUSED_FILE=PASS", flush=True)

    def type_group():
        focus()
        element("ViewButton").invoke()
        item = eventually(lambda: live_menu(ident="ViewGroupByTypeItem"),
                          "PX10 View Type group menu absent", 9)
        item.set_focus()
        assert owned_foreground() and item.has_keyboard_focus()
        keyboard.send_keys("{ENTER}")

    def grouped():
        return any(".txt" in node.window_text()
                   for node in element("LeftFiles").descendants()
                   if node.element_info.control_type == "Button")

    type_group()
    eventually(lambda: pair() and grouped(),
               "PX10 grouped projection dropped selected pair", 14)
    assert left_active() and owned_foreground()
    print("PX10_GUI_GROUP_TWO_SELECTED=PASS", flush=True)

    row(files[0]).set_focus()
    assert row(files[0]).has_keyboard_focus()
    box.iface_value.SetValue("")
    eventually(lambda: pair() and row(files[2]) is not None,
               "PX10 grouped filter-clear dropped selected pair", 12)
    assert row(files[0]).has_keyboard_focus(), (
        "PX10 grouped redraw lost selected row keyboard focus")
    print("PX10_GUI_GROUPED_REFRESH_FOCUS=PASS", flush=True)

    type_group()   # Selecting Type again explicitly turns grouping off.
    eventually(lambda: pair() and not grouped(),
               "PX10 ungrouped pair/heading coherence failed", 12)
    print("PX10_GUI_UNGROUP_TWO_SELECTED=PASS", flush=True)

    box.iface_value.SetValue("Mango")
    eventually(lambda: row(files[0]) is None and row(files[1]) is None and
               "선택됨" not in element("SelectionCountText").window_text(),
               "PX10 filtered-out rows retained ghost selection", 12)
    print("PX10_GUI_EXCLUDED_NO_GHOST_SELECTION=PASS", flush=True)
    box.iface_value.SetValue("")
    eventually(lambda: row(files[0]) is not None and row(files[1]) is not None and
               "선택됨" not in element("SelectionCountText").window_text(),
               "PX10 cleared filter resurrected unselected rows", 12)
    assert left_active()
    assert all(hashlib.sha256((left / name).read_bytes()).digest() == digest
               for name, digest in checksums.items())
    print("PX10_GUI_ORIGINAL_FILE_HASHES_UNCHANGED=PASS", flush=True)
