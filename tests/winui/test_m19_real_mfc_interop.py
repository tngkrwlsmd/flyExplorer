"""M1.9 REAL legacy-MFC-written UXH-07 snapshots -> independently owned WinUI GUI.

Run only AFTER the existing MFC test-owned generator succeeded:
 M19_NATIVE_WORKSPACE_OWNER=<exact logs/uxh07-named-owned-... dir>
 FLY_MIGRATION_CONFIGURATION=Debug|Release

Never opens or modifies the real user's MFC profile, registry or windows.
A WinUI-created subset roundtrip into an actual MFC Open dialog is
separate follow-up work, and is not asserted here.
"""
import ctypes as c
from ctypes import wintypes as W
from pathlib import Path
from paths import ROOT, APP, app_exe
import hashlib
import os
import psutil
import re
import shutil
import subprocess
import tempfile
import time
from pywinauto import Desktop

HERE=APP
owner_arg=os.environ.get("M19_NATIVE_WORKSPACE_OWNER","")
assert owner_arg,"Explicit original test-owned MFC UXH07 fixture directory required"
owner=Path(owner_arg).resolve()
assert owner.is_dir() and owner.parent==ROOT/"logs"
assert owner.name.startswith("uxh07-named-owned-"),"Not an owned MFC fixture"
conf=Path(os.environ["APPDATA"])/"fxfile"/"conf"
NAMES=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
assert all((conf/n).is_file() for n in NAMES)
before={n:hashlib.sha256((conf/n).read_bytes()).hexdigest() for n in NAMES}
configuration=os.environ.get("FLY_MIGRATION_CONFIGURATION","Debug")
assert configuration in ("Debug","Release")
exe=app_exe(configuration)
assert exe.is_file()
base=ROOT/"logs"/"m19"
own=Path(tempfile.mkdtemp(prefix="m19-actual-mfc-schema-",dir=base))
for folder in ("appdata","localdata","tmp"):(own/folder).mkdir()
env={**os.environ,"APPDATA":str(own/"appdata"),
     "LOCALAPPDATA":str(own/"localdata"),
     "TEMP":str(own/"tmp"),"TMP":str(own/"tmp")}
u=c.windll.user32
CALL=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CALL,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
def windows(pid):
    found=[]
    @CALL
    def cb(h,_):
        actual=W.DWORD()
        u.GetWindowThreadProcessId(h,c.byref(actual))
        if actual.value==pid and u.IsWindowVisible(h):
            found.append(int(h))
        return 1
    u.EnumWindows(cb,0)
    return found
def eventual(test,label,seconds=16):
    stop=time.monotonic()+seconds
    while time.monotonic()<stop:
        try:
            if test():return
        except Exception:pass
        time.sleep(.17)
    raise AssertionError(label)
def keys(source):
    body=source.read_text(encoding="utf-16")
    assert "[main]" in body and "[workspace]" in body and len(body)<524288
    result={}
    section=""
    for line in body.splitlines():
        line=line.strip()
        if line.startswith("[") and line.endswith("]"):
            section=line.lower()
            continue
        if section in ("[main]","[workspace]") and "=" in line:
            k,v=line.split("=",1)
            result[k.strip().lower()]=v.strip()
    assert result["schema"]=="1"
    assert result["main.view.row_count"]=="1"
    assert result["main.view.column_count"]=="2"
    for side in (1,2):
        assert Path(result[f"main.view{side}.tab1.path"]).is_dir()
    return result
