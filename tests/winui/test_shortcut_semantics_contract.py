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
        self.assertIn("const bool focused=otherView.Focus(", f6)
        self.assertIn("focused?", f6)
        self.assertIn("포커스를 이동할 수 없습니다.", f6)
        self.assertNotIn("RunTransfer(", f6)

    def test_configurable_ctrl_focus_shortcuts_do_not_mutate_files(self):
        window = compact(WINDOW.read_text(encoding="utf-8"))
        preview = window.split("RootShell().PreviewKeyDown(", 1)[1].split(
            "RefreshWindowTabs();", 1
        )[0]
        for token in (
            "VirtualKey::L", "VirtualKey::E",
            "VirtualKey::F", "VirtualKey::K",
            "VirtualKey::G", "VirtualKey::J",
            "pref.addressShortcut", "pref.searchShortcut",
            "OnAddressDisplayClicked(nullptr,nullptr)",
            "QuickSearchBox()", "SelectAll()", "args.Handled(true)",
        ):
            self.assertIn(token, preview)
        self.assertNotIn("RunTransfer(", preview)
        bindings = (ROOT / "src" / "base" / "ui_preferences.h").read_text(
            encoding="utf-8"
        )
        self.assertIn("validFocusShortcuts(", bindings)
        self.assertIn("kFocusShortcutCount=6", bindings)
        self.assertIn("address!=search", bindings)
        self.assertIn("std::size(choices)==", window)
        self.assertIn("fxfile::uisettings::kFocusShortcutCount", window)
        store = (ROOT / "src" / "base" / "ui_preferences.cpp").read_text(
            encoding="utf-8"
        )
        self.assertIn("address<kFocusShortcutCount", store)
        self.assertIn("search<kFocusShortcutCount", store)
        self.assertIn("addressShortcut=0", bindings)
        self.assertIn("searchShortcut=2", bindings)

    def test_shortcut_editor_supports_save_reset_and_persistence(self):
        ui = (ROOT / "app" / "winui" / "MainWindow.xaml").read_text(
            encoding="utf-8"
        )
        header = (ROOT / "app" / "winui" / "MainWindow.xaml.h").read_text(
            encoding="utf-8"
        )
        window = WINDOW.read_text(encoding="utf-8")
        for token in (
            'x:Name="AddressShortcutBox"', 'x:Name="SearchShortcutBox"',
            'Click="OnApplyShortcuts"', 'Click="OnResetShortcuts"',
        ):
            self.assertIn(token, ui)
        for name in ('AddressShortcutBox', 'SearchShortcutBox'):
            choices = ui.split('x:Name="'+name+'"', 1)[1].split(
                '</ComboBox>', 1
            )[0]
            items = re.findall(r'<ComboBoxItem Content="([^"]+)"/>', choices)
            self.assertEqual(
                ['Ctrl+L', 'Ctrl+E', 'Ctrl+F', 'Ctrl+K', 'Ctrl+G', 'Ctrl+J'],
                items,
            )
        for name in ("OnApplyShortcuts", "OnResetShortcuts"):
            self.assertIn(name, header)
            self.assertIn("void MainWindow::"+name+"(", window)
        self.assertIn("PersistPreferences()", window)

    def test_full_gui_profile_covers_real_shortcut_keyboard(self):
        orchestrator = compact(
            (ROOT / "tools" / "winui" / "run_checks.py").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn('if area == "all":', orchestrator)
        self.assertIn('for focused in ("window-tabs", "shortcuts", "filter-preset"):', orchestrator)
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
