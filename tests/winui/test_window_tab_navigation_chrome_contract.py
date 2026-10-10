"""Completion must update committed history chrome after pending resolves."""

from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[2]

def compact(s):
    return re.sub(r"\s+", " ", s)

class WindowTabChromeContract(unittest.TestCase):
    def test_navigation_chrome_recomputes_from_active_history(self):
        source=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        header=(ROOT/"app/winui/MainWindow.xaml.h").read_text(encoding="utf-8")
        self.assertIn("void UpdateNavigationChrome();",header)
        helper=source.split("void MainWindow::UpdateNavigationChrome()",1)[1].split(
            "void MainWindow::Refresh(",1)[0]
        self.assertIn("pane.pending[pane.active]!=0",helper)
        self.assertIn("nav.canBack()&&!pending",helper)
        self.assertIn("nav.canForward()&&!pending",helper)
        self.assertIn("nav.snapshot().folder.valid()",helper)

    def test_resolved_no_change_and_errors_recompute_chrome(self):
        source=compact((ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8"))
        complete=source.split("void MainWindow::OnNativeResult(",1)[1].split(
            "void MainWindow::OnNativeChange(",1)[0]
        for current,next_kind in (
            ("NoChange","Failed"),
            ("Failed","Rejected"),
            ("Rejected","Extended"),
        ):
            block=complete.split("if(completed.kind==Kind::"+current+")",1)[1].split(
                "if(completed.kind==Kind::"+next_kind+")",1)[0]
            self.assertIn("UpdateNavigationChrome()",block,current)
        refresh=source.split("void MainWindow::Refresh(",1)[1].split(
            "bool MainWindow::OpenFolder(",1)[0]
        self.assertIn("UpdateNavigationChrome()",refresh)

    def test_failed_window_tab_probe_separates_route_and_chrome(self):
        harness=(ROOT/"tests/winui/test_v7_window_tabs_gui.py").read_text(encoding="utf-8")
        for token in ("V7_CLEANUP_ROUTE_NESTED","V7_CLEANUP_BACK_EXISTS",
                      "V7_CLEANUP_BACK_ENABLED","V7_CLEANUP_WINDOW_TABS",
                      "V7_CLEANUP_STATUS_PENDING"):
            self.assertIn(token,harness)

if __name__=="__main__":
    unittest.main()
