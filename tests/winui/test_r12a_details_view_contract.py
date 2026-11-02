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
        self.assertIn('<ToggleMenuFlyoutItem x:Name="ViewFileInfoPaneItem" Text="세부 정보 창"',xaml)
        self.assertNotIn('<MenuFlyoutItem x:Name="ViewFileInfoPaneItem"',xaml)
        self.assertIn('Click="OnViewFileInfoPane"',xaml)
        self.assertIn('<MenuFlyout Opening="OnViewFlyoutOpening" Closed="OnViewFlyoutClosed" Placement="Bottom">',xaml)
        self.assertIn('<Style TargetType="MenuFlyoutPresenter">',xaml)
        self.assertIn('<Setter Property="MaxHeight" Value="400"/>',xaml)
        self.assertLess(xaml.index('x:Name="ViewFileInfoPaneItem"'),
                        xaml.index('x:Name="ViewDetailsItem"'))
        self.assertIn("void SetFileInfoPaneState(bool visible);",header)
        self.assertIn("void OnViewFileInfoPane(",header)
        self.assertIn('Closed="OnViewFlyoutClosed"',xaml)
        self.assertIn("void OnViewFlyoutOpening(IInspectable const&,IInspectable const&);",header)
        self.assertIn("void OnViewFlyoutClosed(IInspectable const&,IInspectable const&);",header)
        self.assertIn("bool fileInfoPaneVisible_=false;",header)
        self.assertIn("ViewFileInfoPaneItem().IsChecked(fileInfoPaneVisible_);",impl)
        self.assertIn("fileInfoPaneVisible_=visible;",impl)
        self.assertIn("bool pendingFileInfoPaneToggle_=false;",header)
        self.assertIn("pendingFileInfoPaneToggle_=true;",impl)
        self.assertIn("const bool requested=pendingFileInfoPaneToggle_;",impl)
        self.assertIn("pendingFileInfoPaneToggle_=false;",impl)
        self.assertIn("if(!requested||!IsLoaded())return;",impl)
        self.assertIn("auto queue=DispatcherQueue();",impl)
        self.assertIn("auto weak=get_weak();",impl)
        self.assertIn("queue.TryEnqueue([weak,generation,identity]{",impl)
        self.assertIn("if(toolbar->IsLoaded()&&toolbar->action_){",impl)
        self.assertIn("toolbar->action_(23);",impl)
        self.assertNotIn("OnViewFileInfoPane(IInspectable const&,RoutedEventArgs const&){if(action_)action_(23);}",impl)
        self.assertIn('void FileToolbar::SetFileInfoPaneState(bool visible){',impl)
        self.assertNotIn("ViewFileInfoPaneItem().Text(",impl)
        self.assertIn('Text="세부 정보 창"',xaml)
        self.assertNotIn("ViewFileInfoPaneItem().IsChecked(visible)",impl)
        self.assertNotIn("item.Icon(checkedIcon)",impl)
        self.assertNotIn("FontIcon checkedIcon",impl)
        self.assertNotIn('OnViewFileInfoPane(IInspectable const&,RoutedEventArgs const&){if(action_)action_(23);}',impl)
        self.assertIn("else if(command==23&&!ui->mFileOperations.busy()",main)
        self.assertIn("!ui->mFileOperations.pendingConfirmationToken()",main)
        self.assertIn("ui->OnToggleFileInfoPane(nullptr,nullptr)",main)
        self.assertIn("fileBar()->SetFileInfoPaneState(visible)",main)
        for n in range(8):
            self.assertIn(f"ChooseView({n})",impl)
        self.assertIn("ViewContentItem().IsChecked(value==7)",impl)


    def test_mouse_tap_fallback_preserves_click_and_closed_dispatch(self):
        """R32 rescue is item-local, queued, one-shot and keyboard-neutral."""
        code=read("app/winui/FileToolbar.xaml.cpp")
        header=read("app/winui/FileToolbar.xaml.h")
        xaml=read("app/winui/FileToolbar.xaml")
        main=read("app/winui/MainWindow.xaml.cpp")
        assert "Click=\"OnViewFileInfoPane\"" in xaml
        self.assertIn("OnViewFileInfoPaneTapped(",header)
        self.assertIn("viewFileInfoPaneClaimed_=false;",code)
        self.assertIn("++viewFlyoutGeneration_;",code)
        self.assertIn("ViewFileInfoPaneItem().AddHandler(UIElement::TappedEvent()",code)
        self.assertIn("if(auto toolbar=tapWeak.get())toolbar->OnViewFileInfoPaneTapped(sender,args);",code)
        self.assertIn("}}),true);",code)
        tapped=code.split("void FileToolbar::OnViewFileInfoPaneTapped(",1)[1].split(
            "void FileToolbar::OnViewFlyoutClosed(",1)[0]
        clicked=code.split("void FileToolbar::OnViewFileInfoPane(",1)[1].split(
            "void FileToolbar::OnViewFileInfoPaneTapped(",1)[0]
        closed=code.split("void FileToolbar::OnViewFlyoutClosed(",1)[1].split(
            "void FileToolbar::OnRememberFolderView(",1)[0]
        self.assertIn("winrt::Microsoft::UI::Input::PointerDeviceType::Mouse",tapped)
        self.assertNotIn("winrt::Windows::Devices::Input::PointerDeviceType",code)
        self.assertIn("#include <winrt/Microsoft.UI.Input.h>",code)
        self.assertIn("viewFileInfoPaneClaimed_",clicked)
        self.assertIn("viewFileInfoPaneClaimed_",tapped)
        self.assertIn("viewFlyoutGeneration_!=generation",tapped)
        self.assertIn("!flyout.IsOpen()",tapped)
        self.assertIn("flyout.Hide();",tapped)
        self.assertLess(tapped.index("viewFileInfoPaneClaimed_=true;"),
                        tapped.index("flyout.Hide();"))
        self.assertNotIn("action_(23)",tapped)
        self.assertIn("viewFlyoutOpen_=false;",closed)
        self.assertIn("pendingFileInfoPaneToggle_=false;",closed)
        self.assertIn("viewFlyoutGeneration_!=generation",closed)
        self.assertIn("fileInfoPaneContext_()!=identity",closed)
        self.assertIn("std::function<std::optional<std::uint64_t>()> fileInfoPaneContext_;",header)
        self.assertIn("std::optional<std::uint64_t> fileInfoPaneOpenIdentity_;",header)
        self.assertIn("fileInfoPaneContext_?fileInfoPaneContext_():std::nullopt;",code)
        self.assertIn("!toolbar->fileInfoPaneOpenIdentity_",tapped)
        self.assertIn("!identity||toolbar->fileInfoPaneContext_()!=identity",closed)
        self.assertNotIn("fileInfoPaneOpenIdentity_==0",code)
        self.assertNotIn("identity==0||",closed)
        self.assertIn("return std::nullopt;",main)
        self.assertIn("states_.emplace_back(0);",
                      read("app/winui/window_workspace_controller.cpp"))
        self.assertIn("toolbar->fileInfoPaneContext_()!=toolbar->fileInfoPaneOpenIdentity_",tapped)
        self.assertIn("queue.TryEnqueue([weak,generation,identity]",closed)
        self.assertIn("fileBar()->SetFileInfoPaneContext([nativeWeak]",main)
        self.assertIn("return ui->ActiveWindowTab().identity;",main)
        self.assertIn("toolbar->action_(23);",closed)
        self.assertLess(closed.index("pendingFileInfoPaneToggle_=false;"),
                        closed.index("toolbar->action_(23);"))
        self.assertIn("else if(command==23&&!ui->mFileOperations.busy()",main)
        self.assertIn("!ui->mFileOperations.pendingConfirmationToken()",main)

    def test_bounded_opt_in_r12_event_trace(self):
        code=read("app/winui/FileToolbar.xaml.cpp")
        gui=read("tests/winui/test_r12a_details_view_gui.py")
        self.assertIn('GetEnvironmentVariableW(L"R12_UI_TRACE"',code)
        self.assertIn('GetTempPathW(MAX_PATH+1,directory)',code)
        self.assertIn('FILE_APPEND_DATA',code)
        self.assertIn('os.environ["R12_UI_TRACE"]="1"',gui)
        self.assertIn('app.profile/"tmp"/"flyExplorer-r12-events.log"',gui)
        for phase in ("flyout_open","details_click","flyout_closed",
                      "queue_added","action23_dispatch","pane_state"):
            self.assertIn('R12EventTrace("'+phase+'"',code)

    def test_opt_in_handled_pointer_trace_distinguishes_input_from_click(self):
        code=read("app/winui/FileToolbar.xaml.cpp")
        gui=read("tests/winui/test_r12a_details_view_gui.py")
        ctor=code.split("FileToolbar::FileToolbar(){",1)[1].split(
            "void FileToolbar::SetAction(",1)[0]
        self.assertIn('GetEnvironmentVariableW(L"R12_UI_TRACE"',ctor)
        self.assertIn("if(GetEnvironmentVariableW(",ctor)
        self.assertIn("PointerPressedEvent()",ctor)
        self.assertIn("PointerReleasedEvent()",ctor)
        self.assertIn("R12EventTrace(pressed,1)",ctor)
        self.assertIn("R12EventTrace(released,1)",ctor)
        self.assertIn("}),true);",ctor)
        self.assertIn('attach(ViewFileInfoPaneItem(), "details_press", "details_release",',ctor)
        self.assertIn('attach(ViewDetailsItem(), "other_press", "other_release",',ctor)
        self.assertIn("PointerCanceledEvent()",ctor)
        self.assertIn("PointerCaptureLostEvent()",ctor)
        self.assertIn("PointerEnteredEvent()",ctor)
        self.assertIn("PointerExitedEvent()",ctor)
        self.assertIn("TappedEvent()",ctor)
        self.assertIn('R12EventTrace(tapped,1)',ctor)
        self.assertIn("(item.IsEnabled()?1:0)",ctor)
        self.assertIn("(item.IsChecked()?2:0)",ctor)
        self.assertIn("(item.IsHitTestVisible()?4:0)",ctor)
        for phase in ("details_press","details_release","details_pstate",
                      "details_rstate","details_ostate","details_cancel",
                      "details_capture_lost","details_enter","details_exit",
                      "details_tap","other_press","other_release",
                      "other_pstate","other_rstate","other_cancel",
                      "other_capture_lost","other_enter","other_exit",
                      "other_tap"):
            self.assertIn('"'+phase+'"',gui)
        self.assertIn('R12EventTrace("details_click"',code)
        self.assertIn('R12EventTrace("flyout_closed"',code)
        self.assertIn('R12EventTrace("action23_dispatch"',code)

    def test_failed_second_pointer_click_snapshots_before_fallback_probes(self):
        gui=read("tests/winui/test_r12a_details_view_gui.py")
        self.assertIn("def read_owned_trace():",gui)
        self.assertIn('app.profile/"tmp"/"flyExplorer-r12-events.log"',gui)
        self.assertIn('trace.is_symlink()',gui)
        self.assertIn("if len(raw)>16384:",gui)
        self.assertIn('return [],"unexpected_event_shape"',gui)
        self.assertIn("events,error=read_owned_trace()",gui)
        second=gui.split("# Snapshot the second physical attempt",1)[1].split(
            "raise\n",1)[0]
        self.assertIn("events,trace_error=read_owned_trace()",second)
        self.assertIn('if event["phase"]=="flyout_open"',second)
        self.assertIn("if len(opens)>=2:",second)
        self.assertIn("attempt=events[opens[-1]:]",second)
        self.assertIn('"second_click_event_gates"',second)
        self.assertIn('"second_click_trace_events"',second)
        self.assertLess(second.index("events,trace_error=read_owned_trace()"),
                        second.index("alternatives={}"))
        self.assertLess(second.index("events,trace_error=read_owned_trace()"),
                        second.index("retry.invoke()"))
        for phase in ("details_press","details_release","details_pstate",
                      "details_rstate","details_ostate","details_cancel",
                      "details_capture_lost","details_enter","details_exit",
                      "details_tap","details_click",
                      "flyout_closed","queue_added","action23_dispatch"):
            self.assertIn('"'+phase+'"',second)

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
