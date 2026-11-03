"""R06a: native Explorer share discovery, never automatic transfer."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def src(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class R06ShareDiscoveryContract(unittest.TestCase):
    def test_share_entry_reuses_selected_explorer_handoff(self):
        ui = src("app/winui/m22_transfers.cpp")
        menu = ui.split("void MainWindow::ShowAppFileContextMenu(", 1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(", 1)[0]
        share = menu.split('menu.Items().Append(make(L"공유 옵션: Windows 탐색기에서 선택"', 1)[1].split("));", 1)[0]
        self.assertIn(",nullptr,", share)
        self.assertIn("canWindowsExplorer", share)
        self.assertIn("ui.RevealSelectedInWindowsExplorer(side)", share)
        self.assertEqual(menu.count('L"공유 옵션: Windows 탐색기에서 선택"'), 1)
        self.assertLess(menu.index('L"공유 옵션: Windows 탐색기에서 선택"'),
                        menu.index('L"추가 옵션 표시"'))
        self.assertNotIn("DataTransferManager", share)
        self.assertNotIn("ShowShareUI", share)

    def test_deferred_click_keeps_existing_context_identity_barriers(self):
        ui = src("app/winui/m22_transfers.cpp")
        body = ui.split("void MainWindow::ShowAppFileContextMenu(", 1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(", 1)[0]
        for marker in (
            "canWindowsExplorer=ready&&boundedSources&&",
            "sourceUnits<=fxfile::shellexplorer::kMaxPathUnits",
            "allFilesystem&&count<=fxfile::shellexplorer::kMaxSelected",
            "state.identity!=identity",
            "state.model.activePane!=side",
            "pane.active!=tab",
            "pane.pending[tab]",
            "pane.routeIds[tab]!=route",
            "pane.tabs[tab].snapshot().parsingName!=sourceShellFolder",
            "pane.filesystemPaths[tab]!=sourceFilesystemFolder",
            "ui->mFileOperations.pendingConfirmationToken()",
            "actual!=*expected",
            "indexed->parsingName!=path",
        ):
            self.assertIn(marker, body)

    def test_native_delegate_only_reveals_files_without_sending(self):
        ui = src("app/winui/m22_transfers.cpp")
        method = ui.split(
            "void MainWindow::RevealSelectedInWindowsExplorer(int side)", 1
        )[1].split("\nvoid MainWindow::", 1)[0]
        for marker in (
            "mFileOperations.busy()",
            "visible.visibleTab!=tab||visible.visibleRoute!=route",
            "view.SelectedItems().Size()",
            "fxfile::shellexplorer::kMaxSelected",
            "!item->isFileSystem()",
            "fxfile::shellexplorer::reveal(paths)",
            "공유·압축 등의 작업은 탐색기 메뉴에서 직접 선택하세요",
        ):
            self.assertIn(marker, method)
        for forbidden in (
            "DataTransferManager", "ShowShareUI", "SetStorageItems(",
            "CopySelectedToWindowsClipboard(", "StartTransfer(",
            "RunTransfer(", "CreateFileW(", "ShellExecuteW(",
        ):
            self.assertNotIn(forbidden, method)
        self.assertIn("SHOpenFolderAndSelectItems(",
                      src("src/base/shell_explorer_delegate.h"))

    def test_separate_share_user_decision_is_documented(self):
        doc = src("docs/development/R06_SHARE_DISCOVERY_20261103.md")
        for phrase in (
            "R06a", "Windows 탐색기에서 선택", "사용자가 직접", "외부 전송",
            "R06b", "미구현", "NOT TESTED",
        ):
            self.assertIn(phrase, doc)


if __name__ == "__main__":
    unittest.main()
