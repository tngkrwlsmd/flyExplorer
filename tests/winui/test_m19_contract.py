"""M1.9 focused source/architecture contracts (NOT a substitute for owned GUI)."""
import subprocess
import unittest
from pathlib import Path
from historical_mfc import text as historical_text

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def code(path):return (ROOT/path).read_text(encoding="utf-8-sig")
class M19IntegrationContracts(unittest.TestCase):
    def test_native_main_workspace_schema_merged_without_replacing_mfc(self):
        native=historical_text("src/fxfile/main_frame.cpp")
        self.assertIn("MainFrame::OnSaveWorkspace",native)
        self.assertIn("MainFrame::OnOpenWorkspace",native)
        self.assertIn("workspace_session::writeMarker",native)
        self.assertIn("sSnapshot.save(xpr::CharSetUtf16)",native)
        self.assertIn("XPR_STRING_LITERAL(\"schema\"), 1",native)

    def test_native_main_explicit_search_history_merged(self):
        native=historical_text("src/fxfile/search_dlg.cpp")
        self.assertIn("OnClearRecent",native)
        self.assertIn("OnRecentLocation",native)
        self.assertIn("IDC_SEARCH_REMEMBER",native)
        self.assertIn("sIncDirDeque.size() == 1 && sExcDirDeque.empty()",native)
        self.assertIn("RecentLocations",native)

    def test_preview_build_links_new_standalone_win32_features(self):
        build=code("app/winui/flyExplorer.project-template.xml")
        for name in ("m19_workspace.cpp","m19_search.cpp","m19_features.cpp",
                     "search_controller.cpp","shell_isolated_supervisor.cpp",
                     "directory_watcher.cpp","shell_namespace_watcher.cpp"):
            self.assertIn(name,build)

    def test_preview_workspace_never_mutates_mfc_user_conf(self):
        src=code("app/winui/m19_workspace.cpp")
        for contract in ("FILE_FLAG_OPEN_REPARSE_POINT","kMaxBytes=1048576",
                         "CREATE_NEW","schema!=1","prepared.selected[pane]",
                         "output=std::move(prepared)"):
            self.assertIn(contract,src)
        for forbidden in ("APPDATA","fxfile-main.conf","RegSetValue","ShellExecute"):
            self.assertNotIn(forbidden,src)

    def test_search_default_opt_out_and_no_namespace_registration(self):
        xaml=code("app/winui/MainWindow.xaml")
        self.assertIn('x:Name="SearchRememberBox" IsChecked="False"',xaml)
        src=code("app/winui/m19_search.cpp")
        for contract in ("kMaxWalk=2500","kMaxDepth=5","kMaxResults=100",
                         "FILE_ATTRIBUTE_REPARSE_POINT","LOCALAPPDATA",
                         "MOVEFILE_REPLACE_EXISTING"):
            self.assertIn(contract,src)
        for forbidden in ("SHChangeNotifyRegister","APPDATA\\fxfile\\conf",
                          "shell:MyComputerFolder","SetWindowLong"):
            self.assertNotIn(forbidden,src)

    def test_preview_uses_bounded_native_search_and_weak_ui_dispatch(self):
        src=code("app/winui/m19_features.cpp")
        controller=code("app/winui/search_controller.cpp")
        self.assertIn("mSearchController.start(",src)
        self.assertIn("scanFiles(",controller)
        self.assertIn("auto weak=get_weak()",src)
        self.assertIn("dispatch.TryEnqueue",src)
        self.assertIn("mSearchController.prepareForClose()",code(
          "app/winui/MainWindow.xaml.cpp"))
        self.assertIn("mShellNavigation->release(ActiveWindowTab().model)",src)
        self.assertIn("mShellNavigation->submitParsing(",src)
        self.assertIn("CreateProcessW(",src)

    def test_workspace_and_search_uia_controls_and_owned_harness(self):
        xaml=code("app/winui/MainWindow.xaml")
        for control in ("WorkspacePanelButton","WorkspaceFileBox",
                        "SaveWorkspaceButton","OpenWorkspaceButton",
                        "SearchPanelButton","SearchScopeBox","SearchTermBox",
                        "SearchRegexBox","SearchCaseBox","SearchTargetBox",
                        "SearchExtensionBox","SearchRememberBox","SearchRecentBox",
                        "SearchRunButton","SearchClearButton"):
            self.assertIn('x:Name="'+control+'"',xaml)
        harness=code("tests/winui/test_shell_gui.py")
        self.assertIn("FLY_M19_OWNED_FEATURES",harness)
        test=code("tests/winui/test_m19_winui_features.py")
        self.assertIn("REAL_M19_WINUI_NAMED_WORKSPACE_ISOLATED_CHILD_TWO_PANES_RESTORED",test)
        self.assertIn("REAL_M19_SEARCH_DEFAULT_OPT_OUT_NO_PERSISTENT_HISTORY",test)

    def test_no_unresolved_merge_conflicts_or_other_worktree_access(self):
        for name in ("MainWindow.xaml.h","MainWindow.xaml.cpp","m19_features.cpp"):
            self.assertNotIn("<<<<<<<",code("app/winui/"+name))
        p=subprocess.run(["git","diff","--name-only","--diff-filter=U"],
           cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0)
        self.assertFalse(p.stdout.strip())
if __name__=="__main__":unittest.main()
