from __future__ import annotations
import argparse
import ctypes
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app"/"winui"
OUT=ROOT/"out"
MSBUILD_RESOLVER=ROOT/"tools"/"winui"/"resolve_msbuild.py"
SETUP_PROJECT_TEMPLATE=ROOT/"packaging"/"installer"/"flyExplorerSetup.project-template.xml"
SETUP_PROJECT=ROOT/"packaging"/"installer"/"flyExplorerSetup.vcxproj"
PROVENANCE_MODULE=ROOT/"packaging"/"provenance.py"

_provenance_spec=importlib.util.spec_from_file_location(
    "flyexplorer_payload_provenance",PROVENANCE_MODULE)
if _provenance_spec is None or _provenance_spec.loader is None:
    raise RuntimeError("cannot load packaging/provenance.py")
payload_provenance=importlib.util.module_from_spec(_provenance_spec)
_provenance_spec.loader.exec_module(payload_provenance)

REQUIRED_TOP=(
    "flyExplorer.exe",
    "flyExplorer.pri",
    "FlyExplorer.winmd",
    "FlyShellIsolationHelper.exe",
    "App.xbf",
    "FileToolbar.xbf",
    "MainWindow.xbf",
    "NavigationSidebar.xbf",
    "ShellHeader.xbf",
    "StatusFooter.xbf",
    "Microsoft.Web.WebView2.Core.dll",
    "Microsoft.Web.WebView2.Core.winmd",
    "Microsoft.WindowsAppRuntime.Bootstrap.dll",
)

DISTRIBUTION_ROOT=ROOT/"packaging"/"licenses"

def distribution_sources() -> list[tuple[Path,Path]]:
    pairs=[
        (ROOT/"LICENSE", Path("licenses/flyExplorer-LICENSE.txt")),
        (ROOT/"CREDITS", Path("licenses/THIRD_PARTY-NOTICES.txt")),
    ]
    if not DISTRIBUTION_ROOT.is_dir():
        fail(f"distribution license directory missing: {DISTRIBUTION_ROOT}")
    for source_path in sorted(DISTRIBUTION_ROOT.rglob("*")):
        if source_path.is_file():
            pairs.append((source_path,Path("licenses")/source_path.relative_to(DISTRIBUTION_ROOT)))
    return pairs

def fail(message: str) -> None:
    raise SystemExit("ERROR: "+message)

def product_version() -> str:
    text=(APP/"product_version.h").read_text(encoding="utf-8")
    m=re.search(r'#define\s+FLYEXPLORER_VERSION_STRING\s+"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"',text)
    if not m:
        fail("product version is missing or malformed")
    return m.group(1)

def collect_payload(configuration: str) -> list[tuple[Path,Path]]:
    source=OUT/"winui"/configuration
    if not source.is_dir():
        fail(f"build output missing: {source}; run build.bat {configuration}")
    for name in REQUIRED_TOP:
        path=source/name
        if not path.is_file():
            fail(f"required runtime file missing: {path}")
    if not (source/"Assets").is_dir():
        fail("Assets directory missing from runtime output")
    bad_suffix={".pdb",".obj",".lib",".exp",".ilk",".py",".cpp",".h"}
    pairs=[]
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        rel=path.relative_to(source)
        if rel.suffix.lower() in bad_suffix:
            fail(f"non-runtime file leaked into Release output: {rel}")
        lower=rel.as_posix().lower()
        for token in ("flyexplorerwinuishell","phase5","islandbridge","legacy/mfc"):
            if token in lower:
                fail(f"retired artifact selected: {rel}")
        pairs.append((path,rel))
    if len(pairs)<20:
        fail("runtime payload is unexpectedly incomplete")
    for source_path,rel in distribution_sources():
        if not source_path.is_file():
            fail(f"required distribution notice missing: {source_path}")
        pairs.append((source_path,rel))
    return pairs

