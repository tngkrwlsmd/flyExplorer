"""Isolated M2.0 native state/command tests, actual user config hash safe."""
import hashlib,os,subprocess
from pathlib import Path
import sys
p=Path(__file__).resolve().parent
root=p.parents[2]
sys.path.insert(0,str(HERE.parent if 'HERE' in globals() else p.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
config=os.environ.get("FLY_M20_CONFIG","Debug")
assert config in ("Debug","Release")
exe=p/"bin"/"x64"/config/"FlyM20StateContracts.exe"
assert exe.is_file()
conf,before=snapshot_legacy_profile()
result=subprocess.run([str(exe)],cwd=exe.parent,capture_output=True,
    text=True,errors="replace",timeout=20)
assert result.returncode==0,(result.returncode,result.stdout,result.stderr)
assert "M20_NATIVE_SUMMARY 52 passed, 0 failed." in result.stdout,result.stdout
assert_legacy_profile_unchanged(conf,before)
print("M20_STANDALONE_NATIVE_"+config+"_52_PASS",True)
print("M20_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(before))
