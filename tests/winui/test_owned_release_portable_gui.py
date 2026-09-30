"""Test-owned local Release output copy + launch (NOT installer certification)."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time


LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
def until(f,label,seconds=22):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if f():
            return
        time.sleep(.4)
    raise AssertionError(label)


def main():
    if os.name!="nt":
        return 2
    here=Path(__file__).resolve().parents[2]/"app"/"winui"
    root=here.parents[1]
    release=here/"x64"/"Release"/"FlyExplorerWinUIShell"
    expected=("FlyExplorerWinUIShell.exe","FlyShellIsolationHelper.exe",
              "FlyExplorerWinUIShell.pri","MainWindow.xbf")
    assert all((release/name).is_file() for name in expected)
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    before={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}
    base=root/"logs"/"m23"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="portable-owned-",dir=base))
    package=owned/"preview-copy"
    package.mkdir()
    copied=[]
    for file in release.iterdir():
        assert not file.is_symlink(),"Linked content is never packaged"
        if file.is_dir():
            # Real MSBuild Release output includes a required XAML Assets
            # directory. Copy only this exact known subtree, not arbitrary
            # directories, links, or intermediate build output.
            assert file.name=="Assets","Unexpected Release output directory"
            for base,dirs,files in os.walk(file,followlinks=False):
                for entry in dirs+files:
                    candidate=Path(base)/entry
                    assert not candidate.is_symlink() and not (
                        hasattr(candidate,"is_junction") and
                        candidate.is_junction()),"Linked packaged asset"
                for name in files:
                    src=Path(base)/name
                    rel=src.relative_to(file)
                    dst=package/"Assets"/rel
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(src,dst)
                    assert hashlib.sha256(dst.read_bytes()).digest()==(
                           hashlib.sha256(src.read_bytes()).digest())
                    copied.append(str(Path("Assets")/rel))
            continue
        assert file.is_file(),"Unexpected Release output item"
        if file.suffix.lower() in (".pdb",".lib",".exp"):
            continue
        dest=package/file.name
        shutil.copy2(file,dest)
        assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(
            file.read_bytes()).digest()
        copied.append(file.name)
    assert all((package/name).is_file() for name in expected)
    assert len(copied)>=10,"Incomplete copied preview runtime/resources"
    folder=owned/"source"
    folder.mkdir()
    marker=folder/"portable-owned.txt"
    marker.write_text("disposable portable preview",encoding="utf-8")
    env=os.environ.copy()
    for name in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        dest=owned/name.lower()
        dest.mkdir()
        env[name]=str(dest)
    for name in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST",
                 "FLY_M22_OWNED_ACTUAL_RECYCLE"):
        env.pop(name,None)
    exe=package/"FlyExplorerWinUIShell.exe"
    import psutil
    from pywinauto import Desktop
    child=subprocess.Popen([str(exe),str(folder)],cwd=package,env=env)
    window=None
    passed=False
    try:
        def loaded():
            nonlocal window
            if child.poll() is not None:
                return False
            if Path(psutil.Process(child.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("Owned Release preview PID mismatch")
            matches=[x for x in Desktop(backend="uia").windows(
                process=child.pid) if "flyExplorer - WinUI 3" in x.window_text()]
            if len(matches)!=1:
                return False
            window=Desktop(backend="uia").window(handle=matches[0].handle)
            return window.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(loaded,"Copied Release GUI failed to start",20)
        def content():
            return [x.window_text() for x in window.child_window(
                auto_id="LeftFiles").descendants()
                if x.element_info.control_type=="ListItem"]
        until(lambda:any("portable-owned.txt" in s and "Windows "+chr(0xC720)+chr(0xD615)+":" in s
                         for s in content()),
              "Copied Release lacks isolated helper/OS type or owned file list",
              seconds=24)
        print("RELEASE_PORTABLE_COPIED_FILES",len(copied),flush=True)
        print("RELEASE_PORTABLE_OWNED_FILE_AND_REGISTERED_TYPE",True,flush=True)
        passed=True
    finally:
        if child.poll() is None:
            if Path(psutil.Process(child.pid).exe()).resolve()==exe.resolve():
                try:
                    from ctypes import windll
                    if window is not None:
                        assert windll.user32.PostMessageW(
                            window.handle,0x10,0,0)
                        child.wait(timeout=10)
                    else:raise RuntimeError("Owned WinUI HWND unavailable")
                except Exception:
                    if child.poll() is None:
                        child.terminate()
                        child.wait(timeout=8)
        unchanged=all((real/name).is_file() and
           hashlib.sha256((real/name).read_bytes()).digest()==digest
           for name,digest in before.items())
        print("LEGACY_PRESENT_SETTINGS_UNCHANGED",unchanged,flush=True)
        if passed and unchanged:
            shutil.rmtree(owned)
        else:
            print("PORTABLE_PREVIEW_FIXTURE_RETAINED_FOR_DEBUG",owned,flush=True)
    return 0 if passed and unchanged else 1


if __name__=="__main__":
    sys.exit(main())
