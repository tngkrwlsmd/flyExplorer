"""R07-18 native dispatch must remain isolated from user GUI and session."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
def read(path):return (ROOT/path).read_text(encoding="utf-8-sig")
class NativeDispatchContract(unittest.TestCase):
    def test_real_sources_and_no_ui_route(self):
        project=read("tests/winui/r07_dispatch_native/FlyR07DispatchNative.project-template.xml")
        self.assertIn(r"app\winui\file_operation_controller.cpp",project)
        self.assertIn(r"src\base\file_command_core.cpp",project)
        self.assertIn("FLY_R07_OWNER_NATIVE_CONTRACT",project)
        for path in ("app/winui/MainWindow.xaml.cpp","app/winui/MainWindow.xaml.h",
                     "app/winui/m22_transfers.cpp","app/winui/m21_commands.cpp"):
            self.assertNotIn("executeTakenRenameRestore(",read(path))
    def test_owner_is_checked_and_retired_before_mutation(self):
        core=read("app/winui/file_operation_controller.cpp")
        body=core.split("FileOperationController::executeTakenRenameRestore(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        for key in ("std::lock_guard<std::mutex> lock(state_->mutex)",
                    "taken.ticket==expected.ticket",
                    "after.fileId==before.fileId",
                    "sameContext(taken.context,liveContext)",
                    "state_->pendingRestoreCheck.reset();",
                    "if(!current)return denied;","restoreRenameNoReplace("):
            self.assertIn(key,body)
        self.assertLess(body.index("state_->pendingRestoreCheck.reset();"),
                        body.index("restoreRenameNoReplace("))
        self.assertEqual(body.count("restoreRenameNoReplace("),1)
    def test_real_owned_file_fixture_and_wrapper(self):
        fixture=read("tests/winui/r07_dispatch_native/dispatch_native_fixture.cpp")
        self.assertIn("Kind::RenameSelected",fixture)
        self.assertIn("CommittedVerified",fixture)
        self.assertIn("concurrent_claim_exactly_once",fixture)
        wrapper=read("tests/winui/r07_dispatch_native/test_native.py")
        self.assertIn("R07_DISPATCH_NATIVE_SUMMARY 13 passed, 0 failed.",wrapper)
        self.assertIn("assert_legacy_profile_unchanged(real,original)",wrapper)
        self.assertIn("shutil.rmtree(owned)",wrapper)
if __name__=="__main__":
    unittest.main()
