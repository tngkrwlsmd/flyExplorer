"""Disposable native Win32 EDIT vs WinUI Korean IME input capability probe.

This is an environment diagnostic. Its PASS means that the diagnostic ran,
not that either flyExplorer or Narrator is accepted. No user data, persistent
language settings, or clipboard are read/written.
"""
from __future__ import annotations
import ctypes as c
from ctypes import wintypes as w
import os
import subprocess
import sys
import time

if os.name != "nt":
    raise SystemExit("Native IME baseline requires Windows")

u = c.WinDLL("user32", use_last_error=True)
imm = c.WinDLL("imm32", use_last_error=True)
ENUM = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.EnumWindows.argtypes = (ENUM, w.LPARAM)
u.GetWindowThreadProcessId.argtypes = (w.HWND, c.POINTER(w.DWORD))
u.GetKeyboardLayout.argtypes = (w.DWORD,)
u.GetKeyboardLayout.restype = c.c_void_p
u.LoadKeyboardLayoutW.argtypes = (w.LPCWSTR, w.UINT)
u.LoadKeyboardLayoutW.restype = c.c_void_p
u.GetForegroundWindow.restype = w.HWND
u.SetFocus.argtypes = (w.HWND,)
u.SetFocus.restype = w.HWND
u.SetForegroundWindow.argtypes = (w.HWND,)
u.PostMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
u.IsWindow.argtypes = (w.HWND,)
u.FindWindowExW.argtypes = (w.HWND, w.HWND, w.LPCWSTR, w.LPCWSTR)
u.FindWindowExW.restype = w.HWND
u.GetWindowTextW.argtypes = (w.HWND, w.LPWSTR, c.c_int)
u.SendMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPCWSTR)
u.SendMessageW.restype = c.c_ssize_t
u.CreateWindowExW.argtypes = (
    w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD,
    c.c_int, c.c_int, c.c_int, c.c_int,
    w.HWND, c.c_void_p, c.c_void_p, c.c_void_p)
u.CreateWindowExW.restype = w.HWND
class Point(c.Structure):
    _fields_=[("x",w.LONG),("y",w.LONG)]
class Msg(c.Structure):
    _fields_=[("hwnd",w.HWND),("message",w.UINT),
              ("wParam",w.WPARAM),("lParam",w.LPARAM),
              ("time",w.DWORD),("pt",Point)]
u.PeekMessageW.argtypes = (c.POINTER(Msg),w.HWND,w.UINT,w.UINT,w.UINT)
u.TranslateMessage.argtypes = (c.POINTER(Msg),)
u.DispatchMessageW.argtypes = (c.POINTER(Msg),)
u.keybd_event.argtypes=(w.BYTE,w.BYTE,w.DWORD,c.c_void_p)
imm.ImmGetContext.argtypes = (w.HWND,)
imm.ImmGetContext.restype = c.c_void_p
imm.ImmReleaseContext.argtypes = (w.HWND, c.c_void_p)
imm.ImmGetOpenStatus.argtypes = (c.c_void_p,)
imm.ImmGetOpenStatus.restype = w.BOOL
imm.ImmSetOpenStatus.argtypes = (c.c_void_p, w.BOOL)
imm.ImmGetConversionStatus.argtypes = (c.c_void_p, c.POINTER(w.DWORD), c.POINTER(w.DWORD))
imm.ImmSetConversionStatus.argtypes = (c.c_void_p,w.DWORD,w.DWORD)


def host():
    # Win32 system classes, no custom WNDPROC or personal application state.
    top = u.CreateWindowExW(0, "STATIC", "flyExplorer test-owned IME baseline",
                            0x10CF0000, 45, 45, 530, 180, None, None, None, None)
    if not top:
        raise OSError("native owned host HWND not available")
    edit = u.CreateWindowExW(0, "EDIT", "",
                             0x50010080, 15, 25, 460, 42, top,
                             None, None, None)
    if not edit:
        raise OSError("native owned EDIT HWND not available")
    u.ShowWindow(top, 5)
    u.UpdateWindow(top)
    u.SetFocus(edit)  # Focus is set by the native owning GUI thread.
    msg = Msg()
    end = time.monotonic() + 60
    while u.IsWindow(top) and time.monotonic() < end:
        while u.PeekMessageW(c.byref(msg), None, 0, 0, 1):
            u.TranslateMessage(c.byref(msg))
            u.DispatchMessageW(c.byref(msg))
        time.sleep(.025)
    if u.IsWindow(top):
        u.DestroyWindow(top)
    return 0