class WindowsPayloadCompression:
    """XPRESS_HUFF buffer-mode resources using Windows' built-in Cabinet API.

    Compression is on installer resources only. The staged runtime, its
    NuGet provenance, and the files extracted at install time remain
    byte-for-byte identical to the verified Release payload.
    """
    ALGORITHM=4  # COMPRESS_ALGORITHM_XPRESS_HUFF
    INSUFFICIENT_BUFFER=122

    def __init__(self):
        if sys.platform!="win32":
            fail("Windows Cabinet compression is required for setup packaging")
        self.api=ctypes.WinDLL("Cabinet.dll",use_last_error=True)
        self._declare("CreateCompressor",
                      [ctypes.c_uint32,ctypes.c_void_p,
                       ctypes.POINTER(ctypes.c_void_p)])
        self._declare("CloseCompressor",[ctypes.c_void_p])
        self._declare("CreateDecompressor",
                      [ctypes.c_uint32,ctypes.c_void_p,
                       ctypes.POINTER(ctypes.c_void_p)])
        self._declare("CloseDecompressor",[ctypes.c_void_p])
        buffer_args=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,
                     ctypes.c_void_p,ctypes.c_size_t,
                     ctypes.POINTER(ctypes.c_size_t)]
        self._declare("Compress",buffer_args)
        self._declare("Decompress",buffer_args)
        self.compressor=ctypes.c_void_p()
        self.decompressor=ctypes.c_void_p()
        if not self.api.CreateCompressor(
            self.ALGORITHM,None,ctypes.byref(self.compressor)):
            fail(f"CreateCompressor failed: {ctypes.get_last_error()}")
        if not self.api.CreateDecompressor(
            self.ALGORITHM,None,ctypes.byref(self.decompressor)):
            self.api.CloseCompressor(self.compressor)
            fail(f"CreateDecompressor failed: {ctypes.get_last_error()}")

    def _declare(self,name,args):
        func=getattr(self.api,name)
        func.argtypes=args
        func.restype=ctypes.c_int

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.api.CloseDecompressor(self.decompressor)
        self.api.CloseCompressor(self.compressor)

    def encode(self,raw:bytes)->bytes:
        if not raw:
            return b""
        source=ctypes.create_string_buffer(raw)
        size=ctypes.c_size_t()
        ok=self.api.Compress(self.compressor,source,len(raw),
                             None,0,ctypes.byref(size))
        if ok or ctypes.get_last_error()!=self.INSUFFICIENT_BUFFER:
            fail(f"Compress size probe failed: {ctypes.get_last_error()}")
        if size.value==0 or size.value>2**32-1:
            fail("invalid compressed payload size")
        compressed=ctypes.create_string_buffer(size.value)
        written=ctypes.c_size_t()
        if not self.api.Compress(
            self.compressor,source,len(raw),compressed,size.value,
            ctypes.byref(written)):
            fail(f"Compress failed: {ctypes.get_last_error()}")
        return compressed.raw[:written.value]

    def decode(self,data:bytes,expected:int)->bytes:
        if not data:
            return b"" if expected==0 else fail("missing compressed data")
        source=ctypes.create_string_buffer(data)
        decoded=ctypes.create_string_buffer(expected)
        written=ctypes.c_size_t()
        if not self.api.Decompress(
            self.decompressor,source,len(data),decoded,expected,
            ctypes.byref(written)):
            fail(f"Decompress failed: {ctypes.get_last_error()}")
        if written.value!=expected:
            fail("decoded payload length mismatch")
        return decoded.raw[:expected]


