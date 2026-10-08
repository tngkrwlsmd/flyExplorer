"""Focused indexed filename search GUI: actual SystemIndex and bounded UI."""
import argparse
import ctypes
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from pywinauto import Desktop
from paths import ROOT,app_exe
from uia_polling import wait_until

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
NAME="flyExplorer-search-v3-owned-marker.txt"
TERM="flyExplorer-search-v3-owned-marker"

def wait(fn,label,seconds=25):
    return wait_until(fn,label,seconds=seconds,interval=.3)

def index_contains(folder,name):
    # Powershell 5.1 supports the Windows Search OLE DB provider. Only
    # inspect the test-owned filename, never log unrelated indexed rows.
    scope="file:"+str(folder).replace("\\","/").rstrip("/")+"/"
    scope=scope.replace("'","''")
    target=name.replace("'","''")
    # Use a single Powershell query with parameters restricted to owned
    # paths; OLE DB is a read-only SystemIndex connection.
    script=f"""
$ErrorActionPreference="Stop"
$db=New-Object System.Data.OleDb.OleDbConnection('Provider=Search.CollatorDSO.1;Extended Properties="Application=Windows"')
try {{
 $db.Open()
 $cmd=$db.CreateCommand()
 $cmd.CommandText="SELECT TOP 10 System.ItemPathDisplay FROM SystemIndex WHERE SCOPE='{scope}' AND System.FileName LIKE '%{target}%'"
 $r=$cmd.ExecuteReader()
 $found=$false
 while($r.Read()){{
   if([string]$r.GetValue(0) -eq '{str(folder / name).replace("'", "''")}'){{$found=$true}}
 }}
 $r.Close()
 if($found){{Write-Output 'OWNED_INDEXED=true'}}
 else{{Write-Output 'OWNED_INDEXED=false'}}
}}finally{{$db.Close()}}
"""
    encoded=__import__("base64").b64encode(script.encode("utf-16-le")).decode("ascii")
    result=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive",
                           "-EncodedCommand",encoded],
                          capture_output=True,text=True,timeout=12)
    return result.returncode==0 and "OWNED_INDEXED=true" in result.stdout

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--capture",choices=("before","after"),default="after")
    args=parser.parse_args()
    exe=app_exe(args.configuration).resolve()
    assert exe.is_file(),exe
    pictures=Path(os.environ["USERPROFILE"])/"Pictures"
    assert pictures.is_dir(),pictures
    fixture=pictures/NAME
    assert not fixture.exists(),fixture
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
    fixture.write_text("test-owned indexed filename verification\n",encoding="utf-8")
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
        panel=control("SearchTermBox")
        if not panel.exists(timeout=.2) or not panel.is_visible():
            window.child_window(auto_id="SearchPanelButton").invoke()
        wait(lambda:panel.exists(timeout=.2) and panel.is_visible(),
             "search panel did not open",12)
        control("SearchScopeBox").set_edit_text(str(pictures))
        panel.set_edit_text(TERM)
        mode=control("SearchModeBox")
        if args.capture=="after":
            assert mode.exists(timeout=2),"Windows index selector missing"
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
            # WSearch can take time to index a newly created file. First prove
            # the fixture is indexed; otherwise there is no fair positive oracle.
            deadline=time.monotonic()+55
            indexed=False
            while time.monotonic()<deadline:
                if index_contains(pictures,NAME):
                    indexed=True;break
                time.sleep(3)
            print("INDEXED_SEARCH_OWNED_SOURCE_INDEXED",indexed,flush=True)
            assert indexed,"test-owned Pictures file was not indexed by WSearch"
            window.child_window(auto_id="SearchRunButton").invoke()
            wait(lambda:TERM in " ".join(
                row.window_text() for row in
                control("SearchMatches").descendants()),
                "indexed result does not contain test-owned file",20)
            summary=window.child_window(auto_id="SearchCountText").window_text()
            print("INDEXED_SEARCH_SUMMARY",repr(summary),flush=True)
            assert "Windows 인덱스 결과" in summary,summary
            assert "1개" in summary,summary
            assert fixture.read_text(encoding="utf-8")=="test-owned indexed filename verification\n"
            print("INDEXED_SEARCH_REAL_INDEX_MATCH_PASS",True,flush=True)
        success=True
    finally:
        if proc and proc.poll() is None:
            try:
                ctypes.windll.user32.PostMessageW(window.handle if window else 0,0x10,0,0)
                proc.wait(timeout=12)
            except Exception:
                proc.terminate();proc.wait(timeout=8)
        fixture.unlink(missing_ok=True)
        unchanged=all((real/name).is_file() and
           hashlib.sha256((real/name).read_bytes()).digest()==value
           for name,value in before.items())
        print("INDEXED_SEARCH_LEGACY_UNCHANGED",unchanged,flush=True)
        print("INDEXED_SEARCH_FIXTURE_REMOVED",not fixture.exists(),flush=True)
        if success:
            assert proc.returncode==0,proc.returncode
            print("INDEXED_SEARCH_PROCESS_EXIT",proc.returncode,flush=True)
        if success and unchanged and not fixture.exists():
            shutil.rmtree(owned,ignore_errors=True)
        else:
            print("INDEXED_SEARCH_OWNED_LOGS",str(owned),flush=True)
    return 0 if success and unchanged and not fixture.exists() else 1

if __name__=="__main__":
    raise SystemExit(main())
