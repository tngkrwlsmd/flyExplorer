"""R07-15 native controller ownership with no GUI or user-file mutations."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged, present_count, snapshot_legacy_profile

exe = HERE / "bin" / "x64" / "Release" / "FlyR07OwnerNative.exe"
assert exe.is_file()
real, original = snapshot_legacy_profile()
log = ROOT / "logs" / "r07-owner"
log.mkdir(parents=True, exist_ok=True)
own = Path(tempfile.mkdtemp(prefix="r07-owner-owned-", dir=log))
try:
    env = {**os.environ, "LOCALAPPDATA": str(own),
           "APPDATA": str(own), "TEMP": str(own), "TMP": str(own)}
    result = subprocess.run(
        [str(exe)], cwd=exe.parent, env=env, capture_output=True,
        text=True, errors="replace", timeout=30
    )
    lines = result.stdout.splitlines()
    summary = "R07_OWNER_NATIVE_SUMMARY 26 passed, 0 failed."
    if result.returncode or summary not in lines:
        failures = [line for line in lines if line.startswith(
            ("R07_OWNER_FAIL", "R07_OWNER_NATIVE_SUMMARY"))]
        raise AssertionError((result.returncode, failures[:20],
                              lines[-6:], result.stderr[-600:]))
    print("R07_OWNER_NATIVE_Release_26_PASS True")
finally:
    assert_legacy_profile_unchanged(real, original)
    shutil.rmtree(own)
    print("R07_OWNER_LEGACY_PROFILE_UNCHANGED True PRESENT", present_count(original))
    print("R07_OWNER_DISPOSABLE_CLEANUP PASS")
