"""Owned GUI probe for View submenu and legacy TB_CUSTOMIZE skin (Windows)."""
from pathlib import Path
from ctypes import wintypes as W
import ctypes as c,hashlib,os,re,shutil,subprocess,tempfile,time
import psutil
from PIL import ImageGrab
from pywinauto import keyboard,mouse,Desktop

R=Path(__file__).resolve().parents[1]
real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
six=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
     "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((real/n).read_bytes()).digest() for n in six}
home=Path(tempfile.mkdtemp(prefix="ui-legacy-owned-",dir=R/"logs"))
config=home/"conf";config.mkdir()
appdata=home/"appdata";appdata.mkdir()
temp=home/"tmp";temp.mkdir()
folder=home/"Owned UI Fixture";folder.mkdir()
for n in six: shutil.copy2(real/n,config/n)
p=config/"fxfile.conf"
b=p.read_bytes();enc="utf-16" if b[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
s=b.decode(enc)
for key,val in (
 ("config.global_hotkey.enable","0"),("config.global_hotkey.windows_startup","0"),
 ("config.global_hotkey.show_tray","0"),("config.register_shell_context_menu","0"),
 ("config.single_process","0"),("config.view1.file_list.init_folder","3")):
 pattern=r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*"
 s,n=re.subn(pattern,lambda m:m.group(1)+val,s)
 if not n: s=s.replace("[config]","[config]\n"+key+" = "+val,1)
p.write_bytes(s.encode(enc))
(config/"fxfile-main.conf").write_text("\n".join(
 ("[main]","main.tip_of_today.show = 0","main.view.row_count = 1",
  "main.view.column_count = 1","main.view1.current_tab = 0",
  "main.view1.tab1.path = "+str(folder),"")),encoding="utf-16")

u=c.windll.user32
CALLBACK=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=(CALLBACK,W.LPARAM)
u.GetWindowThreadProcessId.argtypes=(W.HWND,c.POINTER(W.DWORD))
u.GetClassNameW.argtypes=(W.HWND,W.LPWSTR,c.c_int)
u.GetWindowTextW.argtypes=(W.HWND,W.LPWSTR,c.c_int)
u.PostMessageW.argtypes=(W.HWND,W.UINT,W.WPARAM,W.LPARAM)
u.SendMessageW.argtypes=(W.HWND,W.UINT,W.WPARAM,W.LPARAM)
u.SendMessageW.restype=c.c_ssize_t
u.GetDlgItem.argtypes=(W.HWND,c.c_int)
u.GetDlgItem.restype=W.HWND
class RECT(c.Structure):
 _fields_=[(a,c.c_long) for a in ("left","top","right","bottom")]
u.GetWindowRect.argtypes=(W.HWND,c.POINTER(RECT))
def rect(h):
 q=RECT();assert u.GetWindowRect(h,c.byref(q))
 return (q.left,q.top,q.right,q.bottom)
def classof(h):
 b=c.create_unicode_buffer(128);u.GetClassNameW(h,b,128);return b.value
def title(h):
 b=c.create_unicode_buffer(180);u.GetWindowTextW(h,b,180);return b.value
def owned(pid):
 found=[]
 @CALLBACK
 def cb(h,_):
  q=W.DWORD();u.GetWindowThreadProcessId(h,c.byref(q))
  if q.value==pid:found.append(int(h))
  return 1
 u.EnumWindows(cb,0)
 return found
def visible(pid,clazz):
 return [h for h in owned(pid) if classof(h)==clazz and u.IsWindowVisible(h)]
def exact_main(pid):
 for _ in range(100):
  z=[h for h in owned(pid) if title(h).endswith(" - fxfile")]
  if len(z)==1:return z[0]
  time.sleep(.10)
 raise AssertionError("owned main window not found")
def capture(path,windows):
 regions=[rect(h) for h in windows]
 x=min(q[0] for q in regions);y=min(q[1] for q in regions)
 X=max(q[2] for q in regions);Y=max(q[3] for q in regions)
 assert 30<X-x<1300 and 30<Y-y<1250,regions
 ImageGrab.grab(bbox=(x,y,X,Y),include_layered_windows=True).save(path)
 print("CAPTURED",path.name,"SIZE",(X-x,Y-y),flush=True)
start_existing={p.pid for p in psutil.process_iter(["name"]) if
 (p.info["name"] or "").lower()=="fxfile.exe"}
proc=None;main=None
try:
 env={**os.environ,"APPDATA":str(appdata),"TMP":str(temp),"TEMP":str(temp)}
 proc=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(config)],
     env=env,cwd=home,stdin=subprocess.DEVNULL,
     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 main=exact_main(proc.pid);u.ShowWindow(main,9)
 assert proc.pid not in start_existing
 assert u.PostMessageW(main,0x111,33048,0)
 time.sleep(.5)
 u.SetForegroundWindow(main)
 assert u.GetForegroundWindow()==main
 keyboard.send_keys("%v",pause=.08);time.sleep(.28)
 top=visible(proc.pid,"#32768")
 assert top,"test-owned View popup not visible"
 keyboard.send_keys("w",pause=.08);time.sleep(.30)
 pops=visible(proc.pid,"#32768")
 assert len(pops)>=2,("physical Workspaces submenu did not open",len(pops))
 capture(R/"logs/ui-legacy-owned-workspaces-menu.png",pops[-2:])
 print("NATIVE_SUBMENU_VISIBLE",len(pops),flush=True)
 keyboard.send_keys("{ESC}{ESC}",pause=.07)
 assert u.PostMessageW(main,0x111,33018,0)
 dlg=None;boxes=None
 for _ in range(125):
  for h in visible(proc.pid,"#32770"):
   left=int(u.GetDlgItem(h,0x00C9) or 0)
   right=int(u.GetDlgItem(h,0x00CB) or 0)
   if left and right:
    dlg=h;boxes=(left,right);break
  if dlg:break
  time.sleep(.09)
 assert dlg,("test-owned legacy toolbar customization dialog not opened",
             [(classof(h),title(h)) for h in owned(proc.pid)])
 print("REAL_NATIVE_CUSTOMIZE_DIALOG",title(dlg).encode("unicode_escape").decode(),
       "LIST_CLASSES",[classof(h) for h in boxes],flush=True)
 time.sleep(.6)
 capture(R/"logs/ui-legacy-owned-toolbar-customize.png",[dlg])
 from PIL import Image
 pic=Image.open(R/"logs/ui-legacy-owned-toolbar-customize.png").convert("RGB")
 dr=rect(dlg)
 samples=[]
 for h in boxes:
  q=rect(h);x=q[2]-dr[0]-7;y=(q[1]+q[3])//2-dr[1]
  if 0<=x<pic.width and 0<=y<pic.height:samples.append(pic.getpixel((x,y)))
 print("DARK_NATIVE_LIST_SCROLLBAR_PIXELS",samples,flush=True)
 assert len(samples)==2 and all(max(rgb)<160 for rgb in samples),(
   "old light scrollbars remain on owned Dark customization lists",samples)
 # Real wheel delivery must still scroll the native ListBox even when
 # the shared transparent Dark scrollbar compositor is visible.
 first=boxes[0]
 top_before=int(u.SendMessageW(first,0x018E,0,0)) # LB_GETTOPINDEX
 br=rect(first)
 mouse.scroll(coords=((br[0]+br[2])//2,(br[1]+br[3])//2),
              wheel_dist=-3)
 time.sleep(.45)
 top_after=int(u.SendMessageW(first,0x018E,0,0))
 print("ACTUAL_LISTBOX_WHEEL_TOP_INDEX",top_before,top_after,flush=True)
 assert top_after>top_before,(
   "native customize list scrollbar did not respond to real wheel",
   top_before,top_after)
 capture(R/"logs/ui-legacy-owned-toolbar-scrolled.png",[dlg])
 assert u.PostMessageW(dlg,0x10,0,0)
 for _ in range(85):
  if not u.IsWindow(dlg):break
  time.sleep(.06)
 assert not u.IsWindow(dlg),"test-owned customize dialog remained open"
finally:
 if proc and proc.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=13)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
 same=all(hashlib.sha256((real/n).read_bytes()).digest()==before[n] for n in six)
 print("ORIGINAL_SIX_SETTINGS_IDENTICAL",same,"OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert same and proc and proc.returncode==0
 assert home.parent==R/"logs" and home.name.startswith("ui-legacy-owned-")
 shutil.rmtree(home)
 print("TEST_OWNED_FIXTURE_REMOVED",True,flush=True)
