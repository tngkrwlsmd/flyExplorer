"""Classify a completed Remote Windows Task command failure.

Keep this stdlib-only so the workflow can run it before any GUI dependency setup.
Classification describes the observed failure boundary; it does not guess product
blame when the available evidence cannot establish it.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

EXPLICIT_RE = re.compile(r"FAILURE_CATEGORY=([A-Z0-9_]+)")


def classify(text: str) -> str:
    explicit = EXPLICIT_RE.findall(text)
    if explicit:
        return explicit[-1]

    lower = text.lower()

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
    category = classify("\n".join(chunks))
    print(category)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
