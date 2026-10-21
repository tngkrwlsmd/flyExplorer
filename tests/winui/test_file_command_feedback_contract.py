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
        self.assertIn("rememberOrigin(detail);",completion)
        self.assertIn("completion.touchedFolders",completion)
        self.assertIn("state.transferFailureNotice=message;",completion)
        self.assertIn("if(originActive)StatusText().Text(hstring(detail));",completion)
        self.assertIn("if(originActive)StatusText().Text(hstring(message));",completion)
        self.assertIn(
            "if(completion.context.windowTabIdentity==ActiveWindowTab().identity)",
            completion
        )
        self.assertIn("fxfile::shellnav::NavigationAction::Refresh",completion)
        self.assertIn("if(disposition==Disposition::StaleContext)",completion)

class AsyncWindowTabOwnershipContract(unittest.TestCase):
    def test_file_operations_reject_other_window_tab_results(self):
        header=(APP/"file_operation_controller.h").read_text(encoding="utf-8-sig")
        controller=(APP/"file_operation_controller.cpp").read_text(encoding="utf-8-sig")
        ui=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("std::uint64_t windowTabIdentity=0;",header)
        self.assertIn("a.windowTabIdentity==b.windowTabIdentity",controller)
        self.assertIn("context.windowTabIdentity=ActiveWindowTab().identity;",ui)
        self.assertIn("sameContext(completion.context,liveContext)",controller)
        self.assertIn("sameContext(pending.context,liveContext)",controller)
        self.assertIn("completion.report.error==ERROR_ALREADY_EXISTS",controller)
        self.assertIn("!completion.report.aborted",controller)
        self.assertIn(
            "completion.request.collision==fxfile::shelltransfer::Collision::Reject",
            controller
        )


class SkipExistingTransferContract(unittest.TestCase):
    def test_skip_is_local_preflight_only_and_revalidates_remaining(self):
        header=(APP/"file_operation_controller.h").read_text(encoding="utf-8-sig")
        controller=(APP/"file_operation_controller.cpp").read_text(encoding="utf-8-sig")
        for token in (
            "AllSkipped",
            "skipCollisions(",
            "skippedCollisions=0",
        ):
            self.assertIn(token,header)
        body=controller.split(
            "FileOperationController::skipCollisions(",1)[1].split(
            "FileOperationController::StartStatus FileOperationController::launchTransfer(",1
        )[0]
        for token in (
            "SourceMode::Filesystem",
            "DestinationMode::Filesystem",
            "sameContext(pending.context,liveContext)",
            "CompareStringOrdinal(",
            "if(skipped!=pending.collisions.size())",
            "if(remaining.empty()){",
            "skipped=totalSkipped;",
            "return StartStatus::AllSkipped;",
            "launchTransfer(std::move(pending.request)",
        ):
            self.assertIn(token,body)
        self.assertNotIn("DeleteFileW(",body)
        self.assertNotIn("GetFileAttributesW(",body)
        self.assertNotIn("std::thread(",body)
        self.assertIn("value.skippedCollisions=skippedCollisions;",controller)
        self.assertIn("completion.report.collisions",controller)
        # A reduced request can collide again before the Shell operation.
        # Keep earlier skips across a second dialog or a KeepBoth decision.
        self.assertIn("std::size_t skippedCollisions=0;",controller)
        self.assertIn("completion.report.collisions,completion.skippedCollisions",controller)
        self.assertIn("pending.skippedCollisions+skipped",controller)
        self.assertIn("skipped=totalSkipped;",controller)
        self.assertIn("return StartStatus::AllSkipped;",controller)
        self.assertIn("std::move(completion),totalSkipped",controller)
        self.assertIn("std::move(completion),pending.skippedCollisions",controller)

    def test_ui_shows_explicit_choices_and_never_guesses_success_counts(self):
        body=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        section=body.split("MainWindow::ConfirmCollision(",1)[1].split(
            "void MainWindow::OnTransferCompleted(",1
        )[0]
        self.assertIn('SecondaryButtonText(L"충돌 항목 건너뛰기")',section)
        self.assertIn("ContentDialogResult::Secondary",section)
        self.assertIn("mFileOperations.skipCollisions(",section)
        self.assertIn("mFileOperations.confirmCollision(",section)
        self.assertIn("if(status==FileOperationController::StartStatus::AllSkipped)",section)
        self.assertIn("completion.skippedCollisions",body)
        self.assertIn("std::size_t previouslySkipped",body)
        self.assertIn("completion.skippedCollisions);",body)
        self.assertIn("이전 확인에서 충돌 ",body)
        self.assertIn("일부 항목이 처리됐을 수 있습니다.",body)
        self.assertIn("rememberOrigin(detail);",body)
        self.assertNotIn("report.queued-report.completed",body)


if __name__=="__main__":
    unittest.main()
