"""M1.9 bidirectional legacy UXH-07 WinUI <-> MFC real GUI compatibility.
Only a synthetic, private config and processes started by this test.
"""
from pathlib import Path
import ctypes as c
from ctypes import wintypes as W
import hashlib,os,psutil,re,shutil,subprocess,time
from pywinauto import Desktop,keyboard
ROOT=Path(__file__).resolve().parents[2]
MFC=ROOT/"bin"/"x64"/"fxfile.exe"
assert MFC.is_file(),MFC
u=c.windll.user32
CALL=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CALL,W.LPARAM]
u.EnumChildWindows.argtypes=[W.HWND,CALL,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.GetForegroundWindow.restype=W.HWND
u.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
u.GetClassNameW.argtypes=[W.HWND,W.LPWSTR,c.c_int]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,c.c_int]
def enumerate_handles(pid,children_of=None):
 out=[]
 @CALL
 def collect(h,_):
  if children_of is None:
   actual=W.DWORD()
   u.GetWindowThreadProcessId(h,c.byref(actual))
   if actual.value!=pid:return True
  out.append(int(h));return True
 if children_of is None:u.EnumWindows(collect,0)
 else:u.EnumChildWindows(children_of,collect,0)
 return out
def classname(h):
 buf=c.create_unicode_buffer(120);u.GetClassNameW(h,buf,len(buf));return buf.value
def title(h):
 buf=c.create_unicode_buffer(500);u.GetWindowTextW(h,buf,len(buf));return buf.value
def spin(predicate,message,limit=11):
 deadline=time.monotonic()+limit
 while time.monotonic()<deadline:
  try:
   value=predicate()
   if value:return value
  except Exception:pass
  time.sleep(.13)
 raise AssertionError(message)
def main_window(pid):
 frames=[h for h in enumerate_handles(pid) if title(h).endswith(" - fxfile")
         and u.IsWindowVisible(h)]
 return frames[0] if len(frames)==1 else None
def tabs(hwnd):
 return [
  [x.element_info.name for x in
   Desktop(backend="uia").window(handle=h).descendants()
   if x.element_info.control_type=="TabItem"]
  for h in enumerate_handles(0,children_of=hwnd)
  if classname(h)=="TabCtrl" and u.IsWindowVisible(h)]
def dialog(pid,main):
 for h in enumerate_handles(pid):
  if h==main or classname(h)!="#32770" or not u.IsWindowVisible(h):
   continue
  target=Desktop(backend="uia").window(handle=h)
  try:
   edits=[x for x in target.descendants()
    if x.is_visible() and x.element_info.control_type=="Edit" and
       (x.element_info.name.strip().endswith(":") or
        "file name" in x.element_info.name.lower())]
   if len(edits)==1:return target,edits[0]
  except Exception:pass
 return None
def focus(pid,window):
 for _ in range(4):
  window.set_focus()
  time.sleep(.12)
  foreground=u.GetForegroundWindow()
  owner=W.DWORD()
  if foreground:u.GetWindowThreadProcessId(foreground,c.byref(owner))
  if owner.value==pid:return
 raise AssertionError("Refusing native physical Enter for unowned foreground")
