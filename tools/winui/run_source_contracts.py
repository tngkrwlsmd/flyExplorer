"""Load explicit owned contract files without importing an ambient tests package."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load_suite(paths, root=ROOT):
    root = root.resolve()
    suite = unittest.TestSuite()
    original_path = sys.path[:]
    try:
        for value in paths:
            path = (root / value).resolve()
            if not path.is_relative_to(root) or path.suffix != ".py" or not path.is_file():
                raise ValueError(f"invalid contract path: {value}")
            sys.path.insert(0, str(path.parent))
            name = "_fly_contract_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            selected = unittest.defaultTestLoader.loadTestsFromModule(module)
            if not selected.countTestCases():
                raise ValueError(f"contract contains no tests: {value}")
            suite.addTests(selected)
    finally:
        sys.path[:] = original_path
    return suite


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    original_path = sys.path[:]
    try:
        # Keep sibling modules available to imports inside test methods too.
        sys.path[:0] = [str((ROOT / value).resolve().parent) for value in args.paths]
        result = unittest.TextTestRunner().run(load_suite(args.paths, root=ROOT))
        return 0 if result.wasSuccessful() else 1
    finally:
        sys.path[:] = original_path


if __name__ == "__main__":
    raise SystemExit(main())
