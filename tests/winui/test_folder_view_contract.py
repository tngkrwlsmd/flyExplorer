"""F14 source contracts; these do not certify Windows runtime behavior."""
from pathlib import Path
import unittest

R=Path(__file__).resolve().parents[2]
def src(name):
    return (R/name).read_text(encoding="utf-8-sig")

class FolderViewContracts(unittest.TestCase):
    def test_bounded_inmemory_explicit_overrides(self):
        h=src("app/winui/folder_view_controller.h")
        for token in ("kMaxOverrides=64","bool remember(std::wstring const& folder,int mode)",
                      "bool lookup(std::wstring const& folder,int& mode) const",
                      "bool forget(std::wstring const& folder)",
                      "std::vector<Entry> items_{}",
                      "mode<0||mode>6","items_.pop_back();",
                      "path.lexically_normal().native()==folder"):
            self.assertIn(token,h)
        for forbidden in ("CreateFile", "WriteFile", "RegSetValue", "APPDATA",
                          "std::thread", "std::filesystem::remove("):
            self.assertNotIn(forbidden,h)

    def test_view_menu_is_explicit(self):
        x=src("app/winui/FileToolbar.xaml")
        h=src("app/winui/FileToolbar.xaml.h")
        c=src("app/winui/FileToolbar.xaml.cpp")
        main=src("app/winui/MainWindow.xaml.cpp")
        for action in ("OnRememberFolderView","OnForgetFolderView"):
            self.assertIn('Click="'+action+'"',x)
            self.assertIn("void "+action+"(",h)
            self.assertIn("FileToolbar::"+action+"(",c)
        self.assertIn("SetFolderViewAction",h+c+main)
        self.assertIn("RememberCurrentFolderView(remember)",main)

    def test_navigation_only_not_refresh_or_session_restore(self):
        main=src("app/winui/MainWindow.xaml.cpp")
        nav=main.split("void MainWindow::OnNativeResult(",1)[1].split(
            "void MainWindow::OnNativeChange(",1)[0]
        for token in ("completed.kind==Kind::Applied&&completed.active&&",
                      "!continuation&&completed.action!=Action::Refresh",
                      "mWorkspaceRestore.active(completed.side)",
                      "if(!restoring&&mFolderViews.lookup(path,remembered))",
                      "state.viewMode=static_cast<FileViewMode>(remembered)",
                      "if(ActiveWindowTab().model.activePane==completed.side)",
                      "fileBar()->SetViewIndex(remembered)"):
            self.assertIn(token,nav)
        self.assertLess(nav.index("mFolderViews.lookup(path,remembered)"),
                        nav.index("Refresh(activeStatus);"))
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)",
                      src("app/winui/m20_shell.cpp"))
        self.assertNotIn("mPreferencesCoordinator.setDefaultViewMode",
                         nav)

    def test_command_rechecks_exact_active_route(self):
        code=src("app/winui/m20_shell.cpp")
        command=code.split("void MainWindow::RememberCurrentFolderView(bool remember)",1)[1].split(
            "void MainWindow::UpdateView(int selection)",1)[0]
        for token in ("pane.pending[pane.active]",
                      "shown.visibleRoute!=pane.routeIds[pane.active]",
                      "shown.visibleTab!=pane.active",
                      "FolderViewController::validFolder(folder)",
                      "mFolderViews.remember(folder,",
                      "mFolderViews.forget(folder)"):
            self.assertIn(token,command)
        self.assertNotIn("PersistPreferences()",command)

if __name__=="__main__":
    unittest.main()
