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

    def test_ui_displays_only_accepted_async_report(self):
        menu=read("app/winui/m22_transfers.cpp")
        hdr=read("app/winui/MainWindow.xaml.h")
        xaml=read("app/winui/MainWindow.xaml")
        main=menu.split("void MainWindow::InspectSelectedZip(",1)[1].split(
             "void MainWindow::ShowAppFileContextMenu(",1)[0]
        for v in ("view.SelectedItem","list.SelectedItems().Size()!=1",
                  "mZipInspectionBusy=true", "std::thread([weak,dispatch,path",
                  "fxfile::zipinspect::inspect(path)",
                  "current.identity!=identity",
                  "pane.routeIds[tab]!=route",
                  "report.status!=Status::Accepted",
                  "ZipInspectionItems().Items().Clear()",
                  "ZipInspectionPanel().Visibility(Visibility::Collapsed)"):
            self.assertIn(v,main)
        self.assertIn('make(L"ZIP 내부 항목 검사 (읽기 전용)"',menu)
        self.assertIn("canInspectZip=suffix==L\".zip\"",menu)
        self.assertIn("void InspectSelectedZip(int side);",hdr)
        self.assertIn("void OnCloseZipInspection(",hdr)
        self.assertIn('x:Name="ZipInspectionPanel"',xaml)
        self.assertIn('x:Name="ZipInspectionItems"',xaml)
        self.assertIn('Click="OnCloseZipInspection"',xaml)

    def test_all_other_panels_collapse_zip_results(self):
        for path in ("app/winui/m19_features.cpp",
                     "app/winui/bookmark_features.cpp",
                     "app/winui/filter_rule_features.cpp"):
            self.assertIn("ZipInspectionPanel().Visibility(Visibility::Collapsed);",read(path))
if __name__=="__main__":
    unittest.main()
