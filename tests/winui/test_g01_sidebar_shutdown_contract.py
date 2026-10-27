"""G01 close: detached NavigationSidebar workers must not touch released XAML.

Source-only regression. Product compilation and interactive shutdown are separate.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
SIDEBAR = (ROOT / "app/winui/NavigationSidebar.xaml.cpp").read_text(encoding="utf-8")
HEADER = (ROOT / "app/winui/NavigationSidebar.xaml.h").read_text(encoding="utf-8")

class G01SidebarShutdownContract(unittest.TestCase):
    def test_owner_closes_sidebar_before_xaml_disposal(self):
        close = MAIN.split("void MainWindow::PrepareForClose() noexcept", 1)[1].split(
            "MainWindow::~MainWindow()", 1)[0]
        close_start = close.index("mClosing=true;")
        sidebar = close.index("->PrepareForClose();", close_start)
        for boundary in ("mDetailColumnDragTimer.Stop();",
                         "AddressSuggestionPanel().Visibility(",
                         "mSessionCoordinator.prepareForClose();"):
            self.assertLess(sidebar, close.index(boundary))
        self.assertLess(close_start, sidebar)

    def test_close_invalidates_worker_generation_and_callbacks_without_xaml(self):
        self.assertIn("void PrepareForClose() noexcept;", HEADER)
        self.assertIn("bool mClosing=false;", HEADER)
        body = SIDEBAR.split("void NavigationSidebar::PrepareForClose() noexcept", 1)[1].split(
            "void NavigationSidebar::SetNavigateCallback", 1)[0]
        for fragment in ("if(mClosing)return;", "mClosing=true;",
                         "if(mTreeCancel)mTreeCancel->store(true);",
                         "++mTreeGeneration;", "mTreePending=false;",
                         "mHandler={};", "mTreeCurrent={};", "mTreeNavigate={};"):
            self.assertIn(fragment, body)
        for disallowed in ("FolderTreeView()", "FolderTreeStatus()", "RootNodes().Clear()"):
            self.assertNotIn(disallowed, body)

    def test_both_detached_worker_results_check_shutdown_before_projection(self):
        self.assertEqual(
            SIDEBAR.count("if(auto self=weak.get();self&&!self->mClosing){"), 2
        )
        self.assertIn("if(mClosing||!IsCurrentTreeOwner()", SIDEBAR)
        self.assertIn("if(mClosing||!mTreeVisible||!mTreeCurrent)", SIDEBAR)
        self.assertIn("if(mClosing||width!=16", SIDEBAR)
        for method in ("OnTreeExpanding", "OnTreeCollapsed", "OnTreeSelectionChanged"):
            part = SIDEBAR.split("void NavigationSidebar::" + method,1)[1]
            self.assertIn("if(mClosing)return;", part[:160])
        for name in ("Home","Documents","Downloads","ThisPC",
                     "Desktop","Pictures","Music","Videos"):
            part = SIDEBAR.split("void NavigationSidebar::On"+name+"Clicked", 1)[1]
            self.assertIn("if(mClosing)return;", part[:115])

if __name__ == "__main__":
    unittest.main()
