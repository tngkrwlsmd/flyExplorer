"""Selection-aware command availability must preserve keyboard and mutation boundaries."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class CommandAvailabilityContract(unittest.TestCase):
    def test_file_confirmation_owns_root_shortcuts_without_swallowing_dialog_keys(self):
        code=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        root=code.split("RootShell().PreviewKeyDown(",1)[1]
        guard=root.split("const bool control=",1)[0]
        self.assertIn("ui->mFileOperations.pendingConfirmationToken())return;",guard)
        self.assertNotIn("args.Handled",guard)
        self.assertLess(root.index("pendingConfirmationToken()"),
                        root.index("VirtualKey::F6"))

    def test_selection_controls_are_active_pane_local(self):
        code=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        body=code.split("void MainWindow::UpdateCommandAvailability()",1)[1].split(
            "void MainWindow::OnToggleFileInfoPane",1)[0]
        for text in (
            "state.model.activePane",
            "view.SelectedItems()",
            "if(!row||!row.Tag()){validSelection=false;break;}",
            "state.fileLists[side].visibleRoute==pane.routeIds[pane.active]",
            "pane.active<pane.filesystemPaths.size()",
            "count<=fxfile::shelltransfer::kMaxItems",
            "indexed->parsingName.empty()",
            "fxfile::shelltransfer::kMaxSourcePathUnits-sourceUnits",
            "indexed->isFileSystem()",
            "const bool localSelection=validSelection&&localFolder&&allFilesystem;",
            "const bool canCopyToOpposite=sourceAllowed&&",
            "const bool canMoveToOpposite=localSelection&&destinationFilesystem;",
            "RenameButton().IsEnabled(canRename)",
        ):
            self.assertIn(text,body)
        for command in ("WindowsCutButton","WindowsCopyButton","RecycleButton"):
            self.assertIn(f"{command}().IsEnabled(localSelection)",body)
        self.assertIn("CopyButton().IsEnabled(canCopyToOpposite)",body)
        self.assertIn("MoveButton().IsEnabled(canMoveToOpposite)",body)
        self.assertIn("CreateFolderButton().IsEnabled(localFolder)",body)
        self.assertIn("WindowsPasteButton().IsEnabled(localFolder)",body)
        self.assertNotIn("StatusText().Text",body)
        self.assertNotIn("::GetFileAttributesW",body)

    def test_pending_collision_disables_toolbar_and_both_owned_menus(self):
        code=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        toolbar=code.split("void MainWindow::UpdateCommandAvailability()",1)[1].split(
            "void MainWindow::OnToggleFileInfoPane",1)[0]
        self.assertIn("const bool idle=!mFileOperations.busy()&&",toolbar)
        self.assertIn("!mFileOperations.pendingConfirmationToken();",toolbar)
        transfers=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        background=transfers.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1]
        self.assertIn("const bool ready=!mFileOperations.busy()&&",background)
        self.assertIn("!mFileOperations.pendingConfirmationToken();",background)
        self.assertIn("ui->mFileOperations.pendingConfirmationToken())return;",background)
        operation=transfers.split("void MainWindow::RunTransfer(",1)[1].split(
            "void MainWindow::",1)[0]
        self.assertLess(operation.index("pendingConfirmationToken()"),
                        operation.index("if(mFileOperations.busy())"))
        self.assertIn("return;",operation)

    def test_confirmation_settlement_recomputes_instead_of_forcing_buttons(self):
        code=(APP/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        body=code.split("void MainWindow::ApplyTransferStartStatus(",1)[1].split(
            "void MainWindow::StartTransfer(",1)[0]
        self.assertGreater(body.rindex("UpdateCommandAvailability();"),
                           body.index("status==Start::Cancelled"))
        self.assertGreater(body.rindex("UpdateCommandAvailability();"),
                           body.index("status==Start::AllSkipped"))
        self.assertNotIn(".IsEnabled(true)",body)

    def test_selection_change_and_pane_change_refresh_buttons(self):
        code=(APP/"MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")
        footer=code.split("void MainWindow::UpdateFooterSummary()",1)[1].split(
            "void MainWindow::QueueSelectionPresentationUpdate()",1)[0]
        selected=code.split("void MainWindow::OnFileSelectionChanged(",1)[1].split(
            "void MainWindow::OnFileSelectionKeyUp(",1)[0]
        activate=code.split("void MainWindow::ActivatePane(",1)[1].split(
            "void MainWindow::UpdateActivePaneChrome()",1)[0]
        self.assertIn("UpdateCommandAvailability();",footer)
        self.assertIn("UpdateFooterSummary();",selected)
        self.assertIn("UpdateFooterSummary();",activate)
        self.assertIn("if(mPopulatingFileLists)return;",selected)
        self.assertIn("if(newlySelectedFile&&ActiveWindowTab().model.activePane!=side)",selected)

if __name__=="__main__":
    unittest.main()
