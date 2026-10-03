"""M2.0 focused source/architecture contracts. Real GUI is separate."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
def source(rel):return (ROOT/rel).read_text(encoding="utf-8-sig")
class ModelAndFullShell(unittest.TestCase):
 def test_native_model_no_mfc_winrt_or_profile_access(self):
  code=source("src/base/explorer_ui_state.cpp")+source(
       "src/base/explorer_ui_state.h")
  for token in ("std::array<Pane,2>","enum class Command","Model::dispatch",
                "Model::reset","Model::markPending","Model::completeRequest"):
   self.assertIn(token,code)
  for forbidden in ("CWnd","MainWindow","Xaml","Microsoft::UI",
                    "APPDATA","RegSetValue","CoCreateInstance"):
   self.assertNotIn(forbidden,code)
 def test_shared_model_owns_real_tab_shell_sessions_routes_and_pending(self):
  h=source("src/base/explorer_ui_state.h")
  for v in ("std::vector<shellnav::Session>","routeIds,pending",
            "filesystemPaths","nextRoute_=1"):
   self.assertIn(v,h)
  ui=source("app/winui/MainWindow.xaml.h")
  controller=source("app/winui/window_workspace_controller.h")
  self.assertIn("WindowWorkspaceController mWorkspace",ui)
  self.assertNotIn("mWindowTabs",ui)
  self.assertNotIn("mNextWindowTabIdentity",ui)
  self.assertIn("std::vector<WindowTabState> states_",controller)
  self.assertIn("std::uint64_t nextIdentity_=1",controller)
  self.assertNotIn("struct PaneState",ui)
 def test_all_real_tab_and_pane_commands_dispatch_through_native_model(self):
  cpp=source("app/winui/MainWindow.xaml.cpp")
  controller=source("app/winui/window_workspace_controller.cpp")
  for v in ("Command::AddTab","Command::CloseTab","Command::ToggleSplit",
            "Command::ActivatePane","Command::SelectTab"):
   self.assertIn(v,cpp)
  self.assertGreaterEqual(cpp.count("mWorkspace.dispatch("),5)
  self.assertIn("active().model.dispatch(command,side,tab)",controller)
  self.assertNotIn("mPanes",cpp)
  self.assertNotIn("mNextRoute",cpp)
 def test_request_and_event_matching_keep_stale_helpers_out_of_ui(self):
  nav=source("app/winui/shell_navigation_controller.cpp")
  self.assertIn("model.markPending(side,pane.active,id,true)",nav)
  self.assertIn("model.completeRequest(",nav)
  self.assertIn("pane.pending[tab]!=result.request",nav)
  lib=source("src/base/explorer_ui_state.cpp")
  self.assertIn("pane.routeIds[tab]!=route",lib)
  self.assertIn("pane.pending[tab]!=request",lib)
  self.assertIn("nextRoute_++",lib)
 def test_workspace_reset_uses_native_model_and_still_owns_workers(self):
  src=source("app/winui/m19_features.cpp")
  nav=source("app/winui/shell_navigation_controller.cpp")
  self.assertIn("mWorkspace.resetActive(doc.split,counts,selected)",src)
  self.assertIn("mShellNavigation->release(ActiveWindowTab().model)",src)
  self.assertIn("ActiveWindowTab().model,side,next->tab,next->path,false",src)
  self.assertIn("mWorkspaceRestore.track(side,id)",src)
  self.assertIn("model.markPending(side,tab,id,supersedeOthers)",nav)
 def test_winui_full_frame_has_light_dark_system_and_this_pc(self):
  xaml=source("app/winui/MainWindow.xaml")
  header_path=ROOT/"app/winui/ShellHeader.xaml"
  sidebar_path=ROOT/"app/winui/NavigationSidebar.xaml"
  for x in ('x:Name="RootShell"','x:Name="HeaderView"',
            'x:Name="SidebarView"'):
   self.assertIn(x,xaml)
  ns="{http://schemas.microsoft.com/winfx/2006/xaml}Name"
  header=ET.parse(header_path).getroot()
  names={e.get(ns) for e in header.iter() if e.get(ns)}
  for x in ("ShellHeading","ThemePicker","ThemeStateText"):
   self.assertIn(x,names)
  labels={e.get("Content") for e in header.iter() if e.get("Content")}
  for x in ("\uc2dc\uc2a4\ud15c","\ub77c\uc774\ud2b8","\ub2e4\ud06c"):
   self.assertIn(x,labels)
  sidebar=ET.parse(sidebar_path).getroot()
  side_names={e.get(ns) for e in sidebar.iter() if e.get(ns)}
  self.assertIn("ThisPCButton",side_names)
  code=source("app/winui/m20_shell.cpp")
  for x in ("RequestedTheme(chosen","OpenFolder(L\"shell:MyComputerFolder\")",
            "ElementTheme::Default","ElementTheme::Light",
            "ElementTheme::Dark"):
   self.assertIn(x,code)
 def test_actual_project_links_both_native_and_winui_shell(self):
  xml=source("app/winui/flyExplorer.project-template.xml")
  for x in ("explorer_ui_state.cpp","window_workspace_controller.cpp","m20_shell.cpp","m19_features.cpp",
            "shell_isolated_supervisor.cpp","directory_watcher.cpp"):
   self.assertIn(x,xml)
 def test_owned_real_gui_harness_reaches_actual_theme_pixels(self):
  harness=source("tests/winui/test_shell_gui.py")
  test=source("tests/winui/test_m20_shell_gui.py")
  self.assertIn("FLY_M20_OWNED_SHELL",harness)
  for x in ("ImageGrab.grab","테마: 다크","테마: 라이트",
            "테마: 시스템","REAL_M20_SHARED_NATIVE_COMMANDS"):
   self.assertIn(x,test)
if __name__=="__main__":unittest.main()

class V7WindowTabEngineContract(unittest.TestCase):
 def test_v7_window_tab_route_namespace_and_engine(self):
  root=Path(__file__).resolve().parents[2]
  state=(root/"app/winui/window_tab_state.h").read_text(encoding="utf-8")
  header=(root/"app/winui/MainWindow.xaml.h").read_text(encoding="utf-8")
  impl=(root/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
  core=(root/"src/base/explorer_ui_state.cpp").read_text(encoding="utf-8")
  for token in ("kRouteStride","model(id*kRouteStride)"):
   self.assertIn(token,state)
  self.assertIn("Model::Model(std::uint64_t routeBase)",core)
  controller=(root/"app/winui/window_workspace_controller.cpp").read_text(encoding="utf-8")
  for token in ("CreateWindowTab","ActivateWindowTab","CloseWindowTab",
                "SuspendActiveWindowTab","ReleaseWindowTabRoutes"):
   self.assertIn(token,header);self.assertIn("MainWindow::"+token,impl)
  for token in ("WindowWorkspaceController::create","WindowWorkspaceController::activate",
                "WindowWorkspaceController::close","WindowWorkspaceController::replace"):
   self.assertIn(token,controller)
  self.assertNotIn("mWindowTabs",header)
  self.assertIn("mWorkspace.create()",impl)
  self.assertIn("mShellNavigation->suspend(state.model)",impl)
  self.assertIn("mShellNavigation->release(state.model)",impl)
