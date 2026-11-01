"""V8-B session ownership and lifecycle contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"app"/"winui"

def read(path):
    return path.read_text(encoding="utf-8-sig")

class SessionCoordinatorContract(unittest.TestCase):
    def test_main_window_no_longer_owns_session_generation_state(self):
        header=read(APP/"MainWindow.xaml.h")
        self.assertIn("SessionCoordinator mSessionCoordinator",header)
        for token in ("mSessionEpoch","mSessionRevision","mSessionMutation"):
            self.assertNotIn(token,header)

    def test_coordinator_owns_native_lifecycle_and_no_xaml_surface(self):
        header=read(APP/"session_coordinator.h")
        impl=read(APP/"session_coordinator.cpp")
        self.assertIn("class SessionCoordinator final",header)
        self.assertIn("struct SharedState",header)
        for token in ("std::atomic_uint64_t epoch","std::atomic_uint64_t revision",
                      "std::mutex mutation","prepareForClose()",
                      "SessionCoordinator::save","SessionCoordinator::load",
                      "SessionCoordinator::clear"):
            self.assertIn(token,header+"\n"+impl)
        for forbidden in ("Microsoft::UI::Xaml","DispatcherQueue","TabView",
                          "SplitView","MainWindow"):
            self.assertNotIn(forbidden,header)
            self.assertNotIn(forbidden,impl)

    def test_main_window_routes_session_transitions_through_coordinator(self):
        surface=read(APP/"m23_session.cpp")
        for token in ("mSessionCoordinator.capture(","mSessionCoordinator.save(",
                      "mSessionCoordinator.load(","mSessionCoordinator.clear(",
                      "mSessionCoordinator.applyRestore("):
            self.assertIn(token,surface)
        close=read(APP/"MainWindow.xaml.cpp")
        self.assertIn("mSessionCoordinator.prepareForClose();",close)

    def test_workspace_and_schema_owners_remain_separate(self):
        workspace=read(APP/"window_workspace_controller.h")
        coordinator=read(APP/"session_coordinator.h")
        session_h=read(ROOT/"src"/"base"/"ui_session.h")
        session_cpp=read(ROOT/"src"/"base"/"ui_session.cpp")
        self.assertIn("std::vector<WindowTabState> states_",workspace)
        self.assertNotIn("std::vector<WindowTabState> states_",coordinator)
        self.assertIn("std::vector<WindowTab> windowTabs",session_h)
        self.assertIn("if(version==1)return decodeV1",session_cpp)
        self.assertIn("if(version==2)return decodeV2",session_cpp)
        self.assertIn("if(version==3)return decodeV3",session_cpp)
        self.assertIn("if(version==4)return decodeV4",session_cpp)
        for path in (ROOT/"src"/"base").glob("ui_session.*"):
            body=read(path)
            self.assertNotIn("Microsoft::UI::Xaml",body)
            self.assertNotIn("DispatcherQueue",body)

    def test_project_compiles_coordinator_as_app_component(self):
        project=read(APP/"flyExplorer.project-template.xml")
        self.assertIn('<ClInclude Include="session_coordinator.h" />',project)
        self.assertIn('<ClCompile Include="session_coordinator.cpp">',project)

    def test_private_session_format_is_versioned_bounded_and_reparse_safe(self):
        body=read(ROOT/"src"/"base"/"ui_session.cpp")
        for token in ("'F','X','S','E','S','S','2','3'",
                      "FILE_ATTRIBUTE_REPARSE_POINT","DRIVE_FIXED",
                      "MaxSize=524288","MaxWindowTabs=10","MaxPaneTabs=8",
                      "MaxHistory=16","checksum(bytes,bytes.size()-4)",
                      "MOVEFILE_REPLACE_EXISTING",
                      "if(version==1)return decodeV1",
                      "if(version==2)return decodeV2",
                      "if(version==3)return decodeV3",
                      "if(version==4)return decodeV4"):
            self.assertIn(token,body)
        self.assertIn("winui-session-v1.bin",body)
        self.assertIn("MOVEFILE_WRITE_THROUGH",body)
        self.assertNotIn("fxfile\\\\conf",body)

    def test_session_controls_and_owned_gui_remain_opt_in_and_profile_isolated(self):
        xaml=read(APP/"MainWindow.xaml")
        gui=read(ROOT/"tests"/"winui"/"test_m23_gui.py")
        for control in ("SaveSessionButton","RestoreSessionButton","ClearSessionButton"):
            self.assertIn(control,xaml)
        for forbidden in ("shellclipboard::write(","OpenClipboard(","recycleConfirmed=true"):
            self.assertNotIn(forbidden,gui)

    def test_restore_rejects_invalid_pane_model_before_committing_workspace(self):
        workspace=read(APP/"window_workspace_controller.cpp")
        native=read(ROOT/"src"/"base"/"explorer_ui_state.cpp")
        coordinator=read(APP/"session_coordinator.cpp")
        replace=workspace.split("bool WindowWorkspaceController::replace(",1)[1]
        self.assertIn("!states[i].model.invariant()",replace)
        self.assertLess(replace.index("!states[i].model.invariant()"),
                        replace.index("states_=std::move(states);"))
        self.assertIn("shape(panes[0])&&shape(panes[1])",native)
        self.assertIn("p.routeIds.size()==count",native)
        self.assertIn("p.pending.size()==count",native)
        self.assertIn("p.filesystemPaths.size()==count",native)
        self.assertIn("return workspace.replace(",coordinator)

    def test_native_restore_fixture_covers_rejection_and_valid_unsplit(self):
        fixture=read(ROOT/"tests"/"winui"/"native_workspace_replace_invariant.cpp")
        self.assertIn('#include "../../app/winui/window_workspace_controller.h"',fixture)
        self.assertIn("assert(controller.replace(std::move(valid),1));",fixture)
        self.assertEqual(fixture.count("rejectedWithoutMutation(std::move(bad));"),5)
        for invalid in ("routeIds.clear();","pending.clear();",
                        "filesystemPaths.clear();",
                        "active=bad[0].model.panes[0].tabs.size();",
                        "bad[0].model.activePane=1;"):
            self.assertIn(invalid,fixture)
        for stable in ("assert(controller.count()==oldCount);",
                       "assert(controller.activeIndex()==oldActive);",
                       "assert(controller.active().identity==oldIdentity);"):
            self.assertIn(stable,fixture)
        self.assertIn("assert(controller.replace(std::move(unsplit),0));",fixture)
        self.assertNotIn("ShellExecute",fixture)
        self.assertNotIn("CreateFile",fixture)

if __name__=="__main__":
    unittest.main()
