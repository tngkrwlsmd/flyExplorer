"""Owned GUI acceptance for draggable Details column separators."""
from pathlib import Path
from paths import APP, app_exe
from uia_polling import wait_until
from l08_pointer_oracle import parse_l08_pointer_help, classify_l08_hover
from l08_pointer_oracle import classify_l08_cursor_reference
from l08_sendinput_mouse import sendinput_mouse_move
from PIL import ImageGrab
import ctypes,hashlib,os,re,shutil,subprocess,sys,tempfile,time
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
                "arrow":int(arrow or 0),"sizewe":int(expected or 0),
                "flags":int(info.flags),
                "position":(info.position.x,info.position.y)}
    return info.hCursor==expected

def main(config="Release", pane="left"):
    if pane not in ("left","right"):
        raise ValueError("owned resize pane must be left or right")
    pane_prefix="Right" if pane=="right" else "Left"
    opposite_prefix="Left" if pane=="right" else "Right"
    if os.name!="nt": return 2
    # A remote session can remain logged in while its Winlogon input desktop
    # is inaccessible. Fail before launching the test-owned app: a missing
    # foreground/input desktop is not evidence of a product cursor defect.
    desktop_user32=ctypes.windll.user32
    desktop_user32.GetCursorPos.argtypes=[ctypes.POINTER(wintypes.POINT)]
    desktop_user32.GetCursorPos.restype=wintypes.BOOL
    desktop_point=wintypes.POINT()
    if not desktop_user32.GetCursorPos(ctypes.byref(desktop_point)):
        print("L08_INTERACTIVE_DESKTOP_UNAVAILABLE",pane,flush=True)
        return 2
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
    env["FLY_G01_OWNED_CLOSE_TRACE"]="YES"
    for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
        target=owned/key.lower();target.mkdir();env[key]=str(target)
    proc=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
    # Available even if maximization or early UIA setup fails before hover.
    user32=ctypes.windll.user32
    hwnd=None;passed=False;close_timed_out=False
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
        initial_width=element(pane_prefix+"Files").rectangle().width()
        rect=window().rectangle()
        print("L08_INITIAL_PANE_GEOMETRY",pane,initial_width,
              (rect.left,rect.top,rect.right,rect.bottom),flush=True)
        if initial_width<500 and pane=="right":
            raise AssertionError("right pane too narrow for three Details handles")
        if initial_width<500:
            eventually(lambda:element("SplitButton").exists(timeout=.2) and
                       element("SplitButton").is_visible(),
                       "split toggle unavailable",6)
            element("SplitButton").click_input()
            eventually(lambda:element("LeftFiles").rectangle().width()>=500,
                       "split toggle did not provide enough Details width",8)
        eventually(lambda:element(pane_prefix+"Files").rectangle().width()>=500,
                   pane+" pane is too narrow for all Details columns",6)

        for auto_id in (pane_prefix+"NameColumnResizeThumb",pane_prefix+"TypeColumnResizeThumb",
                        pane_prefix+"SizeColumnResizeThumb",pane_prefix+"NameSortButton",
                        pane_prefix+"TypeSortButton",pane_prefix+"SizeSortButton",
                        pane_prefix+"DateSortButton"):
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
        before=root/("detail-columns-right-before.png" if pane=="right"
                     else "detail-columns-before.png")
        ImageGrab.grab(
            bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(before)

        opposite_before=(element(opposite_prefix+"TypeSortButton").rectangle().width()
                         if pane=="right" else None)
        cursor_observations=[]
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
            # Force a real pointer exit/entry across the 12px thumb.
            # Compare owned WinUI entered counters *before and after*
            # moving the pointer; a nonzero historical counter alone
            # does not prove this hover dispatched PointerEntered.
            def pointer_snapshot():
                try:
                    raw=thumb.element_info.element.CurrentHelpText
                except Exception:
                    return None
                return parse_l08_pointer_help(raw)
            def routed_root_moves():
                # Only parse one bounded, test-owned native diagnostic field.
                # Never print arbitrary StatusText or another app's UIA text.
                status=resize_status()
                if not status.startswith("L08_NATIVE ticks=") or len(status)>400:
                    return None
                match=re.search(r"\brootMove=([0-9]{1,5})(?=\s|$)",status)
                return int(match.group(1)) if match else None
            body=element(pane_prefix+"Files").rectangle()
            sendinput_mouse_move(coords=(body.left+30,body.top+36))
            time.sleep(.10)
            assert owned_foreground(), "diagnostic pointer left owned window"
            # pywinauto.mouse.move uses SetCursorPos. Our exact-source
            # interactive control reproduced zero WinUI enter events with
            # that input, while four-step SendInput produced PointerEntered,
            # a native sizewe cursor and an independent Edit I-beam.
            # Keep the pre-hover baseline and cross the 12px thumb with
            # bounded OS SendInput movement; never use UIA Invoke.
            sendinput_mouse_move(coords=(x-24,y))
            time.sleep(.10)
            pointer_before=pointer_snapshot()
            root_move_before=routed_root_moves()
            for approach_x in (x-12,x-6,x):
                sendinput_mouse_move(coords=(approach_x,y))
                time.sleep(.025)
            assert owned_foreground(), "approach left owned window"
            elapsed=0
            pointer_after=None
            for wait_ms in (70,180,350):
                time.sleep(wait_ms/1000.0)
                elapsed+=wait_ms
                current=horizontal_resize_cursor(details=True)
                owned_hit=hit_info(x,y)
                observed=("sizewe" if current["active"]==current["sizewe"]
                          else "arrow" if current["active"]==current["arrow"]
                          else "other")
                pointer_after=pointer_snapshot()
                root_move_after=routed_root_moves()
                root_move_delta=(root_move_after-root_move_before
                                 if root_move_before is not None and
                                    root_move_after is not None and
                                    root_move_after>=root_move_before else None)
                print("L08_ROOT_POINTER_MOVE",thumb_id,
                      "DWELL_MS",elapsed,"BASELINE",root_move_before,
                      "AFTER",root_move_after,"DELTA",root_move_delta,
                      flush=True)
                # Compare WinUI entry and native cursor from the SAME dwell.
                # A late exit must not be reported as an arrow override.
                dwell_boundary=classify_l08_hover(
                    pointer_before,pointer_after,observed,
                    owned_hit[0]==thumb_id)
                print("L08_HOVER_TIMELINE",thumb_id,"DWELL_MS",elapsed,
                      "HIT",owned_hit,"CURSOR",observed,
                      "WINUI",pointer_after,"BOUNDARY",dwell_boundary,
                      flush=True)
            # Print only strictly parsed, bounded test-owned event counters,
            # never arbitrary UIA HelpText from an external element.
            event_help=pointer_after
            classification=classify_l08_hover(
                pointer_before,pointer_after,observed,
                owned_hit[0]==thumb_id)
            print("L08_POINTER_EVENT_HELP",thumb_id,event_help,flush=True)
            print("L08_POINTER_BOUNDARY",thumb_id,classification,
                  "BASELINE",pointer_before,"LATEST",pointer_after,flush=True)
            print("L08_NATIVE_CURSOR_TRACE",thumb_id,resize_status(),flush=True)
            print("COLUMN_RESIZE_HOVER_PROBE",thumb_id,
                  owned_hit,current,flush=True)
            print("COLUMN_RESIZE_CURSOR_OBSERVED",thumb_id,
                  observed=="sizewe",flush=True)
            print("COLUMN_RESIZE_HIT_BEFORE",thumb_id,owned_hit,flush=True)
            # The global OS cursor can differ from this test thread's cursor
            # and from the owned app's thread-local cursor. Only after the
            # original strict observation has failed, temporarily calibrate
            # SetCursor on this test thread and restore its exact old value.
            # Never use this synthetic calibration to satisfy acceptance.
            if observed!="sizewe":
                user32.GetCursor.restype=wintypes.HANDLE
                user32.SetCursor.argtypes=[wintypes.HANDLE]
                user32.SetCursor.restype=wintypes.HANDLE
                previous=user32.GetCursor()
                try:
                    user32.SetCursor(current["sizewe"])
                    time.sleep(.03)
                    test_thread=horizontal_resize_cursor(details=True)
                    print("L08_TEST_THREAD_CURSOR_CALIBRATION",
                          thumb_id,"OLD",int(previous or 0),
                          "GLOBAL_BEFORE",current,
                          "GLOBAL_DURING",test_thread,
                          "GLOBAL_CHANGED",
                          test_thread["active"]==current["sizewe"],
                          "OWNED_FOREGROUND",owned_foreground(),flush=True)
                finally:
                    user32.SetCursor(previous)
                print("L08_TEST_THREAD_CURSOR_RESTORED",thumb_id,
                      horizontal_resize_cursor(details=True),flush=True)
            # Cursor appearance is an independent L08 acceptance gate.
            # A successful column drag must not mask a persistent arrow.
            assert owned_hit[0]==thumb_id, (
                "L08 pointer missed the expected owned resize handle",
                thumb_id,owned_hit)
            # Preserve the failed OS-cursor oracle but defer its assertion so
            # physical drag, rapid-tail, workspace restore and normal close
            # can be independently exercised in the same exact-SHA run.
            cursor_observations.append(
                (thumb_id,observed,current,owned_hit,event_help))
            assert owned_foreground(), "physical input outside owned window"
            mouse.press(button="left",coords=(x,y))
            print("COLUMN_RESIZE_BUTTON_AFTER_PRESS",
                  bool(ctypes.windll.user32.GetAsyncKeyState(0x01)&0x8000),
                  "status",resize_status(),flush=True)
            try:
                steps=10
                for step in range(1,steps+1):
                    nx=x+round(delta*step/steps)
                    sendinput_mouse_move(coords=(nx,y))
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
        drag_and_verify(pane_prefix+"NameColumnResizeThumb",pane_prefix+"TypeSortButton",40)
        drag_and_verify(pane_prefix+"TypeColumnResizeThumb",pane_prefix+"SizeSortButton",28)
        drag_and_verify(pane_prefix+"SizeColumnResizeThumb",pane_prefix+"DateSortButton",20)

        # No artificial hold: motion shorter than the polling tick still commits.
        thumb=element(pane_prefix+"NameColumnResizeThumb").rectangle()
        x=(thumb.left+thumb.right)//2;y=(thumb.top+thumb.bottom)//2
        start=element(pane_prefix+"TypeSortButton").rectangle().left
        mouse.press(button="left",coords=(x,y))
        try:sendinput_mouse_move(coords=(x+24,y))
        finally:mouse.release(button="left",coords=(x+24,y))
        eventually(lambda:element(pane_prefix+"TypeSortButton").rectangle().left>=start+12,
                   "rapid resize lost its final movement",8)
        print("PX10_COLUMN_RAPID_TAIL_COMMITTED=True",flush=True)
        # Width belongs to the original WindowTab's pane. Check that it
        # survives an unrelated workspace activation and return.
        before_return=element(pane_prefix+"TypeSortButton").rectangle().left
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
        eventually(lambda:abs(element(pane_prefix+"TypeSortButton").rectangle().left-
                              before_return)<=4,
                   "original WindowTab lost resized column width",14)
        print("OWNED_DETAIL_COLUMN_WINDOW_TAB_RESTORED",True,flush=True)
        if pane=="right":
            opposite_after=element(opposite_prefix+"TypeSortButton").rectangle().width()
            assert abs(opposite_after-opposite_before)<=2,(
                "left pane width changed during right pane resize",
                opposite_before,opposite_after)
            print("PX10_RIGHT_OPPOSITE_WIDTH_UNCHANGED",True,flush=True)
        # An I-beam is a useful *independent* OS cursor reference only when
        # UIA confirms our own enabled Edit at the test-owned cursor point.
        # A failed reference is inconclusive; do not remove the strict SIZEWE
        # assertion or turn this into a passing product acceptance.
        owned_edit_hit=False
        text_cursor="other"
        try:
            search=element("QuickSearchBox")
            search_box=search.rectangle()
            search_x=(search_box.left+search_box.right)//2
            search_y=(search_box.top+search_box.bottom)//2
            sendinput_mouse_move(coords=(search_x,search_y))
            time.sleep(.3)
            hit=Desktop(backend="uia").from_point(
                search_x,search_y).element_info
            owned_edit_hit=(getattr(hit,"process_id",None)==proc.pid and
                            getattr(hit,"control_type",None)=="Edit" and
                            search.is_enabled() and owned_foreground())
            text_control=horizontal_resize_cursor(details=True)
            beam=user32.LoadCursorW(None,32513) # IDC_IBEAM
            text_cursor=("ibeam" if text_control["active"]==beam
                         else "arrow" if text_control["active"]==text_control["arrow"]
                         else "other")
            print("L08_TEXTBOX_CURSOR_POSITIVE_CONTROL",
                  "OWNED_EDIT",owned_edit_hit,
                  "OS",text_control,"IBEAM",int(beam or 0),
                  "MATCH",text_cursor=="ibeam",
                  "OWNED_FOREGROUND",owned_foreground(),flush=True)
        except Exception as error:
            print("L08_TEXTBOX_CURSOR_POSITIVE_CONTROL_ERROR",
                  type(error).__name__,flush=True)
        reference=classify_l08_cursor_reference(
            owned_edit_hit,text_cursor,
            tuple(observation[1] for observation in cursor_observations))
        print("L08_CURSOR_REFERENCE_CLASSIFICATION",reference,
              "OWNED_EDIT",owned_edit_hit,flush=True)
        body=element(pane_prefix+"Files").rectangle()
        sendinput_mouse_move(coords=(body.left+30,body.top+40))
        window().set_focus()
        eventually(owned_foreground,"owned window is not foreground for final capture",3)
        rect=window().rectangle()
        after=root/("detail-columns-right-after.png" if pane=="right"
                    else "detail-columns-after.png")
        ImageGrab.grab(
            bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(after)
        print("L08_OWNED_PANE",pane,flush=True)
        print("OWNED_DETAIL_COLUMN_NAME_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_TYPE_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_SIZE_RESIZE",True,flush=True)
        print("OWNED_DETAIL_COLUMN_VISUALS",before.name,after.name,flush=True)
        print("L08_CURSOR_ORACLE_OBSERVATIONS",cursor_observations,flush=True)
        # A successful drag never overrides failed native cursor acceptance.
        assert len(cursor_observations)==3,"L08 cursor probes were skipped"
        for thumb_id,observed,current,owned_hit,event_help in cursor_observations:
            assert observed=="sizewe", (
                "L08 native horizontal resize cursor missing on owned handle",
                thumb_id,current,owned_hit,event_help)
        passed=True
    finally:
        if proc.poll() is None:
            # Verify the normal owned WinUI close path, not terminate().
            if hwnd is None:
                proc.terminate();proc.wait(timeout=8)
            else:
                # Scope all native probes to this test-owned HWND/PID. Query
                # liveness with bounded WM_NULL, never SendMessage(WM_CLOSE),
                # UIA, or an unbounded cross-thread wait during teardown.
                user32.IsWindow.argtypes=[wintypes.HWND]
                user32.IsWindow.restype=wintypes.BOOL
                user32.GetWindowThreadProcessId.argtypes=[
                    wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
                user32.GetWindowThreadProcessId.restype=wintypes.DWORD
                user32.SendMessageTimeoutW.argtypes=[
                    wintypes.HWND,wintypes.UINT,wintypes.WPARAM,
                    wintypes.LPARAM,wintypes.UINT,wintypes.UINT,
                    ctypes.POINTER(ctypes.c_size_t)]
                user32.SendMessageTimeoutW.restype=wintypes.LPARAM
                user32.PostMessageW.argtypes=[
                    wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
                user32.PostMessageW.restype=wintypes.BOOL
                def owned_shutdown_state():
                    if proc.poll() is not None:return ("exited",)
                    if not user32.IsWindow(hwnd):return ("hwnd-destroyed",)
                    process_id=wintypes.DWORD()
                    thread_id=user32.GetWindowThreadProcessId(
                        hwnd,ctypes.byref(process_id))
                    if not thread_id or process_id.value!=proc.pid:
                        return ("hwnd-no-longer-owned",)
                    native_result=ctypes.c_size_t()
                    responsive=bool(user32.SendMessageTimeoutW(
                        hwnd,0,0,0,0x0003,200,ctypes.byref(native_result)))
                    return ("owned-hwnd", "responsive" if responsive else "blocked")
                owner=owned_shutdown_state()
                posted=bool(user32.PostMessageW(hwnd,0x10,0,0)) if (
                    owner[0]=="owned-hwnd") else False
                print("G01_OWNED_WM_CLOSE_POSTED",posted,
                      "PRESTATE",owner,flush=True)
                if posted:
                    began=time.monotonic()
                    # Monotonic deadlines preserve the existing 13s close
                    # budget and identify a blocked native UI thread.
                    for deadline in (.25,1.0,3.0,7.0,13.0):
                        remaining=deadline-(time.monotonic()-began)
                        if remaining>0:
                            try:proc.wait(timeout=remaining)
                            except subprocess.TimeoutExpired:pass
                        if proc.poll() is not None:
                            print("G01_OWNED_WM_CLOSE_EXIT_MS",
                                  int((time.monotonic()-began)*1000),
                                  flush=True)
                            break
                        print("G01_OWNED_WM_CLOSE_TIMELINE",
                              "DEADLINE_MS",int(deadline*1000),
                              "STATE",owned_shutdown_state(),flush=True)
                if proc.poll() is None:
                    close_timed_out=True
                    print("OWNED_DETAIL_COLUMN_CLOSE_TIMEOUT",True,
                          "POSTED",posted,
                          "STATE",owned_shutdown_state(),flush=True)
                    # Preserve the original failure while safely terminating
                    # only this exact test-owned child process.
                    proc.terminate();proc.wait(timeout=5)
        print("OWNED_DETAIL_COLUMN_EXIT",proc.returncode,flush=True)
        # Read only the bounded, test-owned phase trace. Do not read user
        # TEMP, untrusted links, native dumps or arbitrary crash records.
        allowed_close_phases={
            "APPWINDOW_CLOSING_ENTER","APPWINDOW_CLOSING_EXIT",
            "WINDOW_CLOSED_ENTER","WINDOW_CLOSED_EXIT",
            "PREPARE_XAML_ENTER","PREPARE_XAML_ALREADY_CLOSING",
            "FOCUS_TARGET_TOOLTIP_DETACHED",
            "FOCUS_TARGET_TOOLTIP_DETACH_EXCEPTION",
            "VISUAL_TOOLTIP_SWEEP_LIMIT",
            "VISUAL_TOOLTIP_SWEEP_RELEASED",
            "VISUAL_TOOLTIP_SWEEP_EMPTY",
            "VISUAL_TOOLTIP_SWEEP_EXCEPTION",
            "FOCUS_TRANSFER_BEGIN","FOCUS_TRANSFER_EXCEPTION",
            "FOCUS_TRANSFER_SUCCEEDED","FOCUS_TRANSFER_REJECTED",
            "FOCUS_TRANSFER_DONE","PREPARE_XAML_EXIT",
            "FOCUS_BEFORE_TEXT_INPUT","FOCUS_BEFORE_OTHER",
            "FOCUS_BEFORE_NONE","FOCUS_BEFORE_QUERY_EXCEPTION",
            "FOCUS_AFTER_TEXT_INPUT","FOCUS_AFTER_OTHER",
            "FOCUS_AFTER_NONE","FOCUS_AFTER_QUERY_EXCEPTION",
            "PREPARE_CLOSE_ENTER","PREPARE_CLOSE_ALREADY_CLOSING",
            "QUEUED_XAML_TIMERS_STOPPED",
            "CURSOR_HOOKS_STOPPED","XAML_CONTROLS_RELEASED",
            "SESSION_CLOSE_PREPARED","CONTROLLERS_CLOSE_PREPARED",
            "WORKSPACE_ROUTES_INVALIDATED","SHELL_NAV_SHUTDOWN_DONE",
            "PREPARE_CLOSE_EXIT","MAINWINDOW_DESTRUCTOR_ENTER",
            "MAINWINDOW_DESTRUCTOR_EXIT",
            "APP_DESTRUCTOR_ENTER","APP_DESTRUCTOR_BODY_EXIT",
            "NATIVE_CLOSE_AV_ENTER","NATIVE_CLOSE_AV_EXIT",
        }
        # Test-owned VEH records no raw pointers, exception parameters,
        # stack memory, user strings, or unrestricted module names.
        native_close_frame=re.compile(
            r"NATIVE_CLOSE_AV_FRAME_0[0-7]_"
            r"(?:FLY|XAML|COMBASE|COREMSG|NTDLL|OTHER)_[0-9A-F]{8}")
        trace_name=f"fly-g01-close-{proc.pid}.log"
        trace_files=(owned/"tmp"/trace_name,owned/"temp"/trace_name)
        trace_found=False
        for trace in trace_files:
            if (not trace.is_file() or trace.is_symlink() or
                trace.stat().st_size>4096):
                continue
            lines=trace.read_text(encoding="ascii").splitlines()
            if len(lines)>64 or any(
                    line not in allowed_close_phases and
                    native_close_frame.fullmatch(line) is None
                    for line in lines):
                # Keep rejected traces rejected. Publish only a fixed reason,
                # never private phase text, user paths or raw exception data.
                reason=("phase-count-exceeded" if len(lines)>64
                        else "unrecognized-phase")
                print("G01_OWNED_CLOSE_PHASE_TRACE_INVALID",True,
                      "REASON",reason,flush=True)
                continue
            print("G01_OWNED_CLOSE_PHASE_TRACE",
                  ",".join(lines),flush=True)
            trace_found=True
        if not trace_found:
            print("G01_OWNED_CLOSE_PHASE_TRACE_MISSING",True,flush=True)
        safe=all((mfc/n).is_file() and
            hashlib.sha256((mfc/n).read_bytes()).digest()==h
            for n,h in old.items())
        print("SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL",safe,flush=True)
        if passed and safe and proc.returncode==0 and not close_timed_out:
            assert owned.parent==root and owned.name.startswith("columns-gui-owned-")
            assert not owned.is_symlink()
            shutil.rmtree(owned)
            print("OWNED_COLUMN_RESIZE_FIXTURE_REMOVED",True,flush=True)
        else:
            print("OWNED_COLUMN_RESIZE_DIAGNOSTIC_FIXTURE_RETAINED",owned,flush=True)
        if close_timed_out and sys.exc_info()[0] is None:
            # Report a standalone close defect, but never replace an earlier
            # cursor/drag assertion with the secondary shutdown failure.
            raise RuntimeError("PX10 owned WinUI did not close normally")
    return 0 if passed and safe and proc.returncode==0 and not close_timed_out else 1

if __name__=="__main__":
    try:
        result=main(sys.argv[1] if len(sys.argv)>1 else "Release",
                    sys.argv[2] if len(sys.argv)>2 else "left")
    except Exception:
        import traceback
        traceback.print_exc()
        print("OWNED_DETAIL_COLUMN_RESULT FAIL",flush=True)
        sys.exit(1)
    print("OWNED_DETAIL_COLUMN_RESULT "+("PASS" if result==0 else "FAIL"),
          flush=True)
    sys.exit(result)
