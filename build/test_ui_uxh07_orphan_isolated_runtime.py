"""Owned isolated-TEMP crash-orphan/live-lock/reparse UXH-07 probe.

Run only against locally built fxfile.exe. Does not manipulate real TEMP,
global system settings or an existing user's profile.
"""
from pathlib import Path
import os,re,time,ctypes as c,subprocess,hashlib,shutil,secrets,psutil
from ctypes import wintypes as w
R=Path(__file__).resolve().parents[1]
original=Path(os.environ["APPDATA"])/"fxfile"/"conf"
six=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
 "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
hashes={n:hashlib.sha256((original/n).read_bytes()).digest() for n in six}
home=R/"logs"/("uxh07-orphan-isolated-"+secrets.token_hex(4))
home.mkdir();temp=home/"private_temp";temp.mkdir()
config=home/"private_conf";config.mkdir()
fixture=home/"synthetic_folder";fixture.mkdir()
appdata=home/"private_appdata";appdata.mkdir()
for n in six:shutil.copy2(original/n,config/n)
# Only edit owned copies; disable system integrations and startup popups.
p=config/"fxfile.conf";b=p.read_bytes()
encoding="utf-16" if b[:2] in (b"\xff\xfe",b"\xfe\xff") else "utf-8"
t=b.decode(encoding)
for key,val in (("config.global_hotkey.enable","0"),
 ("config.global_hotkey.show_tray","0"),
 ("config.global_hotkey.windows_startup","0"),
 ("config.register_shell_context_menu","0"),
 ("config.single_process","0")):
 t,n=re.subn(r"(?m)^(\s*"+re.escape(key)+r"\s*=\s*)[^\r\n]*",
             lambda m:m.group(1)+val,t)
 if not n:
  assert t.lstrip().startswith("[config]")
  t=t.replace("[config]","[config]\n"+key+" = "+val,1)
p.write_bytes(t.encode(encoding))
(config/"fxfile-main.conf").write_text(
 "[main]\nmain.tip_of_today.show = 0\n"
 "main.view.row_count = 1\nmain.view.column_count = 1\n",
 encoding="utf-16")
MARKER=b"flyExplorer-ephemeral-workspace-v1\n"
def dname():
 for _ in range(100):
  result=temp/("fxw"+secrets.token_hex(2).upper()+".tmp")
  if not result.exists():
   result.mkdir()
   return result
 raise AssertionError("owned isolated synthetic dir name collision")
def stage(path):
 (path/"fxfile-workspace-owned.marker").write_bytes(MARKER)
 (path/"fxfile.conf").write_text("test-owned-synthetic-only\n",encoding="utf-8")
 os.utime(path/"fxfile-workspace-owned.marker",
          (time.time()-72*3600,time.time()-72*3600))
stale=dname();stage(stale)
locked=dname();stage(locked)
# Verify locked marker cannot be acquired a second time by the app.
kernel=c.windll.kernel32
kernel.CreateFileW.argtypes=(w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,
 w.DWORD,w.DWORD,w.HANDLE)
kernel.CreateFileW.restype=w.HANDLE
kernel.CloseHandle.argtypes=(w.HANDLE,)
invalid=c.c_void_p(-1).value
held=kernel.CreateFileW(str(locked/"fxfile-workspace-owned.marker"),
                       0x80000000,0,None,3,0x80,None)
assert held not in (invalid,0),"test failed to lock owned live marker"
target=home/"owned_external_target";target.mkdir()
sentinel=target/"owned-sentinel.txt";sentinel.write_text("test-only keep",encoding="utf-8")
linkpath=None
candidate=dname();candidate.rmdir()
# Junction is a reparse-point negative control with EXCLUSIVELY test-owned
# external target. We never recurse into the junction.
junction=subprocess.run(["cmd","/c","mklink","/J",str(candidate),str(target)],
 capture_output=True,text=True,timeout=6)
