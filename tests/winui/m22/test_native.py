from pathlib import Path
import os,subprocess,hashlib,tempfile,shutil
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CONFIG=os.environ.get("FLY_M22_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
exe=HERE/"bin"/"x64"/CONFIG/"FlyM22ShellTransferContracts.exe"
assert exe.is_file()
real,before=snapshot_legacy_profile()
logs=ROOT/"logs/m22";logs.mkdir(parents=True,exist_ok=True)
own=Path(tempfile.mkdtemp(prefix="m22-owned-transfer-",dir=logs))
(own/"local").mkdir();(own/"appdata").mkdir()
try:
 env={**os.environ,"LOCALAPPDATA":str(own/"local"),"APPDATA":str(own/"appdata"),
      "TEMP":str(own),"TMP":str(own)}
 args=[str(exe),str(own)]
 expected=30
 unc_used=False
 if os.environ.get("FLY_M22_LOOPBACK_ADMIN_SHARE")=="YES":
  drive=own.drive.rstrip(":").lower()
  if drive:
   unc_root=r"\\\\127.0.0.1\\"+drive+"$"+str(own)[2:]
   try:
    probe=subprocess.run(
        ["cmd","/d","/c","dir",unc_root],
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,timeout=6,check=False)
    if probe.returncode==0:
     args.append(unc_root)
     expected=34
     unc_used=True
    else:
     print("M22_NATIVE_LOOPBACK_UNC=NOT_RUN_ADMIN_SHARE_UNAVAILABLE",
           probe.returncode,flush=True)
   except subprocess.TimeoutExpired:
    print("M22_NATIVE_LOOPBACK_UNC=NOT_RUN_ADMIN_SHARE_PROBE_TIMEOUT",
          flush=True)
 proc=subprocess.run(args,cwd=exe.parent,env=env,
     capture_output=True,text=True,errors="replace",timeout=70)
 assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert f"M22_NATIVE_SUMMARY {expected} passed, 0 failed." in proc.stdout,proc.stdout
 print(f"M22_NATIVE_{CONFIG}_{expected}_REAL_OWNED_SHELL_PASS",True)
 if unc_used:
  for marker in (
      "actual_unc_copy_destination",
      "actual_unc_move_source",
      "unc_recycle_remains_rejected",
      "reject_extended_unc_namespace"):
   assert "M22_NATIVE_PASS "+marker in proc.stdout,proc.stdout
  print("M22_NATIVE_LOOPBACK_UNC_COPY_MOVE_PASS",True,flush=True)
finally:
 assert_legacy_profile_unchanged(real,before)
 shutil.rmtree(own)
 print("M22_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(before))
