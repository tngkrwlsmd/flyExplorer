"""Completion must update committed history chrome after pending resolves."""

from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]

def compact(s):
    return re.sub(r"\s+", " ", s)

class WindowTabChromeContract(unittest.TestCase):
    def test_navigation_chrome_recomputes_from_active_history(self):
        source=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        header=(ROOT/"app/winui/MainWindow.xaml.h").read_text(encoding="utf-8")
        self.assertIn("void UpdateNavigationChrome();",header)
        helper=source.split("void MainWindow::UpdateNavigationChrome()",1)[1].split(
            "void MainWindow::Refresh(",1)[0]
        self.assertIn("pane.pending[pane.active]!=0",helper)
        self.assertIn("nav.canBack()&&!pending",helper)
        self.assertIn("nav.canForward()&&!pending",helper)
        self.assertIn("nav.snapshot().folder.valid()",helper)

    def test_resolved_no_change_and_errors_recompute_chrome(self):
        source=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        complete=source.split("void MainWindow::OnNativeResult(",1)[1].split(
            "void MainWindow::OnNativeChange(",1)[0]
        for current,next_kind in (
            ("NoChange","Failed"),
            ("Failed","Rejected"),
            ("Rejected","Extended"),
        ):
            block=complete.split("if(completed.kind==Kind::"+current+")",1)[1].split(
                "if(completed.kind==Kind::"+next_kind+")",1)[0]
            self.assertIn("UpdateNavigationChrome()",block,current)
        refresh=source.split("void MainWindow::Refresh(",1)[1].split(
            "bool MainWindow::OpenFolder(",1)[0]
        self.assertIn("UpdateNavigationChrome()",refresh)

    def test_f06_middle_click_targets_clicked_filesystem_folder(self):
        drag=compact((ROOT/"app/winui/m23_drag.cpp").read_text(encoding="utf-8"))
        main=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        head=(ROOT/"app/winui/MainWindow.xaml.h").read_text(encoding="utf-8")
        self.assertIn("void OpenFolderInNewPaneTab(int side,std::wstring path);",head)
        self.assertIn("IsMiddleButtonPressed()",drag)
        self.assertIn("pane.pending[pane.active]",drag)
        self.assertIn("pane.tabs[pane.active].indexedItem(",drag)
        self.assertIn("indexed->isFolder()&&indexed->isFileSystem()",drag)
        self.assertIn("const auto path=indexed->parsingName;",drag)
        self.assertIn("OpenFolderInNewPaneTab(side,path);",drag)
        self.assertIn("args.Handled(true);",drag)
        open_tab=main.split("void MainWindow::OpenFolderInNewPaneTab(",1)[1].split(
            "void MainWindow::OnNewTabClicked(",1)[0]
        for fragment in ("model.split","kMaxTabsPerPane","Command::AddTab,side",
                         "mWorkspaceRestore.reset(side);","QueuePath(side,std::move(path));",
                         "DispatcherQueue().TryEnqueue(", "originWindow",
                         "active.routeIds[active.active]!=originRoute"):
            self.assertIn(fragment,open_tab)

    def test_f06_breadcrumb_middle_click_uses_tagged_segment(self):
        main=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        snippet=main.split("void MainWindow::UpdateBreadcrumb(",1)[1].split(
            "void MainWindow::OnBreadcrumbSegmentClicked(",1)[0]
        self.assertIn("button.AddHandler(UIElement::PointerPressedEvent()",snippet)
        self.assertIn("IsMiddleButtonPressed()",snippet)
        self.assertIn("unbox_value<hstring>(target.Tag())",snippet)
        self.assertIn("OpenFolderInNewPaneTab(",snippet)
        self.assertIn("args.Handled(true);",snippet)

    def test_f06_quoted_absolute_and_unc_address_preserve_inner_path(self):
        main=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        portion=main.split("std::wstring ResolveFriendlyAddress(",1)[1].split(
            "bool SupportsSortableMetadataDrive(",1)[0]
        self.assertIn('find_first_not_of(L" \\t\\r\\n")',portion)
        self.assertIn('value[first]==L\'"\' && value[last]==L\'"\'',portion)
        self.assertIn("value.substr(first+1,last-first-1)",portion)
        self.assertNotIn("replace(",portion)
        address=main.split("void MainWindow::OnAddressKeyDown(",1)[1].split(
            "void MainWindow::OnAddressGotFocus(",1)[0]
        self.assertIn("OpenFolder(ResolveFriendlyAddress(",address)

    def test_failed_window_tab_probe_separates_route_and_chrome(self):
        harness=(ROOT/"tests/winui/test_v7_window_tabs_gui.py").read_text(encoding="utf-8")
        for token in ("V7_CLEANUP_ROUTE_NESTED","V7_CLEANUP_BACK_EXISTS",
                      "V7_CLEANUP_BACK_ENABLED","V7_CLEANUP_WINDOW_TABS",
                      "V7_CLEANUP_STATUS_PENDING"):
            self.assertIn(token,harness)

if __name__=="__main__":
    unittest.main()
