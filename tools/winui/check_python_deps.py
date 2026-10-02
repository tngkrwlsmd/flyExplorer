"""Check pinned Python dependencies used by owned WinUI GUI automation."""
from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REQ = ROOT / "tests" / "winui" / "requirements-gui.txt"


def load_requirements() -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in REQ.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)", line)
        if not match:
            raise RuntimeError(f"GUI requirement is not exactly pinned: {line}")
        result[match.group(1)] = match.group(2)
    return result
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gui", action="store_true",
        help="Validate pinned GUI automation packages.")
    args = parser.parse_args()

    if not args.gui:
        print("SOURCE_PYTHON_DEPENDENCIES=stdlib-only")
        return 0

    try:
        expected = load_requirements()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    failed: list[str] = []
    for package, want in expected.items():
        try:
            got = metadata.version(package)
        except metadata.PackageNotFoundError:
            got = None
        if got != want:
            failed.append(
                f"{package}: expected {want}, found {got or 'not installed'}")
        else:
            print(f"GUI_DEP_OK {package}=={got}")
    if failed:
        print(
            "ERROR: GUI Python dependency mismatch. Install with "
            "'python -m pip install -r tests/winui/requirements-gui.txt'.",
            file=sys.stderr)
        for item in failed:
            print("ERROR: " + item, file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
