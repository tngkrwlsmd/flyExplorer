"""Focused indexed filename search GUI: actual SystemIndex and bounded UI."""
import argparse
import ctypes
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from pywinauto import Desktop
from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
NAME="Microsoft Edge.lnk"
TERM="Microsoft Edge"

def wait(fn,label,seconds=25):
    return wait_until(fn,label,seconds=seconds,interval=.3)

# Test-owned visual captures need identical Win32 frame sizes. The app's
# EnsureExpandedPanelFits uses monitor work area and launch position, so
# independent launches otherwise produce unequal screenshots despite the
# same UI controls. This thread touches only the PID launched by this test.
def enforce_owned_capture_size(proc,shot,stop,observed):
    width,height=972,720
    user32=ctypes.WinDLL("user32",use_last_error=True)
    class RECT(ctypes.Structure):
        _fields_=[("left",ctypes.c_long),("top",ctypes.c_long),
                  ("right",ctypes.c_long),("bottom",ctypes.c_long)]
    proc_type=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    user32.EnumWindows.argtypes=[proc_type,ctypes.c_void_p]
    user32.GetWindowThreadProcessId.argtypes=[ctypes.c_void_p,
                                                ctypes.POINTER(ctypes.c_ulong)]
    user32.GetWindowTextW.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_int]
    user32.GetWindowRect.argtypes=[ctypes.c_void_p,ctypes.POINTER(RECT)]
    user32.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,
                                   ctypes.c_int,ctypes.c_int,ctypes.c_int,
                                   ctypes.c_int,ctypes.c_uint]
    user32.IsWindowVisible.argtypes=[ctypes.c_void_p]
    def visit(hwnd,_):
        owner=ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value!=proc.pid or not user32.IsWindowVisible(hwnd):
            return True
        title=ctypes.create_unicode_buffer(128)
        user32.GetWindowTextW(hwnd,title,len(title))
        if "flyExplorer" not in title.value:
            return True
        rect=RECT()
        if not user32.GetWindowRect(hwnd,ctypes.byref(rect)):
            return True
        extent=(rect.right-rect.left,rect.bottom-rect.top)
        if extent!=(width,height):
            # SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE. No global
            # display, DPI, focus or user window state is modified.
            if user32.SetWindowPos(hwnd,None,0,0,width,height,0x16):
                observed["resized"]=True
        else:
            observed["fixed"]=True
        return True
    callback=proc_type(visit)
    while not stop.is_set() and proc.poll() is None and not shot.is_file():
        user32.EnumWindows(callback,None)
        stop.wait(.025)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--capture",choices=("before","after"),default="after")
    args=parser.parse_args()
    # The controlled BEFORE capture uses the unchanged main product binary,
    # while the AFTER capture uses the candidate binary. Both are driven by
    # this same test-owned fixture and the same UIA/capture path.
    visual_exe=os.environ.get("FLY_INDEXED_SEARCH_VISUAL_EXE","")
    exe=(Path(visual_exe) if visual_exe else app_exe(args.configuration)).resolve()
    assert exe.is_file(),exe
    # The VM's Pictures scope is not indexed. Use the confirmed built-in
    # Public Desktop scope without modifying any indexed/system file.
    scope=Path(os.environ["PUBLIC"])/"Desktop"
    assert scope.is_dir(),scope
    fixture=scope/NAME
    assert fixture.is_file(),"expected pre-indexed public shortcut missing"
    source_hash=hashlib.sha256(fixture.read_bytes()).digest()
    real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    before={name:hashlib.sha256((real/name).read_bytes()).digest()
            for name in LEGACY if (real/name).is_file()}
    base=ROOT/"logs"/"search-v3-indexed"
    base.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="indexed-search-owned-",dir=base))
    view=owned/"display-folder"
    view.mkdir()
    (view/"owned-visible-row.txt").write_text(
        "test-owned visual fixture\n",encoding="utf-8")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        p=owned/key.lower()
        p.mkdir()
        env[key]=str(p)
    prefs=Path(env["LOCALAPPDATA"])/"flyExplorer"
    prefs.mkdir(parents=True,exist_ok=True)
    (prefs/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
    shot=base/("indexed-search-"+args.capture+".bmp")
    shot.unlink(missing_ok=True)
    env["FLY_CONTENT_REGEX_VISUAL_CAPTURE_PATH"]=str(shot)
    proc=None
    window=None
    success=False
    geometry_stop=threading.Event()
    geometry_thread=None
    geometry_observed={"fixed":False,"resized":False}
    try:
        proc=subprocess.Popen([str(exe),str(view)],
                              cwd=exe.parent,env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        geometry_thread=threading.Thread(
            target=enforce_owned_capture_size,
            args=(proc,shot,geometry_stop,geometry_observed),daemon=True)
        geometry_thread.start()
        def ready():
            nonlocal window
            if proc.poll() is not None:return False
            matches=[w for w in Desktop(backend="uia").windows(process=proc.pid)
                     if "flyExplorer" in w.window_text()]
            if len(matches)!=1:return False
            window=Desktop(backend="uia").window(handle=matches[0].handle)
            return window.child_window(auto_id="SearchPanelButton").exists(timeout=.2)
        wait(ready,"indexed search window",24)
        reported=set()
        def control(auto_id):
            # WinUI 3 can duplicate the same physical XAML control in the
            # accessibility tree. A unique visible geometry/type identifies
            # the same owned control, never a different hidden pane/window.
            nodes=[
                w for w in window.descendants()
                if w.element_info.automation_id==auto_id and w.is_visible()
            ]
            shapes={(w.element_info.control_type,str(w.rectangle()))
                    for w in nodes}
            if auto_id not in reported and len(nodes)!=1:
                print("INDEXED_SEARCH_UIA_DUPLICATE",auto_id,len(nodes),
                      repr(sorted(shapes)),flush=True)
                reported.add(auto_id)
            assert nodes and len(shapes)==1,(
                "ambiguous visible XAML search control",auto_id,
                len(nodes),repr(sorted(shapes)))
            return nodes[0]
        # The owned XAML capture hook already opens SearchPanel at startup.
        # A returned wrapper exposes is_visible(), not exists().
        panel=control("SearchTermBox")
        assert panel.is_visible(),"owned search panel did not open"
        control("SearchScopeBox").set_edit_text(str(scope))
        panel.set_edit_text(TERM)
        if args.capture=="after":
            mode=control("SearchModeBox")
            assert mode.is_visible(),"Windows index selector missing"
            mode.select(1)
            # Modified-date remains unsupported. Size bounds are now a
            # valid indexed criterion and are tested below.
            unsupported=control("SearchModifiedAfterBox")
            unsupported.set_edit_text("2026-01-01")
            control("SearchRunButton").invoke()
            wait(lambda:"인덱스 검색은 파일명·확장자·크기 조건만 지원" in
                control("SearchCountText").window_text(),
                "indexed-only date did not reject before worker start",6)
            unsupported.set_edit_text("")
            minimum=control("SearchMinSizeBox")
            minimum.set_edit_text("1x")
            control("SearchRunButton").invoke()
            wait(lambda:"파일 크기 범위가 올바르지 않습니다" in
                control("SearchCountText").window_text(),
                "indexed malformed size did not reject before worker start",6)
            minimum.set_edit_text("")
            print("INDEXED_SEARCH_UNSUPPORTED_AND_INVALID_SIZE_PRESTART_REJECT_PASS",True,flush=True)
        else:
            # main already includes Search v3's source selector. The change
            # under comparison is the indexed-mode extension hint, not
            # introduction of the selector itself.
            assert control("SearchModeBox").is_visible(),(
                "baseline Windows index source selector missing")
        # App-owned RenderTargetBitmap capture; service desktops can reject
        # pywinauto/PIL screen grabbing even when UIA works.
        wait(lambda:shot.is_file() and shot.stat().st_size>4096,
             "app-owned indexed search capture did not materialize",12)
        geometry_stop.set()
        geometry_thread.join(timeout=2)
        assert geometry_observed["fixed"],(
            "test-owned window was not observed at fixed 972x720",
            geometry_observed)
        print("INDEXED_SEARCH_OWNED_FIXED_FRAME_972x720_PASS",True,flush=True)
        print("INDEXED_SEARCH_CAPTURE",shot.name,flush=True)
        print("INDEXED_SEARCH_CAPTURE_REVISION_EXE",str(exe),flush=True)

        if args.capture=="after":
            # Positive oracle: this public system shortcut was independently
            # confirmed in the actual SystemIndex, with no test-created file
            # outside our owned UI/profiles and no indexing service mutations.
            native=subprocess.run(
                [sys.executable,"-X","utf8",
                 str(Path(__file__).with_name("test_indexed_search_native.py")),
                 "--configuration",args.configuration],
                capture_output=True,text=True,timeout=25)
            print("INDEXED_SEARCH_NATIVE_ORACLE_PASS",
                  native.returncode==0,flush=True)
            assert native.returncode==0,(native.stdout,native.stderr)
            extension=control("SearchExtensionBox")
            extension.set_edit_text(".txt")
            control("SearchRunButton").invoke()
            wait(lambda:"Windows 인덱스 결과" in
                control("SearchCountText").window_text(),
                "indexed extension exclusion did not settle",20)
            assert NAME.casefold() not in " ".join(
                row.window_text() for row in
                control("SearchMatches").descendants()).casefold(),(
                "indexed extension exclusion exposed a .lnk shortcut")
            print("INDEXED_SEARCH_EXTENSION_EXCLUDES_LNK_PASS",True,flush=True)
            extension.set_edit_text(".LNK")
            control("SearchRunButton").invoke()
            wait(lambda:TERM in " ".join(
                row.window_text() for row in
                control("SearchMatches").descendants()),
                "indexed extension match does not contain public system shortcut",20)
            print("INDEXED_SEARCH_EXTENSION_LNK_MATCH_PASS",True,flush=True)
            sample_bytes=fixture.stat().st_size
            upper=(sample_bytes+1023)//1024
            minimum=control("SearchMinSizeBox")
            maximum=control("SearchMaxSizeBox")
            minimum.set_edit_text("0")
            maximum.set_edit_text(str(upper))
            control("SearchRunButton").invoke()
            wait(lambda:"1개" in control("SearchCountText").window_text()
                 and TERM in " ".join(row.window_text() for row in
                     control("SearchMatches").descendants())
                 and control("SearchRunButton").is_enabled(),
                 "indexed inclusive size and extension match failed",20)
            print("INDEXED_SEARCH_GUI_SIZE_MATCH_PASS",True,flush=True)
            minimum.set_edit_text(str(upper+1))
            maximum.set_edit_text("")
            control("SearchRunButton").invoke()
            wait(lambda:"0개" in control("SearchCountText").window_text()
                 and control("SearchRunButton").is_enabled(),
                 "indexed minimum size did not exclude shortcut",20)
            assert TERM not in " ".join(row.window_text() for row in
                control("SearchMatches").descendants()),(
                "indexed size exclusion still displays the shortcut")
            print("INDEXED_SEARCH_GUI_SIZE_EXCLUSION_PASS",True,flush=True)
            minimum.set_edit_text("")
            control("SearchRunButton").invoke()
            wait(lambda:"1개" in control("SearchCountText").window_text()
                 and control("SearchRunButton").is_enabled(),
                 "indexed empty size reset failed",20)
            summary=control("SearchCountText").window_text()
            print("INDEXED_SEARCH_SUMMARY",repr(summary),flush=True)
            assert "Windows 인덱스 결과" in summary,summary
            assert "1개" in summary,summary
            assert hashlib.sha256(fixture.read_bytes()).digest()==source_hash
            print("INDEXED_SEARCH_REAL_INDEX_MATCH_PASS",True,flush=True)
        success=True
    finally:
        geometry_stop.set()
        if geometry_thread:
            geometry_thread.join(timeout=2)
        if proc and proc.poll() is None:
            try:
                ctypes.windll.user32.PostMessageW(window.handle if window else 0,0x10,0,0)
                proc.wait(timeout=12)
            except Exception:
                proc.terminate();proc.wait(timeout=8)
        source_unchanged=(fixture.is_file() and
            hashlib.sha256(fixture.read_bytes()).digest()==source_hash)
        unchanged=all((real/name).is_file() and
           hashlib.sha256((real/name).read_bytes()).digest()==value
           for name,value in before.items())
        print("INDEXED_SEARCH_LEGACY_UNCHANGED",unchanged,flush=True)
        print("INDEXED_SEARCH_SYSTEM_SOURCE_UNCHANGED",source_unchanged,flush=True)
        if success:
            assert proc.returncode==0,proc.returncode
            print("INDEXED_SEARCH_PROCESS_EXIT",proc.returncode,flush=True)
        if success and unchanged and source_unchanged:
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("INDEXED_SEARCH_OWNED_LOGS",str(owned),flush=True)
    return 0 if success and unchanged and source_unchanged else 1

if __name__=="__main__":
    raise SystemExit(main())
