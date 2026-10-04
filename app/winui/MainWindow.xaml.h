#pragma once
#include "MainWindow.g.h"
#include "ShellHeader.xaml.h"
#include "NavigationSidebar.xaml.h"
#include "FileToolbar.xaml.h"
#include "StatusFooter.xaml.h"
#include "file_list_state.h"
#include "window_workspace_controller.h"
#include "session_coordinator.h"
#include "shell_navigation_controller.h"
#include "file_operation_controller.h"
#include "file_detail_controller.h"
#include "preferences_coordinator.h"
#include "workspace_restore_coordinator.h"
#include "search_controller.h"
#include "../../src/base/shell_transfer_core.h"
#include "../../src/base/shell_clipboard_core.h"
#include "../../src/base/file_command_core.h"
#include "../../src/base/shell_navigation_core.h"
#include "../../src/base/explorer_ui_state.h"
#include "../../src/base/bookmark_store.h"
#include "../../src/base/filter_rule_store.h"
#include "../../src/base/search_preset_store.h"
#include "m19_workspace.h"
#include "m19_search.h"
#include <array>
#include <vector>
#include <filesystem>

namespace winrt::FlyExplorer::implementation
{
    struct MainWindow : MainWindowT<MainWindow>
    {
        MainWindow();
        ~MainWindow();
        int32_t MyProperty();
        void MyProperty(int32_t value);

