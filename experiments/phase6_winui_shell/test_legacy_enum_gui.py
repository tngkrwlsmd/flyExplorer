"""Actual OLD MFC ExplorerCtrl path, now using the shared native enum bridge.
Only this test's child is contacted; all paths/profile data are disposable.
"""
from pathlib import Path
import ctypes as c,hashlib,os,re,shutil,subprocess,tempfile,time
from ctypes import wintypes as W
from PIL import ImageGrab

ROOT=Path(__file__).resolve().parents[2]
EXE=ROOT/"bin/x64/fxfile.exe"
assert EXE.is_file(),("compile migration worktree legacy product first",EXE)
profile=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
assert all((profile/n).is_file() for n in names)
hashes={n:hashlib.sha256((profile/n).read_bytes()).digest() for n in names}
out=ROOT/"logs/phase6-winui";out.mkdir(parents=True,exist_ok=True)
home=Path(tempfile.mkdtemp(prefix="legacy-enum-owned-",dir=out))
conf=home/"conf";conf.mkdir()
for n in names:shutil.copy2(profile/n,conf/n)
raw=(conf/"fxfile.conf").read_bytes()
enc="utf-16" if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
settings=raw.decode(enc)
for name in ("config.global_hotkey.enable","config.global_hotkey.show_tray",
             "config.global_hotkey.windows_startup",
             "config.register_shell_context_menu","config.single_process"):
 exp=r"(?m)^(\s*"+re.escape(name)+r"\s*=\s*)[^\r\n]*"
 settings,count=re.subn(exp,lambda m:m.group(1)+"0",settings)
 assert count==1,("cannot safely isolate prior product setting",name,count)
(conf/"fxfile.conf").write_bytes(settings.encode(enc))
child=home/"Owned Parent"/"Owned Child";child.mkdir(parents=True)
(child/"owned-sentinel.txt").write_text("owned only\n",encoding="utf-8")
(child.parent/"parent-sentinel.txt").write_text("owned only\n",encoding="utf-8")
appdata=home/"appdata";appdata.mkdir()
localdata=home/"localdata";localdata.mkdir()
tmp=home/"temp";tmp.mkdir()
env={**os.environ,"APPDATA":str(appdata),"LOCALAPPDATA":str(localdata),
     "TMP":str(tmp),"TEMP":str(tmp)}
u=c.windll.user32
CB=c.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
u.EnumWindows.argtypes=[CB,W.LPARAM]
u.GetWindowThreadProcessId.argtypes=[W.HWND,c.POINTER(W.DWORD)]
u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,c.c_int]
u.SendMessageTimeoutW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM,W.UINT,W.UINT,c.POINTER(c.c_size_t)]
u.SendMessageTimeoutW.restype=W.LPARAM
def text(hwnd):
 b=c.create_unicode_buffer(1000)
 u.GetWindowTextW(hwnd,b,len(b))
 return b.value
def main_of(pid):
 candidates=[]
 @CB
 def each(hwnd,_):
  identity=W.DWORD()
  u.GetWindowThreadProcessId(hwnd,c.byref(identity))
  if identity.value==pid and u.IsWindowVisible(hwnd) and text(hwnd).endswith(" - fxfile"):
   candidates.append(int(hwnd))
  return 1
 u.EnumWindows(each,0)
 return candidates[0] if len(candidates)==1 else 0
def until(fn,label,seconds=8):
 stop=time.monotonic()+seconds
 while time.monotonic()<stop:
  val=fn()
  if val:return val
  time.sleep(.13)
 raise AssertionError(label)
owned=None;hwnd=0;forced=False
try:
 owned=subprocess.Popen([str(EXE),"--conf_dir",str(conf),str(child)],
    cwd=home,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL)
 hwnd=until(lambda:main_of(owned.pid),"real native owned MainFrame absent")
 until(lambda:text(hwnd).lower().endswith("owned child - fxfile"),
       "native ExplorerCtrl could not open test-owned Shell directory")
 print("LEGACY_REAL_GUI_INITIAL_SHELL_CHILD",True,flush=True)
 # Real old MainFrame -> CommandContext -> ExplorerCtrl -> same shared
 # ShellEnumerator->openEnumeration path, no WinUI fake routing.
 for command,expected in ((32004,"owned parent - fxfile"),
                          (32006,"owned child - fxfile"),
                          (32007,"owned parent - fxfile")):
  if owned.poll() is not None:raise AssertionError("owned native app exited early")
  ident=W.DWORD()
  u.GetWindowThreadProcessId(hwnd,c.byref(ident))
  assert ident.value==owned.pid, "refuse command to non-owned HWND"
  result=c.c_size_t()
  succeeded=u.SendMessageTimeoutW(hwnd,0x111,command,0,0x0002,6000,c.byref(result))
  assert succeeded,("owned native command timed out",command)
  until(lambda:text(hwnd).lower().endswith(expected),
        "actual legacy ExplorerCtrl command did not navigate")
  print("LEGACY_REAL_GUI_SHARED_ENUM_COMMAND",command,expected,flush=True)
 assert not u.IsHungAppWindow(hwnd)
 print("LEGACY_REAL_GUI_NOT_HUNG",True,flush=True)
finally:
 if owned and owned.poll() is None:
  identity=W.DWORD()
  if hwnd and u.IsWindow(hwnd):
   u.GetWindowThreadProcessId(hwnd,c.byref(identity))
  if identity.value==owned.pid:
   assert u.PostMessageW(hwnd,0x10,0,0)
  try:owned.wait(timeout=13)
  except subprocess.TimeoutExpired:
   forced=True
   owned.terminate()
   owned.wait(timeout=5)
 same=all(hashlib.sha256((profile/n).read_bytes()).digest()==hashes[n] for n in names)
 print("LEGACY_OWNED_NATIVE_EXIT",owned.returncode if owned else None,
       "FORCED",forced,"ORIGINAL_SIX_SHA256_UNCHANGED",same,flush=True)
 assert owned and owned.returncode==0 and not forced and same
 assert home.parent==out and home.name.startswith("legacy-enum-owned-")
 shutil.rmtree(home)
 print("LEGACY_OWNED_FIXTURE_REMOVED",True,flush=True)
