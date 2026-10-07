"""Focused visual/type/icon/thumbnail acceptance for isolated filesystem detail paths."""
import argparse
import ctypes as c
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from PIL import Image,ImageDraw
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
    parser.add_argument("--force-network-detail",action="store_true")
    parser.add_argument("--force-removable-detail",action="store_true")
    args=parser.parse_args()
    if args.force_network_detail and args.force_removable_detail:
        parser.error("choose only one forced detail path")
    if os.name!="nt":
        return 2

    exe=app_exe(args.configuration).resolve()
    assert exe.is_file(),exe
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}

    evidence=ROOT/"logs"/"network-visual"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="network-visual-owned-",dir=evidence))
    folder=owned/"fixture"
    folder.mkdir()
    (folder/"folder-owned").mkdir()
    (folder/"note-owned.txt").write_text("owned text\n",encoding="utf-8")
    picture=folder/"image-owned.png"
    shot=evidence/f"network-visual-{args.capture}.bmp"
    if shot.exists():
        shot.unlink()
    img=Image.new("RGBA",(96,64),(27,89,183,255))
    draw=ImageDraw.Draw(img)
    draw.rectangle((48,0,95,63),fill=(227,116,28,255))
    draw.ellipse((27,16,68,57),fill=(44,160,98,255))
    img.save(picture)

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower()
        target.mkdir()
        env[key]=str(target)
    pref=Path(env["LOCALAPPDATA"])/"flyExplorer"
    pref.mkdir(parents=True,exist_ok=True)
    (pref/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=medium-icons\r\n")
    env["FLY_NETWORK_VISUAL_CAPTURE_PATH"]=str(shot)
    if args.force_network_detail:
        env["FLY_NETWORK_DETAIL_FORCE_TEST"]="YES"
    else:
        env.pop("FLY_NETWORK_DETAIL_FORCE_TEST",None)
    if args.force_removable_detail:
        env["FLY_REMOVABLE_DETAIL_FORCE_TEST"]="YES"
    else:
        env.pop("FLY_REMOVABLE_DETAIL_FORCE_TEST",None)

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
        until(ready,"network visual fixture window not ready",24)

        pane=parent.child_window(auto_id="LeftFiles")
        def row(name):
            matches=[x for x in pane.descendants()
                     if x.element_info.control_type=="ListItem" and
                        name in x.window_text()]
            return matches[0] if len(matches)==1 else None

        def image_named(item,label):
            if item is None:
                return False
            return any(v.element_info.control_type=="Image" and
                       label in (v.element_info.name or "") and
                       v.is_visible()
                       for v in item.descendants())

        until(lambda:row("image-owned.png") is not None and
                     row("note-owned.txt") is not None and
                     row("folder-owned") is not None,
              "network visual rows did not render",24)
        def retry_detail_once():
            view=parent.child_window(auto_id="ViewButton")
            assert view.exists(timeout=.5) and view.is_visible()
            view.invoke()
            large=Desktop(backend="uia").window(
                title="큰 아이콘",control_type="MenuItem")
            until(lambda:large.exists(timeout=.2),
                  "Large Icons menu item did not open",5)
            large.invoke()
            time.sleep(.4)
            view.invoke()
            medium=Desktop(backend="uia").window(
                title="보통 아이콘",control_type="MenuItem")
            until(lambda:medium.exists(timeout=.2),
                  "Medium Icons menu item did not open",5)
            medium.invoke()
            print("NETWORK_VISUAL_DETAIL_RETRY=VIEW_ROUNDTRIP",flush=True)

        try:
            until(lambda:image_named(row("image-owned.png"),
                                     "Windows Shell image thumbnail"),
                  "PNG Shell thumbnail did not render",10)
        except AssertionError:
            retry_detail_once()
            until(lambda:image_named(row("image-owned.png"),
                                     "Windows Shell image thumbnail"),
                  "PNG Shell thumbnail did not render after one view retry",20)
        until(lambda:image_named(row("note-owned.txt"),
                                 "Windows system registered file icon"),
              "TXT registered Shell icon did not render",24)
        until(lambda:image_named(row("folder-owned"),
                                 "Windows Shell folder icon"),
              "folder Shell icon did not render",24)
        until(lambda:"Windows 유형:" in row("note-owned.txt").window_text(),
              "Windows registered type label did not render",24)

        print("NETWORK_VISUAL_THUMBNAIL_PASS",True,flush=True)
        print("NETWORK_VISUAL_REGISTERED_ICON_PASS",True,flush=True)
        print("NETWORK_VISUAL_FOLDER_ICON_PASS",True,flush=True)
        print("NETWORK_VISUAL_TYPE_LABEL_PASS",True,flush=True)
        print("NETWORK_VISUAL_FORCED_NETWORK_PATH",
              args.force_network_detail,flush=True)
        print("NETWORK_VISUAL_FORCED_REMOVABLE_PATH",
              args.force_removable_detail,flush=True)

        until(lambda:shot.is_file() and shot.stat().st_size>4096,
              "app-owned XAML visual capture did not complete",12)
        with Image.open(shot) as captured:
            width,height=captured.size
            assert width>600 and height>400,(width,height)
            rgb=captured.convert("RGB").resize((96,52))
            sampled=list(rgb.getdata())
            nonblack=sum(1 for r,g,b in sampled if max(r,g,b)>=24)
            ratio=nonblack/len(sampled)
            print("NETWORK_VISUAL_NONBLACK_RATIO",f"{ratio:.4f}",flush=True)
            assert ratio>.08,("captured XAML visual is effectively black",ratio)
        print("NETWORK_VISUAL_WINDOW_RECT",width,height,flush=True)
        print("NETWORK_VISUAL_SCREENSHOT",shot.name,flush=True)
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
        print("NETWORK_VISUAL_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("NETWORK_VISUAL_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged:
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("NETWORK_VISUAL_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged else 1

if __name__=="__main__":
    raise SystemExit(main())
