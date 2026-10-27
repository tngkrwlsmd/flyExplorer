"""G01 owned window-tab callbacks must not invoke MainWindow after close."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
CPP=(ROOT/"app/winui/ShellHeader.xaml.cpp").read_text(encoding="utf-8")
HEADER=(ROOT/"app/winui/ShellHeader.xaml.h").read_text(encoding="utf-8")
MAIN=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")

class G01ShellHeaderCloseContract(unittest.TestCase):
    def test_disconnect_window_tab_delegates_before_xaml_timer_disposal(self):
        self.assertIn("void PrepareForClose() noexcept;",HEADER)
        self.assertIn("bool mClosing=false",HEADER)
        close=MAIN.split("void MainWindow::PrepareForClose() noexcept",1)[1].split(
            "MainWindow::~MainWindow()",1)[0]
        self.assertLess(close.index("mClosing=true;"),close.index("->PrepareForClose();"))
        self.assertLess(close.index("winrt::FlyExplorer::implementation::ShellHeader"),
                        close.index("mDetailColumnDragTimer.Stop();"))
        impl=CPP.split("void ShellHeader::PrepareForClose() noexcept",1)[1].split(
            "void ShellHeader::SetThemeCallback",1)[0]
        for literal in ("mClosing=true;","mHandler={};","mAddWindowTab={};",
                        "mActivateWindowTab={};","mCloseWindowTab={};"):
            self.assertIn(literal,impl)
        self.assertNotIn("WindowTabStrip()",impl)

    def test_queued_tab_add_close_check_close_at_dispatch_time(self):
        self.assertEqual(CPP.count("if(auto self=weak.get();self&&!self->mClosing)"),2)
        for callback in ("mAddWindowTab", "mCloseWindowTab"):
            self.assertIn("if(self->"+callback+")",CPP)
        self.assertIn("if(mClosing||mRestoringTabs)return",CPP)
        self.assertIn("if(mClosing||mRestoring)return;",CPP)
        self.assertIn("if(mClosing)return;\n mRestoringTabs=true;",CPP)
        self.assertIn("if(mClosing)return;\n mAddWindowTab=",CPP)

    def test_close_does_not_invoke_window_tab_callbacks(self):
        impl=CPP.split("void ShellHeader::PrepareForClose() noexcept",1)[1].split(
            "void ShellHeader::SetThemeCallback",1)[0]
        for forbidden in ("mActivateWindowTab(", "mCloseWindowTab(",
                          "mAddWindowTab(", "WindowTabStrip()"):
            self.assertNotIn(forbidden,impl)

if __name__=="__main__":
    unittest.main()
