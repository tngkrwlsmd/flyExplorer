"""R12 View-menu access to already supported details and opt-in text preview.

This is source-contract evidence only; Windows build and GUI are separate.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT/path).read_text(encoding="utf-8-sig")

class R12ViewPaneAccess(unittest.TestCase):
    def test_toolbar_view_menu_routes_without_changing_eight_modes(self):
        xaml=read("app/winui/FileToolbar.xaml")
        hdr=read("app/winui/FileToolbar.xaml.h")
        toolbar=read("app/winui/FileToolbar.xaml.cpp")
        main=read("app/winui/MainWindow.xaml.cpp")
        for marker in (
            'x:Name="ViewFileInfoPaneItem" Text="세부 정보 창"',
            'x:Name="ViewTextPreviewAccessItem" Text="텍스트 미리보기 버튼으로 이동 (Alt+P)"',
            'Click="OnViewFileInfoPane"', 'Click="OnViewTextPreviewAccess"',
        ):
            self.assertIn(marker,xaml)
        for marker in ("void SetFileInfoPaneState(bool visible);",
                       "void OnViewFileInfoPane(", "void OnViewTextPreviewAccess("):
            self.assertIn(marker,hdr)
        self.assertIn("ViewFileInfoPaneItem().IsChecked(visible)",toolbar)
        self.assertIn("if(action_)action_(23)",toolbar)
        self.assertIn('MenuFlyout Closed="OnViewFlyoutClosed"',xaml)
        self.assertIn("void OnViewFlyoutClosed(",hdr)
        self.assertIn("previewFocusAfterViewClosed_=false",hdr)
        self.assertIn("if(action_)previewFocusAfterViewClosed_=true;",toolbar)
        self.assertIn("if(focus&&IsLoaded()&&action_)action_(24)",toolbar)
        self.assertIn("else if(command==23",main)
        self.assertIn("ui->OnToggleFileInfoPane(nullptr,nullptr)",main)
        self.assertIn("else if(command==24)ui->OpenPreviewFromViewMenu()",main)
        self.assertIn("fileBar()->SetFileInfoPaneState(visible)",main)
        self.assertIn("ViewContentItem().IsChecked(value==7)",toolbar)
        for index in range(8):
            self.assertIn(f"ChooseView({index})",toolbar)

    def test_background_view_menu_same_owner_and_checked_details(self):
        app=read("app/winui/m22_transfers.cpp")
        body=app.split("void MainWindow::ShowAppBackgroundContextMenu(",1)[1].split(
            "void MainWindow::",1)[0]
        self.assertEqual(body.count("view.Items().Append(choice("),8)
        self.assertIn('detailsPane.Text(L"세부 정보 창")',body)
        self.assertIn("detailsPane.IsChecked(state.fileInfoPaneVisible)",body)
        self.assertIn("detailsPane.Click(guarded(",body)
        self.assertIn("ui.OnToggleFileInfoPane(nullptr,nullptr)",body)
        self.assertIn('make(L"텍스트 미리보기 버튼으로 이동 (Alt+P)"',body)
        self.assertIn("*focusPreviewAfterClose=true",body)
        self.assertIn("if(std::exchange(*focusPreviewAfterClose,false))",body)
        self.assertIn("ui->OpenPreviewFromViewMenu()",body)
        self.assertIn("pane.routeIds[tab]!=route",body)
        self.assertIn("sourceFilesystemFolder",body)
        self.assertIn("pane.routeIds[tab]!=route",body)

    def test_no_implicit_preview_read_or_new_reader(self):
        code=read("app/winui/m24_preview.cpp")
        body=code.split("void MainWindow::OpenPreviewFromViewMenu()",1)[1].split(
            "void MainWindow::OnFileInfoViewportSizeChanged(",1)[0]
        self.assertIn("mFileOperations.pendingConfirmationToken()",body)
        self.assertIn("OnToggleFileInfoPane(nullptr,nullptr)",body)
        self.assertIn("OnRevealTextPreview(nullptr,nullptr)",body)
        self.assertIn("RootShell().UpdateLayout()",body)
        self.assertIn("DispatcherQueue().TryEnqueue([weak,origin]",body)
        self.assertIn("ui->ActiveWindowTab().identity==origin",body)
        for forbidden in ("QueueTextPreview()", "mTextPreviewEnabled=true",
                          "mTextPreviewEnabled=!mTextPreviewEnabled",
                          "mTextPreviewController.start(", "CreateFileW("):
            self.assertNotIn(forbidden,body)
        self.assertIn("mTextPreviewEnabled=!mTextPreviewEnabled",
                      code.split("void MainWindow::OnToggleTextPreview(",1)[1])
        main=read("app/winui/MainWindow.xaml.cpp")
        self.assertIn("if(!state.fileInfoPaneVisible){",main)
        self.assertIn("mTextPreviewEnabled=false;",main)
        self.assertIn("ApplyFileInfoPaneLayout();",main)

if __name__=="__main__":
    unittest.main()
