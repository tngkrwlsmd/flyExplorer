#!/usr/bin/env python3
"""Stage current UTF-8 help sources and compile fxfile.chm on Windows.

The pre-existing compiled CHM is deliberately not a source of truth. A package
must regenerate it using the installed Microsoft HTML Help Workshop (hhc.exe).
No network access, external Python modules or application execution is needed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "htmlhelp"
STAGE = ROOT / "dist" / ".htmlhelp-build"
OUTPUT = ROOT / "dist" / "fxfile.chm"
PROJECT = "flyExplorer.hhp"
TOPIC = SOURCE / "Html" / "start.htm"
META_CHARSET = re.compile(r"(charset\s*=\s*['\"]?)[\w-]+", re.IGNORECASE)
LOCAL_TOPIC = re.compile(r'<param\s+name\s*=\s*["\']Local["\']\s+value\s*=\s*["\']([^"\']+)', re.IGNORECASE)
INCLUDED_SUFFIXES = {".htm", ".html", ".css", ".gif", ".png", ".jpg", ".jpeg", ".bmp", ".ico"}


class HelpBuildError(Exception):
    pass


def read_source(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp949")


def check_sources() -> list[Path]:
    required = (
        SOURCE / PROJECT,
        SOURCE / "flyExplorer.hhc",
        SOURCE / "flyExplorer.hhk",
        TOPIC,
        SOURCE / "Html" / "license.htm",
        SOURCE / "Html" / "flyExplorer" / "requirements.htm",
    )
    for path in required:
        if not path.is_file():
            raise HelpBuildError("missing HTML Help source: " + str(path.relative_to(ROOT)))
    project = read_source(required[0])
    if "Compiled file=fxfile.chm" not in project or "Default topic=html\\start.htm" not in project:
        raise HelpBuildError("HTML Help project must target fxfile.chm and html\\start.htm")
    start = read_source(TOPIC)
    if "2.0.4-dev" not in start or "이전 버전" not in start:
        raise HelpBuildError("help landing page must disclose its current version and legacy topics")
    license_page = read_source(SOURCE / "Html" / "license.htm")
    if "GNU GPL" not in license_page or "GFL SDK" not in license_page:
        raise HelpBuildError("HTML Help application and third-party license notices are missing")
    known = {p.relative_to(SOURCE).as_posix().casefold() for p in SOURCE.rglob("*") if p.is_file()}
    for index_name in ("flyExplorer.hhc", "flyExplorer.hhk"):
        index = read_source(SOURCE / index_name)
        for match in LOCAL_TOPIC.finditer(index):
            relative = match.group(1).replace("\\", "/").casefold()
            if relative not in known:
                raise HelpBuildError(index_name + " has broken Local topic: " + match.group(1))
    script = read_source(ROOT / "dist" / "make_installer.bat")
    if "rebuild_htmlhelp.py" not in script or "--build" not in script:
        raise HelpBuildError("installer script does not force a fresh compiled help build")
    if "/dist/fxfile.chm" not in read_source(ROOT / ".gitignore"):
        raise HelpBuildError("generated CHM must be ignored rather than tracked")
    return sorted(path for path in SOURCE.rglob("*") if path.is_file())


def to_utf8_html(text: str) -> str:
    if META_CHARSET.search(text):
        return META_CHARSET.sub(lambda m: m.group(1) + "utf-8", text)
    head = re.search(r"<head\b[^>]*>", text, re.IGNORECASE)
    if not head:
        raise HelpBuildError("HTML topic is missing <head> (cannot declare UTF-8)")
    return text[:head.end()] + '\n<meta http-equiv="content-type" content="text/html; charset=utf-8">' + text[head.end():]


def stage_help(files: list[Path]) -> Path:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    included = []
    for source in files:
        relative = source.relative_to(SOURCE)
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix.lower()
        if suffix in (".htm", ".html"):
            target.write_bytes(to_utf8_html(read_source(source)).encode("utf-8"))
        elif suffix in (".hhc", ".hhk"):
            target.write_bytes(read_source(source).encode("cp949"))
        elif source.name != PROJECT:
            shutil.copy2(source, target)
        if suffix in INCLUDED_SUFFIXES:
            included.append(str(relative).replace("/", "\\"))
    project = read_source(SOURCE / PROJECT)
    project += "\n[FILES]\n" + "\n".join(sorted(included, key=str.casefold)) + "\n"
    (STAGE / PROJECT).write_bytes(project.encode("cp949"))
    print("HTML Help staged: {} source files, {} included resources".format(len(files), len(included)))
    return STAGE / PROJECT


def find_compiler() -> Path:
    candidates = []
    configured = os.environ.get("HHC_EXE", "").strip('" ')
    if configured:
        candidates.append(Path(configured))
    on_path = shutil.which("hhc.exe")
    if on_path:
        candidates.append(Path(on_path))
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if base:
            candidates.append(Path(base) / "HTML Help Workshop" / "hhc.exe")
    for path in candidates:
        if path.is_file():
            return path
    raise HelpBuildError("Microsoft HTML Help Workshop hhc.exe not found; install it or set HHC_EXE")


def build_help(files: list[Path]) -> None:
    # Fail closed: never let a failed rebuild silently use yesterday's CHM.
    OUTPUT.unlink(missing_ok=True)
    compiler = find_compiler()
    project = stage_help(files)
    try:
        proc = subprocess.run([str(compiler), str(project)], cwd=str(STAGE),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding="cp949", errors="replace", timeout=180,
                              check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HelpBuildError("HTML Help compiler could not complete: " + str(exc)) from exc
    if proc.stdout:
        print(proc.stdout)
    generated = STAGE / "fxfile.chm"
    # hhc.exe has historically reported exit code 1 on successful builds;
    # neither 0 nor 1 is proof of success without an actual CHM file.
    if proc.returncode not in (0, 1) or not generated.is_file():
        raise HelpBuildError("HTML Help compilation failed or output was not created")
    with generated.open("rb") as stream:
        valid = stream.read(4) == b"ITSF"
    if not valid or generated.stat().st_size < 4096:
        raise HelpBuildError("compiled HTML Help output is missing its CHM signature or is too short")
    shutil.copyfile(generated, OUTPUT)
    print("Fresh HTML Help generated: " + str(OUTPUT.relative_to(ROOT)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="read-only source and link preflight")
    mode.add_argument("--stage", action="store_true", help="stage converted sources without hhc.exe")
    mode.add_argument("--build", action="store_true", help="rebuild CHM using hhc.exe")
    args = parser.parse_args()
    try:
        files = check_sources()
        if args.stage:
            stage_help(files)
        elif args.build:
            build_help(files)
        else:
            print("HTML Help source/package contract: PASS ({} tracked help files)".format(len(files)))
        return 0
    except (HelpBuildError, OSError, UnicodeError) as exc:
        print("HTML Help: FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
