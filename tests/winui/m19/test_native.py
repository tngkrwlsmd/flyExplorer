"""Owned synthetic native contracts for the exact M1.9 WinUI read-only core.
Does not invoke MFC or modify the real fxfile user profile.
"""
from pathlib import Path
import hashlib,os,shutil,subprocess,tempfile
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CONFIG=os.environ.get("FLY_M19_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
EXE=HERE/"bin"/"x64"/CONFIG/"FlyM19NativeContracts.exe"
assert EXE.is_file(),EXE
LOGS=ROOT/"logs"/"m19"
LOGS.mkdir(parents=True,exist_ok=True)
user,before=snapshot_legacy_profile()
root=Path(tempfile.mkdtemp(prefix="owned-m19-native-",dir=LOGS))
(root/"localdata").mkdir()
(root/"appdata").mkdir()
try:
 env={**os.environ,"APPDATA":str(root/"appdata"),"LOCALAPPDATA":str(root/"localdata"),
      "TEMP":str(root),"TMP":str(root),
      "FLY_M19_OWNED_NATIVE_ONLY":"YES"}
 result=subprocess.run([str(EXE),str(root)],env=env,cwd=EXE.parent,
      capture_output=True,encoding="utf-8",errors="replace",timeout=60)
 path=LOGS/("m19-native-"+CONFIG.lower()+"-standalone-results.log")
 path.write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 assert "M19_NATIVE_SUMMARY 64 passed, 0 failed." in result.stdout
 assert_legacy_profile_unchanged(user,before)
 print("M19_NATIVE_TESTED_HELPER_CONFIG",CONFIG,flush=True)
 print("M19_NATIVE_WORKSPACE_CONTENT_REGEX_AND_SCALE_64_PASS",True,flush=True)
 print("M19_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(before),flush=True)
 print("M19_NATIVE_OWNED_PROOF",path.name,flush=True)
finally:
 assert root.name.startswith("owned-m19-native-") and root.parent==LOGS
 shutil.rmtree(root,ignore_errors=False)
 print("M19_NATIVE_SYNTHETIC_FIXTURE_RECLAIMED",True,flush=True)
