from __future__ import annotations
import argparse
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

def generate_payload(stage: Path,obj: Path,pairs: list[tuple[Path,Path]]) -> None:
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    entries=[]
    for index,(src,rel) in enumerate(pairs,start=101):
        dst=stage/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        entries.append((index,rel,dst.stat().st_size,dst))
    header=[
        "#pragma once",
        "#include <cstdint>",
        "struct PayloadFileEntry { int resourceId; wchar_t const* relativePath; std::uint32_t bytes; };",
        "inline constexpr PayloadFileEntry kPayloadFiles[] = {",
    ]
    for rid,rel,size,_ in entries:
        rp=rel.as_posix().replace('"','\\"')
        header.append(f'    {{{rid}, L"{rp}", {size}u}},')
    header += [
        "};",
        f"inline constexpr std::uint64_t kPayloadBytes={sum(e[2] for e in entries)}ull;",
        "",
    ]
    obj.mkdir(parents=True,exist_ok=True)
    (obj/"payload_manifest.h").write_text("\n".join(header),encoding="utf-8",newline="\n")
    rc=[]
    for rid,_,_,dst in entries:
        path=dst.resolve().as_posix().replace('"','\\"')
        rc.append(f'{rid} RCDATA "{path}"')
    (obj/"payload.rc").write_text("\n".join(rc)+"\n",encoding="utf-8",newline="\n")

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
    print(f"SETUP={setup}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
