"""Workspace restore sequencing ownership and stale-completion contracts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def src(rel):
    return (ROOT/rel).read_text(encoding="utf-8-sig")

class WorkspaceRestoreCoordinatorContracts(unittest.TestCase):
    def test_coordinator_owns_queue_and_request_lifecycle_without_winui(self):
        header=src("app/winui/workspace_restore_coordinator.h")
        impl=src("app/winui/workspace_restore_coordinator.cpp")
        main=src("app/winui/MainWindow.xaml.h")
        for token in (
            "class WorkspaceRestoreCoordinator final",
            "std::deque<Task> tasks",
            "std::uint64_t awaitedRequest",
            "void begin(",
            "bool settle(",
            "std::optional<Task> takeNext(",
            "bool track(",
            "void reset() noexcept"):
            self.assertIn(token,header)
        self.assertIn("WorkspaceRestoreCoordinator mWorkspaceRestore",main)
        self.assertNotIn("mRestoreQueue",main)
        for forbidden in ("Microsoft::UI::Xaml","DispatcherQueue","winrt::"):
            self.assertNotIn(forbidden,header+impl)

    def test_main_correlates_restore_progress_with_accepted_request_id(self):
        core=src("app/winui/MainWindow.xaml.cpp")
        navh=src("app/winui/shell_navigation_controller.h")
        nav=src("app/winui/shell_navigation_controller.cpp")
        features=src("app/winui/m19_features.cpp")
        self.assertIn("std::uint64_t request=0",navh)
        self.assertIn("completed.request=result.request",nav)
        self.assertIn("mWorkspaceRestore.settle(",core)
        self.assertIn("completed.request",core)
        self.assertIn("mWorkspaceRestore.track(side,id)",features)
        self.assertIn("mWorkspaceRestore.begin(",features)

    def test_failed_rejected_and_nochange_restore_requests_can_advance(self):
        core=src("app/winui/MainWindow.xaml.cpp")
        for kind in ("Kind::Failed","Kind::Rejected","Kind::NoChange"):
            self.assertIn(kind,core)
        self.assertIn("continueRestore()",core)
        self.assertIn("QueueNextWorkspaceTab(completed.side)",core)

    def test_user_context_changes_cancel_restore_lane(self):
        core=src("app/winui/MainWindow.xaml.cpp")
        self.assertIn("mWorkspaceRestore.reset();",core)
        self.assertGreaterEqual(core.count("mWorkspaceRestore.reset("),4)
        self.assertIn("mWorkspaceRestore.reset(ActiveWindowTab().model.activePane)",core)
        self.assertIn("mWorkspaceRestore.reset(side)",core)

    def test_project_and_native_fixture_link_coordinator(self):
        project=src("app/winui/flyExplorer.project-template.xml")
        native=src("tests/winui/m20/FlyM20StateContracts.project-template.xml")
        fixture=src("tests/winui/m20/m20_native_fixture.cpp")
        for token in ("workspace_restore_coordinator.h",
                      "workspace_restore_coordinator.cpp"):
            self.assertIn(token,project)
            self.assertIn(token,native)
        for token in ("restore_wrong_request_does_not_advance",
                      "restore_failure_settle_allows_next",
                      "restore_reset_rejects_stale_completion",
                      "restore_two_lanes_are_independent"):
            self.assertIn(token,fixture)

    def test_workspace_file_format_is_bounded_utf16_and_never_writes_legacy_profile(self):
        body=src("app/winui/m19_workspace.cpp")
        header=src("app/winui/m19_workspace.h")
        for token in ("kMaxBytes=1048576","kMaxTabs=32",
                      "FILE_FLAG_OPEN_REPARSE_POINT","FILE_ATTRIBUTE_REPARSE_POINT",
                      "readExact","validUtf16","Duplicate or empty workspace key",
                      "CREATE_NEW","FlushFileBuffers"):
            self.assertIn(token,body)
        self.assertIn("std::array<std::vector<std::wstring>,2>",header)
        self.assertNotIn("APPDATA",body)
        self.assertNotIn("fxfile-main.conf",body)

    def test_workspace_ui_routes_restore_through_coordinator(self):
        xaml=src("app/winui/MainWindow.xaml")
        features=src("app/winui/m19_features.cpp")
        for control in ("WorkspacePanelButton","WorkspaceFileBox",
                        "SaveWorkspaceButton","OpenWorkspaceButton"):
            self.assertIn('x:Name="'+control+'"',xaml)
        for token in ("mWorkspaceRestore.begin(","mWorkspaceRestore.track(side,id)",
                      "QueueNextWorkspaceTab"):
            self.assertIn(token,features)

if __name__=="__main__":
    unittest.main()
