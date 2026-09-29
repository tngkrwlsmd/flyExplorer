"""Owned UXH-05 preliminary UIA/MSAA tab discovery on Windows 11."""
import ctypes as c,os,hashlib,shutil,tempfile,subprocess,time,re,sys
from pathlib import Path
from ctypes import wintypes as w
from PIL import ImageGrab
from pywinauto import Desktop,keyboard,mouse
from comtypes import GUID,POINTER
import comtypes.client
comtypes.client.GetModule("oleacc.dll")
from comtypes.gen.Accessibility import IAccessible
R=Path(__file__).resolve().parents[1]
src=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat",
       "fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((src/n).read_bytes()).digest() for n in names}
folder=Path(tempfile.mkdtemp(prefix="uxh05-owned-",dir=R/"logs"))
cp=folder/"conf";cp.mkdir();fixture=folder/"fixture";fixture.mkdir()
for n in names:shutil.copy2(src/n,cp/n)
raw=(cp/"fxfile.conf").read_bytes()
enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
cfg=raw.decode(enc)
for k,v in (("config.theme_mode","1" if "--light" in sys.argv else "2"),
            ("config.global_hotkey.enable","0"),
            ("config.global_hotkey.show_tray","0"),
            ("config.global_hotkey.windows_startup","0"),
            ("config.register_shell_context_menu","0")):
 cfg,num=re.subn(r"(?m)^(\s*"+re.escape(k)+r"\s*=\s*)[^\r\n]*",
                 lambda m:m.group(1)+v,cfg)
 assert num==1,k
(cp/"fxfile.conf").write_bytes(cfg.encode(enc))
(folder/"appdata").mkdir()
for n in ("UXH05-ALPHA","UXH05-BETA","UXH05-GAMMA"):
 (fixture/n).mkdir()
u=c.windll.user32;ole=c.windll.oleacc
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):
 _fields_=[(k,c.c_long) for k in ("left","top","right","bottom")]
