"""G01 active-pane status ownership during independent left/right native results."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
NAV = (ROOT / "app/winui/shell_navigation_controller.cpp").read_text(encoding="utf-8")


class G01ActivePaneStatusContract(unittest.TestCase):
    def test_success_for_inactive_right_tab_does_not_mask_left_failure(self):
        result = MAIN.split("void MainWindow::OnNativeResult(", 1)[1].split(
            "void MainWindow::OnNativeChange(", 1)[0]
        branch = result.split("if(completed.active){\n            ClearFileDetails(", 1)[1].split(
            "}else RefreshTabs(completed.side);", 1)[0]
        self.assertIn("hstring activeStatus=StatusText().Text();", branch)
        self.assertIn(
            "if(completed.side==ActiveWindowTab().model.activePane){",
            branch)
        self.assertIn("activeStatus=completed.recovered?", branch)
        self.assertIn("Refresh(activeStatus);", branch)
        self.assertLess(
            branch.index("hstring activeStatus=StatusText().Text();"),
            branch.index("if(completed.side==ActiveWindowTab().model.activePane){"))
        self.assertLess(
            branch.index("if(completed.side==ActiveWindowTab().model.activePane){"),
            branch.index("Refresh(activeStatus);"))
        self.assertNotIn("Refresh(completed.recovered?", branch)

    def test_controller_active_is_tab_specific_not_current_pane(self):
        self.assertIn("completed.active=tab==pane.active;", NAV)
        self.assertIn("for(int side=0;side<2;++side)", NAV)


if __name__ == "__main__":
    unittest.main()
