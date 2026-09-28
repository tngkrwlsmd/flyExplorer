"""UXH-06/07 feasibility: non-destructive owned search and last-tab GUI proof.

Only synthetic paths in an isolated copied configuration. No product
source changes, system-wide settings, or user's original search directories.
"""
from pathlib import Path
import ctypes as c, hashlib, os, re, shutil, subprocess, sys, tempfile, time
from ctypes import wintypes as w
from pywinauto import keyboard, mouse, Desktop
from comtypes import POINTER
import comtypes.client
comtypes.client.GetModule("oleacc.dll")
from comtypes.gen.Accessibility import IAccessible

R=Path(__file__).resolve().parents[1]
source=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
before={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names}
root=Path(tempfile.mkdtemp(prefix="uxh06-07-owned-",dir=R/"logs"))
conf=root/"conf";conf.mkdir()
for n in names:shutil.copy2(source/n,conf/n)
appdata=root/"appdata";appdata.mkdir()
fixture=root/"fixture";fixture.mkdir()
dirs=[fixture/n for n in ("UXH07 pane one","UXH07 pane two","UXH07 extra tab")]
for d in dirs:d.mkdir()
longpath=fixture
for n in ("UXH06 long search location "+("first_"*5),
          "owned subfolder "+("second_"*5)):
 longpath=longpath/n;longpath.mkdir()
assert len(str(longpath))>112 and len(str(longpath))<245
def cfg_edit(path,updates):
 raw=path.read_bytes()
 enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
 t=raw.decode(enc)
 for key,value in updates.items():
  t,count=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",
       lambda m:m.group(1)+str(value),t)
  if count==0:
   assert t.lstrip().startswith("[config]"),"only in private copied config"
   t=t.replace("[config]","[config]\n"+key+" = "+str(value),1)
  else:assert count==1,key
 path.write_bytes(t.encode(enc))
common={"config.global_hotkey.enable":"0",
 "config.global_hotkey.show_tray":"0",
 "config.global_hotkey.windows_startup":"0",
 "config.register_shell_context_menu":"0"}
if "--restore" in sys.argv:
 common.update({"config.view1.file_list.init_folder":"3",
                "config.view2.file_list.init_folder":"3",
                "config.tab.show_one_tab":"1"})
cfg_edit(conf/"fxfile.conf",common)
# Keep no copied private tabs/search dirs in the launched owned profile.
# Only write synthetic exact paths; no user session values are exposed.
if "--restore" in sys.argv:
 maintext="\n".join(("[main]","main.view.row_count = 1",
   "main.view.column_count = 2","main.view.ratio1 = 0.35",
   "main.view1.current_tab = 0","main.view1.tab1.path = "+str(dirs[0]),
   "main.view2.current_tab = 0","main.view2.tab1.path = "+str(dirs[1]),""))
 (conf/"fxfile-main.conf").write_text(maintext,encoding="utf-16")
else:
 (conf/"fxfile-main.conf").write_text("[main]\nmain.view.row_count = 1\nmain.view.column_count = 1\n",encoding="utf-16")
 (conf/"fxfile-search_dir.conf").write_text(
     "[UXH06 owned saved group]\nsearch_dir.dir_count = 1\n"
     "search_dir.dir1 = "+str(longpath)+"\n",encoding="utf-16")
u=c.windll.user32;oa=c.windll.oleacc
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
class RECT(c.Structure):
 _fields_=[(key,c.c_long) for key in ("left","top","right","bottom")]
class POINT(c.Structure):
 _fields_=[("x",c.c_long),("y",c.c_long)]