def run(saved,left,right,inner,owned,env):
 assert os.environ.get("FLY_M19_CROSS_MFC")=="YES"
 names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf",
        "fxfile-folder_layout.conf")
 real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 hashbefore={n:hashlib.sha256((real/n).read_bytes()).digest() for n in names}
 conf=owned/"m19-mfc-private-conf";conf.mkdir()
 appdata=owned/"m19-mfc-private-appdata";appdata.mkdir()
 for n in names:shutil.copy2(real/n,conf/n)
 cfg=conf/"fxfile.conf"
 data=cfg.read_bytes()
 enc="utf-16" if data[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
 options=data.decode(enc)
 for key,val in (
   ("config.global_hotkey.enable","0"),
   ("config.global_hotkey.show_tray","0"),
   ("config.global_hotkey.windows_startup","0"),
   ("config.register_shell_context_menu","0"),
   ("config.view1.file_list.init_folder","3"),
   ("config.view2.file_list.init_folder","3"),
   ("config.single_process","0")):
  pattern=r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*"
  options,count=re.subn(pattern,lambda m:m.group(1)+val,options)
  if not count:
   assert options.lstrip().startswith("[config]")
   options=options.replace("[config]","[config]\n"+key+" = "+val,1)
 cfg.write_bytes(options.encode(enc))
 (conf/"fxfile-main.conf").write_text("\n".join((
     "[main]","main.tip_of_today.show = 0",
     "main.view.row_count = 1","main.view.column_count = 2",
     "main.view.ratio1 = 0.50",
     "main.view1.current_tab = 0",
     "main.view1.tab1.path = "+str(left),
     "main.view2.current_tab = 0",
     "main.view2.tab1.path = "+str(right),"")),encoding="utf-16")
 runtime={**env,"APPDATA":str(appdata)}
 p=None;child=None
 native_export=owned/"m19-real-mfc-export.fxworkspace"
 def private_children():
  if not p:return []
  try:
   return [q for q in psutil.Process(p.pid).children()
           if q.is_running() and q.exe().lower()==str(MFC).lower() and
           "--conf_dir" in q.cmdline()]
  except (psutil.AccessDenied,psutil.NoSuchProcess):return []
 def close_owned(proc,window):
  if not proc:return
  try:
   if window:u.PostMessageW(window,0x10,0,0)
   proc.wait(timeout=11)
  except (psutil.TimeoutExpired,subprocess.TimeoutExpired):
   target=psutil.Process(proc.pid)
   if (proc.pid==p.pid or target.ppid()==p.pid) and (
          target.exe().lower()==str(MFC).lower()):
    target.terminate();target.wait(timeout=6)
  except psutil.NoSuchProcess:pass
 try:
  p=subprocess.Popen([str(MFC),"--conf_dir",str(conf)],
       cwd=owned,env=runtime,stdin=subprocess.DEVNULL,
       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  owner=spin(lambda:main_window(p.pid),"test-owned native MFC parent absent",14)
  u.ShowWindow(owner,9)
  spin(lambda:len(tabs(owner))==2 and
       all(len(pane)==1 for pane in tabs(owner)),
       "test-owned native MFC baseline was not 1+1 panes",12)
  # WinUI-exported UTF-16 [main] + [workspace] must pass MFC's REAL
  # file picker, parser, exact isolated --conf_dir child creation.
  assert u.PostMessageW(owner,0x111,33053,0)
  target,field=spin(lambda:dialog(p.pid,owner),
        "legacy native Open workspace file dialog did not appear",10)
  field.set_edit_text(str(saved))
  focus(p.pid,target)
  keyboard.send_keys("{ENTER}")
  new=spin(lambda:private_children(),
           "MFC rejected WinUI-exported workspace schema",13)
  assert len(new)==1,(len(new),"expected one isolated MFC child")
  child=new[0]
  assert child.ppid()==p.pid
  args=child.cmdline()
  child_conf=Path(args[args.index("--conf_dir")+1])
  assert child_conf.name.startswith("fxw") and child_conf.suffix==".tmp"
  assert (child_conf/"fxfile-workspace-owned.marker").is_file()
  childwnd=spin(lambda:main_window(child.pid),
                "real MFC isolated WinUI-workspace child has no frame",13)
  def imported():
   names=tabs(childwnd)
   if len(names)!=2 or sorted(map(len,names))!=[1,2]:return None
   if not (any(left.name in x for x in names[0]) and
           any(inner.name in x for x in names[0]) and
           any(right.name in x for x in names[1])):return None
   return names
  actual=spin(imported,
         "MFC file loader did not restore the WinUI-exported 2+1 tabs",14)
  assert len(tabs(owner))==2 and all(len(v)==1 for v in tabs(owner)),(
       "imported WinUI workspace mutated running native MFC parent")
  print("M19_WINUI_EXPORTED_UTF16_WORKSPACE_OPENED_BY_ACTUAL_MFC_GUI",
        True,actual,flush=True)
  close_owned(child,childwnd);child=None
  spin(lambda:not child_conf.exists(),
       "legacy native owned child temp marker not reclaimed",9)
  # Reverse direction: ask REAL MFC UI to export its own workspace.
  assert u.PostMessageW(owner,0x111,33052,0)
  saveWindow,filename=spin(lambda:dialog(p.pid,owner),
        "legacy native Save workspace file dialog did not appear",11)
  filename.set_edit_text(str(native_export))
  focus(p.pid,saveWindow)
  keyboard.send_keys("{ENTER}")
  spin(native_export.is_file,"native MFC GUI did not produce workspace",12)
  encoded=native_export.read_text(encoding="utf-16")
  assert all(x in encoded for x in ("[workspace]","schema = 1",
                                    left.name,right.name))
  print("M19_ACTUAL_NATIVE_MFC_WORKSPACE_EXPORTED_FOR_WINUI_IMPORT",
        True,flush=True)
  assert all(hashlib.sha256((real/n).read_bytes()).digest()==h
             for n,h in hashbefore.items())
  print("M19_CROSS_APP_ORIGINAL_USER_SETTINGS_SIX_HASH_IDENTICAL",
        True,flush=True)
  return native_export
 finally:
  if child:
   hwnd=main_window(child.pid)
   close_owned(child,hwnd)
  if p:
   hwnd=main_window(p.pid)
   close_owned(psutil.Process(p.pid),hwnd)
