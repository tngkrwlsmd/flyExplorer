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


class OpenWithFileAssociationContract(unittest.TestCase):
    def test_picker_is_explicit_and_preserves_default_launch(self):
        code=CONTROLLER.read_text(encoding="utf-8-sig")
        for token in ("enum class Mode { Default, ChooseApp };",
                      "Mode mode=Mode::Default", "if(mode==Mode::Default)try {",
                      "Launcher::QueryFileSupportAsync(file)",
                      "Launcher::LaunchFileAsync(file);",
                      "LauncherOptions options;",
                      "options.DisplayApplicationPicker(true);",
                      "Launcher::LaunchFileAsync(file,options);",
                      "std::chrono::seconds(120)"):
            self.assertIn(token,code)
        for forbidden in ("SHOpenWithDialog","ShellExecuteEx",
                          "RegSetValue","OAIF_REGISTER_EXT"):
            self.assertNotIn(forbidden,code)

    def test_single_selected_file_scoped_to_window_tab(self):
        app=(ROOT/"app"/"winui"/"m22_transfers.cpp").read_text(encoding="utf-8-sig")
        method=app.split("void MainWindow::OpenSelectedWith(int side){",1)[1].split(
            "void MainWindow::ShowAppFileContextMenu(",1)[0]
        header=(ROOT/"app"/"winui"/"MainWindow.xaml.h").read_text(encoding="utf-8-sig")
        self.assertIn("void OpenSelectedWith(int side);",header)
        for token in ("ActiveWindowTab().model.activePane!=side",
                      "visible.visibleRoute!=pane.routeIds[pane.active]",
                      "view.SelectedItems().Size()!=1", "selected->isFileSystem()",
                      "selected->isFolder()", "FileOperationContext(side)",
                      "ui->ActiveWindowTab().identity!=context.windowTabIdentity",
                      "live.tab==context.tab&&live.route==context.route",
                      "live.visibleShellFolder==context.visibleShellFolder",
                      "Open::Mode::ChooseApp", "result==Result::TimedOut"):
            self.assertIn(token,method)
        menu=app.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        self.assertIn('make(L"연결 프로그램으로 열기"',menu)
        self.assertIn("localSelection&&count==1&&!isFolder",menu)
        self.assertIn("ui.OpenSelectedWith(side)",menu)
        self.assertIn("auto expected=std::make_shared<const std::vector<std::uint64_t>>",menu)


if __name__ == "__main__":
    unittest.main()
