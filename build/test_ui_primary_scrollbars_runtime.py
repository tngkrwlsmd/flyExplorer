"""Owned real-Windows GUI: primary native list/tree scrollbar and resize."""
from pathlib import Path
import ctypes as c,hashlib,os,re,shutil,subprocess,tempfile,time,sys
from ctypes import wintypes as w
from pywinauto import mouse
ROOT=Path(__file__).resolve().parents[1]
MODE="light" if "--light" in sys.argv else "dark"
NAMES=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat",
       "fxfile-dlg_state.conf","fxfile-folder_layout.conf")
SOURCE=Path(os.environ["APPDATA"])/"fxfile"/"conf"
before={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
own=Path(tempfile.mkdtemp(prefix="ui-scroll-controls-",dir=ROOT/"logs"))
conf=own/"conf";conf.mkdir()
for n in NAMES:shutil.copy2(SOURCE/n,conf/n)
raw=(conf/"fxfile.conf").read_bytes()
enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
settings=raw.decode(enc)
for key in ("config.global_hotkey.enable","config.global_hotkey.show_tray",
            "config.global_hotkey.windows_startup","config.register_shell_context_menu",
            "config.single_process","config.theme_mode"):
 value=("1" if MODE=="light" else "2") if key=="config.theme_mode" else "0"
 settings,n=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",
                    lambda m:m.group(1)+value,settings)
 assert n==1,key
(conf/"fxfile.conf").write_bytes(settings.encode(enc))
fixture=own/"fixture";fixture.mkdir()
for n in range(65):(fixture/("owned-scrolling-folder-%03d" % n)).mkdir()
# A borrowed real-user main.conf may contain Last Tabs paths from a different
# session. Overwrite ONLY the copied PRIVATE profile with our exact synthetic
# fixture, so this GUI test never navigates the user's previous directories.
settings=(conf/"fxfile.conf").read_bytes().decode(enc)
for key,value in (("config.view1.file_list.init_folder","3"),
                  ("config.view2.file_list.init_folder","3")):
 settings,count=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",
        lambda m:m.group(1)+value,settings)
 if not count:
  assert "[config]" in settings
  settings=settings.replace("[config]","[config]\n"+key+" = "+value,1)
(conf/"fxfile.conf").write_bytes(settings.encode(enc))
(conf/"fxfile-main.conf").write_text("\n".join(("[main]",
 "main.view.row_count = 1","main.view.column_count = 1",
 "main.view1.current_tab = 0",
 "main.view1.tab1.path = "+str(fixture),"")),encoding="utf-16")
(own/"appdata").mkdir()
u=c.windll.user32
class RECT(c.Structure):
 _fields_=[(x,c.c_long) for x in ("left","top","right","bottom")]
class SI(c.Structure):
 _fields_=[("size",w.DWORD),("rc",RECT),("line",c.c_int),
           ("thumbtop",c.c_int),("thumbbottom",c.c_int),
           ("reserved",c.c_int),("states",w.DWORD*6)]
class INFO(c.Structure):
 _fields_=[("size",w.UINT),("mask",w.UINT),("min",c.c_int),("max",c.c_int),
           ("page",w.UINT),("pos",c.c_int),("track",c.c_int)]
CB=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
u.EnumWindows.argtypes=(CB,w.LPARAM)
u.EnumChildWindows.argtypes=(w.HWND,CB,w.LPARAM)
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.GetScrollBarInfo.argtypes=(w.HWND,c.c_long,c.POINTER(SI))
u.GetScrollBarInfo.restype=w.BOOL
u.GetScrollInfo.argtypes=(w.HWND,c.c_int,c.POINTER(INFO))
u.GetScrollInfo.restype=w.BOOL
u.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.SendMessageW.restype=c.c_ssize_t
u.SetWindowPos.argtypes=(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)
def pid(hwnd):
 p=w.DWORD();u.GetWindowThreadProcessId(hwnd,c.byref(p));return p.value
def klass(hwnd):
 buf=c.create_unicode_buffer(80);u.GetClassNameW(hwnd,buf,80);return buf.value
def title(hwnd):
 buf=c.create_unicode_buffer(180);u.GetWindowTextW(hwnd,buf,180);return buf.value
def rect(hwnd):
 x=RECT();u.GetWindowRect(hwnd,c.byref(x));return x.left,x.top,x.right,x.bottom
