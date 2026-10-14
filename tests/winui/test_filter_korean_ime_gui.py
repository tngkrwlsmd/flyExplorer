"""Physical Korean 2-beolsik IME composition in a disposable WinUI rule editor.

This never pastes precomposed Hangul or writes personal files. An installed
Korean IME DLL is only a precondition, not acceptance: UIA must observe
an actual composed Hangul string after Latin key events and persist it.
"""
from __future__ import annotations
import ctypes as c
from ctypes import wintypes as W
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

if os.name != "nt":
    raise SystemExit("Actual Korean IME acceptance needs Windows")


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from paths import app_exe, ROOT
    from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
    from uia_polling import wait_until
    from pywinauto import Desktop, keyboard

    exe=app_exe("Release")
    assert exe.is_file()
    ownroot=ROOT/"logs"/"korean-ime-owned"
    ownroot.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="ime-",dir=ownroot))
    for name in ("files","appdata","localdata","temp"):
        (owned/name).mkdir()
    profile=owned/"localdata"/"flyExplorer"
    profile.mkdir()
    (profile/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
    (owned/"files"/"notes.txt").write_text("owned",encoding="utf-8")
    (owned/"files"/"자료.txt").write_text("owned",encoding="utf-8")
    env={**os.environ,"APPDATA":str(owned/"appdata"),
         "LOCALAPPDATA":str(owned/"localdata"),
         "TEMP":str(owned/"temp"),"TMP":str(owned/"temp")}
    original,hashes=snapshot_legacy_profile()
    u=c.WinDLL("user32",use_last_error=True)
    callback=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    u.EnumWindows.argtypes=(callback,W.LPARAM)
    u.GetWindowThreadProcessId.argtypes=(W.HWND,c.POINTER(W.DWORD))
    u.GetForegroundWindow.restype=W.HWND
    u.GetKeyboardLayout.argtypes=(W.DWORD,)
    u.GetKeyboardLayout.restype=c.c_void_p
    u.LoadKeyboardLayoutW.argtypes=(W.LPCWSTR,W.UINT)
    u.LoadKeyboardLayoutW.restype=c.c_void_p
    u.PostMessageW.argtypes=(W.HWND,W.UINT,W.WPARAM,W.LPARAM)
    u.keybd_event.argtypes=(W.BYTE,W.BYTE,W.DWORD,c.c_void_p)
    class Rect(c.Structure):
        _fields_=[("left",W.LONG),("top",W.LONG),
                  ("right",W.LONG),("bottom",W.LONG)]
    class GuiThreadInfo(c.Structure):
        _fields_=[("cbSize",W.DWORD),("flags",W.DWORD),
                  ("hwndActive",W.HWND),("hwndFocus",W.HWND),
                  ("hwndCapture",W.HWND),("hwndMenuOwner",W.HWND),
                  ("hwndMoveSize",W.HWND),("hwndCaret",W.HWND),
                  ("rcCaret",Rect)]
    u.GetGUIThreadInfo.argtypes=(W.DWORD,c.POINTER(GuiThreadInfo))
    u.GetGUIThreadInfo.restype=W.BOOL
    def owned_focus_hwnd(top,tid):
        info=GuiThreadInfo()
        info.cbSize=c.sizeof(info)
        if not u.GetGUIThreadInfo(tid,c.byref(info)):
            print("KOREAN_IME_GUI_THREAD_INFO_UNAVAILABLE",
                  c.get_last_error(),flush=True)
            return top
        focus=int(info.hwndFocus or 0)
        print("KOREAN_IME_FOCUS_HWND",
              "top",hex(int(top)),"focus",hex(focus),flush=True)
        return focus or top
    def windows(pid):
        found=[]
        @callback
        def visit(hwnd,_):
            owner=W.DWORD()
            u.GetWindowThreadProcessId(hwnd,c.byref(owner))
            if owner.value==pid and u.IsWindowVisible(hwnd):
                found.append(hwnd)
            return True
        u.EnumWindows(visit,0)
        return found
    proc=None
    hwnd=None
    passed=False
    try:
        proc=subprocess.Popen([str(exe),str(owned/"files")],cwd=exe.parent,
                              env=env,stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        wait_until(lambda: len(windows(proc.pid))==1 or proc.poll() is not None,
                   "owned IME WinUI window missing",seconds=20,interval=.2)
        assert proc.poll() is None
        hwnd=windows(proc.pid)[0]
        win=Desktop(backend="uia").window(handle=hwnd)
        win.set_focus()
        assert u.GetForegroundWindow()==hwnd,"Refuse keyboard input outside owned app"
        win.child_window(auto_id="FilterRulePanelButton").click_input()
        editor=win.child_window(auto_id="FilterRuleNameEdit")
        editor.set_focus()
        assert editor.has_keyboard_focus(),"Owned filter name editor focus missing"
        tid=u.GetWindowThreadProcessId(hwnd,c.byref(W.DWORD()))
        original_hkl=int(u.GetKeyboardLayout(tid) or 0)
        print("KOREAN_IME_INITIAL_HKL",hex(original_hkl),flush=True)
        try:
            # The Korean keyboard layout is loaded only for this test and
            # WM_INPUTLANGCHANGEREQUEST is delivered only to the owned HWND.
            ko=int(u.LoadKeyboardLayoutW("00000412",0) or 0)
            assert ko, "Korean keyboard layout not installed"
            assert u.PostMessageW(hwnd,0x0050,0,ko),"Request Korean layout failed"
            wait_until(lambda:int(u.GetKeyboardLayout(tid) or 0)&0xffff==0x0412,
                       "Owned app did not switch to Korean layout",
                       seconds=8,interval=.15)
            composed=False
            observations=[]
            imm=c.WinDLL("imm32",use_last_error=True)
            imm.ImmGetContext.argtypes=(W.HWND,)
            imm.ImmGetContext.restype=c.c_void_p
            imm.ImmGetOpenStatus.argtypes=(c.c_void_p,)
            imm.ImmGetOpenStatus.restype=W.BOOL
            imm.ImmSetOpenStatus.argtypes=(c.c_void_p,W.BOOL)
            imm.ImmSetOpenStatus.restype=W.BOOL
            imm.ImmGetConversionStatus.argtypes=(c.c_void_p,
                                                    c.POINTER(W.DWORD),
                                                    c.POINTER(W.DWORD))
            imm.ImmGetConversionStatus.restype=W.BOOL
            imm.ImmSetConversionStatus.argtypes=(c.c_void_p,
                                                  W.DWORD,W.DWORD)
            imm.ImmSetConversionStatus.restype=W.BOOL
            IME_CMODE_NATIVE=0x0001
            focus_hwnd=owned_focus_hwnd(hwnd,tid)
            context=imm.ImmGetContext(focus_hwnd)
            old_open=bool(imm.ImmGetOpenStatus(context)) if context else None
            conv,sentence=W.DWORD(),W.DWORD()
            conversion_known=bool(context and imm.ImmGetConversionStatus(
                context,c.byref(conv),c.byref(sentence)))
            saved_conversion=(int(conv.value),int(sentence.value)) if conversion_known else None
            print("KOREAN_IME_INITIAL_STATE",
                  {"hkl":hex(int(u.GetKeyboardLayout(tid) or 0)),
                   "focus_hwnd_is_toplevel":focus_hwnd==hwnd,
                   "ime_context_exists":bool(context),
                   "open":old_open,
                   "conversion":saved_conversion},flush=True)
            try:
                methods=("korean-hangul-scancode","korean-right-alt",
                         "owned-ime-open-and-native")
                for method in methods:
                    editor.set_edit_text("")
                    editor.set_focus()
                    assert u.GetForegroundWindow()==hwnd
                    if method=="korean-hangul-scancode":
                        u.keybd_event(0x15,0x72,0,0)
                        u.keybd_event(0x15,0x72,2,0)
                    elif method=="korean-right-alt":
                        u.keybd_event(0xA5,0x38,1,0)
                        u.keybd_event(0xA5,0x38,3,0)
                    elif context:
                        opened=bool(imm.ImmSetOpenStatus(context,True))
                        native=bool(saved_conversion and imm.ImmSetConversionStatus(
                            context,saved_conversion[0]|IME_CMODE_NATIVE,
                            saved_conversion[1]))
                        print("KOREAN_IME_OWNED_NATIVE_REQUEST",
                              {"opened":opened,"native":native},flush=True)
                    else:
                        print("KOREAN_IME_IMM_CONTEXT_UNAVAILABLE",flush=True)
                        continue
                    time.sleep(.35)
                    keyboard.send_keys("gksrmf",pause=.1,vk_packet=False)
                    time.sleep(.9)
                    value=editor.get_value()
                    current_conv,current_sentence=W.DWORD(),W.DWORD()
                    current_known=bool(context and imm.ImmGetConversionStatus(
                        context,c.byref(current_conv),c.byref(current_sentence)))
                    status=bool(imm.ImmGetOpenStatus(context)) if context else None
                    observations.append({"method":method,
                                         "typed":value,"open":status,
                                         "conversion":int(current_conv.value) if current_known else None,
                                         "hkl":hex(int(u.GetKeyboardLayout(tid) or 0))})
                    if value=="한글":
                        composed=True
                        print("KOREAN_IME_ACTUAL_COMPOSITION_METHOD",
                              method,flush=True)
                        break
            finally:
                if context:
                    if saved_conversion is not None:
                        imm.ImmSetConversionStatus(context,*saved_conversion)
                    if old_open is not None:
                        imm.ImmSetOpenStatus(context,old_open)
                    imm.ImmReleaseContext(focus_hwnd,context)
            print("KOREAN_IME_COMPOSITION_OBSERVATIONS",
                  repr(observations),flush=True)
            assert composed, "Physical Korean IME 2-beolsik composition not observed"
            win.child_window(auto_id="FilterRuleMasksEdit").set_edit_text("*.txt")
            win.child_window(auto_id="FilterRuleSaveButton").click_input()
            store=profile/"filter-rules-v1.txt"
            wait_until(lambda:store.is_file() and "한글\t*.txt" in
                       store.read_text(encoding="utf-8"),
                       "Composed Hangul not persisted to owned preset",
                       seconds=9,interval=.15)
            print("KOREAN_IME_ACTUAL_PHYSICAL_COMPOSITION_AND_SAVE=PASS",flush=True)
            passed=True
        finally:
            # Restore keyboard layout for the owned app before closing it.
            if proc.poll() is None and hwnd is not None and original_hkl:
                u.PostMessageW(hwnd,0x0050,0,original_hkl)
    finally:
        if proc is not None:
            if proc.poll() is None and hwnd is not None:
                assert u.PostMessageW(hwnd,0x0010,0,0),"Owned WM_CLOSE failed"
                proc.wait(timeout=14)
            elif proc.poll() is None:
                raise AssertionError("Owned IME process has no safe HWND to close")
            assert proc.returncode==0,"Owned WinUI exited abnormally"
        assert_legacy_profile_unchanged(original,hashes)
        if passed:
            shutil.rmtree(owned)
        else:
            print("KOREAN_IME_OWNED_EVIDENCE_RETAINED",owned,flush=True)
    return 0 if passed else 1


if __name__=="__main__":
    raise SystemExit(main())
