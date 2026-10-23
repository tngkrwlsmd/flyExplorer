"""PX12 narrow visual comparison with a NEW owned-path Explorer window.

Captures real, unmodified foreground pixels. Native Explorer captures use
only the top address/header strip to avoid user Quick Access/history content.
No global theme/DPI mutation and no existing Explorer HWND is touched.
"""
from __future__ import annotations
import base64
import ctypes as ct
from ctypes import wintypes as W
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import winreg

from PIL import ImageGrab
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


def run(*, win, element, focus, eventually, left, right, owned):
    left=Path(left)
    assert left.is_relative_to(owned) and Path(right).is_relative_to(owned)
    target=left/"Nested"
    assert target.is_dir() and (target/"PX12VisualOwned.txt").is_file()
    app_pid=win.wrapper_object().element_info.process_id
    user=ct.windll.user32
    user.GetForegroundWindow.restype=W.HWND
    user.GetWindowThreadProcessId.argtypes=[W.HWND,ct.POINTER(W.DWORD)]
    user.GetDpiForWindow.argtypes=[W.HWND]
    user.GetDpiForWindow.restype=W.UINT
    user.SetWindowPos.argtypes=[W.HWND,W.HWND,ct.c_int,ct.c_int,
                               ct.c_int,ct.c_int,W.UINT]
    user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    user.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,ct.c_int]
    user.GetClassNameW.restype=ct.c_int
    callback=ct.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    user.EnumWindows.argtypes=[callback,W.LPARAM]
    width,height=940,620
    assert user.GetSystemMetrics(0)>=width+55
    assert user.GetSystemMetrics(1)>=height+85

    def pid_of(hwnd):
        owner=W.DWORD()
        if hwnd:user.GetWindowThreadProcessId(hwnd,ct.byref(owner))
        return owner.value

    def class_of(hwnd):
        label=ct.create_unicode_buffer(96)
        user.GetClassNameW(hwnd,label,len(label))
        return label.value

    def cabinets():
        windows=[]
        @callback
        def visitor(hwnd,_):
            if user.IsWindowVisible(hwnd) and class_of(hwnd)=="CabinetWClass":
                windows.append(int(hwnd))
            return True
        user.EnumWindows(visitor,0)
        return set(windows)

    def strict_window(hwnd,pid=None):
        if not hwnd or not user.IsWindowVisible(hwnd):
            raise AssertionError("PX12 compare target not visible")
        if pid is not None and pid_of(hwnd)!=pid:
            raise AssertionError("PX12 compare HWND owner moved")
        user.SetWindowPos(hwnd,None,38,38,width,height,0x0014)
        rect=Desktop(backend="uia").window(handle=hwnd).rectangle()
        assert abs(rect.width()-width)<=5 and abs(rect.height()-height)<=5
        assert 0<=rect.left and 0<=rect.top and rect.right<=user.GetSystemMetrics(0)
        assert rect.bottom<=user.GetSystemMetrics(1)
        assert user.GetDpiForWindow(hwnd)==96, "Excluded non-96 DPI; do not change OS scaling"
        return rect

    def foreground(hwnd,pid=None):
        if user.GetForegroundWindow()!=hwnd:
            raise AssertionError("PX12 refuse capture or input outside test target")
        if pid is not None and pid_of(hwnd)!=pid:
            raise AssertionError("PX12 wrong foreground process")

    def capture(hwnd,pid,kind,strip):
        foreground(hwnd,pid)
        rect=strict_window(hwnd,pid)
        # Strictly within the verified new or app-owned foreground HWND.
        area=(rect.left+4,rect.top+4,rect.right-4,rect.top+strip)
        assert area[3]<rect.bottom
        raw=ImageGrab.grab(bbox=area,include_layered_windows=True)
        output=io.BytesIO()
        raw.save(output,format="PNG",optimize=True)
        png=output.getvalue()
        assert 200<len(png)<240000, (kind,len(png))
        frames.append((kind,png,{
            "filename":kind+".png",
            "pixels":[raw.width,raw.height],
            "sha256":hashlib.sha256(png).hexdigest(),
        }))

    def app_candidates():
        return [x for x in win.descendants(control_type="Button")
                if (x.element_info.name or "").startswith("주소 후보: ")]

    def app_target():
        return any(x.element_info.name=="주소 후보: "+str(target)
                   for x in app_candidates())

    frames=[]
    initial_cabinets=cabinets()
    explorer_hwnd=None
    explore_proc=None
    app_hwnd=win.wrapper_object().handle
    try:
        # App theme is chosen to match the READ-ONLY current Windows apps theme.
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                theme="light" if winreg.QueryValueEx(key,"AppsUseLightTheme")[0] else "dark"
        except OSError:
            theme="unknown"
        assert theme in ("light","dark"), "Cannot establish matched app/OS theme"
        strict_window(app_hwnd,app_pid)
        focus()
        foreground(app_hwnd,app_pid)
        send_keys("^l")
        eventually(lambda:element("AddressBox").has_keyboard_focus(),
                   "PX12 app address not focused",9)
        element("AddressBox").set_edit_text(str(left)+"\\N")
        eventually(app_target,"PX12 test-owned app candidate absent",12)
        assert 1<=len(app_candidates())<=8
        app_candidate_count=len(app_candidates())
        foreground(app_hwnd,app_pid)
        capture(app_hwnd,app_pid,"flyexplorer-candidate",310)
        print("PX12_VISUAL_FLY_CANDIDATE_CAPTURE=PASS",flush=True)

        # Explorer must create a previously non-existent top-level HWND.
        # Never send input to any pre-existing user Explorer window.
        explore_proc=subprocess.Popen(["explorer.exe",str(left)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        def new_window():
            added=cabinets()-initial_cabinets
            if len(added)!=1:return None
            h=next(iter(added))
            wrapper=Desktop(backend="uia").window(handle=h)
            try:
                # New window must visibly expose both synthetic files/folder.
                names={x.window_text() for x in wrapper.descendants()}
                if "Nested" not in names or not any(n.startswith("readme") for n in names):
                    return None
            except Exception:
                return None
            return h
        explorer_hwnd=eventually(new_window,
            "PX12 new isolated Explorer window not ready; refuse existing user HWND",
            16)
        assert explorer_hwnd not in initial_cabinets
        explorer_pid=pid_of(explorer_hwnd)
        assert explorer_pid>0 and class_of(explorer_hwnd)=="CabinetWClass"
        explorer=Desktop(backend="uia").window(handle=explorer_hwnd)
        strict_window(explorer_hwnd,explorer_pid)
        explorer.set_focus()
        eventually(lambda:user.GetForegroundWindow()==explorer_hwnd,
                   "PX12 new Explorer did not gain foreground",8)
        foreground(explorer_hwnd,explorer_pid)
        send_keys("^l")
        def focused_edit():
            try:
                hits=[x for x in explorer.descendants(control_type="Edit")
                      if x.has_keyboard_focus()]
                return hits[0] if len(hits)==1 else None
            except Exception:
                return None
        editor=eventually(focused_edit,
                          "PX12 new Explorer Ctrl+L focused Edit absent",9)
        assert editor.element_info.process_id==explorer_pid
        editor.set_edit_text(str(left)+"\\N")
        foreground(explorer_hwnd,explorer_pid)
        assert focused_edit() is not None
        time.sleep(.3)
        # Do NOT screenshot Explorer's history dropdown or sidebar:
        # their items may be personal, even with a synthetic current folder.
        # Stop at the focused Edit's lower edge: the separate native
        # suggestions popup may contain private Explorer history below it.
        top=explorer.rectangle().top
        cutoff=editor.rectangle().bottom-top+2
        assert 65<=cutoff<=155, "Explorer address bar outside bounded header"
        capture(explorer_hwnd,explorer_pid,"explorer-address-header",cutoff)
        print("PX12_VISUAL_EXPLORER_SAFE_HEADER_CAPTURE=PASS",flush=True)
        # Targeted comparison: Escape must keep the existing folder usable.
        foreground(explorer_hwnd,explorer_pid)
        send_keys("{ESC}")
        print("PX12_EXPLORER_ADDRESS_EDIT_ESCAPE=OBSERVED",flush=True)

        # Return only to the exact known app window for a committed view.
        focus()
        foreground(app_hwnd,app_pid)
        send_keys("{ESC}")
        # A second Escape closes edit mode, if the first only hid candidates.
        foreground(app_hwnd,app_pid)
        send_keys("{ESC}")
        capture(app_hwnd,app_pid,"flyexplorer-committed",180)
        print("PX12_VISUAL_FLY_COMMITTED_CAPTURE=PASS",flush=True)
        metadata={
          "source":"actual Windows WinUI and a new native File Explorer HWND",
          "windows":platform.version(),
          "theme":theme,
          "dpi":96,
          "window_size":[width,height],
          "fixture":"disposable Left/Nested and readme.txt",
          "app_candidate_count":app_candidate_count,
          "reference_comparison":"native Explorer address edit observed; autocomplete list not assumed",
          "reference_capture_limit":"only address/header; no personal recent/suggestion/sidebar contents",
          "frames":[item[2] for item in frames],
        }
        print("PX12_VISUAL_METADATA="+json.dumps(metadata,ensure_ascii=False),
              flush=True)
        # Keep these bounded real-pixel frames accessible for direct review
        # without writing user content or broad desktop screenshots.
        for kind,png,_ in frames:
            print("PX12_VISUAL_IMAGE_"+kind.upper().replace("-","_")+
                  "="+base64.b64encode(png).decode("ascii"),flush=True)
        print("PX12_EXPLORER_MATCHED_COMPARISON_CAPTURE=PASS",flush=True)
    finally:
        if explorer_hwnd and explorer_hwnd not in initial_cabinets and (
                class_of(explorer_hwnd)=="CabinetWClass"):
            # Close only the new HWND; Explorer may share a process with
            # user-owned windows so never terminate or kill explorer.exe.
            user.PostMessageW(explorer_hwnd,0x10,0,0)
            eventually(lambda:explorer_hwnd not in cabinets(),
                       "PX12 new Explorer window did not close normally",10)
        # The caller closes only its own flyExplorer PID and retires its
        # isolated profile and synthetic files in an independent finally.
