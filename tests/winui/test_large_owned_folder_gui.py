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
from PIL import ImageGrab


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
    parser.add_argument("--items",type=int,choices=(1100,2300,5000,8000,20500,25000,25001),default=1100)
    parser.add_argument("--configuration",choices=("Debug","Release"),
                        default="Debug")
    parser.add_argument("--resident-window-evidence",
                        choices=("none","before","after"),default="none")
    parser.add_argument("--browse-over-complete-model",action="store_true")
    args=parser.parse_args()
    if args.resident_window_evidence!="none":
        assert args.items==2300 and args.configuration=="Release"
    if args.browse_over_complete_model:
        assert args.items in (20500,25000,25001) and args.configuration=="Release"
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
    if args.browse_over_complete_model:
        winner=folder/f"bench-{args.items-1:04d}.txt"
        winner.write_bytes(b"x"*4096)
        now=time.time()
        os.utime(winner,(now+7200,now+7200))
        (folder/"bench-17000.txt").rename(folder/"bench-17000.aaa")
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        value=owned/key.lower()
        value.mkdir()
        env[key]=str(value)
    for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
                "FLY_M22_OWNED_ACTUAL_RECYCLE"):
        env.pop(key,None)
    from pywinauto import Desktop, keyboard
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
        def visible_file_list():
            matches=[v for v in parent.descendants()
                     if v.element_info.automation_id=="LeftFiles" and
                        v.element_info.control_type=="List"]
            visible=[v for v in matches if v.is_visible()]
            if visible:
                return visible[-1]
            if matches:
                return matches[-1]
            raise AssertionError("owned LeftFiles list not found")
        def first_row():
            matches=[v for v in visible_file_list().descendants()
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
        more=parent.child_window(auto_id="LeftLoadMoreButton")
        if args.items>=8000:
            until(lambda:more.exists(timeout=.2) and
                  "160/1024+" in more.window_text(),
                  "streamed large folder did not expose the bounded initial page",10)
            more.click_input()
            until(lambda:"320/1024+" in parent.child_window(
                  auto_id="LeftLoadMoreButton").window_text(),
                  "initial streamed view page did not advance",10)
            print("OWNED_LARGE_MODEL_STREAMING_INITIAL_1024",True,flush=True)

        if args.resident_window_evidence!="none":
            previous=parent.child_window(auto_id="LeftLoadPreviousButton")
            status=parent.child_window(auto_id="StatusText")
            def progress_text():
                control=parent.child_window(auto_id="LeftLoadMoreButton")
                if not control.exists(timeout=.15) or not control.is_visible():
                    return ""
                return control.window_text()
            def click_more_and_settle():
                before=progress_text()
                parent.set_focus()
                parent.child_window(auto_id="LeftLoadMoreButton").click_input()
                until(lambda:progress_text()!=before,
                      "resident-window progress did not advance",12)
                if "불러오는 중" in status.window_text():
                    until(lambda:"불러오는 중" not in status.window_text(),
                          "resident-window Shell page did not settle",16)
            for _ in range(24):
                if "2208/2300" in progress_text():
                    break
                click_more_and_settle()
            until(lambda:"2208/2300" in progress_text(),
                  "resident-window probe did not reach matched logical progress",12)
            rect=parent.rectangle()
            evidence=base/("large-resident-window-"+
                args.resident_window_evidence+".png")
            ImageGrab.grab(
                bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(evidence)
            if args.resident_window_evidence=="before":
                assert "bench-0000.txt" in first_row()
                assert not previous.exists(timeout=.2) or not previous.is_visible()
                print("OWNED_RESIDENT_WINDOW_BEFORE_2208_OF_2300",True,
                      evidence.name,flush=True)
                success=True
                return
            until(lambda:previous.exists(timeout=.2) and previous.is_visible(),
                  "bounded resident window did not expose previous-page action",10)
            assert "bench-0252.txt" in first_row(),first_row()
            assert "2208/2300+" in progress_text(),progress_text()
            print("OWNED_RESIDENT_WINDOW_EVICTED_PREFIX_252",True,
                  evidence.name,flush=True)
            previous.click_input()
            until(lambda:"bench-0000.txt" in first_row() and
                  (not previous.exists(timeout=.2) or not previous.is_visible()),
                  "previous resident window did not restore logical prefix",16)
            print("OWNED_RESIDENT_WINDOW_PREVIOUS_REHYDRATED_PREFIX",True,flush=True)
            click_more_and_settle()
            until(lambda:previous.exists(timeout=.2) and previous.is_visible() and
                  "bench-0252.txt" in first_row(),
                  "forward resident rehydration did not return to shifted window",16)
            print("OWNED_RESIDENT_WINDOW_FORWARD_REHYDRATED_TAIL",True,flush=True)

        if args.browse_over_complete_model:
            def fresh_parent():
                windows=[x for x in Desktop(backend="uia").windows(process=process.pid)
                         if "flyExplorer" in x.window_text()]
                if len(windows)!=1:
                    raise AssertionError("owned flyExplorer window identity changed")
                return Desktop(backend="uia").window(handle=windows[0].handle)
            def more_control():
                return fresh_parent().child_window(auto_id="LeftLoadMoreButton")
            def progress_text():
                control=more_control()
                return control.window_text() if control.exists(timeout=.2) and control.is_visible() else ""
            def footer_count():
                control=fresh_parent().child_window(auto_id="ItemCountText")
                if not control.exists(timeout=.2):
                    return 0
                digits="".join(ch for ch in control.window_text() if ch.isdigit())
                return int(digits) if digits else 0
            def fresh_first_row():
                matches=[v for v in fresh_parent().child_window(
                   auto_id="LeftFiles").descendants()
                   if v.element_info.control_type=="ListItem"]
                return matches[0].window_text() if matches else ""
            def status_text():
                control=fresh_parent().child_window(auto_id="StatusText")
                return control.window_text() if control.exists(timeout=.2) else ""
            shown=0
            for _ in range(180):
                text=progress_text()
                head=text.split("/",1)[0]
                try:
                    shown=max(shown,int(head))
                except ValueError:
                    pass
                shown=max(shown,footer_count())
                if shown>20000:
                    break
                before=(text,footer_count())
                until(lambda:more_control().exists(timeout=.2) and
                      more_control().is_visible(),
                      "browse-over-20k load-more action disappeared before completion",14)
                more_control().click_input()
                until(lambda:(progress_text(),footer_count())!=before,
                      "browse-over-20k progress did not advance",14)
                if "불러오는 중" in status_text():
                    until(lambda:"불러오는 중" not in status_text(),
                          "browse-over-20k Shell page did not settle",16)
            shown=max(shown,footer_count())
            assert shown>20000,(progress_text(),footer_count())
            def previous_visible():
                control=fresh_parent().child_window(auto_id="LeftLoadPreviousButton")
                return control.exists(timeout=.2) and control.is_visible()
            until(previous_visible,
                  "browse-over-20k did not retain backward resident navigation",8)
            current=fresh_parent()
            rect=current.rectangle()
            evidence=base/"large-browse-over-20k-after.png"
            ImageGrab.grab(
                bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(evidence)
            # Verify the metadata ceiling *before* completing the name
            # index via its much larger independent browsing budget.
            # This forces the 25,000+one Shell lookahead path to run.
            if args.items in (25000,25001):
                winner_name=f"bench-{args.items-1:04d}.txt"
                fresh_parent().child_window(auto_id="SortPicker").select(2)
                if args.items==25001:
                    until(lambda:"25,000" in status_text(),
                          "25,001-entry metadata sentinel was not refused",90)
                    assert winner_name not in fresh_first_row(), (
                        "partial indexed metadata sort was exposed"
                    )
                    assert process.poll() is None
                    assert (folder/winner_name).stat().st_size==4096
                    print("OWNED_LARGE_25001_METADATA_SORT_REFUSED",True,flush=True)
                    print("OWNED_LARGE_25001_NO_PARTIAL_SORT",True,flush=True)
                    print("OWNED_LARGE_25001_SAMPLED_RSS_MIB",
                          round(psutil.Process(process.pid).memory_info().rss/1048576,1),
                          flush=True)
                    success=True
                    return
                until(lambda:winner_name in fresh_first_row() and
                      str(args.items) in progress_text(),
                      "exact 25,000-entry metadata index size sort failed",90)
                print("OWNED_LARGE_25000_SIZE_SORT_INDEXED",True,flush=True)
                fresh_parent().child_window(auto_id="SortPicker").select(3)
                until(lambda:winner_name in fresh_first_row(),
                      "exact 25,000-entry indexed modified-date sort failed",45)
                print("OWNED_LARGE_25000_DATE_SORT_INDEXED",True,flush=True)
                fresh_parent().child_window(auto_id="SortPicker").select(4)
                until(lambda:"bench-17000.aaa" in fresh_first_row(),
                      "exact 25,000-entry indexed type sort failed",45)
                print("OWNED_LARGE_25000_TYPE_SORT_INDEXED",True,flush=True)
                rect=fresh_parent().rectangle()
                evidence=base/"large-metadata-boundary-25000-after.png"
                ImageGrab.grab(
                    bbox=(rect.left,rect.top,rect.right,rect.bottom),
                    include_layered_windows=True).save(evidence)
                print("OWNED_LARGE_25000_EXACT_LIMIT_SORT_PASS",True,flush=True)
                print("OWNED_LARGE_BOUNDARY_SAMPLED_RSS_MIB",
                      round(psutil.Process(process.pid).memory_info().rss/1048576,1),
                      flush=True)
                success=True
                return

            fresh_parent().child_window(auto_id="SortPicker").select(1)
            until(lambda:"bench-9999.txt" in fresh_first_row(),
                  "indexed global name sort above 20k did not complete",16)
            sort_progress=progress_text()
            assert "20500" in sort_progress,sort_progress
            previous=fresh_parent().child_window(auto_id="LeftLoadPreviousButton")
            assert not previous.exists(timeout=.2) or not previous.is_visible()
            filt=fresh_parent().child_window(auto_id="LeftNameFilterBox")
            assert filt.exists(timeout=.2)
            before_filter=(status_text(),footer_count(),fresh_first_row())
            files=fresh_parent().child_window(auto_id="LeftFiles")
            files.set_focus()
            keyboard.send_keys("^+f")
            until(lambda:fresh_parent().child_window(
                      auto_id="LeftNameFilterBox").has_keyboard_focus(),
                  "Ctrl+Shift+F did not focus the indexed name filter",5)
            target=str(args.items-1)
            keyboard.send_keys(target)
            until(lambda:fresh_parent().child_window(
                      auto_id="LeftNameFilterBox").get_value()==target,
                  "indexed name filter keyboard input did not accept the target",5)
            print("OWNED_LARGE_INDEX_FILTER_INPUT_ACCEPTED",True,flush=True)
            until(lambda:
                  status_text()!=before_filter[0] or
                  footer_count()!=before_filter[1] or
                  fresh_first_row()!=before_filter[2],
                  "indexed name filter event produced no observable change",8)
            print("OWNED_LARGE_INDEX_FILTER_EVENT_STATE",
                  repr(fresh_parent().child_window(
                      auto_id="LeftNameFilterBox").get_value()),
                  repr(status_text()),footer_count(),
                  repr(fresh_first_row()),flush=True)
            until(lambda:footer_count()==1,
                  "indexed name filter model count did not become one",8)
            print("OWNED_LARGE_INDEX_FILTER_MODEL_STATE",
                  repr(status_text()),footer_count(),
                  repr(fresh_first_row()),flush=True)
            until(lambda:f"bench-{args.items-1:04d}.txt" in fresh_first_row(),
                  "indexed name filter did not project the target row",12)
            filt=fresh_parent().child_window(auto_id="LeftNameFilterBox")
            filt.set_focus()
            keyboard.send_keys("^a{BACKSPACE}")
            until(lambda:fresh_parent().child_window(
                      auto_id="LeftNameFilterBox").get_value()=="",
                  "indexed name filter keyboard clear did not empty the editor",5)
            until(lambda:"bench-9999.txt" in fresh_first_row(),
                  "clearing indexed filter did not restore indexed name sort",12)
            fresh_parent().child_window(auto_id="SortPicker").select(2)
            until(lambda:f"bench-{args.items-1:04d}.txt" in fresh_first_row() and
                  str(args.items) in progress_text(),
                  "indexed metadata size sort above 20k did not complete",90)
            assert (folder/f"bench-{args.items-1:04d}.txt").stat().st_size==4096
            print("OWNED_LARGE_OVER_20K_SIZE_SORT_INDEXED",True,flush=True)
            fresh_parent().child_window(auto_id="SortPicker").select(3)
            until(lambda:f"bench-{args.items-1:04d}.txt" in fresh_first_row(),
                  "indexed metadata date sort above 20k did not complete",45)
            print("OWNED_LARGE_OVER_20K_DATE_SORT_INDEXED",True,flush=True)
            fresh_parent().child_window(auto_id="SortPicker").select(4)
            until(lambda:"bench-17000.aaa" in fresh_first_row(),
                  "indexed metadata type sort above 20k did not complete",35)
            print("OWNED_LARGE_OVER_20K_TYPE_SORT_INDEXED",True,flush=True)
            current=fresh_parent()
            rect=current.rectangle()
            evidence=base/"large-name-index-over-20k-after.png"
            ImageGrab.grab(
                bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(evidence)
            print("OWNED_LARGE_BROWSE_OVER_20000",shown,flush=True)
            print("OWNED_LARGE_OVER_20K_NAME_SORT_INDEXED",True,flush=True)
            print("OWNED_LARGE_OVER_20K_NAME_FILTER_INDEXED",True,flush=True)
            print("OWNED_LARGE_OVER_20K_METADATA_SORT_INDEXED",True,flush=True)
            if args.items==25000:
                print("OWNED_LARGE_25000_EXACT_LIMIT_SORT_PASS",True,flush=True)
            print("OWNED_LARGE_BOUNDARY_SAMPLED_RSS_MIB",
                  round(psutil.Process(process.pid).memory_info().rss/1048576,1),
                  flush=True)
            print("OWNED_LARGE_OVER_20K_INDEX_VISUAL",evidence.name,flush=True)
            success=True
            return

        parent.child_window(auto_id="SortPicker").select(1)
        until(lambda:f"bench-{args.items-1:04d}.txt" in first_row(),
              "large-folder global name sort did not complete streamed pages",
              36 if args.items>=8000 else 24)
        if args.resident_window_evidence=="after":
            previous=parent.child_window(auto_id="LeftLoadPreviousButton")
            until(lambda:(not previous.exists(timeout=.2) or
                          not previous.is_visible()) and
                         "bench-2299.txt" in first_row(),
                  "global sort did not rebuild the evicted prefix",16)
            print("OWNED_RESIDENT_WINDOW_GLOBAL_SORT_REBUILT_2300",True,flush=True)
            # This focused resident-window mode has already proved the target
            # navigation and full-model sort boundaries. Do not fall through
            # into the generic 2300-item view/filter tail, whose 160-row reset
            # assumption belongs to a fresh non-windowed scenario.
            success=True
            return
        if args.items>=8000:
            until(lambda:f"320/{args.items}" in parent.child_window(
                  auto_id="LeftLoadMoreButton").window_text(),
                  "global sort did not finish the 8000-item streamed model",12)
            print("OWNED_LARGE_MODEL_STREAMING_SORT_COMPLETES_8000",True,flush=True)
            more.click_input()
            until(lambda:f"480/{args.items}" in parent.child_window(
                  auto_id="LeftLoadMoreButton").window_text(),
                  "post-stream controlled view page did not advance",12)
        elif args.items>=2300:
            until(lambda:more.exists(timeout=.2) and
                  f"160/{args.items}" in more.window_text(),
                  "large native entries were not view-paged",8)
            more.click_input()
            until(lambda:f"320/{args.items}" in parent.child_window(
                  auto_id="LeftLoadMoreButton").window_text(),
                  "controlled extra page did not render",12)
        if args.items==2300:
            filt=parent.child_window(auto_id="LeftNameFilterBox")
            assert filt.exists(timeout=.2)
            files=parent.child_window(auto_id="LeftFiles")
            files.set_focus()
            keyboard.send_keys("^+f")
            until(lambda:filt.has_keyboard_focus(),
                  "Ctrl+Shift+F did not reveal and focus the owned pane name filter",5)
            keyboard.send_keys("2299")
            until(lambda:filt.get_value()=="2299",
                  "keyboard name filter input did not accept the target",5)
            until(lambda:"bench-2299.txt" in first_row() and
                  (not parent.child_window(
                       auto_id="LeftLoadMoreButton").exists(timeout=.1) or
                   not parent.child_window(
                       auto_id="LeftLoadMoreButton").is_visible()),
                  "native file-name filter must not mutate model or page",9)
            keyboard.send_keys("^a{BACKSPACE}")
            until(lambda:filt.get_value()=="",
                  "keyboard name filter clear did not empty the editor",5)
            until(lambda:"bench-2299.txt" in first_row(),
                  "clearing pane filter failed to restore sorted native snapshot",10)
            files.set_focus()
            keyboard.send_keys("^+f")
            until(lambda:filt.has_keyboard_focus(),
                  "Ctrl+Shift+F did not refocus the owned pane name filter",5)
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
