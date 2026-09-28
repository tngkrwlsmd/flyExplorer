"""UXH-07 test-owned native Save/Open named workspace dialogs."""
from pathlib import Path
import ctypes as c,hashlib,os,subprocess,tempfile,shutil,time,re,sys
from ctypes import wintypes as w
from pywinauto import Desktop,keyboard,mouse
import psutil
R=Path(__file__).resolve().parents[1]
user=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((user/n).read_bytes()).hexdigest() for n in names}
home=Path(tempfile.mkdtemp(prefix="uxh07-named-owned-",dir=R/"logs"))
conf=home/"conf";conf.mkdir()
for n in names:shutil.copy2(user/n,conf/n)
appdata=home/"appdata";appdata.mkdir()
fx=home/"fixture";fx.mkdir()
left,right=(fx/"Workspace Owned Left",fx/"Workspace Owned Right")
left.mkdir();right.mkdir()
orig=(conf/"fxfile.conf").read_bytes()
enc="utf-16" if orig[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
opts=orig.decode(enc)
for key,val in (
 ("config.global_hotkey.enable","0"),("config.global_hotkey.show_tray","0"),
 ("config.global_hotkey.windows_startup","0"),
 ("config.register_shell_context_menu","0"),
 ("config.view1.file_list.init_folder","3"),
 ("config.view2.file_list.init_folder","3"),
 ("config.single_process","0")):
 pattern=r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*"
 opts,n=re.subn(pattern,lambda m:m.group(1)+val,opts)
 if not n:
  assert opts.lstrip().startswith("[config]")
  opts=opts.replace("[config]","[config]\n"+key+" = "+val,1)
(conf/"fxfile.conf").write_bytes(opts.encode(enc))
(conf/"fxfile-main.conf").write_text("\n".join(("[main]","main.tip_of_today.show = 0","main.view.row_count = 1",
 "main.view.column_count = 2","main.view.ratio1 = 0.50",
 "main.view1.current_tab = 0","main.view1.tab1.path = "+str(left),
 "main.view2.current_tab = 0","main.view2.tab1.path = "+str(right),"")),
 encoding="utf-16")
u=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):
 _fields_=[(x,c.c_long) for x in ("left","top","right","bottom")]
