"""F07 source contracts only; intentionally no GUI/native test execution."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class RecentActivityContracts(unittest.TestCase):
    def test_bounded_opt_in_and_zero_persistence(self):
        model=source("app/winui/recent_activity_controller.h")
        for token in ("kMaxRecentFiles=16","kMaxFolders=16","bool enabled_=false",
                      "if(!yes)clear();","void clear() noexcept",
                      "if(!enabled_||!acceptable(path))return;",
                      "recordFile(std::wstring const& path)",
                      "recordFolder(std::wstring const& path)",
                      "std::filesystem::path path(name);",
                      "path.lexically_normal().native()==name"):
            self.assertIn(token,model)
        for forbidden in ("CreateFile", "WriteFile", "RegSetValue", "SHAddToRecentDocs",
                          "std::thread", "ifstream", "ofstream"):
            self.assertNotIn(forbidden,model)

    def test_individual_removal_is_memory_only_and_matches_visible_selection(self):
        model=source("app/winui/recent_activity_controller.h")
        xaml=source("app/winui/MainWindow.xaml")
        header=source("app/winui/MainWindow.xaml.h")
        features=source("app/winui/m19_features.cpp")
        for token in ("bool removeFile(std::wstring const& path)",
                      "bool removeFolder(std::wstring const& path)",
                      "files_.erase(it);", "folders_.erase(it);",
                      "if(!enabled_||!acceptable(path))return false;"):
            self.assertIn(token,model)
        for name,handler in (("RecentActivityRemoveFileButton","OnRemoveRecentActivityFile"),
                             ("RecentActivityRemoveFolderButton","OnRemoveRecentActivityFolder")):
            self.assertIn('x:Name="'+name+'"',xaml)
            self.assertIn('Click="'+handler+'"',xaml)
            self.assertIn("void "+handler+"(",header)
            self.assertIn("void MainWindow::"+handler+"(",features)
            self.assertIn(name+"().IsEnabled(false)",features)
        removal=features.split("void MainWindow::OnRemoveRecentActivityFile(",1)[1].split(
            "void MainWindow::OnOpenRecentActivityFile(",1)[0]
        for token in ("RecentActivityPanel().Visibility()!=Visibility::Visible",
                      "unbox_value<hstring>(row.Content())!=hstring(path)",
                      'std::to_wstring(item.visits)+L"회 · "+item.path',
                      "mRecentActivity.removeFile(path)",
                      "mRecentActivity.removeFolder(item.path)",
                      "RefreshRecentActivityPanel()"):
            self.assertIn(token,removal)
        for forbidden in ("DeleteFile", "RemoveDirectory", "Recycle",
                          "CreateFileW", "std::filesystem::remove"):
            self.assertNotIn(forbidden,removal+model)

    def test_only_accepted_navigation_and_file_launch_are_recorded(self):
        main=source("app/winui/MainWindow.xaml.cpp")
        transfer=source("app/winui/m22_transfers.cpp")
        navigation=main.split("void MainWindow::OnNativeResult(",1)[1].split(
            "void MainWindow::OnNativeChange(",1)[0]
        self.assertIn("completed.kind==Kind::Applied&&completed.active&&",navigation)
        self.assertIn("!continuation&&completed.action!=Action::Refresh",navigation)
        self.assertIn("mRecentActivity.recordFolder(pane.filesystemPaths[pane.active]);",
                      navigation)
        activation=main.split("void MainWindow::OpenSelectedFolder(int side)",1)[1].split(
            "void MainWindow::OnLeftFileDoubleTapped(",1)[0]
        self.assertIn("ui->ActiveWindowTab().identity!=context.windowTabIdentity",activation)
        self.assertIn("if(result==Result::Opened)",activation)
        self.assertIn("mRecentActivity.recordFile(openedPath)",activation)
        self.assertIn("if(result==Result::Opened)",transfer)
        self.assertIn("mRecentActivity.recordFile(openedPath)",transfer)

    def test_explicit_controls_and_existing_async_reopen(self):
        xaml=source("app/winui/MainWindow.xaml")
        header=source("app/winui/MainWindow.xaml.h")
        features=source("app/winui/m19_features.cpp")
        for action in ("OnToggleRecentActivity", "OnRecentActivityOptInClicked",
                       "OnClearRecentActivity", "OnOpenRecentActivityFile",
                       "OnOpenRecentActivityFolder", "OnRecentActivitySelectionChanged"):
            self.assertIn(action,xaml)
            self.assertIn(action,header)
        self.assertIn("RecentActivityOptIn().IsChecked().GetBoolean()",features)
        self.assertIn("mRecentActivity.enable(",features)
        self.assertIn("mRecentActivity.clear();",features)
        self.assertIn("mFileOpen.request(path,DispatcherQueue()",features)
        self.assertIn("QueuePath(ActiveWindowTab().model.activePane,entry.path)",features)
        self.assertIn("ui->ActiveWindowTab().identity!=context.windowTabIdentity",features)
        self.assertIn("unbox_value<hstring>(display.Content())",features)
        self.assertIn("RecentActivityPanel().Visibility(Visibility::Collapsed);",
                      source("app/winui/bookmark_features.cpp"))
        self.assertIn("RecentActivityPanel().Visibility(Visibility::Collapsed);",
                      source("app/winui/filter_rule_features.cpp"))

if __name__=="__main__":
    unittest.main()