def generate_payload(stage: Path,obj: Path,pairs: list[tuple[Path,Path]]) -> None:
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    entries=[]
    obj.mkdir(parents=True,exist_ok=True)
    packed_dir=obj/"compressed-resources"
    packed_dir.mkdir(parents=True)
    raw_total=0
    stored_total=0
    with WindowsPayloadCompression() as codec:
        for index,(src,rel) in enumerate(pairs,start=101):
            dst=stage/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            raw=dst.read_bytes()
            raw_size=len(raw)
            if raw_size>2**32-1:
                fail(f"payload exceeds uint32 size: {rel}")
            packed=codec.encode(raw) if raw_size>=128 else b""
            use_compression=bool(packed) and len(packed)+32<raw_size
            if use_compression:
                if codec.decode(packed,raw_size)!=raw:
                    fail(f"compression round-trip mismatch: {rel}")
                resource=packed_dir/f"{index}.bin"
                resource.write_bytes(packed)
                stored_size=len(packed)
            else:
                resource=dst
                stored_size=raw_size
            entries.append((index,rel,raw_size,stored_size,use_compression,resource))
            raw_total+=raw_size
            stored_total+=stored_size
    header=[
        "#pragma once",
        "#include <cstdint>",
        "struct PayloadFileEntry { int resourceId; wchar_t const* relativePath; "
        "std::uint32_t bytes; std::uint32_t storedBytes; bool compressed; };",
        "inline constexpr PayloadFileEntry kPayloadFiles[] = {",
    ]
    for rid,rel,size,stored,compressed,_ in entries:
        rp=rel.as_posix().replace('"','\\"')
        header.append(
            f'    {{{rid}, L"{rp}", {size}u, {stored}u, '
            f'{"true" if compressed else "false"}}},')
    header += [
        "};",
        f"inline constexpr std::uint64_t kPayloadBytes={raw_total}ull;",
        "",
    ]
    (obj/"payload_manifest.h").write_text(
        "\n".join(header),encoding="utf-8",newline="\n")
    rc=[]
    for rid,_,_,_,_,resource in entries:
        path=resource.resolve().as_posix().replace('"','\\"')
        rc.append(f'{rid} RCDATA "{path}"')
    (obj/"payload.rc").write_text(
        "\n".join(rc)+"\n",encoding="utf-8",newline="\n")
    print(f"PAYLOAD_RESOURCE_RAW_BYTES={raw_total}")
    print(f"PAYLOAD_RESOURCE_STORED_BYTES={stored_total}")
    print(f"PAYLOAD_COMPRESSED_FILES={sum(1 for e in entries if e[4])}")


def materialize_setup_project() -> Path:
    if not SETUP_PROJECT_TEMPLATE.is_file():
        fail(f"tracked installer project template missing: {SETUP_PROJECT_TEMPLATE}")
    SETUP_PROJECT.write_text(
        SETUP_PROJECT_TEMPLATE.read_text(encoding="utf-8"),
        encoding="utf-8", newline="\n")
    return SETUP_PROJECT

def resolve_msbuild() -> Path:
    result=subprocess.run([sys.executable,"-X","utf8",str(MSBUILD_RESOLVER)],
                          capture_output=True,text=True,encoding="utf-8")
    path=Path(result.stdout.strip()) if result.returncode==0 else Path()
    if result.returncode or not path.is_file():
        fail(result.stderr.strip() or "MSBuild resolver did not return an existing path")
    return path

def build_setup(obj: Path,package_out: Path) -> Path:
    msbuild=resolve_msbuild()
    setup_project=materialize_setup_project()
    setup=package_out/"flyExplorer-Setup-x64.exe"
    if setup.exists():
        setup.unlink()
    cmd=[
        str(msbuild),str(setup_project),"/nologo","/t:Build",
        "/p:Configuration=Release","/p:Platform=x64",
        f"/p:OutDir={package_out.as_posix()}/",
        f"/p:IntDir={(obj/'build').as_posix()}/",
        f"/p:PayloadRc={(obj/'payload.rc').as_posix()}",
        f"/p:PayloadIncludeDir={obj.as_posix()}",
        "/m:2","/v:minimal",
    ]
    result=subprocess.run(cmd,cwd=ROOT,text=True)
    if result.returncode:
        fail(f"installer build failed with exit {result.returncode}")
    if not setup.is_file() or setup.stat().st_size<100000:
        fail("installer artifact missing or unexpectedly small")
    return setup

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("configuration",nargs="?",default="Release",choices=("Release",))
    args=parser.parse_args()
    try:
        provenance=payload_provenance.verify_snapshot()
    except payload_provenance.ProvenanceError as exc:
        fail(str(exc))

    package_out=OUT/"package"
    package_work=OUT/"obj"/"package"
    if package_out.exists():
        shutil.rmtree(package_out)
    if package_work.exists():
        shutil.rmtree(package_work)
    package_out.mkdir(parents=True)
    stage=package_work/"stage"
    obj=package_work/"build-inputs"
    pairs=collect_payload(args.configuration)
    generate_payload(stage,obj,pairs)
    setup=build_setup(obj,package_out)
    print(f"PRODUCT_VERSION={product_version()}")
    print(f"PAYLOAD_FILES={len(pairs)}")
    print(f"RUNTIME_MANIFEST_SHA256={provenance['runtime_manifest_sha256']}")
    print(f"SETUP={setup}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
