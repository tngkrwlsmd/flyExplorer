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
class RemovableRecyclePolicy(unittest.TestCase):
 def test_ui_promises_no_permanent_fallback(self):
  transfer=(Path(__file__).resolve().parents[2]/"app/winui/m22_transfers.cpp").read_text(encoding="utf-8-sig")
  for token in ("휴지통을 사용할 수 없으면 영구 삭제로 전환하지 않고 작업을 중단합니다.",
                "removableLocalRoot(completion.request.sourceParent)",
                "영구 삭제로 전환하지 않았습니다."):
   self.assertIn(token,transfer)

if __name__=="__main__":unittest.main()
