"""No-user-data-mutation gates for the real test-owned recycle probe."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parent/"test_owned_recycle_gui.py").read_text(encoding="utf-8")
class RecycleSafety(unittest.TestCase):
 def test_global_recycle_requires_empty_and_opt_in(self):
  for item in ("args.apply_owned","if count:","RECYCLE_BIN_INITIAL_ITEM_COUNT",
               'assert bin.Items().Count==0',"filename in i.window_text()",
               "item.Name in (filename,path.stem)",".DoIt()", "verbs=item.Verbs()",
               "restore_verified_owned_item",
               "System.Recycle.DeletedFrom","LEGACY_PRESENT_SETTINGS_UNCHANGED",
               "RECOVERY_REQUIRES_HUMAN"):
   self.assertIn(item,S)
 def test_no_unowned_permanent_deletion(self):
  for bad in ("SHEmptyRecycleBin","os.remove(bin", "EmptyRecycleBin",
              "DeleteFileW", "recycleConfirmed=true"):
   self.assertNotIn(bad,S)
if __name__=="__main__":unittest.main()
