"""Focused F06 in-memory address candidate probe on an owned WinUI process."""
import ctypes
from ctypes import wintypes as W
from pathlib import Path
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


def run(*, win, element, focus, eventually, left, right, owned):
    assert Path(left).is_relative_to(owned) and Path(right).is_relative_to(owned)
    win_pid=win.wrapper_object().element_info.process_id
    assert win_pid>0
    user=ctypes.windll.user32
    user.GetForegroundWindow.restype=W.HWND
    user.GetWindowThreadProcessId.argtypes=(W.HWND,ctypes.POINTER(W.DWORD))
    def guarded_keys(text):
        focus()
        foreground=user.GetForegroundWindow()
        owner=W.DWORD()
        if foreground:user.GetWindowThreadProcessId(foreground,ctypes.byref(owner))
        assert foreground and owner.value==win_pid,"refuse input on foreign window"
        send_keys(text)
    def candidates():
        peers=[]
        for surface in Desktop(backend="uia").windows(process=win_pid):
            for child in surface.descendants(control_type="Button"):
                if child.element_info.process_id!=win_pid:
                    continue
                label=child.element_info.name or ""
                if label.startswith("주소 후보: "):
                    peers.append(child)
        return peers
    assert len(candidates())==0
    guarded_keys("^l")
    eventually(lambda:element("AddressBox").has_keyboard_focus(),
               "Ctrl+L did not focus original TextBox",8)
    address=element("AddressBox")
    typed=str(left)+"\\N"
    address.set_edit_text(typed)
    def find_nested():
        found=[b for b in candidates()
               if b.element_info.name=="주소 후보: "+str(left / "Nested")]
        return found[0] if len(found)==1 else None
    item=eventually(find_nested,
                    "F06 candidate not displayed for loaded owned Nested folder",10)
    assert len(candidates())<=8
    print("F06_BOUNDED_IN_MEMORY_ADDRESS_CANDIDATES=PASS",flush=True)
    item.iface_invoke.Invoke()
    eventually(lambda:element("AddressBox").get_value().rstrip("\\/").casefold()
               ==str(left / "Nested").rstrip("\\/").casefold(),
               "F06 selecting candidate did not navigate existing pane",15)
    assert len([x for x in element("LeftTabs").descendants()
                if x.element_info.control_type=="TabItem"])==1
    assert len([x for x in element("RightTabs").descendants()
                if x.element_info.control_type=="TabItem"])==1
    print("F06_ADDRESS_SUGGESTION_SELECT_NAVIGATES_SAME_TAB=PASS",flush=True)
    guarded_keys("^l")
    eventually(lambda:element("AddressBox").has_keyboard_focus(),
               "second Ctrl+L did not focus existing editor",8)
    element("AddressBox").set_edit_text(str(left)[:-1])
    eventually(lambda:len(candidates())>=1,
               "known left tab address suggestion missing",9)
    guarded_keys("{ESC}")
    eventually(lambda:len(candidates())==0,
               "escape did not dismiss address suggestions",7)
    print("F06_ADDRESS_SUGGESTION_ESCAPE_DISMISSES=PASS",flush=True)
