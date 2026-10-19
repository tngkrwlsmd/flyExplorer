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


def _call_attr(node: ast.AST, *names: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
    )


class _HarnessVisitor(ast.NodeVisitor):
    """Reject known pywinauto mistakes before a Windows runner is spent."""

    def __init__(self, path: Path):
        self.path = path
        self.name_filter_vars: set[str] = set()
        self.wrapper_vars: set[str] = set()
        self.wrapper_list_vars: set[str] = set()
        self.errors: list[str] = []

    def _error(self, node: ast.AST, message: str) -> None:
        self.errors.append(
            f"{self.path.name}:{getattr(node, 'lineno', '?')}: {message}"
        )

    def _remember_assignment(self, target: ast.AST, value: ast.AST) -> None:
        if not isinstance(target, ast.Name):
            return
        if _name_filter_lookup(value):
            self.name_filter_vars.add(target.id)
        if isinstance(value, ast.Subscript):
            if isinstance(value.value, ast.Name) and value.value.id in self.wrapper_list_vars:
                self.wrapper_vars.add(target.id)
            elif _call_attr(value.value, "windows", "descendants"):
                self.wrapper_vars.add(target.id)
        if isinstance(value, (ast.ListComp, ast.GeneratorExp)):
            generators = value.generators
            if any(_call_attr(gen.iter, "windows", "descendants") for gen in generators):
                self.wrapper_list_vars.add(target.id)
        if _call_attr(value, "wrapper_object"):
            self.wrapper_vars.add(target.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._remember_assignment(target, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._remember_assignment(node.target, node.value)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if isinstance(node.target, ast.Name) and _call_attr(
            node.iter, "windows", "descendants"
        ):
            self.wrapper_vars.add(node.target.id)
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

        if isinstance(func, ast.Attribute) and func.attr == "move":
            if any(keyword.arg == "duration" for keyword in node.keywords):
                self._error(
                    node,
                    "pywinauto mouse.move(..., duration=...) is unsupported; "
                    "use bounded stepped moves with explicit sleeps",
                )

        if isinstance(func, ast.Attribute) and func.attr == "child_window":
            owner = func.value
            if isinstance(owner, ast.Name) and owner.id in self.wrapper_vars:
                self._error(
                    node,
                    "UIAWrapper.child_window is invalid; resolve a "
                    "WindowSpecification with Desktop(...).window(handle=...) first",
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


class _PollingBroadCatchVisitor(ast.NodeVisitor):
    POLLING_NAMES = {"until", "eventually", "wait_for", "wait_until"}

    def __init__(self, path: Path):
        self.path = path
        self.function_stack: list[str] = []
        self.errors: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        broad = node.type is None or (
            isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
        )
        if broad and self.function_stack and self.function_stack[-1] in self.POLLING_NAMES:
            self.errors.append(
                f"{self.path.name}:{node.lineno}: polling helper "
                "must not catch Exception/BaseException; retry only known transient UIA errors"
            )
        self.generic_visit(node)


class GuiHarnessStaticContract(unittest.TestCase):
    def test_theme_pixel_probe_avoids_dynamic_left_list(self):
        probe = (TESTS / "test_m20_shell_gui.py").read_text(encoding="utf-8")
        self.assertIn('int(rect.width()*0.86)', probe)
        self.assertIn('int(rect.width()*0.72)', probe)
        self.assertIn('min(80,rect.width()-3)', probe)
        self.assertNotIn('int(rect.width()*0.38)', probe)
        self.assertIn('assert all(light-dark>20 for light,dark in zip(lb,db))', probe)
        self.assertIn('settled_surface(', probe)

    def test_details_column_resize_has_focused_strict_gui_entrypoint(self):
        runner = (TOOLS / "run_checks.py").read_text(encoding="utf-8")
        gui = (TESTS / "test_owned_column_resize_gui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"column-resize",', runner)
        self.assertIn('if area == "column-resize":', runner)
        self.assertIn('str(TESTS / "test_owned_column_resize_gui.py")', runner)
        self.assertIn('OWNED_DETAIL_COLUMN_RESULT ', gui)
        self.assertIn('print("OWNED_DETAIL_COLUMN_RESULT FAIL"', gui)
        self.assertIn('eventually(horizontal_resize_cursor,', gui)
        self.assertIn('SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL', gui)

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

    def test_known_pywinauto_traps_are_detected_by_the_guard(self):
        source = """
def probe(mouse, wrapper):
    mouse.move(coords=(1, 2), duration=.2)
    wrapper.child_window(auto_id="LeftFiles")
"""
        tree = ast.parse(source)
        visitor = _HarnessVisitor(Path("synthetic.py"))
        visitor.wrapper_vars.add("wrapper")
        visitor.visit(tree)
        self.assertEqual(2, len(visitor.errors))

    def test_static_checker_catches_missing_import_name(self):
        self.assertEqual(
            ["sys"],
            static_check.undefined_names(
                "def main():\n    return sys.argv[1]\n",
                "missing_sys.py",
            ),
        )

    def test_all_gui_harnesses_and_critical_helpers_have_no_undefined_globals(self):
        paths = sorted(TESTS.glob("test_*gui.py")) + [
            TESTS / "uia_polling.py",
            TOOLS / "high_contrast_state.py",
            TOOLS / "high_contrast_runner_setup.py",
            TOOLS / "runner_health.py",
            TOOLS / "high_contrast_acceptance.py",
        ]
        failures = []
        for path in paths:
            failures.extend(static_check.check_path(path))
        self.assertEqual([], failures, "\n".join(failures))

    def test_polling_helpers_never_swallow_broad_errors(self):
        paths = sorted(TESTS.glob("test_*gui.py")) + [
            TESTS / "uia_polling.py",
            TOOLS / "high_contrast_runner_setup.py",
            TOOLS / "high_contrast_acceptance.py",
        ]
        failures = []
        for path in paths:
            tree = ast.parse(
                path.read_text(encoding="utf-8-sig"),
                filename=str(path),
            )
            visitor = _PollingBroadCatchVisitor(path)
            visitor.visit(tree)
            failures.extend(visitor.errors)
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
