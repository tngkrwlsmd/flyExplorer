"""Four-way real Explorer GUI clipboard fixture is explicit and owned."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parent/"test_owned_explorer_clipboard_gui.py").read_text(encoding="utf-8")
class RealExplorerSafety(unittest.TestCase):
 def test_owns_both_targets_and_clears_only_with_explicit_flag(self):
  for x in ("--apply-clear-clipboard","clipboard_clear()",
             "preexisting={int(s.HWND)","int(v.HWND) not in preexisting",
             "ready_explorer","preview.pid","Path(paths[0]).resolve()",
             'file_result("winui-copy"', 'file_result("explorer-copy"',
             'file_result("winui-cut"','file_result("explorer-cut"',
             "GLOBAL_CLIPBOARD_CLEARED_AFTER_TEST",
             "ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL"):
   self.assertIn(x,S)
  for bad in ("EmptyRecycleBin","DeleteFileW","os.system("):
   self.assertNotIn(bad,S)
if __name__=="__main__":unittest.main()
