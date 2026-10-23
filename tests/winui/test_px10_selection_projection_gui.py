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

    def no_ghost_selection():
        # At zero selected rows, WinUI can omit its empty TextBlock from
        # UIA entirely. Require no actual selected ListItems, then accept
        # either an absent badge or a visibly empty one.
        selected_rows = [
            node for node in element("LeftFiles").descendants()
            if node.element_info.control_type == "ListItem" and
            node.is_selected()
        ]
        if selected_rows:
            return False
        badge = element("SelectionCountText")
        if not badge.exists(timeout=.1):
            return True
        return not badge.window_text().strip()

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
    # Existing real GUI acceptance uses Ctrl+Shift+F, not a guessed
    # UIA label for the More flyout's popup MenuFlyoutItem.
    focus()
    element("LeftFiles").set_focus()
    assert owned_foreground()
    keyboard.send_keys("^+f")
    box = element("LeftNameFilterBox")
    eventually(lambda: box.has_keyboard_focus() and
               box.is_visible() and box.rectangle().width() > 60,
               "PX10 Ctrl+Shift+F failed to focus the owned left editor", 7)
    print("PX10_GUI_OWNED_FILTER_OPEN=PASS", flush=True)

    one = row(files[0])
    two = row(files[1])
    assert one is not None and two is not None
    one.select()
    two = row(files[1])
    assert two is not None
    two.iface_selection_item.AddToSelection()
    eventually(pair, "PX10 initial multi-selection absent", 10)
    # User-physical filter entry focuses the editor; it must remain the
    # keyboard target while the selected file rows are rebuilt underneath.
    box.set_focus()
    assert owned_foreground() and box.has_keyboard_focus()
    keyboard.send_keys("Alpha")
    eventually(lambda: box.get_value() == "Alpha" and pair() and
               row(files[2]) is None,
               "PX10 physical filter lost the editor or selected pair", 12)
    print("PX10_GUI_FILTER_TWO_SELECTED=PASS", flush=True)
    assert box.has_keyboard_focus(), (
        "PX10 active filter editor lost keyboard focus during redraw")
    print("PX10_GUI_FILTER_EDITOR_FOCUS=PASS", flush=True)

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

    # After grouping, a selected native file is still keyboard focusable.
    row(files[0]).set_focus()
    assert owned_foreground() and row(files[0]).has_keyboard_focus(), (
        "PX10 grouped native file did not accept keyboard focus")
    print("PX10_GUI_GROUPED_FILE_FOCUSABLE=PASS", flush=True)
    # A real keyboard filter edit should keep the editor focused across
    # another rebuild; selected file identities remain unchanged.
    box.set_focus()
    assert owned_foreground() and box.has_keyboard_focus()
    keyboard.send_keys("^a{BACKSPACE}")
    eventually(lambda: box.get_value() == "" and pair() and
               row(files[2]) is not None,
               "PX10 grouped keyboard filter-clear dropped selected pair", 12)
    assert box.has_keyboard_focus(), (
        "PX10 grouped redraw lost active filter editor keyboard focus")
    print("PX10_GUI_GROUPED_EDITOR_FOCUS=PASS", flush=True)

    type_group()   # Selecting Type again explicitly turns grouping off.
    eventually(lambda: pair() and not grouped(),
               "PX10 ungrouped pair/heading coherence failed", 12)
    print("PX10_GUI_UNGROUP_TWO_SELECTED=PASS", flush=True)

    box.set_focus()
    assert owned_foreground() and box.has_keyboard_focus()
    keyboard.send_keys("^a{BACKSPACE}Mango")
    eventually(lambda: box.get_value() == "Mango" and
               row(files[0]) is None and row(files[1]) is None and
               row(files[2]) is not None and no_ghost_selection(),
               "PX10 filtered-out rows retained ghost selection", 12)
    print("PX10_GUI_EXCLUDED_NO_GHOST_SELECTION=PASS", flush=True)
    assert box.has_keyboard_focus()
    keyboard.send_keys("^a{BACKSPACE}")
    eventually(lambda: box.get_value() == "" and
               row(files[0]) is not None and row(files[1]) is not None and
               no_ghost_selection(),
               "PX10 cleared filter resurrected unselected rows", 12)
    assert left_active()
    assert all(hashlib.sha256((left / name).read_bytes()).digest() == digest
               for name, digest in checksums.items())
    print("PX10_GUI_ORIGINAL_FILE_HASHES_UNCHANGED=PASS", flush=True)
