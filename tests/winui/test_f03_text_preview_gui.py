"""Owned F03 GUI smoke: user opt-in, text bytes, stale selection and opt-out.

Invoked only from test_shell_gui.py with FLY_F03_TEXT_ONLY=YES. All
materialized files are within that harness' synthetic Left/Right roots.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
from uuid import uuid4


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
    eventually(lambda:preview_button.exists(timeout=.4),
               "Details region missing opt-in control",9)
    assert "켜기" in preview_button.window_text()
    assert body_text()==""
    assert not preview_status.exists(timeout=.3), "Disabled status must not occupy Details layout"
    def screenshot(label):
        # Only pixels inside this harness-owned application HWND.
        from PIL import ImageGrab
        app=win.wrapper_object()
        user=ctypes.windll.user32
        user.GetForegroundWindow.restype=wintypes.HWND
        user.GetWindowThreadProcessId.argtypes=[
            wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        app.set_focus()
        foreground=user.GetForegroundWindow()
        owner=wintypes.DWORD()
        user.GetWindowThreadProcessId(foreground,ctypes.byref(owner))
        assert foreground==app.handle and owner.value==app.element_info.process_id, (
            "Refuse screenshot of any foreign window",label)
        rect=app.rectangle()
        assert rect.width()>600 and rect.height()>380
        crop=(rect.left+12,rect.top+8,rect.right-8,rect.bottom-8)
        dest=Path(__file__).resolve().parents[2]/"logs"/"f03-visual"
        assert dest.resolve(strict=False).is_relative_to(
            Path(__file__).resolve().parents[2]/"logs")
        dest.mkdir(parents=True,exist_ok=True)
        name="f03-owned-"+label+"-"+uuid4().hex+".png"
        ImageGrab.grab(bbox=crop,include_layered_windows=True).save(
            dest/name,format="PNG",optimize=True)
        assert (dest/name).stat().st_size<3*1024*1024
        print("F03_GUI_SYNTHETIC_WINDOW_"+label.upper()+"_PNG="+str(dest/name),flush=True)

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
    screenshot("before")

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
    screenshot("after")
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
               not preview_status.exists(timeout=.3),
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
