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
 expected=61
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
     expected=65
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
 # A same-named but unrelated partial must remain untouched even when
 # an exact stage from a killed test-owned transfer is reclaimed.
 kill_sentinel=big_dst/".flyExplorer-copy-{00000000-0000-0000-0000-000000000000}.partial"
 kill_sentinel.write_bytes(b"unrelated-partial-data-must-survive")
 kill_stage=None
 kill_identity=None
 kill_proc=subprocess.Popen(
     [str(exe),"--owned-stage-kill",str(source),str(big_dst)],
     cwd=exe.parent,env=env,stdin=subprocess.DEVNULL,
     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 observed=False
 try:
  deadline=time.monotonic()+18
  while time.monotonic()<deadline:
   stages=[p for p in big_dst.glob(".flyExplorer-copy-*.partial")
           if p!=kill_sentinel]
   if stages and kill_proc.poll() is None:
    st=stages[0].lstat()
    if st.st_ino==0 or st.st_size<4*1024*1024:
     time.sleep(.003)
     continue
    kill_stage=stages[0]
    kill_identity=(st.st_dev,st.st_ino)
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
 # This is an explicit receipt-scoped test cleanup, NOT a production
 # orphan sweep. A durable production receipt is not yet implemented.
 # Verify the exact pre-kill path and filesystem file ID; never delete
 # an unknown, renamed or reparse-point stage based only on its name.
 assert kill_stage is not None and kill_identity is not None
 assert kill_stage.parent==big_dst and not kill_stage.is_symlink()
 assert kill_stage.name.startswith(".flyExplorer-copy-{")
 assert kill_stage.name.endswith("}.partial")
 assert kill_stage.exists(),("Interrupted stage unexpectedly disappeared",kill_stage)
 recovered=kill_stage.lstat()
 assert recovered.st_nlink==1
 assert (recovered.st_dev,recovered.st_ino)==kill_identity
 kill_stage.unlink()
 assert not kill_stage.exists()
 assert kill_sentinel.read_bytes()==b"unrelated-partial-data-must-survive"
 assert list(big_dst.glob(".flyExplorer-copy-*.partial"))==[kill_sentinel]
 print("M22_KILLED_STAGE_EXACT_IDENTITY_RECLAIM_TEST_OWNED_ONLY",True,flush=True)
 print("M22_KILLED_STAGE_UNRELATED_PARTIAL_UNTOUCHED",True,flush=True)
 # A forced kill can strand a .partial file. Reclaim only the unique owned
 # workspace in finally; do not delete application/user filesystem files.
 # Test a publication race on another uniquely owned destination.
 # The late target must remain byte-for-byte intact, and the stage should
 # be removed after MoveFileEx declines to overwrite the new target.
 race_dst=own/"publish-race-destination"
 race_dst.mkdir()
 sentinel=race_dst/".flyExplorer-copy-{00000000-0000-0000-0000-000000000000}.partial"
 sentinel.write_bytes(b"unrelated-stage-must-never-be-removed")
 race_process=subprocess.Popen(
     [str(exe),"--owned-stage-race",str(source),str(race_dst)],
     cwd=exe.parent,env=env,stdin=subprocess.DEVNULL,
     stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 raced=False
 try:
  deadline=time.monotonic()+18
  while time.monotonic()<deadline:
   stage_files=[p for p in race_dst.glob(".flyExplorer-copy-*.partial")
                if p.name!=sentinel.name]
   if stage_files and race_process.poll() is None:
    with (race_dst/source.name).open("xb") as out:
     out.write(b"preexisting-race-destination-must-be-kept")
    raced=True
    break
   if race_process.poll() is not None:
    break
   time.sleep(.003)
  stdout,stderr=race_process.communicate(timeout=45)
 finally:
  if race_process.poll() is None:
   race_process.kill()
   race_process.wait(timeout=5)
 assert raced,"Could not introduce a late destination in an active stage"
 assert race_process.returncode==0,(race_process.returncode,
                                    stdout,stderr)
 assert b"M22_OWNED_STAGE_LATE_TARGET_COLLISION=PASS" in stdout
 assert (race_dst/source.name).read_bytes()==(
     b"preexisting-race-destination-must-be-kept")
 assert sentinel.read_bytes()==b"unrelated-stage-must-never-be-removed"
 assert list(race_dst.glob(".flyExplorer-copy-*.partial"))==[sentinel], (
     "The failed copy should clean only its own unfinished stage")
 assert source.stat().st_size==original_size and digest(source)==original_digest
 print("M22_STAGED_LATE_TARGET_COLLISION_PRESERVED_BYTES",True,flush=True)
 print("M22_STAGED_UNRELATED_PARTIAL_NEVER_DELETED",True,flush=True)

 # Deny WRITE_DATA on the test-owned directory only. Revert in finally,
 # before the owned directory is reclaimed. Do not alter user directories
 # or rely on the machine-wide clipboard, Recycle Bin or permission state.
 import re
 whoami=subprocess.run(["whoami","/user","/fo","csv","/nh"],
     capture_output=True,text=True,errors="replace",timeout=10,check=True)
 sid_match=re.search(r"S-1-5-21(?:-\d+){4}",whoami.stdout)
 assert sid_match,("Could not identify test-session SID",whoami.stdout)
 sid="*"+sid_match.group(0)
 denied_dst=own/"write-denied-destination"
 denied_dst.mkdir()
 acl_set=subprocess.run(["icacls",str(denied_dst),"/deny",sid+":(WD)"],
     capture_output=True,text=True,errors="replace",timeout=15,check=False)
 assert acl_set.returncode==0,("Failed to restrict test-owned directory",
                                acl_set.stdout,acl_set.stderr)
 try:
  denied=subprocess.run(
      [str(exe),"--owned-stage-deny",str(source),str(denied_dst)],
      cwd=exe.parent,env=env,capture_output=True,text=True,
      errors="replace",timeout=25,check=False)
  # Move goes through IFileOperation rather than the staged Copy path.
  # Denying creation in a disposable destination must leave the source.
  move_source=big_src/"acl-denied-move.txt"
  move_source.write_bytes(b"owned-move-source-must-survive")
  move_denied=subprocess.run(
      [str(exe),"--owned-move-deny",str(move_source),str(denied_dst)],
      cwd=exe.parent,env=env,capture_output=True,text=True,
      errors="replace",timeout=25,check=False)
 finally:
  acl_undo=subprocess.run(
      ["icacls",str(denied_dst),"/remove:d",sid],
      capture_output=True,text=True,errors="replace",timeout=15,check=False)
  assert acl_undo.returncode==0,("Failed to restore test-owned ACL",
                                 acl_undo.stdout,acl_undo.stderr)
 assert denied.returncode==0,(denied.returncode,
                               denied.stdout,denied.stderr)
 assert "M22_OWNED_STAGE_DENIED_DESTINATION=PASS" in denied.stdout
 assert move_denied.returncode==0,(move_denied.returncode,
                                       move_denied.stdout,move_denied.stderr)
 assert "M22_OWNED_MOVE_DENIED=PASS" in move_denied.stdout
 assert move_source.read_bytes()==b"owned-move-source-must-survive"
 assert not (denied_dst/move_source.name).exists()
 print("M22_DENIED_MOVE_PRESERVES_ORIGINAL_SOURCE",True,flush=True)
 assert not (denied_dst/source.name).exists()
 assert not list(denied_dst.glob(".flyExplorer-copy-*.partial"))
 assert source.stat().st_size==original_size and digest(source)==original_digest
 print("M22_STAGED_DENIED_WRITE_SOURCE_PRESERVED",True,flush=True)
 print("M22_STAGED_DENIED_WRITE_NO_DESTINATION",True,flush=True)
 # Change the ACL AFTER CopyFileEx has opened and written its private
 # stage. This may leave the existing writable handle valid on Windows;
 # acceptance is therefore either a complete verified copy, or an error
 # without any partial final file. Never equate ACL mutation with a guaranteed
 # in-flight write failure.
 live_dst=own/"live-acl-destination"
 live_dst.mkdir()
 live_sentinel=live_dst/"unrelated-marker.txt"
 live_sentinel.write_bytes(b"not-owned-by-current-copy")
 live_proc=subprocess.Popen(
     [str(exe),"--owned-stage-kill",str(source),str(live_dst)],
     cwd=exe.parent,env=env,stdin=subprocess.DEVNULL,
     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 live_stage=None
 live_applied=False
 try:
  deadline=time.monotonic()+18
  while time.monotonic()<deadline:
   found=list(live_dst.glob(".flyExplorer-copy-*.partial"))
   if found and live_proc.poll() is None:
    try:
     if found[0].stat().st_size>=4*1024*1024:
      live_stage=found[0]
      break
    except FileNotFoundError:
     pass
   if live_proc.poll() is not None:
    break
   time.sleep(.002)
  assert live_stage is not None,(
      "Could not observe a writable in-progress test-owned stage")
  live_acl=subprocess.run(
      ["icacls",str(live_dst),"/deny",sid+":(WD)"],
      capture_output=True,text=True,errors="replace",
      timeout=12,check=False)
  assert live_acl.returncode==0,(live_acl.stdout,live_acl.stderr)
  live_applied=True
  # The observed stage must still be in progress when the ACL mutation
  # has finished. Otherwise this run is not evidence of a live-ACL race.
  active_after_acl=live_proc.poll() is None
  live_code=live_proc.wait(timeout=45)
 finally:
  if live_proc.poll() is None:
   live_proc.kill()
   live_proc.wait(timeout=5)
  if live_applied:
   restore=subprocess.run(
       ["icacls",str(live_dst),"/remove:d",sid],
       capture_output=True,text=True,errors="replace",
       timeout=15,check=False)
   assert restore.returncode==0,("Test-owned ACL restore failed",
                                  restore.stdout,restore.stderr)
 assert active_after_acl, "Copy ended before the live ACL was applied"
 assert live_code in (0,23),("Unexpected native outcome",live_code)
 live_target=live_dst/source.name
 if live_code==0:
  assert live_target.stat().st_size==original_size
  assert digest(live_target)==original_digest, (
      "A partially copied final file was published")
 else:
  assert not live_target.exists(), (
      "A failed in-flight copy published an incomplete final file")
 assert source.stat().st_size==original_size and digest(source)==original_digest
 assert live_sentinel.read_bytes()==b"not-owned-by-current-copy"
 print("M22_LIVE_ACL_AFTER_WRITES_SOURCE_BYTES_PRESERVED",True,flush=True)
 print("M22_LIVE_ACL_AFTER_WRITES_NO_TRUNCATED_FINAL",True,flush=True)
 print("M22_LIVE_ACL_PREEXISTING_DESTINATION_PRESERVED",True,flush=True)
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
