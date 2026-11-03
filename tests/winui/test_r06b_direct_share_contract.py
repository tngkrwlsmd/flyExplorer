"""R06b: one-file, window-owned Windows Share UI source contract."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class DirectShareContract(unittest.TestCase):
    def test_single_file_only_and_existing_fallback(self):
        ui=read("app/winui/m22_transfers.cpp")
        menu=ui.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        direct=menu.split('make(L"Windows 공유 창 열기 (파일 1개)"',1)[1].split("));",1)[0]
        self.assertIn("canWindowsExplorer&&localSelection&&count==1&&!isFolder",direct)
        self.assertIn("ui.ShareSelectedWithWindows(side)",direct)
        self.assertIn('L"공유 옵션: Windows 탐색기에서 선택"',menu)
        self.assertIn("ui.RevealSelectedInWindowsExplorer(side)",menu)

    def test_direct_share_requires_latest_owned_selection(self):
        cpp=read("app/winui/m22_transfers.cpp")
        check=cpp.split("bool MainWindow::ShareSelectionStillCurrent(",1)[1].split(
            "winrt::fire_and_forget MainWindow::ShareSelectedWithWindows(",1)[0]
        for token in ("mClosing","mFileOperations.busy()",
            "mFileOperations.pendingConfirmationToken()",
            "now.windowTabIdentity!=origin.windowTabIdentity",
            "now.tab!=origin.tab","now.route!=origin.route",
            "now.visibleFolder!=origin.visibleFolder",
            "now.visibleShellFolder!=origin.visibleShellFolder",
            "visible.visibleRoute!=origin.route",
            "selectedView.SelectedItems().Size()!=1",
            "currentId!=logical", "item->isFileSystem()",
            "!item->isFolder()", "item->parsingName==path"):
            self.assertIn(token,check)

    def test_window_share_contract_has_real_storage_item_not_path_text(self):
        cpp=read("app/winui/m22_transfers.cpp")
        share=cpp.split("winrt::fire_and_forget MainWindow::ShareSelectedWithWindows(",1)[1].split(
            "void MainWindow::RevealSelectedInWindowsExplorer(",1)[0]
        for token in ("GetFileFromPathAsync(", "co_await uiApartment",
            "revision!=mShareRevision", "ShareSelectionStillCurrent(",
            "get_activation_factory<", "IDataTransferManagerInterop",
            "GetForWindow(", "DataRequested(",
            "args.Request().FailWithDisplayText(",
            "single_threaded_vector<", "items.Append(file.as<",
            "package.SetStorageItems(items)", "ShowShareUIForWindow(window)",
            "DataPackageOperation::Copy"):
            self.assertIn(token,share)
        for forbidden in ("DataTransferManager::ShowShareUI(", "GetForCurrentView(",
            "SetText(", "Clipboard::", "StartTransfer(",
            "RunTransfer(", "ShellExecuteW(", "SetStorageItems({"):
            self.assertNotIn(forbidden,share)

    def test_share_event_lifetime_is_owned_and_closed(self):
        header=read("app/winui/MainWindow.xaml.h")
        window=read("app/winui/MainWindow.xaml.cpp")
        for t in ("mShareManager{nullptr}", "mShareRequestedToken{}",
            "mShareHandlerRegistered=false", "mShareRevision=0",
            "ShareSelectionStillCurrent(", "ShareSelectedWithWindows("):
            self.assertIn(t,header)
        closing=window.split("void MainWindow::PrepareForClose() noexcept",1)[1].split(
            "MainWindow::~MainWindow()",1)[0]
        for t in ("mClosing=true", "++mShareRevision",
            "mShareManager.DataRequested(mShareRequestedToken)",
            "mShareHandlerRegistered=false", "mShareManager=nullptr"):
            self.assertIn(t,closing)

    def test_no_send_undo_or_gui_claims(self):
        doc=read("docs/development/R06B_DIRECT_SHARE_20261103.md")
        for key in ("R06b","R07","NOT TESTED","자동 전송",
                    "비패키지","사용자가 공유 대상","충돌"):
            self.assertIn(key,doc)

if __name__=="__main__":
    unittest.main()
