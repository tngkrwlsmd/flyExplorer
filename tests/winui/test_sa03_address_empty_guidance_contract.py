"""SA03: non-focusable empty address hint without changing the cached suggestions."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
XAML = (ROOT / "app/winui/MainWindow.xaml").read_text(encoding="utf-8-sig")
SOURCE = (ROOT / "app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8-sig")


class SA03AddressEmptyGuidanceContract(unittest.TestCase):
    def test_empty_hint_is_not_a_candidate_button_and_is_accessible(self):
        root = ET.fromstring(XAML)
        name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
        panel = next(el for el in root.iter() if el.get(name) == "AddressSuggestionPanel")
        rows = next(el for el in panel.iter() if el.get(name) == "AddressSuggestionRows")
        hint = next(el for el in panel.iter() if el.get(name) == "AddressSuggestionEmptyText")
        self.assertTrue(rows.tag.endswith("}StackPanel"))
        self.assertTrue(hint.tag.endswith("}TextBlock"))
        self.assertNotIn(hint, list(rows))
        self.assertEqual(hint.get("Visibility"), "Collapsed")
        self.assertEqual(hint.get("TextWrapping"), "Wrap")
        self.assertEqual(hint.get("IsHitTestVisible"), "False")
        self.assertTrue(hint.get("AutomationProperties.Name"))
        self.assertIn("Enter", hint.get("Text"))
        self.assertIn("이동을 시도", hint.get("Text"))
        self.assertEqual(panel.get("Visibility"), "Collapsed")

    def test_empty_candidate_branch_keeps_editor_and_panel_visible(self):
        update = SOURCE.split("void MainWindow::UpdateAddressSuggestions()", 1)[1].split(
            "void MainWindow::OnAddressTextChanged(", 1)[0]
        self.assertIn("rows.Children().Clear();", update)
        self.assertIn("if(prefix.size()<3||prefix.size()>1024)", update)
        self.assertIn("std::vector<std::wstring> choices;", update)
        self.assertIn("AddressSuggestionEmptyText().Visibility(", update)
        self.assertIn("choices.empty()?Visibility::Visible:Visibility::Collapsed", update)
        self.assertIn("panel.Visibility(Visibility::Visible);", update)
        self.assertNotIn("if(choices.empty()){panel.Visibility(Visibility::Collapsed);return;}", update)
        # The hint is a presentational alternative, never another candidate.
        self.assertIn("button.Click({this,&MainWindow::OnAddressSuggestionClicked});", update)
        self.assertIn("rows.Children().Append(button);", update)

    def test_keyboard_enter_and_candidate_focus_stay_scoped(self):
        handler = SOURCE.split("void MainWindow::OnAddressKeyDown(", 1)[1].split(
            "void MainWindow::OnAddressGotFocus(", 1)[0]
        self.assertIn("AddressSuggestionRows().Children().Size()>0", handler)
        self.assertIn("first.Focus(FocusState::Keyboard)", handler)
        self.assertIn("ResolveFriendlyAddress(", handler)
        self.assertIn("OpenFolder(requested);", handler)
        self.assertIn("HideAddressSuggestions();", handler)
        self.assertIn("Current().snapshot().parsingName", handler)
        self.assertIn("args.Key()==Windows::System::VirtualKey::Escape", handler)

    def test_no_new_io_or_history_access_while_typing(self):
        update = SOURCE.split("void MainWindow::UpdateAddressSuggestions()", 1)[1].split(
            "void MainWindow::OnAddressTextChanged(", 1)[0]
        for forbidden in ("FindFirstFile", "GetFileAttributes", "SHParseDisplayName",
                          "QueuePath(", "QueuePidl(", "OpenFolder(", "std::filesystem::exists(",
                          "GetFileSystemEntries", "std::thread", "DirectoryWatcher"):
            self.assertNotIn(forbidden, update)
        self.assertIn("choices.size()<8&&inspected<2048", update)
        self.assertIn("pane.pending[tab]", update)


if __name__ == "__main__":
    unittest.main()
