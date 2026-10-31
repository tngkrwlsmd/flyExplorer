"""R03 Content mode source contract; runtime and pixels require Windows checks."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def src(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class ContentViewContracts(unittest.TestCase):
    def test_append_only_mode_and_v4_policy(self):
        state=src("app/winui/file_list_state.h")
        self.assertIn("Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4, ExtraLargeIcons=5, Tiles=6, Content=7",state)
        session=src("src/base/ui_session.cpp")
        self.assertIn("pane.view>7",session)
        self.assertIn("if(version==4)return decodeV4",session)
        pref=src("src/base/ui_preferences.cpp")
        for x in ('case 7:return "content"', "view<8", "pref.defaultViewMode>7"):
            self.assertIn(x,pref)
        self.assertIn("mode<0||mode>7",src("app/winui/folder_view_controller.h"))

    def test_existing_view_entries_and_bounded_content_command(self):
        xaml=src("app/winui/FileToolbar.xaml")
        header=src("app/winui/FileToolbar.xaml.h")
        toolbar=src("app/winui/FileToolbar.xaml.cpp")
        main=src("app/winui/MainWindow.xaml.cpp")
        self.assertIn('x:Name="ViewContentItem" Text="내용" Click="OnViewContent"',xaml)
        self.assertIn("OnViewContent(",header)
        self.assertIn("ChooseView(7)",toolbar)
        self.assertIn("ViewContentItem().IsChecked(value==7)",toolbar)
        self.assertIn('choice(L"내용",viewMode==7,7,true)',src("app/winui/m22_transfers.cpp"))
        ctl=src("app/winui/m20_shell.cpp")
        self.assertIn("if(selection<0||selection>7)return;",ctl)
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)",ctl)
        self.assertIn("case Windows::System::VirtualKey::Number8:",main)
        self.assertIn("viewShortcut=static_cast<int>(FileViewMode::Content)",main)
        self.assertIn("const int next=(std::max)(0,(std::min)(5,",main)
        self.assertIn("defaultViewMode,0,7",main)

    def test_content_row_is_responsive_cached_and_not_new_file_io(self):
        main=src("app/winui/MainWindow.xaml.cpp")
        self.assertIn("const bool contentMode=state.viewMode==FileViewMode::Content",main)
        self.assertIn("requestedView==FileViewMode::Content?32",main)
        self.assertIn("contentMode?32.0:",main)
        self.assertIn("contentRow.ColumnDefinitions().Append(summaryColumn)",main)
        self.assertIn("summaryColumn.Width(GridLength{1.0,GridUnitType::Star})",main)
        self.assertIn("row.HorizontalContentAlignment(HorizontalAlignment::Stretch)",main)
        self.assertIn("addContentDetail(typeAndSize)",main)
        self.assertIn("metadata->bytesLabel",main)
        self.assertIn("addContentDetail(std::wstring(L\"수정: \")+metadata->dateLabel)",main)
        self.assertIn("ToolTipService::SetToolTip(filename,",main)
        self.assertIn("row.MinHeight(82)",main)
        self.assertNotIn("FileViewMode::Content",src("app/winui/file_detail_controller.cpp"))
        self.assertIn("kMaxThumbnailPixels=128",src("src/base/shell_visual_wire.h"))

if __name__=="__main__":unittest.main()
