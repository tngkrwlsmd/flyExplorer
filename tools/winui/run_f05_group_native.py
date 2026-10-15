"""Compile/run all F05 projection and per-tab probes without user files or GUI.

Example: python tools/winui/run_f05_group_native.py
Creates only ignored out/f05-native artifacts inside this source checkout.
On Windows requires the repository's supported VS developer shell (cl.exe).
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    ROOT / "tests/winui/native_f05_group_projection.cpp",
    ROOT / "tests/winui/native_f05_group_presentation.cpp",
    ROOT / "tests/winui/native_f05_group_modes.cpp",
    ROOT / "tests/winui/native_f05_group_tab_cache.cpp",
)


def run():
    compiler = shutil.which("cl.exe" if os.name == "nt" else "g++")
    if compiler is None:
        raise RuntimeError("F05_NATIVE_COMPILER_UNAVAILABLE")
    output = ROOT / "out/f05-native"
    # Refuse an unexpected pre-existing redirected output path.
    if output.is_symlink() or ROOT.is_symlink():
        raise RuntimeError("F05_NATIVE_UNOWNED_OUTPUT")
    output.mkdir(parents=True, exist_ok=True)
    for source in SOURCES:
        if not source.is_file():
            raise RuntimeError("F05_NATIVE_SOURCE_MISSING: " + source.name)
        target = output / (source.stem + (".exe" if os.name == "nt" else ""))
        if target.is_symlink():
            raise RuntimeError("F05_NATIVE_OUTPUT_LINK_REFUSED: " + target.name)
        if os.name == "nt":
            args = [compiler, "/nologo", "/std:c++17", "/utf-8", "/W4", "/WX",
                    "/EHsc", str(source), "/Fe:" + str(target)]
        else:
            args = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-O2", str(source), "-o", str(target)]
        subprocess.run(args, cwd=output, check=True, timeout=90)
        subprocess.run([str(target)], cwd=output, check=True, timeout=20)
    print("F05_NATIVE_ALL_FOUR_GROUP_AND_TAB_PROBES=PASS", flush=True)


if __name__ == "__main__":
    try:
        run()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print("F05_NATIVE_GROUPING=FAIL", str(exc), file=sys.stderr)
        raise SystemExit(1)
