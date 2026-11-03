"""Focused source contracts for pane tab closing and paste discoverability."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2] / "app" / "winui"


def source(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")


class PaneTabClosePasteContract(unittest.TestCase):
    def test_both_panes_request_native_close(self):
        xaml = source("MainWindow.xaml")
        self.assertEqual(xaml.count('TabCloseRequested="OnPaneTabCloseRequested"'), 2)
        impl = source("MainWindow.xaml.cpp")
        for token in ("item.IsClosable(true)", "item.MinWidth(176)", "item.MaxWidth(240)",
                      "void MainWindow::OnPaneTabCloseRequested(",
                      "args.Tab()", "current.routeIds[liveIndex]!=route",
                      "DispatcherQueue().TryEnqueue(",
                      "Command::CloseTabAt,side,index",
                      "if(visible)Refresh(", "RefreshTabs(side);",
                      "pane.tabs.size()<=1",
                      "mShellNavigation->forget(change.releasedRoute)"):
            self.assertIn(token, impl)

    def test_background_close_preserves_active_state_and_sort(self):
        model = (ROOT.parents[1] / "src" / "base" / "explorer_ui_state.cpp").read_text(encoding="utf-8")
        controller = source("window_workspace_controller.cpp")
        self.assertIn("case Command::CloseTabAt:", model)
        self.assertIn("const auto closing=command==Command::CloseTab?pane.active:tab;", model)
        self.assertIn("if(closing<pane.active)--pane.active;", model)
        self.assertIn("if(targetedClose&&closing>=modes.size())return {};", controller)
        self.assertIn("modes.erase(modes.begin()+static_cast<std::ptrdiff_t>(closing))", controller)
        self.assertIn("state.fileLists[side].sortMode=modes[pane.active]", controller)
        self.assertIn("targeted_close_preserves_active_folder_and_pane",
            (ROOT.parents[1] / "tests" / "winui" / "m20" / "m20_native_fixture.cpp").read_text(encoding="utf-8"))
        self.assertIn("tabs.dispatch(Command::CloseTabAt,0,0)",
            (ROOT.parents[1] / "tests" / "winui" / "native_workspace_replace_invariant.cpp").read_text(encoding="utf-8"))

    def test_closing_middle_tab_removes_exact_visual_item(self):
        impl = source("MainWindow.xaml.cpp")
        close = impl.split("void MainWindow::CloseFolderTab(", 1)[1].split(
            "void MainWindow::OnCloseTabClicked(", 1)[0]
        self.assertIn("const auto countBefore=pane.tabs.size();", close)
        self.assertIn("view.TabItems().Size()==countBefore", close)
        self.assertIn("mPopulatingTabs=true;", close)
        self.assertIn("view.TabItems().RemoveAt(static_cast<std::uint32_t>(index))", close)
        self.assertIn("mPopulatingTabs=wasPopulating;", close)
        self.assertNotIn("RemoveAtEnd()", close)

    def test_queued_close_uses_stable_route_not_stale_index(self):
        impl = source("MainWindow.xaml.cpp")
        handler = impl.split("void MainWindow::OnPaneTabCloseRequested(", 1)[1].split(
            "void MainWindow::OnSplitClicked(", 1)[0]
        self.assertIn("DispatcherQueue().TryEnqueue([weak,side,identity,route]", handler)
        self.assertIn("current.routeIds[liveIndex]!=route", handler)
        self.assertIn("if(liveIndex==current.routeIds.size())return;", handler)
        self.assertIn("ui->CloseFolderTab(side,liveIndex);", handler)
        self.assertNotIn("current.routeIds[index]!=route", handler)
        self.assertNotIn("ui->CloseFolderTab(side,index);", handler)

    def test_closed_tab_metadata_and_detail_completions_check_bounds_first(self):
        impl = source("MainWindow.xaml.cpp")
        meta = impl.split("const bool started=mFileMetadata.start(", 1)[1].split(
            "if(!started){", 1)[0]
        detail = impl.split("const bool started=mFileDetails.start(", 1)[1].split(
            "if(!started)listState.invalidateDetails();", 1)[0]
        for callback in (meta, detail):
            self.assertIn("if(ui->mClosing||side<0||side>1)return;", callback)
            bounds = "if(tab>=pane.tabs.size()||tab>=pane.routeIds.size()||"
            self.assertIn(bounds, callback)
            self.assertIn("tab>=pane.pending.size()||pane.active!=tab||", callback)
            self.assertIn("pane.routeIds[tab]!=route", callback)
            self.assertLess(callback.index(bounds), callback.index("pane.tabs[tab].snapshot()"))
        self.assertLess(meta.index("current.acceptsMetadata(ticket,route,tab)"),
                        meta.index("pane.tabs[tab].snapshot()"))

    def test_closing_tab_before_active_rebases_route_owned_list_state(self):
        controller = source("window_workspace_controller.cpp")
        list_state = source("file_list_state.h")
        group = source("file_group_tab_cache.h")
        collapse = source("file_group_presentation.h")
        impl = source("MainWindow.xaml.cpp")
        native = (ROOT.parents[1] / "tests" / "winui" /
                  "native_workspace_replace_invariant.cpp").read_text(encoding="utf-8")
        self.assertIn("state.fileLists[side].onTabClosed(closing,result.releasedRoute,side);",
                      controller)
        for term in ("groupTabCache.onTabClosed(removed,closedRoute,side)",
                     "groupCollapse.shiftTabAfterClose(removed,side)",
                     "if(visibleRoute&&visibleTab>removed)--visibleTab",
                     "if(fileCommandReveal.route&&fileCommandReveal.tab>removed)",
                     "if(metadataRoute==closedRoute)invalidateMetadata()",
                     "if(route==closedRoute)invalidateDetails()"):
            self.assertIn(term, list_state)
        self.assertIn("saved.collapse.shiftTabAfterClose(removed,side)", group)
        self.assertIn("collapse_.shiftTabAfterClose(removed,side)", group)
        self.assertIn("void shiftTabAfterClose(std::size_t removed,int side)", collapse)
        close = impl.split("void MainWindow::CloseFolderTab(", 1)[1].split(
            "void MainWindow::OnCloseTabClicked(", 1)[0]
        self.assertIn("if(index<previousActive){", close)
        for call in ("FillFiles(side);", "ScheduleFileMetadata(side);",
                     "ScheduleFileDetails(side);", "UpdateCommandAvailability();"):
            self.assertIn(call, close)
        self.assertIn("list.visibleRoute==activeRoute&&list.visibleTab==0", native)
        self.assertIn("list.groupCollapse.matches(activeRoute,0,0)", native)
        self.assertIn("list.metadataTab==1&&list.tab==1", native)

    def test_search_context_survives_only_same_route_tab_renumber(self):
        controller = source("search_controller.cpp")
        header = source("search_controller.h")
        features = source("m19_features.cpp")
        window = source("MainWindow.xaml.cpp")
        self.assertIn("static bool rebaseAfterEarlierTabClosed(", header)
        impl = controller.split("bool SearchController::rebaseAfterEarlierTabClosed(", 1)[1].split(
            "SearchController::StartStatus SearchController::start(", 1)[0]
        for token in ("!stored.route", "stored.route!=live.route",
                      "stored.tab<=live.tab", "stored.tab=live.tab",
                      "sameContext(stored,live)", "stored.tab=previousTab"):
            self.assertIn(token, impl)
        self.assertIn("a.tab==b.tab", controller)  # Original strict contract remains.
        completed = features.split("void MainWindow::OnSearchCompleted(", 1)[1].split(
            "std::wstring MainWindow::SelectedSearchMatchPath()", 1)[0]
        self.assertLess(completed.index("rebaseAfterEarlierTabClosed("),
                        completed.index("mSearchController.accept("))
        close = window.split("void MainWindow::CloseFolderTab(", 1)[1].split(
            "void MainWindow::OnCloseTabClicked(", 1)[0]
        self.assertIn("!visible&&index<previousActive&&model.activePane==side", close)
        self.assertIn("mSearchResultValid", close)
        self.assertIn("rebaseAfterEarlierTabClosed(mSearchResultContext,live)", close)
        self.assertIn("if(activeSearch)mSearchController.invalidate();", close)
        locate = features.split("void MainWindow::OnLocateSearchMatch(", 1)[1].split(
            "void MainWindow::OnSelectSearchRecent(", 1)[0]
        self.assertIn("reveal.tab=mSearchResultContext.tab;", locate)

    def test_paste_visible_and_existing_route_preserved(self):
        toolbar = source("FileToolbar.xaml")
        self.assertIn('DefaultLabelPosition="Right"', toolbar)
        self.assertIn('x:Name="WindowsPasteButton" Style="{StaticResource ExplorerPasteCommandButtonStyle}"', toolbar)
        self.assertIn('ToolTipService.ToolTip="붙여넣기 (Ctrl+V)"', toolbar)
        self.assertEqual(toolbar.count('LabelPosition="Collapsed"'), 8)
        self.assertIn('Click="OnWindowsPaste"', toolbar)
        self.assertIn("void FileToolbar::OnWindowsPaste(", source("FileToolbar.xaml.cpp"))
        self.assertIn("ui->PasteFromWindowsClipboard();", source("MainWindow.xaml.cpp"))


if __name__ == "__main__":
    unittest.main()
