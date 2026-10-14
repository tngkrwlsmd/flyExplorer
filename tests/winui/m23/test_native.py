"""M2.3 actual native CF_HDROP wire and IFileOperation; no global clipboard use."""
from pathlib import Path
import tempfile,subprocess,hashlib,os,shutil
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CONFIG=os.environ.get("FLY_M23_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CONFIG/"FlyM23NativeContracts.exe"
assert exe.is_file()
config,before=snapshot_legacy_profile()
log=ROOT/"logs"/"m23";log.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="m23-owned-clipboard-wire-",dir=log))
(own/"local").mkdir();(own/"appdata").mkdir()
try:
 env={**os.environ,"APPDATA":str(own/"appdata"),
      "LOCALAPPDATA":str(own/"local"),"TEMP":str(own),"TMP":str(own)}
 proc=subprocess.run([str(exe),str(own)],cwd=exe.parent,
      env=env,capture_output=True,text=True,errors="replace",timeout=45)
 assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert "M23_NATIVE_SUMMARY 35 passed, 0 failed." in proc.stdout,proc.stdout
 print("M23_NATIVE_"+CONFIG+"_35_PASS_NO_GLOBAL_CLIPBOARD_MUTATION",True)
finally:
 assert_legacy_profile_unchanged(config,before)
 shutil.rmtree(own)
 print("M23_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(before))
