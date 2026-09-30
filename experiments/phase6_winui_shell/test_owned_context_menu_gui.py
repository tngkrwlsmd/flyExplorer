"""Never invoke external verbs: verify test-owned WinUI launches Shell popup.

This is an input/cancel smoke only. It must never click any third-party
command, open a preexisting window or modify unowned files.
"""
import ctypes as c
from ctypes import wintypes as w
import hashlib,os,subprocess,sys,tempfile,time
from pathlib import Path
import psutil
from pywinauto import Desktop,keyboard

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
user=c.windll.user32
user.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
def eventually(fn,label,seconds=13):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  try:
   if fn():return
  except Exception:pass
  time.sleep(.2)
 raise AssertionError(label)
def main(config="Debug"):
 a=Path(__file__).resolve().parent
 exe=a/"x64"/config/"FlyExplorerWinUIShell"/"FlyExplorerWinUIShell.exe"
 helper=exe.parent/"FlyShellIsolationHelper.exe"
 assert exe.is_file() and helper.is_file()
 root=a.parents[1]/"logs"/"m24"
 root.mkdir(parents=True,exist_ok=True)
 owned=Path(tempfile.mkdtemp(prefix="context-gui-owned-",dir=root))
 folder=owned/"source";folder.mkdir()
 file=folder/"context-test-owned.txt"
 file.write_text("test owned only",encoding="utf-8")
 mfc=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 old={n:hashlib.sha256((mfc/n).read_bytes()).digest()
      for n in LEGACY if (mfc/n).is_file()}
 env=os.environ.copy()
 for k in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
  target=owned/k.lower();target.mkdir();env[k]=str(target)
 for key in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST"):
  env.pop(key,None)
 winui=subprocess.Popen([str(exe),str(folder)],cwd=exe.parent,env=env)
 hwnd=None;child=None
 verified=False
 try:
  def get_win():
   nonlocal hwnd
   if winui.poll() is not None:return None
   assert Path(psutil.Process(winui.pid).exe()).resolve()==exe.resolve()
   matches=[q for q in Desktop(backend="uia").windows(process=winui.pid)
            if "flyExplorer - WinUI 3" in q.window_text()]
   if len(matches)!=1:return None
   hwnd=matches[0].handle
   return Desktop(backend="uia").window(handle=hwnd)
  eventually(lambda:get_win() is not None,"Owned preview HWND unavailable")
  win=get_win()
  def row():
   pane=win.child_window(auto_id="LeftFiles")
   if not pane.exists(timeout=.2):return None
   return next((x for x in pane.descendants()
     if x.element_info.control_type=="ListItem" and
        "context-test-owned.txt" in x.window_text()),None)
  eventually(lambda:row() is not None,"Owned file row unavailable")
  eventually(lambda:str(folder).lower() in
             win.child_window(auto_id="AddressBox").get_value().lower(),
             "Owned context fixture route did not commit",12)
  def select_owned_row():
   current=row()
   if current is None:return False
   win.set_focus()
   if user.GetForegroundWindow()!=hwnd:return False
   current.select()
   refreshed=row()
   return refreshed is not None and refreshed.is_selected()
  eventually(select_owned_row,"Owned context row selection did not stabilize",8)
  # The ListViewItem may report a full content-width rectangle much
  # wider than the actual clipped viewport. Click only the verified
  # intersection of this owned row and its owned ListView, never the
  # window caption or another application's desktop coordinates.
  from pywinauto import mouse
  item=row().rectangle()
  area=win.child_window(auto_id="LeftFiles").rectangle()
  left=max(item.left,area.left)
  right=min(item.right,area.right)
  top=max(item.top,area.top)
  bottom=min(item.bottom,area.bottom)
  print("OWNED_CONTEXT_ACTUAL_ROW_AND_VIEW",
        str(item),str(area),flush=True)
  assert right-left>30 and bottom-top>5,(
      "Owned file row not visible inside owned ListView viewport")
  click=(left+min(50,(right-left)//2),(top+bottom)//2)
  assert area.left<click[0]<area.right and area.top<click[1]<area.bottom
  def menu():
   # WinUI may host ContextFlyout in a top-level XAML popup HWND. Search
   # only exact owned-process windows; never inspect other applications.
   hits=[]
   for target in Desktop(backend="uia").windows(process=winui.pid):
    try:
     hits.extend(x for x in target.descendants()
        if x.element_info.name=="Windows Shell isolated context menu")
    except Exception:pass
   return hits[0] if len(hits)==1 else None
  def foreground_owned():
   f=user.GetForegroundWindow()
   if not f:return False
   pid=w.DWORD()
   user.GetWindowThreadProcessId(f,c.byref(pid))
   return pid.value==winui.pid
  def wait_app_menu(seconds):
   end=time.monotonic()+seconds
   while time.monotonic()<end:
    hit=menu()
    if hit is not None:return hit
    time.sleep(.15)
   return None
  # Native watcher/UIA timing can replace the selected peer while the
  # ContextFlyout is opening. Retry the exact clipped pointer gesture at
  # most twice. Between attempts ESC is sent only when the exact owned
  # WinUI process owns foreground; never dismiss or click a foreign menu.
  for attempt in range(2):
   if menu() is not None:break
   eventually(select_owned_row,"Owned context row lost before right click",5)
   item=row().rectangle()
   area=win.child_window(auto_id="LeftFiles").rectangle()
   left=max(item.left,area.left);right=min(item.right,area.right)
   top=max(item.top,area.top);bottom=min(item.bottom,area.bottom)
   assert right-left>30 and bottom-top>5
   click=(left+min(50,(right-left)//2),(top+bottom)//2)
   assert area.left<click[0]<area.right and area.top<click[1]<area.bottom
   mouse.click(button="right",coords=click)
   if wait_app_menu(2.3) is not None:break
   if foreground_owned():
    keyboard.send_keys("{ESC}")
    time.sleep(.25)
  if menu() is None:
   eventually(select_owned_row,"Owned context row lost before keyboard fallback",5)
   current=row()
   assert current is not None
   current.set_focus()
   assert foreground_owned()
   keyboard.send_keys("+{F10}")
   print("OWNED_CONTEXT_KEYBOARD_FALLBACK_USED",True,flush=True)
  try:
   eventually(lambda:menu() is not None,
              "Owned Shell menu launch item absent",6)
  except AssertionError:
   # Diagnostic only, no more synthetic coordinate drags/clicks.
   discovered=[]
   for target in Desktop(backend="uia").windows(process=winui.pid):
    for element in target.descendants():
     if element.element_info.control_type in ("MenuItem","Menu"):
      discovered.append(element.element_info.name[:78])
   print("OWNED_PROCESS_MENU_UIA_DIAGNOSTIC",
         [x.encode("unicode_escape").decode("ascii") for x in discovered[:18]],
         flush=True)
   raise
  menu().click_input()
  def spawned():
   nonlocal child
   candidates=[]
   for q in psutil.Process(winui.pid).children(recursive=False):
    try:
     if Path(q.exe()).resolve()==helper.resolve() and \
        "--context-menu" in q.cmdline():
      candidates.append(q)
    except psutil.Error:pass
   if len(candidates)!=1:return False
   child=candidates[0]
   return True
  eventually(spawned,"WinUI did not launch exact owned isolated context helper",8)
  def owns_foreground():
   f=user.GetForegroundWindow()
   if not f:return False
   pid=w.DWORD()
   user.GetWindowThreadProcessId(f,c.byref(pid))
   return pid.value==child.pid
  eventually(owns_foreground,"Native Shell popup did not own foreground",6)
  print("ACTUAL_OWNED_SHELL_CONTEXT_POPUP_FOREGROUND",True,flush=True)
  # Escape only while exact test-launched helper owns the foreground.
  user.keybd_event(0x1b,0,0,0)
  user.keybd_event(0x1b,0,2,0)
  eventually(lambda:not child.is_running() or child.status()=="zombie",
             "Test-owned Shell popup did not cancel",6)
  assert file.read_text(encoding="utf-8")=="test owned only"
  verified=True
 finally:
  if child is not None and child.is_running():
   try:
    if Path(child.exe()).resolve()==helper.resolve() and \
       "--context-menu" in child.cmdline():
     child.terminate();child.wait(timeout=6)
   except psutil.Error:pass
  if winui.poll() is None:
   if hwnd is not None:
    user.PostMessageW(hwnd,0x10,0,0)
    try:winui.wait(timeout=11)
    except subprocess.TimeoutExpired:
     winui.terminate();winui.wait(timeout=7)
   else:
    winui.terminate();winui.wait(timeout=7)
  safe=all((mfc/n).is_file() and
    hashlib.sha256((mfc/n).read_bytes()).digest()==h
    for n,h in old.items())
  print("SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL",safe,flush=True)
  print("ONLY_TEST_OWNED_SOURCE_UNMODIFIED",
        file.is_file() and file.read_text(encoding="utf-8")=="test owned only",
        flush=True)
  if verified and safe:
   import shutil
   shutil.rmtree(owned)
  else:
   print("OWNED_CONTEXT_DIAGNOSTIC_FIXTURE_RETAINED",owned,flush=True)
 return 0 if verified and safe else 1

if __name__=="__main__":
 sys.exit(main(sys.argv[1] if len(sys.argv)>1 else "Debug"))
