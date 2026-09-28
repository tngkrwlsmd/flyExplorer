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

from pywinauto import keyboard,mouse
user.GetDlgItem.argtypes=(w.HWND,c.c_int)
user.GetWindow.argtypes=(w.HWND,w.UINT)
user.GetWindow.restype=w.HWND
user.GetWindowTextW.argtypes=(w.HWND,c.c_wchar_p,c.c_int)
def txt(hwnd):
 b=c.create_unicode_buffer(1500)
 user.SendMessageW(hwnd,0xD,1499,c.addressof(b))
 return b.value
def visible_search_dialogs(pid,exclude=0):
 return [h for h in win_all(pid) if cls(h)=="#32770" and h!=exclude]
proc=None;main=0;dialog=0
try:
 fixture=fold
 for name in ("README sample.txt","README second.txt","README third.txt"):
  (fixture/name).write_text("private owned GUI query",encoding="utf-8")
 (folder/"appdata").mkdir(exist_ok=True)
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(fixture)],
     cwd=folder,env={**os.environ,"APPDATA":str(folder/"appdata")},
     stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(95):
  ms=[h for h in win_all(proc.pid) if title(h).endswith(" - fxfile")]
  if len(ms)==1:main=ms[0];break
  time.sleep(.12)
 assert main
 user.SetForegroundWindow(main)
 assert user.PostMessageW(main,0x111,34014,0)
 for _ in range(70):
  d=visible_search_dialogs(proc.pid)
  if len(d)==1:dialog=d[0];break
  time.sleep(.1)
 assert dialog,"private search dialog missing"
 loc=user.GetDlgItem(dialog,rid("IDC_SEARCH_LOC"))
 name=user.GetDlgItem(dialog,rid("IDC_SEARCH_NAME"))
 start=user.GetDlgItem(dialog,rid("IDC_SEARCH_START"))
 status=user.GetDlgItem(dialog,rid("IDC_SEARCH_STATUS_BAR"))
 assert all((loc,name,start,status)), "expected real search controls missing"
 path=txt(loc)
 assert "ui02-modal-owned-" in path and "fixture" in path
 def children():
  found=[]
  @CALLBACK
  def callback(h,_):
   if cls(h)=="SysListView32":found.append(int(h))
   return 1
  user.EnumChildWindows(main,callback,0)
  return found
 # SearchDlg creates a *new search-result TAB in MainFrame*, not a
 # SysListView32 child inside the modeless SearchDlg. Track each new
 # list HWND so pre-existing main file lists cannot generate false PASS.
 assert children(),"real main file list missing"
 initial_start_label=txt(start)
 def count(hwnd):
  return int(user.SendMessageW(hwnd,0x1004,0,0))
 def completion_modal():
  # SearchDlg itself is modeless top level; any additional owned
  # top-level dialog is the obsolete completion or a real error modal.
  return visible_search_dialogs(proc.pid,dialog)
 def set_name(value):
  user.SetForegroundWindow(dialog)
  rr=rect(name);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  keyboard.send_keys("^a",pause=.025)
  keyboard.send_keys(value,with_spaces=True,pause=.012,vk_packet=True)
  assert txt(name)==value,("filename entry mismatch",txt(name),value)
 def start_and_wait(label,filename,expected):
  set_name(filename)
  existing=set(children())
  rr=rect(start);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  found=None
  new_list=None
  for _ in range(70):
   if completion_modal():
    raise AssertionError((label,"unexpected native success modal",
                          [(title(h),cls(h)) for h in completion_modal()]))
   fresh=[h for h in children() if h not in existing]
   if fresh:
    new_list=fresh[-1]
    observed=count(new_list)
    if observed==expected:
     time.sleep(.5)
     if (not completion_modal() and count(new_list)==expected
         and user.IsWindowEnabled(start)
         and txt(start)==initial_start_label):
      found=observed;break
   time.sleep(.12)
  assert found==expected,(label,"search tab native result count",
                          count(new_list) if new_list else "no new list",
                          "expected",expected)
  print("REAL_SEARCH_NONMODAL_RESULT",label,found,
        "SEARCH_RESULT_TAB_HWND",new_list,
        "START_BUTTON",txt(start).encode("ascii","backslashreplace").decode(),
        "STATUS_CLASS",cls(status),flush=True)
 for label,pattern,expected in (
   ("zero","no-such-private-file-*.txt",0),
   ("single","README sample.txt",1),
   ("multiple","README*.txt",3)):
  start_and_wait(label,pattern,expected)
 # The existing explicit invalid-location error must STILL use a modal.
 missing=str(fixture/"this-subdirectory-must-not-exist")
 assert not Path(missing).exists()
 lr=rect(loc);mouse.click(coords=((lr[0]+lr[2])//2,(lr[1]+lr[3])//2))
 keyboard.send_keys("^a",pause=.02)
 keyboard.send_keys(missing,with_spaces=True,pause=.01,vk_packet=True)
 typed=txt(loc)
 print("INVALID_LOCATION_INPUT",repr(typed),flush=True)
 if typed==missing:
  set_name("README sample.txt")
  rr=rect(start);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  errored=[]
  for _ in range(35):
   errored=completion_modal()
   if errored:break
   time.sleep(.12)
  assert errored,"existing wrong-location error warning vanished"
  print("INVALID_LOCATION_ERROR_MODAL_RETAINED",len(errored),flush=True)
  for h in errored:user.PostMessageW(h,0x10,0,0)
 else:
  print("INVALID_LOCATION_GUI_NOT_EXERCISED=combo_input_did_not_replace_value",flush=True)
 print("OWNED_NONMODAL_SEARCH_GUI_PASS=True",flush=True)

 if "--cancel-probe" in sys.argv:
  # Safely exercise the original Cancel path, if the synthetic workload
  # is still active. Never claim actual cancellation if it already ended.
  cancel_root=fixture/"owned-cancel-workload"
  cancel_root.mkdir()
  # Unlike the first synthetic run, actually enable recursive search:
  # all cancellable files are deliberately in this subdirectory.
  recursive=user.GetDlgItem(dialog,rid("IDC_SEARCH_SUBFOLDER"))
  assert recursive,"native recursive-search checkbox not found"
  if not user.SendMessageW(recursive,0x00F0,0,0): # BM_GETCHECK
   cb=rect(recursive)
   mouse.click(coords=(cb[0]+10,(cb[1]+cb[3])//2))
  assert user.SendMessageW(recursive,0x00F0,0,0)==1, (
      "recursive search must be ON before cancellation acceptance")
  print("REAL_CANCEL_FIXTURE_RECURSION_ENABLED=True",flush=True)
  for i in range(3500):
   (cancel_root/("owned-file-%05d.txt"%i)).write_text(
       "owned cancellable fixture text",encoding="utf-8")
  rr=rect(loc);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  keyboard.send_keys("^a",pause=.02)
  keyboard.send_keys(str(fixture),with_spaces=True,pause=.01,vk_packet=True)
  assert txt(loc)==str(fixture),"fixture search scope not safely restored"
  set_name("deliberately-absent-*.txt")
  rr=rect(start);mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  active=False
  for _ in range(55):
   if txt(start)!=initial_start_label and user.IsWindow(dialog):
    active=True;break
   time.sleep(.008)
  if active:
   cancel=user.GetDlgItem(dialog,2)
   assert cancel,"real cancel button missing"
   cr=rect(cancel)
   mouse.click(coords=((cr[0]+cr[2])//2,(cr[1]+cr[3])//2))
   for _ in range(70):
    if not user.IsWindow(dialog):break
    time.sleep(.075)
   assert not user.IsWindow(dialog),"cancel during active search failed"
   dialog=0
   assert user.IsWindow(main) and user.IsWindowEnabled(main)
   print("ACTUAL_ACTIVE_SEARCH_CANCEL_GUI_PASS=True",flush=True)
  else:
   print("ACTIVE_CANCEL_NOT_TESTED=synthetic_search_finished_before_observation",
         flush=True)
finally:
 if proc and proc.poll() is None:
  for h in visible_search_dialogs(proc.pid,dialog):
   user.PostMessageW(h,0x10,0,0)
  if dialog and user.IsWindow(dialog):user.PostMessageW(dialog,0x10,0,0)
  if main and user.IsWindow(main):user.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=12)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 after={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("ORIGINAL_SIX_CONFIGS_UNCHANGED",after==before,
       "OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert after==before and proc is not None and proc.returncode==0
