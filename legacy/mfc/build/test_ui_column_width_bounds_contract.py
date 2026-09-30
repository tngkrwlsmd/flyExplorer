"""Native column width range validation is shared by every commit path."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ColumnBounds(unittest.TestCase):
 def test_all_commit_paths_share_validated_width(self):
  cpp=(ROOT/"src/fxfile/cmd/column_set_dlg.cpp").read_text(encoding="utf-8-sig")
  h=(ROOT/"src/fxfile/cmd/column_set_dlg.h").read_text(encoding="utf-8-sig")
  self.assertIn("readEditedColumnWidth(xpr_sint_t aPreviousWidth)",h)
  self.assertEqual(cpp.count("readEditedColumnWidth(sColumnItemData->mWidth)"),4)
  self.assertNotIn("mWidth = GetDlgItemInt(IDC_COLUMN_WIDTH",cpp)
 def test_dpi_scales_bounds_and_legacy_values_are_preserved(self):
  cpp=(ROOT/"src/fxfile/cmd/column_set_dlg.cpp").read_text(encoding="utf-8-sig")
  for snippet in ("scaleForWindow(24, m_hWnd)","scaleForWindow(4096, m_hWnd)",
                  "if (sWidth == aPreviousWidth)","return aPreviousWidth",
                  "sWidth = min(sMaximum + 1", "SetDlgItemInt(IDC_COLUMN_WIDTH"):
   self.assertIn(snippet,cpp)
if __name__=="__main__":unittest.main()
