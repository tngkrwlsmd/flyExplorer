"""Static F05 actual-GUI acceptance scope; NOT a Windows GUI result."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = (ROOT / 'tests/winui/test_shell_gui.py').read_text(encoding='utf-8')
PROBE = (ROOT / 'tests/winui/test_f05_group_modes_gui.py').read_text(encoding='utf-8')
TOOLBAR = (ROOT / 'app/winui/FileToolbar.xaml').read_text(encoding='utf-8')
WINUI = (ROOT / 'app/winui/MainWindow.xaml.cpp').read_text(encoding='utf-8')
HEADER = (ROOT / 'app/winui/MainWindow.xaml.h').read_text(encoding='utf-8')


class F05FourModesHarnessContract(unittest.TestCase):
    def test_owned_opt_in_and_exit_before_default_suite(self):
        for token in ('FLY_F05_MODES_ONLY', 'from test_f05_group_modes_gui import run',
                      'F05_FOUR_MODES_AND_TAB_GUI_PASS=True'):
            self.assertIn(token, HARNESS)
        self.assertIn('FLY_F05_PANES_ONLY', HARNESS)
        self.assertIn('focus=ensure_owned_focus', HARNESS)
        self.assertIn('FLY_F05_VISUAL_BASELINE_ONLY', HARNESS)
        self.assertIn('F05_VISUAL_BASELINE_GUI_PASS=True', HARNESS)
        self.assertIn('F05_VISUAL_BASELINE_ONLY=PASS', PROBE)
        self.assertIn('if capture and os.environ.get(', PROBE)
        self.assertIn('raise SystemExit(0)', HARNESS)


    def test_live_owned_menu_keyboard_and_four_modes(self):
        for name in ('ViewGroupByTypeItem', 'ViewGroupByNameItem',
                     'ViewGroupBySizeItem', 'ViewGroupByMonthItem'):
            self.assertIn(name, TOOLBAR)
            self.assertIn(name, PROBE)
        for token in ('WindowFromPoint', 'owned_foreground()',
                      'menu.set_focus()', 'keyboard.send_keys("{ENTER}")',
                      'focus()', 'Refusing View flyout keys outside',
                      'F05_GUI_GROUP_NAME=PASS', 'F05_GUI_GROUP_SIZE=PASS',
                      'F05_GUI_GROUP_MODIFIED_MONTH=PASS',
                      'F05_GUI_PER_TAB_COLLAPSE_RESTORED=PASS',
                      'F05_GUI_GROUP_EXPLICIT_OFF=PASS'):
            self.assertIn(token, PROBE)

    def test_keyboard_only_disclosure_has_scoped_foreground_guards(self):
        for token in ('FLY_F05_KEYBOARD_DISCLOSURE_ONLY',
                      'assert os.environ.get("FLY_F05_MODES_ONLY")=="YES"',
                      'F05_KEYBOARD_DISCLOSURE_GUI_PASS=True'):
            self.assertIn(token, HARNESS)
        for token in ('assert not capture', 'set_mode("Type")',
                      'disclosure.set_focus()', 'owned_foreground()',
                      'keyboard.send_keys("{SPACE}")',
                      'keyboard.send_keys("{ENTER}")',
                      'F05_KEYBOARD_SPACE_COLLAPSE=PASS',
                      'F05_KEYBOARD_ENTER_EXPAND=PASS'):
            self.assertIn(token, PROBE)
        self.assertNotIn('ImageGrab.grab(', PROBE)

    def test_visual_capture_is_test_owned_and_explicit(self):
        for token in ('FLY_F05_VISUAL_CAPTURE', 'FLY_F05_VISUAL_THEME',
                      'theme in ("light", "dark")',
                      'FLY_F05_OWNED_XAML_VISUAL_DIR',
                      'f05-visual-modes', 'GetDpiForWindow(',
                      'Image.frombytes(', 'struct.unpack_from(',
                      'img.getextrema()', 'Image.alpha_composite(',
                      'DIAGNOSTIC_COMPOSITE_NOT_REAL_BACKDROP=True',
                      'F05_VISUAL_CAPTURE='):
            self.assertIn(token, HARNESS + PROBE)
        self.assertIn('assert os.environ.get("FLY_F05_MODES_ONLY")=="YES"',
                      HARNESS)
        self.assertIn('settings=localdata/"flyExplorer"', HARNESS)
        # The preference parser is CRLF-oriented; Python must emit actual
        # CRLF bytes, not escaped backslash-r/backslash-n text.
        self.assertIn(r'schema=3\r\nlanguage=ko-KR\r\ntheme=', HARNESS)
        self.assertNotIn(r'schema=3\\r\\nlanguage=ko-KR', HARNESS)
        self.assertIn('not visual_dir.is_symlink()', PROBE)
        self.assertIn('png.relative_to(ROOT)', PROBE)
        self.assertIn('RenderTargetBitmap rendered', WINUI)
        self.assertIn('InitializeOwnedF05VisualCaptureTest();', WINUI)
        for token in ('FLY_F05_OWNED_XAML_VISUAL_DIR',
                      'ScheduleOwnedF05VisualCapture',
                      'L"\\\\logs\\\\f05-visual-modes\\\\"',
                      'L"tab-restored"', 'L"collapsed"'):
            self.assertIn(token, WINUI)
        self.assertIn('mOwnedF05VisualCaptureDirectory', HEADER)
        self.assertNotIn('ImageGrab.grab(', PROBE)

    def test_group_pixels_can_be_scoped_without_foreground_input(self):
        for token in ('FLY_F05_VISUAL_GROUP_MODE_ONLY',
                      'FLY_F05_OWNED_XAML_VISUAL_GROUP_MODE',
                      'visual_group in ("type","name","size","month")',
                      'F05_VISUAL_GROUP_FIXTURE_GUI_PASS=True'):
            self.assertIn(token, HARNESS)
        for token in ('F05_VISUAL_GROUP_FIXTURE_MODE=',
                      'PASS_NO_PHYSICAL_INPUT=True',
                      'screenshot(mode)', 'Owned visual fixture group headings'):
            self.assertIn(token, PROBE)
        for token in ('FLY_F05_OWNED_XAML_VISUAL_GROUP_MODE',
                      'shell-owned-', 'snapshot.children.size()!=6',
                      'tab.fileLists[0].metadataCurrent',
                      'mOwnedF05VisualGroupTimer',
                      'ui->ToggleGroupMode(choice)'):
            self.assertIn(token, WINUI)
        self.assertIn('mOwnedF05VisualGroupTimer', HEADER)
        # App-side Type grouping may precede the Python baseline check.
        self.assertIn('FLY_F05_VISUAL_GROUP_MODE_ONLY") == "type"', PROBE)
        self.assertIn('assert heading(".md") is None', PROBE)
        # Physical View-menu checks remain distinct from test-only
        # app-side group presentation, never report them as the same gate.
        self.assertIn('F05_FOUR_MODES_AND_TAB_GUI_PASS=True', HARNESS)
        self.assertIn('keyboard.send_keys("{ENTER}")', PROBE)

    def test_physical_type_diagnostic_uses_separate_owned_right_route(self):
        # Never mix app-side grouping with the explicit View-menu route.
        for token in ('FLY_F05_SCREEN_PHYSICAL_TYPE_ONLY',
                      'assert not os.environ.get("FLY_F05_VISUAL_GROUP_MODE_ONLY")',
                      'F05_PHYSICAL_TYPE_DIAGNOSTIC_GUI_PASS=True'):
            self.assertIn(token, HARNESS)
        for token in ('F05_PHYSICAL_TYPE_INITIAL_RIGHT_ITEMS=',
                      'F05_PHYSICAL_TYPE_EXPLICIT_RIGHT_NAV=PASS',
                      'F05_PHYSICAL_TYPE_MENU_GROUPING_AND_SCREEN=PASS',
                      'safe_click(right_control)', 'Secondary',
                      'address.type_keys("{ENTER}"',
                      'set_mode("Type")', 'screenshot("type")'):
            self.assertIn(token, PROBE)

    def test_optional_real_screen_capture_is_scoped_and_fail_closed(self):
        from owned_f05_compositor import capture_box
        self.assertIn('FLY_F05_SCREEN_WINDOW_CAPTURE', HARNESS)
        self.assertIn('FLY_F05_VISUAL_CAPTURE', HARNESS)
        self.assertIn('FLY_F05_VISUAL_GROUP_MODE_ONLY', HARNESS)
        self.assertIn('from owned_f05_compositor import attempt_capture', PROBE)
        self.assertIn('owned_right_pane_ready()', PROBE)
        self.assertIn('element("RightFiles")', PROBE)
        self.assertIn('Zebra-large.log', PROBE)
        self.assertIn('Right pane synthetic files not ready for screen pixels',
                      PROBE)
        self.assertNotIn('ImageGrab.grab(', PROBE)
        helper = (ROOT / 'tests/winui/owned_f05_compositor.py').read_text(
            encoding='utf-8')
        for guard in ('owned_foreground()', 'GetWindowThreadProcessId',
                      'WindowFromPoint', 'BLOCKED_NONOWNED_OVERLAY',
                      'BLOCKED_BLANK_SCREEN_PIXEL_API',
                      'PIXELS_ONLY_NEEDS_VISUAL_REVIEW',
                      'include_layered_windows=True'):
            self.assertIn(guard, helper)
        self.assertNotIn('ImageGrab.grab()', helper)
        self.assertEqual(capture_box((40, 30, 980, 540), 1024, 768),
                         (40, 30, 980, 540))
        for invalid in ((-1, 20, 940, 540), (40, 30, 1060, 540),
                        (40, 30, 300, 300), (40, 30, 980, 800)):
            with self.subTest(box=invalid), self.assertRaises(ValueError):
                capture_box(invalid, 1024, 768)

    def test_files_owned_and_no_global_changes(self):
        for token in ('left / name', 'left.parent == right.parent',
                      'Mango-medium.md', 'Alpha-small.txt'):
            self.assertIn(token, PROBE)
        for bad in ('SetProcessDpiAwarenessContext', 'SetFileAttributesW',
                    'SystemParametersInfoW', 'SHEmptyRecycleBin',
                    'ClearClipboard', 'SetSystemColors'):
            self.assertNotIn(bad, PROBE)


if __name__ == '__main__':
    unittest.main()
