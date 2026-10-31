"""R05 current-folder terminal delegation contracts (no shell launch)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

class TerminalDelegationContract(unittest.TestCase):
    def test_helper_never_uses_path_as_executable_or_shell_code(self):
        helper=source("src/base/shell_terminal_delegate.h")
        for text in (
            "inline HRESULT openFolder(std::wstring const& folder) noexcept",
            "folder.size()>1024",
            "folder.find_first_of",
            "path.lexically_normal().native()!=folder",
            "root.size()!=3",
            "GetDriveTypeW(root.c_str())!=DRIVE_FIXED",
            "FILE_ATTRIBUTE_DIRECTORY",
            "FILE_ATTRIBUTE_REPARSE_POINT",
            "SHGetKnownFolderPath(",
            "FOLDERID_LocalAppData",
            "Microsoft\\\\WindowsApps\\\\wt.exe",
            "GetFileAttributesW(executable.c_str())",
            'L"-w new new-tab -d \\\\""',
            'if(folder.back()==L\'\\\\\')arguments+=L"\\\\";',
            "request.lpFile=executable.c_str();",
            "request.lpParameters=arguments.c_str();",
            "request.lpDirectory=folder.c_str();",
            "ShellExecuteExW(&request)",
            "CoTaskMemFree",
            "CoUninitialize",
        ):
            self.assertIn(text,helper)
        for forbidden in ("CreateProcessW(", "system(", "WinExec(",
                          "ShellExecuteW(", "cmd.exe", "powershell.exe",
                          "GetClipboardData(", "CreateFileW(", "DeleteFileW(",
                          "SetEnvironmentVariableW("):
            self.assertNotIn(forbidden,helper)

    def test_background_menu_uses_owned_route_guard(self):
        app=source("app/winui/m22_transfers.cpp")
        background=app.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
            "void MainWindow::OnFileRightTapped(",1)[0]
        self.assertIn('make(L"터미널에서 열기",',background)
        self.assertIn("ui.OpenCurrentFolderInWindowsTerminal(side)",background)
        self.assertIn("item.Click(guarded(std::move(action)))",background)
        self.assertIn("const bool localFolder=ready&&!pane.filesystemPaths[tab].empty();",background)
        for token in ("state.identity!=identity","state.model.activePane!=side",
                      "pane.routeIds[tab]!=route","pane.pending[tab]",
                      "pane.filesystemPaths[tab]!=sourceFilesystemFolder",
                      "mFileOperations.pendingConfirmationToken()"):
            self.assertIn(token,background)
        self.assertIn("void OpenCurrentFolderInWindowsTerminal(int side);",
                      source("app/winui/MainWindow.xaml.h"))

    def test_async_terminal_dispatch_rejects_stale_pane(self):
        app=source("app/winui/m22_transfers.cpp")
        body=app.split("void MainWindow::OpenCurrentFolderInWindowsTerminal(int side){",1)[1].split(
            "void MainWindow::RevealSelectedInWindowsExplorer(int side){",1)[0]
        for token in ("mClosing", "mFileOperations.busy()",
                      "mFileOperations.pendingConfirmationToken()",
                      "visible.visibleTab!=tab", "visible.visibleRoute!=route",
                      "std::thread(", "fxfile::shellterminal::openFolder(folder)",
                      "dispatch.TryEnqueue(", "workspace.identity!=identity",
                      "workspace.model.activePane!=side",
                      "pane.routeIds[tab]!=route",
                      "pane.filesystemPaths[tab]!=folder",
                      "ERROR_FILE_NOT_FOUND", "ERROR_NOT_SUPPORTED"):
            self.assertIn(token,body)
        self.assertNotIn("RunTransfer(",body)
        self.assertNotIn("PasteFromWindowsClipboard(",body)
        self.assertNotIn("CreateProcessW(",body)

if __name__=="__main__":
    unittest.main()
