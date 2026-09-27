"""Mutations of native header layout and flat address palette must be detected."""
import unittest
from pathlib import Path
from validate_source_invariants import validate_header_address_surface
ROOT = Path(__file__).resolve().parents[1]

class HeaderAddressRules(unittest.TestCase):
    def test_source_invariants(self):
        self.assertEqual([],validate_header_address_surface())
    def test_native_layout_message_is_installed(self):
        s=(ROOT/"src/fxfile/gui/FlatHeaderCtrl.cpp").read_text(encoding="utf-8")
        self.assertIn("ON_MESSAGE(HDM_LAYOUT, OnHeaderLayout)",s)
    def test_list_view_content_tracks_header(self):
        s=(ROOT/"src/fxfile/gui/FlatHeaderCtrl.cpp").read_text(encoding="utf-8")
        self.assertIn("sLayout->prc->top += sRequiredHeight - sNativeHeight;",s)
    def test_dpi_and_font_height_are_measured(self):
        s=(ROOT/"src/fxfile/gui/FlatHeaderCtrl.cpp").read_text(encoding="utf-8")
        self.assertIn("sMetrics.tmHeight + sMetrics.tmExternalLeading",s)
        self.assertIn("scale(28, sDpi)",s)
    def test_address_uses_single_palette(self):
        s=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertEqual(0,s.count("sPalette.mElevated"))
        self.assertGreaterEqual(s.count("sPalette.mChrome"),5)
    def test_native_high_contrast_mode_remains(self):
        s=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertIn("if (XPR_IS_TRUE(sPalette.mHighContrast))",s)
        self.assertIn("return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);",s)
if __name__=="__main__":unittest.main()