for name,args in (("EnumWindows",(CALLBACK,w.LPARAM)),
 ("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM)),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD))),
 ("GetWindowRect",(w.HWND,c.POINTER(RECT))),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int)),
 ("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int)),
 ("SetWindowPos",(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)),
 ("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM))):
 getattr(u,name).argtypes=args
ole.AccessibleObjectFromWindow.argtypes=(w.HWND,w.DWORD,
    c.POINTER(GUID),c.POINTER(c.c_void_p))
ole.AccessibleObjectFromWindow.restype=w.LONG
def cl(h):
 buf=c.create_unicode_buffer(130);u.GetClassNameW(h,buf,len(buf));return buf.value
def title(h):
 buf=c.create_unicode_buffer(256);u.GetWindowTextW(h,buf,len(buf));return buf.value
def rect(h):
 rr=RECT();u.GetWindowRect(h,c.byref(rr))
 return (rr.left,rr.top,rr.right,rr.bottom)
def en(h,all=False):
 out=[]
 @CALLBACK
 def cb(x,_):
  if all:
   pid=w.DWORD();u.GetWindowThreadProcessId(x,c.byref(pid))
   if pid.value!=h:return True
  out.append(int(x));return True
 u.EnumWindows(cb,0) if all else u.EnumChildWindows(h,cb,0)
 return out
def snapshot(main,step):
 tabs=[h for h in en(main) if cl(h)=="TabCtrl" and u.IsWindowVisible(h)]
 print("GUI_STEP",step,"TAB_HWNDS",[(h,rect(h),title(h)) for h in tabs],
       "MAIN_TITLE",title(main),flush=True)
 for h in tabs:
  out={"handle":h}
  try:
   elem=Desktop(backend="uia").window(handle=h)
   out["uia_root"]=(elem.element_info.control_type,elem.element_info.name)
   out["uia_descendants"]=[(x.element_info.control_type,x.element_info.name,
      x.element_info.automation_id,x.element_info.handle)
      for x in elem.descendants()][:20]
  except Exception as ex:out["uia_error"]=repr(ex)[:100]
  ptr=POINTER(IAccessible)()
  try:
   hr=ole.AccessibleObjectFromWindow(h,0xFFFFFFFC,
      c.byref(IAccessible._iid_),c.cast(c.byref(ptr),c.POINTER(c.c_void_p)))
   out["msaa_hresult"]=hex(hr & 0xFFFFFFFF)
   if hr==0 and bool(ptr):
    out["msaa_child_count"]=ptr.accChildCount
    for child in range(min(7,ptr.accChildCount)+1):
     try:
      out["msaa_child_"+str(child)]=(ptr.accName(child),ptr.accRole(child),
                                    ptr.accState(child))
     except Exception as ex:out["msaa_child_error_"+str(child)]=repr(ex)[:120]
  except Exception as ex:out["msaa_error"]=repr(ex)[:130]
  if hr==0 and bool(ptr) and ptr.accChildCount:
   try:out["msaa_selection"]=str(ptr.accSelection)
   except Exception as ex:out["msaa_selection_error"]=repr(ex)[:125]
   try:out["msaa_second_action"]=str(ptr.accDefaultAction(2))
   except Exception as ex:out["msaa_second_action_error"]=repr(ex)[:130]
   try:out["msaa_second_location"]=str(ptr.accLocation(2))
   except Exception as ex:out["msaa_second_location_error"]=repr(ex)[:130]
  try:
   elem=Desktop(backend="uia").window(handle=h)
   raw_children=[x for x in elem.descendants()
                 if x.element_info.control_type=="TabItem"]
   out["uia_selected"]=[(x.element_info.name,
      x.is_selected() if hasattr(x,"is_selected") else "no method")
      for x in raw_children]
  except Exception as ex:out["uia_selected_error"]=repr(ex)[:110]
  for k,v in out.items():
   print("ACCESS",step,k,str(v).encode("ascii","backslashreplace").decode()[:390],flush=True)
 if "--assert-accessibility" in sys.argv and tabs:
  expected={"initial":1,"after-control-t":2,"after-second-control-t":3}
  if step in expected:
   assert len(out.get("uia_selected",[]))==expected[step],(
       "expected tab UIA children",step,out)
   assert sum(int(bool(x[1])) for x in out["uia_selected"])==1,(
       "missing single selected UIA tab",step,out)
   assert out.get("msaa_selection")==str(expected[step]),(
       "MSAA selection differs from physical new tab",step,out)
   assert out.get("msaa_child_count",0)>=expected[step],(
       "missing real MSAA tab children",step,out)
 if tabs:
  region=rect(tabs[0]);ImageGrab.grab(
   bbox=(region[0],region[1],region[2],region[3]),
   include_layered_windows=True).save(folder/(step+"-tab.png"))
 return tabs
proc=None;main=0
try:
 proc=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(cp),
   str(fixture)],cwd=folder,env={**os.environ,"APPDATA":str(folder/"appdata")},
   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  matches=[h for h in en(proc.pid,True) if title(h).endswith(" - fxfile")]
  if len(matches)==1:main=matches[0];break
  time.sleep(.1)
 assert main,"owned main HWND missing"
 if "--env-inventory" in sys.argv:
  class HC(c.Structure):
   _fields_=[("cbSize",w.UINT),("dwFlags",w.DWORD),
      ("lpszDefaultScheme",w.LPWSTR)]
  state=HC();state.cbSize=c.sizeof(state)
  ok=u.SystemParametersInfoW(0x42,state.cbSize,c.byref(state),0)
  print("UXH05_ACTUAL_WINDOWS_DPI",u.GetDpiForWindow(main),
        "HIGH_CONTRAST_QUERY",bool(ok),
        "HIGH_CONTRAST_ON",bool(state.dwFlags&1) if ok else None,
        flush=True)

 u.ShowWindow(main,9)
 assert u.SetWindowPos(main,0,65,65,1080,680,0x0004)
 time.sleep(.8)
 h0=snapshot(main,"initial")
 assert h0,"custom TabCtrl HWND absent"
 rr=rect(main);mouse.click(coords=(rr[0]+140,rr[1]+14))
 assert u.GetForegroundWindow()==main,"refuse keys without owned focus"
 keyboard.send_keys("^t",pause=.055)
 time.sleep(.45)
 h1=snapshot(main,"after-control-t")
 assert len(h1)==len(h0)
 keyboard.send_keys("^t",pause=.055)
 time.sleep(.45)
 h2=snapshot(main,"after-second-control-t")
 if "--invoke-probe" in sys.argv:
  own=h2[0]
  root_uia=Desktop(backend="uia").window(handle=own)
  actions=[x for x in root_uia.descendants()
      if x.element_info.control_type=="Button" and x.is_visible()]
  assert len(actions)>=2,("no UIA buttons",len(actions))
  for a in actions[:3]:
   info=(a.element_info.name,a.element_info.control_type,a.is_enabled())
   try:
    pattern=a.iface_invoke
    supported=bool(pattern)
   except Exception as ex:
    supported=False
    print("UXH05_UIA_PATTERN_EXCEPTION",
         str(info).encode("ascii","backslashreplace").decode(),
         repr(ex)[:125],flush=True)
   print("UXH05_UIA_BUTTON_INVOKE",
       str(info).encode("ascii","backslashreplace").decode(),
       "SUPPORTED",supported,flush=True)
  print("UXH05_UIA_INVOKE_READONLY_DISCOVERY_COMPLETE=True",flush=True)
  if "--invoke-actions" in sys.argv:
   assert len(actions)==2 and all(a.iface_invoke for a in actions)
   def msaa_count():
    check=POINTER(IAccessible)()
    assert ole.AccessibleObjectFromWindow(own,0xFFFFFFFC,
       c.byref(IAccessible._iid_),
       c.cast(c.byref(check),c.POINTER(c.c_void_p)))==0
    return check.accChildCount
   count_before=msaa_count()
   assert count_before==5
   # The actual UIA proxy's InvokePattern on the existing new-tab
   # glyph must create a real fourth owned tab.
   actions[-1].iface_invoke.Invoke()
   time.sleep(.4)
   count_after=msaa_count()
   print("UXH05_REAL_UIA_NEW_BUTTON_INVOKE_COUNTS",
      count_before,count_after,flush=True)
   assert count_after==6
   # Re-resolve the selected-close glyph after the tab collection
   # changes; never act on a stale UIA node.
   changed=[x for x in Desktop(backend="uia").window(
        handle=own).descendants()
        if x.element_info.control_type=="Button" and x.is_visible()]
   assert len(changed)==2
   changed[0].iface_invoke.Invoke()
   time.sleep(.4)
   assert msaa_count()==5,"actual UIA close must remove one owned tab"
   print("UXH05_DIRECT_UIA_INVOKE_NEW_CLOSE_ACTUAL_GUI_PASS=True",
     flush=True)
 if "--actions" in sys.argv:
  own=h2[0]
  pa=POINTER(IAccessible)()
  hr=ole.AccessibleObjectFromWindow(own,0xFFFFFFFC,
      c.byref(IAccessible._iid_),
      c.cast(c.byref(pa),c.POINTER(c.c_void_p)))
  assert hr==0 and pa.accChildCount==5
  assert pa.accSelection==3
  assert pa.accDefaultAction(4)=="Close"
  assert pa.accDefaultAction(5)=="New tab"
  print("OWNED_ACCESSIBLE_BUTTON_ROLES_AND_DEFAULT_ACTIONS_PASS=True",
        flush=True)
  pa.accSelect(3,1)  # TAKEFOCUS | TAKESELECTION
  time.sleep(.24)
  print("OWNED_MSAA_TAKE_SELECTION_FOCUS",pa.accSelection,
        pa.accFocus,flush=True)
  assert pa.accSelection==1 and pa.accFocus==1
  assert u.GetForegroundWindow()==main
  keyboard.send_keys("{RIGHT}",pause=.06)
  time.sleep(.25)
  assert pa.accSelection==2,("real focused right arrow failed",
                            pa.accSelection)
  print("ACTUAL_FOCUS_AFTER_RIGHT",pa.accSelection,pa.accFocus,flush=True)
  keyboard.send_keys("{END}",pause=.06)
  time.sleep(.24)
  print("ACTUAL_FOCUS_AFTER_END",pa.accSelection,pa.accFocus,flush=True)
  assert pa.accSelection==3
  keyboard.send_keys("{HOME}",pause=.06)
  time.sleep(.24)
  assert pa.accSelection==1
  print("OWNED_ACTUAL_FOCUSED_ARROW_HOME_END_PASS=True",flush=True)
  pa.accDoDefaultAction(3)
  time.sleep(.24)
  assert pa.accSelection==3,(
      "accessible tab default action must select",pa.accSelection)
  pa.accDoDefaultAction(4) # selected third close only
  time.sleep(.4)
  assert pa.accChildCount==4,(
      "accessible selected-close action did not remove tab",
      pa.accChildCount)
  print("OWNED_MSAA_SELECT_TAB_AND_CLOSE_ACTUAL_GUI_PASS=True",flush=True)
  pa.accDoDefaultAction(pa.accChildCount) # New tab
  time.sleep(.3)
  assert pa.accChildCount==5 and pa.accSelection==3,(
      "accessible new-button did not add selected tab",
      pa.accChildCount,pa.accSelection)
  print("OWNED_MSAA_NEW_TAB_ACTUAL_GUI_PASS=True",flush=True)
  snapshot(main,"after-accessible-actions")
  keyboard.send_keys("^w",pause=.06)
  time.sleep(.35)
  assert pa.accChildCount==4
  print("OWNED_CTRL_W_CLOSE_ACTUAL_GUI_PASS=True",flush=True)
  # Return focus to main before the standard Ctrl+Tab command checks.
  mouse.click(coords=(rect(main)[0]+150,rect(main)[1]+15))
  assert u.GetForegroundWindow()==main
 keyboard.send_keys("^{TAB}",pause=.055)
 time.sleep(.4)
 snapshot(main,"after-control-tab")
 keyboard.send_keys("^+{TAB}",pause=.055)
 time.sleep(.4)
 snapshot(main,"after-control-shift-tab")
 if "--focusroutes" in sys.argv:
  focus_obj=POINTER(IAccessible)()
  assert ole.AccessibleObjectFromWindow(h2[0],0xFFFFFFFC,
      c.byref(IAccessible._iid_),
      c.cast(c.byref(focus_obj),c.POINTER(c.c_void_p)))==0
  focus_obj.accSelect(3,1)
  time.sleep(.23)
  assert focus_obj.accFocus==1
  print("FOCUS_ROUTE_INITIAL_MSAA_FOCUSED_CHILD",focus_obj.accFocus,
        "SELECTION",focus_obj.accSelection,flush=True)
  keyboard.send_keys("{TAB}")
  time.sleep(.24)
  print("FOCUS_ROUTE_AFTER_PHYSICAL_TAB",
        "FOCUS",focus_obj.accFocus,
        "SELECTION",focus_obj.accSelection,flush=True)
  # F6 is the existing application-wide next-window binding.
  keyboard.send_keys("{F6}")
  time.sleep(.28)
  print("FOCUS_ROUTE_AFTER_PHYSICAL_F6",
        "FOCUS",focus_obj.accFocus,
        "SELECTION",focus_obj.accSelection,
        "TOP_TITLE",title(main).encode("ascii","backslashreplace").decode(),
        flush=True)
 print("ACCESS_DIAG_FOLDER",str(folder),flush=True)
finally:
 if proc and proc.poll() is None:
  if main:u.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=15)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=5)
 same=all(hashlib.sha256((src/n).read_bytes()).digest()==before[n] for n in names)
 print("ORIGINAL_CONFIG_HASHES_IDENTICAL",same,
       "OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert same and proc and proc.returncode==0
