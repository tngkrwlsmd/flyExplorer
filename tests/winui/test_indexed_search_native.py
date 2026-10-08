"""Read-only native Windows Search helper acceptance against indexed system item."""
import argparse
import hashlib
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
    command=[str(helper),"--indexed-filename-search",str(scope),"Microsoft Edge"]
    result=subprocess.run(command,capture_output=True,timeout=20)
    assert result.returncode==0,(result.returncode,result.stderr[-400:])
    assert len(result.stdout)>=24,("indexed reply missing",len(result.stdout))
    magic,version,status,count,size,checksum=struct.unpack_from("<6I",result.stdout)
    assert (magic,version)==(MAGIC,1),(hex(magic),version)
    assert status==0,("SystemIndex provider query failed",status)
    body=result.stdout[24:]
    assert len(body)==size and wire_checksum(body)==checksum
    assert 1<=count<=1000,count
    names=[]
    cursor=0
    for _ in range(count):
        assert cursor+4<=len(body)
        units=struct.unpack_from("<I",body,cursor)[0];cursor+=4
        assert 0<units<=2048 and cursor+2*units<=len(body)
        names.append(body[cursor:cursor+2*units].decode("utf-16-le"))
        cursor+=2*units
    assert cursor==len(body)
    assert str(sample).casefold() in {x.casefold() for x in names},names[:4]
    assert hashlib.sha256(sample.read_bytes()).digest()==original
    print("INDEXED_NATIVE_SYSTEMINDEX_QUERY_PASS",True,flush=True)
    print("INDEXED_NATIVE_SYSTEM_SOURCE_UNCHANGED",True,flush=True)

if __name__=="__main__":
    main()
