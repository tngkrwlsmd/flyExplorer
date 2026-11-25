"""Persistent pane filter preset source contracts."""
from pathlib import Path
import unittest
import re
import ast
import ctypes as c
from ctypes import wintypes as W
from types import SimpleNamespace
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class FilterPresetContracts(unittest.TestCase):
    def test_private_bounded_atomic_store(self):
        h=read("src/base/filter_rule_store.h")
        cpp=read("src/base/filter_rule_store.cpp")
        for token in (
            "kMaxItems = 20","kMaxName = 56","kMaxMasks = 260",
            "filter-rules-v1.txt","MOVEFILE_REPLACE_EXISTING",
            "MOVEFILE_WRITE_THROUGH","FILE_ATTRIBUTE_REPARSE_POINT",
        ):
            self.assertIn(token,h+cpp)
        self.assertNotIn("FileFilter.item",cpp)
        self.assertIn('GetEnvironmentVariableW(\n        L"LOCALAPPDATA"',cpp)

    def test_filter_keeps_substring_and_adds_bounded_masks(self):
        cpp=read("src/base/filter_rule_store.cpp")
        app=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn('expression.find_first_of(L"*?;")',cpp)
        self.assertIn("wildcardMatch",cpp)
        self.assertIn("std::search(filename.begin()",cpp)
        self.assertIn("fxfile::filterrules::Store::matches(",app)
        self.assertNotIn("std::search(label.begin()",app)

    def test_manager_is_user_visible_and_panel_exclusive(self):
        xaml=read("app/winui/MainWindow.xaml")
        features=read("app/winui/filter_rule_features.cpp")
        m19=read("app/winui/m19_features.cpp")
        bookmarks=read("app/winui/bookmark_features.cpp")
        for key in (
            "FilterRulePanelButton","FilterRulePanel","FilterRuleManagerBox",
            "FilterRuleNameEdit","FilterRuleMasksEdit","FilterRuleSaveButton",
            "FilterRuleApplyButton","FilterRuleDeleteButton",
        ):
            self.assertIn('x:Name="'+key+'"',xaml)
        self.assertIn("OnToggleFilterRules",features)
        self.assertIn("FilterRulePanel().Visibility(Visibility::Collapsed)",m19)
        self.assertIn("FilterRulePanel().Visibility(Visibility::Collapsed)",bookmarks)

    def test_visual_style_persistence_and_row_classification(self):
        h=read("src/base/filter_rule_store.h")
        cpp=read("src/base/filter_rule_store.cpp")
        xaml=read("app/winui/MainWindow.xaml")
        app=read("app/winui/MainWindow.xaml.cpp")
        features=read("app/winui/filter_rule_features.cpp")
        for token in ('kMaxColor = 4','kMaxIcon = 4','schema=2',
                      'schema=1','item.color,item.icon','colorText.size()!=1'):
            self.assertIn(token,h+cpp)
        for name in ("FilterRuleColorBox","FilterRuleIconBox"):
            self.assertIn('x:Name="'+name+'"',xaml)
            self.assertIn(name+"().SelectedIndex(",features)
        self.assertIn("fxfile::filterrules::Store::matches(itemLabel,rule.masks)",app)
        self.assertIn("필터 분류 아이콘",app)
        self.assertIn("FillFiles(0);FillFiles(1)",features)

    def test_light_theme_filename_accent_contrast(self):
        app=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("RootShell().ActualTheme()==ElementTheme::Light",app)
        matches=re.findall(
            r"case ([1-4]):value=light\?Windows::UI::Color\{255,(\d+),(\d+),(\d+)\}",
            app)
        self.assertEqual(len(matches),4,"expected four real light-theme colors")
        self.assertEqual({int(x[0]) for x in matches},{1,2,3,4})
        def channel(x):
            c=int(x)/255
            return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
        for style,r,g,b in matches:
            lum=.2126*channel(r)+.7152*channel(g)+.0722*channel(b)
            self.assertGreaterEqual((1.05)/(lum+.05),4.5,
                                    "light-theme style "+style)

    def test_high_contrast_uses_system_foreground_not_decorative_rgb(self):
        app=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("HIGHCONTRASTW contrast{}",app)
        self.assertIn("SPI_GETHIGHCONTRAST",app)
        self.assertIn("HCF_HIGHCONTRASTON",app)
        self.assertIn("const bool allowDecorativeColor=",app)
        self.assertIn(
            "if(allowDecorativeColor&&decoratedRule&&decoratedRule->color)",app)
        self.assertIn("if(accent)badge.Foreground(accent)",app)
        self.assertIn("if(accent)filename.Foreground(accent)",app)

    def test_screen_reader_ui_a_rule_color_icon_semantics(self):
        app=read("app/winui/MainWindow.xaml.cpp")
        xaml=read("app/winui/MainWindow.xaml")
        self.assertIn("kFilterColors",app)
        self.assertIn("kFilterIcons",app)
        for token in ("필터 프리셋: ", "분류 색상: ", "분류 아이콘: ",
                      "필터 분류 아이콘: "):
            self.assertIn(token,app)
        self.assertIn("row,hstring(label)",app)
        self.assertIn('AutomationProperties.Name="필터 규칙 분류 색상"',xaml)
        self.assertIn('AutomationProperties.Name="필터 규칙 분류 아이콘"',xaml)

    def test_project_and_native_fixture_include_store(self):
        project=read("app/winui/flyExplorer.project-template.xml")
        native=read("tests/winui/m20/m20_native_fixture.cpp")
        m20=read("tests/winui/m20/FlyM20StateContracts.project-template.xml")
        for token in ("filter_rule_store.h","filter_rule_store.cpp"):
            self.assertIn(token,project)
            self.assertIn(token,m20)
        for marker in (
            "filter_rule_literal_substring_compat",
            "filter_rule_wildcard_set_case_insensitive",
            "filter_rule_atomic_save_reload",
            "filter_rule_bounded_20_items",
        ):
            self.assertIn(marker,native)

