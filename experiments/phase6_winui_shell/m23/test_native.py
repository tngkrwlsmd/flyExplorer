"""M2.3 actual native CF_HDROP wire and IFileOperation; no global clipboard use."""
from pathlib import Path
import tempfile,subprocess,hashlib,os,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CONFIG=os.environ.get("FLY_M23_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CONFIG/"FlyM23NativeContracts.exe"
assert exe.is_file()
config=Path(os.environ["APPDATA"])/"fxfile"/"conf"
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
digest=lambda p:hashlib.sha256(p.read_bytes()).digest()
assert all((config/n).is_file() for n in names)
before={n:digest(config/n) for n in names}
log=ROOT/"logs"/"m23";log.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="m23-owned-clipboard-wire-",dir=log))
(own/"local").mkdir();(own/"appdata").mkdir()
try:
 env={**os.environ,"APPDATA":str(own/"appdata"),
      "LOCALAPPDATA":str(own/"local"),"TEMP":str(own),"TMP":str(own)}
 proc=subprocess.run([str(exe),str(own)],cwd=exe.parent,
      env=env,capture_output=True,text=True,errors="replace",timeout=45)
 assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert "M23_NATIVE_SUMMARY 26 passed, 0 failed." in proc.stdout,proc.stdout
 print("M23_NATIVE_"+CONFIG+"_26_PASS_NO_GLOBAL_CLIPBOARD_MUTATION",True)
finally:
 assert all(digest(config/n)==before[n] for n in names)
 shutil.rmtree(own)
 print("M23_ORIGINAL_SIX_USER_CONFIG_HASHES_IDENTICAL",True)
