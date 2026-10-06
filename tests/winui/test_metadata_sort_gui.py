"""Focused owned GUI acceptance for metadata sort correctness above 1,200 items."""
from pathlib import Path
from paths import ROOT, app_exe
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
ITEMS=1305

def until(fn,label,timeout=30):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if fn():
            return
        time.sleep(.35)
    raise AssertionError(label)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    parser.add_argument("--exe",type=Path)
    parser.add_argument("--expect-legacy-fallback",action="store_true")
    parser.add_argument("--capture",choices=("none","before","after"),default="none")
    args=parser.parse_args()
    if os.name!="nt":
        return 2
    exe=(args.exe if args.exe else app_exe(args.configuration)).resolve()
    assert exe.is_file(),f"owned executable missing: {exe}"

    existing=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    hashes={name:hashlib.sha256((existing/name).read_bytes()).digest()
            for name in LEGACY if (existing/name).is_file()}
    evidence_root=ROOT/"logs"/"metadata-sort"
    evidence_root.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="metadata-sort-owned-",dir=evidence_root))
    folder=owned/"1305-files"
    folder.mkdir()

    old_stamp=1609459200
    for n in range(ITEMS-4):
        path=folder/f"mid-{n:04d}.txt"
        path.write_bytes(b"x")
        os.utime(path,(old_stamp,old_stamp))
    type_last=folder/"aa-type-last.zzz"
    type_last.write_bytes(b"type-last")
    os.utime(type_last,(old_stamp+10,old_stamp+10))
    size_winner=folder/"zz-size-winner.bin"
    size_winner.write_bytes(b"S"*8192)
    os.utime(size_winner,(old_stamp+20,old_stamp+20))
    date_winner=folder/"yy-date-winner.txt"
    date_winner.write_bytes(b"newest")
    os.utime(date_winner,(1893456000,1893456000))
    type_first=folder/"zz-type-first.aaa"
    type_first.write_bytes(b"type-first")
    os.utime(type_first,(old_stamp+30,old_stamp+30))
    assert len(list(folder.iterdir()))==ITEMS
    print("METADATA_SORT_FIXTURE_MTIME",
          int((folder/"mid-0000.txt").stat().st_mtime),
          int(date_winner.stat().st_mtime),flush=True)

    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        value=owned/key.lower()
        value.mkdir()
        env[key]=str(value)
    profile=Path(env["LOCALAPPDATA"])/"flyExplorer"
    profile.mkdir()
    (profile/"ui-preferences-v1.txt").write_bytes(
        b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
    for key in ("FLY_M23_OWNED_DRAG_TEST","FLY_M23_OWNED_SESSION",
                "FLY_M22_OWNED_ACTUAL_RECYCLE"):
        env.pop(key,None)

    from pywinauto import Desktop
    import psutil
    import ctypes as c
    from ctypes import wintypes as w

    process=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    parent=None
    success=False
    try:
        def ready():
            nonlocal parent
            if process.poll() is not None:
                return False
            if Path(psutil.Process(process.pid).exe()).resolve()!=exe:
                raise AssertionError("owned PID executable mismatch")
            windows=[x for x in Desktop(backend="uia").windows(process=process.pid)
                     if "flyExplorer" in x.window_text()]
            if len(windows)!=1:
                return False
            parent=Desktop(backend="uia").window(handle=windows[0].handle)
            return parent.child_window(auto_id="LeftFiles").exists(timeout=.2)
        until(ready,"metadata-sort window not ready",20)

        ui=c.windll.user32
        parent.set_focus()
        owner=w.DWORD()
        ui.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
        assert ui.GetWindowThreadProcessId(parent.handle,c.byref(owner))
        assert owner.value==process.pid
        assert ui.GetForegroundWindow()==parent.handle

        def list_view():
            matches=[x for x in parent.descendants()
                     if x.element_info.automation_id=="LeftFiles" and
                        x.element_info.control_type=="List"]
            visible=[x for x in matches if x.is_visible()]
            if visible:return visible[-1]
            if matches:return matches[-1]
            raise AssertionError("LeftFiles list not found")

        def first_row():
            rows=[x for x in list_view().descendants()
                  if x.element_info.control_type=="ListItem"]
            return rows[0].window_text() if rows else ""

        until(lambda:"aa-type-last.zzz" in first_row(),
              "deterministic initial name order not rendered",30)
        status=parent.child_window(auto_id="StatusText")
        desktop=Desktop(backend="uia")
        def choose_sort(label):
            parent.set_focus()
            button=parent.child_window(auto_id="SortButton")
            assert button.exists(timeout=.5) and button.is_visible(),label
            button.click_input()
            found=None
            def resolve_menu_item():
                nonlocal found
                for top in desktop.windows(process=process.pid):
                    candidates=[top]
                    candidates.extend(top.descendants())
                    for candidate in candidates:
                        if (candidate.element_info.control_type=="MenuItem" and
                            candidate.window_text()==label and
                            candidate.is_visible()):
                            found=candidate
                            return True
                return False
            until(resolve_menu_item,f"sort menu item not visible: {label}",5)
            found.click_input()
            expected={
                "이름 오름차순":0,"이름 내림차순":1,
                "크기 내림차순":2,"수정 날짜 내림차순":3,
                "유형 오름차순":4,"유형 내림차순":5,
                "크기 오름차순":6,"수정 날짜 오름차순":7,
            }[label]
            picker=parent.child_window(auto_id="SortPicker")
            header_id={
                0:"LeftNameSortButton",1:"LeftNameSortButton",
                2:"LeftSizeSortButton",3:"LeftDateSortButton",
                4:"LeftTypeSortButton",5:"LeftTypeSortButton",
                6:"LeftSizeSortButton",7:"LeftDateSortButton",
            }[expected]
            header=parent.child_window(auto_id=header_id)
            until(lambda:picker.selected_index()==expected,
                  f"sort picker did not record menu action: {label}",5)
            arrow="↓" if expected in (1,2,3,5) else "↑"
            until(lambda:arrow in header.window_text(),
                  f"sort callback did not update header: {label}",5)
            print("METADATA_SORT_MENU_ACTION",label,
                  "picker",picker.selected_index(),
                  "header",repr(header.window_text()),
                  "status",repr(status.window_text()),flush=True)

        choose_sort("크기 내림차순")

        if args.expect_legacy_fallback:
            until(lambda:"aa-type-last.zzz" in first_row() and
                  "불러오는 중" not in status.window_text(),
                  "legacy metadata fallback state did not settle",40)
            print("METADATA_SORT_LEGACY_NAME_FALLBACK_REPRODUCED",True,flush=True)
        else:
            until(lambda:"zz-size-winner.bin" in first_row(),
                  "size descending did not use full metadata above 1200",45)
            until(lambda:"메타데이터 정렬" in status.window_text(),
                  "metadata sort completion status missing",10)
            print("METADATA_SORT_OVER_1200_SIZE_DESC",True,flush=True)

        if args.capture!="none":
            class RECT(c.Structure):
                _fields_=[("left",w.LONG),("top",w.LONG),
                          ("right",w.LONG),("bottom",w.LONG)]
            rect=RECT()
            assert ui.GetWindowRect(parent.handle,c.byref(rect))
            width=rect.right-rect.left
            height=rect.bottom-rect.top
            print("METADATA_SORT_WINDOW_RECT",
                  rect.left,rect.top,width,height,flush=True)
            assert width>600 and height>400
            time.sleep(1.2)
            shot=evidence_root/f"metadata-sort-{args.capture}.png"
            ImageGrab.grab(
                bbox=(rect.left,rect.top,rect.right,rect.bottom),
                all_screens=True).save(shot)
            print("METADATA_SORT_VISUAL",shot.name,flush=True)

        if not args.expect_legacy_fallback:
            choose_sort("수정 날짜 내림차순")
            print("METADATA_SORT_DATE_FIRST_ROW",repr(first_row()),flush=True)
            date_rows=[row.window_text() for row in list_view().descendants()
                       if row.element_info.control_type=="ListItem" and
                          "yy-date-winner.txt" in row.window_text()]
            print("METADATA_SORT_DATE_WINNER_VISIBLE",date_rows[:1],flush=True)
            until(lambda:"yy-date-winner.txt" in first_row(),
                  "date descending did not use metadata",12)
            print("METADATA_SORT_OVER_1200_DATE_DESC",True,flush=True)
            choose_sort("유형 오름차순")
            until(lambda:"zz-type-first.aaa" in first_row(),
                  "type ascending did not use lightweight type metadata",12)
            print("METADATA_SORT_OVER_1200_TYPE_ASC",True,flush=True)

        assert size_winner.stat().st_size==8192
        assert date_winner.is_file() and type_first.is_file()
        success=True
    finally:
        if process.poll() is None:
            try:
                if parent is not None:
                    c.windll.user32.PostMessageW(parent.handle,0x10,0,0)
                    process.wait(timeout=12)
                else:
                    process.terminate()
                    process.wait(timeout=8)
            except Exception:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=8)
        if success:
            assert process.returncode==0,process.returncode
            print("METADATA_SORT_OWNED_PROCESS_EXIT",process.returncode,flush=True)
        unchanged=all((existing/name).is_file() and
           hashlib.sha256((existing/name).read_bytes()).digest()==digest
           for name,digest in hashes.items())
        print("METADATA_SORT_LEGACY_SETTINGS_UNCHANGED",unchanged,flush=True)
        if success and unchanged:
            shutil.rmtree(owned)
        else:
            print("METADATA_SORT_FIXTURE_RETAINED",owned,flush=True)
    return 0 if success and unchanged else 1

if __name__=="__main__":
    sys.exit(main())
