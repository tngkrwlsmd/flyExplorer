"""Mutation checks for Windows 11-like tab width without clipped narrow layouts."""
import unittest
from pathlib import Path
from validate_source_invariants import validate_explorer_tab_width_contract

SOURCE = (Path(__file__).resolve().parents[1] / "src/fxfile/gui/TabCtrl.cpp").read_text(encoding="utf-8")

class TabWidthContracts(unittest.TestCase):
    def test_updated_source(self):
        self.assertEqual([], validate_explorer_tab_width_contract(SOURCE))
    def assert_broken(self, original, replacement):
        self.assertIn(original, SOURCE)
        self.assertTrue(validate_explorer_tab_width_contract(SOURCE.replace(original,replacement,1)))
    def test_old_narrow_default_cannot_return(self):
        self.assert_broken("kDefaultTabSize     = 232;", "kDefaultTabSize     = 150;")
    def test_active_tab_cannot_overrun_small_frame(self):
        self.assert_broken("sCurrentTabSize = min(max(0, sWidth), sDefaultTabSize);",
                           "sCurrentTabSize = sDefaultTabSize;")
    def test_multi_tab_uses_bounded_active_width(self):
        self.assert_broken("(sWidth - sCurrentTabSize) /", "(sWidth - sDefaultTabSize) /")
    def test_new_button_space_is_preserved(self):
        self.assert_broken("sWidth -= sNewButtonIconSize.cx + sIconOffset * 2;",
                           "sWidth -= 0;")

if __name__ == "__main__":
    unittest.main()
