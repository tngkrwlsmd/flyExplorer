"""M2.6 Windows 11 Fluent shell source/architecture guardrails."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/"app"/"winui"
XNS="{http://schemas.microsoft.com/winfx/2006/xaml}Name"

def text(name):
    return (A/name).read_text(encoding="utf-8-sig")

def names(name):
    root=ET.parse(A/name).getroot()
    return {e.get(XNS) for e in root.iter() if e.get(XNS)}

def attr_values(name):
    root=ET.parse(A/name).getroot()
    return {v for e in root.iter() for v in e.attrib.values() if v}

class FluentShellContract(unittest.TestCase):
    def test_public_custom_titlebar_and_mica_with_safe_fallback(self):
        xaml=text("MainWindow.xaml")
        header=text("ShellHeader.xaml")
        impl=text("MainWindow.xaml.cpp")
        self.assertIn('Background="Transparent"',xaml)
        self.assertIn('x:Name="TitleBarDragRegion"',header)
        self.assertIn("ExtendsContentIntoTitleBar(true)",impl)
        self.assertIn("SetTitleBar(titleHeader->DragRegion())",impl)
        self.assertIn("SystemBackdrop(Microsoft::UI::Xaml::Media::MicaBackdrop{}",impl)
        self.assertNotIn("DwmExtendFrameIntoClientArea",impl)

    def test_explorer_like_v4_compact_title_chrome_without_fake_window_tabs(self):
        main=text("MainWindow.xaml")
        header=text("ShellHeader.xaml")
        impl=text("MainWindow.xaml.cpp")
        self.assertIn('x:Name="TitleBarRoot" Height="34" Padding="10,0,142,0"',header)
        self.assertIn('x:Name="WindowTabStrip" Grid.Column="1"',header)
        self.assertIn('x:Name="TitleBarDragRegion" Grid.Column="2" MinWidth="48"',header)
        self.assertIn('x:Name="ShellHeading" Text="flyExplorer"',header)
        self.assertIn('FontSize="12" FontWeight="Normal" Opacity="0.82"',header)
        self.assertIn('<TabView',header)
        self.assertEqual(main.count('<TabView '),2)
        self.assertIn('<RowDefinition Height="34"/>',main)
        self.assertIn("ExtendsContentIntoTitleBar(true)",impl)
        self.assertIn("SetTitleBar(titleHeader->DragRegion())",impl)

    def test_explorer_command_address_search_and_overflow_surface(self):
        toolbar=text("FileToolbar.xaml")
        main=text("MainWindow.xaml")
        tn=names("FileToolbar.xaml")
        mn=names("MainWindow.xaml")
        self.assertIn("<CommandBar ",toolbar)
        self.assertIn('IsDynamicOverflowEnabled="True"',toolbar)
        self.assertIn('x:Name="ExplorerCommandBar" Grid.Column="0"',toolbar)
        self.assertIn('x:Name="FileNameBox" Grid.Column="1"',toolbar)
        self.assertIn('x:Name="SortPicker" Grid.Column="2"',toolbar)
        for n in ("ExplorerCommandBar","CreateFolderButton","RenameButton",
                  "WindowsCutButton","WindowsCopyButton","WindowsPasteButton",
                  "CopyButton","MoveButton","RecycleButton","SortPicker"):
            self.assertIn(n,tn)
        for n in ("BackButton","ForwardButton","UpButton","AddressBox",
                  "QuickSearchBox","NewTabButton","CloseTabButton","SplitButton"):
            self.assertIn(n,mn)
        self.assertIn("OnQuickSearchKeyDown",main)
        self.assertIn("OnShellSizeChanged",main)
        impl=text("MainWindow.xaml.cpp")
        self.assertIn("FriendlyAddress",impl)
        self.assertIn('return L"\\uB0B4 PC";',impl)
        self.assertIn('return L"shell:MyComputerFolder";',impl)

    def test_navigation_is_fluent_but_route_callbacks_stay_existing_model(self):
        nav=text("NavigationSidebar.xaml")
        impl=text("MainWindow.xaml.cpp")
        nn=names("NavigationSidebar.xaml")
        self.assertIn("ExplorerNavButtonStyle",nav)
        self.assertIn('Background" Value="Transparent"',nav)
        nav_impl=text("NavigationSidebar.xaml.cpp")
        self.assertIn("SetSelected(int target)",nav_impl)
        self.assertIn("SystemControlHighlightAccentBrush",nav_impl)
        self.assertIn("BorderThickness(i==target?",nav_impl)
        for n in ("HomeButton","DesktopButton","DownloadsButton",
                  "DocumentsButton","PicturesButton","MusicButton",
                  "VideosButton","ThisPCButton"):
            self.assertIn(n,nn)
        self.assertIn('ui->OpenFolder(L"shell:MyComputerFolder")',impl)
        self.assertNotIn("NavigationViewItemInvoked",impl)

    def test_dual_panel_is_preserved_with_subtle_chrome_and_aligned_headers(self):
        xaml=text("MainWindow.xaml")
        impl=text("MainWindow.xaml.cpp")
        self.assertEqual(xaml.count("<TabView "),2)
        for n in ("PrimaryPane","SecondaryPane","LeftFiles","RightFiles",
                  "LeftNameHeaderColumn","RightNameHeaderColumn",
                  "LeftNameFilterBox","RightNameFilterBox"):
            self.assertIn('x:Name="'+n+'"',xaml)
        self.assertIn("ExplorerListItemStyle",xaml)
        self.assertIn("ExplorerPaneTitleStyle",xaml)
        self.assertIn('Tapped="OnLeftPaneTapped"',xaml)
        self.assertIn('Tapped="OnRightPaneTapped"',xaml)
        for n in ("LeftTypeHeaderColumn","LeftSizeHeaderColumn","LeftDateHeaderColumn",
                  "RightTypeHeaderColumn","RightSizeHeaderColumn","RightDateHeaderColumn"):
            self.assertIn('x:Name="'+n+'"',xaml)
        self.assertIn('x:Key="ExplorerColumnResizeThumbStyle"',xaml)
        self.assertIn('<Setter Property="Width" Value="12"/>',xaml)
        self.assertIn('<Grid Background="Transparent">',xaml)
        self.assertIn('HorizontalAlignment="Right"',xaml)
        self.assertNotIn('Width="7" Margin="0,1,-3,1"',xaml)
        self.assertEqual(xaml.count('Style="{StaticResource ExplorerColumnResizeThumbStyle}"'),6)
        self.assertNotIn('PointerPressed="OnDetailColumnResizePointerPressed"',xaml)
        self.assertNotIn('PointerMoved="OnDetailColumnResizePointerMoved"',xaml)
        self.assertGreaterEqual(impl.count("RootShell().AddHandler("),4)
        self.assertIn("VisualTreeHelper::GetParent",impl)
        self.assertIn('find(\n               L"ColumnResizeThumb")',impl)
        self.assertIn("GetAsyncKeyState(VK_LBUTTON)",impl)
        self.assertGreaterEqual(impl.count("true);"),4)
        self.assertIn("ApplyDetailColumnLayout(int side)",impl)
        self.assertIn("DetailLayoutProfile() const",impl)
        self.assertIn("DetailColumnWidths(int side) const",impl)
        self.assertIn("GridUnitType::Star",impl)
        self.assertIn("if(pane<340.0)return 1",impl)
        self.assertIn("GridLength{0.0,GridUnitType::Pixel},GridLength{size,GridUnitType::Pixel}",impl)
        for thumb in ("LeftNameColumnResizeThumb","LeftTypeColumnResizeThumb",
                      "LeftSizeColumnResizeThumb","RightNameColumnResizeThumb",
                      "RightTypeColumnResizeThumb","RightSizeColumnResizeThumb"):
            self.assertIn('x:Name="'+thumb+'"',xaml)
        for token in ("OnDetailColumnResizePointerPressed",
                      "OnDetailColumnResizePointerMoved",
                      "OnDetailColumnResizePointerReleased",
                      "OnDetailColumnResizePointerCaptureLost",
                      "CapturePointer(args.Pointer())",
                      "ReleasePointerCapture(args.Pointer())"):
            self.assertIn(token,impl)
        self.assertNotIn("OnDetailColumnResizeDragDelta",impl)
        self.assertIn("PrimaryPane().BorderThickness(Thickness{0.0,2.0,0.0,0.0})",impl)
        self.assertIn("SecondaryPane().BorderThickness(Thickness{0.0,2.0,0.0,0.0})",impl)
        self.assertIn("AutomationProperties::SetName",impl)
        self.assertNotIn("left?2.0:1.0",impl)

    def test_explorer_like_v1_removes_default_development_chrome(self):
        main=text("MainWindow.xaml")
        toolbar=text("FileToolbar.xaml")
        header=text("ShellHeader.xaml")
        nav=text("NavigationSidebar.xaml")
        impl=text("MainWindow.xaml.cpp")
        self.assertIn('x:Name="AddressDisplayButton"',main)
        self.assertIn("CompactAddress",impl)
        self.assertIn('x:Name="LeftTabs" Grid.Row="1" Height="36"',main)
        self.assertIn('x:Name="RightTabs" Grid.Row="1" Height="36"',main)
        self.assertGreaterEqual(main.count('Grid.Row="2" Height="24"'),2)
        self.assertGreaterEqual(main.count('MinHeight="0" Opacity="0"'),4)
        self.assertIn('x:Name="FileNameBox" Grid.Column="1" Width="1" MinWidth="0"',toolbar)
        self.assertIn('x:Name="MoreButton"',toolbar)
        self.assertIn('x:Name="SortButton"',toolbar)
        self.assertIn('x:Name="ViewButton"',toolbar)
        self.assertIn('ExplorerSecondaryCommandButtonStyle',toolbar)
        self.assertIn('x:Name="BreadcrumbPanel"',main)
        self.assertIn('x:Name="AddressEditButton"',main)
        self.assertIn('OnBreadcrumbSegmentClicked',impl)
        self.assertIn('Width="1"',header)
        self.assertIn('Opacity="0"',header)
        self.assertNotIn("외부 Shell 작업은",nav)

    def test_explorer_like_v3_status_selection_and_keyboard_focus_contract(self):
        main=text("MainWindow.xaml")
        toolbar=text("FileToolbar.xaml")
        footer=text("StatusFooter.xaml")
        impl=text("MainWindow.xaml.cpp")
        for token in ('x:Name="ItemCountText"','x:Name="SelectionCountText"'):
            self.assertIn(token,footer)
        self.assertGreaterEqual(main.count('SelectionChanged="OnFileSelectionChanged"'),2)
        self.assertIn("UpdateFooterSummary()",impl)
        self.assertIn("UpdateSelectionChrome()",impl)
        self.assertIn("QueueSelectionPresentationUpdate()",impl)
        self.assertIn("side!=ActiveWindowTab().model.activePane",impl)
        self.assertGreaterEqual(main.count('UseSystemFocusVisuals" Value="True"'),2)
        self.assertGreaterEqual(toolbar.count('UseSystemFocusVisuals" Value="True"'),2)

    def test_explorer_like_v5_real_view_modes_and_shared_sort_contract(self):
        main=text("MainWindow.xaml")
        impl=text("MainWindow.xaml.cpp")
        toolbar=text("FileToolbar.xaml")
        state=text("file_list_state.h")
        prefs=text("../../src/base/ui_preferences.cpp")
        prefh=text("../../src/base/ui_preferences.h")
        self.assertIn("enum class FileViewMode : int { Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4 }",state)
        self.assertIn("FileViewMode viewMode=FileViewMode::Details",state)
        for token in ('x:Name="ViewDetailsItem"','x:Name="ViewListItem"',
                      'x:Name="ViewSmallIconsItem"','x:Name="ViewMediumIconsItem"',
                      'x:Name="ViewLargeIconsItem"'):
            self.assertIn(token,toolbar)
        self.assertIn("ExplorerSmallIconsItemsPanel",main)
        self.assertIn("ExplorerMediumIconsItemsPanel",main)
        self.assertIn("ExplorerLargeIconsItemsPanel",main)
        self.assertIn("UpdateViewPresentation(int side)",impl)
        self.assertIn("ActiveWindowTab().fileLists[side].viewMode",impl)
        self.assertIn("appliedItemsPanel",state)
        self.assertIn("ActiveWindowTab().fileLists[side].appliedItemsPanel!=panel",impl)
        self.assertIn("mFileDetails.cancel(side)",impl)
        self.assertIn("if(state.viewMode==FileViewMode::List){row.MinHeight(32)",impl)
        self.assertIn("row.KeyDown([weak,side]",impl)
        self.assertIn("ui->OpenSelectedFolder(side)",impl)
        self.assertIn("mPreferencesCoordinator.setDefaultViewMode(selection)",text("m20_shell.cpp"))
        self.assertIn("OnHeaderSortClicked",main)
        self.assertIn("UpdateSortPresentation(int side)",impl)
        self.assertIn("selection<0||selection>7",text("m22_transfers.cpp"))
        self.assertIn("defaultViewMode=0",prefh)
        self.assertIn("legacyText",prefs)
        self.assertIn('schema=2\\r\\nlanguage=ko-KR',prefs)
        self.assertIn('view="+viewName(view)',prefs)
        self.assertIn('case 4:return "large-icons"',prefs)
        self.assertIn("view<5",prefs)
        self.assertIn("defaultViewMode>4",prefs)
        session=(ROOT/"src/base/ui_session.cpp").read_text(encoding="utf-8")
        self.assertIn("pane.view>4",session)

    def test_v7_window_tab_state_owns_workspace_without_xaml(self):
        header=text("MainWindow.xaml.h")
        state=text("window_tab_state.h")
        self.assertIn("struct WindowTabState final",state)
        self.assertIn("fxfile::explorerui::Model model",state)
        self.assertIn("fileLists",state)
        self.assertNotIn("Microsoft::UI::Xaml",state)
        controller=text("window_workspace_controller.h")
        self.assertIn("WindowWorkspaceController mWorkspace",header)
        self.assertNotIn("mWindowTabs",header)
        self.assertNotIn("mActiveWindowTab",header)
        self.assertIn("std::vector<WindowTabState> states_",controller)
        self.assertIn("ActiveWindowTab()",header)
        self.assertNotIn("fxfile::explorerui::Model mModel",header)

    def test_explorer_like_v61_icon_view_density_contract(self):
        main=text("MainWindow.xaml")
        impl=text("MainWindow.xaml.cpp")
        self.assertIn('ExplorerSmallIconsItemsPanel',main)
        self.assertIn('ItemWidth="164" ItemHeight="34"',main)
        self.assertIn('ExplorerMediumIconsItemsPanel',main)
        self.assertIn('ItemWidth="96" ItemHeight="96"',main)
        self.assertIn('ExplorerLargeIconsItemsPanel',main)
        self.assertIn('ItemWidth="120" ItemHeight="132"',main)
        self.assertIn('row.Width(160);row.Height(32)',impl)
        self.assertIn('row.Width(92);row.Height(92)',impl)
        self.assertIn('row.Width(112);row.Height(128)',impl)
        self.assertIn('targetSize=large?64.0',impl)
        self.assertIn('filename.Width(large?104.0:84.0)',impl)
        self.assertIn('filename.FontSize(12.0);filename.Width(large?104.0:84.0)',impl)
        self.assertIn('filename.MaxLines(2)',impl)
        self.assertIn('UseSystemFocusVisuals" Value="True"',main)
        self.assertIn('row.MinHeight(32)',impl)
        self.assertIn('header.Height(details?24.0:0.0)',impl)

    def test_v7_private_session_v2_migration_contract(self):
        root=Path(__file__).resolve().parents[2]
        session_h=(root/"src/base/ui_session.h").read_text(encoding="utf-8")
        session_cpp=(root/"src/base/ui_session.cpp").read_text(encoding="utf-8")
        shell_h=(root/"src/base/shell_navigation_core.h").read_text(encoding="utf-8")
        coordinator=(root/"app/winui/session_coordinator.cpp").read_text(encoding="utf-8")
        app=(root/"app/winui/m23_session.cpp").read_text(encoding="utf-8")
        for token in ("struct WindowTab","std::vector<WindowTab> windowTabs",
                      "activeWindow","PaneTab"):
            self.assertIn(token,session_h)
        self.assertIn("if(version==1)return decodeV1",session_cpp)
        self.assertIn("if(version==2)return decodeV2",session_cpp)
        self.assertIn("bool historyLocations(HistoryLocations&)",shell_h)
        self.assertIn("historyPathsFromLocations",shell_h)
        self.assertIn("restoreHistoryPaths",coordinator)
        self.assertIn("payload->session.windowTabs",coordinator)
        self.assertIn("workspace.replace(",coordinator)
        self.assertIn("mSessionCoordinator.applyRestore(",app)

    def test_v7_functional_window_tab_chrome_contract(self):
        root=Path(__file__).resolve().parents[2]
        shell=(root/"app/winui/ShellHeader.xaml").read_text(encoding="utf-8")
        header=(root/"app/winui/ShellHeader.xaml.h").read_text(encoding="utf-8")
        impl=text("MainWindow.xaml.cpp")
        main=text("MainWindow.xaml")
        self.assertIn('x:Name="WindowTabStrip"',shell)
        self.assertIn('IsAddTabButtonVisible="True"',shell)
        self.assertIn("SetWindowTabCallbacks",header)
        for token in ('CreateWindowTab(L"shell:MyComputerFolder")',
                      "ActivateWindowTab","CloseWindowTab","PreviewKeyDown",
                      "GetKeyState(VK_CONTROL)","GetKeyState(VK_SHIFT)"):
            self.assertIn(token,impl)
        self.assertIn('x:Name="LeftTabs"',main)
        self.assertIn('x:Name="RightTabs"',main)

    def test_explorer_like_v6_isolated_shell_visual_contract(self):
        impl=text("MainWindow.xaml.cpp")
        detail=text("file_detail_controller.cpp")
        state=text("file_list_state.h")
        root=Path(__file__).resolve().parents[2]
        assoc=(root/"src/base/shell_assoc_type_core.cpp").read_text(encoding="utf-8")
        helper=(root/"app/winui/helper/FlyShellIsolationHelper.cpp").read_text(encoding="utf-8")
        for token in ("visualPixels","iconWidth","iconHeight"):
            self.assertIn(token,state)
        self.assertIn("RasterizationScale()",impl)
        self.assertIn("ActiveWindowTab().fileLists[side].accepts(",impl)
        for token in ('L".flyfolder"',
                      "request.viewMode==FileViewMode::MediumIcons||"):
            self.assertIn(token,detail)
        self.assertNotIn("SHGetFileInfoW",impl)
        self.assertNotIn("SHGetFileInfoW",detail)
        self.assertIn("requestedPixels",assoc)
        self.assertIn("visualQueryMutex",assoc)
        self.assertIn("SHGFI_LARGEICON",helper)
        self.assertIn("FILE_ATTRIBUTE_DIRECTORY",helper)

    def test_this_pc_local_drive_card_is_bounded_and_provider_safe(self):
        impl=text("MainWindow.xaml.cpp")
        for token in ("GetDriveTypeW","DRIVE_FIXED","DRIVE_REMOVABLE",
                      "GetDiskFreeSpaceExW","ProgressBar usage",
                      "GB \uc0ac\uc6a9 \uac00\ub2a5 / "):
            self.assertIn(token,impl)
        # No generic network drive capacity probe is introduced.
        self.assertNotIn("DRIVE_REMOTE",impl)
        self.assertNotIn("WNet",impl)

    def test_localized_visible_labels_and_no_phase5_resurrection(self):
        values=attr_values("MainWindow.xaml")|attr_values("FileToolbar.xaml")|attr_values("NavigationSidebar.xaml")
        for label in ("\ub4a4\ub85c","\uc55e\uc73c\ub85c","\uc0c1\uc704 \ud3f4\ub354",
                      "\ud604\uc7ac \ud3f4\ub354 \uac80\uc0c9","\ud648","\ub0b4 PC",
                      "\uc774\ub984","\uc720\ud615","\ud06c\uae30","\uc218\uc815 \ub0a0\uc9dc"):
            self.assertIn(label,values)
        joined="\n".join(text(n) for n in
            ("MainWindow.xaml","MainWindow.xaml.cpp","FileToolbar.xaml",
             "NavigationSidebar.xaml","ShellHeader.xaml"))
        for retired in ("phase5_island_bridge","phase5_winui3",
                        "FlyExplorerIslandBridge","FLYEXP_PHASE5_"):
            self.assertNotIn(retired,joined)

if __name__=="__main__":
    unittest.main()
