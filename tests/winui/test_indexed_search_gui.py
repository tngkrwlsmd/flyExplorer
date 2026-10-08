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

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--capture",choices=("before","after"),default="after")
    args=parser.parse_args()
    exe=app_exe(args.configuration).resolve()
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
    try:
        proc=subprocess.Popen([str(exe),str(view)],
                              cwd=exe.parent,env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
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
            # A WinUI checkbox can appear twice in the UIA tree with
            # identical visible bounds. Use the independently-owned extension
            # field to prove index-only criteria rejection instead.
            unsupported=control("SearchExtensionBox")
            unsupported.set_edit_text(".txt")
            control("SearchRunButton").invoke()
            wait(lambda:"인덱스 검색은 파일명 일반 검색만 지원" in
                control("SearchCountText").window_text(),
                "indexed-only unsupported criteria did not reject before start",6)
            unsupported.set_edit_text("")
            print("INDEXED_SEARCH_UNSUPPORTED_PRESTART_REJECT_PASS",True,flush=True)
        else:
            assert not any(
                x.element_info.automation_id=="SearchModeBox"
                for x in window.descendants()),"BEFORE unexpectedly has index mode"
        # App-owned RenderTargetBitmap capture; service desktops can reject
        # pywinauto/PIL screen grabbing even when UIA works.
        wait(lambda:shot.is_file() and shot.stat().st_size>4096,
             "app-owned indexed search capture did not materialize",12)
        print("INDEXED_SEARCH_CAPTURE",shot.name,flush=True)

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
            control("SearchRunButton").invoke()
            wait(lambda:TERM in " ".join(
                row.window_text() for row in
                control("SearchMatches").descendants()),
                "indexed result does not contain public system shortcut",20)
            summary=control("SearchCountText").window_text()
            print("INDEXED_SEARCH_SUMMARY",repr(summary),flush=True)
            assert "Windows 인덱스 결과" in summary,summary
            assert "1개" in summary,summary
            assert hashlib.sha256(fixture.read_bytes()).digest()==source_hash
            print("INDEXED_SEARCH_REAL_INDEX_MATCH_PASS",True,flush=True)
        success=True
    finally:
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
