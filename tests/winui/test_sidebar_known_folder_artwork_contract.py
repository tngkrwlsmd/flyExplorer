"""Sidebar Known Folder artwork reuses the isolated fixed-key visual path."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class SidebarKnownFolderArtworkContract(unittest.TestCase):
    def test_six_profile_buttons_keep_fallback_and_add_native_image_slots(self):
        xaml=source("app/winui/NavigationSidebar.xaml")
        for key in ("Desktop","Documents","Downloads","Pictures","Music","Videos"):
            self.assertIn(f'x:Name="{key}FallbackIcon"',xaml)
            self.assertIn(f'x:Name="{key}Artwork"',xaml)
            self.assertIn(
                f'AutomationProperties.Name="Windows Known Folder sidebar artwork: {key}"',
                xaml,
            )
        self.assertIn('x:Name="HomeButton"',xaml)
        self.assertIn('x:Name="ThisPCButton"',xaml)

    def test_home_and_this_pc_keep_fluent_glyph_scope(self):
        xaml=source("app/winui/NavigationSidebar.xaml")
        self.assertIn('<FontIcon Glyph="&#xE80F;" FontSize="15"/>',xaml)
        self.assertIn('<FontIcon Glyph="&#xE7F8;" FontSize="15"/>',xaml)
        self.assertNotIn('x:Name="HomeArtwork"',xaml)
        self.assertNotIn('x:Name="ThisPCArtwork"',xaml)

    def test_sidebar_queries_fixed_known_folder_pixels_off_ui_thread(self):
        impl=source("app/winui/NavigationSidebar.xaml.cpp")
        for token in (
            "LoadKnownFolderArtwork()",
            "std::thread(",
            "queryKnownFolderVisuals(",
            'L"desktop",L"documents",L"downloads"',
            'L"pictures",L"music",L"videos"',
            "DispatcherQueue()",
            "queue.TryEnqueue(",
            "ApplyKnownFolderArtwork(",
            "WriteableBitmap pixels(16,16)",
            "fallback.Visibility(Visibility::Collapsed)",
        ):
            self.assertIn(token,impl)
        self.assertNotIn("SHGetKnownFolderPath",impl)
        self.assertNotIn("IShellItemImageFactory",impl)

    def test_existing_file_list_visual_contract_remains_shared_source(self):
        core=source("src/base/shell_assoc_type_core.cpp")
        header=source("src/base/shell_assoc_type_core.h")
        worker=source("app/winui/file_detail_controller.cpp")
        self.assertIn("queryKnownFolderVisuals(",header)
        self.assertIn('L"--known-folder-visuals"',core)
        self.assertIn("queryKnownFolderVisuals(",worker)

if __name__=="__main__":
    unittest.main()
