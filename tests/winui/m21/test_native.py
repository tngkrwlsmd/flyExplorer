"""Isolated native M2.1 test. Real legacy user configuration is read-only."""
from pathlib import Path
import os,hashlib,shutil,subprocess,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CFG=os.environ.get("FLY_M21_CONFIG","Debug")
assert CFG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CFG/"FlyM21NativeContracts.exe"
assert exe.is_file()
real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
"fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
digest=lambda x:hashlib.sha256(x.read_bytes()).digest()
assert all((real/n).is_file() for n in names)
original={n:digest(real/n) for n in names}
log=ROOT/"logs/m21";log.mkdir(exist_ok=True,parents=True)
own=Path(tempfile.mkdtemp(prefix="m21-native-owned-",dir=log))
for name in ("local","appdata"):(own/name).mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(own/"local"),"APPDATA":str(own/"appdata"),
      "TEMP":str(own),"TMP":str(own)}
 result=subprocess.run([str(exe),str(own)],env=env,cwd=exe.parent,
  capture_output=True,text=True,errors="replace",timeout=40)
 assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
 assert "M21_NATIVE_SUMMARY 18 passed, 0 failed." in result.stdout,result.stdout
 print("M21_NATIVE_"+CFG+"_18_PASS",True)
finally:
 assert all(digest(real/n)==original[n] for n in names)
 shutil.rmtree(own)
 print("M21_ORIGINAL_SIX_CONFIG_HASHES_IDENTICAL",True)
