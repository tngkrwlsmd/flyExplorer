"""F08 source-only contracts for one-file ZIP Store creation (NOT EXECUTED)."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[2]
def source(p):
    return (R/p).read_text(encoding="utf-8-sig")
class ZipStoreWriterContracts(unittest.TestCase):
    def test_bounded_store_crc_and_headers(self):
        code=source("src/base/zip_store_writer.h")
        for term in ("kMaxInputBytes=8u*1024u*1024u",
                     "zipinspect::detail::safeName(leaf,directory)",
                     "FILE_ATTRIBUTE_REPARSE_POINT",
                     "FILE_SHARE_READ",
                     "crc32(std::vector<unsigned char> const& data)",
                     "0xedb88320u",
                     "0x04034b50u", "0x02014b50u", "0x06054b50u",
                     "detail::word(zip,0x0800)",
                     "GetTempFileNameW", "FlushFileBuffers",
                     "struct Staging final", "temporary.owned=true;",
                     "MoveFileExW(temporary.path,target.c_str()",
                     "MOVEFILE_WRITE_THROUGH",
                     "~Staging(){if(owned)::DeleteFileW(path);}",
                     "temporary.owned=false;"):
            self.assertIn(term,code)
        for forbidden in ("MOVEFILE_REPLACE_EXISTING", "CREATE_ALWAYS",
                          "GENERIC_ALL", "FILE_SHARE_WRITE", "ShellExecute",
                          "IFileOperation"):
            self.assertNotIn(forbidden,code.replace(
                "// MOVEFILE_REPLACE_EXISTING deliberately absent.",""))

    def test_ui_revalidates_selection_and_window_before_publish(self):
        ui=source("app/winui/m22_transfers.cpp")
        method=ui.split("void MainWindow::CreateSelectedZip(int side)",1)[1].split(
            "void MainWindow::ExtractSelectedBatchZip(int side)",1)[0]
        for term in ("view.SelectedItems().Size()!=1",
                     "visible.visibleRoute!=route",
                     "selected->isFolder()",
                     "mZipCreationBusy=true",
                     "fxfile::zipstore::createOne(source)",
                     "current.identity!=origin",
                     "pane.routeIds[tab]!=route",
                     "pane.filesystemPaths[tab]!=folder",
                     "NavigationAction::Refresh"):
            self.assertIn(term,method)
        self.assertNotIn('make(L"ZIP으로 묶기 (무압축, 한 파일)"',ui)
        self.assertIn('make(L"Windows 탐색기에서 선택 열기"',ui)
        self.assertIn("void CreateSelectedZip(int side);",
                      source("app/winui/MainWindow.xaml.h"))
if __name__=="__main__":
    unittest.main()
