"""Resolve the automatic Windows validation scope for one main push.

The classifier is deliberately conservative: hard GUI paths always require GUI
acceptance. A behavior-preserving nonvisual WinUI change may use Release-only
acceptance when the logical-unit commit is named refactor: or carries an
explicit CI-Scope: release trailer.
"""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys

TRAILER_RE = re.compile(
    r"^CI-Scope:\s*(source|release|release-gui)\s*$",
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
    subject = (message or "").splitlines()[0].strip().lower()
    is_refactor = subject.startswith("refactor:")

    if hard_gui:
        return "release-gui", "hard GUI path: " + hard_gui[0]

    if requested == "release-gui":
        return "release-gui", "commit trailer requested release-gui"

    if all(is_source_only(path) for path in paths):
        return "source", "source/policy/metadata-only change"

    if all(is_release_safe(path) for path in paths):
        return "release", "UI-independent/build/native change"

    refactor_eligible = all(
        is_release_safe(path) or is_nonvisual_winui_source(path)
        for path in paths
    )
    if requested == "release" and refactor_eligible:
        return "release", "CI-Scope: release on nonvisual eligible paths"

    if is_refactor and refactor_eligible:
        return "release", "refactor: logical unit on nonvisual eligible paths"

    return "release-gui", "WinUI/runtime behavior change defaults to GUI acceptance"


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
