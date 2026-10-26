"""Isolated native M2.1 test. Real legacy user configuration is read-only."""
from pathlib import Path
import os,hashlib,shutil,subprocess,tempfile
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent if 'HERE' in globals() else p.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CFG=os.environ.get("FLY_M21_CONFIG","Debug")
assert CFG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CFG/"FlyM21NativeContracts.exe"
assert exe.is_file()
real,original=snapshot_legacy_profile()
log=ROOT/"logs/m21";log.mkdir(exist_ok=True,parents=True)
own=Path(tempfile.mkdtemp(prefix="m21-native-owned-",dir=log))
for name in ("local","appdata"):(own/name).mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(own/"local"),"APPDATA":str(own/"appdata"),
      "TEMP":str(own),"TMP":str(own)}
 result=subprocess.run([str(exe),str(own)],env=env,cwd=exe.parent,
  capture_output=True,text=True,errors="replace",timeout=40)
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 assert "M21_NATIVE_SUMMARY 34 passed, 0 failed." in result.stdout,result.stdout
 print("M21_NATIVE_"+CFG+"_34_PASS",True)
finally:
 assert_legacy_profile_unchanged(real,original)
 shutil.rmtree(own)
 print("M21_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(original))
