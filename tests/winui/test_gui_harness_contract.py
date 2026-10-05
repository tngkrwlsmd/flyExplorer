"""Cheap static guardrails for WinUI GUI harnesses and validation helpers."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests" / "winui"
TOOLS = ROOT / "tools" / "winui"
STATIC_PATH = TOOLS / "check_python_static.py"

spec = importlib.util.spec_from_file_location("check_python_static", STATIC_PATH)
assert spec is not None and spec.loader is not None
static_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(static_check)


def _literal_keyword(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def _name_filter_lookup(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "child_window":
        return False
    return _literal_keyword(node, "auto_id") in {
        "LeftNameFilterBox",
        "RightNameFilterBox",
    }


class _HarnessVisitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.name_filter_vars: set[str] = set()
        self.errors: list[str] = []

    def _error(self, node: ast.AST, message: str) -> None:
        self.errors.append(
            f"{self.path.name}:{getattr(node, 'lineno', '?')}: {message}"
        )

    def visit_Assign(self, node: ast.Assign) -> None:
        if _name_filter_lookup(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.name_filter_vars.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and _name_filter_lookup(node.value):
            if isinstance(node.target, ast.Name):
                self.name_filter_vars.add(node.target.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "descendants":
            if any(keyword.arg == "auto_id" for keyword in node.keywords):
                self._error(
                    node,
                    "pywinauto descendants(auto_id=...) is unsupported; "
                    "enumerate descendants() and filter automation_id",
                )

        if isinstance(func, ast.Attribute) and func.attr == "set_edit_text":
            owner = func.value
            if _name_filter_lookup(owner) or (
                isinstance(owner, ast.Name)
                and owner.id in self.name_filter_vars
            ):
                self._error(
                    node,
                    "NameFilterBox must be driven through real keyboard input",
                )
        self.generic_visit(node)


class _BroadSwallowVisitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        broad = node.type is None or (
            isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
        )
        if broad and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.errors.append(
                f"{self.path.name}:{node.lineno}: broad exception is silently swallowed"
            )
        self.generic_visit(node)


class GuiHarnessStaticContract(unittest.TestCase):
    def test_winui_python_sources_parse(self):
        failures = []
        paths = list(TESTS.glob("*.py")) + list(TOOLS.glob("*.py"))
        for path in sorted(paths):
            try:
                ast.parse(
                    path.read_text(encoding="utf-8-sig"),
                    filename=str(path),
                )
            except SyntaxError as exc:
                failures.append(f"{path.name}:{exc.lineno}: {exc.msg}")
        self.assertEqual([], failures, "\n".join(failures))

    def test_known_pywinauto_preflight_traps_are_rejected(self):
        failures = []
        for path in sorted(TESTS.glob("*.py")):
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
            )
            visitor = _HarnessVisitor(path)
            visitor.visit(tree)
            failures.extend(visitor.errors)
        self.assertEqual([], failures, "\n".join(failures))

    def test_static_checker_catches_missing_import_name(self):
        self.assertEqual(
            ["sys"],
            static_check.undefined_names(
                "def main():\n    return sys.argv[1]\n",
                "missing_sys.py",
            ),
        )

    def test_critical_harness_helpers_have_no_undefined_globals(self):
        paths = [
            TOOLS / "high_contrast_state.py",
            TOOLS / "high_contrast_runner_setup.py",
            TOOLS / "runner_health.py",
            TOOLS / "high_contrast_acceptance.py",
            TESTS / "test_high_contrast_gui.py",
        ]
        failures = []
        for path in paths:
            failures.extend(static_check.check_path(path))
        self.assertEqual([], failures, "\n".join(failures))

    def test_critical_polling_paths_do_not_silently_swallow_broad_errors(self):
        paths = [
            TOOLS / "high_contrast_runner_setup.py",
            TOOLS / "high_contrast_acceptance.py",
            TESTS / "test_high_contrast_gui.py",
        ]
        failures = []
        for path in paths:
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
            )
            visitor = _BroadSwallowVisitor(path)
            visitor.visit(tree)
            failures.extend(visitor.errors)
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