# Parse only the owned GUI helpers; never import or execute the fixture.
class _FilterRect:
    def __init__(self, left=10, top=20, right=110, bottom=60):
        self.left, self.top, self.right, self.bottom = left, top, right, bottom

    def width(self):
        return self.right - self.left

    def height(self):
        return self.bottom - self.top


class OwnedFilterInputContracts(unittest.TestCase):
    def setUp(self):
        source = ROOT / "tests/winui/test_filter_preset_gui.py"
        self.tree = ast.parse(source.read_text(encoding="utf-8-sig"))
        names = {"window_owner", "require_foreground", "owned_control",
                 "click_owned", "send_owned_keys", "open_filter_panel",
                 "close_owned", "launch"}
        functions = [n for n in self.tree.body
                     if isinstance(n, ast.FunctionDef) and n.name in names]
        self.assertEqual({n.name for n in functions}, names)
        self.u = Mock()
        self.u.GetForegroundWindow.return_value = 101
        self.u.WindowFromPoint.return_value = 102
        self.u.GetAncestor.return_value = 101
        self.owners = {101: 44, 102: 44}
        def owner(hwnd, out):
            pid = self.owners.get(hwnd, 0)
            out._obj.value = pid
            return int(bool(pid))
        self.u.GetWindowThreadProcessId.side_effect = owner
        self.proc = Mock(pid=44, returncode=0)
        self.proc.poll.return_value = None
        self.win = Mock()
        self.win.rectangle.return_value = _FilterRect(0, 0, 200, 200)
        self.win.element_info.process_id = 44
        self.button = Mock()
        self.button.exists.return_value = True
        self.button.is_enabled.return_value = True
        self.button.is_visible.return_value = True
        self.button.rectangle.return_value = _FilterRect()
        self.button.element_info.process_id = 44
        self.button.has_keyboard_focus.return_value = True
        self.win.child_window.return_value = self.button
        self.keyboard = Mock()
        self.ns = {"c": c, "W": W, "u": self.u,
                   "keyboard": self.keyboard, "print": Mock()}
        exec(compile(ast.Module(body=functions, type_ignores=[]),
                     str(source), "exec"), self.ns)

    def call(self, name, *args):
        return self.ns[name](*args)

    def click(self):
        return self.call("click_owned", self.win, self.proc, 101,
                         "FilterRulePanelButton")

    def test_click_checks_exact_center_before_single_dispatch(self):
        self.click()
        self.button.click_input.assert_called_once_with(coords=(50, 20))
        point = self.u.WindowFromPoint.call_args.args[0]
        self.assertEqual((point.x, point.y), (60, 40))

    def test_foreign_stale_hidden_and_outside_controls_never_click(self):
        cases = (
            ("foreground", lambda: setattr(self.u.GetForegroundWindow, "return_value", 999)),
            ("window_reused", lambda: self.owners.__setitem__(101, 55)),
            ("dead_process", lambda: setattr(self.proc.poll, "return_value", 0)),
            ("foreign_control", lambda: setattr(self.button.element_info, "process_id", 55)),
            ("hidden", lambda: setattr(self.button.is_visible, "return_value", False)),
            ("disabled", lambda: setattr(self.button.is_enabled, "return_value", False)),
            ("missing", lambda: setattr(self.button.exists, "return_value", False)),
            ("outside", lambda: setattr(self.button.rectangle, "return_value", _FilterRect(0, 0, 201, 60))),
            ("foreign_hit", lambda: self.owners.__setitem__(102, 55)),
            ("other_window", lambda: setattr(self.u.GetAncestor, "return_value", 103)),
            ("focus_race", lambda: setattr(self.u.GetForegroundWindow, "side_effect", [101, 999])),
        )
        for label, change in cases:
            with self.subTest(label=label):
                self.setUp()
                change()
                with self.assertRaises(AssertionError):
                    self.click()
                self.button.click_input.assert_not_called()

    def test_input_exception_does_not_replay_click(self):
        self.button.click_input.side_effect = RuntimeError("synthetic input error")
        with self.assertRaises(RuntimeError):
            self.click()
        self.button.click_input.assert_called_once()

    def manager(self, exists, visible=True, pid=44):
        manager = Mock()
        manager.exists.side_effect = exists
        manager.is_visible.return_value = visible
        manager.element_info.process_id = pid
        self.win.child_window.side_effect = lambda auto_id: (
            manager if auto_id == "FilterRuleManagerBox" else self.button)
        return manager

    def test_panel_success_keeps_five_second_observation(self):
        manager = self.manager([False, True])
        self.call("open_filter_panel", self.win, self.proc, 101)
        self.button.click_input.assert_called_once()
        self.assertEqual(manager.exists.call_args_list[-1].kwargs, {"timeout": 5})

    def test_absent_or_already_open_panel_does_not_retry(self):
        self.manager([False, False])
        with self.assertRaisesRegex(AssertionError, "PANEL_NOT_OBSERVED_AFTER_CLICK"):
            self.call("open_filter_panel", self.win, self.proc, 101)
        self.button.click_input.assert_called_once()
        self.setUp()
        self.manager([True])
        with self.assertRaisesRegex(AssertionError, "PANEL_ALREADY_OPEN"):
            self.call("open_filter_panel", self.win, self.proc, 101)
        self.button.click_input.assert_not_called()

    def test_hidden_and_foreign_manager_do_not_pass(self):
        for visible, pid in ((False, 44), (True, 55)):
            with self.subTest(visible=visible, pid=pid):
                self.setUp()
                self.manager([False, True], visible, pid)
                with self.assertRaisesRegex(AssertionError, "MANAGER_NOT_VISIBLE_OWNED"):
                    self.call("open_filter_panel", self.win, self.proc, 101)
                self.button.click_input.assert_called_once()

    def test_keys_and_close_require_live_owned_window(self):
        self.call("send_owned_keys", self.proc, 101, "{ENTER}", self.button)
        self.keyboard.send_keys.assert_called_once_with("{ENTER}")
        self.keyboard.send_keys.reset_mock()
        self.button.has_keyboard_focus.return_value = False
        with self.assertRaises(AssertionError):
            self.call("send_owned_keys", self.proc, 101, "{ENTER}", self.button)
        self.keyboard.send_keys.assert_not_called()
        self.u.GetForegroundWindow.return_value = 999
        with self.assertRaises(AssertionError):
            self.call("send_owned_keys", self.proc, 101, "^+f")
        self.keyboard.send_keys.assert_not_called()
        self.owners[101] = 55
        with self.assertRaises(AssertionError):
            self.call("close_owned", self.proc, 101)
        self.u.PostMessageW.assert_not_called()

    def test_failed_launch_is_tracked_for_cleanup(self):
        launched = []
        self.ns.update(subprocess=SimpleNamespace(Popen=Mock(return_value=self.proc), DEVNULL=-1),
                       EXE=Path("owned.exe"), folder=Path("fixture"), env={},
                       launched=launched, until=Mock(side_effect=AssertionError("startup failed")))
        with self.assertRaisesRegex(AssertionError, "startup failed"):
            self.call("launch")
        self.assertEqual(launched, [self.proc])

    def test_physical_input_and_owned_process_cleanup_remain_guarded(self):
        parents = {child: parent for parent in ast.walk(self.tree)
                   for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"click_input", "send_keys", "PostMessageW"}):
                cursor = node
                while cursor in parents and not isinstance(cursor, ast.FunctionDef):
                    cursor = parents[cursor]
                self.assertIsInstance(cursor, ast.FunctionDef)
                self.assertIn(cursor.name, {"click_owned", "send_owned_keys", "close_owned"})
        cleanup = next(n.finalbody for n in self.tree.body
                       if isinstance(n, ast.Try) and n.finalbody)
        self.assertTrue(any(isinstance(n, ast.For) and isinstance(n.iter, ast.Name)
                            and n.iter.id == "launched" for n in cleanup))


if __name__=="__main__":
    unittest.main()
