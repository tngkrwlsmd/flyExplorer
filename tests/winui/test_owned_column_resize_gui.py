"""Owned GUI acceptance for draggable Details column separators."""
from pathlib import Path
from paths import APP, app_exe
from PIL import ImageGrab
import hashlib,os,shutil,subprocess,sys,tempfile,time
import psutil
from pywinauto import Desktop,mouse

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf",
        "fxfile-folder_layout.conf")

def eventually(fn,label,seconds=12):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        try:
            if fn(): return
        except Exception:
            pass
        time.sleep(.2)
    raise AssertionError(label)

def main(config="Release"):
    if os.name!="nt": return 2
    exe=app_exe(config)
    assert exe.is_file(),"Exact owned WinUI build missing"
    root=APP.parents[1]/"logs"/"m24"
    root.mkdir(parents=True,exist_ok=True)
    owned=Path(tempfile.mkdtemp(prefix="columns-gui-owned-",dir=root))
    folder=owned/"source";folder.mkdir()
    for name in ("alpha.txt","beta.txt","gamma.txt"):
        (folder/name).write_text(name,encoding="utf-8")
    mfc=Path(os.environ["APPDATA"])/"fxfile"/"conf"
    old={n:hashlib.sha256((mfc/n).read_bytes()).digest()
         for n in LEGACY if (mfc/n).is_file()}
    env=os.environ.copy()
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower();target.mkdir();env[key]=str(target)
    proc=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    hwnd=None;passed=False
    try:
        def window():
            nonlocal hwnd
            if proc.poll() is not None:return None
            assert Path(psutil.Process(proc.pid).exe()).resolve()==exe.resolve()
            matches=[q for q in Desktop(backend="uia").windows(process=proc.pid)
                     if "flyExplorer" in q.window_text()]
            if len(matches)!=1:return None
            hwnd=matches[0].handle
            return Desktop(backend="uia").window(handle=hwnd)
        eventually(lambda:window() is not None,"Owned flyExplorer window unavailable")
        win=window()
        def element(auto_id):
            return window().child_window(auto_id=auto_id)

        # The column-resize acceptance only needs the left Details pane.
        # Do not trust cached SecondaryPane UIA visibility or SplitButton text:
        # click once and use the real LeftFiles width delta as the split-state
        # oracle. If the first click made the pane narrower, it started in
        # single-pane mode, so click once more to restore the wider state.
        eventually(lambda:element("SplitButton").exists(timeout=.2) and
                   element("SplitButton").is_visible(),
                   "split toggle unavailable",6)
        initial_width=element("LeftFiles").rectangle().width()
        element("SplitButton").click_input()
        eventually(lambda:abs(element("LeftFiles").rectangle().width()-
                              initial_width)>=80,
                   "split toggle did not materially change left pane width",8)
        toggled_width=element("LeftFiles").rectangle().width()
        if toggled_width<initial_width:
            element("SplitButton").click_input()
            eventually(lambda:element("LeftFiles").rectangle().width()>=
                              initial_width-12,
                       "left pane did not return to single-pane width",8)
        eventually(lambda:element("LeftFiles").rectangle().width()>=500,
                   "single-pane width is too narrow for all Details columns",6)

        for auto_id in ("LeftNameColumnResizeThumb","LeftTypeColumnResizeThumb",
                        "LeftSizeColumnResizeThumb","LeftNameSortButton",
                        "LeftTypeSortButton","LeftSizeSortButton",
                        "LeftDateSortButton"):
            eventually(lambda a=auto_id:element(a).exists(timeout=.2) and
                       element(a).is_visible(),auto_id+" not visible",10)
        rect=window().rectangle()
        before=root/"detail-columns-before.png"
        ImageGrab.grab(
            bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(before)

        def drag_and_verify(thumb_id,next_header_id,delta):
            thumb=element(thumb_id)
            next_header=element(next_header_id)
            start=next_header.rectangle().left
            box=thumb.rectangle()
            x=(box.left+box.right)//2
            y=(box.top+box.bottom)//2
            mouse.move(coords=(x,y))
            mouse.press(button="left",coords=(x,y))
            mouse.move(coords=(x+delta,y),duration=.35)
            mouse.release(button="left",coords=(x+delta,y))
            eventually(lambda:element(next_header_id).rectangle().left>=start+delta-8,
                       thumb_id+" drag did not resize the next column boundary",8)
        drag_and_verify("LeftNameColumnResizeThumb","LeftTypeSortButton",40)
        drag_and_verify("LeftTypeColumnResizeThumb","LeftSizeSortButton",28)
        drag_and_verify("LeftSizeColumnResizeThumb","LeftDateSortButton",20)

        rect=window().rectangle()
        after=root/"detail-columns-after.png"
        ImageGrab.grab(
            bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(after)
        print("OWNED_DETAIL_COLUMN_NAME_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_TYPE_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_SIZE_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_VISUALS",before.name,after.name,flush=True)
        passed=True
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait(timeout=5)
        safe=all((mfc/n).is_file() and
            hashlib.sha256((mfc/n).read_bytes()).digest()==h
            for n,h in old.items())
        print("SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL",safe,flush=True)
        if passed and safe:
            shutil.rmtree(owned)
        else:
            print("OWNED_COLUMN_RESIZE_DIAGNOSTIC_FIXTURE_RETAINED",owned,flush=True)
    return 0 if passed and safe else 1

if __name__=="__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "Release"))
