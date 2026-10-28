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

    def test_px02_history_off_empty_and_populated_have_distinct_accessible_states(self):
        xaml=source("app/winui/MainWindow.xaml")
        features=source("app/winui/m19_features.cpp")
        model=source("app/winui/recent_activity_controller.h")
        ui=xaml.split('x:Name="RecentActivityPanel"',1)[1].split(
            'x:Name="FilterRulePanel"',1)[0]
        refresh=features.split("void MainWindow::RefreshRecentActivityPanel(){",1)[1].split(
            "void MainWindow::OnToggleRecentActivity(",1)[0]
        for term in (
            'x:Name="RecentActivityStateText"',
            'AutomationProperties.Name="최근 활동 기록 상태"',
            '기록 꺼짐 · 파일 및 폴더 활동을 수집하지 않습니다.',
        ):
            self.assertIn(term,ui)
        for term in (
            'const bool enabled=mRecentActivity.enabled();',
            'RecentActivityFiles().IsEnabled(enabled&&!recent.empty());',
            'RecentActivityFolders().IsEnabled(enabled&&!frequent.empty());',
            'RecentActivityClearButton().IsEnabled(',
            'enabled&&(!recent.empty()||!frequent.empty()));',
            'if(!enabled)',
            'else if(recent.empty()&&frequent.empty())',
            '기록 켜짐 · 이 세션에 저장된 활동이 아직 없습니다.',
            '기록 켜짐 · 최근 파일 ',
            'std::to_wstring(recent.size())',
            'std::to_wstring(frequent.size())',
            'RecentActivityStateText().Text(hstring(state));',
            'RecentActivityOpenFileButton().IsEnabled(false);',
            'RecentActivityOpenFolderButton().IsEnabled(false);',
        ):
            self.assertIn(term,refresh)
        self.assertLess(
            refresh.index('const bool enabled=mRecentActivity.enabled();'),
            refresh.index('RecentActivityStateText().Text(hstring(state));'))
        # Do not count a disabled/empty control as consent or silently enable
        # persistence or scan outside this application's explicit session.
        self.assertIn('bool enabled_=false;',model)
        self.assertIn('if(!yes)clear();',model)
        self.assertNotIn('CreateFile',model)
        for operation in (
            'void MainWindow::OnToggleRecentActivity(',
            'void MainWindow::OnRecentActivityOptInClicked(',
            'void MainWindow::OnClearRecentActivity(',
        ):
            handler=features.split(operation,1)[1].split('}\n',1)[0]
            self.assertIn('RefreshRecentActivityPanel();',handler)

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
        self.assertIn("const auto& path=pane.filesystemPaths[pane.active];",
                      navigation)
        self.assertIn("mRecentActivity.recordFolder(path);",navigation)
        self.assertLess(navigation.index("const auto& path=pane.filesystemPaths[pane.active];"),
                        navigation.index("mRecentActivity.recordFolder(path);"))
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
