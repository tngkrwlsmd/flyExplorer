"""F03 owned app-start-to-Preview accessibility gate.

Unlike the focused reveal test, do not focus/click any UI control directly.
Only raise the owned app window; navigate the real Tab sequence with keyboard.
No OS display/accessibility setting is modified.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
from pywinauto import keyboard


def run(*, win, element, eventually, left, right):
    assert Path(left).is_dir() and Path(right).is_dir()
    assert Path(left).parent==Path(right).parent
    app=win.wrapper_object()
    pid=app.element_info.process_id
    assert pid>0
    user=ctypes.windll.user32
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[
        wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]

    def owned_foreground():
        hwnd=user.GetForegroundWindow()
        observed=wintypes.DWORD()
        if hwnd:
            user.GetWindowThreadProcessId(hwnd,ctypes.byref(observed))
        return hwnd==app.handle and observed.value==pid

    def key(sequence):
        assert owned_foreground(), (
            "Refuse physical keyboard input to a foreign foreground window")
        keyboard.send_keys(sequence)

    def focused(name):
        target=element(name)
        if not target.exists(timeout=.12):
            return False
        # UIA reports actual keyboard focus on the named WinUI control.
        state=target.element_info.has_keyboard_focus
        return bool(state() if callable(state) else state)

    details=element("FileInfoToggleButton")
    reveal=element("TextPreviewRevealButton")
    toggle=element("TextPreviewToggleButton")
    preview=element("TextPreviewBody")
    assert details.exists(timeout=3)
    assert not reveal.exists(timeout=.25), "Details unexpectedly visible"

    # Window activation is the only programmatic focus operation. Everything
    # after this line uses actual keyboard input, never target.set_focus().
    win.set_focus()
    assert owned_foreground(), "Owned app is not foreground at startup"

    def tabs_to(name,limit):
        for i in range(limit):
            if focused(name):
                return i
            key("{TAB}")
        raise AssertionError("No keyboard-only Tab path to "+name)

    top_tabs=tabs_to("FileInfoToggleButton",100)
    print("F03_STARTUP_KEYS_DETAILS_TABS="+str(top_tabs),flush=True)
    key("{SPACE}")
    eventually(lambda:reveal.exists(timeout=.2) and reveal.is_visible(),
               "Keyboard-only Details disclosure failed",8)
    assert not preview.exists(timeout=.15) or not preview.window_text(), (
        "Preview read bytes without user opt-in")
    print("F03_STARTUP_KEYS_OPEN_DETAILS=PASS",flush=True)

    reveal_tabs=tabs_to("TextPreviewRevealButton",120)
    print("F03_STARTUP_KEYS_REVEAL_TABS="+str(reveal_tabs),flush=True)
    key("{ENTER}")
    eventually(lambda:toggle.exists(timeout=.2) and toggle.is_visible()
               and focused("TextPreviewToggleButton"),
               "Keyboard-only reveal failed to focus existing opt-in",9)
    assert "켜기" in toggle.window_text()
    assert not preview.exists(timeout=.2) or not preview.window_text(), (
        "Reveal action implicitly read file content")
    print("F03_STARTUP_KEYS_REVEAL_NO_READ=PASS",flush=True)

    key("{SPACE}")
    eventually(lambda:"끄기" in toggle.window_text(),
               "Keyboard-only explicit Space opt-in failed",9)
    status=element("TextPreviewStatus")
    eventually(lambda:status.exists(timeout=.2) and
               "텍스트 파일 한 개를 선택하세요" in status.window_text(),
               "Without selection, opt-in did not request one selected file",7)
    assert not preview.exists(timeout=.2) or not preview.window_text(), (
        "Unexpected content without an explicit selected file")
    print("F03_STARTUP_KEYS_EXPLICIT_OPTIN_NO_SELECTION=PASS",flush=True)