for method,args in (
 ("EnumWindows",(CALLBACK,w.LPARAM)),("EnumChildWindows",(w.HWND,CALLBACK,w.LPARAM)),
 ("GetWindowThreadProcessId",(w.HWND,c.POINTER(w.DWORD))),
 ("GetWindowRect",(w.HWND,c.POINTER(RECT))),
 ("GetClassNameW",(w.HWND,w.LPWSTR,c.c_int)),
 ("GetWindowTextW",(w.HWND,w.LPWSTR,c.c_int)),
 ("GetDlgItem",(w.HWND,c.c_int)),
 ("PostMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM)),
 ("SetWindowPos",(w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT)),
 ("SendMessageW",(w.HWND,w.UINT,w.WPARAM,w.LPARAM))):
 getattr(u,method).argtypes=args
u.SendMessageW.restype=c.c_ssize_t
u.GetDlgItem.restype=w.HWND
u.IsWindowUnicode.argtypes=(w.HWND,)
oa.AccessibleObjectFromWindow.argtypes=(w.HWND,w.DWORD,c.POINTER(c.c_byte*16),c.POINTER(c.c_void_p))
oa.AccessibleObjectFromWindow.restype=w.LONG
def cl(h):
 b=c.create_unicode_buffer(96);u.GetClassNameW(h,b,len(b));return b.value
def title(h):
 b=c.create_unicode_buffer(400);u.GetWindowTextW(h,b,len(b));return b.value
def rect(h):
 x=RECT();assert u.GetWindowRect(h,c.byref(x));return(x.left,x.top,x.right,x.bottom)
def en(h,all=False):
 items=[]
 @CALLBACK
 def cb(x,_):
  if all:
   p=w.DWORD();u.GetWindowThreadProcessId(x,c.byref(p))
   if p.value!=h:return True
  items.append(int(x));return True
 if all:u.EnumWindows(cb,0)
 else:u.EnumChildWindows(h,cb,0)
 return items
def wait_main(pid):
 for _ in range(100):
  wins=[h for h in en(pid,True) if title(h).endswith(" - fxfile")]
  if len(wins)==1:return wins[0]
  time.sleep(.12)
 raise AssertionError("owned main window absent")
def own_launch(args=()):
 p=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),
    "--conf_dir",str(conf),*map(str,args)],cwd=root,
    env={**os.environ,"APPDATA":str(appdata)},
    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 m=wait_main(p.pid)
 u.ShowWindow(m,9)
 u.SetWindowPos(m,0,70,70,1030,675,0x0004)
 time.sleep(.55)
 return p,m
def close(p,m):
 if p and p.poll() is None:
  if m and u.IsWindow(m):u.PostMessageW(m,0x10,0,0)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:
   p.terminate();p.wait(timeout=5)
 assert p and p.returncode==0,("owned exit",p.returncode if p else None)
def get_text(h):
 b=c.create_unicode_buffer(500)
 u.SendMessageW(h,0xD,499,c.addressof(b))
 return b.value
def rid(name):
 text=(R/"src/fxfile/resource.h").read_text(encoding="utf-8-sig",errors="replace")
 return int(re.search(r"(?m)^#define\s+"+re.escape(name)+r"\s+(\d+)",text).group(1))
def open_search(process,main):
 assert u.PostMessageW(main,0x111,34014,0)
 for _ in range(90):
  ds=[h for h in en(process.pid,True) if h!=main and cl(h)=="#32770"]
  matched=[h for h in ds if u.GetDlgItem(h,rid("IDC_SEARCH_LOC")) and
           u.GetDlgItem(h,rid("IDC_SEARCH_RECENT"))]
  if len(matched)==1:return matched[0]
  time.sleep(.14)
 raise AssertionError("owned search dialog absent")
