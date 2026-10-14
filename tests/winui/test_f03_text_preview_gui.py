"""Owned F03 GUI smoke: user opt-in, text bytes, stale selection and opt-out.

Invoked only from test_shell_gui.py with FLY_F03_TEXT_ONLY=YES. All
materialized files are within that harness' synthetic Left/Right roots.
"""
from pathlib import Path
from paths import ROOT
from uuid import uuid4
import ctypes
from ctypes import wintypes


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
    eventually(lambda:body_text()=="" and
               "텍스트 파일" in preview_status.window_text(),
               "Stale text content retained after selecting a folder",9)
    print("F03_GUI_SELECTION_CHANGED_DISCARDS_OLD_BYTES=PASS",flush=True)

    readme=eventually(lambda:row("readme.txt"),
                      "Owned text row unavailable after selection switch",8)
    safe_click(readme)
    eventually(lambda:"owned synthetic only" in body_text(),
               "New selection did not trigger owned text request",14)

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
