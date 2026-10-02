"""Real, disposable WinUI 3 dual-pane shell acceptance (not product-parity certification)."""
from pathlib import Path
from paths import ROOT, APP, app_exe
import ctypes as c, os, re, shutil, subprocess, tempfile, time, hashlib
from ctypes import wintypes as W
from pywinauto import Desktop
from PIL import ImageGrab
from profile_guard import (assert_legacy_profile_unchanged, present_count,
                           snapshot_legacy_profile)

# Read-only original user profile sentinel: the preview has NO permission
# to use the legacy product's real profile or mutate its settings.
REAL_CONF,ORIGINAL_PROFILE=snapshot_legacy_profile()
ORIGINAL_PROFILE_PRESENT=present_count(ORIGINAL_PROFILE)

HERE=APP
CONFIG=os.environ.get("FLY_MIGRATION_CONFIGURATION","Debug")
assert CONFIG in ("Debug","Release")
EXE=app_exe(CONFIG)
assert EXE.exists(),EXE
base=ROOT/"logs/phase6-winui"
base.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix="shell-owned-",dir=base))
left=owned/"Left";right=owned/"Right";inner=left/"Nested";rightinner=right/"Secondary"
for folder in (inner,rightinner):folder.mkdir(parents=True,exist_ok=True)
(left/"readme.txt").write_text("owned synthetic only",encoding="utf-8")
if os.environ.get("FLY_M23_OWNED_FEATURES")=="YES":
 (left/"끌기.txt").write_text("owned M23 drag-copy",encoding="utf-8")
