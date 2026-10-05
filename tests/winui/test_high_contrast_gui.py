"""Owned High Contrast ON acceptance. Never changes global accessibility state."""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
import ctypes as c
from ctypes import wintypes as w
import os
import shutil
import subprocess
import sys
import tempfile
import time

import psutil
from PIL import ImageGrab
from pywinauto import Desktop

u=c.WinDLL("user32",use_last_error=True)
u.GetForegroundWindow.restype=w.HWND
u.SetWindowPos.argtypes=(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)

class HIGHCONTRAST(c.Structure):
    _fields_=(("cbSize",w.UINT),("dwFlags",w.DWORD),
              ("lpszDefaultScheme",w.LPWSTR))

def current_hc():
    state=HIGHCONTRAST()
    state.cbSize=c.sizeof(state)
    assert u.SystemParametersInfoW(0x0042,state.cbSize,c.byref(state),0)
    return bool(state.dwFlags&1),state.lpszDefaultScheme

def until(fn,label,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            if fn():
                return
        except Exception:
            pass
        time.sleep(.2)
    raise AssertionError(label)

def main(configuration="Release"):
    enabled,scheme=current_hc()
    if not enabled:
        print("HIGH_CONTRAST_ON_REQUIRED",repr(scheme),flush=True)
        return 2

    exe=app_exe(configuration)
    assert exe.is_file(),exe
    before=snapshot_legacy_profile()
    root=ROOT/"logs"/"high-contrast"
    root.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="high-contrast-owned-",dir=root))
    folder=owned/"source"
    folder.mkdir()
    for name in ("contrast-alpha.txt","contrast-beta.txt","한국어-고대비.txt"):
        (folder/name).write_text("owned high contrast",encoding="utf-8")

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        dest=owned/key.lower()
        dest.mkdir()
        env[key]=str(dest)

    proc=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    hwnd=None
    passed=False
    try:
        def ready():
            nonlocal hwnd
            if proc.poll() is not None:
                return False
            if Path(psutil.Process(proc.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("flyExplorer PID mismatch")
            windows=[x for x in Desktop(backend="uia").windows(process=proc.pid)
                     if "flyExplorer" in x.window_text()]
            if len(windows)!=1:
                return False
            hwnd=windows[0].handle
            return windows[0].child_window(auto_id="LeftFiles").exists(timeout=.2)

        until(ready,"High Contrast owned flyExplorer window did not start")
        win=Desktop(backend="uia").window(handle=hwnd)
        win.set_focus()
        assert u.SetWindowPos(hwnd,None,40,30,1100,720,0x0014)
        until(lambda:abs(win.rectangle().width()-1100)<=3,
              "High Contrast acceptance size did not apply")
        assert u.GetForegroundWindow()==hwnd
        assert current_hc()[0],"High Contrast turned off during acceptance"

        named=(
            "BackButton","ForwardButton","UpButton","AddressBox",
            "QuickSearchBox","SearchPanelButton","LeftTabs","RightTabs",
            "LeftNameSortButton","RightNameSortButton","LeftFiles","RightFiles",
            "HomeButton","StatusText",
        )
        for key in named:
            element=win.child_window(auto_id=key)
            assert element.exists(timeout=2),key
            assert element.element_info.name,(key,"missing accessible name")

        rows=[x for x in win.child_window(auto_id="LeftFiles").descendants()
              if x.element_info.control_type=="ListItem"]
        assert rows,"High Contrast owned file rows missing"
        rows[0].select()
        until(lambda:any(x.is_selected() for x in
              win.child_window(auto_id="LeftFiles").descendants()
              if x.element_info.control_type=="ListItem"),
              "High Contrast list selection did not become visible to UIA")

        rect=win.rectangle()
        shell_image=root/"high-contrast-shell.png"
        ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                       all_screens=True).save(shell_image)
        print("HIGH_CONTRAST_SHELL_SCREENSHOT",shell_image,flush=True)

        win.child_window(auto_id="SearchPanelButton").click_input()
        until(lambda:win.child_window(auto_id="SearchPanel").exists(timeout=.2)
              and win.child_window(auto_id="SearchPanel").is_visible(),
              "High Contrast search panel did not open")
        search_image=root/"high-contrast-search.png"
        rect=win.rectangle()
        ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                       all_screens=True).save(search_image)
        print("HIGH_CONTRAST_SEARCH_SCREENSHOT",search_image,flush=True)

        assert current_hc()[0],"High Contrast changed during screenshot capture"
        print("OWNED_HIGH_CONTRAST_UIA_AND_SELECTION_PASS",True,flush=True)
        print("OWNED_HIGH_CONTRAST_SEARCH_SURFACE_PASS",True,flush=True)
        passed=True
    finally:
        if proc.poll() is None:
            if hwnd is not None:
                u.PostMessageW(hwnd,0x10,0,0)
                try:
                    proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    proc.wait(timeout=7)
            else:
                proc.terminate()
                proc.wait(timeout=7)
        unchanged=assert_legacy_profile_unchanged(before)
        print("ORIGINAL_SIX_USER_SETTINGS_IDENTICAL",unchanged,flush=True)
        assert current_hc()[0],"High Contrast state changed by owned acceptance"
        if passed and unchanged and proc.returncode==0:
            shutil.rmtree(owned)
        else:
            print("OWNED_HIGH_CONTRAST_FIXTURE_RETAINED",owned,flush=True)

    return 0 if passed and proc.returncode==0 else 1

if __name__=="__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "Release"))
