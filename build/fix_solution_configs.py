#!/usr/bin/env python3
"""Fix Visual Studio solution mappings for fxfile's mixed-architecture build."""

from __future__ import annotations

import codecs
import re
import sys
from pathlib import Path

WIN32_HELPER_PROJECTS = {
    r"src\fxfile-upchecker\fxfile-upchecker.vcxproj",
    r"src\fxfile-launcher\fxfile-launcher.vcxproj",
    r"src\fxfile-keyhook\fxfile-keyhook.vcxproj",
}
UPCHECKER_PROJECT = r"src\fxfile-upchecker\fxfile-upchecker.vcxproj"
AGGREGATE_PROJECT = r"fxfile.vcxproj"

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


def is_x64_configuration(solution_configuration: str) -> bool:
    return "|x64" in solution_configuration.lower()


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

    helper_paths = {normalize_project_path(path) for path in WIN32_HELPER_PROJECTS}
    upchecker_path = normalize_project_path(UPCHECKER_PROJECT)
    aggregate_path = normalize_project_path(AGGREGATE_PROJECT)

    project_guids: dict[str, str] = {}
    for line in lines:
        match = PROJECT_RE.match(line.rstrip("\r\n"))
        if match:
            project_guids[normalize_project_path(match.group(1))] = match.group(2).upper()

    missing = sorted((helper_paths | {aggregate_path}) - set(project_guids))
    if missing:
        print("ERROR: Expected projects were not found in the solution:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    helper_guids = {project_guids[path] for path in helper_paths}
    upchecker_guid = project_guids[upchecker_path]
    aggregate_guid = project_guids[aggregate_path]

    patched_lines: list[str] = []
    mapped_count = 0
    skipped_upchecker = 0
    skipped_aggregate = 0

    for line in lines:
        match = CONFIG_RE.match(line)
        if not match:
            patched_lines.append(line)
            continue

        guid = match.group(2).upper()
        solution_configuration = match.group(3)
        entry_type = match.group(4)

        # The root fxfile.vcxproj is only an umbrella project. Individual
        # projects are already present in the solution, so building the
        # umbrella again only duplicates dependency traversal.
        if guid == aggregate_guid and entry_type == "Build.0":
            skipped_aggregate += 1
            continue

        if guid in helper_guids:
            # The updater links against the x86 multibyte xpr import library.
            # A single solution configuration cannot build xpr as x64 and x86
            # at the same time, so defer the updater during x64 builds. It is
            # built by Release/Debug-x86-Multibyte configurations instead.
            if (
                guid == upchecker_guid
                and entry_type == "Build.0"
                and is_x64_configuration(solution_configuration)
            ):
                skipped_upchecker += 1
                continue

            mapped = helper_configuration(solution_configuration)
            if mapped:
                newline = match.group(6) or ""
                line = (
                    f"{match.group(1)}{match.group(2)}.{solution_configuration}."
                    f"{entry_type} = {mapped}{newline}"
                )
                mapped_count += 1

        patched_lines.append(line)

    if mapped_count == 0:
        print("ERROR: No helper project configuration mappings were found to patch.", file=sys.stderr)
        return 1

    output = "".join(patched_lines).encode("utf-8")
    if has_bom:
        output = codecs.BOM_UTF8 + output
    solution_path.write_bytes(output)

    print("Mapped Win32 helper projects inside the mixed-architecture solution:")
    for path in sorted(WIN32_HELPER_PROJECTS):
        print(f"  {path}")
    print(f"Updated {mapped_count} helper configuration mappings.")
    print(f"Skipped {skipped_upchecker} x64 updater build mappings.")
    print(f"Skipped {skipped_aggregate} aggregate-project build mappings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
