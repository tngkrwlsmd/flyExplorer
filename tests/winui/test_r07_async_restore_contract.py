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
        self.assertIn("post([shared,generation,completion=std::move(completion)",worker)
        self.assertIn("completion(std::move(value));",worker)
        self.assertIn("classifyRestoreOutcome(value.result)",worker)

    def test_no_gui_or_session_wiring(self):
        for path in ("app/winui/MainWindow.xaml.cpp",
                     "app/winui/MainWindow.xaml.h",
                     "app/winui/m21_commands.cpp",
                     "app/winui/m22_transfers.cpp",
                     "app/winui/m23_session.cpp"):
            self.assertNotIn("startTakenRenameRestoreAsync(",read(path))
        self.assertNotIn("startTakenRenameRestoreAsync(",
                         read("src/base/file_command_core.cpp"))

if __name__=="__main__":
    unittest.main()
