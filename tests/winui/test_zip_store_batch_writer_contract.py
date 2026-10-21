"""F08 bounded multi-file ZIP Store source contracts. NOT EXECUTED."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ZipStoreBatchContracts(unittest.TestCase):
    def test_bounded_sources_and_crc(self):
        code=source("src/base/zip_store_batch_writer.h")
        for token in (
            "kMinFiles=2", "kMaxFiles=8",
            "kMaxTotalBytes=8ull*1024ull*1024ull",
            'kArchiveName[]=L"flyExplorer-selection.zip"',
            "zipstore::detail::safeSource(source,parent,leaf,encoded)",
            "zipinspect::detail::same(directory,parent)",
            "zipinspect::detail::same(prior.leaf,leaf)",
            "FILE_FLAG_OPEN_REPARSE_POINT", "FILE_SHARE_READ",
            "FILE_ATTRIBUTE_DIRECTORY", "FILE_ATTRIBUTE_REPARSE_POINT",
            "length>kMaxTotalBytes-totalBytes",
            "detail::unchanged(before,after)",
            "zipstore::detail::crc32(member.data)",
            "0x04034b50u", "0x02014b50u", "0x06054b50u",
            "member.localOffset",
            "GetTempFileNameW(directory.c_str()",
            "zipstore::detail::Staging staging",
            "zipstore::detail::writeAll(writer.h,zip)",
            "::MoveFileExW(staging.path,target.c_str()",
            "MOVEFILE_WRITE_THROUGH",
            "staging.owned=false",
        ):
            self.assertIn(token,code)
        self.assertLess(
            code.index("zipstore::detail::safeSource(source,parent,leaf,encoded)"),
            code.index("GetTempFileNameW(directory.c_str()"))
        self.assertLess(
            code.index("result.output=target;"),
            code.index("::MoveFileExW(staging.path,target.c_str()"))
        for forbidden in (
            "MOVEFILE_REPLACE_EXISTING|", "CREATE_ALWAYS",
            "RemoveDirectoryW(", "ShellExecuteW(", "std::filesystem::remove("
        ):
            self.assertNotIn(forbidden,code)

    def test_ui_multi_select_origin_and_idle_guard(self):
        ui=source("app/winui/m22_transfers.cpp")
        header=source("app/winui/MainWindow.xaml.h")
        command=ui.split("void MainWindow::CreateSelectedBatchZip(int side)",1)[1].split(
            "void MainWindow::CreateSelectedZip(int side)",1)[0]
        for token in (
            "SelectedItems().Size()", "visible.visibleRoute!=route",
            "selectedPaths.push_back(item->parsingName)",
            "std::adjacent_find(ids.begin(),ids.end())",
            "fxfile::zipbatch::createMany(paths)",
            "mZipBatchCreationBusy=true",
            "active.identity!=identity", "pane.routeIds[tab]!=route",
            "pane.filesystemPaths[tab]!=folder",
            "NavigationAction::Refresh",
        ):
            self.assertIn(token,command)
        for token in (
            "bool allRegularFilesystemFiles=true;",
            "const bool zipIdle=",
            "const bool canCreateBatchZip=",
            "count>=fxfile::zipbatch::kMinFiles",
            "count<=fxfile::zipbatch::kMaxFiles",
            'make(L"선택한 파일 ZIP으로 묶기 (2~8개, 무압축)"',
        ):
            self.assertIn(token,ui)
        self.assertIn("void CreateSelectedBatchZip(int side);",header)
        self.assertIn("bool mZipBatchCreationBusy=false;",header)

if __name__=="__main__":
    unittest.main()
