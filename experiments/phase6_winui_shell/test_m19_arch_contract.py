"""M1.9 source and integration contracts; real native/UI fixtures run separately."""
from pathlib import Path
import subprocess,unittest
R=Path(__file__).resolve().parents[2]
UI=R/"experiments/phase6_winui_shell"
NATIVE=R/"src/fxfile"
def text(p):return p.read_text(encoding="utf-8-sig")
class M19IntegrationContracts(unittest.TestCase):
 def test_imported_main_workspace_and_recent_search_still_native(self):
  m=text(NATIVE/"main_frame.cpp")
  s=text(NATIVE/"search_dlg.cpp")
  modern=text(NATIVE/"gui/ModernUI.cpp")
  self.assertIn("workspace_session.h",m)
  self.assertIn("void MainFrame::OnSaveWorkspace",m)
  self.assertIn("void MainFrame::OnOpenWorkspace",m)
  self.assertIn("IDC_SEARCH_REMEMBER",s)
  self.assertIn("RecentLocations",s)
  self.assertIn("Dark",modern)
  self.assertTrue((NATIVE/"workspace_session.h").is_file())
  self.assertFalse((NATIVE/"gui/DarkScrollbarLayer.cpp").exists())

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
  for q in ("kMaxWalk=2500","kMaxDepth=5","kMaxResults=100",
            "kRecentMax=8","FindFirstFileExW",
            "FILE_ATTRIBUTE_REPARSE_POINT","LOCALAPPDATA",
            "flyExplorer.WinUI3Preview","MOVEFILE_WRITE_THROUGH"):
   self.assertIn(q,p)
  self.assertNotIn('L"APPDATA"',p)
  self.assertNotIn("ShellExecuteW",p)
  self.assertIn("SearchRememberBox().IsChecked().GetBoolean()",f)
  self.assertIn("if(remember){",f)
  self.assertIn("std::thread([weak,dispatch,cancel,ticket",f)
  self.assertIn("readRecentScopes(*items)",f)
  self.assertIn("mRecentEdited",f)

 def test_ui_restores_selected_and_inactive_tabs_in_separate_process(self):
  f=text(UI/"m19_features.cpp")
  core=text(UI/"MainWindow.xaml.cpp")
  xaml=text(UI/"MainWindow.xaml")
  for q in ("InitializeM19","ApplyWorkspace","QueueNextWorkspaceTab",
            "mSupervisor->forget(route)","std::thread(",
            "--m19-workspace","GetModuleFileNameW",
            "CreateProcessW","mRestoreQueue[side].emplace_back",
            "saveWorkspaceNew","loadWorkspace"):
   self.assertIn(q,f)
  self.assertIn("QueueNextWorkspaceTab(side)",core)
  self.assertIn("if(mSearchCancel)mSearchCancel->store(true)",core)
  for id in ("WorkspacePanelButton","WorkspaceFileBox",
             "SaveWorkspaceButton","OpenWorkspaceButton",
             "SearchScopeBox","SearchRememberBox","SearchRecentBox",
             "RecentCountText","SearchMatches","SearchClearButton"):
   self.assertIn('x:Name="'+id+'"',xaml)
  self.assertIn('Visibility="Collapsed"',xaml)

 def test_private_supervised_shell_protected_on_current_winui_template(self):
  project=text(UI/"FlyExplorerWinUIShell.project-template.xml")
  native=text(R/"src/base/shell_isolated_supervisor.cpp")
  for unit in ("m19_workspace.cpp","m19_search.cpp","m19_features.cpp",
               "shell_isolated_supervisor.cpp",
               "directory_watcher.cpp","shell_namespace_watcher.cpp"):
   self.assertIn(unit,project)
  self.assertNotIn("shell_async_worker.cpp",project)
  for needle in ("kDeadlineMs=4500","JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
                 "TerminateJobObject(lane->activeJob"):
   self.assertIn(needle,native)

 def test_main_import_is_actual_merge_or_pending_exact_merge(self):
  root=str(R)
  def git(*a):
   p=subprocess.run(["git",*a],cwd=root,capture_output=True,text=True,
      encoding="utf-8",errors="replace")
   return p.returncode,p.stdout.strip()
  # M1.9 imported EXACT main 3a4d27c. Subsequent main cbffb48
  # changed only documentation, so the product source ancestry is intact
  # even though a docs-only tip is not our M1.9 merge parent.
  original_main="3a4d27ce9de3a8b92f23c0b406fe8da195e82ec5"
  rc,head=git("rev-parse","HEAD")
  self.assertEqual(rc,0)
  code,_=git("merge-base","--is-ancestor",original_main,head)
  self.assertEqual(code,0)
  code,main=git("rev-parse","main")
  self.assertEqual(code,0)
  self.assertIn(main,(
      original_main,"cbffb487635a94e625070d5bee9d5e6680006f12"))
  code,files=git("diff","--name-only",original_main+".."+main)
  self.assertEqual(code,0)
  self.assertTrue(all(f=="AGENTS.md" or f.startswith("docs/") or
             f==".agent-policy/PROJECT.md" for f in files.splitlines()),files)

if __name__=="__main__":unittest.main()
