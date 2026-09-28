"""Owned 96-DPI UXH-03 native ExplorerPane layout geometry baseline/acceptance."""
from pathlib import Path
import ctypes as c,hashlib,os,re,shutil,subprocess,tempfile,time,sys
from ctypes import wintypes as w
from PIL import ImageGrab
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ["APPDATA"])/"fxfile"/"conf"
NAMES=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
folder=Path(tempfile.mkdtemp(prefix="uxh03-layout-owned-",dir=ROOT/"logs"))
conf=folder/"conf";conf.mkdir()
for n in NAMES:shutil.copy2(SOURCE/n,conf/n)
raw=(conf/"fxfile.conf").read_bytes()
enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
cfg=raw.decode(enc)
for key,val in (("config.theme_mode","1" if "--light" in sys.argv else "2"),("config.global_hotkey.enable","0"),
    ("config.global_hotkey.show_tray","0"),("config.global_hotkey.windows_startup","0"),
    ("config.register_shell_context_menu","0"),("config.info_bar.show","1")):
 cfg,n=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",lambda m:m.group(1)+val,cfg)
 assert n==1,key
# The original user preference remains untouched. This is an owned,
# explicit explorer-sidebar scenario rather than a claim about their config.
cfg,n=re.subn(r"(?m)^(\s*config\.info_bar\.style\s*=\s*)[^\r\n]*",lambda m:m.group(1)+"1",cfg)
print("OWNED_INFO_BAR_STYLE_CONFIG_OVERRIDDEN",n,flush=True)
(conf/"fxfile.conf").write_bytes(cfg.encode(enc))
fixture=folder/"fixture";fixture.mkdir()
for i in range(12):(fixture/("long descriptive filename 1234567890 %02d.txt"%i)).write_text("owned",encoding="utf-8")
(folder/"appdata").mkdir()
user=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):_fields_=[(k,c.c_long) for k in ("left","top","right","bottom")]
for n,args,ret in (
 ("EnumWindows",(CALLBACK,w.LPARAM),w.BOOL),
 ("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM),w.BOOL),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD)),w.DWORD),
 ("GetWindowRect",(w.HWND,c.POINTER(RECT)),w.BOOL),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int),c.c_int),
 ("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int),c.c_int),
 ("SetWindowPos",(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT),w.BOOL),
 ("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM),w.BOOL),
 ("GetDpiForWindow",(w.HWND,),w.UINT)):
 fn=getattr(user,n);fn.argtypes=args;fn.restype=ret
def rect(h):
 x=RECT();assert user.GetWindowRect(h,c.byref(x));return (x.left,x.top,x.right,x.bottom)
def width(b):return b[2]-b[0]
def cls(h):
 b=c.create_unicode_buffer(150);user.GetClassNameW(h,b,len(b));return b.value
def title(h):
 b=c.create_unicode_buffer(260);user.GetWindowTextW(h,b,len(b));return b.value
def procid(h):
 p=w.DWORD();user.GetWindowThreadProcessId(h,c.byref(p));return p.value
def enum(h,by_window=False):
 out=[]
 @CALLBACK
 def cb(x,_):
  if not by_window or procid(x)==h:out.append(int(x))
  return True
 (user.EnumWindows if by_window else user.EnumChildWindows)(cb if by_window else h,0 if by_window else cb,0) if False else None
 if by_window:user.EnumWindows(cb,0)
 else:user.EnumChildWindows(h,cb,0)
 return out
proc=None;main=0
try:
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(fixture)],cwd=folder,
       env={**os.environ,"APPDATA":str(folder/"appdata")},
       stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(95):
  mains=[h for h in enum(proc.pid,True) if title(h).endswith(" - fxfile")]
  if len(mains)==1:main=mains[0];break
  time.sleep(.12)
 assert main
 print("ACTUAL_MAIN_DPI",user.GetDpiForWindow(main),"MAIN",rect(main),flush=True)
 assert user.GetDpiForWindow(main)==96
 def setsize(wide,high):
  user.ShowWindow(main,9)
  assert user.SetWindowPos(main,0,65,67,wide,high,0x0004)
  time.sleep(.55)
 def post(command):
  assert user.PostMessageW(main,0x111,command,0)
  time.sleep(.7)
 def snap(tag):
  pane=[h for h in enum(main) if cls(h)=="ExplorerPane" and user.IsWindowVisible(h)]
  summary=[]
  for ph in pane:
   cs=[x for x in enum(ph) if user.IsWindowVisible(x)]
   contents=[x for x in cs if cls(x)=="ContentsWnd"]
   lists=[x for x in cs if cls(x)=="SysListView32"]
   if not contents or not lists:
    print("SUBTREE",ph,[(cls(x),rect(x)) for x in cs][:22],flush=True)
   assert len(contents)==1 and lists,("pane has no visible info/list",len(contents),len(lists))
   info=rect(contents[0]);found=sorted((rect(x),x) for x in lists)
   best=max(found,key=lambda entry:width(entry[0]))
   summary.append((rect(ph),info,best[0]))
  summary.sort(key=lambda item:item[0][:2])
  print("UXH03_SCREENSHOT_DIRECTORY",folder,flush=True)
  for k,(p,info,ls) in enumerate(summary):
   print("LAYOUT",tag,"PANE",k,"PANE_W",width(p),"INFO_W",width(info),
         "LIST_W",width(ls),"INFO",info,"LIST",ls,flush=True)
  ImageGrab.grab(bbox=rect(main),include_layered_windows=True).save(folder/(tag+".png"))
  return summary
 setsize(1100,720)
 post(35002)
 base=snap("single-wide")
 assert len(base)==1
 post(35003)
 two=snap("two-wide")
 assert len(two)==2
 setsize(750,550)
 two_small=snap("two-750")
 assert len(two_small)==2
 if "--input" in sys.argv:
  from pywinauto import keyboard,mouse
  user.SetForegroundWindow.argtypes=(w.HWND,)
  user.GetForegroundWindow.restype=w.HWND
  def input_snap(label,full_width):
   panes=snap(label)
   assert len(panes)==2
   for pane,info,ls in panes:
    if full_width:
     assert width(info)<width(pane) and width(ls)>=280,(
        label,"not expanded after real input",pane,info,ls)
    else:
     assert width(info)==width(pane)==width(ls),(
        label,"compact not restored after real input",pane,info,ls)
   return panes
  fr=rect(main)
  mouse.click(coords=(fr[0]+175,fr[1]+14))
  time.sleep(.3)
  assert user.GetForegroundWindow()==main,(
      "refusing to send global keyboard shortcuts to a non-owned window",
      user.GetForegroundWindow(),main)
  keyboard.send_keys("{VK_LWIN down}{UP}{VK_LWIN up}")
  time.sleep(.8)
  assert width(rect(main))>1000,("Win+Up did not maximize owned app",rect(main))
  input_snap("two-keyboard-expanded",True)
  assert user.GetForegroundWindow()==main
  keyboard.send_keys("{VK_LWIN down}{DOWN}{VK_LWIN up}")
  time.sleep(.8)
  assert width(rect(main))==750,("Win+Down did not restore compact width",rect(main))
  input_snap("two-keyboard-restored",False)
  assert user.GetForegroundWindow()==main
  mr=rect(main)
  mouse.double_click(coords=(mr[0]+175,mr[1]+14))
  time.sleep(.75)
  assert width(rect(main))>1000,"double-click did not maximize owned window"
  input_snap("two-mouse-expanded",True)
  mr=rect(main)
  mouse.double_click(coords=(mr[0]+175,mr[1]+14))
  time.sleep(.75)
  assert width(rect(main))==750,"double-click did not restore compact width"
  input_snap("two-mouse-restored",False)
  print("UXH03_REAL_KEYBOARD_AND_MOUSE_RESTORE_PASS=True",flush=True)
 setsize(1100,720)
 expanded=snap("two-reexpanded")
 assert len(expanded)==2
 setsize(750,550)
 post(35005)
 quad_small=snap("four-750")
 assert len(quad_small)==4
 setsize(1200,750)
 quad=snap("four-wide")
 assert len(quad)==4
 post(35002)
 restored=snap("single-restored")
 assert len(restored)==1
 if "--accept" in sys.argv:
  for tag,results in (("two-750",two_small),("four-750",quad_small)):
   for pane,info,ls in results:
    assert width(info)>=width(pane)-2,(
      tag,"compact header did not release full pane width",pane,info,ls)
    assert width(ls)>=width(pane)-2,(tag,"file list remained narrow",ls)
    assert 28<=info[3]-info[1]<=45,(tag,"compact header height",info)
    assert ls[1]>=info[3]-1,(tag,"compact header overlaps file list",info,ls)
  for tag,results in (("two-reexpanded",expanded),("four-wide",quad),
                       ("single-restored",restored)):
   for pane,info,ls in results:
    assert 120<=width(info)<width(pane),(
      tag,"saved wide sidebar not restored",info,pane)
    assert width(ls)>=(285 if tag=="two-reexpanded" else 305),(
      tag,"wide file list became too narrow",ls)
  print("UXH03_COMPACT_FULL_WIDTH_AND_WIDE_RESTORATION_PASS=True",flush=True)
 print("OWNED_ALL_GEOMETRY_SNAPSHOTS_COMPLETE=True",
       "TWO_750_MIN_FILE_WIDTH",min(width(a[2]) for a in two_small),
       "FOUR_1200_MIN_FILE_WIDTH",min(width(a[2]) for a in quad),flush=True)
finally:
 if proc and proc.poll() is None:
  if main and user.IsWindow(main):user.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=14)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
 owned=(conf/"fxfile.conf").read_bytes().decode(enc)
 for key,expected_value in (("config.info_bar.show","1"),
                            ("config.info_bar.style","1")):
  found=re.search(r"(?m)^\s*"+re.escape(key)+r"\s*=\s*([^\r\n]+)",owned)
  assert found and found.group(1).strip()==expected_value,(
      "saved style changed by responsive layout",key,
      found.group(1) if found else None)
 print("OWNED_INFO_BAR_PREFERENCES_UNCHANGED=True",flush=True)
 after={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("ORIGINAL_SIX_CONFIG_HASHES_UNCHANGED",after==before,
       "OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert after==before and proc is not None and proc.returncode==0
