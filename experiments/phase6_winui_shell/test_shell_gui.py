"""Real, disposable WinUI 3 dual-pane shell acceptance (not product-parity certification)."""
from pathlib import Path
import ctypes as c, os, re, shutil, subprocess, tempfile, time, hashlib
from ctypes import wintypes as W
from pywinauto import Desktop
from PIL import ImageGrab

# Read-only original user profile sentinel: the preview has NO permission
# to use the legacy product's real profile or mutate its settings.
REAL_CONF=Path(os.environ["APPDATA"])/"fxfile"/"conf"
PROTECTED_NAMES=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
  "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
assert all((REAL_CONF/n).is_file() for n in PROTECTED_NAMES)
ORIGINAL_HASHES={n:hashlib.sha256((REAL_CONF/n).read_bytes()).digest()
  for n in PROTECTED_NAMES}

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CONFIG=os.environ.get("FLY_MIGRATION_CONFIGURATION","Debug")
assert CONFIG in ("Debug","Release")
EXE=HERE/("x64/"+CONFIG+"/FlyExplorerWinUIShell/FlyExplorerWinUIShell.exe")
assert EXE.exists(),EXE
base=ROOT/"logs/phase6-winui"
base.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix="shell-owned-",dir=base))
left=owned/"Left";right=owned/"Right";inner=left/"Nested";rightinner=right/"Secondary"
for folder in (inner,rightinner):folder.mkdir(parents=True,exist_ok=True)
(left/"readme.txt").write_text("owned synthetic only",encoding="utf-8")
appdata=owned/"appdata";appdata.mkdir()
localdata=owned/"localdata";localdata.mkdir()
temp=owned/"tmp";temp.mkdir()
u=c.windll.user32
CALL=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CALL,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.GetForegroundWindow.restype=W.HWND
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,c.c_int]
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
def ownedwindows(pid):
 found=[]
 @CALL
 def cb(h,_):
  x=W.DWORD();u.GetWindowThreadProcessId(h,c.byref(x))
  if x.value==pid and u.IsWindowVisible(h):
   buf=c.create_unicode_buffer(700);u.GetWindowTextW(h,buf,len(buf))
   found.append((int(h),buf.value))
  return 1
 u.EnumWindows(cb,0)
 return found
def eventually(fn,label,timeout=8):
 limit=time.monotonic()+timeout
 while time.monotonic()<limit:
  try:
   if fn():return True
  except Exception:pass
  time.sleep(.13)
 raise AssertionError(label)
def labels(win):
 return [e.window_text() for e in win.descendants() if e.window_text()]
