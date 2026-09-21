import sys

MIN_VERSION = (3, 9)

if sys.version_info < MIN_VERSION:
    print(
        "ERROR: Python 3.9 or newer is required; "
        f"found {sys.version.split()[0]} at {sys.executable}."
    )
    raise SystemExit(1)

print(f"Python executable = {sys.executable}")
print(f"Python version = {sys.version.split()[0]}")
