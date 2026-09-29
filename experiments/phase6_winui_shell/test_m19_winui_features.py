"""M1.9 owned real UIA integration, called inside the existing safe WinUI GUI harness.

The parent/child windows and user settings are never inferred from titles alone:
every new child PID must belong to the exact test-owned parent or be spawned
directly by this module with the exact compiled preview EXE and isolated
APPDATA/LOCALAPPDATA. No real Explorer/MFC window is controlled here.
"""
import ctypes as c
from ctypes import wintypes as W
from pathlib import Path
import hashlib
import os
import psutil
import subprocess
import time
from pywinauto import Desktop

def run(*,p,win,element,safe_click,focus,eventually,ownedwindows,
        left,right,inner,owned,localdata,env,exe):
    u=c.windll.user32
    u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    assert exe.is_file() and owned.is_dir()
    assert left.parent==owned and right.parent==owned
    assert Path(env["LOCALAPPDATA"])==localdata
    def text(key):
        return element(key).window_text()
    def match(key,needle):
        return needle.lower() in text(key).lower()
    def good(fn,why,timeout=10):
        return eventually(fn,why,timeout)
    def children():
        results=[]
        for proc in psutil.process_iter(["pid","ppid","exe","cmdline"]):
            try:
                info=proc.info
                if info["ppid"]!=p.pid or not info["exe"]:
                    continue
                if Path(info["exe"]).resolve()!=exe.resolve():
                    continue
                if "--m19-workspace" in (info["cmdline"] or []):
                    results.append(proc)
            except(psutil.NoSuchProcess,psutil.AccessDenied,ValueError):
                pass
        return results
    def ui_for_child(proc):
        boxes=ownedwindows(proc.pid)
        return [h for h,t in boxes if "flyExplorer - WinUI 3 migration preview" in t]
    def close_child(proc):
        if proc is None:return
        if not proc.is_running():return
        boxes=ui_for_child(proc)
        assert len(boxes)==1,("not a uniquely owned child window",proc.pid,boxes)
        u.PostMessageW(boxes[0],0x10,0,0)
        try:proc.wait(timeout=9)
        except psutil.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=5)
            raise AssertionError("Owned M1.9 child failed to close normally")
        assert proc.returncode==0 if hasattr(proc,"returncode") else True
    def search_matches(needle):
        return any(needle.lower() in row.window_text().lower()
            for row in element("SearchMatches").descendants())

    # Existing M1.8 GUI harness completed its dual-pane/virtual shell
    # regression. Its current RIGHT pane is back at its owned fixture.
    safe_click(element("PrimaryPaneTitle"))
    good(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
         "M1.9 parent left pane missing after M1.8 regression")
    saved_left=element("AddressBox").get_value()
    safe_click(element("WorkspacePanelButton"))
    for key in ("WorkspaceFileBox","SaveWorkspaceButton",
                "OpenWorkspaceButton"):
        assert element(key).exists(timeout=4),("Missing M1.9 workspace UI",key)
    assert not children(),"Foreign/previous M1.9 children under this owned PID"
    first=owned/"m19-saved-two-pane.fxworkspace"
    edit=element("WorkspaceFileBox")
    edit.set_edit_text(str(first))
    safe_click(element("SaveWorkspaceButton"))
    good(first.is_file,"Real WinUI Save new did not create the owned workspace",12)
    blob=first.read_bytes()
    assert blob.startswith(b"\xff\xfe") and 4<=len(blob)<=1048576
    body=first.read_text(encoding="utf-16")
    assert all(x in body for x in
      ("[main]","[workspace]","schema = 1",
       "main.view1.tab1.path", "main.view2.tab1.path",
       str(left),str(right)))
    before=hashlib.sha256(blob).digest()
    print("REAL_M19_WINUI_NAMED_WORKSPACE_SAVED_MFC_SCHEMA_ONE_TWO_PANES",True,flush=True)
    safe_click(element("SaveWorkspaceButton"))
    good(lambda:match("StatusText","exists"),
         "M1.9 WinUI Save overwrote existing user-owned workspace",7)
    assert hashlib.sha256(first.read_bytes()).digest()==before
    print("REAL_M19_NAMED_WORKSPACE_CREATE_NEW_NO_OVERWRITE",True,flush=True)

    # The real WinUI "Open" control must validate before CreateProcess,
    # launch only a sibling of the owned preview and preserve the parent.
    live=[]
    try:
        safe_click(element("OpenWorkspaceButton"))
        good(lambda:len(children())==1,
             "M1.9 valid Open failed to create exactly one private child",12)
        child=children()[0]
        live.append(child)
        good(lambda:len(ui_for_child(child))==1,
             "M1.9 exact owned WinUI child did not show its separate window",14)
        second=Desktop(backend="uia").window(handle=ui_for_child(child)[0])
        good(lambda:any("Nested" in row.window_text() for row
             in second.child_window(auto_id="LeftFiles").descendants()),
             "child did not restore M1.9 first workspace tab",17)
        good(lambda:any("Secondary" in row.window_text() for row
             in second.child_window(auto_id="RightFiles").descendants()),
             "child did not restore M1.9 second workspace pane",17)
        assert str(left).lower() in saved_left.lower()
        good(lambda:str(left).lower() in
             element("AddressBox").get_value().lower(),
             "opening a workspace replaced the parent folder")
        print("REAL_M19_WINUI_NAMED_WORKSPACE_ISOLATED_CHILD_TWO_PANES_RESTORED",
              True,flush=True)
        close_child(child)
        live.remove(child)

        # MFC UXH-07 schema compatibility: read a second synthetic
        # snapshot using the EXACT main.view1.tabN.path and current_tab keys
        # already emitted by the imported native option.cpp.
        legacy=owned/"m19-mfc-schema-compatible-multi-tab.fxworkspace"
        lines=["[main]","main.view.row_count = 1",
               "main.view.column_count = 2",
               "main.view1.current_tab = 1",
               "main.view1.tab1.path = "+str(left),
               "main.view1.tab2.path = "+str(inner),
               "main.view2.current_tab = 0",
               "main.view2.tab1.path = "+str(right),
               "[workspace]","schema = 1"]
        legacy.write_text("\r\n".join(lines)+"\r\n",encoding="utf-16")
        edit.set_edit_text(str(legacy))
        safe_click(element("OpenWorkspaceButton"))
        good(lambda:len(children())==1,
             "exact MFC-compatible schema did not launch private child",12)
        third=children()[0]
        live.append(third)
        good(lambda:len(ui_for_child(third))==1,
             "MFC-compatible multi-tab child window missing",14)
        third_win=Desktop(backend="uia").window(handle=ui_for_child(third)[0])
        good(lambda:any("Secondary" in row.window_text() for row
             in third_win.child_window(auto_id="RightFiles").descendants()),
             "MFC-compatible second pane did not restore",17)
        # Selected second tab points INTO Nested, so the listing is empty.
        good(lambda:str(inner).lower() in
             third_win.child_window(auto_id="AddressBox").get_value().lower(),
             "MFC-compatible selected second tab address did not restore",17)
        good(lambda:len([x for x in
             third_win.child_window(auto_id="LeftTabs").descendants()
             if x.element_info.control_type=="TabItem"])==2,
             "MFC-compatible active pane did not keep two tabs",7)
        print("REAL_M19_MFC_SCHEMA_ONE_SELECTED_SECOND_TAB_COMPATIBILITY",True,flush=True)
        close_child(third)
        live.remove(third)

        # Invalid files must NEVER start an owned child, mutate the active
        # parent or read outside their synthetic fixture.
        variants=[
            ("empty",b"", ".fxworkspace"),
            ("utf8",b"[workspace]\nschema = 1\n", ".fxworkspace"),
            ("invalid-schema",legacy.read_text(encoding="utf-16").replace(
                "schema = 1","schema = 2").encode("utf-16"),".fxworkspace"),
            ("bad-pane",legacy.read_text(encoding="utf-16").replace(
                "main.view.column_count = 2","main.view.column_count = 8"
                ).encode("utf-16"),".fxworkspace"),
            ("wrong-extension",legacy.read_bytes(),".txt"),
            ("oversize",b"\xff\xfe"+b"z"*1048575,".fxworkspace"),
            ("missing-folder",legacy.read_text(encoding="utf-16").replace(
                str(inner),str(owned/"does-not-exist-m19")).encode("utf-16"),
                ".fxworkspace")
        ]
        for name,data,ext in variants:
            target=owned/("invalid-"+name+ext)
            target.write_bytes(data)
            edit.set_edit_text(str(target))
            safe_click(element("OpenWorkspaceButton"))
            good(lambda:match("StatusText","rejected") or
                match("StatusText","choose an absolute"),
                "invalid workspace not rejected by actual WinUI Open: "+name,10)
            assert not children(),("invalid workspace launched a child",name)
            assert hashlib.sha256(first.read_bytes()).digest()==before
            safe_click(element("PrimaryPaneTitle"))
            assert str(left).lower() in element("AddressBox").get_value().lower()
        print("REAL_M19_SEVEN_INVALID_MFC_WORKSPACES_REJECTED_WITH_PARENT_PRESERVED",
              True,flush=True)

        # Scoped real GUI filename search runs on an independent native
        # thread. The startup checkbox is off and never learns an opted-out
        # folder; all results and preview history use ONLY owned paths.
        safe_click(element("SearchPanelButton"))
        for key in ("SearchScopeBox","SearchTermBox","SearchRememberBox",
                    "SearchRunButton","SearchRecentBox","SearchClearButton",
                    "SearchMatches","SearchCountText"):
            assert element(key).exists(timeout=4),("Missing M1.9 search UI",key)
        scope=element("SearchScopeBox")
        term=element("SearchTermBox")
        recents=element("SearchRecentBox")
        recall=localdata/"flyExplorer.WinUI3Preview"/"recent-scopes-v1.txt"
        assert not recall.exists(),"M1.9 initial test-owned recent history was not empty"
        assert element("SearchRememberBox").get_toggle_state()==0
        scope.set_edit_text(str(left))
        term.set_edit_text("readme")
        safe_click(element("SearchRunButton"))
        good(lambda:search_matches("readme.txt"),
             "real M1.9 file search failed to list owned matching filename",17)
        good(lambda:match("SearchCountText","1 matching files"),
             "M1.9 search result summary missing",7)
        assert not recall.exists(),"Default unchecked search persisted a private path"
        print("REAL_M19_SEARCH_DEFAULT_OPT_OUT_NO_PERSISTENT_HISTORY",True,flush=True)

        safe_click(element("SearchRememberBox"))
        assert element("SearchRememberBox").get_toggle_state()==1
        safe_click(element("SearchRunButton"))
        good(recall.is_file,"opt-in recent search persisted no owned profile",12)
        good(lambda:match("SearchCountText","1 matching files"),
             "M1.9 opted-in search did not finish",10)
        assert str(left) in recall.read_text(encoding="utf-16")
        assert str(right) not in recall.read_text(encoding="utf-16")
        print("REAL_M19_SEARCH_EXPLICIT_OPT_IN_SAVED_ONLY_SCOPE",True,flush=True)

        (right/"m19-other-result.txt").write_text(
            "owned matching fixture",encoding="utf-8")
        scope.set_edit_text(str(right))
        term.set_edit_text("m19-other-result")
        safe_click(element("SearchRunButton"))
        good(lambda:search_matches("m19-other-result.txt"),
             "second owned folder was not independently searched",14)
        good(lambda:recall.exists() and str(right) in
             recall.read_text(encoding="utf-16"),"opted-in second scope not persisted",10)
        content=recall.read_text(encoding="utf-16")
        assert content.index(str(right))<content.index(str(left)),content
        print("REAL_M19_SEARCH_TWO_OPTED_IN_LOCATIONS_NEWEST_FIRST",True,flush=True)
        saved_recent_sha=hashlib.sha256(recall.read_bytes()).digest()
        focus()
        recents.wrapper_object().select(1)
        good(lambda:str(left).lower() in
             element("SearchScopeBox").get_value().lower(),
             "selecting the second recent scope did not update the typed full path",8)
        assert hashlib.sha256(recall.read_bytes()).digest()==saved_recent_sha
        print("REAL_M19_RECENT_SEARCH_SELECTION_DOES_NOT_REWRITE_HISTORY",
              True,flush=True)
        # Real WinUI child with same test-owned LOCALAPPDATA, no parent
        # callbacks or global app/user settings. Verify restart persistence.
        restart=subprocess.Popen([str(exe),str(left)],cwd=exe.parent,env=env,
             stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
             stderr=subprocess.DEVNULL)
        try:
            good(lambda:len(ui_for_child(psutil.Process(restart.pid)))==1,
                 "isolated WinUI restart window missing",14)
            restarted=Desktop(backend="uia").window(
                handle=ui_for_child(psutil.Process(restart.pid))[0])
            search_btn=restarted.child_window(auto_id="SearchPanelButton")
            search_btn.click_input()
            # WinUI ComboBox virtualizes its popup; closed-combo UIA
            # descendants can be empty even with real Items(). The
            # explicit user-visible count is updated ONLY after the
            # asynchronous native load and Items().Append in the UI.
            count=restarted.child_window(auto_id="RecentCountText")
            good(lambda:"2 saved" in count.window_text(),
                 "restarted WinUI failed to reload two opted-in scopes",12)
            print("REAL_M19_SEARCH_RESTART_RECENTS_LOADED",2,flush=True)
        finally:
            if restart.poll() is None:
                target=psutil.Process(restart.pid)
                box=ui_for_child(target)
                if len(box)==1:u.PostMessageW(box[0],0x10,0,0)
                try:restart.wait(timeout=11)
                except subprocess.TimeoutExpired:
                    restart.terminate()
                    restart.wait(timeout=5)
                    raise AssertionError("Owned search restart window failed to close")
            assert restart.returncode==0

        safe_click(element("SearchClearButton"))
        good(lambda:recall.is_file() and
             recall.read_text(encoding="utf-16").strip()=="",
             "M1.9 Clear recent did not persist empty preview history",9)
        good(lambda:"0 saved" in element("RecentCountText").window_text(),
             "Clear recent did not update real WinUI count",6)
        assert str(left).lower() in element("SearchScopeBox").get_value().lower()
        print("REAL_M19_SEARCH_CLEAR_RETAINS_ACTIVE_FULL_SCOPE",True,flush=True)
        print("REAL_M19_SEARCH_CLEAR_PERSISTS_WITHOUT_MUTATING_ACTIVE_SCOPE",
              True,flush=True)
    finally:
        for child in live:
            if child.is_running():
                try:close_child(child)
                except Exception:
                    # Only exact descendants spawned by the owned parent,
                    # never other user/process-name matches.
                    child.terminate()
                    child.wait(timeout=5)
