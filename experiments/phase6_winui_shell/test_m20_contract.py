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
  ui=source("experiments/phase6_winui_shell/MainWindow.xaml.h")
  self.assertIn("fxfile::explorerui::Model mModel",ui)
  self.assertNotIn("struct PaneState",ui)
 def test_all_real_tab_and_pane_commands_dispatch_through_native_model(self):
  cpp=source("experiments/phase6_winui_shell/MainWindow.xaml.cpp")
  for v in ("Command::AddTab","Command::CloseTab","Command::ToggleSplit",
            "Command::ActivatePane","Command::SelectTab"):
   self.assertIn(v,cpp)
  self.assertNotIn("mPanes",cpp)
  self.assertNotIn("mNextRoute",cpp)
 def test_request_and_event_matching_keep_stale_helpers_out_of_ui(self):
  ui=source("experiments/phase6_winui_shell/MainWindow.xaml.cpp")
  self.assertIn("mModel.markPending(side,pane.active,id,true)",ui)
  self.assertIn("mModel.completeRequest(side,i,result.route",ui)
  lib=source("src/base/explorer_ui_state.cpp")
  self.assertIn("pane.routeIds[tab]!=route",lib)
  self.assertIn("pane.pending[tab]!=request",lib)
  self.assertIn("nextRoute_++",lib)
 def test_workspace_reset_uses_native_model_and_still_owns_workers(self):
  src=source("experiments/phase6_winui_shell/m19_features.cpp")
  self.assertIn("mModel.reset(doc.split,counts,selected)",src)
  self.assertIn("mSupervisor->forget(route)",src)
  self.assertIn("mModel.markPending(side,next.first,id,false)",src)
 def test_winui_full_frame_has_light_dark_system_and_this_pc(self):
  xaml=source("experiments/phase6_winui_shell/MainWindow.xaml")
  header_path=ROOT/"experiments/phase6_winui_shell/ShellHeader.xaml"
  sidebar_path=ROOT/"experiments/phase6_winui_shell/NavigationSidebar.xaml"
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
  code=source("experiments/phase6_winui_shell/m20_shell.cpp")
  for x in ("RequestedTheme(chosen","OpenFolder(L\"shell:MyComputerFolder\")",
            "ElementTheme::Default","ElementTheme::Light",
            "ElementTheme::Dark"):
   self.assertIn(x,code)
 def test_actual_project_links_both_native_and_winui_shell(self):
  xml=source("experiments/phase6_winui_shell/FlyExplorerWinUIShell.project-template.xml")
  for x in ("explorer_ui_state.cpp","m20_shell.cpp","m19_features.cpp",
            "shell_isolated_supervisor.cpp","directory_watcher.cpp"):
   self.assertIn(x,xml)
 def test_owned_real_gui_harness_reaches_actual_theme_pixels(self):
  harness=source("experiments/phase6_winui_shell/test_shell_gui.py")
  test=source("experiments/phase6_winui_shell/test_m20_shell_gui.py")
  self.assertIn("FLY_M20_OWNED_SHELL",harness)
  for x in ("ImageGrab.grab","테마: 다크","테마: 라이트",
            "테마: 시스템","REAL_M20_SHARED_NATIVE_COMMANDS"):
   self.assertIn(x,test)
if __name__=="__main__":unittest.main()
