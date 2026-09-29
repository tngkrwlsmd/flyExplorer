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
proc=None;main=0;dlg=0
try:
 env={**os.environ,"APPDATA":str(folder/"appdata")}
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(fold)],cwd=folder,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)
 for _ in range(90):
  ms=[h for h in win_all(proc.pid) if title(h).endswith(" - fxfile")]
  if len(ms)==1:main=ms[0];break
  time.sleep(.12)
 assert main,"owned main window not visible"
 found=[]
 @CALLBACK
 def children(h,_):
  if cls(h)=="ComboBox" and user.IsWindowVisible(h):
   info=CI();info.cbSize=c.sizeof(CI)
   if user.GetComboBoxInfo(h,c.byref(info)) and info.hwndList:found.append(info)
  return True
 user.EnumChildWindows(main,children,0)
 assert found,"owned address combo missing"
 info=found[0];user.SendMessageW(info.hwndCombo,0x1701,3,0)
 user.SendMessageW(info.hwndCombo,0x14f,1,0)
 for _ in range(35):
  if user.IsWindowVisible(info.hwndList):break
  time.sleep(.1)
 assert user.IsWindowVisible(info.hwndList),"address popup did not open"
 time.sleep(.35)
 print("BEFORE_MODAL_ADDRESS_POPUP_VISIBLE",
       bool(user.IsWindowVisible(info.hwndList)),"MODE",MODE,flush=True)
 popup_scroll=ScrollInfo();popup_scroll.size=c.sizeof(popup_scroll)
 assert user.GetScrollBarInfo(info.hwndList,-5,c.byref(popup_scroll))
 popup_rc=(popup_scroll.rc.left,popup_scroll.rc.top,
           popup_scroll.rc.right,popup_scroll.rc.bottom)
 address_overlays=[h for h in win_all(proc.pid)
                   if "DarkScrollbar" in cls(h) and
                   abs(rect(h)[0]-popup_rc[0])<=2 and
                   abs(rect(h)[1]-popup_rc[1])<=2]
 print("PREMODAL_ADDRESS_SCROLL_OVERLAY_COUNT",len(address_overlays),
       "MODE",MODE,flush=True)
 if MODE=="dark":assert address_overlays,"address dark scrollbar missing before modal"
 else:assert not address_overlays,"unexpected address dark overlay in light"
 assert user.PostMessageW(main,0x111,command,0)
 for _ in range(70):
  dialogs=[h for h in win_all(proc.pid) if h!=main and cls(h)=="#32770" and title(h)]
  if dialogs:dlg=dialogs[0];break
  time.sleep(.1)
 assert dlg,("ColumnSet modal did not appear",[(cls(h),title(h)) for h in win_all(proc.pid)])
 # Opening the native modal must not cover the address bar when the
 # monitor has enough free vertical workspace for the dialog below it.
 user.GetParent.argtypes=(w.HWND,)
 user.GetParent.restype=w.HWND
 address=int(info.hwndCombo)
 for _ in range(5):
  if cls(address)=="ComboBoxEx32":break
  address=int(user.GetParent(address) or 0)
  if not address:break
 assert address and cls(address)=="ComboBoxEx32","address ComboBoxEx parent missing"
 addr_rect=rect(address)
 dlg_rect=rect(dlg)
 class MonitorInfo(c.Structure):
  _fields_=[("size",w.DWORD),("monitor",RECT),("work",RECT),("flags",w.DWORD)]
 user.MonitorFromWindow.argtypes=(w.HWND,w.DWORD)
 user.MonitorFromWindow.restype=c.c_void_p
 user.GetMonitorInfoW.argtypes=(c.c_void_p,c.POINTER(MonitorInfo))
 mon=MonitorInfo();mon.size=c.sizeof(mon)
 assert user.GetMonitorInfoW(user.MonitorFromWindow(dlg,2),c.byref(mon))
 gap=max(10,user.GetDpiForWindow(dlg)*10//96)
 room=addr_rect[3]+gap+(dlg_rect[3]-dlg_rect[1])<=mon.work.bottom-gap
 overlap=intersect(addr_rect,dlg_rect)
 print("MODAL_ADDRESS_GEOMETRY_OVERLAP",overlap,
       "CAN_AVOID",room,"ADDRESS_BOTTOM",addr_rect[3],
       "DIALOG_TOP",dlg_rect[1],flush=True)
 if room:assert not overlap,"column modal geometrically covers address row"
 time.sleep(.4)
 overlays=[h for h in win_all(proc.pid) if "DarkScrollbar" in cls(h)]
 leaked=[h for h in address_overlays
         if user.IsWindow(h) and user.IsWindowVisible(h)]
 popup_open=bool(user.IsWindowVisible(info.hwndList))
 print("MODAL_OWNER_MATCHES_MAIN",int(user.GetWindow(dlg,4) or 0)==main,
       "MODAL_DPI",user.GetDpiForWindow(dlg),flush=True)
 print("ADDRESS_POPUP_STILL_VISIBLE",popup_open,
       "ADDRESS_SCROLL_OVERLAY_STILL_VISIBLE",len(leaked),flush=True)
 assert not popup_open and not leaked, "native address dropdown leaked into modal"
 list_id=int(re.search(r"(?m)^#define\s+IDC_COLUMN_LIST\s+(\d+)",resource).group(1))
 lv=int(user.GetDlgItem(dlg,list_id))
 assert lv and cls(lv)=="SysListView32","modal list missing"
 lr=rect(lv)
 pic=ImageGrab.grab(bbox=lr).convert("RGB")
 pic.save(folder/("column-list-"+MODE+".png"))
 samples=[pic.getpixel((x,y))
          for y in range(32,max(33,pic.height-6),5)
          for x in range(18,max(19,pic.width-28),8)]
 dark_ratio=sum(max(rgb)<110 for rgb in samples)/len(samples)
 print("MODAL_LIST_DARK_SAMPLE_RATIO",round(dark_ratio,3),"MODE",MODE,flush=True)
 if MODE=="dark":assert dark_ratio>.5,"modal list retains white surface in Dark"
 else:assert dark_ratio<.25,"modal list unexpectedly dark in Light"

 # Read the real separate SysHeader32 screen area: checking the list alone
 # previously missed an all-white header in the shipped dark dialog.
 user.SendMessageW.restype=c.c_ssize_t
 header=int(user.SendMessageW(lv,0x101f,0,0)) # LVM_GETHEADER
 assert header and cls(header)=="SysHeader32","real list header missing"
 hr=rect(header)
 hp=ImageGrab.grab(bbox=hr).convert("RGB")
 hp.save(folder/("column-header-"+MODE+".png"))
 hs=[hp.getpixel((x,y)) for y in range(2,max(3,hp.height-2),3)
     for x in range(10,max(11,hp.width-12),9)]
 hratio=sum(max(rgb)<110 for rgb in hs)/len(hs)
 print("MODAL_HEADER_DARK_SAMPLE_RATIO",round(hratio,3),"MODE",MODE,
       "HEADER_RECT",hr,flush=True)
 if MODE=="dark":assert hratio>.6,"column header remains bright in Dark"
 else:assert hratio<.25,"light-mode header unexpectedly dark"

 width_id=int(re.search(r"(?m)^#define\s+IDC_COLUMN_WIDTH\s+(\d+)",resource).group(1))
 edit=int(user.GetDlgItem(dlg,width_id))
 assert edit and cls(edit)=="Edit","selected column width input missing"
 ext=user.GetWindowLongW(edit,-20)&0xffffffff
 user.GetPropW.argtypes=(w.HWND,c.c_wchar_p);user.GetPropW.restype=c.c_void_p
 emphasized=bool(user.GetPropW(edit,"flyExplorer.ModernDialog.EmphasizedEdit"))
 print("WIDTH_EDIT_CLIENT_EDGE",bool(ext&0x200),
       "CONTRAST_EMPHASIS",emphasized,"WIDTH_PIXEL",rect(edit)[2]-rect(edit)[0],
       flush=True)
 assert ext&0x200 and emphasized, "numeric width input has no visible bordered style"
 assert rect(edit)[2]-rect(edit)[0]>=65, "numeric edit too narrow"

 # Pointer-select a real row, ensure its stored width is shown in the
 # edit field, then verify ordinary physical Ctrl+A/numeric typing works.
 from pywinauto import mouse, keyboard
 mouse.click(coords=(lr[0]+60,hr[3]+11))
 time.sleep(.2)
 shown=c.create_unicode_buffer(80)
 user.SendMessageW(edit,0x000D,80,c.addressof(shown)) # WM_GETTEXT marshals cross-process
 print("SELECTED_COLUMN_WIDTH_DISPLAY",repr(shown.value),"MODE",MODE,flush=True)
 assert shown.value.isdecimal(),"native row selection did not populate width"
 er=rect(edit)
 mouse.click(coords=((er[0]+er[2])//2,(er[1]+er[3])//2))
 keyboard.send_keys("^a128",pause=.04)
 time.sleep(.2)
 user.SendMessageW(edit,0x000D,80,c.addressof(shown)) # WM_GETTEXT marshals cross-process
 print("PHYSICAL_WIDTH_EDIT_AFTER_CTRL_A",repr(shown.value),"MODE",MODE,flush=True)
 assert shown.value=="128","numeric width input cannot be edited with Ctrl+A"

 # Actual keyboard input and actual OK in a disposable product process.
 # Use a NON-PINNED, currently visible size column: zero previously
 # committed as a zero-pixel real ExplorerCtrl column (reproduced bug).
 files=[]
 @CALLBACK
 def main_lists(h,_):
  if cls(h)=="SysListView32":files.append(int(h))
  return True
 user.EnumChildWindows(main,main_lists,0)
 assert files,"original product file list not found"
 active_list=files[0]
 start=user.SendMessageW(active_list,0x101d,1,0)
 assert start>0,"size column not present"
 cases=[("min_zero","0",start,24),
        ("max_overflow","99999",24,4096),
        ("invalid_alpha","abc",4096,4096)]
 for index,(case,typed,expected_before,expected_after) in enumerate(cases):
  if index:
   assert user.PostMessageW(main,0x111,command,0)
   dlg=0
   for _ in range(70):
    dialogs=[h for h in win_all(proc.pid)
             if h!=main and cls(h)=="#32770" and title(h)]
    if dialogs:dlg=dialogs[0];break
    time.sleep(.1)
   assert dlg,"real column modal did not reopen"
   lv=int(user.GetDlgItem(dlg,list_id))
   assert lv
   header=int(user.SendMessageW(lv,0x101f,0,0))
   hr=rect(header)
   lr=rect(lv)
   edit=int(user.GetDlgItem(dlg,width_id))
   er=rect(edit)
  mouse.click(coords=(lr[0]+60,hr[3]+33))
  time.sleep(.22)
  user.SendMessageW(edit,0x000D,80,c.addressof(shown))
  prior=int(shown.value) if shown.value.isdecimal() else -1
  native_before=user.SendMessageW(active_list,0x101d,1,0)
  print("COLUMN_BOUNDARY_BEFORE",case,prior,native_before,flush=True)
  assert native_before==expected_before,(case,native_before,expected_before)
  assert prior==expected_before,(case,prior,expected_before)
  mouse.click(coords=((er[0]+er[2])//2,(er[1]+er[3])//2))
  keyboard.send_keys("^a"+typed,pause=.04)
  time.sleep(.23)
  user.SendMessageW(edit,0x000D,80,c.addressof(shown))
  print("COLUMN_BOUNDARY_PHYSICAL_INPUT",case,repr(shown.value),flush=True)
  if typed!="abc":
   assert shown.value==typed,(case,"keyboard input mismatch")
  else:
   # ES_NUMBER blocks physical letters. Verify both the field and the real
   # ExplorerCtrl column remain unchanged; cancel the diagnostic modal.
   assert shown.value==str(expected_before),"native numeric Edit accepted letters"
   assert user.SendMessageW(active_list,0x101d,1,0)==expected_before
   print("COLUMN_INVALID_KEYBOARD_CHARACTERS_REJECTED=True",flush=True)
   assert user.PostMessageW(dlg,0x10,0,0)
   break
  ok=int(user.GetDlgItem(dlg,1))
  assert ok and cls(ok)=="Button"
  o=rect(ok)
  mouse.click(coords=((o[0]+o[2])//2,(o[1]+o[3])//2))
  for _ in range(55):
   if not user.IsWindow(dlg) and user.IsWindowEnabled(main):break
   time.sleep(.1)
  assert not user.IsWindow(dlg),"owned column modal did not close"
  time.sleep(.2)
  new_width=user.SendMessageW(active_list,0x101d,1,0)
  print("COLUMN_BOUNDARY_NATIVE_COMMITTED",case,new_width,
        "EXPECTED",expected_after,flush=True)
  assert new_width==expected_after,(case,new_width,expected_after)
 print("COLUMN_MIN_MAX_INVALID_PHYSICAL_GUI_PASS=True",flush=True)
 raise SystemExit(0)

 # A real pointer drag must change the native header's first column width.
 from pywinauto import mouse
 w_before=int(user.SendMessageW(lv,0x101d,0,0)) # LVM_GETCOLUMNWIDTH
 boundary=(hr[0]+w_before-1,(hr[1]+hr[3])//2)
 mouse.press(button="left",coords=boundary)
 mouse.move(coords=(boundary[0]+22,boundary[1]))
 time.sleep(.15)
 mouse.release(button="left",coords=(boundary[0]+22,boundary[1]))
 time.sleep(.25)
 w_after=int(user.SendMessageW(lv,0x101d,0,0))
 print("NATIVE_HEADER_DRAG_WIDTH",w_before,w_after,"MODE",MODE,flush=True)
 assert w_after>=w_before+8, "native header resize divider not draggable"

 scroll=ScrollInfo();scroll.size=c.sizeof(scroll)
 assert user.GetScrollBarInfo(lv,-5,c.byref(scroll)),"modal native vertical scrollbar not available"
 lb=(scroll.rc.left,scroll.rc.top,scroll.rc.right,scroll.rc.bottom)
 covering=[h for h in overlays if intersect(rect(h),lb)]
 print("MODAL_NATIVE_SCROLLBAR_RECT",lb,
       "DARK_OVERLAY_COVERING_LIST",len(covering),"MODE",MODE,flush=True)
 if MODE=="dark":assert covering,"modal list has no modern scrollbar overlay"
 else:assert not covering,"light modal should not use a dark overlay"
 from pywinauto import mouse
 top_before=user.SendMessageW(lv,0x1027,0,0)
 item_count=user.SendMessageW(lv,0x1004,0,0)
 per_page=user.SendMessageW(lv,0x1028,0,0)
 print("MODAL_SCROLL_DIAGNOSTIC_ITEMS",item_count,"PER_PAGE",per_page,
       "STATE",list(scroll.states),"FOREGROUND",int(user.GetForegroundWindow()),flush=True)
 coords=(lb[0]+min(7,max(1,(lb[2]-lb[0])//2)),
         lb[1]+7 if top_before>0 else lb[3]-7)
 mouse.click(coords=coords)
 time.sleep(.3)
 top_after=user.SendMessageW(lv,0x1027,0,0)
 if top_after==top_before:
  # One initial native click may only activate the modal's list.
  mouse.click(coords=coords)
  time.sleep(.3)
  top_after=user.SendMessageW(lv,0x1027,0,0)
 print("MODAL_NATIVE_SCROLL_CLICK",top_before,top_after,"MODE",MODE,flush=True)
 assert (top_after<top_before if top_before>0 else top_after>top_before), (
       "native modal scrollbar did not respond to pointer")
 ImageGrab.grab(bbox=rect(dlg)).save(folder/("column-modal-"+MODE+".png"))
 print("OWNED_MODAL_POPUP_SCROLL_REGRESSION_PASS",MODE,flush=True)
finally:
 if dlg and user.IsWindow(dlg):user.PostMessageW(dlg,0x10,0,0)
 if proc and proc.poll() is None:
  if main and user.IsWindow(main):user.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=9)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 after={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("ORIGINAL_SIX_CONFIGS_UNCHANGED",after==before,"OWNED_EXIT",None if proc is None else proc.returncode,flush=True)
 assert after==before and proc is not None and proc.returncode==0
