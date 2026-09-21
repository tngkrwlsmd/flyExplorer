#!/usr/bin/env python3
"""Fix Visual Studio solution mappings for fxfile's Win32-only helper projects."""

from __future__ import annotations

import codecs
import re
import sys
from pathlib import Path

HELPER_PROJECTS = {
    r"src\fxfile-upchecker\fxfile-upchecker.vcxproj",
    r"src\fxfile-launcher\fxfile-launcher.vcxproj",
    r"src\fxfile-keyhook\fxfile-keyhook.vcxproj",
}

PROJECT_RE = re.compile(
    r'^Project\("[^"]+"\)\s*=\s*"[^"]+",\s*"([^"]+)",\s*"(\{[0-9A-Fa-f-]+\})"\s*$'
)
CONFIG_RE = re.compile(
    r'^(\s*)(\{[0-9A-Fa-f-]+\})\.([^=]+?)\.(ActiveCfg|Build\.0)\s*=\s*(.+?)(\r?\n)?$'
)


def normalize_project_path(value: str) -> str:
    return value.replace("/", "\\").lower()


def helper_configuration(solution_configuration: str) -> str | None:
    name = solution_configuration.strip().lower()
    if name.startswith("debug"):
        return "Debug-x86|Win32"
    if name.startswith("release"):
        return "Release-x86|Win32"
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: fix_solution_configs.py <solution.sln>", file=sys.stderr)
        return 2

    solution_path = Path(sys.argv[1])
    if not solution_path.is_file():
        print(f"ERROR: Solution not found: {solution_path}", file=sys.stderr)
        return 1

    raw = solution_path.read_bytes()
    has_bom = raw.startswith(codecs.BOM_UTF8)
    text = raw.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)

    expected_paths = {normalize_project_path(path) for path in HELPER_PROJECTS}
    helper_guids: dict[str, str] = {}

    for line in lines:
        match = PROJECT_RE.match(line.rstrip("\r\n"))
        if not match:
            continue

        project_path = normalize_project_path(match.group(1))
        if project_path in expected_paths:
            helper_guids[match.group(2).upper()] = match.group(1)

    found_paths = {normalize_project_path(path) for path in helper_guids.values()}
    missing = sorted(expected_paths - found_paths)
    if missing:
        print("ERROR: Expected Win32 helper projects were not found in the solution:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    patched_lines: list[str] = []
    patched_count = 0

    for line in lines:
        match = CONFIG_RE.match(line)
        if match and match.group(2).upper() in helper_guids:
            mapped = helper_configuration(match.group(3))
            if mapped:
                newline = match.group(6) or ""
                line = (
                    f"{match.group(1)}{match.group(2)}.{match.group(3)}."
                    f"{match.group(4)} = {mapped}{newline}"
                )
                patched_count += 1

        patched_lines.append(line)

    if patched_count == 0:
        print("ERROR: No helper project configuration mappings were found to patch.", file=sys.stderr)
        return 1

    output = "".join(patched_lines).encode("utf-8")
    if has_bom:
        output = codecs.BOM_UTF8 + output
    solution_path.write_bytes(output)

    print("Mapped Win32-only helper projects inside the mixed x64 solution:")
    for path in sorted(helper_guids.values()):
        print(f"  {path}")
    print(f"Updated {patched_count} solution configuration mappings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
