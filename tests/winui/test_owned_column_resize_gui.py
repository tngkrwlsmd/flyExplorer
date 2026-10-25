"""Owned GUI acceptance for draggable Details column separators."""
from pathlib import Path
from paths import APP, app_exe
from uia_polling import wait_until
from PIL import ImageGrab
import ctypes,hashlib,os,shutil,subprocess,sys,tempfile,time
from ctypes import wintypes
import psutil
from pywinauto import Desktop,mouse,keyboard

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

        # The owned app can start at 960x519 even on a 1280x768 desktop.
        # Maximize only our test window before testing Details column width.
        window().maximize()
        eventually(lambda:window().rectangle().width()>=1100,
                   "owned window did not maximize for Details columns",6)

        # L08 requires enough actual Details width, not a split-button
        # transition. On smaller desktop sessions (e.g. 1280x768), forcing
        # an unnecessary split click can fail before the hover oracle runs.
        initial_width=element("LeftFiles").rectangle().width()
        rect=window().rectangle()
        print("L08_INITIAL_PANE_GEOMETRY",initial_width,
              (rect.left,rect.top,rect.right,rect.bottom),flush=True)
        if initial_width<500:
            eventually(lambda:element("SplitButton").exists(timeout=.2) and
                       element("SplitButton").is_visible(),
                       "split toggle unavailable",6)
            element("SplitButton").click_input()
            eventually(lambda:element("LeftFiles").rectangle().width()>=500,
                       "split toggle did not provide enough Details width",8)
        eventually(lambda:element("LeftFiles").rectangle().width()>=500,
                   "left pane is too narrow for all Details columns",6)

        for auto_id in ("LeftNameColumnResizeThumb","LeftTypeColumnResizeThumb",
                        "LeftSizeColumnResizeThumb","LeftNameSortButton",
                        "LeftTypeSortButton","LeftSizeSortButton",
                        "LeftDateSortButton"):
            eventually(lambda a=auto_id:element(a).exists(timeout=.2) and
                       element(a).is_visible(),auto_id+" not visible",10)
        # Capture only while the exact owned app window is in the foreground.
        user32=ctypes.windll.user32
        user32.GetForegroundWindow.restype=wintypes.HWND
        def owned_foreground():
            return int(user32.GetForegroundWindow() or 0)==int(hwnd or 0)
        window().set_focus()
        eventually(owned_foreground,"owned window is not foreground for capture",3)
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
            # Force a real pointer exit/entry across the 12px thumb,
            # then measure whether WinUI applies ProtectedCursor after
            # dispatch time. Do not treat the old immediate HCURSOR oracle
            # as visual acceptance or override the already-passing drag.
            body=element("LeftFiles").rectangle()
            mouse.move(coords=(body.left+30,body.top+36))
            time.sleep(.10)
            assert owned_foreground(), "diagnostic pointer left owned window"
            mouse.move(coords=(x,y))
            elapsed=0
            for wait_ms in (70,180,350):
                time.sleep(wait_ms/1000.0)
                elapsed+=wait_ms
                current=horizontal_resize_cursor(details=True)
                owned_hit=hit_info(x,y)
                observed=("sizewe" if current["active"]==current["sizewe"]
                          else "arrow" if current["active"]==current["arrow"]
                          else "other")
                print("L08_HOVER_TIMELINE",thumb_id,"DWELL_MS",elapsed,
                      "HIT",owned_hit,"CURSOR",observed,flush=True)
            # UIA HelpText is emitted only by our own diagnostic Grid.
            # Correlate event arrival with the independent native HCURSOR.
            try:
                event_help=thumb.element_info.element.CurrentHelpText
            except Exception as error:
                event_help="<uia-help-error:"+type(error).__name__+">"
            print("L08_POINTER_EVENT_HELP",thumb_id,event_help,flush=True)
            print("L08_NATIVE_CURSOR_TRACE",thumb_id,resize_status(),flush=True)
            print("COLUMN_RESIZE_HOVER_PROBE",thumb_id,
                  owned_hit,current,flush=True)
            print("COLUMN_RESIZE_CURSOR_OBSERVED",thumb_id,
                  observed=="sizewe",flush=True)
            print("COLUMN_RESIZE_HIT_BEFORE",thumb_id,owned_hit,flush=True)
            # Cursor appearance is an independent L08 acceptance gate.
            # A successful column drag must not mask a persistent arrow.
            assert owned_hit[0]==thumb_id, (
                "L08 pointer missed the expected owned resize handle",
                thumb_id,owned_hit)
            assert observed=="sizewe", (
                "L08 native horizontal resize cursor missing on owned handle",
                thumb_id,current,owned_hit,event_help)
            assert owned_foreground(), "physical input outside owned window"
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
        print("PX10_COLUMN_RAPID_TAIL_COMMITTED=True",flush=True)
        # Width belongs to the original WindowTab's pane. Check that it
        # survives an unrelated workspace activation and return.
        before_return=element("LeftTypeSortButton").rectangle().left
        strip=element("WindowTabStrip")
        def tabs():
            return [t for t in strip.descendants()
                    if t.element_info.control_type=="TabItem"
                    and t.element_info.process_id==proc.pid]
        eventually(lambda:len(tabs())==1,"initial owned WindowTab absent",6)
        window().set_focus()
        assert owned_foreground()
        keyboard.send_keys("^t")
        eventually(lambda:len(tabs())==2,
                   "Ctrl+T did not create second owned WindowTab",10)
        window().set_focus()
        assert owned_foreground()
        tabs()[0].click_input()
        eventually(lambda:abs(element("LeftTypeSortButton").rectangle().left-
                              before_return)<=4,
                   "original WindowTab lost resized column width",14)
        print("OWNED_DETAIL_COLUMN_WINDOW_TAB_RESTORED",True,flush=True)
        body=element("LeftFiles").rectangle()
        mouse.move(coords=(body.left+30,body.top+40))
        window().set_focus()
        eventually(owned_foreground,"owned window is not foreground for final capture",3)
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
            # Verify the normal owned WinUI close path, not terminate().
            if hwnd is None:
                proc.terminate();proc.wait(timeout=8)
            else:
                assert ctypes.windll.user32.PostMessageW(hwnd,0x10,0,0)
                try:proc.wait(timeout=13)
                except subprocess.TimeoutExpired:
                    proc.terminate();proc.wait(timeout=5)
                    raise RuntimeError("PX10 owned WinUI did not close normally")
        print("OWNED_DETAIL_COLUMN_EXIT",proc.returncode,flush=True)
        safe=all((mfc/n).is_file() and
            hashlib.sha256((mfc/n).read_bytes()).digest()==h
            for n,h in old.items())
        print("SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL",safe,flush=True)
        if passed and safe and proc.returncode==0:
            assert owned.parent==root and owned.name.startswith("columns-gui-owned-")
            assert not owned.is_symlink()
            shutil.rmtree(owned)
            print("OWNED_COLUMN_RESIZE_FIXTURE_REMOVED",True,flush=True)
        else:
            print("OWNED_COLUMN_RESIZE_DIAGNOSTIC_FIXTURE_RETAINED",owned,flush=True)
    return 0 if passed and safe and proc.returncode==0 else 1

if __name__=="__main__":
    try:
        result=main(sys.argv[1] if len(sys.argv)>1 else "Release")
    except Exception:
        import traceback
        traceback.print_exc()
        print("OWNED_DETAIL_COLUMN_RESULT FAIL",flush=True)
        sys.exit(1)
    print("OWNED_DETAIL_COLUMN_RESULT "+("PASS" if result==0 else "FAIL"),
          flush=True)
    sys.exit(result)
