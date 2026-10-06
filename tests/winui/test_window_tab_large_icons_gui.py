"""Focused GUI acceptance for Large Icons default on newly created Window Tabs."""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
import argparse
import os
import shutil
import subprocess
import tempfile
import time
from PIL import ImageGrab


def until(fn,label,timeout=25):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if fn():
            return
        time.sleep(.3)
    raise AssertionError(label)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--exe",type=Path)
    parser.add_argument("--expect",choices=("medium","large"),required=True)
    parser.add_argument("--capture",choices=("before","after"),required=True)
    args=parser.parse_args()
    if os.name!="nt":
        return 2

    exe=(args.exe if args.exe else app_exe(args.configuration)).resolve()
    assert exe.is_file(),exe
    real,before=snapshot_legacy_profile()
    evidence=ROOT/"logs"/"window-tab-large-icons"
    evidence.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="window-tab-large-icons-owned-",dir=evidence))
    folder=owned/"fixture"
    folder.mkdir()
    for i in range(8):
        (folder/f"item-{i}.txt").write_text(f"item-{i}",encoding="utf-8")

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower()
        target.mkdir()
        env[key]=str(target)
    profile=Path(env["LOCALAPPDATA"])/"flyExplorer"
    profile.mkdir()
    (profile/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=large-icons\r\n")
    for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
                "FLY_M22_OWNED_ACTUAL_RECYCLE","FLY_METADATA_SORT_OWNED_TEST"):
        env.pop(key,None)

    from pywinauto import Desktop
    from pywinauto.keyboard import send_keys
    import psutil

    process=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    parent=None
    success=False
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:
                return False
            if Path(psutil.Process(process.pid).exe()).resolve()!=exe:
                raise AssertionError("foreign executable owns focused PID")
            wins=[w for w in Desktop(backend="uia").windows(process=process.pid)
                  if "flyExplorer" in w.window_text()]
            if len(wins)!=1:
                return False
            parent=Desktop(backend="uia").window(handle=wins[0].handle)
            return parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(ready,"flyExplorer window not ready",25)

        def tabs():
            strip=parent.child_window(auto_id="WindowTabStrip")
            return [x for x in strip.descendants()
                    if x.element_info.control_type=="TabItem"]

        def rows():
            view=parent.child_window(auto_id="LeftFiles")
            return [x for x in view.descendants()
                    if x.element_info.control_type=="ListItem" and x.is_visible()]

        until(lambda:len(tabs())==1 and len(rows())>=1,
              "initial Large Icons fixture did not render",25)
        initial=rows()[0].rectangle()
        print("WINDOW_TAB_INITIAL_ROW_SIZE",initial.width(),initial.height(),flush=True)
        assert initial.width()>=105 and initial.height()>=115,(
            "initial preference did not render Large Icons",initial)

        parent.set_focus()
        send_keys("^t")
        until(lambda:len(tabs())==2,"Ctrl+T did not create Window Tab",12)
        until(lambda:len(rows())>=1,"new Window Tab rows did not render",25)
        rect=rows()[0].rectangle()
        width,height=rect.width(),rect.height()
        print("WINDOW_TAB_NEW_ROW_SIZE",width,height,flush=True)

        if args.expect=="large":
            assert width>=105 and height>=115,(
                "new Window Tab lost Large Icons default",width,height)
            print("WINDOW_TAB_LARGE_ICONS_DEFAULT_PRESERVED",True,flush=True)
        else:
            assert width<105 and height<115,(
                "baseline no longer reproduces Medium clamp",width,height)
            print("WINDOW_TAB_LEGACY_MEDIUM_CLAMP_REPRODUCED",True,flush=True)

        try:
            parent.set_focus()
        except Exception:
            pass
        box=parent.rectangle()
        shot=evidence/f"window-tab-large-icons-{args.capture}.png"
        ImageGrab.grab(bbox=(box.left,box.top,box.right,box.bottom)).save(shot)
        print("WINDOW_TAB_VISUAL",shot.name,flush=True)
        success=True
    finally:
        if process.poll() is None:
            try:
                import ctypes
                ctypes.windll.user32.PostMessageW(parent.handle if parent else 0,0x10,0,0)
                process.wait(timeout=15)
            except Exception:
                process.terminate()
                process.wait(timeout=10)
        assert process.returncode==0,process.returncode
        assert_legacy_profile_unchanged(real,before)
        if success:
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("WINDOW_TAB_FIXTURE_RETAINED",owned,flush=True)

    return 0


if __name__=="__main__":
    raise SystemExit(main())
