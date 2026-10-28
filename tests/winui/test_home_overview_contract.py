"""PX02 unified Home overview: bounded source-level behavioral contracts.

No real filesystem/home-profile scan or GUI test happens in this module.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class HomeOverviewContracts(unittest.TestCase):
    def test_one_accessible_home_view_contains_all_three_sources(self):
        xaml = read("app/winui/MainWindow.xaml")
        begin = xaml.index('x:Name="HomeOverviewPanel"')
        end = xaml.index('x:Name="BookmarkPanel"', begin)
        home = xaml[begin:end]
        for token in (
            'Visibility="Collapsed" MaxHeight="280"',
            'AutomationProperties.Name="홈 대시보드 · 북마크와 세션 활동"',
            'x:Name="HomePinnedItems"',
            'x:Name="HomeRecentItems"',
            'x:Name="HomeFrequentItems"',
            'x:Name="HomeActivityPrivacyText"',
            'x:Name="HomePinnedStatus"',
            'Click="OnHomeFolderClicked"',
            'Click="OnHomeManageBookmarksClicked"',
            'Click="OnHomeManageActivityClicked"',
        ):
            self.assertIn(token, home)
        self.assertNotIn('IsChecked="True"', home)
        self.assertNotIn('WebView', home)

    def test_home_entry_points_share_one_view_and_preserve_folder_navigation(self):
        main = read("app/winui/MainWindow.xaml.cpp")
        features = read("app/winui/m19_features.cpp")
        header = read("app/winui/MainWindow.xaml.h")
        self.assertIn("if(target==0)ui->ShowHomeOverview();", main)
        self.assertIn("ShowHomeOverview();", main.split(
            "void MainWindow::OnHomeClicked(", 1)[1].split(
            "void MainWindow::OnDocumentsClicked(", 1)[0])
        self.assertIn("HomeOverviewPanel().Visibility(Visibility::Collapsed);",
                      main.split("bool MainWindow::OpenFolder(", 1)[1].split(
                          "void MainWindow::ActivatePane(", 1)[0])
        for signature in ("void ShowHomeOverview();", "void RefreshHomeOverview();",
                          "void OpenRecentActivityFilePath(std::wstring const& path);"):
            self.assertIn(signature, header)
        home = features.split("void MainWindow::ShowHomeOverview(){", 1)[1].split(
            "void MainWindow::RefreshHomeOverview(){", 1)[0]
        for token in (
            "BookmarkPanel().Visibility(Visibility::Collapsed);",
            "RecentActivityPanel().Visibility(Visibility::Collapsed);",
            "WorkspacePanel().Visibility(Visibility::Collapsed);",
            "SearchPanel().Visibility(Visibility::Collapsed);",
            "FilterRulePanel().Visibility(Visibility::Collapsed);",
            "HomeOverviewPanel().Visibility(Visibility::Visible);",
            "RefreshHomeOverview();",
            "OpenFolder(HomePath().native());",
            "OnToggleBookmarks(nullptr,RoutedEventArgs{nullptr});",
            "OnToggleRecentActivity(nullptr,RoutedEventArgs{nullptr});",
        ):
            self.assertIn(token, home)

    def test_bounded_tiles_validate_stale_bookmarks_and_session_folders(self):
        features = read("app/winui/m19_features.cpp")
        home = features.split("void MainWindow::RefreshHomeOverview(){", 1)[1].split(
            "void MainWindow::RefreshRecentActivityPanel(){", 1)[0]
        for token in (
            "constexpr std::size_t kPreview=4;",
            "const auto pinnedLimit=(std::min)(bookmarks.size(),kPreview);",
            "const auto fileLimit=(std::min)(recent.size(),kPreview);",
            "const auto folderLimit=(std::min)(frequent.size(),kPreview);",
            "const auto weak=get_weak();",
            "item.path==target&&item.name==name",
            "if(found==current.end())",
            "if(found==folders.end())",
            "HomeOverviewPanel().Visibility()!=Visibility::Visible",
            "ui->OpenRecentActivityFilePath(path);",
            "ui->OpenFolder(target);",
            "HomePinnedItems().Children();",
            "HomeRecentItems().Children();",
            "HomeFrequentItems().Children();",
        ):
            self.assertIn(token, home)
        self.assertNotIn("std::filesystem::exists(", home)
        self.assertNotIn("SHAddToRecentDocs(", home)
        self.assertNotIn("DeleteFileW(", home)
        self.assertNotIn("CreateProcessW(", home)

    def test_recent_files_use_existing_guarded_async_opener(self):
        features = read("app/winui/m19_features.cpp")
        body = features.split("void MainWindow::OpenRecentActivityFilePath(", 1)[1].split(
            "void MainWindow::OnOpenRecentActivityFolder(", 1)[0]
        for token in (
            "!mRecentActivity.enabled()",
            "mFileOperations.busy()",
            "RecentActivityController::acceptable(path)",
            "std::find(recent.begin(),recent.end(),path)==recent.end()",
            "const auto context=FileOperationContext(side);",
            "mFileOpen.request(path,DispatcherQueue(),",
            "ui->ActiveWindowTab().identity!=context.windowTabIdentity",
            "live.tab==context.tab&&live.route==context.route",
            "live.visibleFolder==context.visibleFolder",
            "if(result==Open::Result::Opened)",
            "ui->mRecentActivity.recordFile(path);",
            "ui->RefreshHomeOverview();",
        ):
            self.assertIn(token, body)
        legacy = features.split("void MainWindow::OnOpenRecentActivityFile(", 1)[1].split(
            "void MainWindow::OpenRecentActivityFilePath(", 1)[0]
        self.assertIn("OpenRecentActivityFilePath(path);", legacy)
        self.assertIn("unbox_value<hstring>(display.Content())!=hstring(path)", legacy)

    def test_history_privacy_defaults_off_and_other_panels_hide_home(self):
        model = read("app/winui/recent_activity_controller.h")
        features = read("app/winui/m19_features.cpp")
        bookmark = read("app/winui/bookmark_features.cpp")
        filter_source = read("app/winui/filter_rule_features.cpp")
        self.assertIn("bool enabled_=false;", model)
        self.assertIn("if(!yes)clear();", model)
        self.assertIn("void clear() noexcept", model)
        home = features.split("void MainWindow::RefreshHomeOverview(){", 1)[1].split(
            "void MainWindow::RefreshRecentActivityPanel(){", 1)[0]
        self.assertLess(home.index("if(!mRecentActivity.enabled()){"),
                        home.index("const auto& recent=mRecentActivity.files();"))
        self.assertIn("기록 꺼짐 · 기존 활동을 읽지 않고", home)
        self.assertIn("if(recent.empty())appendEmpty(", home)
        self.assertIn("if(frequent.empty())appendEmpty(", home)
        self.assertIn("L\"기록 켜짐 · 최근 파일 \"", home)
        for name in ("OnToggleRecentActivity", "OnToggleWorkspaces",
                     "OnToggleSearch"):
            section = features.split(f"void MainWindow::{name}(", 1)[1].split(
                "\n}", 1)[0]
            self.assertIn("HomeOverviewPanel().Visibility(Visibility::Collapsed);",
                          section)
        for part in (bookmark, filter_source):
            self.assertIn("HomeOverviewPanel().Visibility(Visibility::Collapsed);", part)
        self.assertIn("if(HomeOverviewPanel().Visibility()==Visibility::Visible)",
                      bookmark)
        self.assertIn("if(HomeOverviewPanel().Visibility()==Visibility::Visible)",
                      features)


if __name__ == "__main__":
    unittest.main()
