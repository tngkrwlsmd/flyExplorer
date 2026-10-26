"""Source contracts for one-shot file transfer confirmation identity.

No Windows shell operations, clipboard/Recycle Bin mutation, or GUI execution.
The contract checks actual product/WinUI source paths and ordering, not a mock.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"


def source(name):
    return (APP / name).read_text(encoding="utf-8-sig")


def section(text, first, last):
    return text.split(first, 1)[1].split(last, 1)[0]


class PendingTransferIdentityContract(unittest.TestCase):
    def test_pending_tokens_are_bounded_and_unique_per_confirmation(self):
        body = source("file_operation_controller.cpp")
        header = source("file_operation_controller.h")
        self.assertIn("std::uint64_t confirmationSerial=0;", body)
        self.assertIn("std::uint64_t token=0;", body)
        self.assertEqual(2, body.count(
            "state_->pending->token=++state_->confirmationSerial;"))
        self.assertEqual(2, body.count(
            "if(state_->confirmationSerial=="))
        self.assertIn("std::numeric_limits<std::uint64_t>::max", body)
        self.assertIn("pendingConfirmationToken() const noexcept", header)
        getter = section(body,
                         "FileOperationController::pendingConfirmationToken() const noexcept",
                         "void FileOperationController::cancel()")
        self.assertIn("std::lock_guard<std::mutex> lock(state_->mutex);", getter)
        self.assertIn("state_->closing||state_->busy||!state_->pending?", getter)
        self.assertIn("0:state_->pending->token;", getter)

    def test_all_three_decisions_check_token_before_consuming_pending(self):
        body = source("file_operation_controller.cpp")
        h = source("file_operation_controller.h")
        for name, ending in (
            ("confirmRecycle", "confirmCollision"),
            ("confirmCollision", "skipCollisions"),
            ("skipCollisions", "launchTransfer"),
        ):
            token_method = (
                "FileOperationController::StartStatus\nFileOperationController::skipCollisions("
                if name == "skipCollisions" else
                "FileOperationController::StartStatus FileOperationController::"+name+"("
            )
            start = body.index(token_method)
            end = body.index("FileOperationController::"+ending+"(", start + len(token_method))
            operation = body[start:end]
            self.assertIn("std::uint64_t expectedToken", operation, name)
            self.assertIn("if(!expectedToken||!state_->pending||", operation, name)
            self.assertIn("state_->pending->token!=expectedToken", operation, name)
            self.assertLess(operation.index("state_->pending->token!=expectedToken"),
                            operation.index("pending=std::move(*state_->pending)"), name)
            self.assertIn("sameContext(pending.context,liveContext)", operation, name)
            self.assertIn("std::uint64_t expectedToken", h, name)

    def test_old_recycle_dialog_is_dropped_without_mutating_new_pending(self):
        ui = source("m22_transfers.cpp")
        recycle = section(ui, "winrt::fire_and_forget MainWindow::ConfirmRecycle(",
                          "winrt::fire_and_forget MainWindow::ConfirmCollision(")
        self.assertIn("std::size_t count,std::uint64_t token", recycle)
        self.assertIn("co_await dialog.ShowAsync()", recycle)
        check = "if(!token||mFileOperations.pendingConfirmationToken()!=token)co_return;"
        self.assertIn(check, recycle)
        self.assertLess(recycle.index("co_await dialog.ShowAsync()"),
                        recycle.index(check))
        self.assertLess(recycle.index(check),
                        recycle.index("mFileOperations.confirmRecycle("))
        self.assertIn("approved,token,FileOperationContext(", recycle)
        self.assertIn("ConfirmRecycle(recycleCount,mFileOperations.pendingConfirmationToken());", ui)

    def test_collision_keep_both_and_skip_require_same_dialog_token(self):
        ui = source("m22_transfers.cpp")
        collision = section(ui, "winrt::fire_and_forget MainWindow::ConfirmCollision(",
                            "void MainWindow::OnTransferCompleted(")
        check = "if(!token||mFileOperations.pendingConfirmationToken()!=token)co_return;"
        self.assertIn("std::size_t previouslySkipped,std::uint64_t token", collision)
        self.assertIn(check, collision)
        self.assertLess(collision.index("co_await dialog.ShowAsync()"),
                        collision.index(check))
        self.assertLess(collision.index(check),
                        collision.index("mFileOperations.skipCollisions("))
        self.assertLess(collision.index(check),
                        collision.index("mFileOperations.confirmCollision("))
        self.assertIn("token,context,post,std::move(completed),skipped", collision)
        self.assertIn("choice==ContentDialogResult::Primary,token,context,post", collision)
        self.assertIn("completion.skippedCollisions,\n                   mFileOperations.pendingConfirmationToken());", ui)

    def test_close_and_subsequent_transfer_invalidate_old_confirmation(self):
        body = source("file_operation_controller.cpp")
        close = section(body, "FileOperationController::prepareForClose() noexcept",
                        "FileOperationController::StartStatus FileOperationController::requestTransfer(")
        self.assertIn("state_->closing=true;", close)
        self.assertIn("state_->pending.reset();", close)
        new_transfer = section(body, "FileOperationController::StartStatus FileOperationController::requestTransfer(",
                               "FileOperationController::StartStatus FileOperationController::confirmRecycle(")
        self.assertIn("state_->pending.reset();", new_transfer)
        self.assertIn("state_->pending->token=++state_->confirmationSerial;", new_transfer)
        command = section(body, "FileOperationController::StartStatus FileOperationController::startFileCommand(",
                          "FileOperationController::CommandDisposition\nFileOperationController::acceptFileCommand(")
        self.assertIn("state_->pending.reset();", command)

    def test_no_native_mutation_is_performed_by_pending_ui_decisions(self):
        body = source("m22_transfers.cpp")
        dialogs = section(body, "winrt::fire_and_forget MainWindow::ConfirmRecycle(",
                          "void MainWindow::OnTransferCompleted(")
        for native_write in ("MoveFileW(", "CopyFileExW(", "DeleteFileW(",
                             "CreateDirectoryW(", "IFileOperation"):
            self.assertNotIn(native_write, dialogs)
        self.assertIn("FileOperationContext(ActiveWindowTab().model.activePane)", dialogs)


if __name__ == "__main__":
    unittest.main()
