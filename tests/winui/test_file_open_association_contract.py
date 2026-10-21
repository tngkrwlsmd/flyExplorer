"""EP11 source contracts for safe Windows default-app activation.

This file documents expected behavior only; it does not launch a file,
alter associations, run a GUI, or test the operating system.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "app" / "winui" / "file_open_controller.h"
WINDOW = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"


class DefaultFileAssociationContract(unittest.TestCase):
    def test_missing_and_unavailable_associations_are_distinct(self):
        code = CONTROLLER.read_text(encoding="utf-8-sig")
        for token in (
            "Result { Opened, NoAssociation, AppUnavailable, Failed, TimedOut }",
            "Launcher::QueryFileSupportAsync(file)",
            "Support::AppNotInstalled",
            "Support::NotSupported",
            "Support::AppUnavailable",
            "Result::NoAssociation",
            "Result::AppUnavailable",
            "Launcher::LaunchFileAsync(file)",
        ):
            self.assertIn(token, code)
        self.assertLess(
            code.index("Launcher::QueryFileSupportAsync(file)"),
            code.index("Launcher::LaunchFileAsync(file)"),
        )

    def test_duplicate_and_stale_context_handling_remains_bounded(self):
        code = CONTROLLER.read_text(encoding="utf-8-sig")
        for token in (
            "if(!stale)return Start::Busy;",
            "stale=s->current&&!s->current()",
            "++s->ticket;",
            "s->pending.Cancel()",
            "if(s->pending)s->pending.Cancel()",
            "std::chrono::seconds(15)",
            "s->ticket!=ticket",
            "if(!live(s,ticket))",
            "void prepareForClose() noexcept",
        ):
            self.assertIn(token, code)
        self.assertNotIn("ShellExecute", code)
        self.assertNotIn("std::thread", code)

    def test_only_current_tab_presents_launch_result(self):
        code = WINDOW.read_text(encoding="utf-8-sig")
        launch = code.split("void MainWindow::OpenSelectedFolder(int side)", 1)[1].split(
            "void MainWindow::OnLeftFileDoubleTapped(", 1
        )[0]
        for token in (
            "ui->ActiveWindowTab().model.activePane!=context.side",
            "live.tab==context.tab&&live.route==context.route",
            "live.visibleFolder==context.visibleFolder",
            "result==Result::NoAssociation",
            "result==Result::AppUnavailable",
            "result==Result::TimedOut",
            "Windows에서 연결 프로그램을 선택하세요.",
            "이전 파일 열기 요청을 처리 중입니다.",
        ):
            self.assertIn(token, launch)


if __name__ == "__main__":
    unittest.main()
