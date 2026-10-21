"""F08 bounded multi-entry ZIP Store/Deflate extraction source contracts; NOT EXECUTED."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ZipStoreBatchExtractorContracts(unittest.TestCase):
    def test_all_members_validated_before_staging(self):
        s=read("src/base/zip_store_batch_extractor.h")
        checks=(
            "zipinspect::kMaxZipBytes",
            "zipbatch::kMinFiles",
            "zipbatch::kMaxFiles",
            "zipbatch::kMaxTotalBytes-uncompressedTotal",
            "u32(bytes,eocd)!=0x06054b50u",
            "u32(bytes,localCursor)!=0x04034b50u",
            "u32(bytes,directoryCursor)!=0x02014b50u",
            "central+centralBytes!=eocd",
            "u32(bytes,directoryCursor+42)!=localCursor",
            "(method!=0&&method!=8)",
            "(method==8&&versionNeeded!=20)",
            "u16(bytes,localCursor+8)!=method",
            "(method==0&&packed!=unpacked)",
            "unpacked>fxfile::zipbatch::kMaxTotalBytes-uncompressedTotal",
            "fxfile::ziprawdeflate::kMaxPackedBytes",
            "fxfile::ziprawdeflate::kMaxRatio",
            "ziprawdeflate::inflateExact(",
            "uncompressedTotal+=unpacked",
            "member.content.size()!=unpacked",
            "localCursor!=central||directoryCursor!=eocd",
            "u16(bytes,localCursor+6)!=flags",
            "fxfile::zipstorecompat::supportedFlags(flags)",
            "fxfile::zipstorecompat::supportedDosVersion(versionNeeded)",
            "fxfile::zipstorecompat::sameDosTime(",
            "fxfile::zipstorecompat::decodeName(",
            "detail::memberPath(",
            "name,entryRoot,entryChild,entryLeaf",
            "archiveChildren.push_back(entryChild)",
            "archiveChildren.size()>=",
            "previous.name,entryChild",
            "previous.child,entryChild",
            "staging.nestedChildren",
            "++staging.createdChildren;",
            "CreateDirectoryW(childPath.c_str(),nullptr)",
            "rootMode!=!entryRoot.empty()",
            "archiveRoot,entryRoot",
            "previous.name,entryLeaf",
            "staging.nestedRoot",
            "CreateDirectoryW(staging.nestedRoot.c_str(),nullptr)",
            "previous.child,entryChild",
            "std::equal(bytes.begin()+localCursor+30u",
            "zipstore::detail::crc32(member.content)!=checksum",
            "GetFileAttributesW(target.c_str())",
            "GetTempFileNameW(parent.c_str()",
            "CreateDirectoryW(staging.path.c_str(),nullptr)",
            "CREATE_NEW",
            "details.nNumberOfLinks!=1",
            "members[i].content,cancellation)",
            "MoveFileExW(staging.path.c_str(),target.c_str()",
            "MOVEFILE_WRITE_THROUGH",
            "staging.owned=false",
            "Status::Cancelled",
            "zipstore::detail::cancelled(cancellation)",
            "RemoveDirectoryW(path.c_str())",
        )
        for token in checks:
            self.assertIn(token,s)
        self.assertLess(s.index("zipstore::detail::crc32(member.content)!=checksum"),
                        s.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(s.index("ziprawdeflate::inflateExact("),
                        s.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(s.index("detail::memberPath("),
                        s.index("GetTempFileNameW(parent.c_str()"))
        self.assertLess(s.index("result.output=target;"),
                        s.index("::MoveFileExW(staging.path.c_str()"))
        for forbidden in ("MOVEFILE_REPLACE_EXISTING|", "CREATE_ALWAYS",
                          "std::filesystem::remove_all(", "ShellExecuteW("):
            self.assertNotIn(forbidden,s)

    def test_ui_exact_origin_and_menu(self):
        ui=read("app/winui/m22_transfers.cpp")
        header=read("app/winui/MainWindow.xaml.h")
        body=ui.split("void MainWindow::ExtractSelectedBatchZip(int side)",1)[1].split(
            "void MainWindow::ExtractSelectedZip(int side)",1)[0]
        for x in ("view.SelectedItems().Size()!=1", "mZipBatchExtractionBusy=true;",
                  "mZipBatchCancel=cancel;",
                  "zipbatchextract::extractMany(source,cancel.get())",
                  "active.identity!=identity",
                  "pane.routeIds[tab]!=route",
                  "pane.filesystemPaths[tab]!=folder",
                  "NavigationAction::Refresh"):
            self.assertIn(x,body)
        self.assertIn('make(L"ZIP 여러 파일 해제 (Store/Deflate, 2~8개)"',ui)
        self.assertIn("void ExtractSelectedBatchZip(int side);",header)
        self.assertIn("bool mZipBatchExtractionBusy=false;",header)
        self.assertIn("!mZipBatchExtractionBusy;",ui)

if __name__=="__main__":
    unittest.main()
