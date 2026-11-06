"""R07-18: controlled, fixture-owned actual native restore dispatch."""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
exe=HERE/"bin"/"x64"/"Release"/"FlyR07DispatchNative.exe"
assert exe.is_file()
real,original=snapshot_legacy_profile()
log=ROOT/"logs"/"r07-dispatch"
log.mkdir(parents=True,exist_ok=True)
owned=Path(tempfile.mkdtemp(prefix="r07-dispatch-owned-",dir=log))
try:
    env={**os.environ,"LOCALAPPDATA":str(owned),
         "APPDATA":str(owned),"TEMP":str(owned),"TMP":str(owned)}
    result=subprocess.run([str(exe),str(owned)],cwd=exe.parent,env=env,
        capture_output=True,text=True,errors="replace",timeout=50)
    lines=result.stdout.splitlines()
    expect="R07_DISPATCH_NATIVE_SUMMARY 39 passed, 0 failed."
    if result.returncode or expect not in lines:
        problems=[line for line in lines if line.startswith(("R07_DISPATCH_FAIL","R07_DISPATCH_NATIVE_SUMMARY"))]
        raise AssertionError((result.returncode,problems[:20],lines[-5:],result.stderr[-500:]))
    print("R07_DISPATCH_NATIVE_Release_39_PASS True")
finally:
    assert_legacy_profile_unchanged(real,original)
    shutil.rmtree(owned)
    print("R07_DISPATCH_LEGACY_PROFILE_UNCHANGED True PRESENT",present_count(original))
    print("R07_DISPATCH_OWNED_CLEANUP PASS")
