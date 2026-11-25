"""Owned WinUI acceptance for persistent pane filter presets."""
from pathlib import Path
from paths import ROOT, app_exe
from profile_guard import assert_legacy_profile_unchanged, snapshot_legacy_profile
from uia_polling import wait_until
import ctypes as c
import os,shutil,subprocess,tempfile,time
from ctypes import wintypes as W
from pywinauto import Desktop,keyboard
from PIL import ImageGrab

CONFIG=os.environ.get("FLY_MIGRATION_CONFIGURATION","Release")
BASELINE=os.environ.get("FLY_FILTER_PRESET_BASELINE")=="YES"
EXE=app_exe(CONFIG)
BASE=ROOT/"logs"/"filter-preset-owned";BASE.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix="filter-preset-",dir=BASE))
folder=owned/"필터대상";folder.mkdir()
for name in ("alpha.cpp","beta.h","notes.txt","photo1.JPG"):
    (folder/name).write_text("owned",encoding="utf-8")
appdata=owned/"appdata";localdata=owned/"localdata";temp=owned/"tmp"
for p in (appdata,localdata,temp):p.mkdir()
profile=localdata/"flyExplorer";profile.mkdir()
(profile/"ui-preferences-v1.txt").write_bytes(
    b"schema=2\r\nlanguage=ko-KR\r\ntheme=dark\r\nview=details\r\n")
real_conf,before=snapshot_legacy_profile()

u=c.windll.user32
CALL=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CALL,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.GetWindowThreadProcessId.restype=W.DWORD
u.GetForegroundWindow.restype=W.HWND
u.WindowFromPoint.argtypes=[W.POINT]
u.WindowFromPoint.restype=W.HWND
u.GetAncestor.argtypes=[W.HWND,W.UINT]
u.GetAncestor.restype=W.HWND
u.IsWindowVisible.argtypes=[W.HWND]
u.SetWindowPos.argtypes=[W.HWND,W.HWND,c.c_int,c.c_int,c.c_int,c.c_int,W.UINT]
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
launched=[]


def window_owner(hwnd):
    owner=W.DWORD()
    if hwnd and u.GetWindowThreadProcessId(hwnd,c.byref(owner)):
        return owner.value
    return 0


def require_foreground(proc,hwnd):
    assert proc.poll() is None and window_owner(hwnd)==proc.pid, "FILTER_PRESET_OWNED_WINDOW_LOST"
    assert u.GetForegroundWindow()==hwnd, "FILTER_PRESET_FOREGROUND_NOT_OWNED"


def owned_control(win,proc,key):
    control=win.child_window(auto_id=key)
    assert control.exists(timeout=5),key
    assert control.element_info.process_id==proc.pid, "FILTER_PRESET_CONTROL_NOT_OWNED: "+key
    assert control.is_visible() and control.is_enabled(), "FILTER_PRESET_CONTROL_NOT_READY: "+key
    return control


def click_owned(win,proc,hwnd,key):
    control=owned_control(win,proc,key)
    rect=control.rectangle()
    bounds=win.rectangle()
    assert (bounds.left<=rect.left<rect.right<=bounds.right and
            bounds.top<=rect.top<rect.bottom<=bounds.bottom), "FILTER_PRESET_CLICK_OUTSIDE_OWNED_WINDOW: "+key
    dx,dy=rect.width()//2,rect.height()//2
    require_foreground(proc,hwnd)
    hit=u.WindowFromPoint(W.POINT(rect.left+dx,rect.top+dy))
    assert hit and u.GetAncestor(hit,2)==hwnd and window_owner(hit)==proc.pid, "FILTER_PRESET_CLICK_POINT_NOT_OWNED: "+key
    require_foreground(proc,hwnd)
    print("FILTER_PRESET_CLICK_READY",key,flush=True)
    control.click_input(coords=(dx,dy))
    print("FILTER_PRESET_CLICK_DISPATCHED",key,flush=True)


def send_owned_keys(proc,hwnd,keys,control=None):
    if control is not None:
        assert control.element_info.process_id==proc.pid and control.has_keyboard_focus(), "FILTER_PRESET_KEYBOARD_FOCUS_LOST"
    require_foreground(proc,hwnd)
    keyboard.send_keys(keys)


def open_filter_panel(win,proc,hwnd):
    # One real click, no retry and no longer acceptance timeout.
    manager=win.child_window(auto_id="FilterRuleManagerBox")
    assert not (manager.exists(timeout=0) and manager.is_visible()), "FILTER_PRESET_PANEL_ALREADY_OPEN"
    click_owned(win,proc,hwnd,"FilterRulePanelButton")
    assert manager.exists(timeout=5), "FilterRuleManagerBox: FILTER_PRESET_PANEL_NOT_OBSERVED_AFTER_CLICK"
    assert manager.element_info.process_id==proc.pid and manager.is_visible(), "FILTER_PRESET_MANAGER_NOT_VISIBLE_OWNED"
    print("FILTER_PRESET_PANEL_OPENED",True,flush=True)


