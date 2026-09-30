"""Opt-in human WinUI/Windows Explorer clipboard integration.

No automatic clipboard mutations: requires initially EMPTY global clipboard,
opens only a fresh test-owned WinUI preview plus a synthetic Explorer folder,
and verifies only disposable fixture files after the human finishes.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import os
from pathlib import Path
from paths import ROOT, APP, app_exe
import subprocess
import sys
import tempfile


NAMES=("flyExplorer.conf","flyExplorer-main.conf")
LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf",
        "fxfile-folder_layout.conf")


def clipboard_empty():
    user=c.windll.user32
    user.OpenClipboard.argtypes=(w.HWND,)
    user.OpenClipboard.restype=w.BOOL
    user.EnumClipboardFormats.argtypes=(w.UINT,)
    user.EnumClipboardFormats.restype=w.UINT
    if not user.OpenClipboard(None):
        print("BLOCKED: global clipboard is unavailable")
        return False
    try:
        # Only enumerate formats; never inspect, serialize or log user data.
        count=0
        current=0
        while True:
            current=user.EnumClipboardFormats(current)
            if not current:
                break
            count+=1
            if count>256:break
        print("EXISTING_CLIPBOARD_FORMAT_COUNT",count)
        return count==0
    finally:
        user.CloseClipboard()


def main():
    if os.name!="nt" or not sys.stdin.isatty():
        print("BLOCKED: human interactive Windows console required.")
        return 2
    if not clipboard_empty():
        print("BLOCKED: user clipboard is populated or inaccessible.")
        print("Do not clear your existing clipboard merely for automation.")
        return 2
    here=APP
    exe=app_exe("Debug")
    if not exe.is_file():
        print("BLOCKED: build the Debug preview first.")
        return 2
    legacy=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    original={n:hashlib.sha256((legacy/n).read_bytes()).digest()
              for n in LEGACY if (legacy/n).is_file()}
    root=ROOT/"logs"/"m23"
    root.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="clipboard-owned-",dir=root))
    left,right=owned/"left",owned/"right"
    left.mkdir()
    right.mkdir()
    files={
        left/"윈UI-복사.txt":"WinUI to Explorer copy",
        left/"윈UI-잘라.txt":"WinUI to Explorer cut",
        right/"탐색기-복사.txt":"Explorer to WinUI copy",
        right/"탐색기-잘라.txt":"Explorer to WinUI cut",
    }
    for path,data in files.items():path.write_text(data,encoding="utf-8")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        value=owned/key.lower()
        value.mkdir()
        env[key]=str(value)
    for key in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST",
                "FLY_M23_OWNED_DRAG_TRACE"):
        env.pop(key,None)
    preview=subprocess.Popen([str(exe),str(left)],cwd=exe.parent,env=env)
    # A new synthetic folder may reuse the Explorer shell process. Never
    # terminate or manipulate unrelated windows.
    subprocess.Popen(["explorer.exe",str(right)],
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print("OWNED_PREVIEW_PID",preview.pid)
    print("WINUI_SOURCE",left)
    print("EXPLORER_TARGET",right)
    print("TEST 1: WinUI select 윈UI-복사.txt and Windows Copy; Explorer Paste.")
    print("TEST 2: Explorer Copy 탐색기-복사.txt; WinUI Windows Paste.")
    print("TEST 3: WinUI select 윈UI-잘라.txt and Windows Cut; Explorer Paste.")
    print("TEST 4: Explorer Cut 탐색기-잘라.txt; WinUI Windows Paste.")
    print("Perform each step only on these generated fixture files.")
    print("Close ONLY the preview that this script launched when finished.")
    try:
        input("Press Enter after the four steps and preview exit: ")
    except (KeyboardInterrupt,EOFError):
        print("ABORTED: leave the fixture directory for manual inspection.")
        return 2
    if preview.poll() is None:
        print("INCOMPLETE: owned preview is still running. Close it first.")
        return 2
    checks={
        "winui_copy_to_explorer":(left/"윈UI-복사.txt").is_file() and
             (right/"윈UI-복사.txt").is_file() and
             (right/"윈UI-복사.txt").read_text(encoding="utf-8")==files[left/"윈UI-복사.txt"],
        "explorer_copy_to_winui":(right/"탐색기-복사.txt").is_file() and
             (left/"탐색기-복사.txt").is_file() and
             (left/"탐색기-복사.txt").read_text(encoding="utf-8")==files[right/"탐색기-복사.txt"],
        "winui_cut_to_explorer":not (left/"윈UI-잘라.txt").exists() and
             (right/"윈UI-잘라.txt").is_file() and
             (right/"윈UI-잘라.txt").read_text(encoding="utf-8")==files[left/"윈UI-잘라.txt"],
        "explorer_cut_to_winui":not (right/"탐색기-잘라.txt").exists() and
             (left/"탐색기-잘라.txt").is_file() and
             (left/"탐색기-잘라.txt").read_text(encoding="utf-8")==files[right/"탐색기-잘라.txt"],
    }
    legacy_unchanged=all((legacy/n).is_file() and
       hashlib.sha256((legacy/n).read_bytes()).digest()==digest
       for n,digest in original.items())
    print("OWNED_INTEROP_RESULTS",checks)
    print("LEGACY_PRESENT_SETTINGS_UNCHANGED",legacy_unchanged)
    print("EVIDENCE_FIXTURES",owned)
    print("Global clipboard was never altered by this script; your manual")
    print("copy/cut actions may leave owned fixture paths on the clipboard.")
    return 0 if all(checks.values()) and legacy_unchanged else 1


if __name__=="__main__":
    sys.exit(main())
