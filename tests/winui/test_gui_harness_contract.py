"""Static guardrails for WinUI GUI harnesses.

These checks intentionally avoid launching Windows or importing pywinauto.
They catch harness mistakes that must not consume a Remote Windows Task.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests" / "winui"


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
    automation_id = _literal_keyword(node, "auto_id")
    return automation_id in {"LeftNameFilterBox", "RightNameFilterBox"}


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
                    "pywinauto descendants(auto_id=...) is unsupported on the "
                    "project runner; enumerate descendants() and filter "
                    "element_info.automation_id instead",
                )

        if isinstance(func, ast.Attribute) and func.attr == "set_edit_text":
            owner = func.value
            direct_filter = _name_filter_lookup(owner)
            named_filter = (
                isinstance(owner, ast.Name) and owner.id in self.name_filter_vars
            )
            if direct_filter or named_filter:
                self._error(
                    node,
                    "NameFilterBox must be driven through real keyboard input "
                    "(Ctrl+Shift+F/type_keys/send_keys) so TextChanged/event "
                    "delivery is exercised; set_edit_text only proves UIA Value",
                )
        self.generic_visit(node)


class GuiHarnessStaticContract(unittest.TestCase):
    def test_all_winui_python_harnesses_parse(self):
        failures = []
        for path in sorted(TESTS.glob("*.py")):
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


if __name__ == "__main__":
    unittest.main()
