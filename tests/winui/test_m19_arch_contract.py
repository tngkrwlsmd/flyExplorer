"""M1.9 source and integration contracts; real native/UI fixtures run separately."""
from pathlib import Path
import subprocess,unittest
from historical_mfc import text as historical_text, exists as historical_exists
R=Path(__file__).resolve().parents[2]
UI=R/"app/winui"
def text(p):return p.read_text(encoding="utf-8-sig")
class M19IntegrationContracts(unittest.TestCase):
 def test_imported_main_workspace_and_recent_search_still_native(self):
  m=historical_text("src/fxfile/main_frame.cpp")
  s=historical_text("src/fxfile/search_dlg.cpp")
  modern=historical_text("src/fxfile/gui/ModernUI.cpp")
  self.assertIn("workspace_session.h",m)
  self.assertIn("void MainFrame::OnSaveWorkspace",m)
  self.assertIn("void MainFrame::OnOpenWorkspace",m)
  self.assertIn("IDC_SEARCH_REMEMBER",s)
  self.assertIn("RecentLocations",s)
  self.assertIn("Dark",modern)
  self.assertTrue(historical_exists("src/fxfile/workspace_session.h"))
  self.assertFalse(historical_exists("src/fxfile/gui/DarkScrollbarLayer.cpp"))

 def test_bounded_subset_of_mfc_workspace_utf16_safety(self):
  p=text(UI/"m19_workspace.cpp")
  h=text(UI/"m19_workspace.h")
  for q in ("kMaxBytes=1048576","kMaxTabs=32",
            "FILE_FLAG_OPEN_REPARSE_POINT","FILE_ATTRIBUTE_REPARSE_POINT",
            "readExact","validUtf16","Duplicate or empty workspace key",
            "main/main.view.row_count","main/main.view.column_count",
            "main/main.view1","CREATE_NEW","FlushFileBuffers",
            "L\"[main]","L\"\\r\\n[workspace]"):
   if q=="main/main.view1":
    self.assertIn("main/main.view",p)
   else:self.assertIn(q,p)
  self.assertIn("std::array<std::vector<std::wstring>,2>",h)
  self.assertNotIn("APPDATA",p)
  self.assertNotIn("fxfile-main.conf",p)

 def test_strict_opt_in_recent_locations_and_bounded_native_search(self):
  p=text(UI/"m19_search.cpp")
  f=text(UI/"m19_features.cpp")
  controller=text(UI/"search_controller.cpp")
  for q in ("kMaxWalk=2500","kMaxDepth=5","kMaxResults=100",
            "kRecentMax=8","FindFirstFileExW",
            "FILE_ATTRIBUTE_REPARSE_POINT","LOCALAPPDATA",
            "flyExplorer","MOVEFILE_WRITE_THROUGH"):
   self.assertIn(q,p)
  self.assertNotIn('L"APPDATA"',p)
  self.assertNotIn("ShellExecuteW",p)
  self.assertIn("SearchRememberBox().IsChecked().GetBoolean()",f)
  self.assertIn("completion.request.remember",f)
  self.assertIn("scanFiles(",controller)
  self.assertIn("readRecentScopes(loaded)",controller)
  self.assertIn("recentRevision",controller)

 def test_ui_restores_selected_and_inactive_tabs_in_separate_process(self):
  f=text(UI/"m19_features.cpp")
  core=text(UI/"MainWindow.xaml.cpp")
  xaml=text(UI/"MainWindow.xaml")
  for q in ("InitializeM19","ApplyWorkspace","QueueNextWorkspaceTab",
            "mShellNavigation->release(ActiveWindowTab().model)","std::thread(",
            "--m19-workspace","GetModuleFileNameW",
            "CreateProcessW","mRestoreQueue[side].emplace_back",
            "saveWorkspaceNew","loadWorkspace"):
   self.assertIn(q,f)
  self.assertIn("QueueNextWorkspaceTab(completed.side)",core)
  self.assertIn("mSearchController.prepareForClose()",core)
  for id in ("WorkspacePanelButton","WorkspaceFileBox",
             "SaveWorkspaceButton","OpenWorkspaceButton",
             "SearchScopeBox","SearchRememberBox","SearchRecentBox",
             "RecentCountText","SearchMatches","SearchClearButton"):
   self.assertIn('x:Name="'+id+'"',xaml)
  self.assertIn('Visibility="Collapsed"',xaml)

 def test_private_supervised_shell_protected_on_current_winui_template(self):
  project=text(UI/"flyExplorer.project-template.xml")
  native=text(R/"src/base/shell_isolated_supervisor.cpp")
  for unit in ("m19_workspace.cpp","m19_search.cpp","m19_features.cpp",
               "search_controller.cpp","shell_isolated_supervisor.cpp",
               "directory_watcher.cpp","shell_namespace_watcher.cpp"):
   self.assertIn(unit,project)
  self.assertNotIn("shell_async_worker.cpp",project)
  for needle in ("kDeadlineMs=4500","JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                 "TerminateJobObject(lane->activeJob"):
   self.assertIn(needle,native)

 def test_main_import_and_winui_cutover_lineage_are_preserved(self):
  root=str(R)
  def git(*a):
   p=subprocess.run(["git",*a],cwd=root,capture_output=True,text=True,
      encoding="utf-8",errors="replace")
   return p.returncode,p.stdout.strip()
  # M1.9 imported native main 3a4d27c. The owner later promoted the
  # accepted WinUI tree to canonical main, while retaining the last
  # native-default cbffb48 as an explicit merge parent for rollback/history.
  original_main="3a4d27ce9de3a8b92f23c0b406fe8da195e82ec5"
  old_default="cbffb487635a94e625070d5bee9d5e6680006f12"
  accepted_winui="3476ecd863b289244a06159fa59d719e9a48d49a"
  rc,head=git("rev-parse","HEAD")
  self.assertEqual(rc,0)
  code,main=git("rev-parse","main")
  self.assertEqual(code,0)
  for required in (original_main,old_default,accepted_winui):
   code,_=git("merge-base","--is-ancestor",required,main)
   self.assertEqual(code,0,required)
   code,_=git("merge-base","--is-ancestor",required,head)
   self.assertEqual(code,0,required)
  # The canonical main must no longer be the old native-default tip.
  self.assertNotEqual(main,old_default)
  self.assertNotEqual(main,original_main)

if __name__=="__main__":unittest.main()
