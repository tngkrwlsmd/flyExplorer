"""Explicit opt-in one-time actual WinUI recycle + matching own-item restore.

Global Windows Recycle Bin must initially be empty; refuse to enumerate or
manipulate when another user's item is present. Creates and targets one
synthetic fixture only. On failure preserves the owned original folder for
manual recovery and prints no other Recycle Bin item information.
"""
from pathlib import Path
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
def eventually(predicate, label, seconds=16):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(.25)
    raise AssertionError(label)


def restore_verified_owned_item(item):
    # Shell FolderItem.InvokeVerb requires an exact Name from the supported
    # verb collection. Localized names differ across Windows languages.
    verbs=item.Verbs()
    choices=[]
    for idx in range(verbs.Count):
        verb=verbs.Item(idx)
        text=str(verb.Name)
        normalized=text.replace("&","").casefold()
        if "restore" in normalized or "복원" in normalized:
            choices.append(verb)
    if len(choices)!=1:
        raise AssertionError("Cannot identify one exact localized Restore verb")
    choices[0].DoIt()


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration",choices=("Debug","Release"),
                        default="Debug")
    parser.add_argument("--preflight",action="store_true")
    parser.add_argument("--apply-owned",action="store_true")
    args=parser.parse_args()
    if os.name!="nt":
        raise RuntimeError("Windows only")
    import win32com.client
    shell=win32com.client.Dispatch("Shell.Application")
    bin=shell.NameSpace(10)
    if bin is None:
        print("RECYCLE_BIN_UNAVAILABLE")
        return 2
    count=bin.Items().Count
    print("RECYCLE_BIN_INITIAL_ITEM_COUNT",count)
    if args.preflight:
        return 0 if count==0 else 2
    if not args.apply_owned:
        print("NO_MUTATION: require explicit --apply-owned for a disposable fixture")
        return 2
    if count:
        print("BLOCKED: occupied Recycle Bin. No enumeration, no mutation.")
        return 2
    here=Path(__file__).resolve().parent
    root=here.parents[1]
    exe=here/"x64"/args.configuration/"FlyExplorerWinUIShell"/"FlyExplorerWinUIShell.exe"
    assert exe.is_file(),"Expected exact built preview binary"
    base=root/"logs"/"m23"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="recycle-owned-",dir=base))
    src=owned/"left"
    src.mkdir()
    ident=uuid.uuid4().hex[:12]
    filename="휴지통-검증-"+ident+".txt"
    path=src/filename
    data=("owned recycle test "+ident).encode("utf-8")
    path.write_bytes(data)
    backup=owned/"backup.bin"
    backup.write_bytes(data)
    env=os.environ.copy()
    for name in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/name.lower()
        target.mkdir()
        env[name]=str(target)
    for flag in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
                 "FLY_M23_OWNED_DRAG_TRACE"):
        env.pop(flag,None)
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    original={n:hashlib.sha256((real/n).read_bytes()).digest()
              for n in LEGACY if (real/n).is_file()}
    print("TEST_OWNED_FOLDER",owned)
    from pywinauto import Desktop
    child=subprocess.Popen([str(exe),str(src)],cwd=exe.parent,env=env)
    matched=None
    did_recycle=False
    restored=False
    try:
        def ready():
            nonlocal matched
            if child.poll() is not None:
                return False
            windows=[w for w in Desktop(backend="uia").windows(process=child.pid)
                     if "flyExplorer - WinUI 3" in w.window_text()]
            if len(windows)!=1:
                return False
            import psutil
            if Path(psutil.Process(child.pid).exe()).resolve()!=exe.resolve():
                raise AssertionError("Preview PID points to unexpected executable")
            matched=Desktop(backend="uia").window(handle=windows[0].handle)
            return matched.child_window(auto_id="LeftFiles").exists(timeout=.2)
        eventually(ready,"Owned preview never reached its own file list")
        def row():
            return next((i for i in matched.child_window(
                auto_id="LeftFiles").descendants()
                if i.element_info.control_type=="ListItem"
                and filename in i.window_text()),None)
        eventually(lambda:row() is not None,"Owned synthetic file missing in UI")
        assert bin.Items().Count==0,"Another Recycle Bin item appeared; abort"
        row().select()
        eventually(lambda:row() is not None and row().is_selected(),
                   "Synthetic item was not selected")
        matched.child_window(auto_id="RecycleButton").click_input()
        confirm=matched.child_window(title="휴지통으로 보내기",
                                     control_type="Button")
        eventually(lambda:confirm.exists(timeout=.3),
                   "Actual WinUI recycle confirmation missing")
        confirm.click_input()
        eventually(lambda:not path.exists() and bin.Items().Count==1,
                   "Synthetic file did not move to an exclusively owned Recycle Bin")
        did_recycle=True
        item=bin.Items().Item(0)
        assert item.Name in (filename,path.stem),(
            "Unexpected Recycle Bin item; stop without mutation")
        assert Path(str(item.ExtendedProperty(
            "System.Recycle.DeletedFrom"))).resolve()==src.resolve(),(
            "Unexpected original folder; refuse to restore")
        print("OWNED_ACTUAL_RECYCLE_CONFIRMED",True)
        restore_verified_owned_item(item)
        eventually(lambda:path.is_file() and path.read_bytes()==data and
                   bin.Items().Count==0,
                   "Owned item restore did not complete",
                   seconds=18)
        restored=True
        print("OWNED_ACTUAL_RECYCLE_RESTORE_CONFIRMED",True)
    finally:
        if did_recycle and not restored:
            # Before any further mutation, only attempt to restore the
            # uniquely created item if we can prove Bin contains only it.
            try:
                if bin.Items().Count==1:
                    ours=bin.Items().Item(0)
                    if (ours.Name in (filename,path.stem) and
                        Path(str(ours.ExtendedProperty(
                            "System.Recycle.DeletedFrom"))).resolve()==src.resolve()):
                        restore_verified_owned_item(ours)
                        eventually(lambda:path.is_file() and
                                   path.read_bytes()==data and
                                   bin.Items().Count==0,
                                   "Recovery restore not confirmed",8)
                        restored=True
                        print("RECOVERY_RESTORE_CONFIRMED",True)
            except Exception as err:
                print("RECOVERY_REQUIRES_HUMAN",
                      type(err).__name__,"OWNED_FIXTURE",path)
        if child.poll() is None:
            try:
                import ctypes as c
                from ctypes import wintypes as w
                owner=w.DWORD()
                u=c.windll.user32
                u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
                if matched is not None and u.GetWindowThreadProcessId(
                        matched.handle,c.byref(owner)) and owner.value==child.pid:
                    u.PostMessageW(matched.handle,0x10,0,0)
                    child.wait(timeout=12)
                else:
                    child.terminate()
                    child.wait(timeout=8)
            except Exception:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=8)
        unchanged=all((real/n).is_file() and hashlib.sha256(
                    (real/n).read_bytes()).digest()==digest
                    for n,digest in original.items())
        print("LEGACY_PRESENT_SETTINGS_UNCHANGED",unchanged)
        if restored and unchanged:
            shutil.rmtree(owned)
        else:
            print("OWNED_FIXTURE_RETAINED_FOR_RECOVERY",owned)
    return 0 if did_recycle and restored and unchanged else 1


if __name__=="__main__":
    sys.exit(run())
