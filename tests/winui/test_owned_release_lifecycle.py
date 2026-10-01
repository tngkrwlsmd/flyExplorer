"""Real two-revision TEST-ONLY unpackaged Windows WinUI lifecycle.

This is NOT a signed Windows installer or a clean-machine deployment gate.
Only a unique test-owned run directory under logs/m24/lifecycle-owned-prior-v1 can change.
"""
import ctypes as c
import hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from paths import ROOT, APP, app_dir
import psutil
from pywinauto import Desktop

LEGACY=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
        "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(d):
 return {str(p.relative_to(d)):sha(p) for p in d.rglob("*") if p.is_file()
         and p.name!=".fly-owned-install-marker"}
def copy_stage(source,dest,ignore_build=False):
 assert source.is_dir() and not dest.exists()
 for p in source.rglob("*"):
  assert not p.is_symlink()
  if p.is_dir():continue
  if ignore_build and p.suffix.lower() in (".pdb",".lib",".exp"):
   continue
  target=dest/p.relative_to(source)
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(p,target)
  assert sha(p)==sha(target)
def wait_owned_stage_processes(stage,seconds=8):
 root=stage.resolve()
 end=time.monotonic()+seconds
 def owned():
  found=[]
  for proc in psutil.process_iter(["pid","exe"]):
   try:
    exe=proc.info.get("exe")
    if exe and Path(exe).resolve().is_relative_to(root):
     found.append(proc)
   except (psutil.Error,OSError,RuntimeError):
    pass
  return found
 while time.monotonic()<end:
  pending=owned()
  if not pending:return
  time.sleep(.2)
 pending=owned()
 for proc in pending:
  try:proc.terminate()
  except psutil.Error:pass
 _,alive=psutil.wait_procs(pending,timeout=4)
 if alive:
  raise AssertionError("Exact private stage process still owns update files")

def launch(d,folder,env,sha256,label):
 exe=d/"flyExplorer.exe"
 assert exe.is_file() and sha(exe)==sha256
 p=subprocess.Popen([str(exe),str(folder)],cwd=d,env=env)
 hwnd=None
 try:
  end=time.monotonic()+23
  while time.monotonic()<end:
   if p.poll() is not None:break
   if Path(psutil.Process(p.pid).exe()).resolve()!=exe.resolve():
    raise AssertionError("flyExplorer ownership mismatch")
   matches=[w for w in Desktop(backend="uia").windows(process=p.pid)
            if "flyExplorer" in w.window_text()]
   if len(matches)==1:
    hwnd=matches[0].handle
    pane=Desktop(backend="uia").window(handle=hwnd).child_window(
         auto_id="LeftFiles")
    if pane.exists(timeout=.25) and any(
         "lifecycle-owned.txt" in x.window_text()
         for x in pane.descendants()
         if x.element_info.control_type=="ListItem"):
     print("OWNED_UNPACKAGED_RELEASE_LAUNCH",label,True,flush=True)
     return
   time.sleep(.28)
  raise AssertionError("Private "+label+" preview did not display owned fixture")
 finally:
  if p.poll() is None:
   if hwnd:
    c.windll.user32.PostMessageW(hwnd,0x10,0,0)
    try:p.wait(timeout=12)
    except subprocess.TimeoutExpired:
     p.terminate();p.wait(timeout=7)
   else:p.terminate();p.wait(timeout=7)
  assert p.returncode==0,"flyExplorer did not exit cleanly"
  wait_owned_stage_processes(d)

def main():
 a=APP
 r=a.parents[1]
 root=r/"logs"/"m24"/"lifecycle-owned-prior-v1"
 v1=root/"v1"
 current=app_dir("Release")
 prior=json.loads((root/"v1-manifest.json").read_text(encoding="utf-8"))
 expected={name:digest for name,digest in prior}
 assert inventory(v1)==expected
 old=expected["flyExplorer.exe"]
 new=sha(current/"flyExplorer.exe")
 assert old!=new,"Require two real distinct Windows Release binaries"
 run=Path(tempfile.mkdtemp(prefix="lifecycle-run-owned-",dir=root))
 installed,nxt,backup=[run/name for name in ("installed","next","backup")]
 mfc=Path(os.environ["APPDATA"])/"fxfile"/"conf"
 before={n:sha(mfc/n) for n in LEGACY if (mfc/n).is_file()}
 fixture=run/"fixture";fixture.mkdir()
 (fixture/"lifecycle-owned.txt").write_text("exact owned binary upgrade",encoding="utf-8")
 env=os.environ.copy()
 runtime=Path(tempfile.mkdtemp(prefix="runtime-owned-",dir=run))
 for k in ("APPDATA","LOCALAPPDATA","TEMP","TMP"):
  path=runtime/k.lower()
  path.mkdir()
  env[k]=str(path)
 for k in ("FLY_M23_OWNED_SESSION","FLY_M23_OWNED_DRAG_TEST"):
  env.pop(k,None)
 passed=False
 try:
  copy_stage(v1,installed)
  assert inventory(installed)==expected
  (installed/".fly-owned-install-marker").write_text(
      "do not confuse with real product",encoding="ascii")
  launch(installed,fixture,env,old,"v1-install")
  copy_stage(current,nxt,ignore_build=True)
  second=inventory(nxt)
  assert second["flyExplorer.exe"]==new
  assert (nxt/"Assets").is_dir()
  installed.rename(backup)
  nxt.rename(installed)
  (installed/".fly-owned-install-marker").write_text(
      "owned v2 test update",encoding="ascii")
  launch(installed,fixture,env,new,"v2-update")
  assert sha(installed/"flyExplorer.exe")==new
  print("PRIVATE_TWO_DIFFERENT_RELEASE_BUILD_UPDATE_PASS",True,flush=True)
  installed.rename(nxt)
  backup.rename(installed)
  assert inventory(installed)==expected
  launch(installed,fixture,env,old,"v1-rollback")
  print("PRIVATE_EXACT_V1_BINARY_ROLLBACK_PASS",True,flush=True)
  assert installed.parent==run and installed.name=="installed"
  assert (installed/".fly-owned-install-marker").is_file()
  shutil.rmtree(installed)
  print("PRIVATE_OWNED_RELEASE_UNINSTALL_PASS",not installed.exists(),flush=True)
  assert all((mfc/n).is_file() and sha(mfc/n)==hash
             for n,hash in before.items())
  (root/"lifecycle-result.json").write_text(json.dumps({
      "v1_exe_sha256":old,"v2_exe_sha256":new,
      "private_install_update_rollback_uninstall":True,
      "signed_msix_or_production_installer_certified":False},indent=2),
      encoding="utf-8")
  print("ORIGINAL_SIX_MFC_SETTINGS_IDENTICAL",True,flush=True)
  passed=True
 finally:
  if passed:
   assert run.parent==root and run.name.startswith("lifecycle-run-owned-")
   if run.exists() and not run.is_symlink():shutil.rmtree(run)
  else:
   print("OWNED_LIFECYCLE_RECOVERY_FILES_RETAINED",run,flush=True)
 return 0 if passed else 1
if __name__=="__main__":sys.exit(main())
