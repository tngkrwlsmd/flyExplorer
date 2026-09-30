"""Mutations guarding native back/forward/up visual target and user modes."""
import unittest
from pathlib import Path
from validate_source_invariants import validate_phase3_navigation_visual
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src/fxfile/gui/rebar/ToolBarEx.cpp").read_text(encoding="utf-8")
class Phase3NavigationTests(unittest.TestCase):
    def test_new_source(self):
        self.assertEqual([],validate_phase3_navigation_visual(SOURCE))
    def assert_broken(self,old,new):
        self.assertIn(old,SOURCE)
        self.assertTrue(validate_phase3_navigation_visual(SOURCE.replace(old,new,1)))
    def test_not_user_bookmark_or_drive_bars(self):
        self.assert_broken("::GetDlgCtrlID(aToolbar) == AFX_IDW_TOOLBAR",
                           "::GetDlgCtrlID(aToolbar) != 0")
    def test_three_nav_commands_retained(self):
        for cmd in ("ID_GO_BACK","ID_GO_FORWARD","ID_GO_UP"):
            with self.subTest(cmd=cmd):
                self.assert_broken("aCommandId == "+cmd,"aCommandId == 0")
    def test_native_dropdown_preserved(self):
        self.assert_broken("aItem.right - aItem.left - sDrop",
                           "aItem.right - aItem.left")
    def test_hot_background_not_over_user_label(self):
        self.assert_broken("aCustomDraw->nmcd.rc = sNavTile;",
                           "aCustomDraw->nmcd.rc = sItemRect;")
    def test_label_clears_navigation_icon(self):
        self.assert_broken("sNavTile.right +","sItemRect.left +")
    def test_nav_label_keeps_chrome_background(self):
        self.assert_broken(
            "XPR_IS_TRUE(sPrimaryNavVisual) ? aBackground : sItemBackground",
            "sItemBackground")
    def test_history_arrow_hover_separate_from_icon(self):
        self.assert_broken("::PtInRect(&sDropRect, sCursor)",
                           "FALSE")
    def test_below_icon_text_stays_original(self):
        self.assert_broken("XPR_IS_TRUE(sText) && XPR_IS_FALSE(sList)",
                           "XPR_IS_FALSE(sText) && XPR_IS_FALSE(sList)")
if __name__=="__main__":unittest.main()