for name,args in (("EnumWindows",(CALLBACK,w.LPARAM)),("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM)),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD))),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int)),("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int)),
 ("GetWindowRect",(w.HWND,c.POINTER(RECT))),("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM))):
 getattr(u,name).argtypes=args
def en(h,all=False):
 out=[]
 @CALLBACK
 def cb(x,_):
  if all:
   pid=w.DWORD();u.GetWindowThreadProcessId(x,c.byref(pid))
   if pid.value!=h:return True
  out.append(int(x));return True
 if all:u.EnumWindows(cb,0)
 else:u.EnumChildWindows(h,cb,0)
 return out
def cls(h):
 b=c.create_unicode_buffer(160);u.GetClassNameW(h,b,len(b));return b.value
def title(h):
 b=c.create_unicode_buffer(180);u.GetWindowTextW(h,b,len(b));return b.value
def rect(h):
 rr=RECT();u.GetWindowRect(h,c.byref(rr))
 return(rr.left,rr.top,rr.right,rr.bottom)
def frame(pid):
 for _ in range(85):
  x=[h for h in en(pid,True) if title(h).endswith(" - fxfile")]
  if len(x)==1:return x[0]
  time.sleep(.10)
 raise AssertionError("test-owned main frame missing")
def tabs(m):
 return [[x.element_info.name for x in Desktop(backend="uia").window(handle=h).descendants()
    if x.element_info.control_type=="TabItem"]
   for h in en(m) if cls(h)=="TabCtrl" and u.IsWindowVisible(h)]
def dialog(pid,m,when,timeout=80):
 for _ in range(timeout):
  ds=[h for h in en(pid,True) if h!=m and cls(h)=="#32770" and u.IsWindowVisible(h)]
  if ds:return ds[0]
  time.sleep(.1)
 raise AssertionError(when+" file dialog did not open")
p=None;main=0;child=None;childmain=0
before_fly={v.pid for v in psutil.process_iter(["name"])
            if (v.info["name"] or "").lower()=="fxfile.exe"}
try:
 p=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(conf)],
   cwd=home,env={**os.environ,"APPDATA":str(appdata)},
   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 main=frame(p.pid);u.ShowWindow(main,9)
 time.sleep(.7)
 first=tabs(main)
 print("BASELINE_OWNED_WORKSPACE_TWO_PANES",[
   [x.startswith("Workspace Owned") for x in pane] for pane in first],flush=True)
 assert len(first)==2 and sorted([left.name,right.name])==sorted([x for pane in first for x in pane])
 workspace=home/"test-named-workspace.fxworkspace"
 assert u.PostMessageW(main,0x111,33052,0)
 h=dialog(p.pid,main,"Save")
 print("REAL_NATIVE_SAVE_DIALOG",cls(h),title(h).encode("ascii","backslashreplace").decode(),flush=True)
 controls=[(x.element_info.control_type,x.element_info.name) for x in
   Desktop(backend="uia").window(handle=h).descendants() if x.is_visible()]
 print("FILE_DIALOG_UIA_STRUCTURE",[(a,b.encode("ascii","backslashreplace").decode()[:75]) for a,b in controls[:42]],flush=True)
 if "--probe" in sys.argv:
  u.PostMessageW(h,0x10,0,0)
 else:
  edits=[x for x in Desktop(backend="uia").window(handle=h).descendants()
    if x.is_visible() and x.element_info.control_type=="Edit"]
  print("REAL_SAVE_EDIT_NAMES",[
   x.element_info.name.encode("ascii","backslashreplace").decode()[:95]
   for x in edits],flush=True)
  print("FILE_DIALOG_EDIT_COUNT",len(edits),flush=True)
  assert edits,"native save edit not discoverable"
  filename=[x for x in edits
     if x.element_info.name.strip().endswith(":")
        or "file name" in x.element_info.name.lower()]
  assert len(filename)==1,("file-name edit ambiguous",
      [x.element_info.name for x in edits])
  filename[0].set_edit_text(str(workspace))
  filename[0].set_focus()
  keyboard.send_keys("{ENTER}")
  for _ in range(90):
   if workspace.is_file():break
   time.sleep(.1)
  assert workspace.is_file(),"actual file dialog did not save owned workspace"
  contents=workspace.read_text(encoding="utf-16")
  print("WORKSPACE_FILE_WRITTEN",workspace.stat().st_size,
       "HAS_MAIN",("[main]" in contents),
       "HAS_SCHEMA",("[workspace]" in contents),flush=True)
  assert all(k in contents for k in ("[workspace]","schema = 1",left.name,right.name))
  assert u.PostMessageW(main,0x111,33053,0)
  opened=dialog(p.pid,main,"Open")
  print("REAL_NATIVE_OPEN_DIALOG",cls(opened),title(opened).encode("ascii","backslashreplace").decode(),flush=True)
  edits=[x for x in Desktop(backend="uia").window(handle=opened).descendants()
         if x.is_visible() and x.element_info.control_type=="Edit"]
  assert edits,"native open edit not found"
  filename=[x for x in edits
     if x.element_info.name.strip().endswith(":")
        or "file name" in x.element_info.name.lower()]
  assert len(filename)==1,("file-name edit ambiguous",
      [x.element_info.name for x in edits])
  filename[0].set_edit_text(str(workspace))
  filename[0].set_focus()
  keyboard.send_keys("{ENTER}")
  for _ in range(90):
   possible=[]
   for q in psutil.process_iter(["name"]):
    if q.pid in before_fly or q.pid==p.pid:continue
    try:
     if (q.info["name"] or "").lower()!="fxfile.exe" or q.ppid()!=p.pid:continue
     cmd=" ".join(q.cmdline())
     if "--conf_dir" in cmd and "fxw" in cmd:
      possible.append(q)
    except (psutil.NoSuchProcess,psutil.AccessDenied):continue
   if len(possible)==1:
    child=possible[0];break
   time.sleep(.13)
  assert child,"owned parent failed to spawn distinct workspace process"
  childmain=frame(child.pid)
  actual=[]
  for _ in range(70):
   actual=tabs(childmain)
   if len(actual)==2 and all(actual):break
   time.sleep(.1)
  if len(actual)!=2:
   print("CHILD_RESTORE_DIAGNOSTIC",
     "MAIN_TITLE",title(childmain).encode("ascii","backslashreplace").decode(),
     "CHILD_CLASSES",[cls(h) for h in en(childmain)][:17],
     "TOP_DIALOGS",[(cls(h),title(h).encode("ascii","backslashreplace").decode())
        for h in en(child.pid,True) if cls(h)=="#32770"],
     flush=True)
  print("REAL_ISOLATED_WORKSPACE_GUI_PANES",
    [[left.name in name or right.name in name for name in pane] for pane in actual],
    flush=True)
  assert len(actual)==2
  assert sorted(name for pane in actual for name in pane)==sorted((left.name,right.name))
  print("WORKSPACE_NEW_WINDOW_DISTINCT_PID",child.pid!=p.pid,flush=True)
  print("ORIGINAL_WINDOW_TABS_AFTER_OPEN",tabs(main),flush=True)
  assert tabs(main)==first,"opening workspace altered current pane state"
  print("WORKSPACE_REAL_NATIVE_SAVE_OPEN_DIALOGS_COMPLETE=True",flush=True)
  if "--multiple" in sys.argv:
   if childmain and u.IsWindow(childmain):u.PostMessageW(childmain,0x10,0,0)
   if child:child.wait(timeout=12)
   child=None;childmain=0
   active=next(h for h in en(main)
     if cls(h)=="TabCtrl" and u.IsWindowVisible(h))
   rr=rect(active)
   mouse.click(coords=((rr[0]+rr[2])//2,(rr[1]+rr[3])//2))
   keyboard.send_keys("^t",pause=.055)
   for _ in range(45):
    later=tabs(main)
    if sorted(len(q) for q in later)==[1,2]:break
    time.sleep(.12)
   assert sorted(len(q) for q in later)==[1,2],later
   second=home/"second-distinct-named.fxworkspace"
   assert u.PostMessageW(main,0x111,33052,0)
   save=dialog(p.pid,main,"second Save")
   edits=[x for x in Desktop(backend="uia").window(handle=save).descendants()
      if x.is_visible() and x.element_info.control_type=="Edit"
      and x.element_info.name.strip().endswith(":")]
   assert len(edits)==1
   edits[0].set_edit_text(str(second));edits[0].set_focus()
   keyboard.send_keys("{ENTER}")
   for _ in range(65):
    if second.is_file():break
    time.sleep(.12)
   assert second.is_file(),"second different named workspace not saved"
   assert first!=later
   assert workspace.read_bytes()!=second.read_bytes(),(
        "two named snapshots must differ when active tabs differ")
   print("TWO_DISTINCT_NAMED_FILES_WITH_DIFFERENT_TAB_LAYOUTS=True",flush=True)
   assert u.PostMessageW(main,0x111,33053,0)
   op=dialog(p.pid,main,"second Open")
   edits=[x for x in Desktop(backend="uia").window(handle=op).descendants()
      if x.is_visible() and x.element_info.control_type=="Edit"
      and x.element_info.name.strip().endswith(":")]
   assert len(edits)==1
   edits[0].set_edit_text(str(second));edits[0].set_focus()
   keyboard.send_keys("{ENTER}")
   for _ in range(80):
    possibles=[]
    for q in psutil.process_iter(["name"]):
     if q.pid in before_fly or q.pid==p.pid:continue
     try:
      if (q.info["name"] or "").lower()=="fxfile.exe" and q.ppid()==p.pid:
       cmd=" ".join(q.cmdline())
       if "--conf_dir" in cmd and "fxw" in cmd:possibles.append(q)
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    if len(possibles)==1:child=possibles[0];break
    time.sleep(.13)
   assert child,"second named workspace did not open separate window"
   childmain=frame(child.pid)
   result=[]
   for _ in range(70):
    result=tabs(childmain)
    if sorted(len(q) for q in result)==[1,2]:break
    time.sleep(.13)
   assert sorted(len(q) for q in result)==[1,2],result
   assert tabs(main)==later,"second workspace replaced original window"
   print("SECOND_NAMED_WORKSPACE_GUI_RESTORED_DIFFERENT_2_1_TABS=True",flush=True)
finally:
 if child and child.is_running():
  if childmain and u.IsWindow(childmain):
   u.PostMessageW(childmain,0x10,0,0)
  try:child.wait(timeout=11)
  except psutil.TimeoutExpired:
   # Only the test-owned child (direct PID and private conf_dir) may end.
   child.terminate();child.wait(timeout=5)
  print("OWNED_WORKSPACE_CHILD_EXIT",child.returncode if hasattr(child,"returncode")
        else child.wait(timeout=1),flush=True)
 if p and p.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:p.wait(timeout=13)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=4)
 same=all(hashlib.sha256((user/n).read_bytes()).hexdigest()==before[n] for n in names)
 print("ORIGINAL_SETTINGS_SIX_HASHES_IDENTICAL",same,
       "TEST_OWNED_EXIT",p.returncode if p else None,
       "OWNED_FIXTURE",str(home),flush=True)
 assert same and p and p.returncode==0
