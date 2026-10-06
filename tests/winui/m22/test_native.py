from pathlib import Path
import os,subprocess,hashlib,tempfile,shutil
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CONFIG=os.environ.get("FLY_M22_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CONFIG/"FlyM22ShellTransferContracts.exe"
assert exe.is_file()
real,before=snapshot_legacy_profile()
logs=ROOT/"logs/m22";logs.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="m22-owned-transfer-",dir=logs))
(own/"local").mkdir();(own/"appdata").mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(own/"local"),"APPDATA":str(own/"appdata"),
      "TEMP":str(own),"TMP":str(own)}
 proc=subprocess.run([str(exe),str(own)],cwd=exe.parent,env=env,
     capture_output=True,text=True,errors="replace",timeout=50)
 assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert "M22_NATIVE_SUMMARY 29 passed, 0 failed." in proc.stdout,proc.stdout
 print("M22_NATIVE_"+CONFIG+"_29_REAL_OWNED_SHELL_PASS",True)
finally:
 assert_legacy_profile_unchanged(real,before)
 shutil.rmtree(own)
 print("M22_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(before))
