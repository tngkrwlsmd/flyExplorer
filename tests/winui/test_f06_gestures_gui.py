"""F06 owned real-WinUI folder/breadcrumb middle-click and quoted path probe.

Only test-owned local folders are opened; no UNC remote resource is accessed.
The test does not change global Explorer preferences, clipboard or user files.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
from pywinauto import mouse

def run(*,win,element,safe_click,focus,eventually,owned,left,right):
    assert Path(left).is_relative_to(owned) and Path(right).is_relative_to(owned)
    user=ctypes.windll.user32
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=(wintypes.HWND,ctypes.POINTER(wintypes.DWORD))
    pid=win.wrapper_object().element_info.process_id
    assert pid>0
    def owned_middle_click(control):
        focus()
        fg=user.GetForegroundWindow()
        owner=wintypes.DWORD()
        if fg:user.GetWindowThreadProcessId(fg,ctypes.byref(owner))
        assert fg and owner.value==pid,"refuse middle click on foreign HWND"
        point=control.rectangle().mid_point()
        mouse.click(button="middle",coords=(point.x,point.y))
    def pane_tabs(side):
        strip=element("LeftTabs" if side==0 else "RightTabs")
        return [t for t in strip.descendants()
                if t.element_info.control_type=="TabItem"]
    def address():
        return element("AddressBox").get_value().rstrip("\\/").lower()
    def row_for(name):
        return next((r for r in element("LeftFiles").descendants()
                     if r.element_info.control_type=="ListItem" and
                        name in r.window_text()),None)
    eventually(lambda:row_for("Nested") is not None,
               "F06 owned Nested row unavailable",15)
    initial=address()
    left_count=len(pane_tabs(0))
    right_count=len(pane_tabs(1))
    assert left_count==right_count==1
    row=row_for("Nested")
    print("F06_PRE_MIDDLE_ROW",row.rectangle(),"TABS",left_count,right_count,
          "ADDRESS_MATCH",bool(address()==initial),flush=True)
    owned_middle_click(row)
    try:
        eventually(lambda:len(pane_tabs(0))==left_count+1 and
                   "nested" in address(),
                   "F06 folder middle-click did not open pane-local tab",17)
    except AssertionError:
        print("F06_MIDDLE_FAILURE_DIAG","LEFT_TABS",len(pane_tabs(0)),
              "RIGHT_TABS",len(pane_tabs(1)),
              "NESTED_ADDRESS","nested" in address(),
              "ORIGINAL_ADDRESS",address()==initial,
              "STATUS",element("StatusText").window_text(),
              flush=True)
        raise
    assert len(pane_tabs(1))==right_count
    assert element("WindowTabStrip").exists(timeout=.3)
    print("F06_MIDDLE_CLICK_FOLDER_LOCAL_PANE_TAB=PASS",flush=True)
    # The original tab still preserves its route, even after the new tab loads.
    first=pane_tabs(0)[0]
    safe_click(first)
    eventually(lambda:address()==initial,
               "F06 middle-click replaced original tab location",10)
    second=pane_tabs(0)[1]
    safe_click(second)
    eventually(lambda:"nested" in address(),
               "F06 folder tab did not retain Nested path",10)
    def parent_segment():
        # StackPanel itself is not necessarily represented as a UIA element.
        # The tagged breadcrumb Buttons expose an accessible path name.
        return next((b for b in win.descendants(control_type="Button")
                     if (b.window_text() or "").strip()=="주소 경로: Left"),None)
    ancestor=eventually(parent_segment,
                        "F06 owned parent breadcrumb not found",8)
    owned_middle_click(ancestor)
    eventually(lambda:len(pane_tabs(0))==left_count+2 and
               address()==initial,
               "F06 breadcrumb middle-click did not create its own tab",16)
    assert len(pane_tabs(1))==right_count
    print("F06_BREADCRUMB_MIDDLE_CLICK_PANE_ISOLATION=PASS",flush=True)
    # Quoted pasted absolute path with Korean and spaces. Do not synthesize
    # a network share: UNC passthrough is source-verified separately.
    quoted=Path(left)/"한글 경로"
    quoted.mkdir()
    safe_click(element("LeftFiles"))
    box=element("AddressBox")
    box.set_edit_text('"'+str(quoted)+'"')
    focus()
    box.type_keys("{ENTER}",set_foreground=True)
    eventually(lambda:address()==str(quoted).rstrip("\\/").lower(),
               "F06 quoted Unicode folder path not parsed",20)
    assert len(pane_tabs(0))==left_count+2
    assert len(pane_tabs(1))==right_count
    print("F06_QUOTED_UNICODE_LOCAL_ADDRESS=PASS",flush=True)
