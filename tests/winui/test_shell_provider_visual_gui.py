"""Matched app-owned capture for virtual Shell/provider type/icon acceptance."""
import argparse
import ctypes as c
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image
from pywinauto import Desktop
import psutil

from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")

def until(fn,label,timeout=28):
    return wait_until(fn,label,seconds=timeout,interval=.25)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--capture",choices=("before","after"),required=True)
    parser.add_argument("--expect-provider-visual",action="store_true")
    args=parser.parse_args()
    if os.name!="nt":
        return 2

    exe=app_exe(args.configuration).resolve()
    assert exe.is_file(),exe
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}

    evidence=ROOT/"logs"/"shell-provider-visual"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="shell-provider-visual-owned-",dir=evidence))
    folder=owned/"fixture"
    folder.mkdir()
    (folder/"startup-owned.txt").write_text("owned",encoding="utf-8")
    shot=evidence/f"shell-provider-visual-{args.capture}.bmp"
    if shot.exists():
        shot.unlink()

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower()
        target.mkdir()
        env[key]=str(target)
    pref=Path(env["LOCALAPPDATA"])/"flyExplorer"
    pref.mkdir(parents=True,exist_ok=True)
    (pref/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
    env["FLY_SHELL_PROVIDER_VISUAL_CAPTURE_PATH"]=str(shot)

    process=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    parent=None
    success=False
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:
                return False
            if Path(psutil.Process(process.pid).exe()).resolve()!=exe:
                raise AssertionError("owned executable changed")
            wins=[w for w in Desktop(backend="uia").windows(process=process.pid)
                  if "flyExplorer" in w.window_text()]
            if len(wins)!=1:
                return False
            parent=Desktop(backend="uia").window(handle=wins[0].handle)
            return parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(ready,"Shell provider visual fixture window not ready",24)

        pane=parent.child_window(auto_id="LeftFiles")
        address=parent.child_window(auto_id="AddressBox")
        pane.click_input()
        address.set_edit_text("shell:MyComputerFolder")
        address.type_keys("{ENTER}",set_foreground=True)
        until(lambda:address.get_value()=="내 PC",
              "This PC virtual Shell root did not open",20)

        def rows():
            return [x for x in pane.descendants()
                    if x.element_info.control_type=="ListItem"]
        until(lambda:len(rows())>0,"This PC virtual Shell rows did not render",20)
        observed=[x.window_text() for x in rows()]
        print("SHELL_PROVIDER_VISUAL_ROWS",repr(observed[:12]),flush=True)

        if args.expect_provider_visual:
            def provider_row():
                for item in rows():
                    text=item.window_text()
                    if "   |   " not in text:
                        continue
                    type_text=text.split("   |   ",1)[1].split("   |   ",1)[0].strip()
                    images=[v for v in item.descendants()
                            if v.element_info.control_type=="Image" and v.is_visible()]
                    if type_text and type_text!="폴더" and any(
                        "Windows Shell folder icon" in (v.element_info.name or "")
                        for v in images):
                        return item
                return None
            until(lambda:provider_row() is not None,
                  "This PC rows never received provider type/icon detail",12)
            chosen=provider_row()
            print("SHELL_PROVIDER_TYPE_ICON_PASS",True,flush=True)
            print("SHELL_PROVIDER_VISUAL_ROW",chosen.window_text(),flush=True)
        else:
            print("SHELL_PROVIDER_BASELINE_CAPTURE",True,flush=True)

        until(lambda:shot.is_file() and shot.stat().st_size>4096,
              "app-owned provider visual capture did not complete",12)
        with Image.open(shot) as captured:
            width,height=captured.size
            assert width>600 and height>400,(width,height)
            sampled=list(captured.convert("RGB").resize((96,52)).getdata())
            ratio=sum(1 for r,g,b in sampled if max(r,g,b)>=24)/len(sampled)
            print("SHELL_PROVIDER_VISUAL_NONBLACK_RATIO",f"{ratio:.4f}",flush=True)
            assert ratio>.08,("captured XAML visual is effectively black",ratio)
        print("SHELL_PROVIDER_VISUAL_WINDOW_RECT",width,height,flush=True)
        print("SHELL_PROVIDER_VISUAL_SCREENSHOT",shot.name,flush=True)
        success=True
    finally:
        if process.poll() is None:
            try:
                c.windll.user32.PostMessageW(parent.handle if parent else 0,0x10,0,0)
                process.wait(timeout=12)
            except Exception:
                process.terminate()
                process.wait(timeout=8)
        unchanged=all((real/name).is_file() and
            hashlib.sha256((real/name).read_bytes()).digest()==digest
            for name,digest in hashes.items())
        print("SHELL_PROVIDER_VISUAL_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("SHELL_PROVIDER_VISUAL_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged:
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("SHELL_PROVIDER_VISUAL_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged else 1

if __name__=="__main__":
    raise SystemExit(main())
