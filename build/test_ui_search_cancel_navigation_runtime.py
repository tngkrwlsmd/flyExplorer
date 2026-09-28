"""Owned 96-DPI modal/dialog-versus-address popup regression."""
from pathlib import Path
import ctypes as c, hashlib, os, re, shutil, subprocess, tempfile, time, sys
from ctypes import wintypes as w
from PIL import ImageGrab

ROOT=Path(__file__).resolve().parents[1]
MODE='light' if '--light' in sys.argv else 'dark'
SOURCE=Path(os.environ["APPDATA"])/"fxfile"/"conf"
NAMES=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
folder=Path(tempfile.mkdtemp(prefix="ui02-modal-owned-",dir=ROOT/"logs"))
conf=folder/"conf";conf.mkdir()
for name in NAMES: shutil.copy2(SOURCE/name,conf/name)
raw=(conf/"fxfile.conf").read_bytes()
enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
settings=raw.decode(enc)
for key in ("config.global_hotkey.enable","config.global_hotkey.show_tray","config.global_hotkey.windows_startup","config.register_shell_context_menu","config.single_process","config.theme_mode"):
 val=("1" if MODE=="light" else "2") if key=="config.theme_mode" else "0"
 settings,n=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",lambda m:m.group(1)+val,settings)
 assert n==1,key
(conf/"fxfile.conf").write_bytes(settings.encode(enc))
(fold:=folder/"fixture").mkdir()
for i in range(26): (fold/("item-%02d"%i)).mkdir()
(folder/"appdata").mkdir()
resource=(ROOT/"src/fxfile/resource.h").read_text(errors="replace")
command=int(re.search(r"(?m)^#define\s+ID_VIEW_COLUMN_SET\s+(\d+)",resource).group(1))
user=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):_fields_=[(k,c.c_long) for k in ("left","top","right","bottom")]
class CI(c.Structure):
 _fields_=[("cbSize",w.DWORD),("rcItem",RECT),("rcButton",RECT),("stateButton",w.DWORD),("hwndCombo",w.HWND),("hwndItem",w.HWND),("hwndList",w.HWND)]
user.EnumWindows.argtypes=(CALLBACK,w.LPARAM)
user.EnumChildWindows.argtypes=(w.HWND,CALLBACK,w.LPARAM)
user.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
user.GetComboBoxInfo.argtypes=(w.HWND,c.POINTER(CI))
user.GetWindowRect.argtypes=(w.HWND,c.POINTER(RECT))
user.GetWindowLongW.argtypes=(w.HWND,c.c_int)
user.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
user.SendMessageW.restype=c.c_ssize_t
user.GetWindow.argtypes=(w.HWND,w.UINT)
user.GetWindow.restype=w.HWND
class ScrollInfo(c.Structure):
 _fields_=[("size",w.DWORD),("rc",RECT),("line",c.c_int),("top",c.c_int),
          ("bottom",c.c_int),("reserve",c.c_int),("states",w.DWORD*6)]
user.GetScrollBarInfo.argtypes=(w.HWND,c.c_long,c.POINTER(ScrollInfo))
user.GetScrollBarInfo.restype=w.BOOL
def get_pid(hwnd):
 p=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(p));return p.value
def title(hwnd):
 b=c.create_unicode_buffer(160);user.GetWindowTextW(hwnd,b,160);return b.value
def cls(hwnd):
 b=c.create_unicode_buffer(90);user.GetClassNameW(hwnd,b,90);return b.value
def rect(hwnd):
 r=RECT();user.GetWindowRect(hwnd,c.byref(r));return (r.left,r.top,r.right,r.bottom)
def win_all(pid):
 found=[]
 @CALLBACK
 def cb(hwnd,_):
  if get_pid(hwnd)==pid and user.IsWindowVisible(hwnd):found.append(int(hwnd))
  return True
 user.EnumWindows(cb,0);return found
def intersect(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]

from pywinauto import mouse,keyboard
from PIL import ImageGrab
user.GetDlgItem.argtypes=(w.HWND,c.c_int)
user.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
user.SendMessageW.restype=c.c_ssize_t
res=(ROOT/"src/fxfile/resource.h").read_text(errors="replace")
def rid(name):
 return int(re.search(r"(?m)^#define\s+"+re.escape(name)+r"\s+(\d+)",res).group(1))

from pywinauto import keyboard,mouse,Desktop
user.GetDlgItem.argtypes=(w.HWND,c.c_int)
def wtext(h):
 b=c.create_unicode_buffer(2000)
 user.SendMessageW(h,0x000D,1999,c.addressof(b))
 return b.value
