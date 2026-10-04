"""M1.6 test-owned native Shell helper / exact-child process recovery.

This validates an isolated PROCESS experiment, not shipped WinUI routing,
an actual hung third-party Shell extension, or a restricted security sandbox.
"""
from pathlib import Path
import ctypes as ct
from ctypes import wintypes as wt
import hashlib
import os
import shutil
import struct
import subprocess
import tempfile
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from profile_guard import assert_legacy_profile_unchanged,present_count,snapshot_legacy_profile
CONFIG=os.environ.get("FLY_M16_CONFIG","Debug")
assert CONFIG in ("Debug","Release")
EXE=ROOT/"out"/"helper"/CONFIG/"FlyShellIsolationHelper.exe"
assert EXE.is_file(),EXE
LOGROOT=ROOT/"logs"/"m16"
LOGROOT.mkdir(parents=True,exist_ok=True)
OWNED=Path(tempfile.mkdtemp(prefix="m16-process-owned-",dir=LOGROOT))
MAGIC=0x314C5346
K=ct.WinDLL("kernel32",use_last_error=True)
HANDLE=wt.HANDLE
SIZE_T=ct.c_size_t
ULONGLONG=ct.c_ulonglong
DWORD=wt.DWORD

class BasicLimits(ct.Structure):
    _fields_=[("PerProcessUserTimeLimit",ct.c_longlong),
              ("PerJobUserTimeLimit",ct.c_longlong),
              ("LimitFlags",DWORD),
              ("MinimumWorkingSetSize",SIZE_T),
              ("MaximumWorkingSetSize",SIZE_T),
              ("ActiveProcessLimit",DWORD),
              ("Affinity",SIZE_T),
              ("PriorityClass",DWORD),
              ("SchedulingClass",DWORD)]
class IoCounters(ct.Structure):
    _fields_=[(n,ULONGLONG) for n in
      ("ReadOperationCount","WriteOperationCount","OtherOperationCount",
       "ReadTransferCount","WriteTransferCount","OtherTransferCount")]
class ExtendedLimits(ct.Structure):
    _fields_=[("BasicLimitInformation",BasicLimits),
              ("IoInfo",IoCounters),
              ("ProcessMemoryLimit",SIZE_T),("JobMemoryLimit",SIZE_T),
              ("PeakProcessMemoryUsed",SIZE_T),("PeakJobMemoryUsed",SIZE_T)]
K.CreateJobObjectW.argtypes=[ct.c_void_p,wt.LPCWSTR]
K.CreateJobObjectW.restype=HANDLE
K.SetInformationJobObject.argtypes=[HANDLE,ct.c_int,ct.c_void_p,DWORD]
K.SetInformationJobObject.restype=wt.BOOL
K.AssignProcessToJobObject.argtypes=[HANDLE,HANDLE]
K.AssignProcessToJobObject.restype=wt.BOOL
K.IsProcessInJob.argtypes=[HANDLE,HANDLE,ct.POINTER(wt.BOOL)]
K.IsProcessInJob.restype=wt.BOOL
K.TerminateJobObject.argtypes=[HANDLE,ct.c_uint]
K.TerminateJobObject.restype=wt.BOOL
K.CloseHandle.argtypes=[HANDLE]
K.CloseHandle.restype=wt.BOOL
JOBS=[]
CHILDREN=[]

def job_for(owned_child):
    assert owned_child.poll() is None
    h=K.CreateJobObjectW(None,None)
    assert h,"CreateJobObjectW "+str(ct.get_last_error())
    info=ExtendedLimits()
    info.BasicLimitInformation.LimitFlags=0x00002000 # KILL_ON_JOB_CLOSE
    if not K.SetInformationJobObject(h,9,ct.byref(info),ct.sizeof(info)):
        K.CloseHandle(h)
        raise RuntimeError("SetInformationJobObject "+str(ct.get_last_error()))
    if not K.AssignProcessToJobObject(h,int(owned_child._handle)):
        K.CloseHandle(h)
        raise RuntimeError("AssignProcessToJobObject "+str(ct.get_last_error()))
    member=wt.BOOL()
    assert K.IsProcessInJob(int(owned_child._handle),h,ct.byref(member))
    assert member.value,"owned child is not isolated in its private job"
    JOBS.append(h)
    return h

def launch(*args,extra_env=None):
    env={**os.environ,"APPDATA":str(OWNED/"appdata"),"LOCALAPPDATA":str(OWNED/"localdata"),"TEMP":str(OWNED),"TMP":str(OWNED),**(extra_env or {})}
    process=subprocess.Popen([str(EXE),*args],
       stdin=subprocess.PIPE,stdout=subprocess.PIPE,
       stderr=subprocess.DEVNULL,env=env,
       creationflags=0x08000000) # CREATE_NO_WINDOW
    CHILDREN.append(process)
    return process

