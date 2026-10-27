"""G01: queued UI work must not outlive MainWindow shutdown."""
from pathlib import Path
import unittest

MAIN = (Path(__file__).resolve().parents[2] /
        "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")

class G01QueuedMainWindowCloseContract(unittest.TestCase):
    def test_queued_navigation_completion_and_change_check_close(self):
        worker = MAIN.split("void MainWindow::OnNativeResult",1)[0]
        self.assertIn("if(auto ui=weak.get();ui&&!ui->mClosing)\n"
                      "                        ui->OnNativeResult(", worker)
        self.assertIn("if(auto ui=weak.get();ui&&!ui->mClosing)\n"
                      "                        ui->OnNativeChange(", worker)

    def test_direct_navigation_entrypoints_check_closing(self):
        for name in ("OnNativeResult", "OnNativeChange"):
            source = MAIN.split("void MainWindow::"+name,1)[1]
            self.assertIn("if(mClosing)return;", source[:220])

    def test_high_frequency_owned_cursor_timer_cannot_touch_shutdown_xaml(self):
        timer = MAIN.split("timer.Interval(std::chrono::milliseconds(40));",1)[1]
        self.assertIn("if(auto ui=nativeWeak.get();ui&&!ui->mClosing){",
                      timer[:170])
        close = MAIN.split("void MainWindow::PrepareForClose() noexcept",1)[1]
        self.assertLess(close.index("mClosing=true;"),
                        close.index("mDetailColumnHoverTimer.Stop();"))

if __name__=="__main__":
    unittest.main()
