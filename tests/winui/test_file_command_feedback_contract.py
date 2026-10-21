"""Stale native rename/create completions must not disappear without feedback."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class FileCommandFeedbackContract(unittest.TestCase):
    def test_stale_completion_is_not_silent_or_claimed_success(self):
        body=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=body.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        stale=completion.split("if(disposition==Disposition::StaleContext)",1)[1].split(
            "if(disposition==Disposition::Failed)",1)[0]
        self.assertIn("StatusText().Text(",stale)
        self.assertIn("원본 폴더에서 결과를 확인하세요.",stale)
        self.assertIn("return;",stale)
        self.assertNotIn("성공",stale)
        self.assertNotIn("MoveFile",stale)

    def test_failure_and_success_still_use_native_result_and_refresh(self):
        body=(APP/"m21_commands.cpp").read_text(encoding="utf-8-sig")
        completion=body.split("void MainWindow::OnFileCommandCompleted(",1)[1]
        for required in (
            "mFileOperations.acceptFileCommand(",
            "if(disposition==Disposition::Ignored)return;",
            "if(disposition==Disposition::Failed)",
            "koreanError(completion.result.error)",
            "fileBar()->EndNameEdit();",
            "fxfile::shellnav::NavigationAction::Refresh",
        ):
            self.assertIn(required,completion)

class TransferFeedbackContract(unittest.TestCase):
    def test_confirmation_cancel_and_partial_cancel_have_feedback(self):
        body=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        start=body.split("void MainWindow::ApplyTransferStartStatus(",1)[1].split(
            "void MainWindow::StartTransfer(",1)[0]
        completion=body.split("void MainWindow::OnTransferCompleted(",1)[1].split(
            "void MainWindow::OnWindowsCopy(",1)[0]
        self.assertIn("status==Start::Cancelled",start)
        self.assertIn("파일 작업 확인을 취소했습니다.",start)
        self.assertIn("completion.report.aborted",completion)
        self.assertIn("completion.report.error==ERROR_CANCELLED",completion)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.",completion)
        self.assertIn("mTransferFailureNotice=detail;",completion)
        self.assertIn("completion.touchedFolders",completion)

if __name__=="__main__":
    unittest.main()
