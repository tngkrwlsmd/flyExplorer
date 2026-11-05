"""R07-21: WinUI 파일 완료 알림의 약한 참조·종료 안전 대기열 계약."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class R07WinUiDispatchContract(unittest.TestCase):
    def test_actual_dispatcher_queue_is_used_for_file_command(self):
        header=read("app/winui/MainWindow.xaml.h")
        cpp=read("app/winui/m21_commands.cpp")
        self.assertIn("FileOperationController::Post FileOperationUiPost();",header)
        self.assertIn("fxfile::previewops::FileOperationController::Post MainWindow::FileOperationUiPost()",cpp)
        self.assertIn("auto post=FileOperationUiPost();",cpp)
        self.assertIn("std::move(post)",cpp)
        self.assertIn("mFileOperations.startFileCommand(",cpp)

    def test_background_enqueue_does_not_resolve_window(self):
        cpp=read("app/winui/m21_commands.cpp")
        body=cpp.split("fxfile::previewops::FileOperationController::Post MainWindow::FileOperationUiPost()",1)[1].split(
            "void MainWindow::OnCreateFolder(",1)[0]
        self.assertIn("auto dispatch=DispatcherQueue();",body)
        self.assertIn("auto weak=get_weak();",body)
        self.assertIn("return [dispatch,weak]",body)
        self.assertIn("dispatch.TryEnqueue(",body)
        enqueue=body.index("dispatch.TryEnqueue(")
        weak_resolution=body.index("weak.get()")
        self.assertLess(enqueue,weak_resolution)
        self.assertIn("if(!ui->mClosing)task();",body)
        self.assertIn("catch(...){return false;}",body)
        self.assertNotIn("get_strong()",body)
        self.assertNotIn("[this",body)

    def test_restore_composition_stays_private_and_user_disconnected(self):
        cpp=read("app/winui/m21_commands.cpp")
        header=read("app/winui/MainWindow.xaml.h")
        self.assertEqual(cpp.count("startTakenRenameRestoreAsync("),1)
        self.assertIn("StartTakenRenameRestoreForCurrentOwner(",cpp)
        self.assertIn("StartTakenRenameRestoreForCurrentOwner(",header)
        self.assertNotIn("executeTakenRenameRestore(",cpp)
        for path in ("app/winui/MainWindow.xaml.cpp",
                     "app/winui/m22_transfers.cpp",
                     "app/winui/m23_session.cpp",
                     "app/winui/MainWindow.xaml"):
            body=read(path)
            self.assertNotIn("startTakenRenameRestoreAsync(",body)
            self.assertNotIn("StartTakenRenameRestoreForCurrentOwner(",body)

    def test_controller_still_double_rechecks_before_result_delivery(self):
        code=read("app/winui/file_operation_controller.cpp")
        func=code.split("FileOperationController::startTakenRenameRestoreAsync(",1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(",1)[0]
        for field in ("shared->closing","shared->epoch!=value.ticket",
                      "shared->navigationGeneration!=generation"):
            self.assertGreaterEqual(func.count(field),2)
        self.assertIn("post([shared,generation,delivered,",func)

if __name__=="__main__":
    unittest.main()