if junction.returncode==0:
 linkpath=candidate
 assert linkpath.is_dir() and sentinel.is_file()
 stage(target)
 os.utime(target/"fxfile-workspace-owned.marker",
          (time.time()-72*3600,time.time()-72*3600))
 print("TEST_OWNED_JUNCTION_REPARSE_CREATED=True",flush=True)
else:print("TEST_OWNED_JUNCTION_REPARSE_CREATED=False NOT_TESTED",flush=True)
print("TEST_OWNED_72H_ORPHAN_AND_EXCLUSIVE_LIVE_MARKER_CREATED=True",flush=True)
u=c.windll.user32
CALLBACK=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
u.EnumWindows.argtypes=(CALLBACK,w.LPARAM)
u.GetWindowThreadProcessId.argtypes=(w.HWND,c.POINTER(w.DWORD))
u.PostMessageW.argtypes=(w.HWND,w.UINT,w.WPARAM,w.LPARAM)
u.GetWindowTextW.argtypes=(w.HWND,w.LPWSTR,c.c_int)
def owned_title(h):
 b=c.create_unicode_buffer(260)
 u.GetWindowTextW(h,b,len(b))
 return b.value
proc=None
try:
 env={**os.environ,"TEMP":str(temp),"TMP":str(temp),
      "APPDATA":str(appdata)}
 proc=subprocess.Popen([str(R/"bin/x64/fxfile.exe"),"--conf_dir",str(config),
   str(fixture)],cwd=home,env=env,stdin=subprocess.DEVNULL,
   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  if not stale.exists():break
  if proc.poll() is not None:break
  time.sleep(.1)
 print("REAL_APP_CLEANED_ONLY_TEST_OWNED_AGED_ORPHAN",not stale.exists(),
       flush=True)
 assert not stale.exists(),"real app startup failed to reap owned 72h orphan"
 assert locked.is_dir() and (locked/"fxfile.conf").is_file(),(
     "app removed locked live synthetic session")
 print("REAL_APP_PRESERVED_TEST_OWNED_LOCKED_LIVE_SESSION=True",
       flush=True)
 if linkpath:
  assert linkpath.is_dir() and sentinel.read_text()=="test-only keep"
  print("REAL_APP_IGNORED_TEST_OWNED_REPARSE_AND_EXTERNAL_SENTINEL=True",
        flush=True)
 # Close only the exact test-launched PID-owned main window.
 wins=[]
 @CALLBACK
 def cb(h,_):
  q=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(q))
  if (q.value==proc.pid and u.IsWindowVisible(h)
   and owned_title(h).endswith(" - fxfile")):
   wins.append(h)
  return True
 for _ in range(80):
  wins.clear();u.EnumWindows(cb,0)
  if len(wins)>=1:break
  time.sleep(.1)
 assert len(wins)==1 and proc.poll() is None,(
   "refuse to close ambiguous owned main HWND",len(wins),proc.poll())
 assert u.PostMessageW(wins[0],0x10,0,0)
 assert proc.wait(timeout=12)==0
 print("ORPHAN_PROBE_OWNED_REAL_APP_EXIT_0=True",flush=True)
finally:
 if proc and proc.poll() is None:
  proc.terminate();proc.wait(timeout=5)
 kernel.CloseHandle(held)
 assert sentinel.is_file() and sentinel.read_text()=="test-only keep"
 # Remove only individually verified test-owned paths. Junctions never
 # passed to recursive deletion. Avoid touching any real TEMP roots.
 if linkpath:
  assert linkpath.parent==temp
  linkpath.rmdir()
 for x in (locked,stale):
  if x.exists():
   assert x.parent==temp and re.fullmatch("fxw[0-9A-Fa-f]{4}[.]tmp",x.name)
   shutil.rmtree(x)
 assert all(hashlib.sha256((original/n).read_bytes()).digest()==hashes[n]
            for n in six)
 print("ORIGINAL_SIX_USER_SETTINGS_SHA256_UNCHANGED=True",flush=True)
 shutil.rmtree(home)
 print("ALL_TEST_OWNED_ISOLATED_ORPHAN_FIXTURES_REMOVED=True",flush=True)
