"""R04 selected-item shortcut contracts. Source-only, not Windows GUI validation."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

class R04ShortcutContract(unittest.TestCase):
    def test_guarded_context_menu_uses_existing_anchored_editor(self):
        menu=(ROOT/"app/winui/m22_transfers.cpp").read_text(encoding="utf-8")
        selected=menu.split("void MainWindow::ShowAppFileContextMenu(",1)[1].split(
            "void MainWindow::ShowAppBackgroundContextMenu(",1)[0]
        self.assertIn('make(L"바로 가기 만들기"',selected)
        self.assertIn("canRename",selected)
        self.assertIn("focusShortcutNameAfterClose",selected)
        self.assertIn("Kind::CreateShortcut",selected)
        bar=(ROOT/"app/winui/FileToolbar.xaml.cpp").read_text(encoding="utf-8")
        self.assertIn("pendingNameAction_==4?22",bar)
        win=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text(encoding="utf-8")
        self.assertIn("else if(command==22)ui->ExecuteFileCommand(",win)
        source=(ROOT/"app/winui/m21_commands.cpp").read_text(encoding="utf-8")
        for marker in ("Kind::CreateShortcut?4:", "validShortcutLeaf(request.name)",
                       "sameScope(editContext,liveContext)", "sameRenameSource(",
                       "mFileOperations.startFileCommand(",
                       'L"선택 항목의 바로 가기를 만들었습니다."'):
            self.assertIn(marker,source)
        self.assertLess(source.index("validShortcutLeaf(request.name)"),
                        source.index("mFileOperations.startFileCommand("))

    def test_native_worker_preserves_target_and_stages_no_replace(self):
        header=(ROOT/"src/base/file_command_core.h").read_text(encoding="utf-8")
        self.assertIn("CreateShortcut",header)
        core=(ROOT/"src/base/file_command_core.cpp").read_text(encoding="utf-8")
        body=core.split("if(task.kind==Kind::CreateShortcut){",1)[1].split(
            "if(task.kind!=Kind::RenameSelected)",1)[0]
        for marker in ("validShortcutLeaf(task.name)", "DRIVE_FIXED",
                       "FILE_ATTRIBUTE_REPARSE_POINT", "src.parent_path()!=folder",
                       "GetFileAttributesW(target.c_str())", "CREATE_NEW",
                       "IPersistFile*", "CLSID_ShellLink", "persist->Save(",
                       "MOVEFILE_WRITE_THROUGH", "::DeleteFileW(stage.c_str())"):
            self.assertIn(marker,body)
        self.assertNotIn("MOVEFILE_REPLACE_EXISTING",body)
        self.assertNotIn("CREATE_ALWAYS",body)
        native=(ROOT/"tests/winui/m21/m21_native_fixture.cpp").read_text(encoding="utf-8")
        for marker in ("shortcut_creates_nonempty_link_preserves_source",
                       "shortcut_resolves_exact_selected_source",
                       "shortcut_never_overwrites_existing_link",
                       "shortcut_accepts_uppercase_extension",
                       "shortcut_denies_unsafe_link_names",
                       "shortcut_denies_nonchild_source",
                       "shortcut_denies_missing_source"):
            self.assertIn(marker,native)

if __name__=="__main__":
    unittest.main()
