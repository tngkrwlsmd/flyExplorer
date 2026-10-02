"""Static guardrails for the independent WinUI 3 full-shell migration."""
from pathlib import Path
from historical_mfc import text as historical_text
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]/"app"/"winui"
def text(name):
 return (ROOT/name).read_text(encoding="utf-8-sig")

class MigrationContracts(unittest.TestCase):
 def test_true_winui_control_tree_and_pane_state(self):
  xaml=text("MainWindow.xaml")
  header=text("MainWindow.xaml.h")
  impl=text("MainWindow.xaml.cpp")
  self.assertEqual(xaml.count("<TabView "),2)
  # M1.9 adds a separate collapsible read-only search result ListView;
  # preserve exactly two actual navigation panes.
  self.assertEqual(xaml.count("<ListView "),3)
  shell=(Path(__file__).resolve().parents[2]/"app/winui/ShellHeader.xaml").read_text(encoding="utf-8")
  self.assertIn('x:Name="WindowTabStrip"',shell)
  for actual_pane in ('LeftFiles','RightFiles'):
   self.assertEqual(xaml.count('x:Name="'+actual_pane+'"'),1)
  self.assertEqual(xaml.count('x:Name="SearchMatches"'),1)
  self.assertIn("SecondaryColumn",xaml)
  self.assertIn('Background="Transparent"',xaml)
  self.assertIn("SystemBackdrop(Microsoft::UI::Xaml::Media::MicaBackdrop{}",impl)
  for n in ("AddressBox","LeftTabs","RightTabs","LeftFiles","RightFiles",
            "NewTabButton","CloseTabButton","SplitButton"):
   self.assertIn('x:Name="'+n+'"',xaml)
  self.assertIn("WindowWorkspaceController mWorkspace",header)
  self.assertNotIn("mWindowTabs",header)
  self.assertIn("pane.tabs.emplace_back();",
     (ROOT.parents[1]/"src/base/explorer_ui_state.cpp").read_text(encoding="utf-8-sig"))
  self.assertIn("OpenSelectedFolder(int side)",impl)
  self.assertIn("if (mPopulatingTabs",impl)

 def test_separate_from_mfc_and_link_existing_native_file_core(self):
  project=text("flyExplorer.project-template.xml")
  impl=text("MainWindow.xaml.cpp")
  self.assertIn("file_operation_core.cpp",project)
  self.assertIn("shell_navigation_core.cpp",project)
  self.assertIn("shell_navigation_core.h",impl if "shell_navigation_core.h" in impl else text("MainWindow.xaml.h"))
  self.assertIn("PrecompiledHeader>NotUsing",project)
  self.assertIn("file_operation_core.h",impl)
  self.assertIn("fxfile::fileop::execute(nullptr)==ERROR_INVALID_PARAMETER",impl)
  self.assertNotIn("ExplorerCtrl",impl)
  self.assertNotIn("ListCtrlEx",impl)
  self.assertNotIn("ProductCommandBridge",project)
  self.assertNotIn("phase5_island_bridge",project)

 def test_first_slice_is_read_only_and_explicitly_unshipped(self):
  xaml=text("MainWindow.xaml")
  impl=text("MainWindow.xaml.cpp")
  build=text("build.cmd")
  nav=ET.parse(ROOT/"NavigationSidebar.xaml").getroot()
  navtext=" ".join(e.get("Text","") for e in nav.iter())
  self.assertIn("\ud0d0\uc0c9",navtext)
  self.assertNotIn("Shell",navtext)
  self.assertNotIn("\ub3c5\ub9bd \ud504\ub85c\uc138\uc2a4",navtext)
  self.assertTrue((ROOT.parents[1]/"src/base/file_command_core.cpp").is_file())
  self.assertNotIn("std::filesystem::directory_iterator",impl)
  self.assertIn("QueuePidl(side,fxfile::shellnav::Location(entries[index].id)",impl)
  self.assertNotIn("SHFileOperation(",impl)
  self.assertNotIn("DeleteFile(",impl)
  self.assertNotIn("MoveFile(",impl)
  self.assertIn("Canonical flyExplorer WinUI 3 product build",build)
  self.assertIn("project-template.xml",build)
  self.assertIn("Configuration",text("flyExplorer.project-template.xml"))

 def test_shell_navigation_controller_owns_async_lifecycle(self):
  project=text("flyExplorer.project-template.xml")
  header=text("MainWindow.xaml.h")
  impl=text("MainWindow.xaml.cpp")+text("m19_features.cpp")
  controller=text("shell_navigation_controller.cpp")
  controllerhdr=text("shell_navigation_controller.h")
  self.assertIn("shell_navigation_controller.cpp",project)
  self.assertIn("shell_navigation_controller.h",project)
  self.assertIn("ShellNavigationController> mShellNavigation",header)
  for token in ("mSupervisor","mWatcher","mShellWatcher",
                "mWatchedRoutes","mWatchTokens","mWatchedPaths"):
   self.assertNotIn(token,header)
  for token in ("supervisor_->submit","watcher_->watch",
                "shellWatcher_->watch","completeRequest(",
                "pane.tabs[tab].accept","handleChange(",
                "void ShellNavigationController::suspend",
                "void ShellNavigationController::release"):
   self.assertIn(token,controller)
  self.assertIn("watchedRoutes_",controllerhdr)
  self.assertIn("watchTokens_",controllerhdr)
  self.assertIn("mShellNavigation->release",impl)
  self.assertIn("mShellNavigation->suspend",impl)
  self.assertNotIn("mSupervisor->",impl)
  self.assertNotIn("mWatcher->",impl)
  self.assertNotIn("mShellWatcher->",impl)

 def test_file_operation_controller_owns_async_lifecycle(self):
  project=text("flyExplorer.project-template.xml")
  header=text("MainWindow.xaml.h")
  transfer=text("m22_transfers.cpp")
  commands=text("m21_commands.cpp")
  controller=text("file_operation_controller.cpp")
  controllerhdr=text("file_operation_controller.h")
  self.assertIn("file_operation_controller.cpp",project)
  self.assertIn("file_operation_controller.h",project)
  self.assertIn("FileOperationController mFileOperations",header)
  for token in ("mFileOperationPending","mFileOperationEpoch",
                "mTransferProgress","mTransferEpoch"):
   self.assertNotIn(token,header)
  for token in ("shelltransfer::execute","filecommand::execute",
                "state_->busy","state_->epoch","state_->progress",
                "acceptTransfer(","acceptFileCommand(","prepareForClose"):
   self.assertIn(token,controller+controllerhdr)
  self.assertNotIn("shelltransfer::execute",transfer)
  self.assertNotIn("filecommand::execute",commands)
  self.assertIn("mFileOperations.requestTransfer",transfer)
  self.assertIn("mFileOperations.startFileCommand",commands)

 def test_shared_native_enum_and_legacy_call_site(self):
  root=ROOT.parents[1]
  legacy=(root/"src/base/shell_enumerator_win.cpp").read_text(encoding="utf-8-sig")
  low=(root/"src/base/shell_enum_bridge.cpp").read_text(encoding="utf-8-sig")
  core=(root/"src/base/shell_navigation_core.cpp").read_text(encoding="utf-8-sig")
  product=historical_text("src/fxfile/fxfile.gyp")
  project=text("flyExplorer.project-template.xml")
  self.assertIn("shellnav::openEnumeration",legacy)
  self.assertEqual(low.count("folder->EnumObjects("),1)
  self.assertIn("openEnumeration(parent.p,nullptr,flags,&iterator.p)",core)
  # cbffb48 is now history-only and predates the WinUI shared-bridge wiring.
  self.assertNotIn("shell_enum_bridge.cpp",product)
  self.assertNotIn("shell_navigation_core.cpp",product)
  self.assertIn("shell_enum_bridge.cpp",project)
  self.assertIn("shell_navigation_core.cpp",project)
  for token in ("afxwin.h","ListCtrlEx","m_hWnd","CWnd","CDialog"):
   self.assertNotIn(token,low+core)

 def test_async_sta_shared_directory_change_contract(self):
  root=ROOT.parents[1]
  project=text("flyExplorer.project-template.xml")
  winui=text("MainWindow.xaml.cpp")
  mainhdr=text("MainWindow.xaml.h")
  worker=(root/"src/base/shell_async_worker.cpp").read_text(encoding="utf-8")
  bridge=(root/"src/base/directory_change_bridge.cpp").read_text(encoding="utf-8")
  historical_watcher=historical_text("src/fxfile/file_change_watcher.cpp")
  self.assertNotIn("shell_async_worker.cpp",project)
  self.assertIn("shell_isolated_supervisor.cpp",project)
  self.assertIn("directory_watcher.cpp",project)
  self.assertIn("directory_change_bridge.cpp",project)
  self.assertIn("FindFirstChangeNotification(",historical_watcher)
  self.assertIn("FindFirstChangeNotificationW",bridge)
  self.assertIn("FindFirstChangeNotificationA",bridge)
  self.assertIn("COINIT_APARTMENTTHREADED",worker)
  self.assertIn("MsgWaitForMultipleObjectsEx",worker)
  self.assertIn("std::thread([st]{run(st);}).detach()",worker)
  controller=text("shell_navigation_controller.cpp")
  controllerhdr=text("shell_navigation_controller.h")
  self.assertIn("dispatch.TryEnqueue",winui)
  self.assertIn("mShellNavigation->submit",winui)
  self.assertIn("supervisor_->submit",controller)
  self.assertIn("watcher_->watch",controller)
  self.assertNotIn("mWorker->submit",winui)
  self.assertIn("weak.get()",winui)
  self.assertIn("ShellNavigationController> mShellNavigation",mainhdr)
  self.assertNotIn("IsolatedShellSupervisor> mSupervisor",mainhdr)
  self.assertNotIn("DirectoryWatcher> mWatcher",mainhdr)
  self.assertIn("IsolatedShellSupervisor> supervisor_",controllerhdr)
  self.assertIn("DirectoryWatcher> watcher_",controllerhdr)
  self.assertNotIn("std::filesystem::directory_iterator",winui)
  self.assertNotIn("CWnd",worker+bridge)
  self.assertNotIn("ListCtrlEx",worker+bridge)

if __name__=="__main__":unittest.main()
