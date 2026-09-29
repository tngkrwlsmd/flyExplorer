"""Static guardrails for the independent WinUI 3 full-shell migration."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parent
def text(name):
 return (ROOT/name).read_text(encoding="utf-8-sig")

class MigrationContracts(unittest.TestCase):
 def test_true_winui_control_tree_and_pane_state(self):
  xaml=text("MainWindow.xaml")
  header=text("MainWindow.xaml.h")
  impl=text("MainWindow.xaml.cpp")
  self.assertEqual(xaml.count("<TabView "),2)
  self.assertEqual(xaml.count("<ListView "),2)
  self.assertIn("SecondaryColumn",xaml)
  self.assertIn("ThemeResource ApplicationPageBackgroundThemeBrush",xaml)
  for n in ("AddressBox","LeftTabs","RightTabs","LeftFiles","RightFiles",
            "NewTabButton","CloseTabButton","SplitButton"):
   self.assertIn('x:Name="'+n+'"',xaml)
  self.assertIn("std::array<PaneState, 2>",header)
  self.assertIn("pane.tabs.emplace_back();",impl)
  self.assertIn("OpenSelectedFolder(int side)",impl)
  self.assertIn("if (mPopulatingTabs",impl)

 def test_separate_from_mfc_and_link_existing_native_file_core(self):
  project=text("FlyExplorerWinUIShell.project-template.xml")
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
  self.assertIn("Windows Shell namespace preview",xaml)
  self.assertIn("file mutations disabled",impl)
  self.assertNotIn("std::filesystem::directory_iterator",impl)
  self.assertIn("QueuePidl(side,fxfile::shellnav::Location(entries[index].id)",impl)
  self.assertNotIn("SHFileOperation(",impl)
  self.assertNotIn("DeleteFile(",impl)
  self.assertNotIn("MoveFile(",impl)
  self.assertIn("Deliberately independent WinUI 3 executable",build)
  self.assertIn("project-template.xml",build)
  self.assertIn("Configuration",text("FlyExplorerWinUIShell.project-template.xml"))

 def test_shared_native_enum_and_legacy_call_site(self):
  root=ROOT.parents[1]
  legacy=(root/"src/base/shell_enumerator_win.cpp").read_text(encoding="utf-8-sig")
  low=(root/"src/base/shell_enum_bridge.cpp").read_text(encoding="utf-8-sig")
  core=(root/"src/base/shell_navigation_core.cpp").read_text(encoding="utf-8-sig")
  product=(root/"src/fxfile/fxfile.gyp").read_text(encoding="utf-8-sig")
  project=text("FlyExplorerWinUIShell.project-template.xml")
  testgyp=(root/"src/fxfile-tests/fxfile-tests.gyp").read_text(encoding="utf-8-sig")
  self.assertIn("shellnav::openEnumeration",legacy)
  self.assertEqual(low.count("folder->EnumObjects("),1)
  self.assertIn("openEnumeration(parent.p,nullptr,flags,&iterator.p)",core)
  self.assertIn("shell_enum_bridge.cpp",product)
  self.assertNotIn("shell_navigation_core.cpp",product)
  self.assertIn("shell_enum_bridge.cpp",project)
  self.assertIn("shell_navigation_core.cpp",project)
  self.assertIn("shell_navigation_core.cpp",testgyp)
  self.assertIn("shell_enum_bridge.cpp",testgyp)
  for token in ("afxwin.h","ListCtrlEx","m_hWnd","CWnd","CDialog"):
   self.assertNotIn(token,low+core)

 def test_async_sta_shared_directory_change_contract(self):
  root=ROOT.parents[1]
  project=text("FlyExplorerWinUIShell.project-template.xml")
  winui=text("MainWindow.xaml.cpp")
  mainhdr=text("MainWindow.xaml.h")
  worker=(root/"src/base/shell_async_worker.cpp").read_text(encoding="utf-8")
  bridge=(root/"src/base/directory_change_bridge.cpp").read_text(encoding="utf-8")
  legacy=(root/"src/fxfile/file_change_watcher.cpp").read_text(encoding="utf-8-sig")
  native=(root/"src/fxfile-tests/functional_tests.cpp").read_text(encoding="utf-8-sig")
  self.assertNotIn("shell_async_worker.cpp",project)
  self.assertIn("shell_isolated_supervisor.cpp",project)
  self.assertIn("directory_watcher.cpp",project)
  self.assertIn("directory_change_bridge.cpp",project)
  self.assertIn("directorychange::open",legacy)
  self.assertIn("directorychange::rearm",legacy)
  self.assertIn("FindFirstChangeNotificationW",bridge)
  self.assertIn("FindFirstChangeNotificationA",bridge)
  self.assertIn("COINIT_APARTMENTTHREADED",worker)
  self.assertIn("MsgWaitForMultipleObjectsEx",worker)
  self.assertIn("std::thread([st]{run(st);}).detach()",worker)
  self.assertIn("dispatch.TryEnqueue",winui)
  self.assertIn("mSupervisor->submit",winui)
  self.assertIn("mWatcher->watch",winui)
  self.assertNotIn("mWorker->submit",winui)
  self.assertIn("weak.get()",winui)
  self.assertIn("std::unique_ptr<fxfile::shellnav::IsolatedShellSupervisor>",mainhdr)
  self.assertIn("std::unique_ptr<fxfile::directorychange::DirectoryWatcher>",mainhdr)
  self.assertIn("testAsyncShellWorkerAndChangeBridge",native)
  self.assertNotIn("std::filesystem::directory_iterator",winui)
  self.assertNotIn("CWnd",worker+bridge)
  self.assertNotIn("ListCtrlEx",worker+bridge)

if __name__=="__main__":unittest.main()
