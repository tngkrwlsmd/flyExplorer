"""F5/F6 shortcut semantics must be non-mutating and Explorer-aligned."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
WINDOW = ROOT / "app" / "winui" / "MainWindow.xaml.cpp"
TRANSFERS = ROOT / "app" / "winui" / "m22_transfers.cpp"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class ShortcutSemanticsContract(unittest.TestCase):
    def test_f5_is_window_preview_refresh_not_file_transfer(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "RefreshWindowTabs();", 1
        )[0]
        self.assertIn(
            "key==Windows::System::VirtualKey::F5", preview
        )
        f5 = preview.split(
            "key==Windows::System::VirtualKey::F5", 1
        )[1].split(
            "key==Windows::System::VirtualKey::F6", 1
        )[0]
        self.assertIn("NavigationAction::Refresh", f5)
        self.assertIn("QueuePidl(side", f5)
        self.assertNotIn("RunTransfer(", f5)

    def test_f6_is_window_preview_split_pane_focus(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "RefreshWindowTabs();", 1
        )[0]
        f6 = preview.split(
            "key==Windows::System::VirtualKey::F6", 1
        )[1].split(
            "const bool createFolderShortcut", 1
        )[0]
        self.assertIn("model.split", f6)
        self.assertIn("const int other=1-model.activePane", f6)
        self.assertIn("ActivatePane(other)", f6)
        self.assertIn("Focus( Microsoft::UI::Xaml::FocusState::Keyboard)", f6)
        self.assertNotIn("RunTransfer(", f6)

    def test_ctrl_l_and_ctrl_f_focus_existing_fields_without_mutation(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "RefreshWindowTabs();", 1
        )[0]
        address = preview.split(
            "key==Windows::System::VirtualKey::L", 1
        )[1].split("key==Windows::System::VirtualKey::F", 1)[0]
        search = preview.split(
            "key==Windows::System::VirtualKey::F", 1
        )[1].split("key==Windows::System::VirtualKey::F5", 1)[0]
        self.assertIn("control&&!shift&&!alt", preview)
        self.assertIn("OnAddressDisplayClicked(nullptr,nullptr)", address)
        self.assertIn("QuickSearchBox()", search)
        self.assertIn("Focus(", search)
        self.assertIn("SelectAll()", search)
        for branch in (address, search):
            self.assertIn("args.Handled(true)", branch)
            self.assertNotIn("RunTransfer(", branch)
            self.assertNotIn("OpenFolder(", branch)

    def test_full_gui_profile_covers_real_shortcut_keyboard(self):
        orchestrator = compact(
            (ROOT / "tools" / "winui" / "run_checks.py").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn('if area == "all":', orchestrator)
        self.assertIn('for focused in ("window-tabs", "shortcuts"):', orchestrator)
        self.assertIn('gui_command( focused, configuration, env )', orchestrator)
        self.assertIn('"test_shortcut_gui.py"', orchestrator)

    def test_file_operation_shortcuts_do_not_own_f5_or_f6(self):
        transfers = compact(TRANSFERS.read_text(encoding="utf-8"))
        handler = transfers[
            transfers.index("void MainWindow::HandleFileShortcut"):
        ]
        self.assertNotIn("VirtualKey::F5", handler)
        self.assertNotIn("VirtualKey::F6", handler)
        self.assertNotIn(
            "RunTransfer(fxfile::shelltransfer::Kind::Copy);args.Handled(true);return;",
            handler,
        )
        self.assertNotIn(
            "RunTransfer(fxfile::shelltransfer::Kind::Move);args.Handled(true);return;",
            handler,
        )


if __name__ == "__main__":
    unittest.main()