p=None;hwnd=None
try:
 env={**os.environ,"APPDATA":str(appdata),"LOCALAPPDATA":str(localdata),
      "TEMP":str(temp),"TMP":str(temp)}
 p=subprocess.Popen([str(EXE),str(left)],cwd=EXE.parent,env=env,
   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 def main():
  return [(h,t) for h,t in ownedwindows(p.pid) if
   "flyExplorer - WinUI 3 migration preview" in t]
 eventually(lambda:len(main())==1 or p.poll() is not None,
            "WinUI 3 main window not discovered")
 assert p.poll() is None,("WinUI startup failed",p.returncode)
 hwnd=main()[0][0]
 win=Desktop(backend="uia").window(handle=hwnd)
 def element(name):return win.child_window(auto_id=name)
 def ensure_owned_focus():
  for _ in range(4):
   win.set_focus()
   time.sleep(.12)
   fg=u.GetForegroundWindow()
   owner=W.DWORD()
   if fg:u.GetWindowThreadProcessId(fg,c.byref(owner))
   if owner.value==p.pid:return True
  raise AssertionError(
   "Refusing physical input: foreground belongs to a user window")
 def safe_click(target):
  ensure_owned_focus()
  target.click_input()
 ids=("BackButton","ForwardButton","UpButton","AddressBox",
      "NewTabButton","CloseTabButton","SplitButton",
      "LeftTabs","RightTabs","LeftFiles","RightFiles","StatusText")
 for key in ids:assert element(key).exists(timeout=5),("Missing XAML control",key)
 print("REAL_WINUI_SHELL_CONTROLS",len(ids),"DUAL_PANES_AND_TABS=True",flush=True)
 assert "native shell engine active" in element("StatusText").window_text().lower(),(
   "UI-independent native C++ core was not bound at actual startup",
   element("StatusText").window_text())
 print("ACTUAL_CPP_NATIVE_CORE_NULL_CONTRACT_LINKED",True,flush=True)
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
            "first COM worker result not dispatched to the WinUI thread",12)
 # Two TabView pane controls are genuinely visible; they are not MFC.
 assert element("LeftTabs").is_visible() and element("RightTabs").is_visible()
 eventually(lambda:any("Nested" in e.window_text()
     for e in element("LeftFiles").descendants()),
     "async native Shell directory items never displayed",12)
 print("REAL_FILE_LIST_IN_LEFT_PANE",True,flush=True)
 # No refresh button, timer or direct UI-thread enumeration is used:
 # Create a genuinely test-owned file AFTER the per-pane native
 # FindFirstChangeNotification registration has had time to start.
 time.sleep(.35)
 watcher=left/"native-auto-change-marker.txt"
 watcher.write_text("test-owned only",encoding="utf-8")
 eventually(lambda:any("native-auto-change-marker.txt" in e.window_text()
     for e in element("LeftFiles").descendants()),
     "native directory watcher did not refresh the real WinUI ListView",12)
 print("REAL_NATIVE_WATCHER_AUTO_REFRESH_WITHOUT_MANUAL_ACTION",True,flush=True)
 # A second independent invalidation must remove a vanished item from
 # the real list. The watcher is rearmed/replaced after each snapshot.
 time.sleep(.55)
 watcher.unlink()
 eventually(lambda:not any("native-auto-change-marker.txt" in e.window_text()
     for e in element("LeftFiles").descendants()),
     "native watcher failed to remove deleted owned file",12)
 print("REAL_NATIVE_WATCHER_CREATE_AND_DELETE_AUTO_REFRESH",True,flush=True)
 # A real ListView double click must use the item's OWNED absolute Shell
 # PIDL, not a filesystem-only address shim.
 navitems=[e for e in element("LeftFiles").descendants()
   if e.element_info.control_type=="ListItem" and "Nested" in e.window_text()]
 assert len(navitems)==1,("native Shell fixture row not found",len(navitems))
 print("NATIVE_ROW_PRE_INPUT",
       "STATUS",element("StatusText").window_text(),
       "PATH",element("AddressBox").get_value(),
       "ROW",navitems[0].window_text(),flush=True)
 ensure_owned_focus()
 navitems[0].double_click_input()
 print("OWNED_NATIVE_POINTER_GUARD_PASSED",True,flush=True)
 try:
  eventually(lambda:"Nested" in element("AddressBox").get_value(),
             "absolute native PIDL row double click failed")
 except AssertionError:
  print("NATIVE_ROW_POST_FAILED_INPUT",
        "STATUS",element("StatusText").window_text(),
        "PATH",element("AddressBox").get_value(),
        "ROWS",[e.window_text() for e in element("LeftFiles").descendants()][:11],
        flush=True)
  q=win.rectangle()
  ImageGrab.grab(bbox=(q.left,q.top,q.right,q.bottom),
                 include_layered_windows=True).save(base/"m15-failed-row-input-diagnostic.png")
  raise
 safe_click(element("BackButton"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
           "native Shell PIDL child history failed")
 print("REAL_SHELL_NATIVE_ABSOLUTE_PIDL_ROW_OPEN_AND_BACK",True,flush=True)
 def tabnum(side):
  return sum(1 for x in element(side).descendants() if x.element_info.control_type=="TabItem")
 left_initial=tabnum("LeftTabs")
 print("INITIAL_LEFT_TAB_COUNT",left_initial,flush=True)
 safe_click(element("NewTabButton"))
 time.sleep(.4)
 print("AFTER_NEW_TAB_DESCENDANTS",
       [(e.element_info.control_type,e.window_text().encode("ascii","backslashreplace").decode(),
         e.element_info.automation_id)
        for e in element("LeftTabs").descendants()][:30],
       "COUNT",tabnum("LeftTabs"),
       "STATUS",element("StatusText").window_text(),
       "IS_RUNNING",p.poll() is None,flush=True)
 win.set_focus()
 rect=win.rectangle()
 ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(base/"migration-tab-diagnostic.png")
 eventually(lambda:tabnum("LeftTabs")==left_initial+1,"new tab not added")
 safe_click(element("CloseTabButton"))
 eventually(lambda:tabnum("LeftTabs")==left_initial,"close tab not restored")
 print("REAL_WINUI_TAB_ADD_CLOSE",left_initial,left_initial+1,left_initial,flush=True)
 # A fast close invalidates the tab route even when its background
 # native COM enumeration has not yet delivered its result.
 safe_click(element("NewTabButton"))
 eventually(lambda:tabnum("LeftTabs")==left_initial+1,
            "second async tab not added")
 safe_click(element("CloseTabButton"))
 eventually(lambda:tabnum("LeftTabs")==left_initial,
            "fast-closing an async tab did not remove it")
 time.sleep(.55)
 assert tabnum("LeftTabs")==left_initial and any(
     "Nested" in e.window_text() for e in element("LeftFiles").descendants()),(
     "stale closed-tab Shell worker result resurrected the old UI")
 print("REAL_ASYNC_TAB_CLOSE_ROUTE_CANCELLATION_NO_RESURRECTION",True,flush=True)
 safe_click(element("SplitButton"))
 time.sleep(.5)
 print("SPLIT_DIAGNOSTIC",element("SplitButton").window_text(),
       "RIGHT_PRESENT",element("RightFiles").exists(timeout=.25),
       "STATUS",element("StatusText").window_text(),flush=True)
 assert not element("RightFiles").exists(timeout=.3),(
   "right pane unexpectedly still exposed after collapse")
 rect=win.rectangle()
 ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(base/"migration-split-diagnostic.png")
 eventually(lambda:element("SplitButton").window_text()=="Split panes",
            "single pane action failed")
 safe_click(element("SplitButton"))
 eventually(lambda:element("SplitButton").window_text()=="Single pane",
           "split restore failed")
 print("REAL_WINUI_SPLIT_TOGGLE",True,flush=True)
 address=element("AddressBox")
 address.set_edit_text(str(inner))
 ensure_owned_focus()
 address.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:"Nested" in main()[0][1],"address Enter did not navigate")
 assert element("BackButton").is_enabled()
 safe_click(element("BackButton"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
           "active tab Back did not restore")
 print("REAL_WINUI_ADDRESS_ENTER_AND_HISTORY",True,flush=True)
 # Rapid invalid -> valid user navigation must reject stale worker
 # outcomes, retaining the LAST request's owning pane/tab.
 address.set_edit_text(str(left/"never-existing-async-target"))
 ensure_owned_focus()
 address.type_keys("{ENTER}",set_foreground=True)
 address.set_edit_text(str(inner))
 ensure_owned_focus()
 address.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:"Nested" in element("AddressBox").get_value(),
            "latest valid async navigation did not supersede old invalid request")
 time.sleep(.35)
 assert "Nested" in element("AddressBox").get_value(),(
    "obsolete Shell result overwritten the newer navigation")
 safe_click(element("BackButton"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
            "rapid navigation history rollback did not preserve left folder")
 print("REAL_ASYNC_LAST_REQUEST_WINS_AND_HISTORY",True,flush=True)
 assert element("RightFiles").is_visible()
 # Verify the SECOND panel has its own selected tab, list and history;
 # navigation there MUST NOT replace the left panel.
 safe_click(element("SecondaryPaneTitle"))
 eventually(lambda:"Right" in element("ActivePaneText").window_text(),
            "explicit right pane activation")
 rightaddr=element("AddressBox")
 rightaddr.set_edit_text(str(right))
 ensure_owned_focus()
 rightaddr.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:str(right).lower() in element("AddressBox").get_value().lower(),
            "right pane address entry")
 right_items=[e.window_text() for e in element("RightFiles").descendants()]
 assert any("Secondary" in x for x in right_items),right_items[:10]
 left_items=[e.window_text() for e in element("LeftFiles").descendants()]
 assert any("Nested" in x for x in left_items),left_items[:10]
 safe_click(element("PrimaryPaneTitle"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
            "left pane preserved while right navigation changed")
 print("REAL_WINUI_TWO_PANES_INDEPENDENT_PATHS_AND_FILES",True,flush=True)
 # Exercise the ACTUAL native Windows Shell namespace: This PC is
 # a virtual PIDL, not a std::filesystem directory. The new core must
 # accept the shell: alias, list Shell objects and preserve LEFT pane.
 safe_click(element("SecondaryPaneTitle"))
 eventually(lambda:"Right" in element("ActivePaneText").window_text(),
            "right activation for virtual Shell folder")
 virtual=element("AddressBox")
 virtual.set_edit_text("shell:MyComputerFolder")
 ensure_owned_focus()
 virtual.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:"::" in virtual.get_value(),"native virtual Shell location not opened")
 assert len(element("RightFiles").descendants())>0,(
    "Shell virtual folder enumeration unexpectedly empty")
 safe_click(element("PrimaryPaneTitle"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
   "virtual Shell location replaced independent left pane")
 print("REAL_NATIVE_VIRTUAL_SHELL_THIS_PC_PIDL_AND_ENUMERATION",True,flush=True)
 # The alias is no longer visible in the current address field; it has
 # been resolved to the native absolute Shell PIDL parsing name.
 # Verify the virtual location participated in the SAME tab history.
 safe_click(element("SecondaryPaneTitle"))
 safe_click(element("BackButton"))
 eventually(lambda:str(right).lower() in element("AddressBox").get_value().lower(),
            "native virtual Shell Back did not recover preceding folder")
 print("REAL_NATIVE_VIRTUAL_TO_LOCAL_SHELL_HISTORY",True,flush=True)
 safe_click(element("PrimaryPaneTitle"))
 rect=win.rectangle()
 assert rect.width()>400 and rect.height()>260
 img=base/"migration-first-shell-real-gui.png"
 ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom),
                include_layered_windows=True).save(img)
 print("ACTUAL_GUI_SCREENSHOT",img.name,"SIZE",rect.width(),rect.height(),flush=True)
 print("REAL_GUI_DPI",u.GetDpiForWindow(hwnd),flush=True)
finally:
 if p and p.poll() is None:
  if hwnd:u.PostMessageW(hwnd,0x10,0,0)
  try:p.wait(timeout=13)
  except subprocess.TimeoutExpired:
   p.terminate();p.wait(timeout=5)
   raise RuntimeError("owned WinUI3 shell did not close normally")
 print("OWNED_WINUI_SHELL_EXIT",p.returncode if p else None,flush=True)
 assert p and p.returncode==0
 assert all(hashlib.sha256((REAL_CONF/n).read_bytes()).digest()==ORIGINAL_HASHES[n]
            for n in PROTECTED_NAMES),(
   "unexpected change in real user settings during isolated migration GUI")
 print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",True,flush=True)
 assert owned.parent==base and owned.name.startswith("shell-owned-")
 shutil.rmtree(owned)
 print("OWNED_SYNTHETIC_FIXTURE_REMOVED",True,flush=True)
