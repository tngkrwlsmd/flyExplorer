"""Source-level audit: all shared scrollbar attachment paths and modal cleanup."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def source(rel):return (ROOT/rel).read_text(encoding="utf-8-sig")
class ScrollbarCoverage(unittest.TestCase):
 def test_shared_list_and_tree_coverage(self):
  m=source("src/fxfile/gui/ModernUI.cpp")
  for token in ('"SysListView32"','"SysTreeView32"','"ListBox"',
                'WS_VSCROLL | WS_HSCROLL','DialogScrollableSubclassProc',
                'WM_NCDESTROY','kDialogScrollSubclassId'):
   self.assertIn(token,m)
  self.assertIn('configureDarkScrollbarOverlay(',m)
  self.assertIn('removeDarkScrollbarOverlay(aHwnd)',m)
 def test_legacy_main_controls_remain_integrated(self):
  for name in ("ListCtrlEx.cpp","TreeCtrlEx.cpp"):
   m=source("src/fxfile/gui/"+name)
   self.assertIn('configureDarkScrollbarOverlay(',m)
   self.assertIn('removeDarkScrollbarOverlay(',m)
  b=source("src/fxfile/bookmark_set_wnd.cpp")
  self.assertIn("configureDarkScrollbarOverlay(",b)
  self.assertIn("removeDarkScrollbarOverlay(",b)
 def test_modal_dismisses_address_dropdown_and_hides_popup_topmost(self):
  dialog=source("src/fxfile/gui/ModernDialog.cpp")
  m=source("src/fxfile/gui/ModernUI.cpp")
  cmd=source("src/fxfile/cmd/cmd_column.cpp")
  self.assertIn("dismissOwnedDropdowns(m_hWnd)",dialog)
  self.assertIn("CB_GETDROPPEDSTATE",m)
  self.assertIn("CB_SHOWDROPDOWN, FALSE",m)
  self.assertIn("sPopupOccluded",m)
  self.assertIn("mPopupHostRoot",m)
  self.assertIn("XPR_TRUE, m_hWnd",source("src/fxfile/address_bar.cpp"))
  self.assertIn("sOwnerState",m)
  self.assertIn("ColumnSetDlg sDlg(sMainFrame)",cmd)
  column=source("src/fxfile/cmd/column_set_dlg.cpp")
  self.assertIn("sFrame->getAddressBar(-1)",column)
  self.assertIn("GetMonitorInfo",column)
  self.assertIn("sBelow + sDialogRect.Height()",column)
 def test_popup_retains_normal_native_scroll_and_high_contrast_escape(self):
  address=source("src/fxfile/address_bar.cpp")
  self.assertIn("configureDarkScrollbarOverlay(",address)
  self.assertIn("mHighContrast",address)
  m=source("src/fxfile/gui/ModernUI.cpp")
  self.assertIn("aPopupTopMost ? HWND_TOPMOST : HWND_TOP",m)
  self.assertIn("DialogScrollableSubclassProc",m)
if __name__=="__main__":unittest.main()
