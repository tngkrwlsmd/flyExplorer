"""Resolve and validate the canonical flyExplorer Windows C++ toolchain.

Supported full builds use Visual Studio 18.x, MSVC v145 x64 tools, and
Windows SDK 10.0.26100.0. VS 2022/v143 is not a validated full-build target.
App builds additionally pass --winui to validate Windows Store C++ imports;
helper/native builds only require the desktop toolchain.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

REQUIRED_MSBUILD_MAJOR = 18
REQUIRED_TOOLSET = "v145"
REQUIRED_VCTOOLS_PREFIX = "14.5"
REQUIRED_SDK = "10.0.26100.0"


def existing(path: str | Path) -> Path | None:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_file() else None


def vswhere_path() -> Path | None:
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    candidate = Path(pf86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    return candidate if candidate.is_file() else None
def candidate_msbuilds() -> list[Path]:
    override = os.environ.get("MSBUILD")
    if override:
        found = existing(override)
        if found is None:
            raise RuntimeError(f"MSBUILD override does not exist: {override}")
        return [found]

    candidates: list[Path] = []
    vswhere = vswhere_path()
    if vswhere is not None:
        result = subprocess.run(
            [str(vswhere), "-latest", "-products", "*", "-requires",
             "Microsoft.Component.MSBuild",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
             "-find", r"MSBuild\**\Bin\MSBuild.exe"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in result.stdout.splitlines():
            if found := existing(line.strip()):
                candidates.append(found)

    if on_path := shutil.which("MSBuild.exe"):
        if found := existing(on_path):
            candidates.append(found)

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique
def installation_root(msbuild: Path) -> Path | None:
    for parent in (msbuild.parent, *msbuild.parents):
        if (parent / "VC" / "Tools" / "MSVC").is_dir() and (parent / "MSBuild").is_dir():
            return parent
    return None


def msbuild_major(msbuild: Path) -> int | None:
    result = subprocess.run(
        [str(msbuild), "-nologo", "-version"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        token = line.strip().split(".", 1)[0]
        if token.isdigit():
            return int(token)
    return None


def winui_target_errors(toolsets: list[Path]) -> list[str]:
    # MSBuild resolves Store imports separately from desktop C++ toolsets.
    # A desktop-only installation otherwise falls through to TargetPlatformVersion
    # 7.0 and reports a misleading missing-SDK error in CppWinRTVerifyKitVersion.
    required = (
        "Default.props",
        "Platforms/x64/Platform.Default.props",
        "Platforms/x64/Platform.props",
        "Platforms/x64/Platform.targets",
        f"Platforms/x64/PlatformToolsets/{REQUIRED_TOOLSET}/Toolset.props",
        f"Platforms/x64/PlatformToolsets/{REQUIRED_TOOLSET}/Toolset.targets",
    )
    for toolset in toolsets:
        store = toolset.parents[4] / "Application Type" / "Windows Store" / "10.0"
        if all((store / relative).is_file() for relative in required):
            return []
    return [
        "Windows Store C++ x64 targets for MSVC v145 are missing or incomplete. "
        "In Visual Studio Installer, add C++ Universal Windows Platform tools "
        "(Microsoft.VisualStudio.ComponentGroup.UWP.VC) to the selected "
        "Visual Studio 18.x installation; the Windows SDK alone is insufficient."
    ]


def validation_errors(msbuild: Path, *, winui: bool = False) -> list[str]:
    install = installation_root(msbuild)
    if install is None:
        return [f"cannot determine Visual Studio installation root from {msbuild}"]

    errors: list[str] = []
    major = msbuild_major(msbuild)
    if major != REQUIRED_MSBUILD_MAJOR:
        errors.append(
            f"MSBuild major version {major!r} is not supported; "
            f"flyExplorer canonical full builds require Visual Studio/MSBuild "
            f"{REQUIRED_MSBUILD_MAJOR}.x")
    toolsets = list((install / "MSBuild" / "Microsoft" / "VC").glob(
        f"v*/Platforms/x64/PlatformToolsets/{REQUIRED_TOOLSET}/Toolset.props"))
    if not toolsets:
        errors.append(f"MSVC platform toolset {REQUIRED_TOOLSET} is missing under {install}")

    if winui:
        errors.extend(winui_target_errors(toolsets))

    version_file = install / "VC" / "Auxiliary" / "Build" / "Microsoft.VCToolsVersion.default.txt"
    if not version_file.is_file():
        errors.append(f"default MSVC tools version file is missing: {version_file}")
    else:
        version = version_file.read_text(encoding="utf-8", errors="replace").strip()
        if not version.startswith(REQUIRED_VCTOOLS_PREFIX):
            errors.append(
                f"default MSVC tools version {version!r} is not {REQUIRED_TOOLSET} "
                f"({REQUIRED_VCTOOLS_PREFIX}x)")
        compiler = (install / "VC" / "Tools" / "MSVC" / version /
                    "bin" / "Hostx64" / "x64" / "cl.exe")
        if not compiler.is_file():
            errors.append(f"x64 C++ compiler is missing: {compiler}")

    pf86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    kits = pf86 / "Windows Kits" / "10"
    sdk_files = (
        kits / "Include" / REQUIRED_SDK / "um" / "Windows.h",
        kits / "Lib" / REQUIRED_SDK / "um" / "x64" / "kernel32.lib",
        kits / "bin" / REQUIRED_SDK / "x64" / "rc.exe",
    )
    for path in sdk_files:
        if not path.is_file():
            errors.append(f"Windows SDK {REQUIRED_SDK} component is missing: {path}")
    return errors


def resolve(*, winui: bool = False) -> Path | None:
    candidates = candidate_msbuilds()
    if not candidates:
        return None
    diagnostics: list[str] = []
    for candidate in candidates:
        errors = validation_errors(candidate, winui=winui)
        if not errors:
            return candidate
        diagnostics.extend(errors)
    if diagnostics:
        raise RuntimeError("; ".join(dict.fromkeys(diagnostics)))
    return None
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--winui", action="store_true",
        help="also require the Windows Store C++ x64 targets used by the WinUI app")
    args = parser.parse_args()
    try:
        path = resolve(winui=args.winui)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if path is None:
        print(
            "ERROR: compatible MSBuild not found. Install Visual Studio 18.x "
            "with MSVC v145 x64 tools and Windows SDK 10.0.26100.0, or set "
            "MSBUILD to that installation's MSBuild.exe.",
            file=sys.stderr)
        return 3

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
