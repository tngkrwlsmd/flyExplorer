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
u.SetWindowTextW.argtypes = (w.HWND, w.LPCWSTR)
u.SendMessageW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPWSTR)
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
    # Only the thread which owns the EDIT probes and changes its HIMC.
    # Its status is exposed on the disposable window title for the parent.
    owned_ime_state = None
    def update_owned_ime():
        nonlocal owned_ime_state
        ctx = imm.ImmGetContext(edit)
        details = ["context=" + str(bool(ctx))]
        if ctx:
            opened = bool(imm.ImmGetOpenStatus(ctx))
            mode, sentence = w.DWORD(), w.DWORD()
            known = bool(imm.ImmGetConversionStatus(
                ctx, c.byref(mode), c.byref(sentence)))
            owned_ime_state = (opened, int(mode.value), int(sentence.value)) if known else (opened, None, None)
            set_open = bool(imm.ImmSetOpenStatus(ctx, True))
            set_native = bool(known and imm.ImmSetConversionStatus(
                ctx, mode.value | 1, sentence.value))
            details.extend(["initial_open=" + str(opened),
                            "initial_native=" + str(bool(mode.value & 1)) if known else "initial_native=unknown",
                            "set_open=" + str(set_open),
                            "set_native=" + str(set_native)])
            imm.ImmReleaseContext(edit, ctx)
        u.SetWindowTextW(top, "owned IME | " + "|".join(details))
    def restore_owned_ime():
        nonlocal owned_ime_state
        if owned_ime_state is not None:
            ctx = imm.ImmGetContext(edit)
            if ctx:
                opened, mode, sentence = owned_ime_state
                if mode is not None:
                    imm.ImmSetConversionStatus(ctx, mode, sentence)
                imm.ImmSetOpenStatus(ctx, opened)
                imm.ImmReleaseContext(edit, ctx)
            owned_ime_state = None
    end = time.monotonic() + 60
    while u.IsWindow(top) and time.monotonic() < end:
        while u.PeekMessageW(c.byref(msg), None, 0, 0, 1):
            if msg.hwnd == top and msg.message == 0x8001:  # owned IME enable
                update_owned_ime()
                continue
            if msg.hwnd == top and msg.message == 0x8002:  # restore
                restore_owned_ime()
                continue
            u.TranslateMessage(c.byref(msg))
            u.DispatchMessageW(c.byref(msg))
        time.sleep(.025)
    restore_owned_ime()
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
        def read_owned_edit():
            # Cross-process GetWindowTextW intentionally returns empty for
            # edit controls. WM_GETTEXT is system-marshalled for the owned EDIT.
            buf = c.create_unicode_buffer(256)
            u.SendMessageW(edit, 0x000D, 256, buf)
            return buf.value
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
        observations = []
        try:
            # A composed-text result is meaningful only after the test-owned
            # native control demonstrably receives actual physical key input.
            wnd.click_input()
            require_foreground_owned()
            u.SendMessageW(edit, 0x000C, 0, "owned-readback-check")
            readback = read_owned_edit()
            print("KOREAN_IME_NATIVE_TEXT_READBACK",
                  {"correct": readback == "owned-readback-check",
                   "value": readback}, flush=True)
            assert readback == "owned-readback-check", (
                "Owned native EDIT WM_GETTEXT roundtrip failed")
            u.SendMessageW(edit, 0x000C, 0, "")
            keyboard.send_keys("123", pause=.09, vk_packet=False)
            time.sleep(.45)
            digits = read_owned_edit()
            physical_delivery = digits == "123"
            print("KOREAN_IME_NATIVE_PHYSICAL_DIGITS",
                  {"value": digits, "delivered": physical_delivery},
                  flush=True)
            if not physical_delivery:
                print("KOREAN_IME_NATIVE_INPUT_DELIVERY=ENVIRONMENT_BLOCKED",
                      flush=True)
                print("KOREAN_IME_NATIVE_EDIT_COMPOSED=False", flush=True)
                print("KOREAN_IME_BASELINE_DIAGNOSTIC=PASS", flush=True)
                return 0
            for method in ("physical-hangul-key", "owned-thread-imm-native"):
                wnd.click_input()
                require_foreground_owned()
                u.SendMessageW(edit, 0x000C, 0, "")  # owned WM_SETTEXT
                owned_ime = ""
                if method == "physical-hangul-key":
                    u.keybd_event(0x15, 0x72, 0, None)
                    u.keybd_event(0x15, 0x72, 2, None)
                else:
                    assert u.PostMessageW(top, 0x8001, 0, 0)
                    time.sleep(.35)
                    title = c.create_unicode_buffer(256)
                    u.GetWindowTextW(top, title, 255)
                    owned_ime = title.value
                    print("KOREAN_IME_NATIVE_OWNER_THREAD_STATE", owned_ime, flush=True)
                    assert owned_ime.startswith("owned IME | "), (
                        "IME owner thread did not handle the state request")
                time.sleep(.25)
                keyboard.send_keys("gksrmf",pause=.09,vk_packet=False)
                time.sleep(.5)
                data = read_owned_edit()
                observations.append({"method":method,"typed":data,
                                     "owned_ime_state":owned_ime})
                if data == "한글":
                    break
        finally:
            u.PostMessageW(top, 0x8002, 0, 0)  # Restore only owned IME state.
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
