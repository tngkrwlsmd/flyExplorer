"""R07-23C: 실제 WinUI 대기열/완료 콜백의 창 수명 보호 계약.

이 검사는 소스 수준 회귀 검사이며, 네이티브 복원과 DispatcherQueue의
실제 비동기 결합을 실행하거나 수용했다고 주장하지 않는다.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[2] / "app/winui/m21_commands.cpp")


class RestoreWinUiDispatchContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = SOURCE.read_text(encoding="utf-8-sig")
        cls.post = source.split(
            "FileOperationController::Post MainWindow::FileOperationUiPost(){", 1
        )[1].split(
            "FileOperationController::RestoreCallback MainWindow::FileOperationRestoreCallback(){", 1
        )[0]
        cls.callback = source.split(
            "FileOperationController::RestoreCallback MainWindow::FileOperationRestoreCallback(){", 1
        )[1].split("bool MainWindow::RestoreCompletionContextCurrent(", 1)[0]
        cls.completion = source.split(
            "void MainWindow::OnRenameRestoreCompleted(", 1
        )[1].split("void MainWindow::OnCreateFolder(", 1)[0]

    def test_worker_only_enqueues_and_ui_task_checks_window_lifetime(self):
        self.assertIn("auto weak=get_weak();", self.post)
        self.assertIn("dispatch.TryEnqueue(", self.post)
        self.assertIn("if(auto ui=weak.get())", self.post)
        self.assertIn("if(!ui->mClosing)task();", self.post)
        self.assertLess(self.post.index("dispatch.TryEnqueue("),
                        self.post.index("if(auto ui=weak.get())"))
        self.assertLess(self.post.index("if(auto ui=weak.get())"),
                        self.post.index("if(!ui->mClosing)task();"))
        self.assertIn("}catch(...){return false;}", self.post)

    def test_restore_callback_uses_weak_window_and_rechecks_context(self):
        self.assertIn("auto weak=get_weak();", self.callback)
        self.assertIn("if(auto ui=weak.get())ui->OnRenameRestoreCompleted(", self.callback)
        self.assertIn(
            "if(!RestoreCompletionContextCurrent(completion.context))return;",
            self.completion,
        )
        self.assertLess(
            self.completion.index("RestoreCompletionContextCurrent(completion.context)"),
            self.completion.index("state.fileOperationNotice=notice;"),
        )


if __name__ == "__main__":
    unittest.main()
