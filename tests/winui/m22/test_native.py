from pathlib import Path
import os,subprocess,hashlib,tempfile,shutil,time
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
 expected=38
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
     expected=42
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
 # Win32 real I/O probes remain in this unique owned workspace only.
 # A 512 MiB sparse source reduces disk pressure while ensuring that the
 # progress callback can be observed before cancellation/termination.
 big_src=own/"interruption-source"
 big_dst=own/"interruption-destination"
 big_src.mkdir();big_dst.mkdir()
 source=big_src/"owned-512MiB.bin"
 with source.open("wb") as out:
  out.write(b"FLY-STAGE-SOURCE-START")
  out.truncate(512*1024*1024)
 with source.open("r+b") as out:
  out.seek(-24,2)
  out.write(b"FLY-STAGE-SOURCE-END!!!!")
 def digest(path):
  hashobj=hashlib.sha256()
  with path.open("rb") as stream:
   while data:=stream.read(2*1024*1024):
    hashobj.update(data)
  return hashobj.hexdigest()
 original_digest=digest(source)
 original_size=source.stat().st_size
 cancel_proc=subprocess.run(
     [str(exe),"--owned-stage-cancel",str(source),str(big_dst)],
     cwd=exe.parent,env=env,capture_output=True,text=True,
     errors="replace",timeout=50,check=False)
 assert cancel_proc.returncode==0,(cancel_proc.returncode,
                                    cancel_proc.stdout,cancel_proc.stderr)
 assert "M22_OWNED_STAGED_MID_COPY_CANCEL=PASS" in cancel_proc.stdout
 assert not (big_dst/source.name).exists()
 assert source.stat().st_size==original_size and digest(source)==original_digest
 print("M22_REAL_STAGED_MID_COPY_CANCEL_SOURCE_UNCHANGED",True,flush=True)
 # Only terminate this Popen-owned fixture; never kill Explorer, the app,
 # another shell helper, or any unrelated user process.
 kill_proc=subprocess.Popen(
     [str(exe),"--owned-stage-kill",str(source),str(big_dst)],
     cwd=exe.parent,env=env,stdin=subprocess.DEVNULL,
     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 observed=False
 try:
  deadline=time.monotonic()+18
  while time.monotonic()<deadline:
   stages=list(big_dst.glob(".flyExplorer-copy-*.partial"))
   if stages and kill_proc.poll() is None:
    kill_proc.kill()
    kill_proc.wait(timeout=5)
    observed=True
    break
   if kill_proc.poll() is not None:
    break
   time.sleep(.003)
 finally:
  if kill_proc.poll() is None:
   kill_proc.kill()
   kill_proc.wait(timeout=5)
 assert observed,"Could not interrupt an actively staged test-owned copy"
 assert not (big_dst/source.name).exists(), "partial content published as target"
 assert source.stat().st_size==original_size and digest(source)==original_digest
 print("M22_REAL_STAGED_KILLED_COPY_FINAL_TARGET_ABSENT",True,flush=True)
 print("M22_REAL_STAGED_KILLED_COPY_SOURCE_BYTES_UNCHANGED",True,flush=True)
 # A forced kill can strand a .partial file. Reclaim only the unique owned
 # workspace in finally; do not delete application/user filesystem files.
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
