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
        self.assertIn('if area in ("column-resize","column-resize-right"):', runner)
        self.assertIn('str(TESTS / "test_owned_column_resize_gui.py")', runner)
        self.assertIn('OWNED_DETAIL_COLUMN_RESULT ', gui)
        for marker in (
            'OWNED_DETAIL_COLUMN_RESULT PASS',
            'OWNED_DETAIL_COLUMN_NAME_RESIZE True',
            'OWNED_DETAIL_COLUMN_TYPE_RESIZE True',
            'OWNED_DETAIL_COLUMN_SIZE_RESIZE True',
            'SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL True',
        ):
            self.assertIn(marker, runner)
        self.assertIn('if not all(marker in lines for marker in required)', runner)
        self.assertIn('L08_REQUIRED_GUI_MARKERS_MISSING_OR_ERROR', runner)
        self.assertIn('print("OWNED_DETAIL_COLUMN_RESULT FAIL"', gui)
        self.assertIn('current=horizontal_resize_cursor(details=True)', gui)
        self.assertIn('assert len(cursor_observations)==3', gui)
        self.assertIn('L08 native horizontal resize cursor missing on owned handle', gui)
        self.assertIn('SIX_ORIGINAL_MFC_SETTINGS_IDENTICAL', gui)

    def test_m19_search_preset_reset_reveals_the_owned_query_editor(self):
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        reset = gui.split("# Restore legacy-default options", 1)[1].split(
            '"Search v2 option reset did not restore default search"', 1
        )[0]
        self.assertIn('search_control("SearchTargetBox").wrapper_object().select(0)', reset)
        self.assertIn('owned_search_scroll = element("SearchPanel").wrapper_object().iface_scroll', reset)
        self.assertIn("if owned_search_scroll.CurrentVerticallyScrollable:", reset)
        self.assertIn("owned_search_scroll.SetScrollPercent(-1, 0)", reset)
        self.assertIn('element("SearchTermBox").exists(timeout=.2)', reset)
        self.assertIn('element("SearchTermBox").is_visible()', reset)
        self.assertLess(reset.index("owned_search_scroll.SetScrollPercent(-1, 0)"),
                        reset.index('search_control("SearchTermBox").set_edit_text("readme")'))

    def test_m19_owned_search_control_scrolls_and_fails_closed(self):
        from types import SimpleNamespace
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        function = next(node for node in ast.parse(gui).body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "reveal_search_control")
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     "M19 search visibility", "exec"), namespace)
        reveal_search_control = namespace["reveal_search_control"]

        class Rect:
            def __init__(self, top=0, bottom=100):
                self.left, self.right, self.top, self.bottom = 0, 100, top, bottom
            def width(self): return self.right - self.left
            def height(self): return self.bottom - self.top

        for case in ("visible", "offscreen", "clipped", "missing", "no-scroll",
                     "hidden-panel", "wrong-key", "reentry"):
            with self.subTest(case=case):
                position = 0
                pending = None
                calls = []
                scroll = SimpleNamespace(CurrentVerticallyScrollable=case != "no-scroll")

                def set_scroll(horizontal, vertical):
                    nonlocal pending
                    self.assertEqual(-1, horizontal)
                    self.assertIsNone(pending, "more than one scroll per poll")
                    calls.append(vertical)
                    pending = vertical

                scroll.SetScrollPercent = set_scroll

                class Panel:
                    def exists(self, timeout): return True
                    def is_visible(self): return case != "hidden-panel"
                    def rectangle(self): return Rect()
                    def wrapper_object(self): return SimpleNamespace(iface_scroll=scroll)

                class Item:
                    def exists(self, timeout):
                        return (case not in ("missing", "no-scroll") and
                                (case != "offscreen" or position >= 60))
                    def is_visible(self): return True
                    def rectangle(self):
                        if case == "clipped" and position < 60:
                            return Rect(90, 110)
                        if case == "reentry" and position < 60:
                            return Rect(110, 130)
                        return Rect(20, 40)

                panel, item = Panel(), Item()

                def element(key):
                    self.assertIn(key, ("SearchPanel", "SearchMinSizeBox"))
                    return panel if key == "SearchPanel" else item

                def eventually(probe, label, timeout):
                    nonlocal pending, position
                    self.assertEqual(timeout, 8)
                    for _ in range(20):
                        if pending is not None:
                            position, pending = pending, None
                        value = probe()
                        if value:
                            return value
                    raise AssertionError(label)

                if case in ("visible", "offscreen", "clipped", "reentry"):
                    self.assertIs(item, reveal_search_control(
                        element, eventually, "SearchMinSizeBox"))
                    self.assertEqual(calls, [] if case == "visible" else list(range(0, 61, 10)))
                    if case == "reentry":
                        position = 0
                        calls.clear()
                        self.assertIs(item, reveal_search_control(
                            element, eventually, "SearchMinSizeBox"))
                        self.assertEqual(calls, list(range(0, 61, 10)))
                else:
                    with self.assertRaises(AssertionError):
                        reveal_search_control(element, eventually,
                            "LeftFiles" if case == "wrong-key" else "SearchMinSizeBox")
                    self.assertEqual(calls, list(range(0, 101, 10)) if case == "missing" else [])

        # The observed failing V3 editor and later actions use this real helper.
        self.assertIn('search_control("SearchMinSizeBox").set_edit_text("7")', gui)
        self.assertIn('click_search("SearchRunButton")', gui)
        click = gui.split("def click_search(key):", 1)[1].split("def children():", 1)[0]
        self.assertLess(click.index("focus()"), click.index("search_control(key)"))
        self.assertLess(click.index("owner.value == p.pid"), click.index("item.click_input()"))

    def test_m19_search_click_rechecks_foreground_after_scroll(self):
        from types import SimpleNamespace
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        function = next(node for node in ast.walk(ast.parse(gui))
                        if isinstance(node, ast.FunctionDef) and node.name == "click_search")
        for foreground, owner in ((51, 42), (51, 77), (0, 0)):
            with self.subTest(foreground=foreground, owner=owner):
                events = []

                def focus(): events.append("focus")

                def search_control(key):
                    self.assertEqual("SearchRunButton", key)
                    events.append("reveal")
                    return SimpleNamespace(click_input=lambda: events.append("click"))

                def get_foreground():
                    events.append("foreground")
                    return foreground

                def get_owner(hwnd, target):
                    self.assertEqual(foreground, hwnd)
                    target.value = owner

                namespace = {
                    "focus": focus, "search_control": search_control,
                    "u": SimpleNamespace(GetForegroundWindow=get_foreground,
                                         GetWindowThreadProcessId=get_owner),
                    "W": SimpleNamespace(DWORD=lambda: SimpleNamespace(value=0)),
                    "c": SimpleNamespace(byref=lambda value: value),
                    "p": SimpleNamespace(pid=42),
                }
                exec(compile(ast.Module(body=[function], type_ignores=[]),
                             "M19 search click", "exec"), namespace)
                click = namespace["click_search"]
                if owner == 42:
                    click("SearchRunButton")
                    self.assertEqual(["focus", "reveal", "foreground", "click"], events)
                else:
                    with self.assertRaisesRegex(AssertionError, "outside owned app"):
                        click("SearchRunButton")
                    self.assertEqual(["focus", "reveal", "foreground"], events)

    def test_m19_search_pointer_requires_stable_owned_target(self):
        from types import SimpleNamespace
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        names = {"clear_search_inside", "reveal_search_control",
                 "owned_search_pointer", "click_search"}
        functions = [node for node in ast.walk(ast.parse(gui))
                     if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(names, {node.name for node in functions})
        code = compile(ast.Module(body=functions, type_ignores=[]),
                       "M19 content regex pointer", "exec")

        cases = ("direct", "child", "clipped", "moving", "wrong-control",
                 "foreign-window", "foreign-peer", "disabled", "lost-hit",
                 "lost-foreground")
        scenarios = [(key, case) for key in ("SearchContentRegexBox", "SearchClearButton")
                     for case in cases]
        scenarios += [("SearchClearButton", case) for case in
                      ("margin-recovery", "narrow", "short", "edge", "lost-geometry",
                       "no-scroll-clipped", "wrap-recovery")]
        for key, case in scenarios:
            with self.subTest(key=key, case=case):
                calls = []
                state = SimpleNamespace(scroll=0, probes=0, hits=0)

                class Rect:
                    def __init__(self, top=0, bottom=100, left=0, right=100):
                        self.left, self.right, self.top, self.bottom = left, right, top, bottom
                    def width(self): return self.right - self.left
                    def height(self): return self.bottom - self.top

                class Peer:
                    def __init__(self, automation_id, pid=42, parent=None):
                        self.element_info = SimpleNamespace(automation_id=automation_id,
                                                            process_id=pid)
                        self._parent = parent
                    def parent(self): return self._parent

                target = Peer(key)
                panel_peer = Peer("SearchPanel")
                other = Peer("SearchScopeBox", parent=panel_peer)
                scroll = SimpleNamespace(CurrentVerticallyScrollable=case != "no-scroll-clipped")

                def set_scroll(horizontal, vertical):
                    self.assertEqual(-1, horizontal)
                    calls.append(("scroll", vertical))
                    state.scroll = vertical

                scroll.SetScrollPercent = set_scroll

                class Panel:
                    def exists(self, timeout): return True
                    def is_visible(self): return True
                    def rectangle(self): return Rect()
                    def wrapper_object(self): return SimpleNamespace(iface_scroll=scroll)

                class Item:
                    element_info = target.element_info
                    def exists(self, timeout): return True
                    def is_visible(self): return True
                    def is_enabled(self): return case != "disabled"
                    def rectangle(self):
                        if case == "moving" and state.probes == 2:
                            return Rect(30, 50, 2, 98)
                        if case == "narrow":
                            return Rect(20, 40, 40, 60)
                        if case == "short":
                            return Rect(25, 35, 2, 98)
                        if (case in ("edge", "no-scroll-clipped") or
                                (case == "margin-recovery" and state.scroll != 75) or
                                (case == "wrap-recovery" and len([v for v in calls if v[0] == "scroll"]) < 7) or
                                (case == "lost-geometry" and state.hits >= 2)):
                            return Rect(20, 40, 1, 99)
                        return Rect(20, 40, 2, 98)
                    def click_input(self): self_test.fail("unverified wrapper click")

                self_test = self
                panel, item = Panel(), Item()

                def element(name):
                    return panel if name == "SearchPanel" else item

                def good(probe, label, timeout):
                    self.assertEqual(8, timeout)
                    for _ in range(20):
                        state.probes += 1
                        result = probe()
                        if result:
                            return result
                    raise AssertionError(label)

                def window_at(point):
                    return 77 if case == "foreign-window" else 42

                def peer_at(x, y):
                    state.hits += 1
                    if case == "foreign-peer": return Peer("", 77)
                    if case == "wrong-control" or (case == "clipped" and
                            (state.scroll < 30 if key == "SearchContentRegexBox" else state.scroll != 75)):
                        return other
                    if case == "lost-hit" and state.hits >= 3: return other
                    if case == "child": return Peer("", parent=target)
                    return target

                def window_owner(hwnd, owner): owner.value = hwnd

                def mouse_click(button, coords):
                    self.assertEqual("left", button)
                    calls.append(("click", coords))

                # Function objects support ctypes signature attributes just
                # like the real user32 calls used by click_search.
                namespace = {"element": element, "good": good,
                             "focus": lambda: calls.append(("focus",)),
                             "p": SimpleNamespace(pid=42),
                             "u": SimpleNamespace(WindowFromPoint=window_at,
                                 GetForegroundWindow=lambda: 77 if case == "lost-foreground" else 42,
                                 GetWindowThreadProcessId=window_owner),
                             "W": SimpleNamespace(POINT=lambda *p: p, HWND=int,
                                 DWORD=lambda: SimpleNamespace(value=0)),
                             "c": SimpleNamespace(byref=lambda v: v),
                             "Desktop": lambda **kw: SimpleNamespace(from_point=peer_at),
                             "mouse": SimpleNamespace(click=mouse_click)}
                exec(code, namespace)
                if case in ("direct", "child", "clipped", "moving", "margin-recovery", "wrap-recovery"):
                    namespace["click_search"](key)
                    self.assertEqual([("click", (50, 30))],
                                     [v for v in calls if v[0] == "click"])
                    self.assertGreaterEqual(state.hits, 3)
                    if case in ("clipped", "margin-recovery"):
                        self.assertIn(("scroll", 30 if key == "SearchContentRegexBox" else 75), calls)
                    if case == "wrap-recovery":
                        self.assertEqual([100, 75, 85, 100, 65, 50, 75],
                                         [v[1] for v in calls if v[0] == "scroll"])
                    if case == "moving":
                        self.assertGreaterEqual(state.probes, 4)
                else:
                    with self.assertRaisesRegex(AssertionError,
                            "outside owned app|not stable or not on target|changed before click"):
                        namespace["click_search"](key)
                    self.assertFalse(any(v[0] == "click" for v in calls))

    def test_m19_content_regex_guards_inputs_and_result_transitions(self):
        from types import SimpleNamespace
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        names = {"set_content_regex", "content_regex_query"}
        functions = [node for node in ast.walk(ast.parse(gui))
                     if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(names, {node.name for node in functions})
        code = compile(ast.Module(body=functions, type_ignores=[]),
                       "M19 content regex contract", "exec")

        def exercise(initial=0, count="검색 결과 1개", *, missed_toggle=False,
                     missed_edit=False, lost_toggle=False, missed_run=False):
            state = SimpleNamespace(toggle=initial, value="needle", count=count,
                                    next_count=None, clicks=[])

            def edit(value):
                if not missed_edit:
                    state.value = value
                if lost_toggle:
                    state.toggle = 0

            def element(key):
                self.assertIn(key, ("SearchContentBox", "SearchContentRegexBox"))
                return SimpleNamespace(set_edit_text=edit, get_value=lambda: state.value,
                    wrapper_object=lambda: SimpleNamespace(
                        get_toggle_state=lambda: state.toggle))

            def click(key):
                state.clicks.append(key)
                if key == "SearchContentRegexBox" and not missed_toggle:
                    state.toggle = 1 - state.toggle
                if key == "SearchRunButton" and not missed_run:
                    state.count = state.next_count

            def good(predicate, why, timeout):
                self.assertTrue(predicate(), why)

            def text(key):
                self.assertEqual("SearchCountText", key)
                return state.count

            namespace = {"search_control": element, "element": element,
                         "click_search": click, "good": good, "text": text}
            exec(code, namespace)
            return state, namespace["set_content_regex"], namespace["content_regex_query"]

        state, toggle, query = exercise()
        toggle(1)
        for expected in (0, 1):
            state.next_count = f"검색 결과 {expected}개"
            query(str(expected), expected, "regex result")
        toggle(0)
        self.assertEqual(0, state.toggle)
        self.assertEqual(["SearchContentRegexBox", "SearchRunButton",
                          "SearchRunButton", "SearchContentRegexBox"], state.clicks)
        for initial, wanted, missed, error, clicks in (
                (1, 1, False, "unexpected initial toggle", []),
                (0, 1, True, "physical click not acknowledged", ["SearchContentRegexBox"]),
                (1, 0, True, "physical click not acknowledged", ["SearchContentRegexBox"])):
            with self.subTest(initial=initial, wanted=wanted, missed=missed):
                state, toggle, _ = exercise(initial, missed_toggle=missed)
                with self.assertRaisesRegex(AssertionError, error):
                    toggle(wanted)
                self.assertEqual(clicks, state.clicks)
        for options, error in (({"missed_edit": True}, "exact input not acknowledged"),
                               ({"lost_toggle": True}, "toggle not enabled")):
            with self.subTest(options=options):
                state, _, query = exercise(1, **options)
                with self.assertRaisesRegex(AssertionError, error):
                    query("new", 0, "regex result")
                self.assertEqual([], state.clicks)
        for previous, expected in ((1, 0), (0, 1)):
            with self.subTest(previous=previous, expected=expected):
                state, _, query = exercise(1, f"검색 결과 {previous}개", missed_run=True)
                with self.assertRaisesRegex(AssertionError, f"observed count:.*{previous}개"):
                    query("new", expected, "regex result")
                self.assertEqual(["SearchRunButton"], state.clicks)

        no_match = gui.index('content_regex_query(r"^Alpha\\s+Need(Missing|Absent)')
        match = gui.index('content_regex_query(r"^Alpha\\s+Need(Le|Missing)')
        self.assertLess(no_match, match)
        self.assertIn('assert not search_matches("content-utf8.txt")', gui[no_match:match])

    def test_m19_recent_clear_recovers_owned_scroll_without_click_bypass(self):
        gui = (TESTS / "test_m19_winui_features.py").read_text(encoding="utf-8")
        click = gui.split("def click_search(key):", 1)[1].split("def children():", 1)[0]
        self.assertIn('if key in ("SearchContentRegexBox", "SearchClearButton"):', click)
        self.assertLess(click.index("focus()"), click.index("scroll.SetScrollPercent(-1, 100)"))
        self.assertLess(click.index("scroll.SetScrollPercent(-1, 100)"),
                        click.index("reveal_search_control(element, good, key, pointer)"))
        self.assertLess(click.index("assert pointer(item) == point"),
                        click.index('mouse.click(button="left", coords=point)'))
        self.assertLess(click.index("owner.value == p.pid"),
                        click.index('mouse.click(button="left", coords=point)'))
        self.assertIn('M19_RECENT_CLEAR_POINTER_VERIFIED', click)
        clear = gui.split('click_search("SearchClearButton")', 1)[1].split(
            'print("REAL_M19_SEARCH_CLEAR_RETAINS_ACTIVE_FULL_SCOPE"', 1)[0]
        self.assertNotIn("click_input(", clear)
        self.assertNotIn("safe_click(", clear)
        self.assertNotIn("focus()", clear)
        self.assertIn('clear_positions = (75, 85, 100, 65, 50)', gui)
        self.assertIn('clear_search_inside(item, panel)', gui)

    def test_m19_recent_clear_reveals_owned_scope_without_weakening_persistence(self):
        gui = (TESTS / "test_m19_winui_features.py").read_text(
            encoding="utf-8")
        clear = gui.split('click_search("SearchClearButton")', 1)[1].split(
            'print("REAL_M19_SEARCH_CLEAR_RETAINS_ACTIVE_FULL_SCOPE"', 1)[0]
        for marker in (
            "M1.9 Clear recent click not acknowledged by owned WinUI",
            "M1.9 Clear recent action reported persistence failure",
            'recall.read_text(encoding="utf-16").strip()==""',
            'good(lambda:"저장 0개" in element("RecentCountText").window_text()',
            "if owned_scroll.CurrentVerticallyScrollable:",
            "owned_scroll.SetScrollPercent(-1, 0)",
            'element("SearchScopeBox").exists(timeout=.2)',
            'element("SearchScopeBox").is_visible()',
            'str(left).lower()==element("SearchScopeBox").get_value().lower()',
        ):
            self.assertIn(marker, clear)
        self.assertLess(clear.index('recall.read_text(encoding="utf-16")'),
                        clear.index('owned_scroll.SetScrollPercent(-1, 0)'))
        self.assertLess(clear.index('owned_scroll.SetScrollPercent(-1, 0)'),
                        clear.index('element("SearchScopeBox").exists(timeout=.2)'))
        self.assertLess(clear.index('element("SearchScopeBox").is_visible()'),
                        clear.index('assert str(left).lower()==element("SearchScopeBox").get_value().lower()'))
        self.assertNotIn('safe_click(', clear)

    def test_m19_recent_clear_scope_oracle_rejects_other_full_paths(self):
        gui = (TESTS / "test_m19_winui_features.py").read_text(
            encoding="utf-8")
        start = gui.index('click_search("SearchClearButton")')
        end = gui.index('print("REAL_M19_SEARCH_CLEAR_RETAINS_ACTIVE_FULL_SCOPE"')
        assertions = [node for node in ast.walk(ast.parse(gui))
                      if isinstance(node, ast.Assert)
                      and gui.count("\n", 0, start) < node.lineno
                      <= gui.count("\n", 0, end)
                      and 'SearchScopeBox' in ast.unparse(node.test)]
        self.assertEqual(1, len(assertions))
        # Exercise the actual GUI predicate without importing Windows/UIA.
        # A path containing the expected root is not that same full scope.
        predicate = compile(ast.Expression(assertions[0].test),
                            "M19 clear scope predicate", "eval")
        expected = r"C:\M19-owned\Left"
        for value, accepted in (
            (expected, True), (expected.upper(), True),
            (expected + "-other", False), (expected + r"\Nested", False),
            (r"D:\M19-owned\Left", False), (expected[:-1], False), ("", False),
        ):
            with self.subTest(scope=value):
                class ScopeBox:
                    def get_value(self):
                        return value

                def element(key):
                    self.assertEqual("SearchScopeBox", key)
                    return ScopeBox()

                actual = eval(predicate, {"__builtins__": {"str": str}},
                              {"left": expected, "element": element})
                self.assertEqual(accepted, actual)

    def test_virtual_shell_wait_requires_owned_drive_rows_and_stable_route(self):
        from types import SimpleNamespace
        gui = (TESTS / "test_shell_gui.py").read_text(encoding="utf-8")
        evidence = (TESTS / "gui_failure_evidence.py").read_text(encoding="utf-8")
        funcs = []
        for source, name in ((gui, "owned_virtual_drive_ready"),
                             (evidence, "_startup_status_category")):
            funcs.append(next(node for node in ast.parse(source).body
                              if isinstance(node, ast.FunctionDef) and node.name == name))
        namespace = {}
        exec(compile(ast.Module(body=funcs, type_ignores=[]),
                     "owned virtual route readiness", "exec"), namespace)
        ready = namespace["owned_virtual_drive_ready"]

        def peer(kind, pid=42, children=(), visible=True):
            return SimpleNamespace(
                element_info=SimpleNamespace(control_type=kind, process_id=pid),
                descendants=lambda: list(children), is_visible=lambda: visible)

        drive = peer("ListItem", children=[peer("ProgressBar")])
        local = peer("ListItem", children=[peer("Text")])
        foreign_row = peer("ListItem", 77, [peer("ProgressBar")])
        foreign_capacity = peer("ListItem", children=[peer("ProgressBar", 77)])
        hidden = peer("ListItem", children=[peer("ProgressBar")], visible=False)
        loaded = "폴더를 불러왔습니다."
        cases = (
            ("ready", "오른쪽", "내 PC", loaded, [drive], True),
            ("recovered", "오른쪽", "내 PC", "응답 지연 후 폴더를 불러왔습니다.", [drive], True),
            ("current-recovered", "오른쪽", "내 PC",
             "일시적인 오류 후 재시도하여 폴더를 불러왔습니다.", [drive], True),
            ("current-recovered-empty", "오른쪽", "내 PC",
             "일시적인 오류 후 재시도하여 폴더를 불러왔습니다.", [], False),
            ("current-recovery-incomplete", "오른쪽", "내 PC",
             "일시적인 오류 후 재시도하여 폴더를 불러오는 중입니다.", [drive], False),
            ("empty", "오른쪽", "내 PC", loaded, [], False),
            ("stale-local", "오른쪽", "내 PC", loaded, [local], False),
            ("loading", "오른쪽", "내 PC", "폴더를 불러오는 중입니다.", [drive], False),
            ("failure", "오른쪽", "내 PC", "Shell 폴더를 열지 못했습니다.", [drive], False),
            ("unknown", "오른쪽", "내 PC", "", [drive], False),
            ("wrong-pane", "왼쪽", "내 PC", loaded, [drive], False),
            ("wrong-route", "오른쪽", "other", loaded, [drive], False),
            ("foreign-row", "오른쪽", "내 PC", loaded, [foreign_row], False),
            ("foreign-child", "오른쪽", "내 PC", loaded, [foreign_capacity], False),
            ("hidden-row", "오른쪽", "내 PC", loaded, [hidden], False),
            ("decorative", "오른쪽", "내 PC", loaded, [peer("ProgressBar")], False),
        )
        for name, pane, address, status, rows, expected in cases:
            with self.subTest(name=name):
                controls = {
                    "ActivePaneText": SimpleNamespace(window_text=lambda: pane),
                    "AddressBox": SimpleNamespace(get_value=lambda: address),
                    "StatusText": SimpleNamespace(window_text=lambda: status),
                    "RightFiles": SimpleNamespace(descendants=lambda: rows),
                }
                self.assertEqual(expected, ready(controls.__getitem__, 42))

        # A route change while the UIA row tree is being inspected cannot
        # be promoted to success. A later poll can accept the new valid tree.
        addresses = iter(("내 PC", "other", "내 PC", "내 PC"))
        controls["ActivePaneText"] = SimpleNamespace(window_text=lambda: "오른쪽")
        controls["AddressBox"] = SimpleNamespace(get_value=lambda: next(addresses))
        controls["StatusText"] = SimpleNamespace(window_text=lambda: loaded)
        controls["RightFiles"] = SimpleNamespace(descendants=lambda: [drive])
        self.assertFalse(ready(controls.__getitem__, 42))
        self.assertTrue(ready(controls.__getitem__, 42))

        controls["AddressBox"] = SimpleNamespace(get_value=lambda: "내 PC")
        controls["RightFiles"] = SimpleNamespace(descendants=lambda: [])
        self.assertFalse(ready(controls.__getitem__, 42))
        controls["RightFiles"] = SimpleNamespace(descendants=lambda: [drive])
        self.assertTrue(ready(controls.__getitem__, 42))

        virtual = gui.split("# Exercise the ACTUAL native Windows Shell namespace:", 1)[1].split(
            " if loopback_unc:", 1)[0]
        self.assertIn('eventually(lambda:owned_virtual_drive_ready(element,p.pid)', virtual)
        self.assertIn('element("BackButton").is_enabled()', virtual)
        self.assertIn("and right_helper_ready()", virtual)
        self.assertIn('REAL_NATIVE_VIRTUAL_SHELL_THIS_PC_PIDL_AND_ENUMERATION', virtual)
        self.assertIn('REAL_NATIVE_VIRTUAL_TO_LOCAL_SHELL_HISTORY', virtual)
        self.assertNotIn('assert len(element("RightFiles").descendants())', virtual)

    def test_integrated_shell_gui_captures_owned_shutdown_stack_on_timeout(self):
        gui = (TESTS / "test_shell_gui.py").read_text(encoding="utf-8")
        self.assertIn("from owned_process_dump import capture_owned_dump", gui)
        self.assertIn('owned / "shutdown-evidence"', gui)
        self.assertIn('"OWNED_SHELL_SHUTDOWN_DUMP"', gui)
        timeout_body = gui.split("except subprocess.TimeoutExpired:", 1)[1].split(
            'raise RuntimeError("owned WinUI3 shell did not close normally")', 1
        )[0]
        self.assertLess(
            timeout_body.index("capture_owned_dump(p, EXE,"),
            timeout_body.index("p.terminate()"),
        )
        self.assertIn("p.wait(timeout=5)", timeout_body)
        self.assertIn('assert p and p.returncode==0', gui)

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
