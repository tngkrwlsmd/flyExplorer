"""Actual bounded large-folder WinUI navigation/sort probe with disposable owner PID."""
from pathlib import Path
from paths import ROOT, APP, app_exe
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time


LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf",
        "fxfile-folder_layout.conf")


def until(fn,label,timeout):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if fn():
            return
        time.sleep(.4)
    raise AssertionError(label)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--items",type=int,choices=(1100,2300,5000,8000),default=1100)
    parser.add_argument("--configuration",choices=("Debug","Release"),
                        default="Debug")
    args=parser.parse_args()
    if os.name!="nt":
        return 2
    here=APP
    root=ROOT
    exe=app_exe(args.configuration)
    assert exe.is_file(),"Exact owned WinUI build missing"
    existing=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((existing/name).read_bytes()).digest()
            for name in LEGACY if (existing/name).is_file()}
    base=root/"logs"/"m23"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="large-owned-",dir=base))
    folder=owned/(str(args.items)+"-files")
    folder.mkdir()
    for n in range(args.items):
        (folder/f"bench-{n:04d}.txt").write_text(
            f"test-owned file {n}\n",encoding="utf-8")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        value=owned/key.lower()
        value.mkdir()
        env[key]=str(value)
    for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
                "FLY_M22_OWNED_ACTUAL_RECYCLE"):
        env.pop(key,None)
    from pywinauto import Desktop
    import psutil
    import ctypes as c
    from ctypes import wintypes as w
    started=time.monotonic()
    process=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    parent=None
    success=False
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:
                return False
            if Path(psutil.Process(process.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("Owned PID executable mismatch")
            windows=[x for x in Desktop(backend="uia").windows(process=process.pid)
                     if "flyExplorer" in x.window_text()]
            if len(windows)!=1:
                return False
            parent=Desktop(backend="uia").window(handle=windows[0].handle)
            return parent.child_window(auto_id="LeftFiles").exists(timeout=.25)
        until(ready,"Owner preview window not ready",20)
        def first_row():
            matches=[v for v in parent.child_window(
               auto_id="LeftFiles").descendants()
               if v.element_info.control_type=="ListItem"]
            return matches[0].window_text() if matches else ""
        until(lambda:"bench-0000.txt" in first_row(),
              "large-folder native Shell first row not rendered",
              48 if args.items>=8000 else 28)
        first_elapsed=time.monotonic()-started
        # Focus only an exact newly created GUI window and verify PID.
        parent.set_focus()
        ui=c.windll.user32
        owner=w.DWORD()
        ui.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
        assert ui.GetWindowThreadProcessId(parent.handle,c.byref(owner))
        assert owner.value==process.pid
        assert ui.GetForegroundWindow()==parent.handle
        parent.child_window(auto_id="SortPicker").select(1)
        until(lambda:f"bench-{args.items-1:04d}.txt" in first_row(),
              "large-folder name descending did not show the final owned file",20)
        if args.items>=2300:
            more=parent.child_window(auto_id="LeftLoadMoreButton")
            until(lambda:more.exists(timeout=.2) and
                  f"160/{args.items}" in more.window_text(),
                  "large native entries were not view-paged",8)
            more.click_input()
            until(lambda:f"320/{args.items}" in parent.child_window(
                  auto_id="LeftLoadMoreButton").window_text(),
                  "controlled extra page did not render",12)
        if args.items==2300:
            from pywinauto import keyboard
            filt=parent.child_window(auto_id="LeftNameFilterBox")
            assert filt.exists(timeout=.2)
            filt.set_edit_text("2299")
            until(lambda:"bench-2299.txt" in first_row() and
                  (not parent.child_window(
                       auto_id="LeftLoadMoreButton").exists(timeout=.1) or
                   not parent.child_window(
                       auto_id="LeftLoadMoreButton").is_visible()),
                  "native file-name filter must not mutate model or page",9)
            filt.set_edit_text("")
            until(lambda:"bench-2299.txt" in first_row(),
                  "clearing pane filter failed to restore sorted native snapshot",10)
            files=parent.child_window(auto_id="LeftFiles")
            files.set_focus()
            keyboard.send_keys("^+f")
            until(lambda:filt.has_keyboard_focus(),
                  "Ctrl+Shift+F did not focus the owned pane name filter",5)
            print("OWNED_LARGE_CTRL_SHIFT_F_FILTER_FOCUS",True,flush=True)
            print("OWNED_LARGE_PROGRESSIVE_PAGE_FILTER_RESET",True,flush=True)
        assert (folder/"bench-0000.txt").read_text(encoding="utf-8").startswith(
            "test-owned")
        assert (folder/"bench-1099.txt").is_file()
        assert (folder/f"bench-{args.items-1:04d}.txt").is_file()
        print("OWNED_LARGE_FOLDER_ITEM_COUNT",args.items,flush=True)
        print("OWNED_LARGE_FOLDER_FIRST_RENDER_SECONDS",
              round(first_elapsed,2),flush=True)
        print("OWNED_LARGE_FOLDER_NAVIGATION_AND_NAME_SORT",True,flush=True)
        if args.items>=8000:
            print("OWNED_LARGE_FOLDER_OVER_6000_PAGED_TRANSPORT",True,flush=True)
        success=True
    finally:
        if process.poll() is None:
            import psutil
            if Path(psutil.Process(process.pid).exe()).resolve()==exe.resolve():
                try:
                    if parent is not None:
                        c.windll.user32.PostMessageW(parent.handle,0x10,0,0)
                        process.wait(timeout=12)
                    else:
                        raise RuntimeError("No matching owned HWND")
                except Exception:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=8)
        unchanged=all((existing/name).is_file() and
           hashlib.sha256((existing/name).read_bytes()).digest()==digest
           for name,digest in hashes.items())
        print("LEGACY_PRESENT_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success and unchanged:
            shutil.rmtree(owned)
        else:
            print("OWNED_EVIDENCE_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged else 1


if __name__=="__main__":
    sys.exit(main())
