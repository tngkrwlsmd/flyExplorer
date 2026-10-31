"""R11 visible file-context shortcut hints; no additional key handlers."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class R11ShortcutHints(unittest.TestCase):
    def test_only_selected_context_displays_real_keyboard_shortcuts(self):
        src=(ROOT/"app/winui/m22_transfers.cpp").read_text(encoding="utf-8-sig")
        selected=src.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        self.assertIn("item.KeyboardAcceleratorTextOverride(shortcutHint)",selected)
        self.assertIn("wchar_t const* shortcutHint=nullptr",selected)
        expected={
            "잘라내기":("Ctrl+X","CopySelectedToWindowsClipboard(side,true)"),
            "복사":("Ctrl+C","CopySelectedToWindowsClipboard(side,false)"),
            "경로 복사":("Ctrl+Shift+C","CopySelectedToWindowsClipboard(side,false,true)"),
            "이름 바꾸기":("F2","Kind::RenameSelected"),
            "삭제":("Delete","Kind::Recycle"),
        }
        for label,(hint,action) in expected.items():
            with self.subTest(label=label):
                start=selected.index('menu.Items().Append(make(L"'+label+'"')
                after=selected.find(' menu.Items().Append(',start+1)
                item=selected[start:] if after<0 else selected[start:after]
                self.assertIn('L"'+hint+'"',item)
                self.assertIn(action,item)
        self.assertNotIn("KeyboardAccelerators().Append",selected)
        self.assertNotIn("KeyboardAccelerator(",selected)

    def test_existing_keydown_still_owns_execution(self):
        src=(ROOT/"app/winui/m22_transfers.cpp").read_text(encoding="utf-8-sig")
        for marker in (
            "VirtualKey::C", "VirtualKey::X", "VirtualKey::F2",
            "VirtualKey::Delete",
            "CopySelectedToWindowsClipboard(",
            "fxfile::filecommand::Kind::RenameSelected",
            "fxfile::shelltransfer::Kind::Recycle",
        ):
            self.assertIn(marker,src)
        self.assertIn("void MainWindow::ShowAppBackgroundContextMenu(",src)

if __name__=="__main__":
    unittest.main()
