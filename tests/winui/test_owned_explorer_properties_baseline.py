"""Read-only OS baseline: Alt+Enter Properties in one newly opened test-owned Explorer.

Closes only a fresh Properties HWND demonstrably linked to our disposable file.
Never focus/close a pre-existing Explorer HWND or modify global clipboard.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

import pythoncom
import win32com.client
from PIL import ImageGrab
from pywinauto import Desktop
from paths import ROOT
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
u=c.WinDLL("user32",use_last_error=True)
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.GetWindowThreadProcessId.restype=w.DWORD
u.GetForegroundWindow.restype=w.HWND
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.PostMessageW.restype=w.BOOL

def until(test,label,seconds=15):
    return wait_until(test,label,seconds=seconds,interval=.2)

def main():
    pythoncom.CoInitialize()
    base=ROOT/"logs"/"m24"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="properties-os-baseline-",dir=base))
    folder=owned/"source"
    folder.mkdir()
    file=folder/"properties-os-owned.txt"
    file.write_text("owned properties baseline\n",encoding="utf-8")
    expected=file.read_bytes()
    mfc=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={n:hashlib.sha256((mfc/n).read_bytes()).digest()
            for n in LEGACY if (mfc/n).is_file()}
    shell=win32com.client.Dispatch("Shell.Application")
    preexplorer={int(x.HWND) for x in shell.Windows()}
    baseline={x.handle for x in Desktop(backend="uia").windows()}
    explorer=None
    props=None
    success=False
    target=folder.resolve().as_uri().rstrip("/").casefold()
    try:
        shell.Explore(str(folder))
        def ready():
            nonlocal explorer
            found=[]
            for x in shell.Windows():
                try:
                    if int(x.HWND) not in preexplorer and \
                       str(x.LocationURL).rstrip("/").casefold()==target:
                        found.append(x)
                except Exception:pass
            if len(found)!=1:return False
            explorer=found[0]
            return True
        until(ready,"Fresh owned Explorer window missing",20)
        hwnd=int(explorer.HWND)
        window=Desktop(backend="uia").window(handle=hwnd)
        item=explorer.Document.Folder.Items().Item(file.name)
        assert item is not None
        explorer.Document.SelectItem(item,1|4|8|16)
        until(lambda:explorer.Document.SelectedItems().Count==1 and
              explorer.Document.SelectedItems().Item(0).Name==file.name,
              "Owned Explorer file not selected",8)
        window.set_focus()
        assert int(u.GetForegroundWindow())==hwnd,(
            "Explorer not foreground; refuse keyboard input")
        window.type_keys("%{ENTER}",set_foreground=False)
        def properties():
            nonlocal props
            matches=[]
            for candidate in Desktop(backend="uia").windows():
                try:
                    if candidate.handle in baseline or not candidate.is_visible():
                        continue
                    label=candidate.window_text()
                    if not re.search(r"(properties|속성)",label,re.I):
                        continue
                    child=" ".join(x.window_text()
                                   for x in candidate.descendants()[:120])
                    if file.name.casefold() in (label+" "+child).casefold():
                        matches.append(candidate)
                except Exception:pass
            if len(matches)!=1:return False
            props=matches[0]
            return True
        until(properties,"Explorer OS baseline Properties dialog not found",18)
        rect=props.rectangle()
        assert rect.width()>=220 and rect.height()>=160
        assert props.handle not in baseline
        assert file.name.casefold() in (
            props.window_text()+" "+" ".join(
                x.window_text() for x in props.descendants()[:120])).casefold()
        ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                       include_layered_windows=True).save(
                           base/"owned-os-properties-baseline.png")
        print("OWNED_EXPLORER_OS_PROPERTIES_VISIBLE",True,flush=True)
        print("OWNED_EXPLORER_OS_PROPERTIES_DIMENSIONS",
              rect.width(),rect.height(),flush=True)
        assert u.PostMessageW(props.handle,0x10,0,0)
        until(lambda:all(x.handle!=props.handle for x in
                          Desktop(backend="uia").windows()),
              "Test-owned Explorer Properties dialog not closed",12)
        print("OWNED_EXPLORER_OS_PROPERTIES_CLOSED",True,flush=True)
        assert file.read_bytes()==expected
        success=True
    finally:
        if props is not None and props.handle not in baseline:
            try:
                if "properties" in props.window_text().casefold() or \
                   "속성" in props.window_text():
                    u.PostMessageW(props.handle,0x10,0,0)
            except Exception:pass
        if explorer is not None:
            try:
                if int(explorer.HWND) not in preexplorer and \
                   str(explorer.LocationURL).rstrip("/").casefold()==target:
                    u.PostMessageW(int(explorer.HWND),0x10,0,0)
            except Exception:pass
        unchanged=all((mfc/n).is_file() and
                      hashlib.sha256((mfc/n).read_bytes()).digest()==digest
                      for n,digest in hashes.items())
        print("OWNED_EXPLORER_OS_PROPERTIES_MFC_IDENTICAL",unchanged,flush=True)
        if success and unchanged and file.is_file() and file.read_bytes()==expected:
            shutil.rmtree(owned)
        else:
            print("OWNED_EXPLORER_OS_PROPERTIES_FIXTURE_RETAINED",
                  owned,flush=True)
    return 0 if success and unchanged else 1

if __name__=="__main__":
    sys.exit(main())
