"""Model-level streaming contracts for large Shell folders."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class LargeFolderStreamingContracts(unittest.TestCase):
    def test_supervisor_returns_one_page_not_aggregated_snapshot(self):
        h=read("src/base/shell_isolated_supervisor.h")
        cpp=read("src/base/shell_isolated_supervisor.cpp")
        self.assertIn("submitPage(",h)
        self.assertIn("std::uint32_t pageOffset=0",h)
        self.assertIn("item.pageOffset,item.pageLimit",cpp)
        self.assertNotIn("Snapshot aggregate",cpp)
        self.assertNotIn("aggregate.children",cpp)

    def test_session_append_is_same_folder_and_expected_offset_only(self):
        h=read("src/base/shell_navigation_core.h")
        cpp=read("src/base/shell_navigation_core.cpp")
        self.assertIn("appendPage(Snapshot&& page,std::size_t expectedOffset)",h)
        self.assertIn("current_.nextOffset!=expectedOffset",cpp)
        self.assertIn("page.baseOffset!=expectedOffset",cpp)
        self.assertIn("page.nextOffset!=expectedOffset+page.children.size()",cpp)
        self.assertIn("::ILIsEqual(current_.folder.get(),page.folder.get())",cpp)
        self.assertIn("current_.nextOffset=page.nextOffset",cpp)
        self.assertIn("current_.truncated=page.truncated",cpp)

    def test_controller_continuation_reuses_pending_identity(self):
        h=read("app/winui/shell_navigation_controller.h")
        cpp=read("app/winui/shell_navigation_controller.cpp")
        self.assertIn("Extended",h)
        self.assertIn("submitContinuation(",h+cpp)
        self.assertIn("supervisor_->submitPage(",cpp)
        self.assertIn("const auto offset=snapshot.nextOffset",cpp)
        self.assertIn("model.markPending(side,pane.active,id,true)",cpp)
        self.assertIn("NavigationAction::Continue",cpp)
        self.assertIn("appendPage(",cpp)

    def test_ui_starts_with_truncated_page_and_loads_on_demand(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        state=read("app/winui/file_list_state.h")
        transfers=read("app/winui/m22_transfers.cpp")
        self.assertIn("bool streamToComplete=false",state)
        self.assertIn("QueueNextFolderPage(",main)
        self.assertIn("snapshot.truncated?L\"+\"",main)
        self.assertIn("snapshot.truncated||items.size()>1200",main)
        self.assertIn("state.visibleCount+=160",main)
        self.assertIn("QueueNextFolderPage(side,true)",transfers)
        self.assertIn("!state.filenameFilter.empty()&&snapshot.truncated",main)

    def test_real_owned_gui_proves_initial_1024_then_global_8000(self):
        gui=read("tests/winui/test_large_owned_folder_gui.py")
        for marker in (
            "160/1024+",
            "OWNED_LARGE_MODEL_STREAMING_INITIAL_1024",
            "OWNED_LARGE_MODEL_STREAMING_SORT_COMPLETES_8000",
            "bench-{args.items-1:04d}.txt",
        ):
            self.assertIn(marker,gui)

if __name__=="__main__":
    unittest.main()
