"""Owned synthetic native contracts for the exact M1.9 WinUI read-only core.
Does not invoke MFC or modify the real fxfile user profile.
"""
from pathlib import Path
import hashlib,os,shutil,subprocess,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONFIG=os.environ.get("FLY_M19_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
EXE=HERE/"bin"/"x64"/CONFIG/"FlyM19NativeContracts.exe"
assert EXE.is_file(),EXE
LOGS=ROOT/"logs"/"m19"
LOGS.mkdir(parents=True,exist_ok=True)
user=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
"fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
assert all((user/f).is_file() for f in names)
before={f:hashlib.sha256((user/f).read_bytes()).digest() for f in names}
root=Path(tempfile.mkdtemp(prefix="owned-m19-native-",dir=LOGS))
(root/"localdata").mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(root/"localdata"),
      "TEMP":str(root),"TMP":str(root),
      "FLY_M19_OWNED_NATIVE_ONLY":"YES"}
 result=subprocess.run([str(EXE),str(root)],env=env,cwd=EXE.parent,
      capture_output=True,encoding="utf-8",errors="replace",timeout=27)
 path=LOGS/("m19-native-"+CONFIG.lower()+"-standalone-results.log")
 path.write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 assert "M19_NATIVE_SUMMARY 12 passed, 0 failed." in result.stdout
 assert all(hashlib.sha256((user/f).read_bytes()).digest()==h
            for f,h in before.items())
 print("M19_NATIVE_TESTED_HELPER_CONFIG",CONFIG,flush=True)
 print("M19_NATIVE_WORKSPACE_AND_RECENT_SEARCH_12_PASS",True,flush=True)
 print("M19_ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",True,flush=True)
 print("M19_NATIVE_OWNED_PROOF",path.name,flush=True)
finally:
 assert root.name.startswith("owned-m19-native-") and root.parent==LOGS
 shutil.rmtree(root,ignore_errors=False)
 print("M19_NATIVE_SYNTHETIC_FIXTURE_RECLAIMED",True,flush=True)
