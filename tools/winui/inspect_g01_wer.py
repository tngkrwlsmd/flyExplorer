#!/usr/bin/env python3
"""Read-only, privacy-minimized flyExplorer Windows Error Reporting inventory.

Inspect only existing AppCrash_flyExplorer.exe_*/Report.wer files and emit
aggregate crash signatures. Never read dumps, user application files, loaded
module paths, or raw exception descriptions. No WER settings are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re


REPORT_PREFIX = "AppCrash_flyExplorer.exe_"
MAX_REPORT_BYTES = 512 * 1024
MODULE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
HEX_RE = re.compile(r"^[0-9a-fA-F]{1,16}$")
VALUE_RE = re.compile(r"^Sig\[(\d+)\]\.Value=(.*)$")


def parse_report(data: bytes) -> tuple[str, str, str] | None:
    """Return only (module basename, exception code, offset)."""
    if not data or len(data) > MAX_REPORT_BYTES:
        return None
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        contents = data.decode("utf-16", errors="replace")
    elif data[:256].count(b"\x00") > 8:
        contents = data.decode("utf-16-le", errors="replace")
    else:
        contents = data.decode("utf-8-sig", errors="replace")
    fields = {}
    for line in contents.splitlines():
        match = VALUE_RE.match(line)
        if match:
            number, value = match.groups()
            if number in ("0", "3", "6", "7"):
                if number in fields:
                    return None
                fields[number] = value.strip()
    if fields.get("0", "").casefold() != "flyexplorer.exe":
        return None
    module, code, offset = (fields.get(key, "") for key in ("3", "6", "7"))
    if not MODULE_RE.fullmatch(module):
        return None
    if not HEX_RE.fullmatch(code) or len(code) != 8:
        return None
    if not HEX_RE.fullmatch(offset):
        return None
    return module.lower(), "0x" + code.lower(), "0x" + offset.lower().lstrip("0").rjust(1, "0")


def default_roots() -> list[Path]:
    roots = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "Microsoft" / "Windows" / "WER" / "ReportArchive")
    program = os.environ.get("PROGRAMDATA")
    if program:
        roots.append(Path(program) / "Microsoft" / "Windows" / "WER" / "ReportArchive")
    return roots


def inventory(roots: list[Path], max_reports: int = 256) -> dict:
    """Aggregate only the matching direct-child report files (no recursion)."""
    signatures: Counter[tuple[str, str, str]] = Counter()
    counted = 0
    inspected = 0
    for root in roots:
        if root.is_symlink() or not root.is_dir():
            continue
        try:
            candidates = sorted(
                (child for child in root.iterdir()
                 if child.name.startswith(REPORT_PREFIX)
                 and child.is_dir() and not child.is_symlink()),
                key=lambda item: item.name,
            )
        except OSError:
            continue
        for directory in candidates:
            if inspected >= max_reports:
                break
            inspected += 1
            report = directory / "Report.wer"
            try:
                if report.is_symlink() or not report.is_file():
                    continue
                if report.stat().st_size > MAX_REPORT_BYTES:
                    continue
                signature = parse_report(report.read_bytes())
            except OSError:
                continue
            if signature is not None:
                signatures[signature] += 1
                counted += 1
        if inspected >= max_reports:
            break
    ordered = sorted(
        signatures.items(),
        key=lambda entry: (-entry[1], entry[0]),
    )
    return {
        "reports_inspected": inspected,
        "valid_flyexplorer_reports": counted,
        "signatures": [
            {
                "fault_module": module,
                "exception_code": code,
                "module_offset": offset,
                "report_count": count,
            }
            for (module, code, offset), count in ordered
        ],
        "contains_native_call_stack": False,
        "changes_system_settings": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, action="append",
                        help="existing WER ReportArchive root (may repeat)")
    parser.add_argument("--limit", type=int, default=256,
                        help="maximum report directories to inspect (1..1024)")
    args = parser.parse_args()
    if not 1 <= args.limit <= 1024:
        parser.error("--limit must be between 1 and 1024")
    print(json.dumps(
        inventory(args.root if args.root else default_roots(), args.limit),
        ensure_ascii=True, sort_keys=True,
    ))


if __name__ == "__main__":
    main()
