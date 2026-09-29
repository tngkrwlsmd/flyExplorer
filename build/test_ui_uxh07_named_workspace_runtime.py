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
def invoke_workspace_menu(which,mode):
 # Actual foreground physical key or pointer activation, NEVER
 # blindly use menu positions as a keyboard Enter command.
 target=33052 if which=="save" else 33053
 assert u.IsWindow(main)
 # Match previously validated UXH-04 owner-drawn menu's focus path.
 bounds=rect(main)
 mouse.click(coords=(bounds[0]+170,bounds[1]+14))
 assert u.GetForegroundWindow()==main
 root_before={h for h in en(p.pid,True)
              if cls(h)=="#32768" and u.IsWindowVisible(h)}
 keyboard.send_keys("%v",pause=.09)
 time.sleep(.28)
 new=[h for h in en(p.pid,True) if
      cls(h)=="#32768" and u.IsWindowVisible(h) and h not in root_before]
 if not new:
  print("WORKSPACE_ALT_V_SAFE_DIAGNOSTIC",
     "BEFORE",len(root_before),
     "AFTER",[(cls(h),title(h)) for h in en(p.pid,True)
       if cls(h)=="#32768"],
     "FOREGROUND",u.GetForegroundWindow()==main,flush=True)
 assert new,"physical Alt+V did not open owned View menu"
 root=int(u.SendMessageW(new[-1],0x01E1,0,0))
 u.GetMenuItemCount.argtypes=(w.HMENU,)
 u.GetMenuItemCount.restype=c.c_int
 u.GetSubMenu.argtypes=(w.HMENU,c.c_int)
 u.GetSubMenu.restype=w.HMENU
 u.GetMenuItemID.argtypes=(w.HMENU,c.c_int)
 u.GetMenuItemID.restype=w.UINT
 u.GetMenuState.argtypes=(w.HMENU,w.UINT,w.UINT)
 u.GetMenuState.restype=w.UINT
 u.GetMenuItemRect.argtypes=(w.HWND,w.HMENU,w.UINT,c.POINTER(RECT))
 u.GetMenuItemRect.restype=w.BOOL
 matches=[]
 for i in range(u.GetMenuItemCount(root)):
  sub=u.GetSubMenu(root,i)
  if not sub:continue
  sub=int(sub)
  ids=[u.GetMenuItemID(sub,j) for j in range(u.GetMenuItemCount(sub))]
  if ids.count(33052)==1 and ids.count(33053)==1:matches.append((i,sub))
 assert len(matches)==1,("workspace submenu not uniquely owned",matches)
 index,sub=matches[0]
 assert not (int(u.GetMenuState(sub,target,0))&3),("disabled native command",target)
 print("WORKSPACE_REAL_NATIVE_MENU_COMMAND_IDS_VERIFIED",which,
       mode,"SUBMENU_POSITION",index,flush=True)
 if mode=="keyboard":
  keyboard.send_keys("w",pause=.09)
  time.sleep(.21)
  visible=[h for h in en(p.pid,True) if cls(h)=="#32768"
          and u.IsWindowVisible(h) and h not in new]
  assert visible,"physical W did not open verified Workspaces submenu"
  menu=int(u.SendMessageW(visible[-1],0x01E1,0,0))
  ids=[u.GetMenuItemID(menu,j) for j in range(u.GetMenuItemCount(menu))]
  assert ids.count(target)==1,("opened unexpected W submenu",ids,target)
  keyboard.send_keys("s" if target==33052 else "o",pause=.085)
  print("WORKSPACE_VERIFIED_REAL_PHYSICAL_MNEMONIC_DISPATCH",which,flush=True)
 else:
  bound=RECT()
  assert u.GetMenuItemRect(main,root,index,c.byref(bound))
  mouse.move(coords=((bound.left+bound.right)//2,(bound.top+bound.bottom)//2))
  time.sleep(.4)
  visible=[h for h in en(p.pid,True) if cls(h)=="#32768"
           and u.IsWindowVisible(h) and h not in new]
  assert visible,"physical pointer hover did not open submenu"
  actual=int(u.SendMessageW(visible[-1],0x01E1,0,0))
  ids=[u.GetMenuItemID(actual,j) for j in range(u.GetMenuItemCount(actual))]
  assert ids.count(target)==1,("pointer displayed unexpected submenu",ids)
  leaf=RECT()
  idx=ids.index(target)
  assert u.GetMenuItemRect(main,actual,idx,c.byref(leaf))
  mouse.click(coords=((leaf.left+leaf.right)//2,(leaf.top+leaf.bottom)//2))
  print("WORKSPACE_VERIFIED_REAL_PHYSICAL_POINTER_DISPATCH",which,flush=True)
 time.sleep(.28)
def tabs(m):
 return [[x.element_info.name for x in Desktop(backend="uia").window(handle=h).descendants()
    if x.element_info.control_type=="TabItem"]
   for h in en(m) if cls(h)=="TabCtrl" and u.IsWindowVisible(h)]
def dialog(pid,m,when,timeout=80):
 for _ in range(timeout):
  ds=[h for h in en(pid,True) if h!=m and cls(h)=="#32770"
      and u.IsWindowVisible(h) and title(h)!="Workspaces"]
  for h in ds:
   try:
    fields=[x for x in Desktop(backend="uia").window(handle=h).descendants()
      if x.is_visible() and x.element_info.control_type=="Edit"
      and x.element_info.name.strip().endswith(":")]
    if len(fields)==1:return h
   except Exception:pass
  time.sleep(.1)
 raise AssertionError(when+" file dialog did not open")
p=None;main=0;child=None;childmain=0
u.SendMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.SendMessageW.restype=c.c_ssize_t
owned_child_dirs=[]
def check_child_isolation(q):
 cmd=q.cmdline()
 assert "--conf_dir" in cmd,cmd
 folder=Path(cmd[cmd.index("--conf_dir")+1])
 assert folder.name.startswith("fxw") and folder.suffix==".tmp"
 assert (folder/"fxfile-workspace-owned.marker").is_file()
 for opt in ("fxfile-toolbar.dat","fxfile-coolbar.dat"):
  assert (folder/opt).read_bytes()==(conf/opt).read_bytes(),opt
 owned_child_dirs.append(folder)
 print("OWNED_CHILD_PRIVATE_MARKER_AND_CUSTOM_TOOLBARS_COPIED=True",flush=True)
def assert_child_cleaned(folder):
 for _ in range(65):
  if not folder.exists():break
  time.sleep(.1)
 assert not folder.exists(),("private session still present after normal exit",
                            [p.name for p in folder.iterdir()] if folder.exists() else [])
 print("OWNED_CHILD_PRIVATE_CONFIG_REMOVED_AFTER_EXIT=True",flush=True)
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
 (invoke_workspace_menu("save", "keyboard" if
    "--menu-keyboard" in sys.argv else "pointer") if
    ("--menu-keyboard" in sys.argv or "--menu-pointer" in sys.argv)
    else u.PostMessageW(main,0x111,33052,0))
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
  (invoke_workspace_menu("open", "keyboard" if
    "--menu-keyboard" in sys.argv else "pointer") if
    ("--menu-keyboard" in sys.argv or "--menu-pointer" in sys.argv)
    else u.PostMessageW(main,0x111,33053,0))
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
  if child is None:
   warns=[]
   for h in en(p.pid,True):
    if cls(h)=="#32770" and u.IsWindowVisible(h):
     try:
      labels=[x.element_info.name.encode("ascii","backslashreplace").decode()
        for x in Desktop(backend="uia").window(handle=h).descendants()
        if x.element_info.control_type=="Text"]
     except Exception:labels=[]
     warns.append((title(h).encode("ascii","backslashreplace").decode(),labels))
   print("VALID_WORKSPACE_OPEN_NOT_SPAWNED_MODAL_DIAGNOSTIC",warns,flush=True)
  assert child,"owned parent failed to spawn distinct workspace process"
  check_child_isolation(child)
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
  if "--negative" in sys.argv:
   if childmain and u.IsWindow(childmain):
    u.PostMessageW(childmain,0x10,0,0)
   if child:child.wait(timeout=12)
   if owned_child_dirs:assert_child_cleaned(owned_child_dirs[-1])
   child=None;childmain=0
   base=workspace.read_text(encoding="utf-16")
   target=str(left)
   # Verify that every malformed synthetic fixture actually changes
   # the correctly parsed value before opening any native dialog.
   def rewrite(key,value):
    pattern=r"(?m)^([ \t]*"+re.escape(key)+r"[ \t]*=[ \t]*)[^\r\n]*"
    changed,count=re.subn(pattern,lambda m:m.group(1)+value,base)
    assert count==1 and changed!=base,("invalid fixture not modified",key,count)
    assert re.search(r"(?m)^"+re.escape(key)+r"[ \t]*=[ \t]*"+re.escape(value)+r"$",changed),key
    return changed
   new_schema=rewrite("schema","2")
   new_row=rewrite("main.view.row_count","0")
   missing_tab=rewrite("main.view1.tab1.path","")
   missing_folder=base.replace(target,str(home/"does-not-exist-uxh07"))
   assert missing_folder!=base
   malformed=[
    ("empty",b""),
    ("unknown-schema",new_schema.encode("utf-16")),
    ("bad-row",new_row.encode("utf-16")),
    ("missing-tab",missing_tab.encode("utf-16")),
    ("missing-folder",missing_folder.encode("utf-16")),
    ("oversize",b"x"*1048577),
    ("truncated",base.encode("utf-16")[:23]),
    ("wrong-extension",base.encode("utf-16"))]
   print("INVALID_FIXTURES_CHECKED_BEFORE_GUI",len(malformed),flush=True)
   for name,blob in malformed:
    suffix=".txt" if name=="wrong-extension" else ".fxworkspace"
    path=home/("bad-"+name+suffix)
    path.write_bytes(blob)
    assert u.PostMessageW(main,0x111,33053,0)
    opened=dialog(p.pid,main,"invalid "+name)
    edits=[x for x in Desktop(backend="uia").window(handle=opened).descendants()
       if x.is_visible() and x.element_info.control_type=="Edit"
       and x.element_info.name.strip().endswith(":")]
    assert len(edits)==1,("invalid native file-name edit",name)
    edits[0].set_edit_text(str(path));edits[0].set_focus()
    keyboard.send_keys("{ENTER}")
    warning=None
    for _ in range(85):
     matches=[h for h in en(p.pid,True)
         if cls(h)=="#32770" and u.IsWindowVisible(h)
         and title(h)=="Workspaces"]
     if matches:warning=matches[0];break
     time.sleep(.09)
    assert warning,("no warning for malformed user workspace",name)
    labels=[x.element_info.name for x in
       Desktop(backend="uia").window(handle=warning).descendants()
       if x.element_info.control_type=="Text"]
    assert labels,("empty validation warning",name)
    print("REAL_INVALID_WORKSPACE_WARNING",name,
      [v.encode("ascii","backslashreplace").decode()[:95] for v in labels],flush=True)
    # Only the verified TEST-OWNED warning's actual OK button may be
    # clicked. Posting WM_COMMAND(IDOK) to a MFC MessageBox is not
    # equivalent to physical mouse input and failed in the baseline.
    wrapper=Desktop(backend="uia").window(handle=warning)
    buttons=[x for x in wrapper.descendants() if
      x.element_info.control_type=="Button" and x.is_visible()
      and x.is_enabled()]
    print("OWNED_WARNING_BUTTONS",name,
      [(x.element_info.name.encode("ascii","backslashreplace").decode()[:80],
        x.element_info.automation_id) for x in buttons],flush=True)
    # Identify the real native affirmative button by observed UIA ID
    # 2; the separate title-bar Close button has no automation ID.
    # Avoid localized text in the remote test source, which can be
    # transcoded by PowerShell on this specific development machine.
    ok=[x for x in buttons if x.element_info.automation_id=="2"]
    assert len(ok)==1,("expected unique native affirmative control",
      name,[(x.element_info.name.encode("ascii","backslashreplace").decode(),
             x.element_info.automation_id) for x in buttons])
    assert u.GetForegroundWindow()==warning,(
       "do not click until the expected test-owned warning is foreground",
       name,u.GetForegroundWindow(),warning)
    ok[0].click_input()
    for _ in range(55):
     if not u.IsWindow(warning) or not u.IsWindowVisible(warning):break
     time.sleep(.08)
    if u.IsWindow(warning) and u.IsWindowVisible(warning):
     # On this owned Windows 11 desktop a mouse click can occasionally
     # leave the same modal visible. Use a *real physical Enter* only
     # if that exact verified test-owned dialog still has the foreground.
     assert u.GetForegroundWindow()==warning,(
        "ambiguous active window after owned OK click; refuse keyboard",
        name,u.GetForegroundWindow(),warning)
     keyboard.send_keys("{ENTER}",pause=.06)
     for _ in range(50):
      if not u.IsWindow(warning) or not u.IsWindowVisible(warning):break
      time.sleep(.08)
    assert not u.IsWindowVisible(warning),(
       "physical button AND foreground-confirmed Enter failed",name)
    assert tabs(main)==first,("invalid workspace touched active tabs",name)
    unexpected=[]
    for q in psutil.process_iter(["name"]):
     try:
      if q.pid not in before_fly and q.pid!=p.pid and q.ppid()==p.pid:
       if (q.info["name"] or "").lower()=="fxfile.exe":
        unexpected.append(q.pid)
     except(psutil.NoSuchProcess,psutil.AccessDenied):pass
    assert not unexpected,("invalid fixture spawned a real app child",name,
                           unexpected)
    assert child is None
   print("INVALID_WORKSPACE_FILES_REJECTED_BY_REAL_NATIVE_DIALOGS",
         len(malformed),flush=True)
  print("WORKSPACE_REAL_NATIVE_SAVE_OPEN_DIALOGS_COMPLETE=True",flush=True)
  if "--multiple" in sys.argv:
   if childmain and u.IsWindow(childmain):u.PostMessageW(childmain,0x10,0,0)
   if child:child.wait(timeout=12)
   if owned_child_dirs: assert_child_cleaned(owned_child_dirs[-1])
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
   (invoke_workspace_menu("save", "keyboard" if
    "--menu-keyboard" in sys.argv else "pointer") if
    ("--menu-keyboard" in sys.argv or "--menu-pointer" in sys.argv)
    else u.PostMessageW(main,0x111,33052,0))
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
   (invoke_workspace_menu("open", "keyboard" if
    "--menu-keyboard" in sys.argv else "pointer") if
    ("--menu-keyboard" in sys.argv or "--menu-pointer" in sys.argv)
    else u.PostMessageW(main,0x111,33053,0))
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
   if child is None:
    warnings=[]
    for h in en(p.pid,True):
     if cls(h)=="#32770" and u.IsWindowVisible(h):
      try:
       labels=[x.element_info.name.encode("ascii","backslashreplace").decode()
        for x in Desktop(backend="uia").window(handle=h).descendants()
        if x.element_info.control_type=="Text"]
      except Exception:labels=[]
      warnings.append((title(h).encode("ascii","backslashreplace").decode(),labels))
    print("SECOND_WORKSPACE_NOT_SPAWNED_NATIVE_DIALOGS",warnings,flush=True)
   assert child,"second named workspace did not open separate window"
   check_child_isolation(child)
   childmain=frame(child.pid)
   result=[]
   for _ in range(70):
    result=tabs(childmain)
    if sorted(len(q) for q in result)==[1,2]:break
    time.sleep(.13)
   assert sorted(len(q) for q in result)==[1,2],result
   assert tabs(main)==later,"second workspace replaced original window"
   print("SECOND_NAMED_WORKSPACE_GUI_RESTORED_DIFFERENT_2_1_TABS=True",flush=True)
   if "--restart" in sys.argv:
    # Close both original owned windows normally, then reuse the
    # SAME private conf directory in a different real parent process.
    assert u.PostMessageW(childmain,0x10,0,0)
    assert child.wait(timeout=14)==0
    assert_child_cleaned(owned_child_dirs[-1])
    child=None;childmain=0
    assert u.PostMessageW(main,0x10,0,0)
    assert p.wait(timeout=14)==0
    p=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(conf)],
      cwd=home,env={**os.environ,"APPDATA":str(appdata)},
      stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL)
    main=frame(p.pid);u.ShowWindow(main,9)
    restored_parent=[]
    for _ in range(65):
     restored_parent=tabs(main)
     if sorted(len(q) for q in restored_parent)==[1,2]:break
     time.sleep(.12)
    assert sorted(len(q) for q in restored_parent)==[1,2],(
      "original Last Tabs session was not restored after parent restart",
      restored_parent)
    for path,expected in ((workspace,(1,1)),(second,(1,2))):
     assert u.PostMessageW(main,0x111,33053,0)
     op=dialog(p.pid,main,"restarted Open")
     edits=[x for x in Desktop(backend="uia").window(handle=op).descendants()
        if x.is_visible() and x.element_info.control_type=="Edit"
        and x.element_info.name.strip().endswith(":")]
     assert len(edits)==1
     edits[0].set_edit_text(str(path));edits[0].set_focus()
     actual_input=edits[0].iface_value.CurrentValue
     assert path.is_file() and path.stat().st_size>0
     print("RESTART_NATIVE_FILE_INPUT",
           path.name,"EXACT",actual_input==str(path),
           "BYTES",path.stat().st_size,flush=True)
     assert actual_input==str(path),(
       "real file name edit differs from test-owned snapshot",
       actual_input,str(path))
     if u.GetForegroundWindow()!=op:
      bounds=edits[0].rectangle()
      mouse.click(coords=((bounds.left+bounds.right)//2,
                          (bounds.top+bounds.bottom)//2))
     assert u.GetForegroundWindow()==op,(
       "restarted native file dialog is not foreground; refuse blind Enter",
       path.name,u.GetForegroundWindow(),op)
     print("RESTARTED_DIALOG_FOREGROUND_CONFIRMED",path.name,flush=True)
     open_buttons=[x for x in Desktop(backend="uia").window(handle=op).descendants()
        if x.element_info.control_type=="Button" and x.is_visible()
        and x.is_enabled() and x.element_info.automation_id=="1"]
     assert len(open_buttons)==1,(
       "test-owned native Open button not uniquely identified",
       [(x.element_info.name.encode("ascii","backslashreplace").decode(),
         x.element_info.automation_id)
        for x in Desktop(backend="uia").window(handle=op).descendants()
        if x.element_info.control_type=="Button" and x.is_visible()])
     open_buttons[0].click_input()
     print("RESTART_NATIVE_OPEN_BUTTON_PHYSICAL_CLICK",path.name,flush=True)
     child=None
     for _ in range(95):
      possible=[]
      for q in psutil.process_iter(["name"]):
       try:
        if (q.info["name"] or "").lower()=="fxfile.exe" and q.ppid()==p.pid:
         argv=q.cmdline()
         if "--conf_dir" not in argv:continue
         private=Path(argv[argv.index("--conf_dir")+1])
         if re.fullmatch(r"fxw[0-9a-fA-F]{1,4}\.tmp",private.name,re.I):
          possible.append(q)
       except (psutil.NoSuchProcess,psutil.AccessDenied):pass
      if len(possible)==1:child=possible[0];break
      time.sleep(.12)
     if child is None:
      dialogs=[]
      for h in en(p.pid,True):
       if cls(h)!="#32770" or not u.IsWindowVisible(h):continue
       try:
        labels=[x.element_info.name.encode("ascii","backslashreplace").decode()
           for x in Desktop(backend="uia").window(handle=h).descendants()
           if x.element_info.control_type=="Text"]
       except Exception:labels=[]
       dialogs.append((title(h).encode("ascii","backslashreplace").decode(),
                       labels[:6]))
      print("RESTARTED_PARENT_OPEN_DIAGNOSTIC",path.name,dialogs,
            "NATIVE_DIALOG_VISIBLE",bool(u.IsWindowVisible(op)),
            "NATIVE_DIALOG_FOREGROUND",u.GetForegroundWindow()==op,
            "PARENT_EXIT",p.poll(),flush=True)

     assert child,("restarted parent could not open named workspace",path.name)
     check_child_isolation(child)
     childmain=frame(child.pid)
     actual=[]
     for _ in range(70):
      actual=tabs(childmain)
      if sorted(len(q) for q in actual)==sorted(expected):break
      time.sleep(.12)
     assert sorted(len(q) for q in actual)==sorted(expected),(
       "reopened workspace tab layout mismatch",path.name,actual)
     assert tabs(main)==restored_parent,(
       "named workspace replaced the restarted Last Tabs session",path.name)
     assert u.PostMessageW(childmain,0x10,0,0)
     assert child.wait(timeout=14)==0
     assert_child_cleaned(owned_child_dirs[-1])
     child=None;childmain=0
    print("PARENT_NORMAL_RESTART_BOTH_NAMED_WORKSPACES_AND_LAST_TABS_PRESERVED=True",
          flush=True)
finally:
 if p:
  for q in psutil.process_iter(["name"]):
   try:
    if q.pid==p.pid or q.pid in before_fly or q.ppid()!=p.pid:
     continue
    if (q.info["name"] or "").lower()!="fxfile.exe":
     continue
    argv=q.cmdline()
    if "--conf_dir" not in argv:continue
    private=Path(argv[argv.index("--conf_dir")+1])
    if not (private.name.lower().startswith("fxw") and
      private.suffix==".tmp" and
      (private/"fxfile-workspace-owned.marker").is_file()):
     continue
    wins=[h for h in en(q.pid,True) if
      title(h).endswith(" - fxfile") and u.IsWindow(h)]
    if len(wins)==1:
     u.PostMessageW(wins[0],0x10,0,0)
     try:q.wait(timeout=12)
     except psutil.TimeoutExpired:
      q.terminate();q.wait(timeout=5)
     print("ONLY_TEST_SPAWNED_UNEXPECTED_CHILD_CLOSED",q.pid,flush=True)
   except(psutil.NoSuchProcess,psutil.AccessDenied):pass
 if child and child.is_running():
  if childmain and u.IsWindow(childmain):
   u.PostMessageW(childmain,0x10,0,0)
  try:child.wait(timeout=11)
  except psutil.TimeoutExpired:
   # Only the test-owned child (direct PID and private conf_dir) may end.
   child.terminate();child.wait(timeout=5)
  print("OWNED_WORKSPACE_CHILD_EXIT",child.returncode if hasattr(child,"returncode")
        else child.wait(timeout=1),flush=True)
  if owned_child_dirs: assert_child_cleaned(owned_child_dirs[-1])
 if p and p.poll() is None:
  if main and u.IsWindow(main):u.PostMessageW(main,0x10,0,0)
  try:p.wait(timeout=13)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=4)
 same=all(hashlib.sha256((user/n).read_bytes()).hexdigest()==before[n] for n in names)
 print("ORIGINAL_SETTINGS_SIX_HASHES_IDENTICAL",same,
       "TEST_OWNED_EXIT",p.returncode if p else None,
       "OWNED_FIXTURE",str(home),flush=True)
 assert same and p and p.returncode==0
