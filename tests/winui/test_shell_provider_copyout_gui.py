"""Focused real Windows Compressed Folder provider Copy-out acceptance."""
import ctypes as c
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import zipfile

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
MEMBER="provider-copy-out-owned.txt"
PAYLOAD="flyExplorer provider copy-out owned payload\n"

def until(fn,label,seconds=28):
    return wait_until(fn,label,seconds=seconds,interval=.25)

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    args=parser.parse_args()
    if os.name!="nt":
        return 2

    exe=app_exe(args.configuration).resolve()
    assert exe.is_file(),exe
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}

    evidence=ROOT/"logs"/"shell-provider-copyout"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="shell-provider-copyout-owned-",dir=evidence))
    archive=owned/"provider-source.zip"
    destination=owned/"destination"
    destination.mkdir()
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MEMBER,PAYLOAD)

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower()
        target.mkdir()
        env[key]=str(target)
    pref=Path(env["LOCALAPPDATA"])/"flyExplorer"
    pref.mkdir(parents=True,exist_ok=True)
    (pref/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")

    process=subprocess.Popen(
        [str(exe),str(destination)],cwd=exe.parent,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    parent=None
    success=False
    user32=c.windll.user32
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:
                return False
            wins=[w for w in Desktop(backend="uia").windows(process=process.pid)
                  if "flyExplorer" in w.window_text()]
            if len(wins)!=1:
                return False
            parent=Desktop(backend="uia").window(handle=wins[0].handle)
            return (parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
                    and parent.child_window(auto_id="RightFiles").exists(timeout=.2))
        until(ready,"provider copy-out fixture window not ready",24)

        left=parent.child_window(auto_id="LeftFiles")
        right=parent.child_window(auto_id="RightFiles")
        address=parent.child_window(auto_id="AddressBox")
        status=parent.child_window(auto_id="StatusText")

        def focus_owned():
            parent.set_focus()
            time.sleep(.10)
            return True

        # Use the product's accepted F6 split-pane traversal rather than
        # service-desktop mouse movement. Startup activates the left pane.
        focus_owned()
        send_keys("{F6}")
        time.sleep(.25)
        address.set_edit_text(str(destination))
        address.type_keys("{ENTER}",set_foreground=True)
        until(lambda:str(destination).lower() in address.get_value().lower(),
              "right destination folder did not open",18)

        # Return to the left pane and open the test-owned ZIP through Windows'
        # built-in Compressed Folder Shell provider.
        focus_owned()
        send_keys("{F6}")
        time.sleep(.25)
        address.set_edit_text(str(archive))
        address.type_keys("{ENTER}",set_foreground=True)

        def source_row():
            matches=[x for x in left.descendants()
                     if x.element_info.control_type=="ListItem"
                     and MEMBER in x.window_text()]
            return matches[0] if len(matches)==1 else None
        until(lambda:source_row() is not None,
              "ZIP provider member did not enumerate",24)
        print("SHELL_PROVIDER_COPYOUT_ZIP_ENUMERATION",True,flush=True)

        focus_owned()
        source_row().select()
        until(lambda:source_row().is_selected(),
              "provider source selection was lost",8)

        # The same provider source MUST remain move-closed in this unit.
        move=parent.child_window(auto_id="MoveButton")
        focus_owned()
        move.invoke()
        until(lambda:"복사만 지원" in status.window_text(),
              "provider Move was not rejected by copy-only policy",8)
        assert not (destination/MEMBER).exists()
        print("SHELL_PROVIDER_COPYOUT_MOVE_REMAINS_REJECTED",True,flush=True)

        # Copy-out materializes the provider item into the real opposite folder.
        copy=parent.child_window(auto_id="CopyButton")
        focus_owned()
        copy.invoke()
        until(lambda:(destination/MEMBER).is_file(),
              "provider Copy-out did not materialize destination file",24)
        assert (destination/MEMBER).read_text(encoding="utf-8")==PAYLOAD
        until(lambda:"복사를 완료했습니다" in status.window_text(),
              "provider Copy-out completion status missing",12)

        with zipfile.ZipFile(archive,"r") as zf:
            assert MEMBER in zf.namelist()
            assert zf.read(MEMBER).decode("utf-8")==PAYLOAD
        print("SHELL_PROVIDER_COPYOUT_PASS",True,flush=True)
        print("SHELL_PROVIDER_COPYOUT_SOURCE_PRESERVED",True,flush=True)
        success=True
    finally:
        if process.poll() is None:
            try:
                user32.PostMessageW(parent.handle if parent else 0,0x10,0,0)
                process.wait(timeout=12)
            except Exception:
                process.terminate()
                process.wait(timeout=8)
        unchanged=all((real/name).is_file() and
            hashlib.sha256((real/name).read_bytes()).digest()==digest
            for name,digest in hashes.items())
        print("SHELL_PROVIDER_COPYOUT_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("SHELL_PROVIDER_COPYOUT_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged:
            shutil.rmtree(owned,ignore_errors=True)
            print("SHELL_PROVIDER_COPYOUT_FIXTURE_REMOVED",not owned.exists(),flush=True)
        else:
            print("SHELL_PROVIDER_COPYOUT_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged else 1

if __name__=="__main__":
    raise SystemExit(main())
