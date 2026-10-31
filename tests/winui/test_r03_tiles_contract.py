"""R03 Tiles source-level contracts. Real WinUI and pixels require Windows evidence."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def source(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class TilesContracts(unittest.TestCase):
    def test_append_mode_without_v4_format_migration(self):
        state=source("app/winui/file_list_state.h")
        self.assertIn("Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4, ExtraLargeIcons=5, Tiles=6", state)
        v4=source("src/base/ui_session.cpp")
        self.assertIn("pane.view>7",v4)
        self.assertIn("if(version==4)return decodeV4",v4)
        prefs=source("src/base/ui_preferences.cpp")
        for s in ('case 6:return "tiles"', 'view<8', 'pref.defaultViewMode>7'):
            self.assertIn(s,prefs)
        self.assertIn("mode<0||mode>7",source("app/winui/folder_view_controller.h"))

    def test_menu_keyboard_and_zoom_boundaries(self):
        bar=source("app/winui/FileToolbar.xaml")
        cpp=source("app/winui/FileToolbar.xaml.cpp")
        window=source("app/winui/MainWindow.xaml.cpp")
        self.assertIn('x:Name="ViewTilesItem" Text="타일" Click="OnViewTiles"',bar)
        self.assertIn("OnViewTiles(",source("app/winui/FileToolbar.xaml.h"))
        self.assertIn("ChooseView(6)",cpp)
        self.assertIn("ViewTilesItem().IsChecked(value==6)",cpp)
        self.assertIn('choice(L"타일",viewMode==6,6,true)',source("app/winui/m22_transfers.cpp"))
        self.assertIn("if(selection<0||selection>7)return;",source("app/winui/m20_shell.cpp"))
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)",source("app/winui/m20_shell.cpp"))
        self.assertIn("case Windows::System::VirtualKey::Number7:",window)
        self.assertIn("viewShortcut=static_cast<int>(FileViewMode::Tiles)",window)
        # Tiles are not an icon-size step; Ctrl+wheel keeps previous 0..5.
        self.assertIn("const int next=(std::max)(0,(std::min)(5,",window)

    def test_tile_visual_has_type_size_and_no_new_thumbnail_access(self):
        main=source("app/winui/MainWindow.xaml.cpp")
        self.assertIn('x:Key="ExplorerTilesItemsPanel"',source("app/winui/MainWindow.xaml"))
        self.assertIn('panel==5?L"ExplorerTilesItemsPanel"',main)
        self.assertIn("const bool tiles=state.viewMode==FileViewMode::Tiles",main)
        self.assertIn("const double targetSize=tiles?48.0:",main)
        self.assertIn("fields.Children().Append(filename)",main)
        self.assertIn("addTileDetail(typeLabel.empty()?",main)
        self.assertIn("addTileDetail(metadata->bytesLabel)",main)
        self.assertIn("row.Width(256);row.Height(80)",main)
        self.assertIn("requestedView==FileViewMode::Tiles?48",main)
        self.assertNotIn("FileViewMode::Tiles",source("app/winui/file_detail_controller.cpp"))
        self.assertIn("kMaxThumbnailPixels=128",source("src/base/shell_visual_wire.h"))

if __name__=="__main__":
    unittest.main()
