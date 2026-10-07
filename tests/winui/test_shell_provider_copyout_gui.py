"""Focused virtual Pictures Library provider-root Copy-out acceptance."""
import ctypes as c
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from pywinauto import Desktop
from pywinauto.keyboard import send_keys

from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
MEMBER="flyExplorer-provider-copy-out-owned.txt"
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

    pictures=Path(os.path.expandvars(r"%USERPROFILE%\Pictures"))
    assert pictures.is_dir(),pictures
    source=pictures/MEMBER
    assert not source.exists(),source
    source.write_text(PAYLOAD,encoding="utf-8")

    evidence=ROOT/"logs"/"shell-provider-copyout"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="shell-provider-copyout-owned-",dir=evidence))
    destination=owned/"destination"
    destination.mkdir()

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
        [str(exe),"shell:PicturesLibrary"],cwd=exe.parent,env=env,
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
        address=parent.child_window(auto_id="AddressBox")
        status=parent.child_window(auto_id="StatusText")

        def focus_owned():
            parent.set_focus()
            time.sleep(.10)

        # Start directly in the same built-in virtual Pictures Library route
        # already accepted by provider visual/thumbnail validation. This avoids
        # making the fixture depend on a filesystem -> virtual address transition.
        until(lambda:"Pictures.library-ms" in address.get_value() or
                     address.get_value() in ("그림","사진"),
              "Pictures Library virtual root did not open",20)

        def source_row():
            matches=[x for x in left.descendants()
                     if x.element_info.control_type=="ListItem"
                     and MEMBER in x.window_text()]
            return matches[0] if len(matches)==1 else None
        until(lambda:source_row() is not None,
              "owned Pictures Library provider item did not enumerate",24)
        print("SHELL_PROVIDER_COPYOUT_PICTURES_ENUMERATION",True,flush=True)

        # Only after the provider source has been observed, pin the opposite
        # pane to the test-owned filesystem destination. F6 changes pane focus
        # without physical pointer input; the left provider route must survive.
        focus_owned();send_keys("{F6}");time.sleep(.2)
        address.set_edit_text(str(destination))
        address.type_keys("{ENTER}",set_foreground=True)
        until(lambda:str(destination).lower() in address.get_value().lower(),
              "right destination folder did not open",18)
        assert source_row() is not None,(
            "opening the opposite destination replaced provider source pane")

        focus_owned();send_keys("{F6}");time.sleep(.2)
        source_row().select()
        until(lambda:source_row().is_selected(),
              "provider source selection was lost",8)

        # Provider-root sources remain copy-only in this unit.
        parent.child_window(auto_id="MoveButton").invoke()
        until(lambda:"복사만 지원" in status.window_text(),
              "provider Move was not rejected by copy-only policy",8)
        assert not (destination/MEMBER).exists()
        print("SHELL_PROVIDER_COPYOUT_MOVE_REMAINS_REJECTED",True,flush=True)

        parent.child_window(auto_id="CopyButton").invoke()
        until(lambda:"복사만 지원" not in status.window_text(),
              "provider Copy-out command did not leave Move rejection status",8)
        print("SHELL_PROVIDER_COPYOUT_COPY_START_STATUS",
              repr(status.window_text()),flush=True)
        def copy_finished():
            text=status.window_text()
            return ((destination/MEMBER).is_file() or
                    "복사를 완료했습니다" in text or
                    "완료하지 못했습니다" in text or
                    "올바르지 않습니다" in text or
                    "권한이 없습니다" in text or
                    "취소했습니다" in text or
                    "오류:" in text)
        until(copy_finished,"provider Copy-out never completed",24)
        print("SHELL_PROVIDER_COPYOUT_COPY_FINAL_STATUS",
              repr(status.window_text()),flush=True)
        assert (destination/MEMBER).is_file(),(
            "provider Copy-out did not materialize destination file",
            status.window_text())
        assert (destination/MEMBER).read_text(encoding="utf-8")==PAYLOAD
        until(lambda:"복사를 완료했습니다" in status.window_text(),
              "provider Copy-out completion status missing",12)
        assert source.read_text(encoding="utf-8")==PAYLOAD
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
        source.unlink(missing_ok=True)
        unchanged=all((real/name).is_file() and
            hashlib.sha256((real/name).read_bytes()).digest()==digest
            for name,digest in hashes.items())
        print("SHELL_PROVIDER_COPYOUT_OWNED_SOURCE_REMOVED",
              not source.exists(),flush=True)
        print("SHELL_PROVIDER_COPYOUT_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("SHELL_PROVIDER_COPYOUT_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged and not source.exists():
            shutil.rmtree(owned,ignore_errors=True)
            print("SHELL_PROVIDER_COPYOUT_FIXTURE_REMOVED",not owned.exists(),flush=True)
        else:
            print("SHELL_PROVIDER_COPYOUT_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged and not source.exists() else 1

if __name__=="__main__":
    raise SystemExit(main())
