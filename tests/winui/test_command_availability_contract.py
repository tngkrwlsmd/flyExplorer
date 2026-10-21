"""Selection-aware command availability must preserve keyboard and mutation boundaries."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

class CommandAvailabilityContract(unittest.TestCase):
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
