"""PX10 exact workspace/pane/PanTab ownership of Details resize drags.

Source-only, deliberately does not claim native build or pointer GUI acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2] / "app" / "winui"


def read(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")


class DetailColumnDragOwnershipContracts(unittest.TestCase):
    def test_press_records_originating_window_and_folder_tab(self):
        source = read("MainWindow.xaml.cpp")
        header = read("MainWindow.xaml.h")
        press = source.split(
            "void MainWindow::OnDetailColumnResizePointerPressed(", 1
        )[1].split("void MainWindow::ApplyDetailColumnPointerPosition()", 1)[0]
        self.assertIn("std::uint64_t mDetailColumnPointerWindowIdentity=0;", header)
        self.assertIn("std::size_t mDetailColumnPointerPaneTab=0;", header)
        self.assertIn(
            "mDetailColumnPointerWindowIdentity=ActiveWindowTab().identity;", press
        )
        self.assertIn(
            "mDetailColumnPointerPaneTab=\n"
            "            ActiveWindowTab().model.panes[side].active;", press
        )
        self.assertLess(
            press.index("mDetailColumnPointerWindowIdentity="),
            press.index("mDetailColumnPointerDrag=true;"),
        )
        # The established 16ms timer and explicit release-tail flush remain.
        self.assertIn("std::chrono::milliseconds(16)", press)
        self.assertIn("ui->ApplyDetailColumnPointerPosition();", press)

    def test_invalid_context_is_canceled_before_any_width_mutation(self):
        source = read("MainWindow.xaml.cpp")
        body = source.split(
            "void MainWindow::ApplyDetailColumnPointerPosition()", 1
        )[1].split("void MainWindow::OnDetailColumnResizePointerMoved(", 1)[0]
        for predicate in (
            "if(mClosing||",
            "mDetailColumnPointerSide<0||mDetailColumnPointerSide>1",
            "mDetailColumnPointerColumn<0||mDetailColumnPointerColumn>2",
            "ActiveWindowTab().identity!=mDetailColumnPointerWindowIdentity",
            "ActiveWindowTab().model.activePane!=mDetailColumnPointerSide",
            "ActiveWindowTab().model.panes[mDetailColumnPointerSide].active!=",
            "mDetailColumnPointerPaneTab",
        ):
            self.assertIn(predicate, body)
        for canceled in (
            "mDetailColumnPointerDrag=false;",
            "mDetailColumnPointerSide=-1;",
            "mDetailColumnPointerColumn=-1;",
            "mDetailColumnDragTimer.Stop();",
        ):
            self.assertIn(canceled, body)
        self.assertLess(body.index("mDetailColumnPointerPaneTab){"),
                        body.index("POINT next{};"))
        self.assertLess(body.index("POINT next{};"),
                        body.index("auto& state=ActiveWindowTab().fileLists["))
        for prior_limit in (
            "state.nameColumnWidth+delta,120.0,360.0",
            "state.typeColumnWidth+delta,96.0,320.0",
            "state.sizeColumnWidth+delta,64.0,180.0",
        ):
            self.assertIn(prior_limit, body)

    def test_no_session_or_file_operations_are_involved(self):
        header = read("MainWindow.xaml.h")
        model = read("window_tab_state.h")
        self.assertIn("std::array<fxfile::previewlist::PaneState,2> fileLists", model)
        self.assertNotIn("std::vector<int> mDetailColumnPointer", header)
        self.assertIn("void OnDetailColumnResizePointerReleased(", header)


if __name__ == "__main__":
    unittest.main()
