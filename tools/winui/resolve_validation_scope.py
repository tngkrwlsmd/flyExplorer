"""Classify changed paths into the smallest source-test areas and build scope."""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath
import re
import subprocess
import sys

PRODUCT_AREAS = (
    "core",
    "shell",
    "search",
    "file-operations",
    "session",
    "accessibility",
    "packaging",
    "large-folder",
    "identity-settings",
)
ALL_PRODUCT_AREAS = frozenset(PRODUCT_AREAS)

SOURCE_PREFIXES = ("docs/", ".agent-policy/", "tools/policy/")
SOURCE_FILES = {
    "AGENTS.md",
    "README",
    "README.md",
    "LICENSE",
    "CREDITS",
    ".github/workflows/remote-windows-task.yml",
}
INFRA_FILES = {
    ".github/workflows/remote-windows-task.yml",
    ".github/workflows/windows-build.yml",
    "tools/winui/run_checks.py",
    "tools/winui/resolve_validation_scope.py",
    "tools/winui/validate_remote_request.py",
    "tools/winui/classify_remote_failure.py",
    "tools/winui/store_remote_evidence.py",
    "tests/winui/test_remote_failure_classifier.py",
    "tests/winui/test_remote_request_preflight_contract.py",
    "tests/winui/test_remote_windows_task_contract.py",
    "tests/winui/test_remote_evidence_archive_contract.py",
    "tests/winui/test_validation_scope_contract.py",
}
HARNESS_FILES = {
    "tools/winui/check_python_static.py",
    "tools/winui/runner_health.py",
    "tests/winui/test_gui_harness_contract.py",
    "tests/winui/test_build_environment_contract.py",
    "tests/winui/uia_polling.py",
}


def normalize(path: str) -> str:
    return path.strip().replace("\\", "/")


def is_source_only(path: str) -> bool:
    path = normalize(path)
    if path in SOURCE_FILES or path.startswith(SOURCE_PREFIXES):
        return True
    return path.startswith("tests/winui/") and path.endswith("_contract.py")


def classify(paths: list[str], message: str) -> tuple[str, str]:
    paths = [normalize(path) for path in paths if normalize(path)]
    if not paths:
        raise ValueError("at least one changed path is required")
    if all(is_source_only(path) for path in paths):
        return "source", "source/policy/metadata-only change"
    return "release", "product/build change uses one build-focused Release validation"


def _test_area(path: str) -> set[str]:
    name = PurePosixPath(path).name.lower()
    if any(token in name for token in ("search", "filter_preset")):
        return {"search"}
    if any(token in name for token in ("session", "workspace_restore")):
        return {"session"}
    if any(token in name for token in ("installer", "release_payload", "lifecycle_safety",
                                       "portable_safety", "registered_file_type")):
        return {"packaging"}
    if any(token in name for token in ("accessibility", "high_contrast")):
        return {"accessibility"}
    if "large_folder" in name:
        return {"large-folder"}
    if any(token in name for token in ("bookmark", "preferences", "product_identity")):
        return {"identity-settings"}
    if any(token in name for token in ("clipboard", "recycle")):
        return {"file-operations"}
    if any(token in name for token in ("known_folder", "thumbnail", "external_context",
                                       "file_detail")):
        return {"shell"}
    if name in {"test_arch_contract.py", "test_m26_fluent_contract.py"}:
        return {"core"}
    return set()


def areas_for_path(path: str) -> set[str]:
    path = normalize(path)
    lower = path.lower()

    if lower.startswith("tests/winui/"):
        return _test_area(path)
    if lower.startswith("packaging/") or lower in {"package.bat"}:
        return {"packaging"}

    if lower.startswith("app/winui/"):
        name = PurePosixPath(lower).name
        if "search" in name or name == "m19_search.cpp":
            return {"search"}
        if any(token in name for token in (
            "session", "workspace_restore", "window_workspace"
        )):
            return {"session"}
        if any(token in name for token in (
            "file_operation", "m21_commands", "m22_transfers", "m23_drag"
        )):
            return {"file-operations"}
        if any(token in name for token in (
            "shell_navigation", "file_detail", "known_folder"
        )):
            return {"shell"}
        if "preferences" in name:
            return {"identity-settings"}
        if PurePosixPath(lower).suffix in {
            ".cpp", ".h", ".hpp", ".idl", ".rc", ".xml", ".xaml"
        }:
            return {"core"}
        return set()

    if lower.startswith("src/base/"):
        name = PurePosixPath(lower).name
        if name.startswith("search"):
            return {"search"}
        if name.startswith("ui_session"):
            return {"session"}
        if name.startswith(("file_command", "shell_transfer", "shell_clipboard")):
            return {"file-operations"}
        if name.startswith("shell_"):
            return {"shell"}
        if name.startswith(("ui_preferences", "bookmark")):
            return {"identity-settings"}
        return set(ALL_PRODUCT_AREAS)

    if lower in {"build.bat", "clean.bat", "run.bat", "test.bat"}:
        return set(ALL_PRODUCT_AREAS)
    return set()


def affected_areas(paths: list[str]) -> set[str]:
    result: set[str] = set()
    unknown_product = False
    for raw in paths:
        path = normalize(raw)
        found = areas_for_path(path)
        result.update(found)
        if found:
            continue
        if path.startswith(("app/winui/", "src/base/")):
            unknown_product = True
    return set(ALL_PRODUCT_AREAS) if unknown_product else result


def change_families(paths: list[str]) -> set[str]:
    families: set[str] = set()
    for raw in paths:
        path = normalize(raw)
        if path in INFRA_FILES or path.startswith(".github/workflows/"):
            families.add("infra")
        if (
            path in HARNESS_FILES
            or path.startswith("tools/winui/high_contrast_")
            or (path.startswith("tests/winui/") and path.endswith("_gui.py"))
        ):
            families.add("harness")
        if areas_for_path(path):
            families.add("product")
    return families


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
    message = "\n".join(git_lines("log", "-1", "--format=%B", args.head))
    scope, reason = classify(paths, message)
    areas = sorted(affected_areas(paths))
    families = sorted(change_families(paths))
    print("Changed paths:")
    for path in paths:
        print(f"  {path}")
    print(f"VALIDATION_REASON={reason}")
    print(f"VALIDATION_SCOPE={scope}")
    print(f"VALIDATION_AREAS={','.join(areas) or '-'}")
    print(f"VALIDATION_FAMILIES={','.join(families) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
