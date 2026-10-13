"""F02 source/XAML invariants: cached metadata, route identity and opt-in UI."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
X="{http://schemas.microsoft.com/winfx/2006/xaml}Name"
def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class F02ReadOnlyDetailsContract(unittest.TestCase):
    def test_xaml_readonly_named_accessible_details(self):
        doc=ET.parse(ROOT/"app/winui/MainWindow.xaml")
        nodes={e.get(X):e for e in doc.iter() if e.get(X)}
        self.assertEqual(nodes["FileInfoPane"].get("Visibility"),"Collapsed")
        self.assertEqual(nodes["FileInfoColumn"].get("Width"),"0")
        self.assertEqual(nodes["FileInfoToggleButton"].get("Click"),"OnToggleFileInfoPane")
        for field in ("FileInfoHint","FileInfoName","FileInfoType",
                      "FileInfoLocation","FileInfoSize","FileInfoModified"):
            self.assertEqual(nodes[field].tag.split("}")[-1],"TextBlock")
            self.assertEqual(nodes[field].get("TextWrapping"),"Wrap")
            self.assertIsNone(nodes[field].get("AutomationProperties.Name"))

    def test_window_tab_owns_opt_in_and_no_global_preferences(self):
        state=read("app/winui/window_tab_state.h")
        main=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("bool fileInfoPaneVisible=false;",state)
        source=main.split("void MainWindow::OnToggleFileInfoPane(",1)[1].split(
            "void MainWindow::UpdateFooterSummary(",1)[0]
        for token in ("state.fileInfoPaneVisible=!state.fileInfoPaneVisible;",
                      "ApplyFileInfoPaneLayout();","UpdateFileInfoPane();"):
            self.assertIn(token,source)
        self.assertNotIn("PersistPreferences()",source)
        self.assertNotIn("GetFileAttributes",source)
        self.assertNotIn("SHGet",source)

    def test_details_width_drives_narrow_file_list_profile(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        profile=main.split("int MainWindow::DetailLayoutProfile() const",1)[1].split(
            "std::array<GridLength,4> MainWindow::DetailColumnWidths(",1)[0]
        self.assertIn("ActiveWindowTab().fileInfoPaneVisible?260.0:0.0",profile)
        self.assertIn("mShellWidth-nav-17.0-details",profile)
        toggle=main.split("void MainWindow::OnToggleFileInfoPane(",1)[1].split(
            "void MainWindow::ApplyFileInfoPaneLayout(",1)[0]
        for token in ("ApplyFileInfoPaneLayout();",
                      "const int profile=DetailLayoutProfile();",
                      "mDetailLayoutProfiles[side]=profile;",
                      "FillFiles(side);","UpdateFileInfoPane();"):
            self.assertIn(token,toggle)

    def test_live_route_and_cached_metadata_only(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        source=main.split("void MainWindow::UpdateFileInfoPane(",1)[1].split(
            "void MainWindow::UpdateFooterSummary(",1)[0]
        for token in (
            "view.SelectedItems().Size()!=1",
            "pane.pending[pane.active]",
            "state.visibleRoute!=route||state.visibleTab!=pane.active",
            "state.renderedLogical.begin()",
            "path!=state.renderedPaths[rendered]",
            "snapshot.residentIndex(logical,resident)",
            "state.metadataCurrent(route,pane.active",
            "state.isCurrent(route,pane.active",
            "FileInfoName().Text(hstring(name))",
            "FileInfoModified().Text(L\"정보 없음\")",
        ):
            self.assertIn(token,source)
        for forbidden in ("GetFileAttributesW(", "FindFirstFileW(", "SHGetFileInfo",
                          "GetFileSizeEx(", "std::filesystem::exists(",
                          "mFileMetadata.start(", "mFileDetails.start("):
            self.assertNotIn(forbidden,source)
        self.assertIn("UpdateFileInfoPane();",main)
        self.assertIn("ApplyFileInfoPaneLayout();",main)

if __name__=="__main__":
    unittest.main()
