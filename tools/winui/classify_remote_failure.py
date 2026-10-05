"""Classify one Remote Windows Task failure from bounded text evidence."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

EXPLICIT_RE = re.compile(r"FAILURE_CATEGORY=([A-Z0-9_]+)")
ALIASES = {
    "REUSED_RUNTIME_MISMATCH": "RUNTIME_REUSE_MISMATCH",
}


def classify(text: str) -> str:
    explicit = EXPLICIT_RE.findall(text)
    if explicit:
        return ALIASES.get(explicit[-1], explicit[-1])

    lower = text.lower()

    if (
        "jobs=[]" in lower
        or "jobs = []" in lower
        or "invalid workflow file" in lower
        or "workflow is not valid" in lower
    ):
        return "WORKFLOW_DEFINITION_FAILURE"

    if (
        "resource not accessible by integration" in lower
        or "write access to repository not granted" in lower
        or "permission to " in lower and " denied" in lower
    ):
        return "REPOSITORY_PERMISSION_FAILURE"

    if (
        "reused_runtime_mismatch" in lower
        or ("expected digest:" in lower and "actual digest:" in lower)
    ):
        return "RUNTIME_REUSE_MISMATCH"

    if (
        "getrelativepath" in lower
        and (
            "methodnotfound" in lower
            or "does not contain a method named" in lower
        )
    ):
        return "POWERSHELL_COMPATIBILITY_FAILURE"

    if (
        "owned installed app did not close within the accepted" in lower
        or (
            "subprocess.timeoutexpired" in lower
            and "test_installed_lifecycle.py" in lower
            and "flyexplorer.exe" in lower
        )
    ):
        return "INSTALLED_APP_SHUTDOWN_TIMEOUT"

    if "subprocess.timeoutexpired" in lower:
        return "SUBPROCESS_TIMEOUT_FAILURE"

    if re.search(r"error C\d+|error LNK\d+|error MSB\d+|fatal error C\d+", text):
        return "PRODUCT_BUILD_FAILURE"

    if (
        "NameError:" in text
        or "FullyQualifiedErrorId : MethodNotFound" in text
        or "does not contain a method named" in text
        or re.search(r"TypeError:.*unexpected keyword argument", text)
        or "UIAWrapper' object has no attribute 'child_window'" in text
        or "IUIA.build_condition() got an unexpected keyword argument" in text
    ):
        return "HARNESS_PROGRAMMING_FAILURE"

    if "NoPatternInterfaceError" in text:
        return "AUTOMATION_API_FAILURE"
    if "ElementAmbiguousError" in text or "ElementNotFoundError" in text:
        return "AUTOMATION_DISCOVERY_FAILURE"
    if "TimeoutError" in text:
        return "AUTOMATION_TIMEOUT_FAILURE"
    if "AssertionError:" in text or re.search(r"(?m)^(?:FAIL:|FAILED)", text):
        return "TEST_ASSERTION_FAILURE"
    return "COMMAND_FAILURE_UNCLASSIFIED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--text", default="")
    args = parser.parse_args(argv)

    chunks = [args.text]
    for path in args.paths:
        try:
            chunks.append(path.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError:
            continue
    print(classify("\n".join(chunks)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
