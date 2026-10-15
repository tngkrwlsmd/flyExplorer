"""F05 exact owned Windows: independent left/right type-group state and route reset.

Opt-in FLY_F05_PANES_ONLY=YES; all input targets belong to the spawned
flyExplorer and all fixtures to the harness-owned Left/Right directories.
No user files or OS display/accessibility settings are modified.
"""
from pathlib import Path
from pywinauto import Desktop
import ctypes
from ctypes import wintypes
import time


def run(*,win,element,safe_click,eventually,left,right):
    assert left.parent==right.parent and left.name=="Left" and right.name=="Right"
    assert all((left/name).is_file() for name in
               ("readme.txt","group-guide.md","group-events.log"))
    assert all((right/name).is_file() for name in
               ("group-right.txt","group-right.md","group-right.log"))
    assert (right/"Secondary").is_dir()
    app=win.wrapper_object()
    pid=app.element_info.process_id
    assert pid>0
    user=ctypes.windll.user32
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[
        wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]

    def foreground_owned():
        hwnd=user.GetForegroundWindow()
        process=wintypes.DWORD()
        if hwnd:user.GetWindowThreadProcessId(hwnd,ctypes.byref(process))
        return process.value==pid

    def row(side,name):
        return next((entry for entry in element(side).descendants()
                     if entry.element_info.control_type=="ListItem"
                     and name in entry.window_text()),None)

    def disclosure(side,ext):
        return next((entry for entry in element(side).descendants()
                     if entry.element_info.control_type=="Button"
                     and ext in entry.window_text()),None)

    def owned_menu():
        # Flyout is often a separate top-level WinUI HWND. Only touch UIA
        # peers belonging to this test-owned process.
        for top in Desktop(backend="uia").windows():
            if top.element_info.process_id!=pid:continue
            for child in [top,*top.descendants()]:
                if child.element_info.automation_id!="ViewGroupByTypeItem":
                    continue
                # WinUI retains UIA peers for dismissed MenuFlyout roots.
                # The first matching ID need not be the menu just opened.
                # Only return an onscreen, live, hit-testable menu peer.
                try:
                    bounds=child.rectangle()
                    if not child.is_visible() or bounds.width()<12 or bounds.height()<12:
                        continue
                    location=bounds.mid_point()
                    user.WindowFromPoint.argtypes=[wintypes.POINT]
                    user.WindowFromPoint.restype=wintypes.HWND
                    hit=user.WindowFromPoint(wintypes.POINT(location.x,location.y))
                    process=wintypes.DWORD()
                    if hit:user.GetWindowThreadProcessId(hit,ctypes.byref(process))
                    if process.value!=pid:
                        continue
                    return child
                except (AttributeError,RuntimeError,ValueError):
                    continue
        return None

    def enable_group(side,expected_names):
        assert foreground_owned(),"Refuse opening flyout outside owned foreground"
        print("F05_BEFORE_MENU="+side+
              " STATUS_UESC="+element("StatusText").window_text().encode(
                  "unicode_escape").decode("ascii"),flush=True)
        element("ViewButton").invoke()
        menu=eventually(owned_menu,"Owned group menu item not visible",9)
        assert menu.element_info.process_id==pid
        try:
            toggle_state=str(menu.iface_toggle.CurrentToggleState)
        except Exception as exc:
            toggle_state=type(exc).__name__
        print("F05_MENU_TOGGLE_BEFORE="+side+" VALUE="+toggle_state,
              flush=True)
        assert foreground_owned(),"Refuse foreign foreground mouse input"
        menu.click_input()  # ToggleMenuFlyoutItem lacks InvokePattern
        print("F05_GROUP_TOGGLE_DIAG="+side+
              " ACTIVE="+element("ActivePaneText").window_text()+
              " STATUS_UESC="+element("StatusText").window_text().encode(
                  "unicode_escape").decode("ascii")+
              " LEFT_HEADINGS="+str(sum(disclosure("LeftFiles",ext) is not None
                                        for ext in (".txt",".md",".log")))+
              " RIGHT_HEADINGS="+str(sum(disclosure("RightFiles",ext) is not None
                                         for ext in (".txt",".md",".log"))),
              flush=True)
        try:
            eventually(lambda:all(disclosure(side,ext) is not None
                                  for ext in (".txt",".md",".log")),
                       "Full group headings were not displayed in "+side,12)
        except AssertionError:
            assert foreground_owned(),"Refuse follow-up outside owned GUI"
            element("ViewButton").invoke()
            opened=eventually(owned_menu,"Follow-up View menu not visible",7)
            assert opened.element_info.process_id==pid
            try:
                checked=str(opened.iface_toggle.CurrentToggleState)
            except Exception as exc:
                checked=type(exc).__name__
            print("F05_MENU_TOGGLE_AFTER_FAILED_CLICK="+side+
                  " VALUE="+checked,flush=True)
            raise
        for name in expected_names:
            assert row(side,name),"Grouped real file missing: "+name

    def navigate_right(folder):
        safe_click(element("RightFiles"))
        address=element("AddressBox")
        address.set_edit_text(str(folder))
        address.type_keys("{ENTER}",set_foreground=True)
        eventually(lambda:address.get_value().rstrip("\\/").lower()==
                   str(folder).rstrip("\\/").lower(),
                   "Right pane did not navigate to owned folder",15)

    eventually(lambda:row("LeftFiles","readme.txt") and
               row("LeftFiles","group-guide.md"),
               "Left synthetic rows unavailable",12)
    assert disclosure("LeftFiles",".md") is None
    assert disclosure("RightFiles",".md") is None
    print("F05_BOTH_PANES_START_UNGROUPED=PASS",flush=True)

    navigate_right(right)
    eventually(lambda:row("RightFiles","group-right.txt") and
               row("RightFiles","group-right.md") and
               row("RightFiles","group-right.log"),
               "Right synthetic metadata rows unavailable",15)
    # Complete file enumeration and its owned metadata worker are async.
    time.sleep(.8)
    enable_group("RightFiles",("group-right.txt","group-right.md","group-right.log"))
    assert disclosure("LeftFiles",".md") is None,(
        "Right grouping unexpectedly enabled left grouping")
    print("F05_RIGHT_GROUP_DOES_NOT_GROUP_LEFT=PASS",flush=True)

    safe_click(disclosure("RightFiles",".md"))
    eventually(lambda:row("RightFiles","group-right.md") is None,
               "Right Markdown collapse did not hide right Markdown",10)
    assert row("RightFiles","group-right.txt"),"Right TXT incorrectly hidden"
    print("F05_RIGHT_MD_COLLAPSED=PASS",flush=True)

    safe_click(element("LeftFiles"))
    safe_click(eventually(lambda:row("LeftFiles","readme.txt"),
                          "Left owned row disappeared after right collapse",8))
    eventually(lambda:"왼쪽" in element("ActivePaneText").window_text(),
               "Left pane never became active after real click",9)
    print("F05_LEFT_REACTIVATED="+element("ActivePaneText").window_text(),flush=True)
    enable_group("LeftFiles",("readme.txt","group-guide.md","group-events.log"))
    assert disclosure("RightFiles",".md") is not None
    assert row("RightFiles","group-right.md") is None,(
        "Left grouping unexpectedly expanded collapsed right Markdown")
    safe_click(disclosure("LeftFiles",".log"))
    eventually(lambda:row("LeftFiles","group-events.log") is None,
               "Left log disclosure failed",9)
    assert row("LeftFiles","readme.txt")
    assert row("RightFiles","group-right.log"),(
        "Left log disclosure incorrectly collapsed the right log group")
    print("F05_LEFT_RIGHT_COLLAPSE_INDEPENDENT=PASS",flush=True)

    # Revisiting a pane must restore its view toggle and preserve the
    # other pane's group state, not propagate or silently reenable it.
    safe_click(eventually(lambda:row("RightFiles","group-right.txt"),
                          "Right TXT disappeared after left collapse",9))
    assert row("RightFiles","group-right.md") is None
    assert row("LeftFiles","group-events.log") is None
    print("F05_SWITCH_PANES_GROUP_STATE_PRESERVED=PASS",flush=True)

    navigate_right(right/"Secondary")
    eventually(lambda:disclosure("RightFiles",".md") is None
               and disclosure("RightFiles",".txt") is None,
               "Old route's disclosure headings survived right navigation",13)
    assert row("LeftFiles","readme.txt") and (
           row("LeftFiles","group-events.log") is None), (
           "Right route navigation destroyed left pane's independent state")
    print("F05_RIGHT_ROUTE_INVALIDATES_OLD_GROUP=PASS",flush=True)

    navigate_right(right)
    eventually(lambda:row("RightFiles","group-right.md"),
               "Right file rows missing after navigation back",13)
    assert disclosure("RightFiles",".md") is None,(
        "Group mode was resurrected by a stale right route")
    assert disclosure("LeftFiles",".md") is not None
    assert row("LeftFiles","group-events.log") is None
    print("F05_RIGHT_NAVIGATION_DOES_NOT_TOUCH_LEFT=PASS",flush=True)
