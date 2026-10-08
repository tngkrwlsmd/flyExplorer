"""Owned two-pane Pictures Library Copy-in GUI acceptance."""
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
MEMBER="flyExplorer-provider-copy-in-owned.txt"
SENTINEL="flyExplorer-provider-copy-in-sentinel.txt"
PAYLOAD="flyExplorer provider Copy-in test-owned payload\n"

def until(fn,label,seconds=28):
    return wait_until(fn,label,seconds=seconds,interval=.25)

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    args=parser.parse_args()
    if os.name!="nt":return 2
    exe=app_exe(args.configuration).resolve()
    assert exe.is_file(),exe
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}
    pictures=Path(os.path.expandvars(r"%USERPROFILE%\Pictures"))
    assert pictures.is_dir(),pictures
    output=pictures/MEMBER
    sentinel=pictures/SENTINEL
    assert not output.exists(),output
    assert not sentinel.exists(),sentinel
    evidence=ROOT/"logs"/"shell-provider-copyin"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="shell-provider-copyin-owned-",dir=evidence))
    origin=owned/"origin"
    origin.mkdir()
    source=origin/MEMBER
    source.write_text(PAYLOAD,encoding="utf-8")
    sentinel.write_text("owned sentinel\n",encoding="utf-8")
    workspace=owned/"provider-copyin.fxworkspace"
    provider_root=r"::{031E4825-7B94-4DC3-B131-E946B44C8DD5}\Pictures.library-ms"
    workspace.write_text(
        "[main]\r\n"
        "main.view.row_count = 1\r\n"
        "main.view.column_count = 2\r\n"
        "main.view1.current_tab = 0\r\n"
        f"main.view1.tab1.path = {origin}\r\n"
        "main.view2.current_tab = 0\r\n"
        f"main.view2.tab1.path = {provider_root}\r\n"
        "\r\n[workspace]\r\nschema = 1\r\n",encoding="utf-16")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        path=owned/key.lower()
        path.mkdir()
        env[key]=str(path)
    pref=Path(env["LOCALAPPDATA"])/"flyExplorer"
    pref.mkdir(parents=True,exist_ok=True)
    (pref/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
    process=subprocess.Popen([str(exe),"--m19-workspace",str(workspace)],
                             cwd=exe.parent,env=env,
                             stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    parent=None
    success=False
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:return False
            wins=[w for w in Desktop(backend="uia").windows(process=process.pid)
                  if "flyExplorer" in w.window_text()]
            if len(wins)!=1:return False
            parent=Desktop(backend="uia").window(handle=wins[0].handle)
            return (parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
                    and parent.child_window(auto_id="RightFiles").exists(timeout=.2))
        until(ready,"provider Copy-in window",24)
        left=parent.child_window(auto_id="LeftFiles")
        right=parent.child_window(auto_id="RightFiles")
        status=parent.child_window(auto_id="StatusText")
        def source_row():
            rows=[x for x in left.descendants()
                  if x.element_info.control_type=="ListItem" and
                  MEMBER in x.window_text()]
            return rows[0] if len(rows)==1 else None
        until(lambda:source_row() is not None,"filesystem source not shown",28)
        until(lambda:any(SENTINEL in x.window_text() for x in right.descendants()
                  if x.element_info.control_type=="ListItem"),
              "Pictures Library provider target not shown",28)
        print("SHELL_PROVIDER_COPYIN_DESTINATION_READY",True,flush=True)
        parent.child_window(auto_id="PrimaryPaneTitle").invoke()
        until(lambda:"왼쪽 창을 선택했습니다" in status.window_text(),
              "source pane activation did not commit",8)
        source_row().select()
        until(lambda:source_row().is_selected(),"source not selected",8)
        parent.child_window(auto_id="MoveButton").invoke()
        until(lambda:"파일 복사만 지원" in status.window_text(),
              "provider target Move was not rejected",8)
        assert not output.exists()
        print("SHELL_PROVIDER_COPYIN_MOVE_REJECTED",True,flush=True)
        parent.child_window(auto_id="CopyButton").invoke()
        until(lambda:output.is_file() or "오류:" in status.window_text() or
                    "권한이 없습니다" in status.window_text() or
                    "올바르지 않습니다" in status.window_text() or
                    "완료하지 못했습니다" in status.window_text(),
              "provider Copy-in did not finish",28)
        print("SHELL_PROVIDER_COPYIN_FINAL_STATUS",repr(status.window_text()),flush=True)
        assert output.is_file(),("provider target Copy-in failed",status.window_text())
        assert output.read_text(encoding="utf-8")==PAYLOAD
        assert source.read_text(encoding="utf-8")==PAYLOAD
        until(lambda:parent.child_window(auto_id="CopyButton").is_enabled()
              and not parent.child_window(auto_id="CancelButton").is_enabled(),
              "provider Copy-in controller not idle",12)
        print("SHELL_PROVIDER_COPYIN_PASS",True,flush=True)
        print("SHELL_PROVIDER_COPYIN_SOURCE_PRESERVED",True,flush=True)
        success=True
    finally:
        if process.poll() is None:
            try:
                c.windll.user32.PostMessageW(parent.handle if parent else 0,0x10,0,0)
                process.wait(timeout=12)
            except Exception:
                process.terminate();process.wait(timeout=8)
        output.unlink(missing_ok=True)
        sentinel.unlink(missing_ok=True)
        unchanged=all((real/name).is_file() and
            hashlib.sha256((real/name).read_bytes()).digest()==digest
            for name,digest in hashes.items())
        print("SHELL_PROVIDER_COPYIN_OWNED_ITEMS_REMOVED",
              not output.exists() and not sentinel.exists(),flush=True)
        print("SHELL_PROVIDER_COPYIN_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("SHELL_PROVIDER_COPYIN_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged and not output.exists() and not sentinel.exists():
            shutil.rmtree(owned,ignore_errors=True)
            print("SHELL_PROVIDER_COPYIN_FIXTURE_REMOVED",not owned.exists(),flush=True)
        else:
            print("SHELL_PROVIDER_COPYIN_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged and not output.exists() and not sentinel.exists() else 1
if __name__=="__main__":
    raise SystemExit(main())
