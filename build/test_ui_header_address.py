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
    def test_round_address_frame_and_native_combo_repaint(self):
        s=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertIn("ModernUI::getControlCornerRadius(aHwnd)",s)
        self.assertIn("::ExtSelectClipRgn(sDC, sRounded, RGN_DIFF)",s)
        self.assertEqual(3,s.count("PaintRoundedAddressFrame("))
    def test_rounded_address_never_overrides_high_contrast(self):
        s=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertIn("XPR_IS_TRUE(aPalette.mHighContrast)",s)
        self.assertIn("PaintRoundedAddressFrame(m_hWnd, sPalette);",s)
    def test_native_high_contrast_mode_remains(self):
        s=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertIn("if (XPR_IS_TRUE(sPalette.mHighContrast))",s)
        self.assertIn("return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);",s)
    def test_address_dropdown_uses_dark_palette_for_native_items(self):
        s = (ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        item = s.split("AddressBar::drawDarkDropdownItem(", 1)[1].split(
            "AddressBar::OuterSubclassProc(", 1)[0]
        self.assertIn("CBEIF_TEXT | CBEIF_IMAGE", item)
        self.assertIn("sPalette.mChrome", item)
        self.assertIn("sPalette.mSelection", item)
        self.assertIn("sPalette.mText", item)
        self.assertIn("sPalette.mHighContrast", item)
        self.assertIn("ODS_COMBOBOXEDIT", item)

    def test_address_dropdown_reuses_scrollbar_overlay_without_replacing_input(self):
        cpp = (ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        header = (ROOT/"src/fxfile/address_bar.h").read_text(encoding="utf-8")
        section = cpp.split("void AddressBar::installDropdownSubclass(",1)[1].split(
            "void AddressBar::removeDropdownSubclass(",1)[0]
        self.assertIn("::GetComboBoxInfo(", section)
        self.assertIn("::SetWindowSubclass(", section)
        self.assertIn("configureDarkScrollbarOverlay(", section)
        self.assertIn("sPalette.mHighContrast", section)
        self.assertIn("case CB_SHOWDROPDOWN:",cpp)
        self.assertIn("removeDarkScrollbarOverlay(mDropdownHwnd)",cpp)
        self.assertIn("mDropdownHwnd",header)

    def test_address_popup_topmost_overlay_is_scoped_and_cleans_up(self):
        header=(ROOT/"src/fxfile/gui/ModernUI.h").read_text(encoding="utf-8")
        renderer=(ROOT/"src/fxfile/gui/ModernUI.cpp").read_text(encoding="utf-8")
        address=(ROOT/"src/fxfile/address_bar.cpp").read_text(encoding="utf-8")
        self.assertIn("aPopupTopMost = XPR_FALSE",header)
        self.assertIn("aPopupTopMost ? HWND_TOPMOST : HWND_TOP",renderer)
        self.assertIn("WM_SHOWWINDOW && !aWParam",address)
        self.assertIn("removeDarkScrollbarOverlay(aHwnd)",address)

if __name__=="__main__":unittest.main()
