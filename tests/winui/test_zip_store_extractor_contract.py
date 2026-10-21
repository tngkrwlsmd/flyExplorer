"""F08 single-file Store extraction source contracts (NOT EXECUTED)."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ZipStoreExtractorContracts(unittest.TestCase):
    def test_single_entry_strict_layout_and_crc_before_publication(self):
        code=read("src/base/zip_store_extractor.h")
        for term in (
            "zipinspect::kMaxZipBytes", "ziprawdeflate::kMaxOutputBytes",
            "FILE_FLAG_OPEN_REPARSE_POINT", "FILE_SHARE_READ",
            "u32(archiveBytes,eocd)!=0x06054b50u",
            "u32(archiveBytes,central)!=0x02014b50u",
            "u32(archiveBytes,0)!=0x04034b50u",
            "u16(archiveBytes,eocd+10)!=1",
            "!fxfile::zipstorecompat::supportedFlags(flags)||",
            "fxfile::zipstorecompat::supportedDosVersion(versionMade)",
            "fxfile::zipstorecompat::supportedDosVersion(versionNeeded)",
            "fxfile::zipstorecompat::sameDosTime(archiveBytes,0,central)",
            "fxfile::zipstorecompat::decodeName(",
            "(method==0&&packed!=expanded)",
            "(method!=0&&method!=8)",
            "(method==8&&versionNeeded!=20)",
            "ziprawdeflate::inflateExact(",
            "u32(archiveBytes,central+42)!=0",
            "central+centralBytes!=eocd",
            "dataBegin+packed!=central",
            "std::equal(archiveBytes.begin()+30u",
            "detail::safeLeaf(member)",
            "outputPath.parent_path().native()!=parent",
            "zipstore::detail::crc32(payload)!=checksum",
            "GetFileAttributesW(target.c_str())",
            "GetTempFileNameW(parent.c_str(),L\"fxe\"",
            "detail::Staging staging",
            "staging.owned=true",
            "information.nNumberOfLinks==1",
            "zipstore::detail::writeAll(writer.h,payload)",
            "MoveFileExW(staging.path,target.c_str()",
            "MOVEFILE_WRITE_THROUGH",
            "staging.owned=false"):
            self.assertIn(term,code)
        self.assertLess(
            code.index("zipstore::detail::crc32(payload)!=checksum"),
            code.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(
            code.index("answer.output=target;"),
            code.index("::MoveFileExW(staging.path,target.c_str()"))
        for forbidden in ("MOVEFILE_REPLACE_EXISTING|",
                          "CREATE_ALWAYS", "MoveFileW(",
                          "RemoveDirectoryW(", "ShellExecuteW("):
            self.assertNotIn(forbidden,code)

    def test_ui_wiring_and_context_not_ever_written_from_worker(self):
        ui=read("app/winui/m22_transfers.cpp")
        h=read("app/winui/MainWindow.xaml.h")
        start=ui.split("void MainWindow::ExtractSelectedZip(int side)",1)[1].split(
            "void MainWindow::InspectSelectedZip(int side)",1)[0]
        for term in (
            "view.SelectedItems().Size()!=1",
            "selected->isFileSystem()",
            "selected->isFolder()",
            "mZipExtractionBusy=true",
            "fxfile::zipextract::extractOne(source)",
            "active.identity!=identity",
            "pane.routeIds[tab]!=route",
            "pane.filesystemPaths[tab]!=folder",
            "NavigationAction::Refresh"):
            self.assertIn(term,start)
        self.assertIn("bool mZipExtractionBusy=false;",h)
        self.assertIn("void ExtractSelectedZip(int side);",h)
        self.assertIn('make(L"ZIP 해제 (Store/Deflate, 한 파일)"',ui)
        self.assertIn('canInspectZip=suffix==L".zip"&&zipIdle;',ui)
        self.assertIn('const bool zipIdle=!mZipCreationBusy&&!mZipInspectionBusy&&',ui)
        self.assertIn('!mZipExtractionBusy&&!mZipBatchCreationBusy;',ui)

if __name__=="__main__":
    unittest.main()
