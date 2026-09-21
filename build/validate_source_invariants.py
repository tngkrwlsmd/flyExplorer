#!/usr/bin/env python3
"""Fast source-level preflight checks for flyExplorer.

This guard intentionally covers cheap, deterministic invariants that should fail
before GYP generation or a Visual Studio build. It does not replace compilation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FXFILE_SRC = ROOT / "src" / "fxfile"

# Project-wide helpers that are not guaranteed by stdafx.h must be included
# directly by each translation unit that uses them. Add future cross-cutting
# dependencies here instead of relying on accidental transitive includes.
DIRECT_HEADER_RULES = (
    {
        "name": "ModernUI",
        "tokens": re.compile(r"\bui::(?:ModernUI|ThemePalette)\b|\bWM_DPICHANGED\b"),
        "required_header_basename": "ModernUI.h",
    },
)

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^">]+)[">]', re.MULTILINE)
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)


def strip_comments(text: str) -> str:
    return LINE_COMMENT_RE.sub("", BLOCK_COMMENT_RE.sub("", text))


def direct_include_basenames(text: str) -> set[str]:
    return {Path(match).name for match in INCLUDE_RE.findall(text)}


def validate_translation_units() -> list[str]:
    errors: list[str] = []

    for path in sorted(FXFILE_SRC.rglob("*.cpp")):
        text = path.read_text(encoding="utf-8", errors="replace")
        code = strip_comments(text)
        includes = direct_include_basenames(text)

        for rule in DIRECT_HEADER_RULES:
            if not rule["tokens"].search(code):
                continue

            required = str(rule["required_header_basename"])
            if required not in includes:
                rel = path.relative_to(ROOT).as_posix()
                errors.append(
                    f"{rel}: uses {rule['name']} symbols but does not directly include {required}"
                )

    return errors


def validate_modern_ui_registration() -> list[str]:
    errors: list[str] = []
    gyp_path = ROOT / "src" / "fxfile" / "fxfile.gyp"
    manifest_path = ROOT / "src" / "fxfile" / "res" / "fxfile.exe.manifest"

    try:
        gyp = gyp_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{gyp_path.relative_to(ROOT)}: cannot read: {exc}"]

    for entry in ("./gui/ModernUI.cpp", "./gui/ModernUI.h"):
        if entry not in gyp:
            errors.append(f"src/fxfile/fxfile.gyp: missing source registration {entry}")

    if "AdditionalManifestFiles" not in gyp or "./res/fxfile.exe.manifest" not in gyp:
        errors.append(
            "src/fxfile/fxfile.gyp: Modern UI manifest is not registered with VCManifestTool"
        )

    try:
        manifest = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{manifest_path.relative_to(ROOT)}: cannot read: {exc}")
    else:
        if "PerMonitorV2, PerMonitor" not in manifest:
            errors.append(
                "src/fxfile/res/fxfile.exe.manifest: Per-Monitor V2 DPI awareness is missing"
            )

    return errors


def main() -> int:
    errors = validate_translation_units()
    errors.extend(validate_modern_ui_registration())

    if errors:
        print("Source invariant preflight: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Source invariant preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
