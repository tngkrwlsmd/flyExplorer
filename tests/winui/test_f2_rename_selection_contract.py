"""Source-level contract for F2 rename selection without changing filesystem operations."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"


class RenameSelectionContract(unittest.TestCase):
    def test_file_stem_is_selected_without_last_extension(self):
        body = (APP / "FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        for token in (
            "BeginNameEdit(int action,hstring const& initial,bool isFolder)",
            "name.find_last_of(L'.')",
            "(action==1||action==2)&&!isFolder",
            "dot>0&&dot+1<name.size()",
            "box.Select(0,static_cast<int>(dot))",
            "else box.SelectAll()",
        ):
            self.assertIn(token, body)

    def test_folder_type_comes_from_indexed_item_not_filename_guess(self):
        commands = (APP / "m21_commands.cpp").read_text(encoding="utf-8-sig")
        header = (APP / "FileToolbar.xaml.h").read_text(encoding="utf-8-sig")
        self.assertIn("renameFolder=indexed->isFolder();", commands)
        self.assertIn("hstring(initial),renameFolder", commands)
        self.assertIn("hstring const& initial,bool isFolder", header)
        self.assertNotIn("std::filesystem::path(initial).extension()", commands)

    def test_rename_and_create_operations_unchanged(self):
        bar = (APP / "FileToolbar.xaml.cpp").read_text(encoding="utf-8-sig")
        self.assertIn("pendingNameAction_=action", bar)
        self.assertIn("box.Focus(FocusState::Programmatic)", bar)
        self.assertIn("void FileToolbar::EndNameEdit()", bar)
        self.assertIn("pendingNameAction_==0?9:pendingNameAction_==1?10:", bar)
        self.assertIn("pendingNameAction_==2?16:-1", bar)


if __name__ == "__main__":
    unittest.main()
