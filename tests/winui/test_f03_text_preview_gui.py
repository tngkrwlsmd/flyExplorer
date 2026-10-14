"""Owned F03 GUI smoke: user opt-in, text bytes, stale selection and opt-out.

Invoked only from test_shell_gui.py with FLY_F03_TEXT_ONLY=YES. All
materialized files are within that harness' synthetic Left/Right roots.
"""
from pathlib import Path
import os
from paths import ROOT
from uuid import uuid4
import ctypes
from ctypes import wintypes
import time


def run(*, win, element, safe_click, eventually, left, right):
    assert Path(left).is_dir() and Path(right).is_dir()
    open_details=element("FileInfoToggleButton")
    preview_button=element("TextPreviewToggleButton")
    def body_text():
        # WinUI may omit an empty TextBlock from UIA entirely.
        node=element("TextPreviewBody")
        return node.window_text() if node.exists(timeout=.2) else ""
    preview_status=element("TextPreviewStatus")
    assert open_details.exists(timeout=5)
    assert not preview_button.exists(timeout=.3), "F03 must start collapsed"
    safe_click(open_details)
    # Check file identity while upper metadata is still on screen,
    # before scrolling down to the bottom-only opt-in controls.
    def row(name):
        view=element("LeftFiles")
        return next((x for x in view.descendants()
                     if x.element_info.control_type=="ListItem"
                     and name in x.window_text()),None)
    readme=eventually(lambda:row("readme.txt"),
                      "Owned TXT row not found",12)
    safe_click(readme)
    eventually(lambda:element("FileInfoName").window_text()=="readme.txt",
               "Selected file identity mismatch",9)
    assert body_text()=="", "Default-disabled view showed content"
    # F02 proved the Details ScrollViewer may virtualize low/offscreen
    # TextBlocks out of UIA. Scroll only *inside this owned app pane*;
    # do not change XAML to chase an offscreen automation element.
    from pywinauto import mouse
    eventually(lambda:element("FileInfoLocation").exists(timeout=.3),
               "Owned Details pane did not open",9)
    location=element("FileInfoLocation")
    rect=location.rectangle()
    pane=element("FileInfoPane")
    bounds=pane.rectangle()
    point=rect.mid_point()
    assert pane.element_info.process_id==win.element_info.process_id
    assert bounds.left<=point.x<=bounds.right and bounds.top<=point.y<=bounds.bottom
    win.set_focus()
    mouse.scroll(wheel_dist=-12,coords=(point.x,point.y))
    eventually(lambda:preview_button.exists(timeout=.4) and
               preview_status.exists(timeout=.3),
               "Owned Details scroll did not reveal opt-in text controls",10)
    print("F03_GUI_OWNED_DETAILS_SCROLL_REVEALED_CONTROLS=PASS",flush=True)
    assert "켜기" in preview_button.window_text()
    assert body_text()==""
    assert "꺼" in preview_status.window_text()
    def capture_owned_window(stage):
        # Only the current harness-owned flyExplorer top-level window.
        app=win.wrapper_object()
        app.set_focus()
        user=ctypes.windll.user32
        user.GetForegroundWindow.restype=wintypes.HWND
        user.GetWindowThreadProcessId.argtypes=[
            wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        foreground=user.GetForegroundWindow()
        pid=wintypes.DWORD()
        assert foreground==app.handle, "Refuse to capture any foreign window"
        user.GetWindowThreadProcessId(foreground,ctypes.byref(pid))
        assert pid.value==app.element_info.process_id, "Foreign process screenshot refused"
        image=app.capture_as_image()
        assert image.width>=650 and image.height>=400, "Unexpected owned app image bounds"
        dest=ROOT/"logs"/"f03-visual"
        assert dest.resolve(strict=False).is_relative_to((ROOT/"logs").resolve())
        dest.mkdir(parents=True,exist_ok=True)
        path=dest/("f03-owned-"+stage+"-"+uuid4().hex+".png")
        image.save(path,format="PNG",optimize=True)
        assert 0<path.stat().st_size<=3*1024*1024
        print("F03_GUI_OWNED_WINDOW_"+stage.upper()+"_PNG="+str(path),flush=True)

    print("F03_GUI_DEFAULT_OFF_NO_AUTO_CONTENT_READ=PASS",flush=True)

    capture_owned_window("before")

    # The control can be below the Details scroll viewport; use only this
    # owned WinUI window's exposed Invoke pattern.
    try:
        preview_button.iface_scroll_item.ScrollIntoView()
    except Exception:
        pass
    preview_button.iface_invoke.Invoke()
    eventually(lambda:"owned synthetic only" in body_text(),
               "Explicit text read was not shown",14)
    assert "끄기" in preview_button.window_text()
    capture_owned_window("after")
    print("F03_GUI_EXPLICIT_TEXT_CONTENT=PASS",flush=True)

    nested=eventually(lambda:row("Nested"),
                      "Owned second row not found",8)
    safe_click(nested)
    eventually(lambda:bool(nested.iface_selection_item.CurrentIsSelected),
               "Owned folder selection did not settle",7)
    eventually(lambda:body_text()=="" and
               "텍스트 파일" in preview_status.window_text(),
               "Stale text content retained after selecting a folder",9)
    # Wait for the actual SelectionItem state and UI layout to settle
    # before attempting another *physical* click on this owned ListView.
    time.sleep(.45)
    print("F03_GUI_SELECTION_CHANGED_DISCARDS_OLD_BYTES=PASS",flush=True)

    readme=eventually(lambda:row("readme.txt"),
                      "Owned text row unavailable after selection switch",8)
    safe_click(readme)
    # In an extended-selection ListView, physical UIA click_input is
    # not proof that the selection actually changed. Capture the actual
    # selected bit before diagnosing the asynchronous Preview controller.
    selected_until=time.monotonic()+2.5
    after_click=False
    while time.monotonic()<selected_until:
        current=row("readme.txt")
        if current and bool(current.iface_selection_item.CurrentIsSelected):
            readme=current
            after_click=True
            break
        time.sleep(.12)
    selection=readme.iface_selection_item
    print("F03_GUI_RESELECT_SETTLED_PHYSICAL_CLICK_SELECTED="+str(after_click),flush=True)
    if not after_click:
        # Physical click_input targets the UIA item's center. With a
        # multi-select ListView, verify a filename-side physical click
        # separately before falling back to SelectionItem.Select().
        from pywinauto import mouse
        target=readme.rectangle()
        list_rect=element("LeftFiles").rectangle()
        root_rect=win.rectangle()
        # Both the target point and the ListView must belong to the
        # harness-owned foreground process; never click foreign pixels.
        x=target.left+min(65,max(8,target.width()//4))
        y=(target.top+target.bottom)//2
        assert target.width()>=85 and target.height()>=22
        assert list_rect.left+4<x<list_rect.right-4
        assert list_rect.top+4<y<list_rect.bottom-4
        assert root_rect.left+8<x<root_rect.right-8
        assert root_rect.top+8<y<root_rect.bottom-8
        win.set_focus()
        user=ctypes.windll.user32
        user.GetForegroundWindow.restype=wintypes.HWND
        user.GetWindowThreadProcessId.argtypes=[
            wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        foreground=user.GetForegroundWindow()
        pid=wintypes.DWORD()
        user.GetWindowThreadProcessId(foreground,ctypes.byref(pid))
        assert foreground==win.handle and pid.value==win.element_info.process_id, (
            "Refuse physical click without owned foreground")
        # Guard the pixel itself, not only the foreground title: floating
        # or foreign always-on-top windows must never receive test clicks.
        user.WindowFromPoint.argtypes=[wintypes.POINT]
        user.WindowFromPoint.restype=wintypes.HWND
        user.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT]
        user.GetAncestor.restype=wintypes.HWND
        hit=user.WindowFromPoint(wintypes.POINT(x,y))
        hit_root=user.GetAncestor(hit,2) if hit else None  # GA_ROOT
        hit_pid=wintypes.DWORD()
        if hit_root:
            user.GetWindowThreadProcessId(hit_root,ctypes.byref(hit_pid))
        assert hit_root==win.handle and hit_pid.value==pid.value, (
            "Refuse pointer input at a foreign or obscured pixel")
        ctrl=bool(user.GetAsyncKeyState(0x11)&0x8000)
        shift=bool(user.GetAsyncKeyState(0x10)&0x8000)
        print("F03_GUI_RESELECT_INPUT_MODIFIERS_CTRL="+str(ctrl)+" SHIFT="+str(shift),flush=True)
        assert not ctrl and not shift, "Refuse ambiguous modified mouse selection"
        print("F03_GUI_RESELECT_TARGET_RELATIVE_X="+str(x-list_rect.left),flush=True)
        print("F03_GUI_RESELECT_ITEM_WIDTH="+str(target.width()),flush=True)
        print("F03_GUI_RESELECT_LIST_WIDTH="+str(list_rect.width()),flush=True)
        print("F03_GUI_RESELECT_TARGET_Y_IN_LIST="+str(y-list_rect.top),flush=True)
        mouse.click(button="left",coords=(x,y))
        deadline=time.monotonic()+2.5
        while time.monotonic()<deadline:
            current=row("readme.txt")
            if current and bool(current.iface_selection_item.CurrentIsSelected):
                readme=current
                after_click=True
                break
            time.sleep(.12)
        print("F03_GUI_RESELECT_FILENAME_PHYSICAL_CLICK_SELECTED="+str(after_click),flush=True)
    # With SelectionMode=Multiple, a selected TXT alongside the
    # still-selected folder is not a valid single-file Preview choice.
    both=bool(readme.iface_selection_item.CurrentIsSelected) and bool(
        row("Nested").iface_selection_item.CurrentIsSelected)
    print("F03_GUI_RESELECT_BOTH_ROWS_SELECTED="+str(both),flush=True)
    physical_single=after_click and not both
    print("F03_GUI_RESELECT_PHYSICAL_SINGLE_SELECTION="+str(physical_single),flush=True)
    if os.environ.get("FLY_F03_STRICT_PHYSICAL_RESELECT")=="YES":
        print("F03_GUI_STRICT_PHYSICAL_RESELECT="+
              ("PASS" if physical_single else "FAIL"),flush=True)
        assert physical_single, (
            "Owned filename-side physical click did not establish one TXT "
            "selection; do not treat UIA Select() as mouse acceptance")
    if not physical_single:
        selection.Select()
        eventually(lambda:bool(readme.iface_selection_item.CurrentIsSelected) and
                   not bool(row("Nested").iface_selection_item.CurrentIsSelected),
                   "Owned UIA Select did not establish exactly one TXT",7)
        print("F03_GUI_RESELECT_UIA_SELECT_FALLBACK=PASS",flush=True)
    eventually(lambda:"owned synthetic only" in body_text(),
               "SelectionItem-confirmed reselect did not trigger owned text request",14)

    preview_button.iface_invoke.Invoke()
    eventually(lambda:body_text()=="" and
               "꺼" in preview_status.window_text(),
               "Disabled view did not clear previous bytes",8)
    print("F03_GUI_EXPLICIT_OPTOUT_CLEARS_CONTENT=PASS",flush=True)

    safe_click(open_details)
    assert not preview_button.exists(timeout=.3)
    safe_click(open_details)
    eventually(lambda:preview_button.exists(timeout=.5) and
               "켜기" in preview_button.window_text() and
               body_text()=="",
               "Reopened Details unexpectedly enabled text reader",9)
    print("F03_GUI_REOPEN_REQUIRES_NEW_OPTIN=PASS",flush=True)
