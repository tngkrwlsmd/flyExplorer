"""PX12: actual WinUI candidate click, committed location, and fail-closed UX.

Uses test_shell_gui's private profile, real WinUI process, and synthetic folder.
Never navigates to or modifies paths outside the verified owned fixture.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


def run(*, win, element, focus, eventually, left, right, owned):
    left = Path(left)
    assert left.is_relative_to(owned) and Path(right).is_relative_to(owned)
    pid = win.wrapper_object().element_info.process_id
    user = ctypes.windll.user32
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    def owned_foreground():
        hwnd = user.GetForegroundWindow()
        owner = wintypes.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        return bool(hwnd and owner.value == pid)

    def norm(value):
        return str(value).rstrip("\\/").casefold()

    def committed(path):
        return norm(element("AddressBox").get_value()) == norm(path)

    def has_row(name):
        return any(name in row.window_text() for row in
                   element("LeftFiles").descendants()
                   if row.element_info.control_type == "ListItem")

    def candidate(target):
        label = "주소 후보: " + str(target)
        matches = []
        for top in Desktop(backend="uia").windows(process=pid):
            for button in top.descendants(control_type="Button"):
                if button.element_info.process_id == pid and (
                        button.element_info.name == label):
                    matches.append(button)
        return matches[0] if len(matches) == 1 else None

    def offer(prefix, target):
        focus()
        assert owned_foreground()
        send_keys("^l")
        eventually(lambda: element("AddressBox").has_keyboard_focus(),
                   "PX12 Ctrl+L did not open owned address editor", 9)
        element("AddressBox").set_edit_text(str(prefix))
        item = eventually(lambda: candidate(target),
                          "PX12 expected owned candidate not offered", 11)
        assert item.element_info.process_id == pid
        assert owned_foreground()
        return item

    assert committed(left) and has_row("Nested") and has_row("readme.txt")
    # PX12 keyboard-only focus path: two owned, in-memory sibling candidates.
    # No candidate gets invoked and the committed folder must not change.
    assert owned_foreground()
    send_keys("^l")
    eventually(lambda: element("AddressBox").has_keyboard_focus(),
               "PX12 keyboard editor not focused", 9)
    element("AddressBox").set_edit_text(str(left) + "\\PX12")
    nearby = left / "PX12Nearby"
    vanishing = left / "PX12Vanishing"
    eventually(lambda: candidate(nearby) and candidate(vanishing),
               "PX12 two owned keyboard candidates missing", 9)
    # UIA SetValue does not guarantee real keyboard focus; explicitly ensure
    # that the owned TextBox, not an unrelated foreground element, receives Down.
    address = element("AddressBox")
    address.set_focus()
    eventually(lambda: address.has_keyboard_focus(),
               "PX12 editor lost real focus after SetValue", 8)
    assert candidate(nearby) and candidate(vanishing)
    # Preserve the actual view order rather than assuming filesystem-index
    # enumeration is lexicographic.
    targets = {str(nearby), str(vanishing)}
    ordered = []
    for top in Desktop(backend="uia").windows(process=pid):
        for button in top.descendants(control_type="Button"):
            name = button.element_info.name or ""
            if name.startswith("주소 후보: ") and name[7:] in targets:
                ordered.append(Path(name[7:]))
    assert len(ordered) == 2 and set(ordered) == {nearby, vanishing}, ordered
    first, second = ordered
    def press(keys):
        assert owned_foreground(), "Refuse keyboard input to foreign window"
        send_keys(keys)
    press("{DOWN}")
    eventually(lambda: candidate(first) and candidate(first).has_keyboard_focus(),
               "PX12 Down did not focus first candidate", 7)
    press("{DOWN}")
    eventually(lambda: candidate(second) and candidate(second).has_keyboard_focus(),
               "PX12 Down did not focus second candidate", 7)
    press("{DOWN}")
    assert candidate(second).has_keyboard_focus(), (
        "PX12 last candidate lost keyboard focus")
    press("{UP}")
    eventually(lambda: candidate(first) and candidate(first).has_keyboard_focus(),
               "PX12 Up did not focus previous candidate", 7)
    press("{UP}")
    eventually(lambda: element("AddressBox").has_keyboard_focus(),
               "PX12 Up did not restore address editor", 7)
    assert committed(left) is False
    press("{ESC}")
    eventually(lambda: candidate(first) is None and candidate(second) is None,
               "PX12 Escape failed to dismiss keyboard candidates", 8)
    # The first Escape only dismisses candidates; the second restores the
    # last committed breadcrumb (the accepted existing address contract).
    assert not committed(left)
    press("{ESC}")
    eventually(lambda: committed(left),
               "PX12 second Escape did not restore committed address", 8)
    print("PX12_GUI_KEYBOARD_CANDIDATE_UP_DOWN=PASS", flush=True)

    stale = left / "PX12Vanishing"
    assert stale.is_dir() and stale.is_relative_to(owned)
    item = offer(str(left) + "\\PX12V", stale)
    print("PX12_GUI_STALE_CANDIDATE_OFFERED=PASS", flush=True)

    # The candidate is already in a visible WinUI menu. Remove only the
    # disposable empty folder; the asynchronous Shell open must now fail.
    stale.rmdir()
    assert not stale.exists() and candidate(stale) is not None
    assert owned_foreground()
    item.iface_invoke.Invoke()
    # The direct-click handler should restore committed chrome immediately,
    # regardless of whether the async native failure has completed yet.
    assert committed(left), "PX12 stale candidate leaked pending path to address"
    print("PX12_GUI_FAILED_CANDIDATE_COMMITTED_ADDRESS=PASS", flush=True)
    eventually(lambda: "기존 폴더는 유지됩니다" in
               element("StatusText").window_text(),
               "PX12 missing real native Shell failed-navigation completion", 17)
    assert committed(left) and has_row("Nested") and has_row("readme.txt")
    assert not has_row("PX12OwnedDestination.txt")
    assert len(element("LeftTabs").descendants(control_type="TabItem")) == 1
    print("PX12_GUI_FAILED_CANDIDATE_PANE_RETAINED=PASS", flush=True)

    # Repeat with a real, known candidate. At the first observable moment
    # the address is either still committed Left or already committed Nested;
    # it must never show the half-typed candidate prefix.
    target = left / "Nested"
    item = offer(str(left) + "\\N", target)
    assert committed(left) is False  # Actual candidate prefix is being edited.
    assert owned_foreground()
    item.iface_invoke.Invoke()
    shown = norm(element("AddressBox").get_value())
    assert shown in (norm(left), norm(target)), (
        "PX12 valid candidate displayed uncommitted path")
    print("PX12_GUI_VALID_CANDIDATE_IMMEDIATE_CHROME=PASS", flush=True)
    eventually(lambda: committed(target) and
               has_row("PX12OwnedDestination.txt"),
               "PX12 actual successful candidate navigation not committed", 17)
    assert not has_row("readme.txt")
    assert len(element("LeftTabs").descendants(control_type="TabItem")) == 1
    print("PX12_GUI_VALID_CANDIDATE_NAVIGATED=PASS", flush=True)
