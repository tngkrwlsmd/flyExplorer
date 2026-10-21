"""F08 read-only ZIP inspection source contracts; no runtime is launched."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
def read(p):
    return (ROOT/p).read_text(encoding="utf-8-sig")

class ZipInspectionSourceContracts(unittest.TestCase):
    def test_format_bounds_and_fail_closed(self):
        s=read("src/base/zip_inspection.h")
        for v in ("kMaxZipBytes=16u*1024u*1024u","kMaxEntries=128",
                  "kMaxExpandedBytes=64ull*1024ull*1024ull",
                  "kMaxSingleBytes=32u*1024u*1024u",
                  "FILE_FLAG_OPEN_REPARSE_POINT","FILE_SHARE_READ",
                  "0x06054b50u","0x02014b50u","0x04034b50u",
                  "name.find(L'\\\\')!=std::wstring::npos",
                  "segment==L\"..\"","std::towupper(c)",
                  "expanded>std::uint64_t(compressed)*100u",
                  "std::sort(intervals.begin(),intervals.end())",
                  "if(detail::same(a,b))",
                  "Status::UnsafeEntry","Status::Unsupported"):
            self.assertIn(v,s)
        for forbidden in ("DeleteFileW(", "MoveFileExW(", "CreateDirectoryW(",
                          "GENERIC_WRITE", "CREATE_ALWAYS", "std::ofstream",
                          "IFileOperation", "ShellExecute"):
            self.assertNotIn(forbidden,s)

    def test_retired_inspection_panel_has_no_live_ui_entry_point(self):
        # Keep the bounded parser contract as rollback evidence, but never
        # register an invisible inspector panel or an F08 menu command.
        menu=read("app/winui/m22_transfers.cpp")
        hdr=read("app/winui/MainWindow.xaml.h")
        xaml=read("app/winui/MainWindow.xaml")
        self.assertIn('make(L"Windows 탐색기에서 선택 열기"',menu)
        self.assertNotIn("InspectSelectedZip",menu)
        self.assertNotIn("OnCloseZipInspection",hdr)
        self.assertNotIn("ZipInspectionPanel",xaml)
        self.assertNotIn("ZipInspectionItems",xaml)
        for path in ("app/winui/m19_features.cpp",
                     "app/winui/bookmark_features.cpp",
                     "app/winui/filter_rule_features.cpp"):
            self.assertNotIn("ZipInspectionPanel",read(path))

if __name__=="__main__":
    unittest.main()
