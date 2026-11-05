"""R07-6: transient accepted-rename owner lookup, never Undo authority."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R07RenameOwnerContract(unittest.TestCase):
    def test_candidate_is_transient_and_not_saved_or_wired_to_ui(self):
        header = read("app/winui/file_operation_controller.h")
        controller = read("app/winui/file_operation_controller.cpp")
        for marker in (
            "struct RenameRestoreCandidate final",
            "std::uint64_t ticket=0",
            "Context context{}",
            "std::wstring originalPath{}",
            "fxfile::filecommand::Result renamed{}",
            "std::optional<RenameRestoreCandidate> renameRestoreCandidate(",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, header)
        self.assertIn("std::optional<FileOperationController::RenameRestoreCandidate>", controller)
        self.assertNotIn("UndoFile(", controller)
        self.assertNotIn("RedoFile(", controller)
        self.assertNotIn("RenameTargetLease", controller)
        self.assertNotIn("SetFileInformationByHandle", controller)
        self.assertNotIn("renameRestoreCandidate(", read("app/winui/m22_transfers.cpp"))

    def test_only_current_successful_verified_rename_is_recorded(self):
        cpp = read("app/winui/file_operation_controller.cpp")
        body = cpp.split("FileOperationController::acceptFileCommand(", 1)[1].split(
            "FileOperationController::renameRestoreCandidate(", 1
        )[0]
        for marker in (
            "state_->closing||completion.ticket!=state_->epoch",
            "completion.ticket==0||!state_->busy",
            "state_->busy=false",
            "state_->renameCandidate.reset();",
            "!sameContext(completion.context,liveContext)",
            "completion.result.error!=ERROR_SUCCESS",
            "completion.kind==fxfile::filecommand::Kind::RenameSelected",
            "completion.result.renameEvidence.verified",
            "!completion.originalRenameSource.empty()",
            "!completion.result.target.empty()",
            "state_->renameCandidate.emplace(RenameRestoreCandidate{",
            "completion.ticket,completion.context,",
            "completion.originalRenameSource,completion.result",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, body)
        self.assertLess(body.index("completion.ticket==0||!state_->busy"),
                        body.index("state_->renameCandidate.emplace("))
        self.assertLess(body.index("!sameContext(completion.context,liveContext)"),
                        body.index("state_->renameCandidate.emplace("))
        self.assertLess(body.index("completion.result.error!=ERROR_SUCCESS"),
                        body.index("state_->renameCandidate.emplace("))
        self.assertIn("catch(...)", body)

    def test_new_operation_or_close_invalidates_previous_candidate(self):
        cpp = read("app/winui/file_operation_controller.cpp")
        pieces = (
            cpp.split("void FileOperationController::prepareForClose()", 1)[1].split(
                "FileOperationController::StartStatus FileOperationController::requestTransfer(", 1
            )[0],
            cpp.split("FileOperationController::requestTransfer(", 1)[1].split(
                "FileOperationController::StartStatus FileOperationController::confirmRecycle(", 1
            )[0],
            cpp.split("FileOperationController::launchTransfer(", 1)[1].split(
                "FileOperationController::TransferDisposition", 1
            )[0],
            cpp.split("FileOperationController::startFileCommand(", 1)[1].split(
                "FileOperationController::CommandDisposition", 1
            )[0],
        )
        for piece in pieces:
            self.assertIn("state_->renameCandidate.reset();", piece)
        # Neither file commands nor transfers can reuse a wrapped ticket.
        self.assertGreaterEqual(
            cpp.count("if(state_->epoch==(std::numeric_limits<std::uint64_t>::max)())"),
            2,
        )

    def test_lookup_rejects_and_discards_wrong_owner_or_ticket(self):
        cpp = read("app/winui/file_operation_controller.cpp")
        body = cpp.split("FileOperationController::renameRestoreCandidate(", 1)[1]
        for marker in (
            "std::lock_guard<std::mutex> lock(state_->mutex)",
            "state_->closing||state_->busy||state_->pending",
            "!state_->renameCandidate",
            "state_->renameCandidate->ticket==0",
            "state_->renameCandidate->ticket!=state_->epoch",
            "!sameContext(state_->renameCandidate->context,liveContext)",
            "state_->renameCandidate.reset();",
            "return std::nullopt;",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, body)
        self.assertLess(body.index("state_->renameCandidate.reset();"),
                        body.index("return state_->renameCandidate;"))
        for forbidden in ("CreateFileW(", "MoveFileW(", "MoveFileExW(",
                          "DeleteFileW(", "SetFileInformationByHandle("):
            self.assertNotIn(forbidden, body)


if __name__ == "__main__":
    unittest.main()
