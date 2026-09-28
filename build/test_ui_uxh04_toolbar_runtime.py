"""UXH-04 owned toolbar geometry and discoverability baseline, no source modifications."""
from pathlib import Path
import ctypes as c,os,hashlib,shutil,tempfile,subprocess,time,re,sys
from ctypes import wintypes as w
from PIL import ImageGrab
R=Path(__file__).resolve().parents[1];src=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in names}
folder=Path(tempfile.mkdtemp(prefix="uxh04-owned-",dir=R/"logs"))
cp=folder/"conf";cp.mkdir();fixture=folder/"fixture";fixture.mkdir()
for n in names:shutil.copy2(src/n,cp/n)
raw=(cp/"fxfile.conf").read_bytes();enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
cfg=raw.decode(enc)
for k,v in (("config.theme_mode","2"),("config.global_hotkey.enable","0"),
 ("config.global_hotkey.show_tray","0"),("config.global_hotkey.windows_startup","0"),
 ("config.register_shell_context_menu","0")):
 cfg,num=re.subn(r"(?m)^(\s*"+re.escape(k)+r"\s*=\s*)[^\r\n]*",lambda m:m.group(1)+v,cfg)
 assert num==1,k
(cp/"fxfile.conf").write_bytes(cfg.encode(enc))
original_saved_band=(cp/"fxfile-coolbar.dat").read_bytes()
if "--fresh" in sys.argv:(cp/"fxfile-coolbar.dat").unlink()
(folder/"appdata").mkdir()
for i in range(3):(fixture/("command-layout-test-%d.txt"%i)).write_text("owned",encoding="utf-8")
u=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):_fields_=[(k,c.c_long) for k in ("left","top","right","bottom")]
for name,args in (("EnumWindows",(CALLBACK,w.LPARAM)),("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM)),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD))),("GetWindowRect",(w.HWND,c.POINTER(RECT))),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int)),("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int)),
 ("SetWindowPos",(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)),
 ("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM)),
 ("SendMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM))):
 getattr(u,name).argtypes=args
u.SendMessageW.restype=c.c_ssize_t
def rect(h):
 a=RECT();u.GetWindowRect(h,c.byref(a));return(a.left,a.top,a.right,a.bottom)
def cl(h):
 a=c.create_unicode_buffer(110);u.GetClassNameW(h,a,len(a));return a.value
def title(h):
 a=c.create_unicode_buffer(210);u.GetWindowTextW(h,a,len(a));return a.value
def en(h,all=False):
 out=[]
 @CALLBACK
 def cb(x,_):
  if all:
   p=w.DWORD();u.GetWindowThreadProcessId(x,c.byref(p))
   if p.value!=h:return True
  out.append(int(x));return True
 if all:u.EnumWindows(cb,0)
 else:u.EnumChildWindows(h,cb,0)
 return out
def wd(r):return r[2]-r[0]
def ht(r):return r[3]-r[1]
proc=None;main=0
try:
 proc=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(cp),str(fixture)],cwd=folder,
  env={**os.environ,"APPDATA":str(folder/"appdata")},stdin=subprocess.DEVNULL,
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  matches=[h for h in en(proc.pid,True) if title(h).endswith(" - fxfile")]
  if len(matches)==1:main=matches[0];break
  time.sleep(.1)
 assert main
 u.ShowWindow(main,9)
 for outer in (750,1100):
  assert u.SetWindowPos(main,0,65,65,outer,550 if outer==750 else 720,0x0004)
  time.sleep(.9)
  u.PostMessageW(main,0x111,35003,0) if outer==750 else None
  time.sleep(.45)
  ch=[(cl(h),rect(h),h) for h in en(main) if u.IsWindowVisible(h)]
  toolbar=[(k,r,h) for k,r,h in ch if k in ("ToolbarWindow32","ReBarWindow32","CoolBar")]
  rebars=[(k,r,h) for k,r,h in ch if "ReBar" in k or "Rebar" in k]
  lists=[(k,r,h) for k,r,h in ch if k=="SysListView32"]
  print("SCENARIO",("FRESH" if "--fresh" in sys.argv else "SAVED"),outer,
        "MAIN",rect(main),"TOOLBARS",[(k,r) for k,r,_ in toolbar],
        "REBARS",[(k,r) for k,r,_ in rebars],
        "LISTS",[(r[1],r[3]) for _,r,_ in lists],flush=True)
  for _,r,h in rebars:
   num=int(u.SendMessageW(h,0x40C,0,0))
   print("REBAR_BAND_COUNT",num,"RECT",r,"HEIGHT",ht(r),flush=True)
  if outer==750:
   from pywinauto import Desktop
   visible=[]
   for control in Desktop(backend="uia").window(handle=main).descendants():
    try:
     if control.is_visible() and control.element_info.control_type in ("Button","MenuItem","SplitButton"):
      b=control.rectangle();visible.append((control.element_info.control_type,
           control.element_info.name.encode("ascii","backslashreplace").decode()[:60],
           (b.left,b.top,b.right,b.bottom)))
    except Exception:pass
   print("UIA_VISIBLE_COMMANDS",len(visible),"SAMPLES",visible[:24],flush=True)
   if "--exercise" in sys.argv or "--persist" in sys.argv:
    assert "--fresh" not in sys.argv,"only a saved layout is eligible"
    from pywinauto import mouse,keyboard
    def visible_popups():
     return [h for h in en(proc.pid,True)
             if cl(h)=="#32768" and u.IsWindowVisible(h)]
    def print_menu(hwnd,tag):
     try:
      items=[x for x in Desktop(backend="uia").window(handle=hwnd).descendants()
             if x.element_info.control_type=="MenuItem"]
      names=[(x.element_info.name.encode("ascii","backslashreplace").decode()[:78],
              str(x.rectangle())) for x in items]
      print("REAL_MENU",tag,names[:21],flush=True)
      return items
     except Exception as ex:
      print("REAL_MENU_UNAVAILABLE",tag,str(ex)[:100],flush=True)
      return []
    def click_compact_menu():
     # Actual owned title-bar click ensures Alt+V cannot affect other apps.
     mr=rect(main);mouse.click(coords=(mr[0]+170,mr[1]+14))
     assert u.GetForegroundWindow()==main, "refusing global keys on other app"
     keyboard.send_keys("%v",pause=.03)
     time.sleep(.4)
     before_popups=visible_popups()
     print("VIEW_MENU_POPUPS",[(h,rect(h)) for h in before_popups],flush=True)
     if not before_popups:
      raise AssertionError("Alt+V did not physically open View menu")
     items=print_menu(before_popups[-1],"view")
     first=next((x for x in items if x.is_visible()),None)
     assert first,"View menu exposed no items to UI automation"
     ri=first.rectangle()
     mouse.move(coords=((ri.left+min(65,ri.right-ri.left-7)),(ri.top+ri.bottom)//2))
     time.sleep(.45)
     opened=[h for h in visible_popups() if h not in before_popups]
     if not opened:
      # Normal native arrow-key entry into the first View submenu.
      keyboard.send_keys("{HOME}{RIGHT}")
      time.sleep(.4)
      opened=[h for h in visible_popups() if h not in before_popups]
     assert opened,"Tools submenu could not be opened using pointer or keyboard"
     options=print_menu(opened[-1],"tools")
     # This legacy owner-drawn MFC menu exposes empty UIA item names.
     # Identify the exact native command ID, then click its real screen
     # menu-item rectangle. NEVER guess a menu row index or post WM_COMMAND.
     u.GetMenuItemCount.argtypes=(w.HMENU,)
     u.GetMenuItemCount.restype=c.c_int
     u.GetMenuItemID.argtypes=(w.HMENU,c.c_int)
     u.GetMenuItemID.restype=w.UINT
     u.GetMenuItemRect.argtypes=(w.HWND,w.HMENU,w.UINT,c.POINTER(RECT))
     u.GetMenuItemRect.restype=w.BOOL
     hmenu=int(u.SendMessageW(opened[-1],0x01E1,0,0))
     n=u.GetMenuItemCount(hmenu) if hmenu else -1
     found=[i for i in range(n) if u.GetMenuItemID(hmenu,i)==33049]
     print("NATIVE_COMPACT_MENU_COMMAND_POS",found,"TOTAL",n,flush=True)
     assert len(found)==1,("real native command ID 33049 missing",n,found)
     bound=RECT()
     assert u.GetMenuItemRect(main,hmenu,found[0],c.byref(bound))
     assert bound.right>bound.left and bound.bottom>bound.top
     print("NATIVE_COMPACT_MENU_ITEM_RECT",
           (bound.left,bound.top,bound.right,bound.bottom),flush=True)
     mouse.click(coords=(bound.left+min(110,(bound.right-bound.left)//2),
                         (bound.top+bound.bottom)//2))
     time.sleep(.65)
    # The native rebar HWND remains the same while its screen rect changes.
    rebar_hwnd=rebars[0][2]
    rebar_height=lambda:ht(rect(rebar_hwnd))
    assert rebar_height()==141,("saved layout baseline changed",rebar_height())
    click_compact_menu()
    print("REAL_COMPACTED_REBAR_HEIGHT",rebar_height(),flush=True)
    assert rebar_height()==101,("user-click compact mode did not free row",rebar_height())
    if "--exercise" in sys.argv:
     click_compact_menu()
     print("REAL_RESTORED_REBAR_HEIGHT",rebar_height(),flush=True)
     assert rebar_height()==141,("second user click failed to restore",rebar_height())
     print("UXH04_ACTUAL_POINTER_MENU_TOGGLE_AND_RESTORE_PASS=True",flush=True)
    else:
     print("UXH04_ACTUAL_POINTER_COMPACT_LEFT_ACTIVE_UNTIL_EXIT=True",flush=True)

  ImageGrab.grab(bbox=rect(main),include_layered_windows=True).save(folder/(str(outer)+".png"))
 print("BASELINE_EVIDENCE_FOLDER",folder,flush=True)
finally:
 if proc and proc.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:proc.wait(timeout=14)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=4)
 after={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in names}
 copy_saved=(cp/"fxfile-coolbar.dat").read_bytes()
 if "--exercise" in sys.argv or "--persist" in sys.argv:
  print("OWNED_COOLBAR_PERSISTED_LAYOUT_IDENTICAL_TO_ORIGINAL",
        copy_saved==original_saved_band,flush=True)
  assert copy_saved==original_saved_band,(
      "temporary compact mode must not persist or erase custom band layout")
 print("ORIGINAL_SETTINGS_IDENTICAL",after==before,"OWNED_EXIT",proc.returncode if proc else None,flush=True)
 assert after==before and proc is not None and proc.returncode==0
