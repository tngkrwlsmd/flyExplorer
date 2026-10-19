"""Owned GUI acceptance for draggable Details column separators."""
from pathlib import Path
from paths import APP, app_exe
from uia_polling import wait_until
from PIL import ImageGrab
import ctypes,hashlib,os,shutil,subprocess,sys,tempfile,time
from ctypes import wintypes
import psutil
from pywinauto import Desktop,mouse

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf",
        "fxfile-folder_layout.conf")

def eventually(fn,label,seconds=12):
    return wait_until(fn, label, seconds=seconds, interval=.2)

def horizontal_resize_cursor(details=False):
    class CursorInfo(ctypes.Structure):
        _fields_=[("cbSize",wintypes.DWORD),("flags",wintypes.DWORD),
                  ("hCursor",wintypes.HANDLE),("position",wintypes.POINT)]
    user=ctypes.windll.user32
    user.LoadCursorW.argtypes=[wintypes.HINSTANCE,ctypes.c_void_p]
    user.LoadCursorW.restype=wintypes.HANDLE
    info=CursorInfo();info.cbSize=ctypes.sizeof(info)
    if not user.GetCursorInfo(ctypes.byref(info)):raise ctypes.WinError()
    expected=user.LoadCursorW(None,32644) # IDC_SIZEWE
    if details:
        arrow=user.LoadCursorW(None,32512) # IDC_ARROW
        return {"active":int(info.hCursor or 0),
                "arrow":int(arrow or 0),"sizewe":int(expected or 0)}
    return info.hCursor==expected

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
    env["FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC"]="1"
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
        def resize_status():
            try:
                return element("StatusText").window_text()
            except Exception as error:
                return "<status-error:"+type(error).__name__+">"

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
            window().set_focus()
            time.sleep(.12)
            thumb=element(thumb_id)
            next_header=element(next_header_id)
            start=next_header.rectangle().left
            box=thumb.rectangle()
            x=(box.left+box.right)//2
            y=(box.top+box.bottom)//2
            assert box.width()>=10 and box.height()>=8,(thumb_id,box)
            print("COLUMN_RESIZE_DRAG_BEGIN",thumb_id,
                  (box.left,box.top,box.right,box.bottom),
                  "boundary",start,flush=True)
            def hit_info(px,py):
                try:
                    hit=Desktop(backend="uia").from_point(px,py)
                    info=hit.element_info
                    # Never put titles from a foreign foreground window in CI logs.
                    if getattr(info,"process_id",None)!=proc.pid:
                        return ("not-owned-hit",)
                    return (info.automation_id,info.control_type)
                except Exception as error:
                    return ("<uia-error>",type(error).__name__,"")
            mouse.move(coords=(x,y))
            # Record the actual UIA hit and native cursor BEFORE the strict
            # cursor assertion; otherwise a failed hover hides the evidence.
            print("COLUMN_RESIZE_HOVER_PROBE",thumb_id,
                  hit_info(x,y),horizontal_resize_cursor(details=True),flush=True)
            eventually(horizontal_resize_cursor,
                       thumb_id+" did not display the horizontal resize cursor",3)
            print("COLUMN_RESIZE_HIT_BEFORE",thumb_id,hit_info(x,y),flush=True)
            mouse.press(button="left",coords=(x,y))
            print("COLUMN_RESIZE_BUTTON_AFTER_PRESS",
                  bool(ctypes.windll.user32.GetAsyncKeyState(0x01)&0x8000),
                  "status",resize_status(),flush=True)
            try:
                steps=10
                for step in range(1,steps+1):
                    nx=x+round(delta*step/steps)
                    mouse.move(coords=(nx,y))
                    time.sleep(.08)
                    boundary=element(next_header_id).rectangle().left
                    print("COLUMN_RESIZE_STEP",thumb_id,step,
                          "cursor",nx,y,"boundary",boundary,
                          "button",bool(ctypes.windll.user32.GetAsyncKeyState(0x01)&0x8000),
                          "hit",hit_info(nx,y),"status",resize_status(),flush=True)
            finally:
                mouse.release(button="left",coords=(x+delta,y))
            eventually(lambda:element(next_header_id).rectangle().left>=start+12,
                       thumb_id+" drag did not resize the next column boundary",8)
            end=element(next_header_id).rectangle().left
            eventually(horizontal_resize_cursor,
                       thumb_id+" lost the resize cursor after release",3)
            print("COLUMN_RESIZE_DRAG_END",thumb_id,
                  "boundary",end,"delta",end-start,flush=True)
        drag_and_verify("LeftNameColumnResizeThumb","LeftTypeSortButton",40)
        drag_and_verify("LeftTypeColumnResizeThumb","LeftSizeSortButton",28)
        drag_and_verify("LeftSizeColumnResizeThumb","LeftDateSortButton",20)

        # No artificial hold: motion shorter than the polling tick still commits.
        thumb=element("LeftNameColumnResizeThumb").rectangle()
        x=(thumb.left+thumb.right)//2;y=(thumb.top+thumb.bottom)//2
        start=element("LeftTypeSortButton").rectangle().left
        mouse.press(button="left",coords=(x,y))
        try:mouse.move(coords=(x+24,y))
        finally:mouse.release(button="left",coords=(x+24,y))
        eventually(lambda:element("LeftTypeSortButton").rectangle().left>=start+12,
                   "rapid resize lost its final movement",8)
        eventually(horizontal_resize_cursor,"rapid resize lost its cursor",3)
        body=element("LeftFiles").rectangle()
        mouse.move(coords=(body.left+30,body.top+40))
        eventually(lambda:not horizontal_resize_cursor(),
                   "resize cursor remained outside the header",3)

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
