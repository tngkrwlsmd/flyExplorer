"""UXH-03 keeps the user's saved panel and pane-specific folder state."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
class ResponsivePaneContract(unittest.TestCase):
 def test_narrow_only_compact_and_prefs_unchanged(self):
  s=(R/"src/fxfile/explorer_pane.cpp").read_text(encoding="utf-8-sig")
  sect=s.split("void ExplorerPane::recalcLayout(void)",1)[1].split("void ExplorerPane::OnPaint",1)[0]
  for v in ("sRect.Width() - sContentsMargin.left < sMinListWidth",
    "CONTENTS_BASIC_STYLE_HEIGHT", "mContentsWnd->setCompactLayout(sCompactContents)",
    "scaleForWindow(", "mContentsWnd->m_hWnd"):
   self.assertIn(v,sect)
  self.assertNotIn("gOpt->mConfig.mContentsStyle =",sect)
  self.assertNotIn("destroyContentsWnd()",sect)
 def test_compact_preserves_folder_and_bookmarks(self):
  s=(R/"src/fxfile/contents_wnd.cpp").read_text(encoding="utf-8-sig")
  p=s.split("void ContentsWnd::setCompactLayout",1)[1].split("void ContentsWnd::OnPaint",1)[0]
  for v in ("mCompactLayout = aCompact", "SW_HIDE", "SW_SHOWNA",
            "updateBookmarkPosition()", "Invalidate(FALSE)"):
   self.assertIn(v,p)
  paint=s.split("void ContentsWnd::OnPaint",1)[1].split("ContentsWnd::OnEraseBkgnd",1)[0]
  self.assertIn("sContentsStyle",paint)
  self.assertIn("mFolderName.c_str()",paint)
  self.assertNotIn("gOpt->mConfig.mContentsStyle =",p)
if __name__=="__main__":unittest.main()
