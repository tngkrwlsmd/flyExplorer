from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "winui"
BASE = ROOT / "src" / "base"

def read(path):
    return path.read_text(encoding="utf-8-sig")

class BookmarkContracts(unittest.TestCase):
    def test_native_store_is_built_into_product(self):
        project = read(APP / "flyExplorer.project-template.xml")
        for path in ("bookmark_features.cpp",
                     r"..\..\src\base\bookmark_store.cpp",
                     r"..\..\src\base\bookmark_store.h"):
            self.assertIn(path, project)

    def test_store_is_bounded_private_and_atomic(self):
        header = read(BASE / "bookmark_store.h")
        body = read(BASE / "bookmark_store.cpp")
        self.assertIn("kMaxItems = 100", header)
        self.assertIn("kMaxName = 256", header)
        self.assertIn("bookmarks-v1.txt", body)
        self.assertIn("MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH", body)
        self.assertIn("FILE_ATTRIBUTE_REPARSE_POINT", body)
        self.assertNotIn(r"APPDATA\fxfile", body)

    def test_legacy_import_is_explicit_read_only_source(self):
        body = read(BASE / "bookmark_store.cpp")
        self.assertIn('L"bookmark.item" + std::to_wstring(i)', body)
        self.assertIn('L".name"', body)
        self.assertIn('L".path"', body)
        self.assertIn("SHGetKnownFolderPath", body)
        self.assertNotIn("TypeBookmark", body)

    def test_winui_has_bookmark_bar_and_management_actions(self):
        xaml = read(APP / "MainWindow.xaml")
        header = read(APP / "MainWindow.xaml.h")
        for token in (
            'x:Name="BookmarkButtonsPanel"',
            'x:Name="AddBookmarkButton"',
            'x:Name="BookmarkManagerButton"',
            'x:Name="BookmarkPanel"',
            'x:Name="BookmarkManagerBox"',
            'x:Name="BookmarkNameEdit"',
            'x:Name="BookmarkImportPathBox"',
        ):
            self.assertIn(token, xaml)
        for handler in (
            "OnAddBookmark", "OnToggleBookmarks",
            "OnBookmarkSelectionChanged", "OnRenameBookmark",
            "OnDeleteBookmark", "OnImportBookmarks",
        ):
            self.assertIn(handler, header)

    def test_owned_gui_persistence_is_in_canonical_gui_stage(self):
        checks = read(ROOT / "tools" / "winui" / "run_checks.py")
        gui = read(ROOT / "tests" / "winui" / "test_bookmark_gui.py")
        self.assertIn("test_bookmark_gui.py", checks)
        for token in (
            "OWNED_BOOKMARK_ADD_RENAME_DELETE_IMPORT",
            "OWNED_BOOKMARK_RESTART_PERSISTENCE",
            "ORIGINAL_BOOKMARK_TEST_USER_CONFIG_SHA256_IDENTICAL",
        ):
            self.assertIn(token, gui)

if __name__ == "__main__":
    unittest.main()
