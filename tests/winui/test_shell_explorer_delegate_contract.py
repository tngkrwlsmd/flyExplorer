"""Windows Explorer delegation source contracts; NOT EXECUTED."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class WindowsExplorerDelegationContracts(unittest.TestCase):
    def test_os_owns_archive_and_extension_commands(self):
        h=source("src/base/shell_explorer_delegate.h")
        for token in (
            "kMaxSelected=128",
            "kMaxPathUnits=16u*1024u",
            "lexically_normal().native()!=path",
            "CompareStringOrdinal(",
            "CoInitializeEx(",
            "COINIT_APARTMENTTHREADED",
            "SHParseDisplayName(",
            "ILFindLastID(absolute)",
            "SHOpenFolderAndSelectItems(",
            "CoTaskMemFree(",
            "CoUninitialize()",
        ):
            self.assertIn(token,h)
        for forbidden in ("ShellExecuteW(", "CreateFileW(",
                          "MoveFileExW(", "DeleteFileW(",
                          "CreateDirectoryW(", "CopyFileW(",
                          "system(", "WinExec("):
            self.assertNotIn(forbidden,h)

    def test_native_command_is_explicit_and_origin_scoped(self):
        ui=source("app/winui/m22_transfers.cpp")
        header=source("app/winui/MainWindow.xaml.h")
        for token in (
            '#include "../../src/base/shell_explorer_delegate.h"',
            "void MainWindow::RevealSelectedInWindowsExplorer(int side)",
            "shellexplorer::kMaxSelected",
            "visible.visibleRoute!=route",
            "item->isFileSystem()",
            "shellexplorer::reveal(paths)",
            "workspace.identity!=identity",
            "pane.routeIds[tab]!=route",
            "pane.filesystemPaths[tab]!=folder",
            'make(L"Windows 탐색기에서 선택 열기"',
            "ui.RevealSelectedInWindowsExplorer(side)",
            "ui.ShowExternalWindowsContextMenu(side)",
        ):
            self.assertIn(token,ui)
        self.assertIn("void RevealSelectedInWindowsExplorer(int side);",header)

    def test_no_duplicate_archive_commands_are_exposed(self):
        ui=source("app/winui/m22_transfers.cpp")
        menu=ui.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        for text in (
            "ZIP 내부 항목 검사",
            "ZIP으로 묶기",
            "선택한 파일 ZIP으로 묶기",
            "폴더 ZIP으로 묶기",
            "ZIP 해제",
            "ZIP 여러 파일 해제",
        ):
            self.assertNotIn('make(L"'+text,menu)
        # Native ZIP helpers deliberately stay available in the source tree
        # until the handoff is build/runtime/GUI-verified on Windows.
        self.assertIn("void MainWindow::CreateSelectedZip(int side)",ui)
        self.assertIn("void MainWindow::ExtractSelectedBatchZip(int side)",ui)

if __name__=="__main__":
    unittest.main()
