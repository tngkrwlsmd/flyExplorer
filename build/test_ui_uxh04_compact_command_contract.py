"""Explicit toolbar compaction may not rewrite saved custom row preferences."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]/"src/fxfile"
class CommandContract(unittest.TestCase):
 def test_opt_in_and_saved_state(self):
  s=(R/"main_coolbar.cpp").read_text(encoding="utf-8-sig")
  for t in ("mTemporaryCompact = XPR_TRUE", "mTemporaryCompact = XPR_FALSE",
            "mPreviousDriveWidth = sDriveBand.cx",
            "mPreviousBookmarkWidth = sBookmarkBand.cx",
            "sBookmarkBand.fStyle &= ~RBBS_BREAK",
            "if (XPR_IS_TRUE(mTemporaryCompact))",
            "sCoolBarState.cx = mPreviousDriveWidth",
            "sCoolBarState.cx = mPreviousBookmarkWidth",
            "sBookmarkBand.cxIdeal + sBookmarkBand.cxHeader"):
   self.assertIn(t,s)
  self.assertNotIn("gOpt->mMain.mDriveBar = ",s.split(
     "xpr_bool_t MainCoolBar::toggleTemporaryCompact",1)[1].split(
       "void MainCoolBar::setWrapable",1)[0])
 def test_menu_router_translation(self):
  for f,needle in (
      ("resource.h","ID_VIEW_TOOL_COMPACT_ROWS"),
      ("cmd/router/cmd_command_map.cpp","new cmd::ToolCompactRowsCommand"),
      ("cmd/cmd_main_gui.cpp","ToolCompactRowsCommand::execute"),
      ("command_string_table.cpp","cmd.tools.compact_rows"),
      ("Languages/Korean.xml","cmd.tools.compact_rows"),
      ("fxfile.rc","Compact &drive/bookmark rows")):
   self.assertIn(needle,(R/f).read_text(encoding="utf-8-sig"))
if __name__=="__main__":unittest.main()