if os.environ.get("FLY_M22_OWNED_FEATURES")=="YES":
 for name,value in (
   ("복사본.txt","owned copied"),
   ("작은.txt","x"),
   ("큰.txt","z"*12000),
   ("이동.txt","owned moved"),
   ("자료.txt","owned source")):
  (left/name).write_text(value,encoding="utf-8")
 (right/"자료.txt").write_text("preexisting right",encoding="utf-8")
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
 owned_block=os.environ.get("FLY_M17_OWNED_HANG")=="YES"
 owned_com=os.environ.get("FLY_M18_OWNED_COM_HANG")=="YES"
 owned_notify=os.environ.get("FLY_M18_OWNED_SHELL_NOTIFY")=="YES"
 owned_exhaust=os.environ.get("FLY_M18_EXHAUST_TIMEOUT")=="YES"
 loopback_unc=os.environ.get("FLY_M18_LOOPBACK_UNC")=="YES"
 assert not (owned_block and owned_com)
 if owned_block or owned_com:
  assert CONFIG=="Debug","owned fault injection is Debug-only"
 if owned_block:env["FLY_M16_OWNED_TEST_ONLY"]="YES"
 if owned_com or owned_exhaust:
  env["FLY_M18_OWNED_COM_TEST_ONLY"]="YES"
 if owned_notify:
  assert CONFIG=="Debug","owned namespace event test is Debug-only"
  env["FLY_M18_OWNED_SHELL_NOTIFY"]="YES"
 args=[str(EXE),str(left)]
 if owned_block:args.append("--m17-test-left-helper-hang")
 if owned_com:args.append("--m18-test-left-com-hang")
 if owned_exhaust:
  assert CONFIG=="Debug","exhausted COM probe is Debug-only"
  args.append("--m18-test-exhaust-com-on-virtual")
 if owned_notify:args.append("--m18-owned-shell-notification")
 p=subprocess.Popen(args,cwd=EXE.parent,env=env,
   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 def main():
  return [(h,t) for h,t in ownedwindows(p.pid) if
   "flyExplorer" in t]
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
 startup_status=element("StatusText").window_text().lower()
 # The isolated supervisor permits two bounded 4.5-second attempts. Leave
 # room for that recovery budget plus process/UIA publication without
 # changing the product's native deadline.
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
            "UI-independent native core/helper was not active at startup",18)
 assert "?? ?????" not in element("StatusText").window_text(),(
   "native helper committed the owned route but left an error status",
   element("StatusText").window_text())
 print("ACTUAL_CPP_NATIVE_CORE_NULL_CONTRACT_LINKED",True,flush=True)
 if owned_block or owned_com:
  eventually(lambda:any("Nested" in e.window_text()
      for e in element("RightFiles").descendants()),
      "right pane stalled when LEFT owned helper blocked",3)
  assert not any("Nested" in e.window_text()
      for e in element("LeftFiles").descendants()),(
      "left unexpectedly finished before test-owned block deadline")
  print("REAL_WINUI_RIGHT_PANE_PROGRESS_WHILE_LEFT_HELPER_BLOCKED",True,flush=True)
  eventually(lambda:"응답 지연 후 복구" in
      element("StatusText").window_text().lower(),
      "left helper timeout and restart never reached real WinUI",13)
  print("REAL_WINUI_LEFT_HELPER_TIMEOUT_AND_AUTOMATIC_RESTART",True,flush=True)
  if owned_com:
   print("REAL_WINUI_OWNED_COM_VTABLE_STALL_RECOVERED",True,flush=True)
 # Two TabView pane controls are genuinely visible; they are not MFC.
 assert element("LeftTabs").is_visible() and element("RightTabs").is_visible()
 eventually(lambda:any("Nested" in e.window_text()
     for e in element("LeftFiles").descendants()),
     "async native Shell directory items never displayed",12)
 print("REAL_FILE_LIST_IN_LEFT_PANE",True,flush=True)
 if os.environ.get("FLY_V7_WINDOW_TABS_ONLY")=="YES":
  from test_v7_window_tabs_gui import run as v7_tabs_run
  v7_tabs_run(win=win,element=element,safe_click=safe_click,
              focus=ensure_owned_focus,eventually=eventually,owned=owned,
              localdata=localdata,env=env,exe=EXE)
  print("REAL_V7_WINDOW_TABS_ONLY_COMPLETE",True,flush=True)
  raise SystemExit(0)
 if owned_exhaust:
  # Both COM attempts hang only inside test-owned helpers, AFTER a real
  # initial local folder has been committed. Check actual failure UX.
  safe_click(element("LeftFiles"))
  address=element("AddressBox")
  address.set_edit_text("shell:MyComputerFolder")
  ensure_owned_focus()
  address.type_keys("{ENTER}",set_foreground=True)
  eventually(lambda:"4.5초씩 두 번 응답하지" in
      element("StatusText").window_text().lower(),
      "exhausted COM child requests gave no meaningful error",14)
  assert any("Nested" in x.window_text()
      for x in element("LeftFiles").descendants())
  assert any("Nested" in x.window_text()
      for x in element("RightFiles").descendants())
  print("REAL_WINUI_BOTH_COM_TIMEOUTS_EXHAUSTED_PREVIOUS_FOLDERS_PRESERVED",
        True,flush=True)
  safe_click(element("LeftFiles"))
  eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
      "exhausted COM request discarded the old selected folder")
 if owned_notify:
  # Only an OWNED synthetic filesystem folder receives this Shell event.
  # Virtual This PC registration is enabled in the app but NOT faked globally.
  shell=c.WinDLL("shell32",use_last_error=True)
  shell.SHChangeNotify.argtypes=[c.c_long,c.c_uint,c.c_void_p,c.c_void_p]
  owned_path=c.c_wchar_p(str(left))
  time.sleep(.45)
  for attempt in range(4):
   shell.SHChangeNotify(0x1000,0x0005,
                        c.cast(owned_path,c.c_void_p),None)
   try:
    eventually(lambda:"폴더 변경 알림을 반영" in
        element("StatusText").window_text().lower(),
        "owned Shell notification did not reach WinUI",1.25)
    break
   except AssertionError:
    if attempt==3:raise
  print("REAL_WINUI_OWNED_SHELL_NAMESPACE_EVENT_REFRESH",True,flush=True)
 else:
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
 # A watcher refresh replaces native rows asynchronously. Re-resolve the
 # owned ListView until the stable Shell snapshot is visible instead of
 # treating the short UIA replacement window as a product navigation failure.
 eventually(lambda:len([e for e in element("LeftFiles").descendants()
   if e.element_info.control_type=="ListItem" and "Nested" in e.window_text()])==1,
   "native Shell fixture row did not settle after watcher refresh",8)
 navitems=[e for e in element("LeftFiles").descendants()
   if e.element_info.control_type=="ListItem" and "Nested" in e.window_text()]
 assert len(navitems)==1,("native Shell fixture row not found",len(navitems))
 print("NATIVE_ROW_PRE_INPUT",
       "STATUS",element("StatusText").window_text(),
       "PATH",element("AddressBox").get_value(),
       "ROW",navitems[0].window_text(),flush=True)
 ensure_owned_focus()
 # Focus acquisition can rebuild the WinUIA peer after watcher invalidation;
 # resolve the exact owned row again immediately before the physical gesture.
 navitems=[e for e in element("LeftFiles").descendants()
   if e.element_info.control_type=="ListItem" and "Nested" in e.window_text()]
 assert len(navitems)==1,("native Shell fixture row lost before input",len(navitems))
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
 def original_tab_visible():
  return tabnum("LeftTabs")==left_initial and any(
      "Nested" in e.window_text() for e in element("LeftFiles").descendants())
 eventually(original_tab_visible,
            "closing async tab did not restore the original tab UI",4)
 # Give the closed route's worker ample time to report, then require the
 # restored original UI to remain intact. This separates UIA render latency
 # from the actual stale-result rejection assertion.
 time.sleep(1.2)
 assert original_tab_visible(),(
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
 eventually(lambda:element("SplitButton").window_text()=="분할 창",
            "single pane action failed")
 safe_click(element("SplitButton"))
 eventually(lambda:element("SplitButton").window_text()=="단일 창",
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
 # navigation there MUST NOT replace the left panel. The visual pane-title
 # button is intentionally retired; activate through an actual file row when
 # available so UIA does not land on ListView whitespace/scroll chrome.
 right_surface=element("RightFiles")
 right_item=next((x for x in right_surface.descendants()
                  if x.element_info.control_type=="ListItem"),None)
 safe_click(right_item or right_surface)
 eventually(lambda:"오른쪽" in element("ActivePaneText").window_text(),
            "explicit right pane activation")
 rightaddr=element("AddressBox")
 rightaddr.set_edit_text(str(right))
 ensure_owned_focus()
 rightaddr.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:str(right).lower() in element("AddressBox").get_value().lower(),
            "right pane address entry")
 # Typed address updates before out-of-process Shell response; require real
 # rows. Full M2.6 owned integration also has theme/search/session workers, so
 # allow the same bounded native helper more time without accepting address
 # text alone as success.
 def right_helper_ready():
  return any(e.element_info.control_type=="ListItem" and
             "Secondary" in e.window_text()
             for e in element("RightFiles").descendants())
 try:
  eventually(right_helper_ready,
      "right helper did not deliver real independent pane entries",20)
 except AssertionError:
  print("RIGHT_HELPER_DIAGNOSTIC",
        element("StatusText").window_text(),
        element("AddressBox").get_value(),
        [e.window_text() for e in element("RightFiles").descendants()[:12]],
        flush=True)
  raise
 right_items=[e.window_text() for e in element("RightFiles").descendants()]
 left_items=[e.window_text() for e in element("LeftFiles").descendants()]
 assert any("Nested" in x for x in left_items),left_items[:10]
 safe_click(element("LeftFiles"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
            "left pane preserved while right navigation changed")
 print("REAL_WINUI_TWO_PANES_INDEPENDENT_PATHS_AND_FILES",True,flush=True)
 # Exercise the ACTUAL native Windows Shell namespace: This PC is
 # a virtual PIDL, not a std::filesystem directory. The new core must
 # accept the shell: alias, list Shell objects and preserve LEFT pane.
 safe_click(element("RightFiles"))
 eventually(lambda:"오른쪽" in element("ActivePaneText").window_text(),
            "right activation for virtual Shell folder")
 virtual=element("AddressBox")
 virtual.set_edit_text("shell:MyComputerFolder")
 ensure_owned_focus()
 virtual.type_keys("{ENTER}",set_foreground=True)
 eventually(lambda:element("AddressBox").get_value()=="내 PC",
            "native virtual Shell location not opened")
 assert len(element("RightFiles").descendants())>0,(
    "Shell virtual folder enumeration unexpectedly empty")
 safe_click(element("LeftFiles"))
 eventually(lambda:str(left).lower() in element("AddressBox").get_value().lower(),
   "virtual Shell location replaced independent left pane")
 print("REAL_NATIVE_VIRTUAL_SHELL_THIS_PC_PIDL_AND_ENUMERATION",True,flush=True)
 # M2.6 shows the friendly label while the native model keeps the PIDL.
 # Verify the virtual location participated in the SAME tab history.
 safe_click(element("RightFiles"))
 safe_click(element("BackButton"))
 eventually(lambda:str(right).lower() in element("AddressBox").get_value().lower(),
            "native virtual Shell Back did not recover preceding folder")
 print("REAL_NATIVE_VIRTUAL_TO_LOCAL_SHELL_HISTORY",True,flush=True)
 if loopback_unc:
  # Nonexistent share on 127.0.0.1; no network configuration or live share changed.
  safe_click(element("RightFiles"))
  ensure_owned_focus()
  bad=element("AddressBox")
  bad.set_edit_text(r"\\127.0.0.1\flyexplorer-m18-owned-no-share")
  ensure_owned_focus()
  bad.type_keys("{ENTER}",set_foreground=True)
  eventually(lambda:any(x in element("StatusText").window_text().lower()
      for x in ("네트워크 폴더에 접근할 수 없거나","4.5초씩 두 번 응답하지")),
      "owned loopback UNC error did not explain the failure",15)
  assert any("Secondary" in row.window_text()
      for row in element("RightFiles").descendants()),(
      "failed loopback UNC changed previously accepted right folder")
  print("REAL_WINUI_LOOPBACK_UNC_REJECTED_WITH_PRIOR_FOLDER_PRESERVED",
        element("StatusText").window_text(),flush=True)
 if os.environ.get("FLY_OWNED_COMPACT_MONITOR_CASE")=="YES":
  # Reproduce the 720px work-area / y=78 / 634px free-height case
  # with this exact owned HWND; no desktop/user window is repositioned.
  assert os.environ.get("FLY_M19_OWNED_FEATURES")=="YES"
  assert u.GetSystemMetrics(0)>=1100 and u.GetSystemMetrics(1)>=740
  u.SetWindowPos.argtypes=[W.HWND,W.HWND,c.c_int,c.c_int,
                            c.c_int,c.c_int,W.UINT]
  assert u.SetWindowPos(hwnd,None,78,78,960,519,0x0014)
  eventually(lambda:abs(win.rectangle().height()-519)<=3,
             "owned compact-window placement did not take effect",5)
  print("M20_OWNED_COMPACT_PRE_M19",str(win.rectangle()),flush=True)
 if os.environ.get("FLY_M19_OWNED_FEATURES")=="YES":
  from test_m19_winui_features import run as run_m19
  run_m19(p=p,win=win,element=element,safe_click=safe_click,
          focus=ensure_owned_focus,eventually=eventually,
          ownedwindows=ownedwindows,
          left=left,right=right,inner=inner,
          owned=owned,localdata=localdata,env=env,exe=EXE)
 # Diagnostic only: distinguish a post-M19 expanded-panel layout from
 # the same M20 native command test on an otherwise independent window.
 if os.environ.get("FLY_M20_OWNED_COLLAPSE_M19_PANELS")=="YES":
  assert os.environ.get("FLY_M19_OWNED_FEATURES")=="YES"
  for button,child in (("SearchPanelButton","SearchScopeBox"),
                       ("WorkspacePanelButton","WorkspaceFileBox")):
   if element(child).exists(timeout=.3):
    safe_click(element(button))
    eventually(lambda:not element(child).exists(timeout=.2),
      "owned M19 panel did not collapse: "+child,6)
  print("M20_TEST_OWNED_M19_PANELS_COLLAPSED",True,flush=True)
 if os.environ.get("FLY_M20_OWNED_SHELL")=="YES":
  if os.environ.get("FLY_OWNED_LAYOUT_DIAG")=="YES":
   observed=[]
   for key in ("SearchPanelButton","SearchScopeBox","WorkspacePanelButton",
               "ThisPCButton","SidebarView","LeftFiles","StatusText"):
    try:
     control=element(key).wrapper_object()
     observed.append((key,str(control.rectangle()),control.is_visible()))
    except Exception as err:
     observed.append((key,type(err).__name__))
   print("M20_PANEL_LAYOUT_PRETEST",str(win.rectangle()),observed,flush=True)
  from test_m20_shell_gui import run as m20_run
  m20_run(win=win,element=element,safe_click=safe_click,
          focus=ensure_owned_focus,eventually=eventually,owned=owned)
 if os.environ.get("FLY_V7_WINDOW_TABS")=="YES":
  from test_v7_window_tabs_gui import run as v7_tabs_run
  v7_tabs_run(win=win,element=element,safe_click=safe_click,
              focus=ensure_owned_focus,eventually=eventually,owned=owned,
              localdata=localdata,env=env,exe=EXE)
 if os.environ.get("FLY_M21_OWNED_FEATURES")=="YES":
  from test_m21_gui import run as m21_run
  m21_run(p=p,win=win,element=element,safe_click=safe_click,
          focus=ensure_owned_focus,eventually=eventually,
          left=left,right=right,localdata=localdata,env=env,exe=EXE)
 if os.environ.get("FLY_M22_OWNED_FEATURES")=="YES":
  from test_m22_gui import run as m22_run
  m22_run(win=win,element=element,safe_click=safe_click,
          focus=ensure_owned_focus,eventually=eventually,left=left,right=right)
 if os.environ.get("FLY_M23_OWNED_FEATURES")=="YES":
  from test_m23_gui import run as m23_run
  m23_run(win=win,element=element,safe_click=safe_click,
          focus=ensure_owned_focus,eventually=eventually,
          left=left,right=right,localdata=localdata,env=env,exe=EXE)
 safe_click(element("LeftFiles"))
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
 assert_legacy_profile_unchanged(REAL_CONF,ORIGINAL_PROFILE)
 print("LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,
       "PRESENT",ORIGINAL_PROFILE_PRESENT,flush=True)
 if ORIGINAL_PROFILE_PRESENT==6:
  print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",True,flush=True)
 else:
  print("ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL","NOT_APPLICABLE",
        "PRESENT",ORIGINAL_PROFILE_PRESENT,flush=True)
 assert owned.parent==base and owned.name.startswith("shell-owned-")
 shutil.rmtree(owned)
 print("OWNED_SYNTHETIC_FIXTURE_REMOVED",True,flush=True)