def main():
    from pywinauto import Desktop, keyboard
    proc = subprocess.Popen([sys.executable, __file__, "--native-host"],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    top = None
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline and proc.poll() is None:
            found = []
            @ENUM
            def check(hwnd, _):
                pid = w.DWORD()
                u.GetWindowThreadProcessId(hwnd, c.byref(pid))
                if pid.value == proc.pid and u.IsWindowVisible(hwnd):
                    found.append(hwnd)
                return True
            u.EnumWindows(check, 0)
            if len(found) == 1:
                top = found[0]
                break
            time.sleep(.2)
        assert top and proc.poll() is None, "Owned native EDIT host unavailable"
        edit = u.FindWindowExW(top, None, "Edit", None)
        assert edit, "Native EDIT child is missing"
        wnd = Desktop(backend="win32").window(handle=edit)
        wnd.click_input()
        def require_foreground_owned():
            fg=u.GetForegroundWindow()
            owner=w.DWORD()
            if fg:
                u.GetWindowThreadProcessId(fg,c.byref(owner))
            if not fg or owner.value != proc.pid:
                u.SetForegroundWindow(top)
                time.sleep(.25)
                fg=u.GetForegroundWindow()
                owner=w.DWORD()
                if fg:
                    u.GetWindowThreadProcessId(fg,c.byref(owner))
            print("KOREAN_IME_NATIVE_OWNED_FG",
                  {"top":hex(int(top)),"foreground":hex(int(fg or 0)),
                   "foreground_owned":owner.value==proc.pid},flush=True)
            assert owner.value==proc.pid, "Refuse physical keys outside test-owned foreground"
        require_foreground_owned()
        tid = u.GetWindowThreadProcessId(top, c.byref(w.DWORD()))
        original_hkl = int(u.GetKeyboardLayout(tid) or 0)
        ko = int(u.LoadKeyboardLayoutW("00000412", 0) or 0)
        assert ko and u.PostMessageW(top, 0x0050, 0, ko), "Korean HKL request failed"
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            if int(u.GetKeyboardLayout(tid) or 0) & 0xffff == 0x412:
                break
            time.sleep(.1)
        korean_hkl=hex(int(u.GetKeyboardLayout(tid) or 0))
        context = imm.ImmGetContext(edit)
        old_open = bool(imm.ImmGetOpenStatus(context)) if context else None
        conv, sentence = w.DWORD(),w.DWORD()
        old_status = (int(conv.value),int(sentence.value)) if (
            context and imm.ImmGetConversionStatus(context,c.byref(conv),c.byref(sentence))) else None
        observations = []
        try:
            # A composed-text result is meaningful only after the test-owned
            # native control demonstrably receives actual physical key input.
            wnd.click_input()
            require_foreground_owned()
            u.SendMessageW(edit, 0x000C, 0, "")
            keyboard.send_keys("123", pause=.09)
            time.sleep(.45)
            digits = c.create_unicode_buffer(256)
            u.GetWindowTextW(edit, digits, 255)
            physical_delivery = digits.value == "123"
            print("KOREAN_IME_NATIVE_PHYSICAL_DIGITS",
                  {"value": digits.value, "delivered": physical_delivery},
                  flush=True)
            if not physical_delivery:
                print("KOREAN_IME_NATIVE_INPUT_DELIVERY=ENVIRONMENT_BLOCKED",
                      flush=True)
                print("KOREAN_IME_NATIVE_EDIT_COMPOSED=False", flush=True)
                print("KOREAN_IME_BASELINE_DIAGNOSTIC=PASS", flush=True)
                return 0
            for method in ("physical-hangul-key", "native-imm-mode"):
                wnd.click_input()
                require_foreground_owned()
                u.SendMessageW(edit, 0x000C, 0, "")  # owned WM_SETTEXT
                if method == "physical-hangul-key":
                    u.keybd_event(0x15, 0x72, 0, None)
                    u.keybd_event(0x15, 0x72, 2, None)
                elif context:
                    imm.ImmSetOpenStatus(context, True)
                    if old_status:
                        imm.ImmSetConversionStatus(context,old_status[0]|0x1,old_status[1])
                time.sleep(.25)
                keyboard.send_keys("gksrmf",pause=.09)
                time.sleep(.5)
                data = c.create_unicode_buffer(256)
                u.GetWindowTextW(edit,data,255)
                observations.append({"method":method,"typed":data.value,
                                     "context_exists":bool(context),
                                     "open":bool(imm.ImmGetOpenStatus(context)) if context else None})
                if data.value == "한글":
                    break
        finally:
            if context:
                if old_status:
                    imm.ImmSetConversionStatus(context,*old_status)
                if old_open is not None:
                    imm.ImmSetOpenStatus(context,old_open)
                imm.ImmReleaseContext(edit,context)
            if original_hkl:
                u.PostMessageW(top, 0x0050, 0, original_hkl)
        print("KOREAN_IME_NATIVE_EDIT_HKL",korean_hkl,flush=True)
        print("KOREAN_IME_NATIVE_EDIT_OBSERVATIONS",repr(observations),flush=True)
        verdict = any(x["typed"] == "한글" for x in observations)
        print("KOREAN_IME_NATIVE_INPUT_DELIVERY=PASS", flush=True)
        print("KOREAN_IME_NATIVE_EDIT_COMPOSED="+str(verdict),flush=True)
        print("KOREAN_IME_BASELINE_DIAGNOSTIC=PASS",flush=True)
        return 0
    finally:
        if proc.poll() is None:
            if top:
                u.PostMessageW(top, 0x0010, 0, 0)
            proc.wait(timeout=10)
        assert proc.returncode == 0, "Native test-owned input host failed to exit"


if __name__ == "__main__":
    raise SystemExit(host() if len(sys.argv) > 1 and sys.argv[1] == "--native-host"
                     else main())
