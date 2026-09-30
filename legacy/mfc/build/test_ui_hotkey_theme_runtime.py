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

from pywinauto import keyboard,mouse
user.GetDlgItem.argtypes=(w.HWND,c.c_int)
from PIL import ImageGrab
proc=None;main=0;dlg=0
try:
 env={**os.environ,"APPDATA":str(folder/"appdata")}
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(fold)],
   cwd=folder,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL)
 for _ in range(85):
  candidates=[h for h in win_all(proc.pid) if title(h).endswith(" - fxfile")]
  if len(candidates)==1:main=candidates[0];break
  time.sleep(.12)
 assert main
 assert user.PostMessageW(main,0x111,32002,0)
 for _ in range(65):
  d=[h for h in win_all(proc.pid) if h!=main and cls(h)=="#32770" and title(h)]
  if d:dlg=d[0];break
  time.sleep(.1)
 assert dlg,("bookmark dialog missing",[(cls(h),title(h)) for h in win_all(proc.pid)])
 boxes=[]
 @CALLBACK
 def inner(h,_):
  if cls(h).lower()=="msctls_hotkey32":boxes.append(int(h))
  return 1
 user.EnumChildWindows(dlg,inner,0)
 assert len(boxes)==1,boxes
 hk=boxes[0]
 user.GetWindowTextW.argtypes=(w.HWND,c.c_wchar_p,c.c_int)
 b=c.create_unicode_buffer(80);user.GetWindowTextW(hk,b,80)
 print("ACTUAL_HOTKEY_WINDOW_TEXT",repr(b.value),flush=True)
 orig=user.SendMessageW(hk,0x402,0,0) # HKM_GETHOTKEY
 print("ACTUAL_HOTKEY_INITIAL",hex(orig & 0xffff),flush=True)
 rr=rect(hk)
 img=ImageGrab.grab(bbox=rr).convert("RGB")
 img.save(folder/("hotkey-"+MODE+"-before.png"))
 interior=[img.getpixel((x,y)) for x in range(3,max(4,img.width-3),3)
           for y in range(3,max(4,img.height-3),3)]
 sample=sum(max(rgb)<110 for rgb in interior)/len(interior)
 print("ACTUAL_HOTKEY_INITIAL_DARK_RATIO",round(sample,3),"MODE",MODE,flush=True)
 # Real Ctrl+2 should be accepted without changing a bookmark.
 user.SetForegroundWindow(dlg)
 focus=rect(hk)
 mouse.click(coords=((focus[0]+focus[2])//2,(focus[1]+focus[3])//2))
 keyboard.send_keys("^2",pause=.055)
 time.sleep(.2)
 v=int(user.SendMessageW(hk,0x402,0,0))&65535
 b=c.create_unicode_buffer(80);user.GetWindowTextW(hk,b,80)
 print("ACTUAL_PHYSICAL_CTRL_2",hex(v),repr(b.value),flush=True)
 assert (v&255)==ord("2") and (v>>8)&2,("hotkey keyboard input broken",hex(v))
 after=ImageGrab.grab(bbox=rect(hk)).convert("RGB")
 after.save(folder/("hotkey-"+MODE+"-after.png"))
 pixel=[after.getpixel((x,y)) for x in range(3,max(4,after.width-3),3)
        for y in range(3,max(4,after.height-3),3)]
 ratio=sum(max(rgb)<110 for rgb in pixel)/len(pixel)
 print("ACTUAL_HOTKEY_EDITED_DARK_RATIO",round(ratio,3),"MODE",MODE,flush=True)
 if "--baseline" not in sys.argv:
  if MODE=="dark":assert ratio>.68,"native hotkey remains bright in Dark"
  else:assert ratio<.25,"hotkey incorrectly dark in Light"
 print("OWNED_HOTKEY_GUI_PROBE_PASS",MODE,flush=True)
finally:
 if proc and proc.poll() is None:
  if dlg and user.IsWindow(dlg):user.PostMessageW(dlg,0x10,0,0)
  if main and user.IsWindow(main):user.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=11)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 after_hash={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("OWNED_ORIGINAL_CONFIG_HASHES_UNCHANGED",after_hash==before,"EXIT",proc.returncode if proc else None,flush=True)
 assert proc is not None and proc.returncode==0 and after_hash==before