def request(path=None,pidl_bytes=None,offset=0,limit=1024):
    assert 0<=offset<20000 and 1<=limit<=1024 and offset+limit<=20000
    if pidl_bytes is not None:
        assert pidl_valid(pidl_bytes)
        return struct.pack("<IIIIII",MAGIC,3,2,len(pidl_bytes),
                           offset,limit)+pidl_bytes
    raw=str(path).encode("utf-16le")
    units=len(raw)//2
    assert 0<units<=16384
    return struct.pack("<IIIIII",MAGIC,3,1,units,offset,limit)+raw

def pidl_valid(raw):
    off=0
    while True:
        if off+2>len(raw):return False
        cb=int.from_bytes(raw[off:off+2],"little")
        if cb==0:return off+2==len(raw)
        if cb<2 or off+cb>len(raw):return False
        off+=cb

def parse(frame):
    if len(frame)<28:raise ValueError("short result")
    magic,version,hr,count,n,expected,flags=struct.unpack_from("<IIiIIII",frame)
    if magic!=MAGIC or version!=3 or count>1024 or n>8*1024**2:
        raise ValueError("result protocol bounds")
    if len(frame)!=28+n:raise ValueError("result frame length")
    body=frame[28:]
    digest=2166136261
    for byte in body:digest=((digest^byte)*16777619)&0xffffffff
    if digest!=expected:raise ValueError("corrupted body")
    if flags&~1:raise ValueError("unknown flags")
    if hr<0:
        if count or n or flags:raise ValueError("failure contains state")
        return {"hr":hr,"entries":[],"flags":0}
    off=0
    def u32():
        nonlocal off
        if off+4>n:raise ValueError("truncated u32")
        value=struct.unpack_from("<I",body,off)[0]
        off+=4
        return value
    def string(max_units=4096):
        nonlocal off
        units=u32()
        if units>max_units or off+units*2>n:raise ValueError("string bounds")
        value=body[off:off+units*2].decode("utf-16le","strict")
        off+=units*2
        return value
    def pidl():
        nonlocal off
        sz=u32()
        if not 2<=sz<=65536 or off+sz>n:raise ValueError("pidl bounds")
        value=body[off:off+sz]
        off+=sz
        if not pidl_valid(value):raise ValueError("malformed PIDL")
        return value
    folder={"display":string(),"parsing":string(),
            "filesystem_path":string(16384),"pidl":pidl()}
    items=[]
    for _ in range(count):
        attr=u32()
        items.append({"attributes":attr,"name":string(),
                      "parsing":string(),"pidl":pidl()})
    if off!=n:raise ValueError("unconsumed data")
    return {"hr":hr,"folder":folder,"entries":items,"flags":flags}

def roundtrip(folder=None,timeout=12,pidl_bytes=None,offset=0,page_limit=1024):
    child=launch()
    job=job_for(child)
    started=time.monotonic()
    out,_=child.communicate(
        request(folder,pidl_bytes,offset,page_limit),timeout=timeout)
    elapsed=time.monotonic()-started
    assert child.returncode==0,("helper failed",child.returncode)
    return parse(out),out,elapsed