        void OnBackClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnForwardClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnUpClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnAddressKeyDown(IInspectable const&, Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnAddressGotFocus(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnAddressLostFocus(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnAddressDisplayClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnBreadcrumbSegmentClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnQuickSearchKeyDown(IInspectable const&, Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnShellSizeChanged(IInspectable const&, Microsoft::UI::Xaml::SizeChangedEventArgs const&);
        void OnNewTabClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnCloseTabClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSplitClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnActivateLeft(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnActivateRight(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnHomeClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDocumentsClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDownloadsClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnThisPCClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void ApplyThemeChoice(int selection);
        void ExecuteFileCommand(fxfile::filecommand::Kind kind);
        void BeginFileNameCommand(fxfile::filecommand::Kind kind);
        void ToggleNameFilter(int side);
        void OnLeftTabSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnRightTabSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnLeftFileDoubleTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::DoubleTappedRoutedEventArgs const&);
        void OnRightFileDoubleTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::DoubleTappedRoutedEventArgs const&);
        void OnLeftPaneTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::TappedRoutedEventArgs const&);
        void OnRightPaneTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::TappedRoutedEventArgs const&);
        void OnLeftFileKeyDown(IInspectable const&,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnRightFileKeyDown(IInspectable const&,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnAddBookmark(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnToggleBookmarks(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnBookmarkSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnRenameBookmark(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDeleteBookmark(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnImportBookmarks(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnToggleFilterRules(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnFilterRuleSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnNewFilterRule(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSaveFilterRule(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnApplyFilterRule(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDeleteFilterRule(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnToggleWorkspaces(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSaveWorkspace(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnOpenWorkspace(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnToggleSearch(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnRunSearch(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSelectSearchRecent(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnClearSearchRecent(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSearchPresetSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnNewSearchPreset(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSaveSearchPreset(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnApplySearchPreset(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDeleteSearchPreset(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnCreateFolder(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnRenameSelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnWindowsCopy(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnWindowsCut(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnWindowsPaste(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnExternalWindowsContextMenu(IInspectable const&,
             Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSavePrivateSession(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnRestorePrivateSession(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnClearPrivateSession(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnCopySelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnMoveSelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnRecycleSelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnCancelTransfer(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnNameFilterChanged(
            IInspectable const&,
            Microsoft::UI::Xaml::Controls::TextChangedEventArgs const&);
        void OnLoadMoreFiles(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnNameColumnWidthChanged(
            IInspectable const&,
            Microsoft::UI::Xaml::Controls::Primitives::RangeBaseValueChangedEventArgs const&);
        void OnFileRightTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::RightTappedRoutedEventArgs const&);
        void OnFileSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnFileSelectionKeyUp(IInspectable const&,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnFileDragItemsStarting(IInspectable const&,
            Microsoft::UI::Xaml::Controls::DragItemsStartingEventArgs const&);
        void OnFileRowDragStarting(int side,
            Microsoft::UI::Xaml::UIElement const&,
            Microsoft::UI::Xaml::DragStartingEventArgs const&);
        void OnFileDragOver(IInspectable const&,
            Microsoft::UI::Xaml::DragEventArgs const&);
        winrt::fire_and_forget OnFileDrop(IInspectable const&,
            Microsoft::UI::Xaml::DragEventArgs const&);
        void RunTransfer(fxfile::shelltransfer::Kind);
        void UpdateSort(int selection);
        void UpdateView(int selection);
        void OnHeaderSortClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);

    private:
        fxfile::previewtabs::WindowWorkspaceController mWorkspace{};
        fxfile::sessioncoord::SessionCoordinator mSessionCoordinator{};
        fxfile::previewtabs::WindowTabState& ActiveWindowTab(){
            return mWorkspace.active();
        }
        fxfile::previewtabs::WindowTabState const& ActiveWindowTab() const{
            return mWorkspace.active();
        }
        bool CreateWindowTab(std::wstring const& startPath);
        bool ActivateWindowTab(std::size_t index);
        bool CloseWindowTab(std::size_t index);
        void SuspendActiveWindowTab();
        void ApplyActiveWindowTab(winrt::hstring const& status);
        void ReleaseWindowTabRoutes(fxfile::previewtabs::WindowTabState& state);
        void PrepareForClose() noexcept;
        void RefreshWindowTabs();
        std::wstring WindowTabLabel(fxfile::previewtabs::WindowTabState const&) const;
        fxfile::previewprefs::PreferencesCoordinator mPreferencesCoordinator{};
        fxfile::previewops::FileOperationController mFileOperations{};
        // Reusable XAML controls expose their inner primitives to the
        // existing M2.1 callers without coupling native state to views.
        winrt::FlyExplorer::implementation::FileToolbar* fileBar(){
            return winrt::get_self<implementation::FileToolbar>(ToolbarView());
        }
        winrt::FlyExplorer::implementation::StatusFooter* footer(){
            return winrt::get_self<implementation::StatusFooter>(FooterView());
        }
        Microsoft::UI::Xaml::Controls::TextBox FileNameBox(){
            return fileBar()->FileNameBox();
        }
        Microsoft::UI::Xaml::Controls::AppBarButton CreateFolderButton(){
            return fileBar()->CreateFolderButton();
        }
        Microsoft::UI::Xaml::Controls::AppBarButton RenameButton(){
            return fileBar()->RenameButton();
        }
        Microsoft::UI::Xaml::Controls::TextBlock StatusText(){
            return footer()->StatusText();
        }
        Microsoft::UI::Xaml::Controls::TextBlock ActivePaneText(){
            return footer()->ActivePaneText();
        }
        Microsoft::UI::Xaml::Controls::TextBlock ItemCountText(){
            return footer()->ItemCountText();
        }
        Microsoft::UI::Xaml::Controls::TextBlock SelectionCountText(){
            return footer()->SelectionCountText();
        }
        using FileDetail=fxfile::previewlist::FileDetail;
        using FileViewMode=fxfile::previewlist::FileViewMode;
        fxfile::previewdetail::FileDetailController mFileDetails{};
        void ScheduleFileDetails(int side,bool force=false);
        void ClearFileDetails(int side);
        Microsoft::UI::Dispatching::DispatcherQueueTimer mTransferTimer{nullptr};
        void InitializePrivateSession();
        void LoadPrivateSession();
        std::vector<std::wstring> mClipboardSources;
        std::wstring mClipboardParent;
        bool mClipboardMove=false;
        std::wstring mPrivateDragToken,mPrivateDragParent;
        std::vector<std::wstring> mPrivateDragSources;
        std::uint64_t mPrivateDragRoute=0;
        int mPrivateDragSide=-1;
        bool mDropReading=false;
        void HandleFileShortcut(int side,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args);
        void StartInternalPaste();
        bool CopySelectedToWindowsClipboard(int side,bool cut);
        void PasteFromWindowsClipboard();

        using FileOperationController=fxfile::previewops::FileOperationController;
        FileOperationController::Context FileOperationContext(int side) const;
        void SetFileButtonsBusy(bool busy,bool cancellable);
        void StartTransfer(fxfile::shelltransfer::Request request);
        void ApplyTransferStartStatus(
            FileOperationController::StartStatus status,std::size_t recycleCount=0);
        void OnTransferCompleted(FileOperationController::TransferCompletion completion);
        void OnFileCommandCompleted(FileOperationController::FileCommandCompletion completion);
        winrt::fire_and_forget ConfirmCollision();
        winrt::fire_and_forget ConfirmRecycle(std::size_t count);
        bool mPopulatingTabs = false;
        bool mSuppressWindowTabRefresh = false;
        bool mClosing = false;
        bool mPopulatingFileLists = false;
        void UpdateFooterSummary();
        void PersistPreferences();
        void UpdateSelectionChrome();
        void UpdateCommandAvailability();
        void QueueSelectionPresentationUpdate();
        std::unique_ptr<fxfile::previewnav::ShellNavigationController> mShellNavigation;
        bool mOwnedShellNotifyTest=false;
        bool mOwnedComExhaustOnVirtual=false;
        fxfile::previewrestore::WorkspaceRestoreCoordinator mWorkspaceRestore{};
        fxfile::bookmarks::Store mBookmarks{};
        bool mPopulatingBookmarks=false;
        void InitializeBookmarks();
        void RefreshBookmarks();
        void RefreshBookmarkManager(int selected);
        fxfile::filterrules::Store mFilterRules{};
        bool mPopulatingFilterRules=false;
        void InitializeFilterRules();
        void RefreshFilterRuleManager(int selected);
        fxfile::previewsearch::SearchController mSearchController{};
        fxfile::searchpresets::Store mSearchPresets{};
        bool mPopulatingRecents=false;
        bool mPopulatingSearchPresets=false;
        void InitializeSearchPresets();
        void RefreshSearchPresetManager(int selected);
        fxfile::searchpresets::Preset SearchPresetFromUi();
        void ApplySearchPresetToUi(fxfile::searchpresets::Preset const& value);
        void EnsureExpandedPanelFits();
        void InitializeM19();
        std::uint64_t QueuePath(int side,std::wstring path);
        void QueuePidl(int side,fxfile::shellnav::Location target,
                       fxfile::shellnav::NavigationAction action);
        void OnNativeResult(fxfile::shellnav::IsolatedResult result);
        void OnNativeChange(std::uint64_t route,std::uint64_t token);
        void UpdateWatch(int side,bool force=false);
        fxfile::shellnav::Session &Current();
        std::filesystem::path HomePath() const;
        void Refresh(winrt::hstring const& status = L"Ready");
        void RefreshTabs(int side);
        bool mColumnControlsReady=false;
        double mShellWidth=972.0;
        std::array<int,2> mDetailLayoutProfiles{{-1,-1}};
        int DetailLayoutProfile() const;
        std::array<Microsoft::UI::Xaml::GridLength,4> DetailColumnWidths(int side) const;
        void ApplyDetailColumnLayout(int side);
        void UpdateViewPresentation(int side);
        void UpdateSortPresentation(int side);
        void UpdateBreadcrumb(std::wstring const& address);
        void FillFiles(int side);
        bool OpenFolder(std::wstring const& path);
        void ActivatePane(int side);
        void UpdateActivePaneChrome();
        void OpenSelectedFolder(int side);
        void ApplyWorkspace(fxfile::preview::Workspace&&);
        void QueueNextWorkspaceTab(int side);
        using SearchController=fxfile::previewsearch::SearchController;
        SearchController::Context SearchContext();
        void RefreshRecentSearchOptions();
        void OnSearchCompleted(SearchController::Completion completion);
        bool WorkspaceModel(fxfile::preview::Workspace&,std::wstring& reason) const;
    };
}
namespace winrt::FlyExplorer::factory_implementation
{
    struct MainWindow : MainWindowT<MainWindow, implementation::MainWindow> {};
}
