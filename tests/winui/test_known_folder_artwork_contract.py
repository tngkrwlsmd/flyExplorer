"""Path-specific Known Folder artwork stays bounded and isolated."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT/path).read_text(encoding="utf-8")

class KnownFolderArtworkContract(unittest.TestCase):
    def test_fixed_known_folder_key_allowlist_and_os_resolution(self):
        header=source("src/base/shell_assoc_type_core.h")
        core=source("src/base/shell_assoc_type_core.cpp")
        self.assertIn("safeKnownFolderKey",header)
        self.assertIn("knownFolderPath",header)
        self.assertIn("queryKnownFolderVisuals",header)
        for key in ("desktop","documents","downloads","pictures","music","videos"):
            self.assertIn('L"'+key+'"',core)
        for token in (
            "FOLDERID_Desktop","FOLDERID_Documents","FOLDERID_Downloads",
            "FOLDERID_Pictures","FOLDERID_Music","FOLDERID_Videos",
            "SHGetKnownFolderPath",
        ):
            self.assertIn(token,core)

    def test_helper_accepts_only_fixed_tokens_and_returns_pixels(self):
        helper=source("app/winui/helper/FlyShellIsolationHelper.cpp")
        self.assertIn('L"--known-folder-visuals"',helper)
        self.assertIn("argc>9",helper)
        self.assertIn("SHGetKnownFolderPath",helper)
        self.assertIn("SHGetFileInfoW(path,0",helper)
        self.assertIn("IShellItemImageFactory",helper)
        self.assertIn("SIIGBF_ICONONLY",helper)
        self.assertIn("SHCreateItemFromParsingName",helper)
        self.assertIn("GetDIBits",helper)
        self.assertIn("CryptBinaryToStringA",helper)

    def test_file_detail_prefers_known_artwork_and_keeps_generic_fallback(self):
        worker=source("app/winui/file_detail_controller.cpp")
        state=source("app/winui/file_list_state.h")
        app=source("app/winui/MainWindow.xaml.cpp")
        self.assertIn("knownFolderKeyByIndex",worker)
        self.assertIn("queryKnownFolderVisuals(",worker)
        self.assertIn('windowsTypes.find(L".flyfolder")',worker)
        self.assertIn("entry.knownFolderVisual=true",worker)
        self.assertIn("bool knownFolderVisual=false",state)
        self.assertIn('L"Windows Known Folder artwork"',app)
        self.assertNotIn("SHGetFileInfoW",worker)
        self.assertNotIn("SHGetKnownFolderPath",app)

if __name__=="__main__":
    unittest.main()