REAL_CONF,original=snapshot_legacy_profile()
(OWNED/"appdata").mkdir()
(OWNED/"localdata").mkdir()
try:
    left=OWNED/"Left";right=OWNED/"Right"
    (left/"OwnedNested").mkdir(parents=True)
    (right/"OtherNested").mkdir(parents=True)
    (left/"owned.txt").write_text("synthetic only",encoding="utf-8")
    first,raw,sec=roundtrip(left)
    assert first["hr"]==0 and any(
        e["name"]=="OwnedNested" and e["attributes"]&0x20000000
        for e in first["entries"])
    assert any(e["name"]=="owned.txt" for e in first["entries"])
    assert first["folder"]["filesystem_path"].lower().endswith("left")
    page0,_,_=roundtrip(left,offset=0,page_limit=1)
    page1,_,_=roundtrip(left,offset=1,page_limit=1)
    assert len(page0["entries"])==1 and page0["flags"]==1
    assert len(page1["entries"])==1 and page1["entries"][0]["name"]!=page0["entries"][0]["name"]
    print("REAL_NATIVE_HELPER_PAGED_OFFSET_LIMIT_PASS",True)
    identical,_,_=roundtrip(pidl_bytes=first["folder"]["pidl"])
    assert identical["hr"]==0 and set(e["name"] for e in identical["entries"])==set(
        e["name"] for e in first["entries"])
    print("REAL_NATIVE_HELPER_LOCAL_COM_SHELL_ENUM_AND_PIDLS PASS",
          "items",len(first["entries"]),"elapsed_ms",round(sec*1000))
    print("REAL_NATIVE_HELPER_ABSOLUTE_PIDL_REQUEST_PASS",True)
    virt,_,_=roundtrip("shell:MyComputerFolder")
    assert virt["hr"]==0 and virt["folder"]["pidl"]
    assert len(virt["entries"])>0 and not virt["folder"]["filesystem_path"]
    virtual_pidl,_,_=roundtrip(pidl_bytes=virt["folder"]["pidl"])
    assert virtual_pidl["hr"]==0 and virtual_pidl["folder"]["pidl"]==virt["folder"]["pidl"]
    print("REAL_NATIVE_HELPER_VIRTUAL_ABSOLUTE_PIDL_PASS",True)
    print("REAL_NATIVE_HELPER_VIRTUAL_THIS_PC PASS",
          "items",len(virt["entries"]))
    failure,_,_=roundtrip(left/"missing-does-not-exist")
    assert failure["hr"]<0 and failure["entries"]==[]
    print("HELPER_INVALID_PATH_RETURNS_NO_PARTIAL_SNAPSHOT PASS")
    for damaged in (raw[:19],raw+b"x",
                    raw[:28]+bytes([raw[28]^1])+raw[29:]):
        try:parse(damaged)
        except ValueError:pass
        else:raise AssertionError("malformed wire reply accepted")
    print("HOST_PROTOCOL_REJECTS_TRUNCATED_OVERSIZE_CORRUPTED_FRAMES PASS")
    malformed=launch()
    job_for(malformed)
    _,_=malformed.communicate(
        struct.pack("<IIIIII",MAGIC,3,1,16385,0,1024),timeout=4)
    assert malformed.returncode==4
    incomplete=launch()
    job_for(incomplete)
    _,_=incomplete.communicate(
        struct.pack("<IIIIII",MAGIC,3,1,6,0,1024)+b"x",timeout=4)
    assert incomplete.returncode==5
    print("HELPER_OVERSIZED_AND_TRUNCATED_REQUESTS_REJECTED PASS")
    # Start two independent lanes. The left one is deliberately *owned* and
    # synthetic; no real Shell extension/user process is hung or terminated.
    blocked=launch("--test-block",
          extra_env={"FLY_M16_OWNED_TEST_ONLY":"YES"})
    slowjob=job_for(blocked)
    time.sleep(.3)
    assert blocked.poll() is None
    healthy,_,elapsed=roundtrip(right,timeout=10)
    assert healthy["hr"]==0 and any(
         e["name"]=="OtherNested" for e in healthy["entries"])
    assert blocked.poll() is None
    print("TWO_HELPERS_INDEPENDENT_PANES_WHILE_ONE_TEST_BLOCKED PASS",
          "healthy_ms",round(elapsed*1000))
    # Actual bounded watchdog deadline, not an immediate unconditional kill.
    deadline=time.monotonic()+0.8
    while blocked.poll() is None and time.monotonic()<deadline:
        time.sleep(.04)
    assert blocked.poll() is None, "test hang unexpectedly returned"
    begin_recovery=time.monotonic()
    assert K.TerminateJobObject(slowjob,0xE017)
    blocked.wait(timeout=4)
    assert blocked.returncode!=0
    assert time.monotonic()-begin_recovery<4
    recovered,_,_=roundtrip(left)
    assert recovered["hr"]==0 and any(
        e["name"]=="OwnedNested" for e in recovered["entries"])
    print("OWNED_JOB_ONLY_TIMEOUT_TERMINATION_AND_FRESH_RESTART PASS")
    # Verify Windows itself reaps the owned child if its private job handle
    # is closed: parent crash must not orphan a stuck extension process.
    abandoned=launch("--test-block",
          extra_env={"FLY_M16_OWNED_TEST_ONLY":"YES"})
    abandoned_job=job_for(abandoned)
    time.sleep(.15)
    assert abandoned.poll() is None
    JOBS.remove(abandoned_job)
    close_started=time.monotonic()
    assert K.CloseHandle(abandoned_job)
    abandoned.wait(timeout=4)
    # KILL_ON_JOB_CLOSE may use exit status 0: verify that a 30-second
    # synthetic block was reaped in <4s, not a specific exit code.
    assert time.monotonic()-close_started<4
    assert abandoned.returncode!=42
    print("OWNED_JOB_KILL_ON_CLOSE_AUTOMATIC_RECLAMATION PASS")
finally:
    # Fail-closed: only handles of helpers THIS harness started. Never
    # enumerate or terminate Windows Explorer / another user's product.
    for child in CHILDREN:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
        if child.stdin:child.stdin.close()
        if child.stdout:child.stdout.close()
    for handle in JOBS:
        K.CloseHandle(handle)
    assert_legacy_profile_unchanged(REAL_CONF,original)
    same=True
    print("LEGACY_USER_PROFILE_SENTINEL_UNCHANGED",True,"PRESENT",present_count(original))
    if OWNED.parent==LOGROOT and OWNED.name.startswith("m16-process-owned-"):
        shutil.rmtree(OWNED)
    print("OWNED_M16_FIXTURES_AND_PROCESSES_CLEANED",True)
    assert same