def click_control(h):
 box=rect(h)
 mouse.click(coords=((box[0]+box[2])//2,(box[1]+box[3])//2))
def tab_snapshot(main):
 from comtypes import GUID
 tabs=[h for h in en(main) if cl(h)=="TabCtrl" and u.IsWindowVisible(h)]
 rows=[]
 for h in tabs:
  el=Desktop(backend="uia").window(handle=h)
  items=[x.element_info.name for x in el.descendants()
         if x.element_info.control_type=="TabItem"]
  rows.append((h,rect(h),items))
 return rows
p=m=p2=m2=None
try:
 if "--search" in sys.argv:
  p,m=own_launch([fixture])
  assert u.GetDpiForWindow(m)==96,"actual 96DPI only evidence"
  assert u.PostMessageW(m,0x111,34014,0),"search dialog command"
  dialog=0
  for _ in range(80):
   ds=[h for h in en(p.pid,True) if h!=m and cl(h)=="#32770"]
   candidates=[h for h in ds if
      u.GetDlgItem(h,rid("IDC_SEARCH_LOC")) and
      u.GetDlgItem(h,rid("IDC_SEARCH_NAME"))]
   if len(candidates)==1:dialog=candidates[0];break
   time.sleep(.12)
  if not dialog:
   print("OWNED_DIALOG_CLASS_DIAG",[(cl(h),
      sorted(set(cl(x) for x in en(h)))[:12])
      for h in en(p.pid,True) if cl(h)=="#32770"],flush=True)
  assert dialog,"owned search dialog with location/name controls missing"
  combo=u.GetDlgItem(dialog,rid("IDC_SEARCH_LOC"))
  print("REAL_SEARCH_LOCATION_CONTROL_CLASS",
    cl(combo) if combo else "MISSING",
    "DIALOG_CHILD_CLASSES",sorted(set(cl(h) for h in en(dialog))),flush=True)
  assert combo and cl(combo).lower().startswith("comboboxex"),cl(combo)
  children=en(combo)
  inner=next((h for h in children if cl(h)=="ComboBox"),0)
  edit=next((h for h in children if cl(h)=="Edit"),0)
  if not edit and inner:
   edit=next((h for h in en(inner) if cl(h)=="Edit"),0)
  assert inner and edit,[(cl(h),h) for h in children]
  count=int(u.SendMessageW(inner,0x146,0,0))
  assert count>=9,("user-group location not populated in native combo",count)
  print("UXH06_PRIVATE_USER_GROUP_PRESENT_BY_NATIVE_ITEM_COUNT=True",
        "TOTAL_SCOPE_CHOICES",count,
        "LABEL_READ=NOT_TESTED_OWNER_DRAW",flush=True)
  r=rect(edit)
  mouse.click(coords=((r[0]+r[2])//2,(r[1]+r[3])//2))
  from pywinauto import keyboard
  keyboard.send_keys("^a",pause=.03)
  keyboard.send_keys(str(longpath),with_spaces=True,pause=.002,vk_packet=True)
  time.sleep(.26)
  actual=get_text(edit)
  assert actual==str(longpath),("full edit path is not preserved",
       len(actual),len(str(longpath)))
  width=r[2]-r[0]
  # Each of the >112 characters needs more than 750px at standard
  # fonts: native auto-horizontal-scroll style must retain all text.
  style=u.GetWindowLongW(inner,-16)
  print("UXH06_FULL_NATIVE_EDIT_LOCATION_RETAINED=True",
      "PATH_LENGTH",len(actual),"EDIT_WIDTH_PX",width,
      "CBS_AUTOHSCROLL_FLAG",bool(style&0x40),flush=True)
  assert len(actual)>112 and width<640
  keyboard.send_keys("{HOME}")
  time.sleep(.12)
  home=get_text(edit)
  keyboard.send_keys("{END}")
  time.sleep(.12)
  assert home==actual==get_text(edit)
  print("UXH06_HOME_END_PRESERVE_EXACT_LONG_SCOPE=True",flush=True)
  if "--feature" in sys.argv:
   preview=u.GetDlgItem(dialog,rid("IDC_SEARCH_SCOPE_PREVIEW"))
   full=u.GetDlgItem(dialog,rid("IDC_SEARCH_SCOPE_FULL"))
   recent=u.GetDlgItem(dialog,rid("IDC_SEARCH_RECENT"))
   remember=u.GetDlgItem(dialog,rid("IDC_SEARCH_REMEMBER"))
   assert all((preview,full,recent,remember))
   assert int(u.SendMessageW(recent,0x146,0,0))==0
   click_control(preview)
   time.sleep(.18)
   assert get_text(full)==str(longpath),("full-scope preview failed",
                                          len(get_text(full)))
   assert u.GetWindowLongW(full,-16)&0x800
   print("UXH06_REAL_READONLY_FULL_SCOPE_DISPLAY_PASS=True",
         "LENGTH",len(get_text(full)),flush=True)
   click_control(remember)
   assert u.SendMessageW(remember,0xF0,0,0)==1
   print("UXH06_REAL_OPT_IN_REMEMBER_SELECTED=True",flush=True)
   (longpath/"uxh06-owned-find.txt").write_text("owned",encoding="utf-8")
   click_control(u.GetDlgItem(dialog,rid("IDC_SEARCH_NAME")))
   keyboard.send_keys("^a",pause=.03)
   keyboard.send_keys("uxh06-owned-find.txt",pause=.025)
   click_control(u.GetDlgItem(dialog,rid("IDC_SEARCH_START")))
   recent_count=0
   for _ in range(75):
    recent_count=int(u.SendMessageW(recent,0x146,0,0))
    if recent_count:break
    time.sleep(.15)
   assert recent_count==1,("valid opted-in search not remembered",
                          recent_count)
   print("UXH06_REAL_VALID_SEARCH_SAVED_ONE_RECENT=True",flush=True)
   time.sleep(.22)
  # Actual current-folder feature: it is a separate command which
  # must continue to set the search location from the active pane.
  current=u.GetDlgItem(dialog,rid("IDC_SEARCH_CUR_LOC"))
  assert current and u.IsWindowVisible(current)
  print("UXH06_EXISTING_CURRENT_FOLDER_COMMAND_VISIBLE=True",flush=True)
  assert u.PostMessageW(dialog,0x10,0,0)
  time.sleep(.24)
  close(p,m);p=None;m=None
  if "--feature" in sys.argv:
   state=(conf/"fxfile-dlg_state.conf").read_text(
      encoding="utf-16",errors="replace")
   assert "RecentLocations" in state and str(longpath) in state,(
       "valid opted-in search was not serialized on normal exit")
   p2,m2=own_launch([fixture])
   second=open_search(p2,m2)
   cb=u.GetDlgItem(second,rid("IDC_SEARCH_RECENT"))
   assert u.SendMessageW(cb,0x146,0,0)==1
   print("UXH06_RESTART_RECENT_SCOPE_PERSISTENCE_PASS=True",flush=True)
   # Click the actual native drop-list item (never programmatically
   # fake WM_COMMAND or send accidental Enter to a default search).
   click_control(cb)
   time.sleep(.2)
   pop=[h for h in en(p2.pid,True)
        if cl(h)=="ComboLBox" and u.IsWindowVisible(h)]
   assert pop,("real recent dropdown not expanded",
               [(cl(h),rect(h)) for h in en(p2.pid,True)[:10]])
   box=rect(pop[-1])
   mouse.click(coords=(box[0]+min(60,(box[2]-box[0])//2),
                       box[1]+min(11,(box[3]-box[1])//2)))
   time.sleep(.32)
   scope=u.GetDlgItem(second,rid("IDC_SEARCH_LOC"))
   edit2=next((h for h in en(scope) if cl(h)=="Edit"),0)
   if not edit2:
    inner2=next((h for h in en(scope) if cl(h)=="ComboBox"),0)
    edit2=next((h for h in en(inner2) if cl(h)=="Edit"),0)
   assert edit2 and get_text(edit2)==str(longpath),(
       "physical recent selection failed to restore full path",
       get_text(edit2) if edit2 else None)
   print("UXH06_REAL_RECENT_PICK_RESTORED_FULL_SCOPE_PASS=True",flush=True)
   click_control(u.GetDlgItem(second,rid("IDC_SEARCH_RECENT_CLEAR")))
   assert u.SendMessageW(cb,0x146,0,0)==0
   print("UXH06_REAL_CLEAR_RECENT_LIST_PASS=True",flush=True)
   assert u.PostMessageW(second,0x10,0,0)
   time.sleep(.3)
   close(p2,m2);p2=None;m2=None
   after=(conf/"fxfile-dlg_state.conf").read_text(
      encoding="utf-16",errors="replace")
   assert str(longpath) not in after,"cleared path remains on disk"
   p,m=own_launch([fixture])
   third=open_search(p,m)
   cb3=u.GetDlgItem(third,rid("IDC_SEARCH_RECENT"))
   check=u.GetDlgItem(third,rid("IDC_SEARCH_REMEMBER"))
   assert u.SendMessageW(cb3,0x146,0,0)==0
   assert u.SendMessageW(check,0xF0,0,0)==0,(
        "remember opt-in must default off on each open")
   print("UXH06_RESTART_AFTER_CLEAR_EMPTY_AND_OPT_OUT_DEFAULT_PASS=True",
         flush=True)
   assert u.PostMessageW(third,0x10,0,0)
   time.sleep(.23)
   close(p,m);p=None;m=None
 else:
  p,m=own_launch()
  assert u.GetDpiForWindow(m)==96
  first=tab_snapshot(m)
  print("UXH07_INITIAL_OWNED_SPLIT_TABS",
     [(len(row[2]),[x.startswith("UXH07") for x in row[2]]) for row in first],
     flush=True)
  assert len(first)==2,("native 1x2 views not restored",first)
  assert all(len(row[2])==1 for row in first),first
  names_now=[n for h,b,ns in first for n in ns]
  assert all(d.name in names_now for d in dirs[:2]),names_now
  print("UXH07_EXISTING_TWO_PANES_DISTINCT_SAVED_TAB_PATHS_RESTORED=True",flush=True)
  # Real Ctrl+T creates an additional tab in the currently active view.
  mouse.click(coords=(first[0][1][0]+35,(first[0][1][1]+first[0][1][3])//2))
  keyboard.send_keys("^t",pause=.055)
  time.sleep(.48)
  second=tab_snapshot(m)
  assert len(second)==2
  assert sum(len(row[2]) for row in second)==3,second
  print("UXH07_REAL_CTRL_T_CREATES_SECOND_TAB_IN_OWNED_PANE=True",flush=True)
  close(p,m);p=None;m=None
  saved=(conf/"fxfile-main.conf").read_text(encoding="utf-16")
  def value(key):
   match=re.search(r"(?m)^\s*"+re.escape(key)+r"\s*=\s*([^\r\n]*)",saved)
   return match.group(1).strip() if match else None
  assert value("main.view.row_count")=="1"
  assert value("main.view.column_count")=="2"
  assert value("main.view1.tab1.path") is not None
  assert value("main.view2.tab1.path") is not None
  assert value("main.view1.tab2.path") is not None,(
     "added tab path not serialized",)
  print("UXH07_NATIVE_SPLIT_AND_BOTH_PANE_TABS_SERIALIZED=True",
     "TABS_PER_VIEW",(2,1),flush=True)
  p2,m2=own_launch()
  third=tab_snapshot(m2)
  assert len(third)==2 and sorted(len(row[2]) for row in third)==[1,2],third
  print("UXH07_SECOND_OWNED_PROCESS_RESTORES_1X2_TABS=True",flush=True)
  close(p2,m2);p2=None;m2=None
 print("OWNED_EVIDENCE_FOLDER",root,flush=True)
finally:
 for pr,mw in ((p,m),(p2,m2)):
  if pr is not None:close(pr,mw)
 after={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in names}
 same=all(after[n]==before[n] for n in names)
 print("ORIGINAL_SETTINGS_SIX_HASHES_IDENTICAL",same,flush=True)
 assert same
