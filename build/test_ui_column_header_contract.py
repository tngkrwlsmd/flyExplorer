"""The column dialog must use native dark header and visible width editing."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def source(name):return (ROOT/name).read_text(encoding="utf-8-sig")
class NativeColumnHeader(unittest.TestCase):
 def test_dialog_has_persistent_native_flat_header(self):
  header=source("src/fxfile/cmd/column_set_dlg.h")
  body=source("src/fxfile/cmd/column_set_dlg.cpp")
  self.assertIn("FlatHeaderCtrl mColumnHeader;",header)
  self.assertIn("mColumnHeader.SubclassWindow(",body)
  self.assertIn("mColumnHeader.initHeader(XPR_FALSE)",body)
  self.assertIn("HDS_FULLDRAG",body)
  self.assertIn("enableResizeGripHints(XPR_TRUE)",body)
 def test_grips_preserve_native_resize_and_high_contrast(self):
  body=source("src/fxfile/gui/FlatHeaderCtrl.cpp")
  for term in ("mResizeGripHints","mHighContrast","sPalette.mSecondaryText",
               "sSeparatorRect", "sGrip"):
   self.assertIn(term,body)
  self.assertIn("drawFlatBorder",body)
 def test_numeric_edit_uses_theme_focus_and_better_geometry(self):
  cpp=source("src/fxfile/cmd/column_set_dlg.cpp")
  shared=source("src/fxfile/gui/ModernUI.cpp")
  rc=source("src/fxfile/fxfile.rc")
  self.assertIn("WS_EX_CLIENTEDGE",cpp)
  self.assertIn("emphasizeDialogEdit(",cpp)
  self.assertIn("kDialogEmphasizedEditProperty",shared)
  self.assertIn("sPalette.mFocus",shared)
  self.assertIn("sPalette.mSecondaryText",shared)
  self.assertIn("IDC_COLUMN_WIDTH,129,199,48,16",rc)
  self.assertIn('"px",IDC_STATIC,182,203,18,9',rc)
if __name__=="__main__":unittest.main()
