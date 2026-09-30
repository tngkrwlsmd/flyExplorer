from pathlib import Path
import os,subprocess,hashlib,tempfile,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONFIG=os.environ.get("FLY_M22_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CONFIG/"FlyM22ShellTransferContracts.exe"
assert exe.is_file()
real=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat","fxfile-coolbar.dat",
       "fxfile-dlg_state.conf","fxfile-folder_layout.conf")
sha=lambda x:hashlib.sha256(x.read_bytes()).digest()
assert all((real/n).is_file() for n in names)
before={n:sha(real/n) for n in names}
logs=ROOT/"logs/m22";logs.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="m22-owned-transfer-",dir=logs))
(own/"local").mkdir();(own/"appdata").mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(own/"local"),"APPDATA":str(own/"appdata"),
      "TEMP":str(own),"TMP":str(own)}
 proc=subprocess.run([str(exe),str(own)],cwd=exe.parent,env=env,
     capture_output=True,text=True,errors="replace",timeout=50)
 assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert "M22_NATIVE_SUMMARY 18 passed, 0 failed." in proc.stdout,proc.stdout
 print("M22_NATIVE_"+CONFIG+"_18_REAL_OWNED_SHELL_PASS",True)
finally:
 assert all(sha(real/n)==before[n] for n in names)
 shutil.rmtree(own)
 print("M22_ORIGINAL_SIX_CONF_SHA256_UNMODIFIED",True)
