"""Static F05 actual-GUI acceptance scope; NOT a Windows GUI result."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = (ROOT / 'tests/winui/test_shell_gui.py').read_text(encoding='utf-8')
PROBE = (ROOT / 'tests/winui/test_f05_group_modes_gui.py').read_text(encoding='utf-8')
TOOLBAR = (ROOT / 'app/winui/FileToolbar.xaml').read_text(encoding='utf-8')


class F05FourModesHarnessContract(unittest.TestCase):
    def test_owned_opt_in_and_exit_before_default_suite(self):
        for token in ('FLY_F05_MODES_ONLY', 'from test_f05_group_modes_gui import run',
                      'F05_FOUR_MODES_AND_TAB_GUI_PASS=True'):
            self.assertIn(token, HARNESS)
        self.assertIn('FLY_F05_PANES_ONLY', HARNESS)
        self.assertIn('raise SystemExit(0)', HARNESS)


    def test_live_owned_menu_keyboard_and_four_modes(self):
        for name in ('ViewGroupByTypeItem', 'ViewGroupByNameItem',
                     'ViewGroupBySizeItem', 'ViewGroupByMonthItem'):
            self.assertIn(name, TOOLBAR)
            self.assertIn(name, PROBE)
        for token in ('WindowFromPoint', 'owned_foreground()',
                      'menu.set_focus()', 'keyboard.send_keys("{ENTER}")',
                      'F05_GUI_GROUP_NAME=PASS', 'F05_GUI_GROUP_SIZE=PASS',
                      'F05_GUI_GROUP_MODIFIED_MONTH=PASS',
                      'F05_GUI_PER_TAB_COLLAPSE_RESTORED=PASS',
                      'F05_GUI_GROUP_EXPLICIT_OFF=PASS'):
            self.assertIn(token, PROBE)

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
