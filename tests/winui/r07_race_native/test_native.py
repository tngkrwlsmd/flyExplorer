"""R07-17: deterministic, disposable native race tests only."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import (assert_legacy_profile_unchanged,
                           present_count,snapshot_legacy_profile)

exe=HERE/"bin"/"x64"/"Release"/"FlyR07RaceNative.exe"
assert exe.is_file()
real,original=snapshot_legacy_profile()
log=ROOT/"logs"/"r07-race"
log.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="r07-race-owned-",dir=log))
try:
    env={**os.environ,"LOCALAPPDATA":str(own),
         "APPDATA":str(own),"TEMP":str(own),"TMP":str(own)}
    result=subprocess.run(
        [str(exe),str(own)],env=env,cwd=exe.parent,
        capture_output=True,text=True,errors="replace",timeout=45,
    )
    lines=result.stdout.splitlines()
    for line in lines:
        if line.startswith("R07_RACE_PARENT_MOVE_ATTEMPT "):
            print(line[:240])
    summary="R07_RACE_NATIVE_SUMMARY 8 passed, 0 failed."
    if result.returncode!=0 or summary not in lines:
        diagnostic=[line for line in lines if line.startswith(
            ("R07_RACE_FAIL ","R07_RACE_PARENT_MOVE_ATTEMPT ",
             "R07_RACE_NATIVE_SUMMARY "))]
        raise AssertionError((result.returncode,diagnostic[:20],
                              lines[-5:],result.stderr[-500:]))
    print("R07_RACE_NATIVE_Release_8_PASS True")
finally:
    assert_legacy_profile_unchanged(real,original)
    shutil.rmtree(own)
    print("R07_RACE_LEGACY_PROFILE_UNCHANGED True PRESENT",present_count(original))
    print("R07_RACE_OWNED_CLEANUP PASS")
