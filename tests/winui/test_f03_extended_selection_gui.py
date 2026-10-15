"""Physical Ctrl/Shift and keyboard selection on two owned WinUI file panes.

Invoked only via FLY_F03_EXTENDED_ONLY=YES in test_shell_gui.py.
Uses disposable fixture paths and refuses input outside the owned app.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import time
from pywinauto import keyboard, mouse


def run(*, win, element, safe_click, eventually, left, right):
    assert Path(left).is_dir() and Path(right).is_dir()
    app=win.wrapper_object()
    pid=app.element_info.process_id
    assert pid>0
    user=ctypes.windll.user32
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[
        wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.WindowFromPoint.argtypes=[wintypes.POINT]
    user.WindowFromPoint.restype=wintypes.HWND
    user.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT]
    user.GetAncestor.restype=wintypes.HWND

    def row(side,name):
        view=element(side)
        assert view.element_info.process_id==pid
        return next((x for x in view.descendants()
                     if x.element_info.control_type=="ListItem"
                     and name in x.window_text()),None)

    def selected(side,name):
        node=row(side,name)
        return node is not None and bool(
            node.iface_selection_item.CurrentIsSelected)

    def only(side,name):
        other="Nested" if name=="readme.txt" else "readme.txt"
        return selected(side,name) and not selected(side,other)

    def both(side):
        return selected(side,"Nested") and selected(side,"readme.txt")

    def modified_click(side,name,key):
        item=eventually(lambda:row(side,name),
                        "Owned row missing before modified click",9)
        rect=item.rectangle()
        view=element(side).rectangle()
        window=win.rectangle()
        x=rect.left+min(65,max(8,rect.width()//4))
        y=(rect.top+rect.bottom)//2
        assert rect.width()>=85 and rect.height()>=22
        assert view.left+4<x<view.right-4 and view.top+4<y<view.bottom-4
        assert window.left+8<x<window.right-8 and window.top+8<y<window.bottom-8
        win.set_focus()
        foreground=user.GetForegroundWindow()
        owner=wintypes.DWORD()
        if foreground:
            user.GetWindowThreadProcessId(foreground,ctypes.byref(owner))
        assert foreground==app.handle and owner.value==pid, (
            "Refuse input without owned foreground")
        hit=user.WindowFromPoint(wintypes.POINT(x,y))
        hit_root=user.GetAncestor(hit,2) if hit else None
        hit_owner=wintypes.DWORD()
        if hit_root:
            user.GetWindowThreadProcessId(hit_root,ctypes.byref(hit_owner))
        assert hit_root==app.handle and hit_owner.value==pid, (
            "Refuse modified click at foreign or obscured pixel")
        assert not (user.GetAsyncKeyState(0x11)&0x8000)
        assert not (user.GetAsyncKeyState(0x10)&0x8000)
        held="{VK_CONTROL" if key=="Ctrl" else "{VK_SHIFT"
        keyboard.send_keys(held+" down}")
        try:
            mouse.click(button="left",coords=(x,y))
        finally:
            keyboard.send_keys(held+" up}")
        time.sleep(.16)

    for side in ("LeftFiles","RightFiles"):
        eventually(lambda:row(side,"Nested") and row(side,"readme.txt"),
                   "Expected paired synthetic rows in "+side,15)
        safe_click(row(side,"Nested"))
        eventually(lambda:only(side,"Nested"),
                   "Plain click failed to select only Nested in "+side,9)
        keyboard.send_keys("{DOWN}")
        eventually(lambda:only(side,"readme.txt"),
                   "Arrow Down did not replace selection in "+side,9)
        print("F03_EXTENDED_"+side.upper()+"_KEYBOARD_DOWN=PASS",flush=True)

        modified_click(side,"Nested","Ctrl")
        eventually(lambda:both(side),"Ctrl+click did not add row in "+side,9)
        modified_click(side,"Nested","Ctrl")
        eventually(lambda:only(side,"readme.txt"),
                   "Ctrl+click did not toggle row off in "+side,9)
        print("F03_EXTENDED_"+side.upper()+"_CTRL_TOGGLE=PASS",flush=True)

        safe_click(row(side,"Nested"))
        eventually(lambda:only(side,"Nested"),
                   "Plain click did not reset selection in "+side,9)
        modified_click(side,"readme.txt","Shift")
        eventually(lambda:both(side),
                   "Shift+click did not select range in "+side,9)
        safe_click(row(side,"readme.txt"))
        eventually(lambda:only(side,"readme.txt"),
                   "Plain click did not clear Shift range in "+side,9)
        print("F03_EXTENDED_"+side.upper()+"_SHIFT_RANGE=PASS",flush=True)
        print("F03_EXTENDED_"+side.upper()+"_PLAIN_REPLACES=PASS",flush=True)
    print("F03_EXTENDED_BOTH_PANES_INPUT_PASS=True",flush=True)
