"""Bounded PX12 GUI acceptance must have positive real-Shell markers."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class Px12GuiChromeContract(unittest.TestCase):
    def test_dedicated_scoped_owned_shell_path(self):
        s = source("tests/winui/test_shell_gui.py")
        runner = source("tools/winui/run_checks.py")
        self.assertIn('FLY_PX12_ADDRESS_CHROME_ONLY', s)
        self.assertIn('from test_px12_address_chrome_gui import run', s)
        self.assertIn('PX12_ADDRESS_CANDIDATE_CHROME_GUI_PASS=True', s)
        self.assertIn('"address-candidate-chrome"', runner)
        self.assertIn('PX12_REQUIRED_OWNED_GUI_EVIDENCE_MISSING', runner)
        self.assertIn('OWNED_SYNTHETIC_FIXTURE_REMOVED True', runner)
    def test_real_candidate_and_failed_navigation_oracle(self):
        s = source("tests/winui/test_px12_address_chrome_gui.py")
        for fragment in ('stale.rmdir()', 'candidate(stale) is not None',
                         'item.iface_invoke.Invoke()', 'assert committed(left)',
                         '기존 폴더는 유지됩니다', 'PX12_GUI_VALID_CANDIDATE_NAVIGATED=PASS',
                         'PX12_GUI_FAILED_CANDIDATE_PANE_RETAINED=PASS',
                         'PX12_GUI_VALID_CANDIDATE_IMMEDIATE_CHROME=PASS',
                         'PX12_GUI_KEYBOARD_CANDIDATE_UP_DOWN=PASS',
                         'candidate(first).has_keyboard_focus()',
                         'candidate(second).has_keyboard_focus()'):
            self.assertIn(fragment, s)
        for banned in ('ImageGrab', 'SetFileAttributesW', 'net share',
                       'shutil.rmtree', 'os.system('):
            self.assertNotIn(banned, s)


if __name__ == "__main__":
    unittest.main()