def close_owned(proc,hwnd):
    assert proc.poll() is None and window_owner(hwnd)==proc.pid, "FILTER_PRESET_CLOSE_NOT_OWNED"
    assert u.PostMessageW(hwnd,0x0010,0,0), "FILTER_PRESET_CLOSE_POST_FAILED"
    proc.wait(timeout=12)
    assert proc.returncode==0,proc.returncode

def windows(pid):
    out=[]
    @CALL
    def cb(hwnd,_):
        owner=W.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(owner))
        if owner.value==pid and u.IsWindowVisible(hwnd):out.append(int(hwnd))
        return 1
    u.EnumWindows(cb,0);return out
def until(fn,label,timeout=12):
    return wait_until(fn, label, seconds=timeout, interval=.15)
def row_texts(win):
    files=win.child_window(auto_id="LeftFiles")
    return [x.window_text() for x in files.descendants(control_type="ListItem")]

env={**os.environ,"APPDATA":str(appdata),"LOCALAPPDATA":str(localdata),
     "TEMP":str(temp),"TMP":str(temp)}
def launch():
    p=subprocess.Popen([str(EXE),str(folder)],cwd=EXE.parent,env=env,
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    launched.append(p)  # Track immediately, including failed startup.
    until(lambda:bool(windows(p.pid)) or p.poll() is not None,
          "filter preset window missing",18)
    assert p.poll() is None,p.returncode
    handles=windows(p.pid)
    assert len(handles)==1, "FILTER_PRESET_AMBIGUOUS_OWNED_WINDOW"
    hwnd=handles[0]
    assert window_owner(hwnd)==p.pid, "FILTER_PRESET_WINDOW_NOT_OWNED"
    assert u.SetWindowPos(hwnd,0,90,55,1060,760,0x0040), "FILTER_PRESET_WINDOW_POSITION_FAILED"
    win=Desktop(backend="uia").window(handle=hwnd)
    until(lambda:str(folder).lower() in
          win.child_window(auto_id="AddressBox").get_value().lower(),
          "initial owned folder did not settle",18)
    assert window_owner(hwnd)==p.pid and win.element_info.process_id==p.pid, "FILTER_PRESET_WINDOW_NOT_OWNED"
    win.set_focus()
    until(lambda:u.GetForegroundWindow()==hwnd or p.poll() is not None,
          "FILTER_PRESET_FOREGROUND_NOT_ACQUIRED",5)
    require_foreground(p,hwnd)
    return p,hwnd,win

try:
    p,hwnd,win=launch()
    if BASELINE:
        capture=os.environ.get("FLY_FILTER_PRESET_SCREENSHOT")
        if capture:
            require_foreground(p,hwnd)
            rect=win.rectangle()
            ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(capture)
        close_owned(p,hwnd)
        assert_legacy_profile_unchanged(real_conf,before)
        print("FILTER_PRESET_BASELINE_CAPTURE_PASS",True,flush=True)
        raise SystemExit(0)

    open_filter_panel(win,p,hwnd)
    for key in ("FilterRuleManagerBox","FilterRuleNameEdit",
                "FilterRuleMasksEdit","FilterRuleColorBox","FilterRuleIconBox",
                "FilterRuleNewButton","FilterRuleSaveButton",
                "FilterRuleApplyButton","FilterRuleDeleteButton"):
        assert win.child_window(auto_id=key).exists(timeout=5),key
    name=win.child_window(auto_id="FilterRuleNameEdit")
    masks=win.child_window(auto_id="FilterRuleMasksEdit")
    name.set_edit_text("코드 파일")
    masks.set_edit_text("*.cpp; *.h")
    colors=win.child_window(auto_id="FilterRuleColorBox")
    icons=win.child_window(auto_id="FilterRuleIconBox")
    colors.set_focus()
    until(lambda:colors.has_keyboard_focus(),
          "filter color selector did not receive keyboard focus",5)
    send_owned_keys(p,hwnd,"{HOME}{DOWN}",colors)
    until(lambda:colors.selected_text()=="파랑",
          "physical keyboard did not select blue classification",5)
    icons.set_focus()
    until(lambda:icons.has_keyboard_focus(),
          "filter icon selector did not receive keyboard focus",5)
    send_owned_keys(p,hwnd,"{HOME}{DOWN}",icons)
    until(lambda:icons.selected_text()=="별",
          "physical keyboard did not select star classification",5)
    save=win.child_window(auto_id="FilterRuleSaveButton")
    save.set_focus()
    until(lambda:save.has_keyboard_focus(),
          "filter save button not keyboard focusable",5)
    send_owned_keys(p,hwnd,"{ENTER}",save)
    preset_file=profile/"filter-rules-v1.txt"
    status=win.child_window(auto_id="StatusText")
    until(lambda:"필터 프리셋을 저장했습니다." in status.window_text() and
          preset_file.is_file(),
          "preset save did not reach durable success state",8)
    saved=preset_file.read_text(encoding="utf-8")
    assert "schema=2" in saved and "코드 파일\t*.cpp;*.h\t1\t1" in saved,saved
    click_owned(win,p,hwnd,"FilterRuleApplyButton")
    until(lambda:any("alpha.cpp" in t for t in row_texts(win)) and
          any("beta.h" in t for t in row_texts(win)) and
          all("notes.txt" not in t for t in row_texts(win)),
          "wildcard preset did not filter pane",10)
    until(lambda:any("필터 분류 아이콘" in x.window_text()
                     for x in win.child_window(auto_id="LeftFiles").descendants()),
          "styling badge not present in matching file rows",10)
    until(lambda:any(
          "분류 색상: 파랑" in t and "분류 아이콘: 별" in t
          for t in row_texts(win) if "alpha.cpp" in t),
          "UIA file row omits accessible style/color/icon meaning",8)
    until(lambda:any("필터 분류 아이콘: 별" in item.window_text()
                     for item in win.child_window(auto_id="LeftFiles").descendants()),
          "UIA classification glyph does not identify star badge",8)
    print("FILTER_PRESET_KEYBOARD_AND_UIA_SEMANTICS_PASS",True,flush=True)
    print("FILTER_PRESET_STYLED_BADGE_AND_SCHEMA2_PASS",True,flush=True)
    print("FILTER_PRESET_SAVE_APPLY_MASK_PASS",True,flush=True)

    filt=win.child_window(auto_id="LeftNameFilterBox")
    files=win.child_window(auto_id="LeftFiles")
    files.set_focus()
    send_owned_keys(p,hwnd,"^+f")
    until(lambda:filt.has_keyboard_focus(),
          "Ctrl+Shift+F did not focus the pane name filter",5)
    send_owned_keys(p,hwnd,"note",filt)
    until(lambda:filt.get_value()=="note",
          "keyboard substring filter input did not reach the editor",5)
    until(lambda:any("notes.txt" in t for t in row_texts(win)) and
          all("alpha.cpp" not in t for t in row_texts(win)),
          "legacy substring filter compatibility failed",10)
    print("FILTER_PRESET_SUBSTRING_COMPAT_PASS",True,flush=True)

    capture=os.environ.get("FLY_FILTER_PRESET_SCREENSHOT")
    if capture:
        require_foreground(p,hwnd)
        rect=win.rectangle()
        ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(capture)

    close_owned(p,hwnd)
    p2,hwnd2,win2=launch()
    open_filter_panel(win2,p2,hwnd2)
    name2=win2.child_window(auto_id="FilterRuleNameEdit")
    masks2=win2.child_window(auto_id="FilterRuleMasksEdit")
    until(lambda:name2.get_value()=="코드 파일" and
          masks2.get_value()=="*.cpp;*.h" and
          win2.child_window(auto_id="FilterRuleColorBox").selected_text()=="파랑" and
          win2.child_window(auto_id="FilterRuleIconBox").selected_text()=="별",
          "saved preset did not survive restart",8)
    click_owned(win2,p2,hwnd2,"FilterRuleApplyButton")
    until(lambda:any("alpha.cpp" in t for t in row_texts(win2)) and
          all("notes.txt" not in t for t in row_texts(win2)),
          "persisted preset did not apply after restart",10)
    print("FILTER_PRESET_RESTART_PERSISTENCE_PASS",True,flush=True)
    click_owned(win2,p2,hwnd2,"FilterRuleDeleteButton")
    status2=win2.child_window(auto_id="StatusText")
    until(lambda:"필터 프리셋을 삭제했습니다." in status2.window_text(),
          "preset delete did not reach durable success state",8)
    deleted=preset_file.read_text(encoding="utf-8")
    assert deleted.strip()=="schema=1",deleted
    print("FILTER_PRESET_DELETE_PASS",True,flush=True)
    close_owned(p2,hwnd2)

    assert_legacy_profile_unchanged(real_conf,before)
    print("FILTER_PRESET_OWNED_GUI_EXIT_0",True,flush=True)
    print("FILTER_PRESET_LEGACY_PROFILE_UNCHANGED",True,flush=True)
finally:
    for proc in launched:
        if proc.poll() is None:
            proc.kill();proc.wait(timeout=5)
    shutil.rmtree(owned,ignore_errors=True)
