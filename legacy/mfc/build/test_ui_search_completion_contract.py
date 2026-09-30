"""Normal native search completion remains nonmodal, errors unchanged."""
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/"src/fxfile/search_dlg.cpp"
class SearchCompletion(unittest.TestCase):
 def test_nonmodal_success_and_accessible_status(self):
  s=p.read_text(encoding="utf-8-sig")
  seg=s.split("LRESULT SearchDlg::OnFinalize",1)[1].split(
      "void SearchDlg::getStatusNumberFormat",1)[0]
  self.assertIn("mStatusBar.setPaneText(0, sStatusText)",seg)
  self.assertIn("mStatusBar.setDynamicPaneText(1, sStatusElapsedTimeText",seg)
  self.assertIn("mStatusBar.announceAccessibleStatus(",seg)
  native=(p.parent/"gui/StatusBar.cpp").read_text(encoding="utf-8-sig")
  self.assertIn("::DefWindowProc(m_hWnd, WM_SETTEXT",native)
  self.assertIn("NotifyWinEvent(EVENT_OBJECT_NAMECHANGE",native)
  self.assertIn("setPaneText(0, sText)",native)
  self.assertNotIn("MessageBox(",seg)
  self.assertIn("popup.search.msg.wrong_location",s)
  self.assertIn("MessageBox(sMsg, XPR_NULL, MB_OK | MB_ICONSTOP)",s)
 def test_cancel_path_still_stops_search_and_closes(self):
  s=p.read_text(encoding="utf-8-sig")
  seg=s.split("void SearchDlg::OnCancel(void)",1)[1].split(
      "LRESULT SearchDlg::OnFinalize",1)[0]
  self.assertIn("mSearchFile->stop()",seg)
  self.assertIn("DestroyWindow()",seg)
if __name__=="__main__":unittest.main()
