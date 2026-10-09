"""Read-only native Windows Search helper acceptance against indexed system item."""
import argparse
import hashlib
from datetime import datetime, timedelta
import os
from pathlib import Path
import struct
import subprocess

from paths import app_exe

MAGIC=0x33585346
def wire_checksum(value):
    total=2166136261
    for byte in value:
        total=((total^byte)*16777619)&0xffffffff
    return total

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--configuration",choices=("Debug","Release"),default="Release")
    args=parser.parse_args()
    helper=app_exe(args.configuration).resolve().with_name("FlyShellIsolationHelper.exe")
    assert helper.is_file(),helper
    scope=Path(os.environ["PUBLIC"])/"Desktop"
    sample=scope/"Microsoft Edge.lnk"
    assert sample.is_file(),("public index sample unavailable",sample)
    original=hashlib.sha256(sample.read_bytes()).digest()
    def indexed(extension=None, min_kb=None, max_kb=None, after=None, before=None):
        command=[str(helper),"--indexed-filename-search",
                 str(scope),"Microsoft Edge"]
        if after is not None or before is not None:
            command.extend((extension or "",
                            str(min_kb) if min_kb is not None else "",
                            str(max_kb) if max_kb is not None else "",
                            str(after) if after is not None else "",
                            str(before) if before is not None else ""))
        elif min_kb is not None or max_kb is not None:
            command.extend((extension or "", str(min_kb) if min_kb is not None else "",
                            str(max_kb) if max_kb is not None else ""))
        elif extension is not None:
            command.append(extension)
        result=subprocess.run(command,capture_output=True,timeout=20)
        assert result.returncode==0,(result.returncode,result.stderr[-400:])
        assert len(result.stdout)>=24,("indexed reply missing",len(result.stdout))
        magic,version,status,count,size,checksum=struct.unpack_from("<6I",result.stdout)
        assert (magic,version)==(MAGIC,1),(hex(magic),version)
        assert status==0,("SystemIndex provider query failed",status)
        body=result.stdout[24:]
        assert len(body)==size and wire_checksum(body)==checksum
        assert 0<=count<=1000,count
        names=[]
        cursor=0
        for _ in range(count):
            assert cursor+4<=len(body)
            units=struct.unpack_from("<I",body,cursor)[0];cursor+=4
            assert 0<units<=2048 and cursor+2*units<=len(body)
            names.append(body[cursor:cursor+2*units].decode("utf-16-le"))
            cursor+=2*units
        assert cursor==len(body)
        return names

    unfiltered=indexed()
    assert str(sample).casefold() in {x.casefold() for x in unfiltered}
    print("INDEXED_NATIVE_SYSTEMINDEX_QUERY_PASS",True,flush=True)
    matching=indexed(".LNK")
    assert str(sample).casefold() in {x.casefold() for x in matching}
    assert all(p.casefold().endswith(".lnk") for p in matching)
    excluded=indexed("txt")
    assert str(sample).casefold() not in {x.casefold() for x in excluded}
    assert all(p.casefold().endswith(".txt") for p in excluded)
    print("INDEXED_NATIVE_EXTENSION_MATCH_AND_EXCLUDE_PASS",True,flush=True)
    # The actual index entry must survive the inclusive signed System.Size
    # predicate, and the exact same indexed filename must disappear above
    # its read-only filesystem size. No index reconfiguration or fixture copy.
    sample_bytes=sample.stat().st_size
    upper=(sample_bytes+1023)//1024
    matches=indexed(".LNK", min_kb=0, max_kb=upper)
    assert str(sample).casefold() in {x.casefold() for x in matches}
    excluded_size=indexed(".LNK", min_kb=upper+1)
    assert str(sample).casefold() not in {x.casefold() for x in excluded_size}
    print("INDEXED_NATIVE_SIZE_MATCH_AND_EXCLUDE_PASS",True,flush=True)
    # A helper invocation with bad numeric arguments must fail before a
    # query is dispatched (in contrast to a legitimate empty result).
    for lower,upper_arg in (("1x", ""), ("20", "10"),
                            ("9007199254740992", "")):
        cmd=[str(helper),"--indexed-filename-search",
             str(scope),"Microsoft Edge",".LNK",lower,upper_arg]
        invalid=subprocess.run(cmd,capture_output=True,timeout=5)
        assert invalid.returncode!=0,(lower,upper_arg,invalid.returncode)
    print("INDEXED_NATIVE_SIZE_INVALID_ARGS_REJECTED_PASS",True,flush=True)
    # Exercise exact inclusive local-day bounds on the already-indexed
    # public shortcut. Never alter the system source or index service.
    source_mtime=sample.stat().st_mtime_ns
    local_day=datetime.fromtimestamp(sample.stat().st_mtime).date()
    same=local_day.isoformat()
    following=(local_day+timedelta(days=1)).isoformat()
    previous=(local_day-timedelta(days=1)).isoformat()
    included=indexed(".LNK", min_kb=0, max_kb=upper, after=same, before=same)
    assert str(sample).casefold() in {x.casefold() for x in included},(
        "actual indexed file not found within its inclusive local date")
    after_excluded=indexed(".LNK", after=following)
    before_excluded=indexed(".LNK", before=previous)
    assert str(sample).casefold() not in {x.casefold() for x in after_excluded}
    assert str(sample).casefold() not in {x.casefold() for x in before_excluded}
    print("INDEXED_NATIVE_DATE_INCLUSIVE_AND_EXCLUDES_PASS",True,flush=True)
    for start,end in (("2025-02-29",""), ("2026/01/01",""),
                      ("2026-04-01","2026-03-31"),
                      ("1600-12-31","")):
        args=[str(helper),"--indexed-filename-search",
              str(scope),"Microsoft Edge",".LNK","","",start,end]
        rejected=subprocess.run(args,capture_output=True,timeout=5)
        assert rejected.returncode!=0,(start,end,rejected.returncode)
    print("INDEXED_NATIVE_DATE_INVALID_ARGS_REJECTED_PASS",True,flush=True)
    assert sample.stat().st_mtime_ns==source_mtime
    assert hashlib.sha256(sample.read_bytes()).digest()==original
    print("INDEXED_NATIVE_SYSTEM_SOURCE_UNCHANGED",True,flush=True)

if __name__=="__main__":
    main()
