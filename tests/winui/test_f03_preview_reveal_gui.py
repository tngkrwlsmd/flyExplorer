"""F03 owned focus/scroll affordance: reveal cannot opt in on its own.

Run only under FLY_F03_REVEAL_ONLY=YES from disposable test_shell_gui.py.
Screenshot only the owned app window; never capture an unrelated desktop.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
from uuid import uuid4
from pywinauto import keyboard
from paths import ROOT


def run(*, win, element, safe_click, eventually, left, right):
    assert Path(left).is_dir() and Path(right).is_dir()
    assert "owned" in str(left).lower()
    open_details=element("FileInfoToggleButton")
    reveal=element("TextPreviewRevealButton")
    toggle=element("TextPreviewToggleButton")
    body=element("TextPreviewBody")

    def body_text():
        return body.window_text() if body.exists(timeout=.2) else ""

    def readme_row():
        return next((item for item in element("LeftFiles").descendants()
                     if item.element_info.control_type=="ListItem"
                     and "readme.txt" in item.window_text()),None)

    assert not reveal.exists(timeout=.25), "Details should start closed"
    safe_click(open_details)
    eventually(lambda:reveal.exists(timeout=.3) and reveal.is_visible(),
               "Top-of-Details reveal control not accessible",9)
    row=eventually(readme_row,"Owned readme.txt not found",9)
    safe_click(row)
    eventually(lambda:element("FileInfoName").window_text()=="readme.txt",
               "Selected file metadata did not update",9)
    assert body_text()=="", "Content read before explicit opt-in"
    assert "이동" in reveal.window_text()
    print("F03_REVEAL_STARTS_OFF=PASS",flush=True)

    def screenshot(stage):
        app=win.wrapper_object()
        app.set_focus()
        user=ctypes.windll.user32
        user.GetForegroundWindow.restype=wintypes.HWND
        user.GetWindowThreadProcessId.argtypes=[
            wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        hwnd=user.GetForegroundWindow()
        pid=wintypes.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        assert hwnd==app.handle and pid.value==app.element_info.process_id, (
            "Refuse screenshot outside harness-owned foreground window")
        dest=ROOT/"logs"/"f03-visual"
        assert dest.resolve(strict=False).is_relative_to(
            (ROOT/"logs").resolve())
        dest.mkdir(parents=True,exist_ok=True)
        img=app.capture_as_image()
        assert img.width>=650 and img.height>=400
        path=dest/("f03-reveal-"+stage+"-"+uuid4().hex+".png")
        img.save(path,format="PNG",optimize=True)
        assert 0<path.stat().st_size<=3*1024*1024
        print("F03_REVEAL_SCREENSHOT_"+stage.upper()+"_PNG="+str(path),
              flush=True)

    screenshot("top")
    reveal.set_focus()
    keyboard.send_keys("{ENTER}")
    eventually(lambda:toggle.exists(timeout=.3) and toggle.is_visible(),
               "Keyboard activation did not bring original opt-in into view",10)
    assert "켜기" in toggle.window_text()
    assert body_text()=="", "Reveal was mistaken for content opt-in"
    print("F03_REVEAL_KEYBOARD_FOCUS=PASS",flush=True)
    screenshot("focused")
    # Press Space in the focused original opt-in Button, not UIA Invoke:
    # the physical keyboard gesture is the separate user permission.
    toggle.set_focus()
    keyboard.send_keys("{SPACE}")
    eventually(lambda:"owned synthetic only" in body_text(),
               "Keyboard opt-in did not show the selected owned TXT",14)
    assert "끄기" in toggle.window_text()
    print("F03_REVEAL_EXPLICIT_OPTIN=PASS",flush=True)
