"""Positive real run.bat Release launch with exact test-owned GUI and process exit.

This uses the canonical launcher (rather than directly launching the EXE),
tests real dual pane UIA and resource/helper presence, then closes ONLY the
window spawned from the disposable profile and fixture.
"""
from __future__ import annotations
import ctypes as c
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import shutil

from paths import ROOT, app_exe, helper_exe
from profile_guard import snapshot_legacy_profile, assert_legacy_profile_unchanged
from uia_polling import wait_until
import psutil
from pywinauto import Desktop

assert os.name == "nt"
exe=app_exe("Release")
helper=helper_exe("Release")
assert exe.is_file() and helper.is_file(), "complete Release binaries missing"
assert (exe.parent/"FlyShellIsolationHelper.exe").is_file(), "sibling helper missing"
assert (ROOT/"run.bat").is_file()
original,old=snapshot_legacy_profile()
base=ROOT/"logs"/"run-bat-owned"
base.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix="run-bat-owned-",dir=base))
for name in ("folder", "appdata", "localdata", "tmp"):
    (owned/name).mkdir()
(owned/"folder"/"run-bat-한글.txt").write_text("exact owned launch fixture",encoding="utf-8")
user=c.windll.user32
user.GetForegroundWindow.restype=W.HWND
user.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
cb=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
user.EnumWindows.argtypes=[cb,W.LPARAM]

def owned_windows(pid):
    found=[]
    @cb
    def visit(hwnd,_):
        value=W.DWORD()
        user.GetWindowThreadProcessId(hwnd,c.byref(value))
        if value.value==pid and user.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    user.EnumWindows(visit,0)
    return found

def launched():
    exact=os.path.normcase(str(exe.resolve()))
    target=os.path.normcase(str((owned/"folder").resolve()))
    found=[]
    for proc in psutil.process_iter(["pid","exe","cmdline"]):
        try:
            if os.path.normcase(str(proc.info.get("exe") or ""))!=exact:
                continue
            args=proc.info.get("cmdline") or []
            if any(os.path.normcase(str(arg))==target for arg in args[1:]):
                found.append(proc)
        except (psutil.AccessDenied,psutil.NoSuchProcess):
            pass
    return found

proc=None
try:
    assert not launched(), "existing process with exact owned fixture"
    env={**os.environ,"APPDATA":str(owned/"appdata"),
         "LOCALAPPDATA":str(owned/"localdata"),
         "TEMP":str(owned/"tmp"),"TMP":str(owned/"tmp")}
    invoke=subprocess.run(
        ["cmd.exe","/d","/c",str(ROOT/"run.bat"),"Release",str(owned/"folder")],
        cwd=ROOT,env=env,stdin=subprocess.DEVNULL,
        # Windows start can let the GUI child inherit pipe handles. Waiting
        # for PIPE EOF here deadlocks until that child exits, before UIA can
        # validate and close it. The launcher has no expected output contract.
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=18,
        creationflags=subprocess.CREATE_NO_WINDOW)
    assert invoke.returncode==0, ("run.bat returned failure",invoke.returncode)
    print("REAL_RUN_BAT_RELEASE_DISPATCH_0",True,flush=True)
    wait_until(lambda: len(launched())==1, "run.bat did not spawn exactly one owned app",
               seconds=23,interval=.18)
    proc=launched()[0]
    pid=proc.pid
    wait_until(lambda: len(owned_windows(pid))>=1 or not proc.is_running(),
               "owned WinUI window missing after canonical launcher",seconds=20,interval=.15)
    assert proc.is_running() and len(owned_windows(pid))==1
    hwnd=owned_windows(pid)[0]
    win=Desktop(backend="uia").window(handle=hwnd)
    for control in ("LeftFiles","RightFiles","AddressBox","StatusText","WindowTabStrip"):
        assert win.child_window(auto_id=control).exists(timeout=7),control
    def contents():
        return [x.window_text() for x in
                win.child_window(auto_id="LeftFiles").descendants(control_type="ListItem")]
    wait_until(lambda: any("run-bat-한글.txt" in n for n in contents()),
               "real file row not displayed",seconds=20,interval=.2)
    wait_until(lambda: str(owned/"folder").casefold() in
               win.child_window(auto_id="AddressBox").get_value().casefold(),
               "canonical launcher folder argument not honored",seconds=12,interval=.2)
    print("REAL_RUN_BAT_DUAL_PANES_AND_UNICODE_FILE",True,flush=True)
    owner=W.DWORD()
    user.GetWindowThreadProcessId(hwnd,c.byref(owner))
    assert owner.value==pid, "Refuse close of a non-owned HWND"
    assert user.PostMessageW(hwnd,0x0010,0,0),"owned WM_CLOSE failed"
    try:
        rc=proc.wait(timeout=18)
    except psutil.TimeoutExpired:
        raise AssertionError("owned app did not exit normally on WM_CLOSE")
    assert rc==0, ("run.bat launched app crashed during shutdown",rc)
    print("REAL_RUN_BAT_OWNED_PROCESS_EXIT_0",True,flush=True)
finally:
    if proc is not None and proc.is_running():
        proc.terminate()
        try: proc.wait(timeout=6)
        except psutil.TimeoutExpired: proc.kill();proc.wait(timeout=6)
    assert_legacy_profile_unchanged(original,old)
    shutil.rmtree(owned)
print("REAL_RUN_BAT_RELEASE_ACCEPTANCE=PASS",flush=True)
