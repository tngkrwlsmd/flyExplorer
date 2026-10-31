"""R12a: View-menu Details access without enabling preview or file mutation.

Source contract only. Windows executable and GUI acceptance remain separate.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class R12aDetailsViewEntry(unittest.TestCase):
    def test_toolbar_reuses_existing_details_pane_and_all_view_modes(self):
        xaml=read("app/winui/FileToolbar.xaml")
        header=read("app/winui/FileToolbar.xaml.h")
        impl=read("app/winui/FileToolbar.xaml.cpp")
        main=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn('x:Name="ViewFileInfoPaneItem" Text="세부 정보 창"',xaml)
        self.assertIn('Click="OnViewFileInfoPane"',xaml)
        self.assertIn("void SetFileInfoPaneState(bool visible);",header)
        self.assertIn("void OnViewFileInfoPane(",header)
        self.assertIn('Closed="OnViewFlyoutClosed"',xaml)
        self.assertIn("void OnViewFlyoutClosed(IInspectable const&,IInspectable const&);",header)
        self.assertIn("bool pendingFileInfoPaneToggle_=false;",header)
        self.assertIn("pendingFileInfoPaneToggle_=true;",impl)
        self.assertIn("const bool requested=pendingFileInfoPaneToggle_;",impl)
        self.assertIn("pendingFileInfoPaneToggle_=false;",impl)
        self.assertIn("if(requested&&IsLoaded()&&action_)action_(23);",impl)
        self.assertNotIn("OnViewFileInfoPane(IInspectable const&,RoutedEventArgs const&){if(action_)action_(23);}",impl)
        self.assertIn("ViewFileInfoPaneItem().IsChecked(visible)",impl)
        self.assertIn("if(action_)action_(23)",impl)
        self.assertIn("else if(command==23&&!ui->mFileOperations.busy()",main)
        self.assertIn("!ui->mFileOperations.pendingConfirmationToken()",main)
        self.assertIn("ui->OnToggleFileInfoPane(nullptr,nullptr)",main)
        self.assertIn("fileBar()->SetFileInfoPaneState(visible)",main)
        for n in range(8):
            self.assertIn(f"ChooseView({n})",impl)
        self.assertIn("ViewContentItem().IsChecked(value==7)",impl)

    def test_background_menu_retains_route_guard_and_details_check(self):
        code=read("app/winui/m22_transfers.cpp")
        menu=code.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
            "void MainWindow::",1)[0]
        self.assertEqual(menu.count("view.Items().Append(choice("),8)
        self.assertIn('detailsPane.Text(L"세부 정보 창")',menu)
        self.assertIn("detailsPane.IsEnabled(ready)",menu)
        self.assertIn("detailsPane.IsChecked(state.fileInfoPaneVisible)",menu)
        self.assertIn("detailsPane.Click(guarded(",menu)
        self.assertIn("ui.OnToggleFileInfoPane(nullptr,nullptr)",menu)
        self.assertIn("pane.routeIds[tab]!=route",menu)
        self.assertIn("sourceFilesystemFolder",menu)

    def test_preview_still_requires_existing_explicit_opt_in(self):
        xaml=read("app/winui/FileToolbar.xaml")
        main=read("app/winui/MainWindow.xaml.cpp")
        preview=read("app/winui/m24_preview.cpp")
        self.assertNotIn("ViewTextPreviewAccessItem",xaml)
        self.assertNotIn("OpenPreviewFromViewMenu()",main)
        self.assertNotIn("OpenPreviewFromViewMenu()",preview)
        self.assertIn("mTextPreviewEnabled=!mTextPreviewEnabled",preview)
        self.assertIn("if(!state.fileInfoPaneVisible){",main)
        self.assertIn("mTextPreviewEnabled=false;",main)
        self.assertIn("ApplyFileInfoPaneLayout();",main)

if __name__=="__main__":
    unittest.main()
