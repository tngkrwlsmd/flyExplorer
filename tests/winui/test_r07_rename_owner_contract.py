"""R07-6/7: accepted-rename owner candidate is taken once, never Undo authority."""
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
            "std::optional<RenameRestoreCandidate> takeRenameRestoreCandidate(",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, header)
        self.assertIn("std::optional<FileOperationController::RenameRestoreCandidate>", controller)
        self.assertNotIn("UndoFile(", controller)
        self.assertNotIn("RedoFile(", controller)
        self.assertNotIn("RenameTargetLease", controller)
        self.assertNotIn("SetFileInformationByHandle", controller)
        self.assertNotIn("takeRenameRestoreCandidate(", read("app/winui/m22_transfers.cpp"))

    def test_only_current_successful_verified_rename_is_recorded(self):
        cpp = read("app/winui/file_operation_controller.cpp")
        body = cpp.split("FileOperationController::acceptFileCommand(", 1)[1].split(
            "FileOperationController::takeRenameRestoreCandidate(", 1
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
        body = cpp.split("FileOperationController::takeRenameRestoreCandidate(", 1)[1]
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
                        body.index("return taken;"))
        for forbidden in ("CreateFileW(", "MoveFileW(", "MoveFileExW(",
                          "DeleteFileW(", "SetFileInformationByHandle("):
            self.assertNotIn(forbidden, body)


    def test_claim_consumes_candidate_under_lock_without_filesystem_work(self):
        header = read("app/winui/file_operation_controller.h")
        cpp = read("app/winui/file_operation_controller.cpp")
        body = cpp.split("FileOperationController::takeRenameRestoreCandidate(", 1)[1]
        self.assertIn("takeRenameRestoreCandidate(", header)
        self.assertNotIn("renameRestoreCandidate(", header)
        self.assertIn("std::lock_guard<std::mutex> lock(state_->mutex)", body)
        self.assertIn("auto taken=std::move(state_->renameCandidate);", body)
        self.assertIn("state_->renameCandidate.reset();", body)
        self.assertIn("return taken;", body)
        self.assertIn("catch(...)", body)
        self.assertLess(body.index("auto taken=std::move(state_->renameCandidate);"),
                        body.index("return taken;"))
        self.assertLess(body.index("state_->renameCandidate.reset();",
                                   body.index("auto taken=std::move(state_->renameCandidate);")),
                        body.index("return taken;"))
        self.assertNotIn("return state_->renameCandidate;", body)
        self.assertNotIn("CreateFileW(", body)
        self.assertNotIn("MoveFileW(", body)
        self.assertNotIn("SetFileInformationByHandle(", body)

    def test_recheck_is_one_shot_and_compares_original_receipt(self):
        header = read("app/winui/file_operation_controller.h")
        cpp = read("app/winui/file_operation_controller.cpp")
        self.assertIn("bool recheckAndRetireRenameRestoreCandidate(", header)
        self.assertIn("pendingRestoreCheck", cpp)
        take = cpp.split("FileOperationController::takeRenameRestoreCandidate(", 1)[1].split(
            "bool FileOperationController::recheckAndRetireRenameRestoreCandidate(", 1
        )[0]
        self.assertIn("auto taken=std::move(state_->renameCandidate);", take)
        self.assertIn("state_->renameCandidate.reset();", take)
        self.assertIn("state_->pendingRestoreCheck=taken;", take)
        self.assertLess(take.index("state_->renameCandidate.reset();",
                                   take.index("auto taken=std::move(")),
                        take.index("state_->pendingRestoreCheck=taken;"))
        check = cpp.split("bool FileOperationController::recheckAndRetireRenameRestoreCandidate(", 1)[1]
        for token in (
            "std::lock_guard<std::mutex> lock(state_->mutex)",
            "if(!state_->pendingRestoreCheck)return false;",
            "!state_->closing&&!state_->busy&&!state_->pending",
            "taken.ticket!=0&&taken.ticket==state_->epoch",
            "taken.ticket==expected.ticket",
            "sameContext(expected.context,liveContext)",
            "sameContext(taken.context,liveContext)",
            "expected.originalPath==taken.originalPath",
            "left.error==ERROR_SUCCESS&&right.error==left.error",
            "right.target==left.target",
            "before.verified&&after.verified==before.verified",
            "after.volumeSerial==before.volumeSerial",
            "after.fileId==before.fileId",
            "after.fileSize==before.fileSize",
            "after.lastWriteTime==before.lastWriteTime",
            "state_->pendingRestoreCheck.reset();",
        ):
            with self.subTest(token=token):
                self.assertIn(token, check)
        self.assertLess(check.index("const bool current="),
                        check.index("state_->pendingRestoreCheck.reset();"))
        self.assertLess(check.index("state_->pendingRestoreCheck.reset();"),
                        check.index("return current;"))
        for forbidden in ("restoreRenameNoReplace(", "CreateFileW(", "MoveFileW(",
                          "DeleteFileW(", "SetFileInformationByHandle("):
            self.assertNotIn(forbidden, check)

    def test_new_work_and_close_expire_even_already_taken_candidate(self):
        cpp = read("app/winui/file_operation_controller.cpp")
        boundaries = (
            ("void FileOperationController::prepareForClose()", "FileOperationController::StartStatus FileOperationController::requestTransfer("),
            ("FileOperationController::requestTransfer(", "FileOperationController::StartStatus FileOperationController::confirmRecycle("),
            ("FileOperationController::launchTransfer(", "FileOperationController::TransferDisposition"),
            ("FileOperationController::startFileCommand(", "FileOperationController::CommandDisposition"),
            ("FileOperationController::acceptFileCommand(", "FileOperationController::takeRenameRestoreCandidate("),
        )
        for first, last in boundaries:
            with self.subTest(boundary=first):
                part = cpp.split(first, 1)[1].split(last, 1)[0]
                self.assertIn("state_->pendingRestoreCheck.reset();", part)
        self.assertNotIn(
            "recheckAndRetireRenameRestoreCandidate(",
            read("app/winui/m22_transfers.cpp")
        )

    def test_navigation_owner_generation_and_all_ui_transition_bridges(self):
        controller = read("app/winui/file_operation_controller.cpp")
        header = read("app/winui/file_operation_controller.h")
        ui = read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("void invalidateRenameOwnerOnNavigation() noexcept;", header)
        generation = controller.split("void FileOperationController::invalidateRenameOwnerOnNavigation()", 1)[1].split(
            "void FileOperationController::prepareForClose()", 1)[0]
        for token in (
            "std::lock_guard<std::mutex> lock(state_->mutex)",
            "++state_->navigationGeneration;",
            "state_->renameCandidate.reset();",
            "state_->pendingRestoreCheck.reset();",
        ):
            self.assertIn(token, generation)
        self.assertIn("fileCommandNavigationGeneration=state_->navigationGeneration", controller)
        accept = controller.split("FileOperationController::acceptFileCommand(", 1)[1].split(
            "FileOperationController::takeRenameRestoreCandidate(", 1)[0]
        self.assertIn("state_->fileCommandNavigationGeneration!=state_->navigationGeneration", accept)
        for segment, ending in (
            ("std::uint64_t MainWindow::QueuePath(", "void MainWindow::QueuePidl("),
            ("void MainWindow::QueuePidl(", "bool MainWindow::QueueNextFolderPage("),
            ("void MainWindow::SuspendActiveWindowTab()", "void MainWindow::ApplyActiveWindowTab("),
            ("bool MainWindow::CloseWindowTab(", "void MainWindow::UpdateNavigationChrome("),
            ("void MainWindow::ActivatePane(", "void MainWindow::OnBackClicked("),
            ("void MainWindow::OpenFolderInNewPaneTab(", "void MainWindow::OnNewTabClicked("),
            ("void MainWindow::OnNewTabClicked(", "void MainWindow::CloseFolderTab("),
            ("void MainWindow::CloseFolderTab(", "void MainWindow::OnCloseTabClicked("),
            ("void MainWindow::OnSplitClicked(", "void MainWindow::OnActivateLeft("),
            ("void MainWindow::OnLeftTabSelectionChanged(", "void MainWindow::OnRightTabSelectionChanged("),
            ("void MainWindow::OnRightTabSelectionChanged(", "void MainWindow::OpenSelectedFolder("),
        ):
            part=ui.split(segment, 1)[1].split(ending, 1)[0]
            with self.subTest(segment=segment):
                self.assertIn("invalidateRenameOwnerOnNavigation();",part)
        self.assertIn("if(id&&action!=fxfile::shellnav::NavigationAction::Refresh)", ui)
        self.assertIn("if(changed)mFileOperations.invalidateRenameOwnerOnNavigation();", ui)


if __name__ == "__main__":
    unittest.main()
