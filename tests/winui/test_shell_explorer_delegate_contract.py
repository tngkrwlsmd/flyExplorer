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
            "sourceUnits<=fxfile::shellexplorer::kMaxPathUnits",
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
        self.assertIn("void OpenCurrentFolderInWindowsExplorer(int side);",header)
        for token in (
            'void MainWindow::OpenCurrentFolderInWindowsExplorer(int side)',
            "shellexplorer::openFolder(folder)",
            "pane.routeIds[tab]!=route",
            "pane.filesystemPaths[tab]!=folder",
            'make(L"Windows 탐색기에서 현재 폴더 열기"',
            "ui.OpenCurrentFolderInWindowsExplorer(side)",
        ):
            self.assertIn(token,ui)

    def test_right_tapped_on_handled_list_item_reaches_owned_menu(self):
        xaml=source("app/winui/MainWindow.xaml")
        cpp=source("app/winui/MainWindow.xaml.cpp")
        for token in ('KeyDown="OnLeftFileKeyDown"', 'KeyDown="OnRightFileKeyDown"'):
            self.assertIn(token,xaml)
        self.assertNotIn('RightTapped="OnFileRightTapped"',xaml)
        body=cpp.split("MainWindow::MainWindow()",1)[1].split(
            "RootShell().AddHandler(",1)[0]
        for token in (
            "UIElement::RightTappedEvent()",
            "RightTappedEventHandler{",
            "this,&MainWindow::OnFileRightTapped",
            "for(auto const& files:{LeftFiles(),RightFiles()})",
            "true);",
        ):
            self.assertIn(token,body)
        self.assertIn("void MainWindow::OnFileRightTapped(",source("app/winui/m22_transfers.cpp"))

    def test_deferred_context_menus_reject_closed_tabs_and_retargeted_folders(self):
        ui=source("app/winui/m22_transfers.cpp")
        file_menu=ui.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        background=ui.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
            "void MainWindow::OnFileRightTapped(",1)[0]
        for body in (file_menu,background):
            for token in (
                "const auto sourceShellFolder=",
                "const auto sourceFilesystemFolder=",
                "pane.active!=tab",
                "tab>=pane.tabs.size()",
                "tab>=pane.pending.size()",
                "tab>=pane.routeIds.size()",
                "tab>=pane.filesystemPaths.size()",
                "pane.tabs[tab].snapshot().parsingName!=sourceShellFolder",
                "pane.filesystemPaths[tab]!=sourceFilesystemFolder",
            ):
                self.assertIn(token,body)
            # A saved PaneTab route alone is insufficient after navigation.
            self.assertLess(
                body.index("pane.tabs[tab].snapshot().parsingName!=sourceShellFolder"),
                body.index("action(*ui);"))
        self.assertIn("actual!=*expected",file_menu)
        self.assertIn("ui->mFileOperations.busy()",file_menu)

    def test_native_folder_handoff_is_explicit_and_read_only(self):
        h=source("src/base/shell_explorer_delegate.h")
        for token in (
            "HRESULT openFolder(std::wstring const& folder) noexcept",
            "folder.find(L'\\0')",
            "lexically_normal().native()!=folder",
            "GetFileAttributesW(folder.c_str())",
            "FILE_ATTRIBUTE_DIRECTORY",
            "COINIT_APARTMENTTHREADED",
            "SHELLEXECUTEINFOW request{}",
            "SEE_MASK_FLAG_NO_UI|SEE_MASK_NOASYNC",
            'request.lpVerb=L"explore"',
            "ShellExecuteExW(&request)",
        ):
            self.assertIn(token,h)
        self.assertNotIn("ShellExecuteExW(&request)",h.split(
            "inline HRESULT openFolder(",1)[0])

    def test_owned_gui_exercises_both_native_windows_explorer_commands(self):
        test=source("tests/winui/test_ep05_explorer_handoff_gui.py")
        harness=source("tests/winui/test_shell_gui.py")
        runner=source("tools/winui/run_checks.py")
        for command in (
            "Windows 탐색기에서 선택 열기",
            "Windows 탐색기에서 현재 폴더 열기",
            "EP05_NATIVE_EXPLORER_SELECTED_OWNED_FILE=PASS",
            "EP05_NATIVE_EXPLORER_OPENED_OWNED_FOLDER=PASS",
            "EP05_NATIVE_EXPLORER_HANDOFF_READ_ONLY=PASS",
            "if handle not in baseline and handle in explorer_windows()",
            'cls.value != "CabinetWClass"',
            'exe == "explorer.exe"',
            "owner.value == owned_pid",
            'if peer.element_info.control_type not in ("MenuItem", "Button", "Text")',
            "EP05_OWNED_MENU_UIA",
            "left_edge=max(item.left,area.left)",
            "right_edge=min(item.right,area.right)",
            "top_edge=max(item.top,area.top)",
            "bottom_edge=min(item.bottom,area.bottom)",
            'mouse.click(button="right",coords=click)',
            "eventually(select_owned_file,",
        ):
            self.assertIn(command,test)
        self.assertIn('if os.environ.get("FLY_EP05_EXPLORER_HANDOFF")=="YES":',harness)
        self.assertIn("ep05_run(win=win,element=element",harness)
        self.assertIn('gui_env["FLY_EP05_EXPLORER_HANDOFF"] = "YES"',runner)

    def test_archive_code_is_not_compiled_into_product(self):
        project=source("app/winui/flyExplorer.project-template.xml")
        for inactive in ("zip_raw_deflate.cpp", "zip_raw_deflate_compress.cpp",
                         "miniz_tinfl.c", "miniz_tdef.c"):
            self.assertNotIn(inactive,project)
        self.assertIn('ClCompile Include="m22_transfers.cpp"',project)

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
        # No dormant archive worker, command handler, busy bit or cancel
        # path should remain attached to WinUI after retiring the F08 menu.
        header=source("app/winui/MainWindow.xaml.h")
        for retired in (
            "CreateSelectedFolderZip", "CreateSelectedBatchZip",
            "CreateSelectedDeflateZip", "CreateSelectedZip",
            "ExtractSelectedBatchZip", "ExtractSelectedZip",
            "mZipBatchCancel", "mZipCreationBusy",
            "mZipDeflateCreationBusy", "mZipExtractionBusy",
            "mZipBatchCreationBusy", "mZipBatchExtractionBusy",
        ):
            self.assertNotIn(retired,ui)
            self.assertNotIn(retired,header)
        self.assertIn("mFileOperations.cancel();",ui)
        self.assertIn("fileBar()->CancelButton().IsEnabled(busy&&cancellable);",ui)
        for path in (
            "src/base/zip_store_writer.h",
            "src/base/zip_deflate_writer.h",
            "src/base/zip_store_extractor.h",
            "src/base/zip_store_batch_writer.h",
            "src/base/zip_store_batch_extractor.h",
            "src/base/zip_inspection.h",
        ):
            self.assertTrue((ROOT/path).is_file())

if __name__=="__main__":
    unittest.main()
