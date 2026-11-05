"""R07-23B: 완료 알림은 원래 창의 현재 패널에만 귀속된다."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "app/winui/m21_commands.cpp"


class RestoreCompletionPaneContract(unittest.TestCase):
    def test_inactive_pane_rejected_before_route_and_notice(self):
        source = SOURCE.read_text(encoding="utf-8-sig")
        body = source.split("bool MainWindow::RestoreCompletionContextCurrent(", 1)[1].split(
            "void MainWindow::OnRenameRestoreCompleted(", 1
        )[0]
        self.assertIn("state.identity!=origin.windowTabIdentity", body)
        self.assertIn("state.model.activePane!=origin.side)return false;", body)
        self.assertLess(body.index("state.model.activePane!=origin.side"),
                        body.index("pane.routeIds[origin.tab]!=origin.route"))
        completion = source.split("void MainWindow::OnRenameRestoreCompleted(", 1)[1].split(
            "void MainWindow::OnCreateFolder(", 1
        )[0]
        self.assertIn("if(!RestoreCompletionContextCurrent(completion.context))return;", completion)
        self.assertLess(completion.index("RestoreCompletionContextCurrent"),
                        completion.index("state.fileOperationNotice=notice;"))


if __name__ == "__main__":
    unittest.main()
