"""Side-effect-free bounded Shell navigation wire client for owned probes."""
import struct

MAGIC=0x314C5346

def request(path=None,pidl_bytes=None,offset=0,limit=1024):
    assert 0<=offset<100000 and 1<=limit<=1024 and offset+limit<=100000
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
