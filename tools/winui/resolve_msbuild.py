"""Resolve MSBuild without assuming one Visual Studio edition/install path."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys


def existing(path: str | Path) -> Path | None:
    candidate = Path(path)
    return candidate if candidate.is_file() else None


def resolve() -> Path | None:
    override = os.environ.get("MSBUILD")
    if override and (found := existing(override)):
        return found
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = Path(pf86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if vswhere.is_file():
        result = subprocess.run(
            [str(vswhere), "-latest", "-products", "*", "-requires",
             "Microsoft.Component.MSBuild", "-find", r"MSBuild\**\Bin\MSBuild.exe"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        for line in result.stdout.splitlines():
            if found := existing(line.strip()):
                return found
    fallback = Path(r"C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe")
    return existing(fallback)


def main() -> int:
    path = resolve()
    if path is None:
        print("ERROR: MSBuild not found via MSBUILD override, vswhere, or validated fallback", file=sys.stderr)
        return 3
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
