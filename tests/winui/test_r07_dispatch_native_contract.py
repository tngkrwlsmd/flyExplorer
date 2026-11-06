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
        self.assertIn("FLY_R07_RESTORE_RACE_NATIVE_TEST",project)
        self.assertNotIn("FLY_R07_RESTORE_RACE_NATIVE_TEST",read("app/winui/flyExplorer.project-template.xml"))
        for path in ("app/winui/MainWindow.xaml.cpp","app/winui/MainWindow.xaml.h",
                     "app/winui/m22_transfers.cpp","app/winui/m21_commands.cpp"):
            self.assertNotIn("executeTakenRenameRestore(",read(path))
    def test_owner_claim_is_atomic_but_native_call_does_not_hold_ui_mutex(self):
        core=read("app/winui/file_operation_controller.cpp")
        body=core.split("FileOperationController::executeTakenRenameRestoreOnState(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        for key in ("std::lock_guard<std::mutex> lock(shared->mutex)",
                    "taken.ticket==expected.ticket",
                    "after.fileId==before.fileId",
                    "sameContext(taken.context,liveContext)",
                    "shared->pendingRestoreCheck.reset();",
                    "originalCopy=taken.originalPath;",
                    "renamedCopy=taken.renamed;",
                    "shared->busy=true;",
                    "shared->restoreInFlight=true;",
                    "shared->restoreInFlight=false;",
                    "restoreRenameNoReplace("):
            with self.subTest(key=key):
                self.assertIn(key,body)
        self.assertLess(body.index("shared->pendingRestoreCheck.reset();"),
                        body.index("shared->busy=true;"))
        self.assertLess(body.index("shared->busy=true;"),
                        body.index("restoreRenameNoReplace("))
        self.assertLess(body.index("restoreRenameNoReplace("),
                        body.index("if(!shared->closing&&shared->epoch==taken.ticket)"))
        self.assertEqual(1,body.count("restoreRenameNoReplace("))
        self.assertIn("return outcome;",body)
        self.assertIn("classifyRestoreOutcome(",core)
        self.assertIn("Status::CommittedUnverified",core)
        self.assertIn("Status::NativeCallFailedUnknownState",core)
    def test_real_owned_file_fixture_and_wrapper(self):
        fixture=read("tests/winui/r07_dispatch_native/dispatch_native_fixture.cpp")
        self.assertIn("Kind::RenameSelected",fixture)
        self.assertIn("CommittedVerified",fixture)
        self.assertIn("concurrent_claim_exactly_once",fixture)
        self.assertIn("inflight_navigation_returns_before_native",fixture)
        self.assertIn("inflight_close_prompt_preserves_native_outcome",fixture)
        self.assertIn("all_pre_native_rejections_classified_not_attempted",fixture)
        self.assertIn("inflight_duplicate_file_completion_rejected",fixture)
        self.assertIn("inflight_duplicate_transfer_completion_rejected",fixture)
        self.assertIn("file_command_post_rejected_releases_busy",fixture)
        controller=read("app/winui/file_operation_controller.cpp")
        self.assertIn("!state_->busy||state_->restoreInFlight",controller)
        self.assertIn("state_->restoreInFlight)\n        return TransferDisposition::Ignored;",controller)
        wrapper=read("tests/winui/r07_dispatch_native/test_native.py")
        self.assertIn("R07_DISPATCH_NATIVE_SUMMARY 39 passed, 0 failed.",wrapper)
        self.assertIn("assert_legacy_profile_unchanged(real,original)",wrapper)
        self.assertIn("shutil.rmtree(owned)",wrapper)
if __name__=="__main__":
    unittest.main()
