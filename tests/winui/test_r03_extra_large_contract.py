"""R03 extra-large icon source contract; actual WinUI GUI is checked separately."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

class R03ExtraLargeContract(unittest.TestCase):
    def test_append_only_mode_number_and_v4_schema(self):
        enum = read("app/winui/file_list_state.h")
        self.assertIn("Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4, ExtraLargeIcons=5", enum)
        v4 = read("src/base/ui_session.cpp")
        self.assertIn("pane.view>5", v4)
        self.assertIn("if(version==4)return decodeV4", v4)
        prefs = read("src/base/ui_preferences.cpp")
        for token in ('case 5:return "extra-large-icons"', "view<6", "pref.defaultViewMode>5"):
            self.assertIn(token, prefs)
        self.assertIn("mode<0||mode>5", read("app/winui/folder_view_controller.h"))

    def test_live_commands_and_selection_owner(self):
        bar = read("app/winui/FileToolbar.xaml")
        cpp = read("app/winui/FileToolbar.xaml.cpp")
        main = read("app/winui/MainWindow.xaml.cpp")
        for token in ('x:Name="ViewExtraLargeIconsItem"', 'Click="OnViewExtraLargeIcons"'):
            self.assertIn(token, bar)
        self.assertIn("OnViewExtraLargeIcons(", read("app/winui/FileToolbar.xaml.h"))
        self.assertIn("ChooseView(5)", cpp)
        self.assertIn("ViewExtraLargeIconsItem().IsChecked(value==5)", cpp)
        self.assertIn('choice(L"아주 큰 아이콘",viewMode==5,5,true)', read("app/winui/m22_transfers.cpp"))
        controller = read("app/winui/m20_shell.cpp")
        self.assertIn("if(selection<0||selection>5)return;", controller)
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)", controller)
        self.assertIn("(std::min)(5,", main)
        self.assertIn("FileViewMode::ExtraLargeIcons", main)
        self.assertIn("case Windows::System::VirtualKey::Number1:", main)

    def test_wrap_render_and_bounded_existing_thumbnail_api(self):
        main=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn('x:Key="ExplorerExtraLargeIconsItemsPanel"', read("app/winui/MainWindow.xaml"))
        self.assertIn('panel==4?L"ExplorerExtraLargeIconsItemsPanel"', main)
        self.assertIn("const bool iconGrid=medium||large||extraLarge", main)
        self.assertIn("const double targetSize=extraLarge?112.0:", main)
        self.assertIn("row.Width(168);row.Height(190)", main)
        self.assertIn("requestedView==FileViewMode::ExtraLargeIcons?128.0", main)
        self.assertEqual(read("app/winui/file_detail_controller.cpp").count(
            "request.viewMode==FileViewMode::ExtraLargeIcons"), 2)
        self.assertIn("kMaxThumbnailPixels=128", read("src/base/shell_visual_wire.h"))

if __name__ == "__main__":
    unittest.main()
