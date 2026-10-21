"""Explicit file loading survives installed tests packages and duplicate basenames."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("contract_file_loader", ROOT / "tools/winui/run_source_contracts.py")
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


class ContractFileLoaderTests(unittest.TestCase):
    def test_ambient_tests_package_and_duplicate_names_do_not_hide_selected_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for side in ("left", "right"):
                parent = root / side
                parent.mkdir()
                path = parent / "test_same.py"
                path.write_text(
                    "import unittest\nclass Owned(unittest.TestCase):\n"
                    f" def test_{side}(self): self.assertTrue(True)\n",
                    encoding="utf-8")
                paths.append(str(path.relative_to(root)))
            before = sys.path[:]
            with patch.dict(sys.modules, {"tests": types.ModuleType("tests")}):
                suite = loader.load_suite(paths, root)
            self.assertEqual(sys.path, before)
            self.assertEqual(suite.countTestCases(), 2)
            self.assertTrue(unittest.TextTestRunner(stream=io.StringIO()).run(suite).wasSuccessful())

    def test_cli_keeps_sibling_imports_available_until_test_finishes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "owned_lazy_dependency.py").write_text("VALUE = 42", encoding="utf-8")
            (root / "test_lazy.py").write_text(
                "import unittest\nclass Owned(unittest.TestCase):\n"
                " def test_lazy(self):\n"
                "  from owned_lazy_dependency import VALUE\n"
                "  self.assertEqual(VALUE, 42)\n", encoding="utf-8")
            before = sys.path[:]
            try:
                with patch.object(loader, "ROOT", root), patch("sys.stderr", io.StringIO()):
                    self.assertEqual(loader.main(["test_lazy.py"]), 0)
                self.assertEqual(sys.path, before)
            finally:
                sys.modules.pop("owned_lazy_dependency", None)

    def test_empty_file_cannot_be_a_successful_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "empty.py").write_text("value = 1", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no tests"):
                loader.load_suite(["empty.py"], root)

    def test_import_and_assertion_failures_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "broken.py"
            path.write_text("raise RuntimeError('owned import failure')", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "owned import failure"):
                loader.load_suite(["broken.py"], root)
            path = root / "failing.py"
            path.write_text(
                "import unittest\nclass Owned(unittest.TestCase):\n"
                " def test_failure(self): self.fail('owned failure')\n", encoding="utf-8")
            suite = loader.load_suite(["failing.py"], root)
            result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            self.assertFalse(result.wasSuccessful())
            self.assertEqual(len(result.failures), 1)

    def test_missing_or_outside_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("missing.py", "../outside.py"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    loader.load_suite([path], root)


if __name__ == "__main__":
    unittest.main()