def all_windows(pidnumber):
 wins=[]
 @CB
 def callback(hwnd,_):
  if pid(hwnd)==pidnumber and u.IsWindowVisible(hwnd):wins.append(int(hwnd))
  return 1
 u.EnumWindows(callback,0)
 return wins
def info(hwnd,bar):
 a=INFO();a.size=c.sizeof(INFO);a.mask=0x17
 assert u.GetScrollInfo(hwnd,bar,c.byref(a)),("scrollinfo missing",klass(hwnd),bar)
 return a
def overlay_match(wins,scroll_rect):
 return [h for h in wins if
     rect(h)[0] < scroll_rect[2] and scroll_rect[0] < rect(h)[2] and
     rect(h)[1] < scroll_rect[3] and scroll_rect[1] < rect(h)[3]]
proc=None;main=0
try:
 proc=subprocess.Popen([str(ROOT/"bin/x64/fxfile.exe"),"--conf_dir",str(conf),str(fixture)],
       cwd=own,env={**os.environ,"APPDATA":str(own/"appdata")},
       stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for attempt in range(95):
  ms=[h for h in all_windows(proc.pid) if title(h).endswith(" - fxfile")]
  if len(ms)==1:main=ms[0];break
  time.sleep(.1)
 assert main,"owned flyExplorer main window missing"
 controls=[]
 @CB
 def child(hwnd,_):
  if u.IsWindowVisible(hwnd) and klass(hwnd) in ("SysListView32","SysTreeView32"):
   controls.append((klass(hwnd),int(hwnd)))
  return 1
 u.EnumChildWindows(main,child,0)
 ctrls={}
 for name,hwnd in controls:ctrls.setdefault(name,hwnd)
 assert len(ctrls)==2,("list/tree controls missing",controls)
 print("LIVE_PRIMARY_WINDOW_DPI",u.GetDpiForWindow(main),"MODE",MODE,flush=True)
 # At 96 DPI the test-owned main frame is resized to exercise post-layout
 # overlay coordinates; no system-wide DPI or display settings are changed.
 u.ShowWindow(main,9)
 # Win32 can report a scrollbar "visible" when the lower edge of an owned
 # main window extends BELOW the physical monitor work area. Previously
 # the test clicked tree scrollbar y=783 on a desktop ending above that.
 work=RECT()
 u.SystemParametersInfoW.argtypes=(w.UINT,w.UINT,c.POINTER(RECT),w.UINT)
 u.SystemParametersInfoW.restype=w.BOOL
 assert u.SystemParametersInfoW(0x30,0,c.byref(work),0),"work area unavailable"
 width=min(980,work.right-work.left-36)
 height=min(680,work.bottom-work.top-45)
 assert width>700 and height>460,("real desktop too small",width,height)
 x=work.left+18;y=work.top+20
 assert u.SetWindowPos(main,0,x,y,width,height,0x0004),"owned window resize failed"
 time.sleep(.45)
 assert rect(main)[2]-rect(main)[0] <= 1010
 assert rect(main)[3] <= work.bottom-5,("owned native scroll control offscreen",
     rect(main),work.bottom)
 print("OWNED_MAIN_FITS_MONITOR_WORKAREA",(x,y,width,height),
       "WORKAREA_BOTTOM",work.bottom,flush=True)
 # Wait for the fixture's actual native list population BEFORE testing tree
 # arrows, so a delayed startup restore does not re-layout a control mid-click.
 lv=ctrls["SysListView32"]
 count=0
 for _ in range(105):
  count=int(u.SendMessageW(lv,0x1004,0,0))
  if count>=55:break
  time.sleep(.1)
 assert count>=55,("owned private fixture not selected",count,str(fixture))
 print("PRIVATE_SYNTHETIC_SCOPED_LIST_ENTRIES",count,flush=True)
 # Another *owned* top-level popup, Tip of the Day, is enabled by some
 # copied profiles. If present it is MODAL and silently eats all scrollbar
 # pointer input even while the underlying HWND/scrollbar reports VISIBLE.
 # Dismiss only a dialog belonging to this exact test-owned process.
 u.GetDlgItem.argtypes=(w.HWND,c.c_int)
 u.GetDlgItem.restype=w.HWND
 tip=next((h for h in all_windows(proc.pid)
           if h!=main and klass(h)=="#32770" and u.GetDlgItem(h,1029)),0)
 if tip:
  check=u.GetDlgItem(tip,1029)
  u.SetForegroundWindow.argtypes=(w.HWND,)
  u.SetForegroundWindow(tip)
  time.sleep(.12)
  if u.SendMessageW(check,0xF0,0,0):
   cb=rect(check)
   mouse.click(coords=((cb[0]+cb[2])//2,(cb[1]+cb[3])//2))
   time.sleep(.12)
   assert u.SendMessageW(check,0xF0,0,0)==0
  ok=u.GetDlgItem(tip,1)
  assert ok,"owned Tip modal has no native OK button"
  rr=rect(ok)
  mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
  for _ in range(20):
   if not u.IsWindow(tip):break
   time.sleep(.1)
  assert not u.IsWindow(tip),"test-owned startup modal failed to close"
  print("OWNED_STARTUP_TIP_MODAL_PHYSICALLY_DISMISSED",True,flush=True)
 # Never attempt native scrollbar physical input into an unfocused preview.
 u.SetForegroundWindow.argtypes=(w.HWND,)
 u.SetForegroundWindow.restype=w.BOOL
 u.GetForegroundWindow.restype=w.HWND
 u.SetForegroundWindow(main)
 time.sleep(.18)
 if pid(u.GetForegroundWindow())!=proc.pid:
  window_rect=rect(main)
  mouse.click(coords=((window_rect[0]+window_rect[2])//2,
                       window_rect[1]+13))
  time.sleep(.25)
 assert pid(u.GetForegroundWindow())==proc.pid,(
     "owned application has no foreground desktop for physical input")
 for name,hwnd in ctrls.items():
  assert u.IsWindow(hwnd) and u.IsWindowVisible(hwnd),name
  if name=="SysListView32":
   # Actual directory population is asynchronous after process startup.
   count=0
   for _ in range(80):
    count=int(u.SendMessageW(hwnd,0x1004,0,0))
    if count>=55:break
    time.sleep(.12)
   assert count>=55,("owned synthetic fixture did not load",count,str(fixture))
  for bar,object_id,orient in ((1,-5,"VERT"),(0,-6,"HORZ")):
   si=SI();si.size=c.sizeof(SI)
   got=bool(u.GetScrollBarInfo(hwnd,object_id,c.byref(si)))
   a=info(hwnd,bar)
   sr=si.rc.left,si.rc.top,si.rc.right,si.rc.bottom
   active=got and not (si.states[0]&0x8000) and sr[2]>sr[0] and sr[3]>sr[1]
   possible=a.max-a.min+1>max(1,a.page)
   print("NATIVE_SCROLL_COVERAGE",name,orient,"VISIBLE",active,"POSSIBLE",possible,
         "PAGE",a.page,"RANGE",(a.min,a.max),"POSITION",a.pos,flush=True)
   if not active or not possible:
    print("SCROLL_DIRECTION_NOT_APPLICABLE",name,orient,flush=True);continue
   overlays=[h for h in all_windows(proc.pid) if "DarkScrollbar" in klass(h)]
   matches=overlay_match(overlays,sr)
   print("VISUAL_OVERLAY_PRESENT",name,orient,bool(matches),"MODE",MODE,flush=True)
   if MODE=="dark":assert matches,(name,orient,"modern overlay missing")
   else:assert not matches,(name,orient,"dark overlay in Light")
   at_max=a.pos>=a.max-max(1,a.page)+1
   reverse=a.pos>a.min and at_max
   if orient=="VERT":
    x=(sr[0]+sr[2])//2;y=sr[1]+7 if reverse else sr[3]-7
   else:
    y=(sr[1]+sr[3])//2;x=sr[0]+7 if reverse else sr[2]-7
   mouse.click(coords=(x,y))
   time.sleep(.2)
   after=info(hwnd,bar).pos
   if after==a.pos:
    mouse.click(coords=(x,y));time.sleep(.2);after=info(hwnd,bar).pos
   print("NATIVE_POINTER_SCROLL",name,orient,a.pos,after,"MODE",MODE,flush=True)
   assert (after<a.pos if reverse else after>a.pos),(name,orient,"pointer scroll blocked")
   # Native scrollbar remains attached after window resizing/re-layout.
   si2=SI();si2.size=c.sizeof(SI)
   assert u.GetScrollBarInfo(hwnd,object_id,c.byref(si2))
   overlays=[h for h in all_windows(proc.pid) if "DarkScrollbar" in klass(h)]
   final=(si2.rc.left,si2.rc.top,si2.rc.right,si2.rc.bottom)
   if MODE=="dark":assert overlay_match(overlays,final)
 # A native vertical thumb drag and scrollbar track page-click must remain
 # reachable THROUGH the visual-only dark overlay, not merely arrow clicks.
 lv=ctrls["SysListView32"]
 def thumb_y(stat):
  rr=stat.rc
  height=rr.bottom-rr.top
  if 0<=stat.thumbtop<=height and 0<=stat.thumbbottom<=height:
   return rr.top+(stat.thumbtop+stat.thumbbottom)//2
  return (stat.thumbtop+stat.thumbbottom)//2
 def thumb_edges(stat):
  height=stat.rc.bottom-stat.rc.top
  if 0<=stat.thumbtop<=height and 0<=stat.thumbbottom<=height:
   return stat.rc.top+stat.thumbtop,stat.rc.top+stat.thumbbottom
  return stat.thumbtop,stat.thumbbottom
 stat=SI();stat.size=c.sizeof(SI)
 assert u.GetScrollBarInfo(lv,-5,c.byref(stat))
 prev=info(lv,1).pos
 cy=thumb_y(stat)
 cx=(stat.rc.left+stat.rc.right)//2
 lo=stat.rc.top+stat.line+6
 hi=stat.rc.bottom-stat.line-6
 assert lo<cy<hi,("native thumb geometry invalid",cy,lo,hi,
                 stat.thumbtop,stat.thumbbottom)
 direction=1 if cy+42<hi else -1
 target=cy+direction*34
 mouse.press(button="left",coords=(cx,cy))
 for part in (0.3,0.65,1.0):
  mouse.move(coords=(cx,cy+int(direction*34*part)))
  time.sleep(.05)
 mouse.release(button="left",coords=(cx,target))
 time.sleep(.2)
 dragged=info(lv,1).pos
 print("NATIVE_SCROLLBAR_THUMB_DRAG",prev,dragged,"MODE",MODE,flush=True)
 assert dragged!=prev,"native scrollbar thumb drag blocked"
 stat=SI();stat.size=c.sizeof(SI)
 assert u.GetScrollBarInfo(lv,-5,c.byref(stat))
 thumb_top,thumb_bottom=thumb_edges(stat)
 track_after=thumb_bottom+12
 if track_after<stat.rc.bottom-stat.line-4:
  track_y=track_after
 elif thumb_top-12>stat.rc.top+stat.line+4:
  track_y=thumb_top-12
 else:
  track_y=None
 if track_y is not None:
  before_track=info(lv,1).pos
  mouse.click(coords=(cx,track_y))
  time.sleep(.22)
  after_track=info(lv,1).pos
  print("NATIVE_SCROLLBAR_TRACK_CLICK",before_track,after_track,
        "MODE",MODE,flush=True)
  assert after_track!=before_track,"native track page-click blocked"
 else:
  print("NATIVE_SCROLLBAR_TRACK_CLICK_NOT_APPLICABLE",MODE,flush=True)

 # Wheel is tested separately: list top-index changes with actual wheel input.
 lv=ctrls["SysListView32"]
 pre=u.SendMessageW(lv,0x1027,0,0)
 lr=rect(lv)
 mouse.scroll(coords=(lr[0]+80,lr[1]+95),wheel_dist=-3)
 time.sleep(.25)
 post=u.SendMessageW(lv,0x1027,0,0)
 print("NATIVE_LIST_MOUSE_WHEEL",pre,post,"MODE",MODE,flush=True)
 assert post!=pre,"real list mouse wheel did not scroll"
 print("PRIMARY_LIST_TREE_SCROLLBAR_GUI_PASS",MODE,flush=True)
finally:
 if proc and proc.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 after={n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in NAMES}
 print("ORIGINAL_SIX_CONFIGS_UNCHANGED",after==before,"OWNED_EXIT",
       None if proc is None else proc.returncode,flush=True)
 assert after==before and proc is not None and proc.returncode==0
