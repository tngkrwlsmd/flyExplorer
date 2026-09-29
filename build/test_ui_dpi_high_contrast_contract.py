"""Static DPI/HC source contracts. Do not conflate with real monitor tests."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def src(rel):return (ROOT/rel).read_text(encoding="utf-8-sig")
class DpiContrastSource(unittest.TestCase):
 def test_runtime_dpi_source_and_scale_formula(self):
  ui=src("src/fxfile/gui/ModernUI.cpp")
  self.assertIn('::GetProcAddress(sUser32, "GetDpiForWindow")',ui)
  self.assertIn('::MulDiv(aValue, static_cast<xpr_sint_t>(aDpi), kDefaultDpi)',ui)
  self.assertIn("scale(aValue, getDpi(aHwnd))",ui)
  self.assertRegex(src("src/fxfile/gui/FlatHeaderCtrl.cpp"),
                   r"ON_MESSAGE\(WM_DPICHANGED,\s*OnDpiChanged\)")
  self.assertIn("WM_DPICHANGED",src("src/fxfile/address_bar.cpp"))
  self.assertIn("OnDpiChanged",src("src/fxfile/gui/ModernDialog.cpp"))
  self.assertIn("scaleForWindow(10, m_hWnd)",
                src("src/fxfile/cmd/column_set_dlg.cpp"))
 def test_source_only_dpi_boundary_math_matrix(self):
  # Matches signed Win32 MulDiv for these positive DPI-scaled constants.
  expected={96:(10,24,4096),120:(13,30,5120),
            144:(15,36,6144),192:(20,48,8192)}
  for dpi,triplet in expected.items():
   scaled=tuple((n*dpi+48)//96 for n in (10,24,4096))
   self.assertEqual(scaled,triplet)
 def test_hc_guards_cover_palette_scroll_header_popup(self):
  ui=src("src/fxfile/gui/ModernUI.cpp")
  header=src("src/fxfile/gui/FlatHeaderCtrl.cpp")
  address=src("src/fxfile/address_bar.cpp")
  column=src("src/fxfile/cmd/column_set_dlg.cpp")
  self.assertIn("SPI_GETHIGHCONTRAST",ui)
  self.assertIn("HCF_HIGHCONTRASTON",ui)
  self.assertIn("sPalette.mHighContrast",ui)
  self.assertIn("mHighContrast",header)
  self.assertIn("mHighContrast",address)
  self.assertIn("mHighContrast",column)
  self.assertIn("aPalette->mHighContrast",ui)
if __name__=="__main__":unittest.main()
