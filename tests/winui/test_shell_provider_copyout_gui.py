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
    destination_sentinel=destination/"destination-ready.txt"
    destination_sentinel.write_text("owned destination sentinel\n",encoding="utf-8")
    workspace=owned/"provider-copyout.fxworkspace"
    provider_root=r"::{031E4825-7B94-4DC3-B131-E946B44C8DD5}\Pictures.library-ms"
    workspace.write_text(
        "[main]\r\n"
        "main.view.row_count = 1\r\n"
        "main.view.column_count = 2\r\n"
        "main.view1.current_tab = 0\r\n"
        f"main.view1.tab1.path = {provider_root}\r\n"
        "main.view2.current_tab = 0\r\n"
        f"main.view2.tab1.path = {destination}\r\n"
        "\r\n[workspace]\r\nschema = 1\r\n",
        encoding="utf-16")

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
        [str(exe),"--m19-workspace",str(workspace)],cwd=exe.parent,env=env,
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

        # Restore both panes atomically through the existing validated M19
        # workspace bridge: left is the canonical Pictures Library provider
        # identity, right is the test-owned filesystem destination.
        def source_row():
            matches=[x for x in left.descendants()
                     if x.element_info.control_type=="ListItem"
                     and MEMBER in x.window_text()]
            return matches[0] if len(matches)==1 else None
        def destination_ready():
            return any("destination-ready.txt" in x.window_text()
                       for x in right.descendants()
                       if x.element_info.control_type=="ListItem")
        until(lambda:source_row() is not None,
              "owned Pictures Library provider item did not enumerate",28)
        until(destination_ready,
              "workspace did not commit right destination filesystem pane",28)
        print("SHELL_PROVIDER_COPYOUT_PICTURES_ENUMERATION",True,flush=True)
        print("SHELL_PROVIDER_COPYOUT_DESTINATION_READY",True,flush=True)

        parent.child_window(auto_id="PrimaryPaneTitle").invoke()
        until(lambda:"왼쪽 창을 선택했습니다" in status.window_text(),
              "left pane activation did not commit",8)
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
        copy_button=parent.child_window(auto_id="CopyButton")
        cancel_button=parent.child_window(auto_id="CancelButton")
        until(lambda:copy_button.is_enabled() and not cancel_button.is_enabled(),
              "provider Copy-out controller did not return idle",12)
        print("SHELL_PROVIDER_COPYOUT_CONTROLLER_IDLE",True,flush=True)
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
