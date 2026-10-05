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
    until(lambda:bool(windows(p.pid)) or p.poll() is not None,
          "filter preset window missing",18)
    assert p.poll() is None,p.returncode
    hwnd=windows(p.pid)[0]
    u.SetWindowPos(hwnd,0,90,55,1060,760,0x0040)
    win=Desktop(backend="uia").window(handle=hwnd)
    until(lambda:str(folder).lower() in
          win.child_window(auto_id="AddressBox").get_value().lower(),
          "initial owned folder did not settle",18)
    return p,hwnd,win

try:
    p,hwnd,win=launch()
    if BASELINE:
        capture=os.environ.get("FLY_FILTER_PRESET_SCREENSHOT")
        if capture:
            rect=win.rectangle()
            ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(capture)
        u.PostMessageW(hwnd,0x0010,0,0)
        p.wait(timeout=12)
        assert p.returncode==0,p.returncode
        assert_legacy_profile_unchanged(real_conf,before)
        print("FILTER_PRESET_BASELINE_CAPTURE_PASS",True,flush=True)
        raise SystemExit(0)

    win.child_window(auto_id="FilterRulePanelButton").click_input()
    for key in ("FilterRuleManagerBox","FilterRuleNameEdit",
                "FilterRuleMasksEdit","FilterRuleNewButton","FilterRuleSaveButton",
                "FilterRuleApplyButton","FilterRuleDeleteButton"):
        assert win.child_window(auto_id=key).exists(timeout=5),key
    name=win.child_window(auto_id="FilterRuleNameEdit")
    masks=win.child_window(auto_id="FilterRuleMasksEdit")
    name.set_edit_text("코드 파일")
    masks.set_edit_text("*.cpp; *.h")
    win.child_window(auto_id="FilterRuleSaveButton").click_input()
    preset_file=profile/"filter-rules-v1.txt"
    status=win.child_window(auto_id="StatusText")
    until(lambda:"필터 프리셋을 저장했습니다." in status.window_text() and
          preset_file.is_file(),
          "preset save did not reach durable success state",8)
    saved=preset_file.read_text(encoding="utf-8")
    assert "코드 파일\t*.cpp;*.h" in saved,saved
    win.child_window(auto_id="FilterRuleApplyButton").click_input()
    until(lambda:any("alpha.cpp" in t for t in row_texts(win)) and
          any("beta.h" in t for t in row_texts(win)) and
          all("notes.txt" not in t for t in row_texts(win)),
          "wildcard preset did not filter pane",10)
    print("FILTER_PRESET_SAVE_APPLY_MASK_PASS",True,flush=True)

    filt=win.child_window(auto_id="LeftNameFilterBox")
    files=win.child_window(auto_id="LeftFiles")
    files.set_focus()
    keyboard.send_keys("^+f")
    until(lambda:filt.has_keyboard_focus(),
          "Ctrl+Shift+F did not focus the pane name filter",5)
    keyboard.send_keys("note")
    until(lambda:filt.get_value()=="note",
          "keyboard substring filter input did not reach the editor",5)
    until(lambda:any("notes.txt" in t for t in row_texts(win)) and
          all("alpha.cpp" not in t for t in row_texts(win)),
          "legacy substring filter compatibility failed",10)
    print("FILTER_PRESET_SUBSTRING_COMPAT_PASS",True,flush=True)

    capture=os.environ.get("FLY_FILTER_PRESET_SCREENSHOT")
    if capture:
        rect=win.rectangle()
        ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
            include_layered_windows=True).save(capture)

    u.PostMessageW(hwnd,0x0010,0,0);p.wait(timeout=12);assert p.returncode==0
    p2,hwnd2,win2=launch()
    win2.child_window(auto_id="FilterRulePanelButton").click_input()
    name2=win2.child_window(auto_id="FilterRuleNameEdit")
    masks2=win2.child_window(auto_id="FilterRuleMasksEdit")
    until(lambda:name2.get_value()=="코드 파일" and
          masks2.get_value()=="*.cpp;*.h",
          "saved preset did not survive restart",8)
    win2.child_window(auto_id="FilterRuleApplyButton").click_input()
    until(lambda:any("alpha.cpp" in t for t in row_texts(win2)) and
          all("notes.txt" not in t for t in row_texts(win2)),
          "persisted preset did not apply after restart",10)
    print("FILTER_PRESET_RESTART_PERSISTENCE_PASS",True,flush=True)
    win2.child_window(auto_id="FilterRuleDeleteButton").click_input()
    status2=win2.child_window(auto_id="StatusText")
    until(lambda:"필터 프리셋을 삭제했습니다." in status2.window_text(),
          "preset delete did not reach durable success state",8)
    deleted=preset_file.read_text(encoding="utf-8")
    assert deleted.strip()=="schema=1",deleted
    print("FILTER_PRESET_DELETE_PASS",True,flush=True)
    u.PostMessageW(hwnd2,0x0010,0,0);p2.wait(timeout=12);assert p2.returncode==0

    assert_legacy_profile_unchanged(real_conf,before)
    print("FILTER_PRESET_OWNED_GUI_EXIT_0",True,flush=True)
    print("FILTER_PRESET_LEGACY_PROFILE_UNCHANGED",True,flush=True)
finally:
    for key in ("p","p2"):
        proc=locals().get(key)
        if proc is not None and proc.poll() is None:
            proc.kill();proc.wait(timeout=5)
    shutil.rmtree(owned,ignore_errors=True)