try:
    for name,expected_tabs in (
        ("test-named-workspace.fxworkspace",1),
        ("second-distinct-named.fxworkspace",2)):
        original=owner/name
        assert original.is_file() and original.stat().st_size<1048576
        doc=keys(original)
        print("NATIVE_MFC_WRITTEN_SNAPSHOT_SHA256",name,
              hashlib.sha256(original.read_bytes()).hexdigest().upper(),flush=True)
        source=original
        if expected_tabs==2:
            # The real MFC test's second tab points at the real user's
            # virtual Documents GUID. Do not enumerate an unowned user's
            # Documents during an interoperability test. Retain ALL other
            # bytes/keys of the actual MFC-produced file and substitute
            # only that known test fixture tab for an OWNED local folder.
            prior=doc["main.view1.tab2.path"]
            assert prior.startswith("::"),"Unexpected native fixture target"
            owned_second=own/"Owned synthetic replacement for virtual Documents"
            owned_second.mkdir()
            native_text=original.read_text(encoding="utf-16")
            assert native_text.count(prior)==1
            safe_text=native_text.replace(prior,str(owned_second),1)
            source=own/"owned-mfc-generated-two-tab-safe.fxworkspace"
            source.write_bytes(safe_text.encode("utf-16"))
            doc=keys(source)
            print("M19_NATIVE_MFC_SECOND_VIRTUAL_TEST_TARGET_REPLACED_WITH_OWNED_FOLDER",
                  True,flush=True)
        selected=int(doc["main.view1.current_tab"])
        assert selected==expected_tabs-1
        target=doc[f"main.view1.tab{selected+1}.path"]
        secondary=doc["main.view2.tab1.path"]
        proc=subprocess.Popen([str(exe),"--m19-workspace",str(source)],
            cwd=exe.parent,env=env,stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        helpers=[]
        try:
            eventual(lambda:len(windows(proc.pid))>=1 or proc.poll() is not None,
                     "MFC-owned workspace did not launch exact WinUI preview",15)
            assert proc.poll() is None,("WinUI crashed loading real MFC snapshot",
                                       name,proc.returncode)
            main_window=Desktop(backend="uia").window(handle=windows(proc.pid)[0])
            address=main_window.child_window(auto_id="AddressBox")
            eventual(lambda:target.lower() in address.get_value().lower(),
                     "Actual MFC-authored selected tab failed in WinUI",24)
            left=main_window.child_window(auto_id="LeftTabs")
            eventual(lambda:len([x for x in left.descendants()
                     if x.element_info.control_type=="TabItem"])==expected_tabs,
                     "Actual MFC-authored tab count failed in WinUI",12)
            main_window.set_focus()
            main_window.child_window(auto_id="SecondaryPaneTitle").click_input()
            eventual(lambda:secondary.lower() in address.get_value().lower(),
                     "Actual MFC-authored RIGHT folder not restored in WinUI",15)
            main_window.child_window(auto_id="PrimaryPaneTitle").click_input()
            eventual(lambda:target.lower() in address.get_value().lower(),
                     "Actual MFC selected LEFT tab not preserved across pane switch",9)
            helpers=psutil.Process(proc.pid).children(recursive=True)
            print("REAL_M19_ACTUAL_MFC_GENERATED_WORKSPACE_RESTORED_IN_WINUI",
                  name,"SELECTED",selected,"TABS",expected_tabs,
                  "HELPERS",len(helpers),flush=True)
        finally:
            if proc.poll() is None:
                visible=windows(proc.pid)
                assert visible, "Only close an exactly owned WinUI window"
                u.PostMessageW(visible[0],0x10,0,0)
                try:proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    proc.terminate();proc.wait(timeout=5)
                    raise AssertionError("Owned WinUI legacy-interop app did not exit")
            assert proc.returncode==0,(name,proc.returncode)
            for helper in helpers:
                eventual(lambda h=helper:not h.is_running() or
                    h.status()==psutil.STATUS_ZOMBIE,
                    "owned Shell helper not reclaimed on child exit",9)
    print("REAL_M19_EXACT_NATIVE_MFC_SINGLE_TAB_AND_OWNED_SANITIZED_NATIVE_TWO_TAB_ACCEPTED",
          True,flush=True)
finally:
    assert all(hashlib.sha256((conf/n).read_bytes()).hexdigest()==before[n]
               for n in NAMES),"Real user settings changed"
    print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",True,flush=True)
    assert own.parent==base and own.name.startswith("m19-actual-mfc-schema-")
    shutil.rmtree(own)
    print("OWNED_M19_NATIVE_INTEROPERABILITY_PROFILE_REMOVED",True,flush=True)
