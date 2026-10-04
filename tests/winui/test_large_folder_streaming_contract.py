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

    def test_session_supports_bounded_bidirectional_resident_window(self):
        h=read("src/base/shell_navigation_core.h")
        cpp=read("src/base/shell_navigation_core.cpp")
        self.assertIn("kResidentWindowEntries=2048",h)
        self.assertIn("residentEndOffset() const noexcept",h)
        self.assertIn("prependPage(Snapshot&& page,std::size_t expectedEnd)",h)
        self.assertIn("trimResidentFront(std::size_t maximum)",h)
        self.assertIn("trimResidentBack(std::size_t maximum)",h)
        self.assertIn("current_.residentEndOffset()!=expectedOffset",cpp)
        self.assertIn("expectedOffset>current_.nextOffset",cpp)
        self.assertIn("const bool advancesFrontier=expectedOffset==current_.nextOffset",cpp)
        self.assertIn("page.nextOffset!=expectedEnd",cpp)
        self.assertIn("current_.baseOffset=page.baseOffset",cpp)

    def test_controller_pages_forward_rehydrates_and_pages_backward(self):
        h=read("app/winui/shell_navigation_controller.h")
        cpp=read("app/winui/shell_navigation_controller.cpp")
        self.assertIn("PageDirection",h)
        self.assertIn("submitNextPage(",h+cpp)
        self.assertIn("submitPreviousPage(",h+cpp)
        self.assertIn("snapshot.residentEndOffset()",cpp)
        self.assertIn("snapshot.nextOffset-residentEnd",cpp)
        self.assertIn("snapshot.baseOffset-offset",cpp)
        self.assertIn("supervisor_->submitPage(",cpp)
        self.assertIn("result.pageLimit",cpp)
        self.assertIn("session.prependPage(",cpp)
        self.assertIn("PageDirection::Backward",cpp)
        self.assertIn("model.markPending(side,pane.active,id,true)",cpp)
        self.assertIn("kMaxBrowseEntries",cpp)
        self.assertIn("ceiling-residentEnd",cpp)

    def test_ui_row_identity_is_logical_not_resident_vector_index(self):
        core=read("src/base/shell_navigation_core.h")
        state=read("app/winui/file_list_state.h")
        main=read("app/winui/MainWindow.xaml.cpp")
        consumers=[
            main,
            read("app/winui/m21_commands.cpp"),
            read("app/winui/m22_transfers.cpp"),
            read("app/winui/m23_drag.cpp"),
        ]
        self.assertIn("logicalIndex(std::size_t resident)",core)
        self.assertIn("residentIndex(std::uint64_t logical",core)
        self.assertIn("std::size_t renderedBaseOffset=0",state)
        self.assertIn("std::vector<std::uint64_t> renderedLogical",state)
        self.assertIn("snapshot.logicalIndex(index)",main)
        self.assertIn("renderedState.renderedLogical",main)
        for source in consumers:
            self.assertNotIn("unbox_value<uint32_t>(row.Tag())",source)
            self.assertNotIn("unbox_value<uint32_t>(entry.Tag())",source)
        self.assertGreaterEqual(
            sum("indexedItem(" in source for source in consumers),
            4,
        )

    def test_session_retains_lightweight_name_index_beyond_resident_window(self):
        core=read("src/base/shell_navigation_core.h")
        cpp=read("src/base/shell_navigation_core.cpp")
        main=read("app/winui/MainWindow.xaml.cpp")
        state=read("app/winui/file_list_state.h")
        self.assertIn("struct IndexedItem final",core)
        self.assertIn("std::vector<IndexedItem> nameIndex_",core)
        self.assertIn("indexedFrontier() const noexcept",core)
        self.assertIn("mergeIndexPage(Snapshot const& page)",core+cpp)
        self.assertIn("page.baseOffset>nameIndex_.size()",cpp)
        self.assertIn("state.indexedNameProjection",main)
        self.assertIn("state.indexToComplete",main)
        self.assertIn("session.nameIndex()",main)
        self.assertIn("state.indexedNameProjection&&!state.indexToComplete&&mode<=1",main)
        self.assertIn("session.indexedFrontier()==snapshot.nextOffset",main)
        self.assertIn("state.indexedNameSort=state.sortMode<=1",main)
        self.assertIn("const bool indexedComplete=",main)
        self.assertIn("if(indexedComplete)incomplete=false",main)
        self.assertIn("bool indexedNameSort=false",state)

    def test_ui_browses_window_and_rebuilds_complete_model_for_sort_filter(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        ui=read("app/winui/MainWindow.xaml")
        state=read("app/winui/file_list_state.h")
        transfers=read("app/winui/m22_transfers.cpp")
        self.assertIn("bool streamToComplete=false",state)
        self.assertIn("LeftLoadPreviousButton",ui)
        self.assertIn("RightLoadPreviousButton",ui)
        self.assertIn("OnLoadPreviousFiles",ui+main)
        self.assertIn("trimResidentFront(",main)
        self.assertIn("trimResidentBack(",main)
        self.assertIn("submitPreviousPage(",main)
        self.assertIn("snapshot.residentEndOffset()<snapshot.nextOffset",main)
        self.assertIn("snapshot.baseOffset",transfers)
        self.assertIn("QueueNextFolderPage(side,true)",transfers)
        self.assertIn("state.filenameFilter.empty()&&mode==0",main)
        self.assertIn("snapshot.baseOffset+(std::min)(order.size(),state.visibleCount)",main)
        self.assertIn("kMaxCompleteModelEntries",main)
        self.assertIn("kMaxBrowseEntries",main)
        self.assertIn("fullModelLimitReached",main)

    def test_owned_gui_covers_browse_over_complete_model_ceiling(self):
        gui=read("tests/winui/test_large_owned_folder_gui.py")
        for marker in (
            "20500",
            "--browse-over-complete-model",
            "OWNED_LARGE_BROWSE_OVER_20000",
            "OWNED_LARGE_OVER_20K_NAME_SORT_INDEXED",
            "OWNED_LARGE_OVER_20K_NAME_FILTER_INDEXED",
            "OWNED_LARGE_OVER_20K_SIZE_SORT_REFUSED",
            "large-name-index-over-20k-after.png",
        ):
            self.assertIn(marker,gui)

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
