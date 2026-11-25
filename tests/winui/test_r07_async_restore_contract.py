"""R07-20: 백그라운드 이름 복원 완료 알림의 수명·소유권 계약."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(name):
    return (ROOT/name).read_text(encoding="utf-8-sig")

class R07AsyncRestoreContract(unittest.TestCase):
    def test_worker_captures_shared_lifetime_not_controller_this(self):
        source=read("app/winui/file_operation_controller.cpp")
        header=read("app/winui/file_operation_controller.h")
        self.assertIn("startTakenRenameRestoreAsync(",header)
        self.assertIn("executeTakenRenameRestoreOnState(",header)
        worker=source.split("FileOperationController::startTakenRenameRestoreAsync(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        self.assertIn("auto shared=state_;",worker)
        self.assertIn("std::thread([",worker)
        self.assertIn("shared,generation,taken=std::move(taken)",worker)
        self.assertNotIn("[this",worker)
        self.assertIn("executeTakenRenameRestoreOnState(",worker)

    def test_close_navigation_and_new_epoch_protect_queued_delivery(self):
        source=read("app/winui/file_operation_controller.cpp")
        worker=source.split("FileOperationController::startTakenRenameRestoreAsync(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        for key in ("shared->closing","shared->epoch!=value.ticket",
                    "shared->navigationGeneration!=generation"):
            self.assertGreaterEqual(worker.count(key),2)
        self.assertIn("post([shared,generation,delivered,",worker)
        self.assertIn("completion(std::move(value));",worker)
        self.assertIn("classifyRestoreOutcome(value.result)",worker)

    def test_replayed_ui_queue_task_is_delivered_once(self):
        source=read("app/winui/file_operation_controller.cpp")
        worker=source.split("FileOperationController::startTakenRenameRestoreAsync(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        self.assertIn("#include <atomic>",source)
        self.assertIn("std::make_shared<std::atomic_bool>(false)",worker)
        self.assertIn("delivered->exchange(true,std::memory_order_acq_rel)",worker)
        self.assertLess(worker.index("delivered->exchange("),
                        worker.index("completion(std::move(value));"))
        fixture=read("tests/winui/r07_dispatch_native/dispatch_native_fixture.cpp")
        for test in (
            "async_foreign_window_not_started",
            "async_foreign_pane_not_started",
            "async_foreign_panetab_not_started",
            "async_foreign_route_not_started",
            "async_foreign_folder_not_started",
            "async_foreign_shell_folder_not_started",
            "async_separate_windows_cannot_exchange_queued_results",
            "async_duplicate_queued_task_delivers_callback_once",
        ):
            with self.subTest(test=test):
                self.assertIn(test,fixture)

    def test_async_start_reserves_before_thread_and_retires_on_failure(self):
        source=read("app/winui/file_operation_controller.cpp")
        worker=source.split("FileOperationController::startTakenRenameRestoreAsync(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        for token in ("shared->busy=true;", "shared->restoreInFlight=true;"):
            self.assertLess(worker.index(token),worker.index("std::thread(["))
        self.assertIn("shared,taken,liveContext,true",worker)
        self.assertIn("if(shared->epoch==ticket&&shared->restoreInFlight)",worker)
        failure=worker.rsplit("}catch(...){",1)[1]
        self.assertIn("shared->pendingRestoreCheck.reset();",failure)
        self.assertIn("shared->restoreInFlight=false;",failure)
        self.assertIn("shared->busy=false;",failure)
        claim=source.split("FileOperationController::executeTakenRenameRestoreOnState(",1)[1].split(
            "FileOperationController::executeTakenRenameRestore(",1)[0]
        self.assertIn("if(asyncReserved)",claim)
        self.assertIn("}else if(shared->restoreInFlight)",claim)
        recheck=source.split("bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[1]
        self.assertLess(recheck.index("if(state_->restoreInFlight)return false;"),
                        recheck.index("state_->pendingRestoreCheck.reset();"))
        self.assertIn("#if defined(FLY_R07_RESTORE_RACE_NATIVE_TEST)\n            FlyR07RestoreStartHook();",worker)
        self.assertNotIn("FLY_R07_RESTORE_RACE_NATIVE_TEST",
                         read("app/winui/flyExplorer.project-template.xml"))

    def test_no_user_command_or_session_wiring(self):
        commands=read("app/winui/m21_commands.cpp")
        self.assertEqual(commands.count("startTakenRenameRestoreAsync("),1)
        self.assertIn("StartPendingRenameRestoreForCurrentOwner(",commands)
        for path in ("app/winui/MainWindow.xaml.cpp",
                     "app/winui/MainWindow.xaml",
                     "app/winui/m22_transfers.cpp",
                     "app/winui/m23_session.cpp"):
            body=read(path)
            self.assertNotIn("startTakenRenameRestoreAsync(",body)
            self.assertNotIn("StartPendingRenameRestoreForCurrentOwner(",body)
        self.assertNotIn("startTakenRenameRestoreAsync(",
                         read("src/base/file_command_core.cpp"))

if __name__=="__main__":
    unittest.main()
