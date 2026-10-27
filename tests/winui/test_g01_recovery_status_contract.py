"""G01: distinguish successful recovery from its transport/timing cause.

This source contract is not WinUI rendering or GUI acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
UI = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
SUP = (ROOT / "src/base/shell_isolated_supervisor.cpp").read_text(encoding="utf-8")


class G01RecoveredStatusContract(unittest.TestCase):
    def test_recovered_label_applies_to_timeout_and_broken_pipe(self):
        retry = SUP.split("void IsolatedShellSupervisor::runLane(", 1)[1]
        self.assertIn("outcome.hr==HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)", retry)
        self.assertIn("if((outcome.timeout||brokenPipe)&&", retry)
        self.assertIn("result.recovered=true;", retry)
        self.assertEqual(retry.count("result.recovered=true;"), 1)
        self.assertIn("constexpr DWORD kMaxAttempts=2;", SUP)

        segment = UI.split("void MainWindow::OnNativeResult(", 1)[1].split(
            "void MainWindow::OnNativeChange(", 1)[0]
        active = segment.split(
            "if(completed.side==ActiveWindowTab().model.activePane){", 1
        )[1].split("Refresh(activeStatus);", 1)[0]
        self.assertIn("activeStatus=completed.recovered?", active)
        self.assertIn('L"일시적인 오류 후 재시도하여 폴더를 불러왔습니다."', active)
        self.assertNotIn('L"응답 지연 후 폴더를 불러왔습니다."', active)
        self.assertIn('L"폴더 변경 알림을 반영했습니다."', active)
        self.assertIn('L"폴더를 불러왔습니다."', active)

    def test_inactive_pane_result_does_not_mask_active_failure(self):
        segment = UI.split("void MainWindow::OnNativeResult(", 1)[1].split(
            "void MainWindow::OnNativeChange(", 1)[0]
        self.assertIn("hstring activeStatus=StatusText().Text();", segment)
        self.assertIn(
            "if(completed.side==ActiveWindowTab().model.activePane){",
            segment
        )
        self.assertLess(
            segment.index("if(completed.side==ActiveWindowTab().model.activePane){"),
            segment.index("Refresh(activeStatus);"),
        )


if __name__ == "__main__":
    unittest.main()
