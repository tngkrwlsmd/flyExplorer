"""Isolated M2.0 native state/command tests, actual user config hash safe."""
import hashlib,os,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
root=p.parents[2]
config=os.environ.get("FLY_M20_CONFIG","Debug")
assert config in ("Debug","Release")
exe=p/"bin"/"x64"/config/"FlyM20StateContracts.exe"
assert exe.is_file()
names=("fxfile.conf","fxfile-main.conf","fxfile-toolbar.dat",
       "fxfile-coolbar.dat","fxfile-dlg_state.conf","fxfile-folder_layout.conf")
conf=Path(os.environ["APPDATA"])/"fxfile"/"conf"
assert all((conf/n).is_file() for n in names)
digest=lambda x:hashlib.sha256(x.read_bytes()).digest()
before={n:digest(conf/n) for n in names}
result=subprocess.run([str(exe)],cwd=exe.parent,capture_output=True,
    text=True,errors="replace",timeout=20)
assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
assert "M20_NATIVE_SUMMARY 16 passed, 0 failed." in result.stdout,result.stdout
assert all(digest(conf/n)==before[n] for n in names)
print("M20_STANDALONE_NATIVE_"+config+"_16_PASS",True)
print("M20_ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL",True)
