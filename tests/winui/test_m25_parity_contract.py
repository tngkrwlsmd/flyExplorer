"""M2.5 comparison is grounded in tracked native sources and partial coverage."""
import unittest
from pathlib import Path
from historical_mfc import exists as historical_exists
R=Path(__file__).resolve().parents[2]
class ParityContract(unittest.TestCase):
 def test_tracked_legacy_evidence_and_known_gaps(self):
  report=(R/"docs/development/WINUI3_M25_PARITY_AND_RELEASE_GATES_20260930.md").read_text(encoding="utf-8")
  for historical in (
      "src/fxfile/bookmark.cpp",
      "src/fxfile/file_filter.cpp",
      "src/fxfile/search_dlg.cpp",
      "src/fxfile/accel_table.cpp"):
   self.assertTrue(historical_exists(historical),historical)
   self.assertIn(historical,report)
  for token in ("Ctrl+Shift+F","2,600","bookmarks or regex",
                "High Contrast ON","not a signed NSIS/MSI/MSIX installer"):
   self.assertIn(token.lower(),report.lower())
if __name__=="__main__":unittest.main()
