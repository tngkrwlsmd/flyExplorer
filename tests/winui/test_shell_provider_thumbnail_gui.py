"""Matched virtual Shell/provider thumbnail acceptance through Pictures Library."""
import argparse
import ctypes as c
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image,ImageDraw
from pywinauto import Desktop

from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
OWNED_NAME="flyExplorer-provider-thumbnail-owned.png"

def until(fn,label,timeout=28):
    return wait_until(fn,label,seconds=timeout,interval=.25)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--capture",choices=("before","after"),required=True)
    parser.add_argument("--expect-provider-thumbnail",action="store_true")
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
    owned_image=pictures/OWNED_NAME
    assert not owned_image.exists(),owned_image
    image=Image.new("RGBA",(160,112),(34,95,176,255))
    draw=ImageDraw.Draw(image)
    draw.rectangle((80,0,159,111),fill=(224,115,30,255))
    draw.ellipse((48,24,112,88),fill=(45,163,99,255))
    image.save(owned_image)

    evidence=ROOT/"logs"/"shell-provider-thumbnail"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="shell-provider-thumbnail-owned-",dir=evidence))
    shot=evidence/f"shell-provider-thumbnail-{args.capture}.bmp"
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
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=large-icons\r\n")
    env["FLY_SHELL_PROVIDER_VISUAL_CAPTURE_PATH"]=str(shot)

    process=subprocess.Popen([str(exe),"shell:PicturesLibrary"],cwd=exe.parent,env=env)
    parent=None
    success=False
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
            return parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(ready,"provider thumbnail fixture window not ready",24)

        pane=parent.child_window(auto_id="LeftFiles")
        address=parent.child_window(auto_id="AddressBox")
        until(lambda:"Pictures.library-ms" in address.get_value() or
                     address.get_value() in ("그림","사진"),
              "Pictures Library virtual root did not open",20)

        def rows():
            return [x for x in pane.descendants()
                    if x.element_info.control_type=="ListItem"]
        def target():
            matches=[x for x in rows() if OWNED_NAME in x.window_text()]
            return matches[0] if len(matches)==1 else None
        def images_named(label):
            item=target()
            if item is None:
                return []
            return [v for v in item.descendants()
                    if v.element_info.control_type=="Image" and
                       label in (v.element_info.name or "") and v.is_visible()]

        until(lambda:target() is not None,
              "owned image did not appear in Pictures Library",24)
        until(lambda:images_named("Windows system registered file icon") or
                     images_named("Windows Shell image thumbnail"),
              "provider image never received Shell visual detail",20)

        if args.expect_provider_thumbnail:
            until(lambda:len(images_named("Windows Shell image thumbnail"))==1,
                  "provider image thumbnail did not render",20)
            print("SHELL_PROVIDER_THUMBNAIL_PASS",True,flush=True)
        else:
            assert not images_named("Windows Shell image thumbnail")
            print("SHELL_PROVIDER_THUMBNAIL_BASELINE_NO_THUMBNAIL",True,flush=True)

        print("SHELL_PROVIDER_THUMBNAIL_ROW",repr(target().window_text()),flush=True)
        print("SHELL_PROVIDER_THUMBNAIL_VISUALS",
              repr([(v.element_info.control_type,v.element_info.name or "")
                    for v in target().descendants()]),flush=True)

        until(lambda:shot.is_file() and shot.stat().st_size>4096,
              "app-owned provider thumbnail capture did not complete",12)
        with Image.open(shot) as captured:
            width,height=captured.size
            assert width>600 and height>400,(width,height)
            sampled=list(captured.convert("RGB").resize((96,52)).getdata())
            ratio=sum(1 for r,g,b in sampled if max(r,g,b)>=24)/len(sampled)
            print("SHELL_PROVIDER_THUMBNAIL_NONBLACK_RATIO",f"{ratio:.4f}",flush=True)
            assert ratio>.08,("captured XAML visual is effectively black",ratio)
        print("SHELL_PROVIDER_THUMBNAIL_WINDOW_RECT",width,height,flush=True)
        print("SHELL_PROVIDER_THUMBNAIL_SCREENSHOT",shot.name,flush=True)
        success=True
    finally:
        if process.poll() is None:
            try:
                c.windll.user32.PostMessageW(parent.handle if parent else 0,0x10,0,0)
                process.wait(timeout=12)
            except Exception:
                process.terminate()
                process.wait(timeout=8)
        owned_image.unlink(missing_ok=True)
        unchanged=all((real/name).is_file() and
            hashlib.sha256((real/name).read_bytes()).digest()==digest
            for name,digest in hashes.items())
        print("SHELL_PROVIDER_THUMBNAIL_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        print("SHELL_PROVIDER_THUMBNAIL_OWNED_IMAGE_REMOVED",
              not owned_image.exists(),flush=True)
        if success:
            assert process.returncode==0,process.returncode
            print("SHELL_PROVIDER_THUMBNAIL_PROCESS_EXIT",process.returncode,flush=True)
        if success and unchanged and not owned_image.exists():
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("SHELL_PROVIDER_THUMBNAIL_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged and not owned_image.exists() else 1

if __name__=="__main__":
    raise SystemExit(main())
