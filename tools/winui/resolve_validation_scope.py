"""Resolve the automatic build-focused Windows scope for one main push.

Automatic main pushes use only source or release. GUI/visual acceptance belongs
to the pre-main remote-shell development loop. release-gui/full remain manual
workflow_dispatch choices and are never selected by this classifier.
"""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys

TRAILER_RE = re.compile(
    r"^CI-Scope:\s*(source|release)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

SOURCE_PREFIXES = (
    "docs/",
    ".agent-policy/",
    "tools/policy/",
)
SOURCE_FILES = {
    "AGENTS.md",
    "README",
    "README.md",
    "LICENSE",
    "CREDITS",
    ".github/workflows/remote-windows-task.yml",
    ".github/workflows/remote-windows-task-cleanup.yml",
}

RELEASE_PREFIXES = (
    "src/base/",
    "packaging/",
    "tests/winui/m19/",
    "tests/winui/m20/",
    "tests/winui/m21/",
    "tests/winui/m22/",
    "tests/winui/m23/",
)
RELEASE_FILES = {
    "build.bat",
    "clean.bat",
    "package.bat",
    "run.bat",
    "test.bat",
    ".github/workflows/windows-build.yml",
    "app/winui/flyExplorer.project-template.xml",
    "tools/winui/resolve_validation_scope.py",
    "tools/winui/resolve_msbuild.py",
    "tools/winui/verify_restore.py",
    "tools/winui/collect_ci_failure_artifacts.py",
}

HARD_GUI_FILES = {
    "tests/winui/test_shell_gui.py",
    "tests/winui/requirements-gui.txt",
    "tools/winui/run_checks.py",
}
HARD_GUI_EXTENSIONS = {
    ".xaml",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
}


def normalize(path: str) -> str:
    return path.strip().replace("\\", "/")


def is_source_only(path: str) -> bool:
    path = normalize(path)
    if path in SOURCE_FILES or path.startswith(SOURCE_PREFIXES):
        return True
    return bool(re.fullmatch(r"tests/winui/test_.*_contract\.py", path))


def is_hard_gui(path: str) -> bool:
    path = normalize(path)
    lower = path.lower()
    if path in HARD_GUI_FILES:
        return True
    if lower.startswith("app/winui/assets/"):
        return True
    if lower.startswith("app/winui/") and PurePosixPath(lower).suffix in HARD_GUI_EXTENSIONS:
        return True
    return False


def is_release_safe(path: str) -> bool:
    path = normalize(path)
    if is_source_only(path):
        return True
    if path in RELEASE_FILES or path.startswith(RELEASE_PREFIXES):
        return True
    return False


def is_nonvisual_winui_source(path: str) -> bool:
    path = normalize(path)
    if not path.startswith("app/winui/") or is_hard_gui(path):
        return False
    suffix = PurePosixPath(path.lower()).suffix
    return suffix in {".cpp", ".h", ".hpp", ".idl", ".rc", ".xml"}


def requested_scope(message: str) -> str | None:
    matches = TRAILER_RE.findall(message or "")
    return matches[-1].lower() if matches else None


def classify(paths: list[str], message: str) -> tuple[str, str]:
    paths = [normalize(path) for path in paths if normalize(path)]
    if not paths:
        raise ValueError("at least one changed path is required")

    hard_gui = [path for path in paths if is_hard_gui(path)]
    requested = requested_scope(message)

    if hard_gui:
        return (
            "release",
            "hard GUI path; GUI acceptance must be completed pre-main: "
            + hard_gui[0],
        )

    if all(is_source_only(path) for path in paths):
        return "source", "source/policy/metadata-only change"

    if requested == "source":
        # A trailer may not downgrade product/build paths.
        requested = None

    return "release", "product/build change uses build-focused Release CI"


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        text=True,
        encoding="utf-8",
        errors="strict",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    paths = git_lines("diff", "--name-only", args.before, args.head)
    message_lines = git_lines("log", "-1", "--format=%B", args.head)
    message = "\n".join(message_lines)
    scope, reason = classify(paths, message)

    print("Changed paths:")
    for path in paths:
        print(f"  {path}")
    print(f"VALIDATION_REASON={reason}")
    print(f"VALIDATION_SCOPE={scope}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