def setedit(h,value):
 user.SetForegroundWindow(dialog)
 rc=rect(h);mouse.click(coords=((rc[0]+rc[2])//2,(rc[1]+rc[3])//2))
 keyboard.send_keys("^a",pause=.014)
 keyboard.send_keys(value,with_spaces=True,pause=.008,vk_packet=True)
 time.sleep(.12)
 assert wtext(h)==value,("actual keyboard input failed",wtext(h),value)
def childlists(h):
 found=[]
 @CALLBACK
 def cb(hwnd,_):
  if cls(hwnd)=="SysListView32":found.append(int(hwnd))
  return True
 user.EnumChildWindows(h,cb,0);return found
def new_dialog(pid):
 return [h for h in win_all(pid) if h!=main and cls(h)=="#32770"]
proc=None;main=0;dialog=0;hook=0
mode="cancel" if "--cancel" in sys.argv else "navigate"
try:
 private=fold
 nested=private/"owned-search-target-parent"
 nested.mkdir()
 owned_file=nested/"owned-location-file.txt"
 owned_file.write_text("private owned search target",encoding="utf-8")
 if mode=="cancel":
  # No external volumes or changes to original settings. Large, owned
  # sparse/zero-filled text is scanned by the actual Release worker.
  # Creating only TWO files avoids thousands of redundant filesystem ops.
  for i in range(2):
   with (private/("owned-slow-content-%d.txt"%i)).open("wb") as fd:
    fd.truncate(160*1024*1024)
  print("CANCEL_PRIVATE_TEXT_FILE_COUNT=2 BYTES_EACH=167772160",flush=True)
 (folder/"appdata").mkdir(exist_ok=True)
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(private)],
         cwd=folder,env={**os.environ,"APPDATA":str(folder/"appdata")},
         stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(85):
  wins=[h for h in win_all(proc.pid) if title(h).endswith(" - fxfile")]
  if len(wins)==1:main=wins[0];break
  time.sleep(.12)
 assert main
 user.SetForegroundWindow(main)
 assert user.PostMessageW(main,0x111,34014,0)
 for _ in range(65):
  ds=new_dialog(proc.pid)
  if len(ds)==1:dialog=ds[0];break
  time.sleep(.12)
 assert dialog
 loc=user.GetDlgItem(dialog,rid("IDC_SEARCH_LOC"))
 name=user.GetDlgItem(dialog,rid("IDC_SEARCH_NAME"))
 start=user.GetDlgItem(dialog,rid("IDC_SEARCH_START"))
 textedit=user.GetDlgItem(dialog,rid("IDC_SEARCH_TEXT"))
 recursive=user.GetDlgItem(dialog,rid("IDC_SEARCH_SUBFOLDER"))
 assert all((loc,name,start,textedit,recursive))
 assert str(private).lower() in wtext(loc).lower(),(
    "refuse non-owned search target",repr(wtext(loc)))
 original_button=wtext(start)
 print("OWNED_SEARCH_ROOT_VERIFIED=True MODE",mode,flush=True)
 if mode=="navigate":
  if not user.SendMessageW(recursive,0x00F0,0,0):
   rr=rect(recursive);mouse.click(coords=(rr[0]+10,(rr[1]+rr[3])//2))
  assert user.SendMessageW(recursive,0x00F0,0,0)==1
  setedit(name,owned_file.name)
  import pythoncom
  status=user.GetDlgItem(dialog,rid("IDC_SEARCH_STATUS_BAR"))
  assert status
  events=[]
  initial_accessible=Desktop(backend="uia").window(handle=status).element_info.name
  print("NATIVE_STATUS_INITIAL_UIA_NAME",
        initial_accessible.encode("ascii","backslashreplace").decode(),flush=True)
  PROCTYPE=c.WINFUNCTYPE(None,w.HANDLE,w.DWORD,w.HWND,c.c_long,c.c_long,w.DWORD,w.DWORD)
  @PROCTYPE
  def callback(handle,event,hwnd,obj,child,thread,ms):
   if int(hwnd)==int(status):
    events.append((int(event),int(obj),int(child)))
  user.SetWinEventHook.argtypes=(w.DWORD,w.DWORD,w.HMODULE,PROCTYPE,w.DWORD,w.DWORD,w.DWORD)
  user.SetWinEventHook.restype=w.HANDLE
  user.UnhookWinEvent.argtypes=(w.HANDLE,)
  hook=user.SetWinEventHook(0x800C,0x800E,None,callback,proc.pid,0,0)
  assert hook,"owned accessibility listener unavailable"
  prior=set(childlists(main))
  rr=rect(start);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  result=0
  for _ in range(75):
   pythoncom.PumpWaitingMessages()
   fresh=[h for h in childlists(main) if h not in prior]
   if fresh and user.SendMessageW(fresh[-1],0x1004,0,0)==1 and wtext(start)==original_button:
    result=fresh[-1];break
   time.sleep(.1)
  for _ in range(10):
   pythoncom.PumpWaitingMessages()
   time.sleep(.02)
  accessible=Desktop(backend="uia").window(handle=status).element_info.name
  print("NATIVE_STATUS_ACCESSIBILITY","EVENTS",events[:6],
        "UIA_NAME",accessible.encode("ascii","backslashreplace").decode(),
        "HWND_TEXT",wtext(status).encode("ascii","backslashreplace").decode(),
        flush=True)
  assert any(event==0x800C and obj==-4 and child==0
             for event,obj,child in events),(
         "real OS name-change accessibility event absent",events)
  assert accessible and "1" in accessible,(
         "UIA status name not readable after native completion",repr(accessible))
  assert wtext(status) and "1" in wtext(status),(
         "native custom status HWND still has no spoken summary")
  assert result,("no owned search-result tab with one file",
                 [(h,int(user.SendMessageW(h,0x1004,0,0))) for h in childlists(main)])
  assert (not [h for h in new_dialog(proc.pid) if h!=dialog])
  # A real user can close the modeless Search window and operate the
  # already-created search result tab without launching file contents.
  user.UnhookWinEvent(hook);hook=0
  user.PostMessageW(dialog,0x10,0,0)
  for _ in range(65):
   if not user.IsWindow(dialog):break
   time.sleep(.08)
  assert not user.IsWindow(dialog)
  dialog=0
  assert user.IsWindow(result) and user.IsWindowVisible(result)
  row=Desktop(backend="win32").window(handle=result).wrapper_object().get_item(0).rectangle()
  print("OWNED_RESULT_ITEM_RECT",(row.left,row.top,row.right,row.bottom),flush=True)
  rc=rect(result);cx=rc[0]+(row.left+min(row.right,180))//2;cy=rc[1]+(row.top+row.bottom)//2
  user.SetForegroundWindow(main)
  mouse.click(coords=(cx,cy))
  selected=user.SendMessageW(result,0x102C,0,0x0002) # LVM_GETITEMSTATE LVIS_SELECTED
  assert selected&2,("result file was not selected by real mouse click",selected)
  mouse.click(button="right",coords=(cx,cy))
  popup=[]
  for _ in range(28):
   popup=[h for h in win_all(proc.pid) if cls(h)=="#32768"]
   if popup:break
   time.sleep(.09)
  assert popup,"native Shell context menu not displayed for owned result"
  print("OWNED_RESULT_NATIVE_CONTEXT_MENU_VISIBLE=True",flush=True)
  user.GetMenuItemCount.argtypes=(w.HMENU,)
  user.GetMenuItemCount.restype=c.c_int
  user.GetMenuStringW.argtypes=(w.HMENU,w.UINT,c.c_wchar_p,c.c_int,w.UINT)
  user.GetMenuStringW.restype=c.c_int
  for pop in popup:
   mh=int(user.SendMessageW(pop,0x01E1,0,0))
   n=user.GetMenuItemCount(mh) if mh else -1
   entries=[]
   for j in range(min(5,max(0,n))):
    buf=c.create_unicode_buffer(150)
    user.GetMenuStringW(mh,j,buf,149,0x400)
    entries.append(buf.value.encode("ascii","backslashreplace").decode())
   print("NATIVE_MENU_DIAGNOSTIC",rect(pop),n,entries,flush=True)
  try:
   uia=Desktop(backend="uia").window(handle=popup[-1]).descendants()
   print("NATIVE_MENU_UIA_ITEMS",
     [x.element_info.name.encode("ascii","backslashreplace").decode()[:85]
      for x in uia if x.element_info.control_type=="MenuItem"][:9],
     flush=True)
  except Exception as ex:
   print("MENU_UIA_UNAVAILABLE",repr(ex)[:90],flush=True)
  from PIL import ImageGrab
  pr=rect(popup[-1])
  if pr[2]>pr[0] and pr[3]>pr[1] and pr[2]-pr[0]<900:
   ImageGrab.grab(bbox=pr,include_layered_windows=True).save(
       folder/"owned-result-popup.png")

  # SearchResultCtrl::OnContextMenu inserts its own OPEN_PARENT_FOLDER
  # command at FIRST position of the native Shell context popup.
  # The native first item has been verified as Open parent folder by
  # GetMenuStringW above. Click its *actual screen rectangle* rather
  # than assuming keyboard HOME is delivered to the Shell popup.
  first_item=next((x for x in uia if
      x.element_info.control_type=="MenuItem"),None)
  assert first_item,"native Open parent item not exposed for real clicking"
  item_rc=first_item.rectangle()
  print("NATIVE_OPEN_PARENT_MENU_ITEM_RECT",
        (item_rc.left,item_rc.top,item_rc.right,item_rc.bottom),flush=True)
  assert item_rc.left>=pr[0] and item_rc.right<=pr[2]
  mouse.click(coords=(item_rc.left+min(85,(item_rc.right-item_rc.left)//2),
                      (item_rc.top+item_rc.bottom)//2))

  navigated=False
  for _ in range(55):
   if "owned-search-target-parent" in title(main).lower():
    navigated=True;break
   time.sleep(.14)
  if not navigated:
   visible_edits=[]
   @CALLBACK
   def cb(h,_):
    if cls(h) in ("Edit","ComboBox") and user.IsWindowVisible(h):
     val=wtext(h)
     if val and ("fixture" in val.lower() or "owned-search" in val.lower()):
      visible_edits.append((cls(h),val.encode("ascii","backslashreplace").decode()[:115]))
    return 1
   user.EnumChildWindows(main,cb,0)
   print("POST_MENU_NATIVE_ADDRESS_VALUES",visible_edits[:8],
         "REMAINING_POPUPS",
         [(cls(h),rect(h)) for h in win_all(proc.pid) if cls(h)=="#32768"],
         flush=True)
   print("POST_MENU_MAIN_TITLE",title(main).encode("ascii","backslashreplace").decode(),
        "OPEN_WINDOWS",[(cls(h),title(h).encode("ascii","backslashreplace").decode()[:48])
                        for h in win_all(proc.pid)][:9],flush=True)
  assert navigated,("native Open parent folder command did not navigate",
                    title(main))
  assert owned_file.is_file(),"private result file unexpectedly changed"
  print("REAL_SEARCH_RESULT_OPEN_PARENT_FOLDER_GUI_PASS=True",
        "MAIN_TITLE",title(main).encode("ascii","backslashreplace").decode(),
        flush=True)
 else:
  setedit(name,"owned-slow-*.txt")
  setedit(textedit,"absent-test-token")
  # Do not rely on IDCANCEL: SearchDlg deliberately disables Close
  # during a running search; the UI's actual cancellation is the
  # same IDC_SEARCH_START button relabelled Stop while active.
  start_rc=rect(start)
  cx=(start_rc[0]+start_rc[2])//2
  cy=(start_rc[1]+start_rc[3])//2
  user.SetForegroundWindow(dialog)
  mouse.click(coords=(cx,cy))
  active=False
  for _ in range(130):
   if wtext(start)!=original_button:
    active=True;break
   time.sleep(.008)
  if not active:
   print("REAL_ACTIVE_SEARCH_CANCEL_NOT_TESTED=workload_completed_before_Stop",
         flush=True)
  else:
   assert user.IsWindowEnabled(start),"actual Stop command unexpectedly disabled"
   assert not user.IsWindowEnabled(user.GetDlgItem(dialog,2)), (
      "Close must be disabled while native search is active")
   print("ACTUAL_NATIVE_SEARCH_STOP_STATE_OBSERVED=True",flush=True)
   # Real pointer input, not WM_COMMAND or a fabricated status variable.
   mouse.click(coords=(cx,cy))
   restored=False
   for _ in range(90):
    if wtext(start)==original_button and user.IsWindowEnabled(user.GetDlgItem(dialog,2)):
     restored=True;break
    time.sleep(.075)
   assert restored,"real Stop action did not return to idle Search"
   assert not [h for h in new_dialog(proc.pid) if h!=dialog], (
     "stop left unexpected modal dialog")
   print("REAL_ACTIVE_SEARCH_CANCEL_STOP_GUI_PASS=True",flush=True)
finally:
 if hook:user.UnhookWinEvent(hook)
 if proc and proc.poll() is None:
  if dialog and user.IsWindow(dialog):
   user.PostMessageW(dialog,0x10,0,0)
  if main and user.IsWindow(main):
   user.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=18)
  except subprocess.TimeoutExpired:
   proc.terminate();proc.wait(timeout=7)
 if mode=="cancel":
  for i in range(2):
   owned=fold/("owned-slow-content-%d.txt"%i)
   if owned.is_file() and owned.stat().st_size==160*1024*1024:
    owned.unlink()  # Only test-owned files made in this exact fixture.
 after={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("SIX_USER_CONFIGURATION_SHA_UNCHANGED",after==before,
       "OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert proc is not None and proc.returncode==0 and after==before
