"""Current retired-MFC recovery and known functional-gap contract."""
import unittest
from pathlib import Path
from historical_mfc import exists as historical_exists
R=Path(__file__).resolve().parents[2]
class ParityContract(unittest.TestCase):
 def test_retired_mfc_recovery_and_current_known_gaps(self):
  status=(R/"docs/development/CURRENT_STATUS.md").read_text(encoding="utf-8")
  for historical in (
      "src/fxfile/bookmark.cpp",
      "src/fxfile/file_filter.cpp",
      "src/fxfile/search_dlg.cpp",
      "src/fxfile/accel_table.cpp"):
   self.assertTrue(historical_exists(historical),historical)
  self.assertIn("cbffb48",status)
  for token in ("6,000","bookmark","regex","High Contrast ON",
                "signed clean-machine"):
   self.assertIn(token.lower(),status.lower())
if __name__=="__main__":unittest.main()
