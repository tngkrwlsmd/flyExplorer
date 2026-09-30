"""Actual current-DPI keyboard/UIA and responsive sizes. NO global HC/DPI changes."""
import ctypes as c
from ctypes import wintypes as w
import hashlib,os,subprocess,sys,tempfile,time
from pathlib import Path
import psutil
from pywinauto import Desktop,keyboard

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
u=c.WinDLL("user32",use_last_error=True)
u.GetDpiForWindow.argtypes=(w.HWND,)
u.GetDpiForWindow.restype=w.UINT
u.GetForegroundWindow.restype=w.HWND
u.SetWindowPos.argtypes=(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)
class HIGHCONTRAST(c.Structure):
 _fields_=(("cbSize",w.UINT),("dwFlags",w.DWORD),
           ("lpszDefaultScheme",w.LPWSTR))
def high_contrast():
 x=HIGHCONTRAST();x.cbSize=c.sizeof(x)
 assert u.SystemParametersInfoW(0x0042,x.cbSize,c.byref(x),0)
 return bool(x.dwFlags&1)
def until(f,msg,seconds=18):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  try:
   if f():return
  except Exception:pass
  time.sleep(.2)
 raise AssertionError(msg)
def main(config="Debug"):
 a=Path(__file__).resolve().parent
 exe=a/"x64"/config/"FlyExplorerWinUIShell"/"FlyExplorerWinUIShell.exe"
 assert exe.is_file()
 root=a.parents[1]/"logs"/"m24";root.mkdir(parents=True,exist_ok=True)
 own=Path(tempfile.mkdtemp(prefix="accessibility-owned-",dir=root))
 folder=own/"source";folder.mkdir()
 filename=chr(0xD55C)+chr(0xAE00)+"-accessibility.txt"
 (folder/filename).write_text("owned only",encoding="utf-8")
 real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 before={n:hashlib.sha256((real/n).read_bytes()).digest()
         for n in LEGACY if (real/n).is_file()}
 initial_hc=high_contrast()
 initial_dpi=0
 env=os.environ.copy()
 for key in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
  dest=own/key.lower();dest.mkdir();env[key]=str(dest)
 for key in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST"):
  env.pop(key,None)
 p=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
 hwnd=None;passed=False
 try:
  def ready():
   nonlocal hwnd
   if p.poll() is not None:return False
   assert Path(psutil.Process(p.pid).exe()).resolve()==exe.resolve()
   windows=[x for x in Desktop(backend="uia").windows(process=p.pid)
            if "flyExplorer - WinUI 3" in x.window_text()]
   if len(windows)!=1:return False
   hwnd=windows[0].handle
   return Desktop(backend="uia").window(handle=hwnd).child_window(
        auto_id="LeftFiles").exists(timeout=.2)
  until(ready,"Owned WinUI accessibility probe did not start")
  win=Desktop(backend="uia").window(handle=hwnd)
  initial_dpi=u.GetDpiForWindow(hwnd)
  assert 96<=initial_dpi<=384
  assert u.GetSystemMetrics(80)==1,"Unexpected monitor change during probe"
  named=("BackButton","ForwardButton","UpButton","AddressBox",
         "QuickSearchBox","NewTabButton","CloseTabButton","SplitButton",
         "LeftFiles","RightFiles","LeftNameFilterBox","RightNameFilterBox",
         "LeftNameWidthSlider","RightNameWidthSlider","SortPicker",
         "ThisPCButton")
  sizes=((960,634),(1100,680),(1240,710))
  for width,height in sizes:
   win.set_focus()
   assert u.GetForegroundWindow()==hwnd
   assert u.SetWindowPos(hwnd,None,40,30,width,height,0x0014)
   until(lambda:abs(win.rectangle().width()-width)<=3,
         "Owned responsive width did not apply")
   # UIA Name and valid geometry underpin Narrator exposure, but cannot
   # prove actual Narrator spoken announcements.
   for key in named:
    element=win.child_window(auto_id=key)
    assert element.exists(timeout=2),(key,width,height)
    assert element.element_info.name,(key,"missing accessible name")
   pane=win.child_window(auto_id="LeftFiles")
   until(lambda:any(filename in x.window_text() for x in pane.descendants()
          if x.element_info.control_type=="ListItem"),
         "Owned Korean accessibility row missing")
   # Geometry confirms the Fluent hierarchy remains title/commands,
   # address+search, then dual-pane content at each responsive size.
   back=win.child_window(auto_id="BackButton").rectangle()
   address_rect=win.child_window(auto_id="AddressBox").rectangle()
   search_rect=win.child_window(auto_id="QuickSearchBox").rectangle()
   left_rect=win.child_window(auto_id="LeftFiles").rectangle()
   assert back.top<=address_rect.top<left_rect.top,(width,height,"vertical order")
   assert address_rect.right<=search_rect.left+3,(width,height,"address/search order")
   print("REAL_OWNED_M26_FLUENT_16_NAMED_CONTROLS_AND_RESPONSIVE_SIZE",
         width,height,True,flush=True)
  win.set_focus()
  assert u.GetForegroundWindow()==hwnd
  address=win.child_window(auto_id="AddressBox")
  address.set_focus()
  for n in range(4):
   assert u.GetForegroundWindow()==hwnd
   keyboard.send_keys("{TAB}",pause=.07)
  print("REAL_OWNED_PHYSICAL_KEYBOARD_TAB_FOCUS_SEQUENCE",True,flush=True)
  assert high_contrast()==initial_hc
  assert u.GetDpiForWindow(hwnd)==initial_dpi
  print("ACTUAL_ONE_MONITOR_DPI_AND_HIGH_CONTRAST_CURRENT_STATE",
        initial_dpi,initial_hc,flush=True)
  print("NOT_VERIFIED_ALTERNATE_DPI_HC_ON_NARRATOR_KOREAN_IME",True,flush=True)
  passed=True
 finally:
  if p.poll() is None:
   if hwnd is not None:
    u.PostMessageW(hwnd,0x10,0,0)
    try:p.wait(timeout=12)
    except subprocess.TimeoutExpired:
     p.terminate();p.wait(timeout=7)
   else:p.terminate();p.wait(timeout=7)
  unchanged=all((real/n).is_file() and
       hashlib.sha256((real/n).read_bytes()).digest()==v
       for n,v in before.items())
  print("ORIGINAL_SIX_USER_SETTINGS_IDENTICAL",unchanged,flush=True)
  assert high_contrast()==initial_hc
  if passed and unchanged:
   import shutil;shutil.rmtree(own)
  else:print("OWNED_ACCESSIBILITY_FIXTURE_RETAINED",own,flush=True)
 return 0 if passed and unchanged else 1
if __name__=="__main__":
 sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "Debug"))
