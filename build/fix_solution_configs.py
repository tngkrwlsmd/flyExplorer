#!/usr/bin/env python3
"""Fix Visual Studio solution/project settings for fxfile's modern build."""

from __future__ import annotations

import codecs
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

WIN32_HELPER_PROJECTS = {
    r"src\fxfile-upchecker\fxfile-upchecker.vcxproj",
    r"src\fxfile-launcher\fxfile-launcher.vcxproj",
    r"src\fxfile-keyhook\fxfile-keyhook.vcxproj",
}
MFC_PROJECTS = {
    r"src\fxfile\fxfile.vcxproj",
    r"src\fxfile-launcher\fxfile-launcher.vcxproj",
    r"src\fxfile-upchecker\fxfile-upchecker.vcxproj",
}
UPCHECKER_PROJECT = r"src\fxfile-upchecker\fxfile-upchecker.vcxproj"
XPR_PROJECT = r"src\xpr\xpr.vcxproj"
AGGREGATE_PROJECT = r"fxfile.vcxproj"

XPR_TARGET_NAMES = {
    "debug-x86-unicode": "libxprw_dbg",
    "release-x86-unicode": "libxprw",
    "debug-x86-multibyte": "libxpr_dbg",
    "release-x86-multibyte": "libxpr",
    "debug-x64-unicode": "libxprw_dbg",
    "release-x64-unicode": "libxprw",
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


def is_x64_configuration(solution_configuration: str) -> bool:
    return "|x64" in solution_configuration.lower()


def qualify(tag: str, namespace: str) -> str:
    return f"{{{namespace}}}{tag}" if namespace else tag


def set_xpr_target_names(project_path: Path) -> int:
    if not project_path.is_file():
        raise FileNotFoundError(project_path)

    tree = ET.parse(project_path)
    root = tree.getroot()

    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag[1:].split("}", 1)[0]
        ET.register_namespace("", namespace)

    configurations: list[tuple[str, str]] = []
    for item_group in root.findall(qualify("ItemGroup", namespace)):
        if item_group.get("Label") != "ProjectConfigurations":
            continue

        for project_configuration in item_group.findall(
            qualify("ProjectConfiguration", namespace)
        ):
            include = project_configuration.get("Include", "")
            if "|" not in include:
                continue
            configuration, platform = include.split("|", 1)
            if configuration.lower() in XPR_TARGET_NAMES:
                configurations.append((configuration, platform))

    seen = {configuration.lower() for configuration, _ in configurations}
    missing = sorted(set(XPR_TARGET_NAMES) - seen)
    if missing:
        raise ValueError(
            "Missing xpr project configurations: " + ", ".join(missing)
        )

    insert_at = len(root)
    for index, element in enumerate(list(root)):
        if element.tag != qualify("Import", namespace):
            continue
        project = element.get("Project", "")
        if "Microsoft.Cpp.targets" in project:
            insert_at = index
            break

    changed = 0
    for configuration, platform in configurations:
        property_group = ET.Element(
            qualify("PropertyGroup", namespace),
            {
                "Condition": (
                    f"'$(Configuration)|$(Platform)'=="
                    f"'{configuration}|{platform}'"
                )
            },
        )
        target_name = ET.SubElement(
            property_group, qualify("TargetName", namespace)
        )
        target_name.text = XPR_TARGET_NAMES[configuration.lower()]
        root.insert(insert_at + changed, property_group)
        changed += 1

    tree.write(project_path, encoding="utf-8", xml_declaration=True)
    return changed

def set_static_mfc(project_path: Path) -> int:
    if not project_path.is_file():
        raise FileNotFoundError(project_path)

    tree = ET.parse(project_path)
    root = tree.getroot()

    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag[1:].split("}", 1)[0]
        ET.register_namespace("", namespace)

    changed = 0
    for group in root.findall(qualify("PropertyGroup", namespace)):
        if group.get("Label") != "Configuration":
            continue

        use_of_mfc = group.find(qualify("UseOfMfc", namespace))
        if use_of_mfc is None:
            use_of_mfc = ET.Element(qualify("UseOfMfc", namespace))
            use_of_mfc.text = "Static"

            configuration_type = group.find(qualify("ConfigurationType", namespace))
            if configuration_type is not None:
                index = list(group).index(configuration_type) + 1
                group.insert(index, use_of_mfc)
            else:
                group.append(use_of_mfc)
            changed += 1
        elif use_of_mfc.text != "Static":
            use_of_mfc.text = "Static"
            changed += 1

    tree.write(project_path, encoding="utf-8", xml_declaration=True)
    return changed


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
    mfc_paths = {normalize_project_path(path) for path in MFC_PROJECTS}
    upchecker_path = normalize_project_path(UPCHECKER_PROJECT)
    xpr_path = normalize_project_path(XPR_PROJECT)
    aggregate_path = normalize_project_path(AGGREGATE_PROJECT)

    project_guids: dict[str, str] = {}
    project_paths: dict[str, str] = {}
    for line in lines:
        match = PROJECT_RE.match(line.rstrip("\r\n"))
        if match:
            normalized = normalize_project_path(match.group(1))
            project_guids[normalized] = match.group(2).upper()
            project_paths[normalized] = match.group(1)

    missing = sorted((helper_paths | mfc_paths | {xpr_path, aggregate_path}) - set(project_guids))
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

    mfc_changed = 0
    for normalized in sorted(mfc_paths):
        relative = Path(project_paths[normalized].replace("\\", "/"))
        project_path = solution_path.parent / relative
        try:
            mfc_changed += set_static_mfc(project_path)
        except (OSError, ET.ParseError) as error:
            print(f"ERROR: Failed to patch MFC project {project_path}: {error}", file=sys.stderr)
            return 1

    xpr_relative = Path(project_paths[xpr_path].replace("\\", "/"))
    xpr_project_path = solution_path.parent / xpr_relative
    try:
        xpr_changed = set_xpr_target_names(xpr_project_path)
    except (OSError, ET.ParseError, ValueError) as error:
        print(f"ERROR: Failed to patch xpr target names in {xpr_project_path}: {error}", file=sys.stderr)
        return 1

    print("Mapped Win32 helper projects inside the mixed-architecture solution:")
    for path in sorted(WIN32_HELPER_PROJECTS):
        print(f"  {path}")
    print(f"Updated {mapped_count} helper configuration mappings.")
    print(f"Skipped {skipped_upchecker} x64 updater build mappings.")
    print(f"Skipped {skipped_aggregate} aggregate-project build mappings.")
    print(f"Applied static MFC settings to {len(MFC_PROJECTS)} projects ({mfc_changed} configurations updated).")
    print(f"Aligned xpr TargetName values with linker outputs ({xpr_changed} configurations updated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
