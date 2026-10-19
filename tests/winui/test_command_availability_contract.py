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
            "if(!row||!row.Tag())continue",
            "pane.active<pane.pending.size()&&!pane.pending[pane.active]",
            "const bool hasItems=ready&&chosen>0",
            "RenameButton().IsEnabled(canRename)",
            "indexed->isFileSystem()",
            "indexed->parsingName.empty()",
        ):
            self.assertIn(text,body)
        for command in ("WindowsCutButton","WindowsCopyButton","RecycleButton",
                        "CopyButton","MoveButton"):
            self.assertIn(f"{command}().IsEnabled(hasItems)",body)
        self.assertNotIn("StatusText().Text",body)

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
