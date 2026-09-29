"""Actual 1,100-file WinUI navigation/sort probe with disposable owner PID."""
from pathlib import Path
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
    parser.add_argument("--configuration",choices=("Debug","Release"),
                        default="Debug")
    args=parser.parse_args()
    if os.name!="nt":
        return 2
    here=Path(__file__).resolve().parent
    root=here.parents[1]
    exe=here/"x64"/args.configuration/"FlyExplorerWinUIShell"/"FlyExplorerWinUIShell.exe"
    assert exe.is_file(),"Exact owned WinUI build missing"
    existing=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((existing/name).read_bytes()).digest()
            for name in LEGACY if (existing/name).is_file()}
    base=root/"logs"/"m23"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="large-owned-",dir=base))
    folder=owned/"1100-files"
    folder.mkdir()
    for n in range(1100):
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
                     if "flyExplorer - WinUI 3" in x.window_text()]
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
              "1,100-file native Shell first row not rendered",28)
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
        until(lambda:"bench-1099.txt" in first_row(),
              "1,100-file name descending did not show the final owned file",20)
        assert (folder/"bench-0000.txt").read_text(encoding="utf-8").startswith(
            "test-owned")
        assert (folder/"bench-1099.txt").is_file()
        print("OWNED_1100_LARGE_FOLDER_FIRST_RENDER_SECONDS",
              round(first_elapsed,2),flush=True)
        print("OWNED_1100_NATIVE_NAVIGATION_AND_NAME_SORT",True,flush=True)
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
