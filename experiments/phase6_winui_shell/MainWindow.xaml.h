#pragma once
#include "MainWindow.g.h"
#include "ShellHeader.xaml.h"
#include "NavigationSidebar.xaml.h"
#include "FileToolbar.xaml.h"
#include "StatusFooter.xaml.h"
#include "file_list_state.h"
#include "../../src/base/shell_transfer_core.h"
#include "../../src/base/shell_clipboard_core.h"
#include "../../src/base/preview_preferences.h"
#include "../../src/base/preview_session.h"
#include "../../src/base/file_command_core.h"
#include <mutex>
#include "../../src/base/shell_navigation_core.h"
#include "../../src/base/explorer_ui_state.h"
#include "../../src/base/shell_async_worker.h"
#include "../../src/base/shell_isolated_supervisor.h"
#include "../../src/base/directory_watcher.h"
#include "../../src/base/shell_namespace_watcher.h"
#include "m19_workspace.h"
#include "m19_search.h"
#include <atomic>
#include <deque>
#include <array>
#include <vector>
#include <filesystem>

namespace winrt::FlyExplorerWinUIShell::implementation
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
        void OnLeftTabSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnRightTabSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnLeftFileDoubleTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::DoubleTappedRoutedEventArgs const&);
        void OnRightFileDoubleTapped(IInspectable const&,
            Microsoft::UI::Xaml::Input::DoubleTappedRoutedEventArgs const&);
        void OnLeftFileKeyDown(IInspectable const&,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnRightFileKeyDown(IInspectable const&,
            Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
        void OnToggleWorkspaces(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSaveWorkspace(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnOpenWorkspace(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnToggleSearch(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnRunSearch(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSelectSearchRecent(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
        void OnClearSearchRecent(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
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

    private:
        fxfile::explorerui::Model mModel;
        fxfile::previewsettings::Preferences mPreferences{};
        std::shared_ptr<std::mutex> mPreferencesWriteMutex=
            std::make_shared<std::mutex>();
        std::shared_ptr<std::atomic_uint64_t> mPreferencesRevision=
            std::make_shared<std::atomic_uint64_t>(0);
        bool mFileOperationPending=false;
        std::uint64_t mFileOperationEpoch=0;
        // Reusable XAML controls expose their inner primitives to the
        // existing M2.1 callers without coupling native state to views.
        winrt::FlyExplorerWinUIShell::implementation::FileToolbar* fileBar(){
            return winrt::get_self<implementation::FileToolbar>(ToolbarView());
        }
        winrt::FlyExplorerWinUIShell::implementation::StatusFooter* footer(){
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
        using FileDetail=fxfile::previewlist::FileDetail;
        std::array<fxfile::previewlist::PaneState,2> mFileLists{};
        // Incremental thumbnail requests must stop issuing new child
        // Shell processes when navigation invalidates the native route.
        std::array<std::shared_ptr<std::atomic_bool>,2> mDetailCancel{};
        void ScheduleFileDetails(int side,bool force=false);
        void ClearFileDetails(int side);
        std::shared_ptr<fxfile::shelltransfer::Progress> mTransferProgress;
        Microsoft::UI::Dispatching::DispatcherQueueTimer mTransferTimer{nullptr};
        std::uint64_t mTransferEpoch=0;
        std::uint64_t mSessionEpoch=0;
        std::shared_ptr<std::mutex> mSessionMutation=
            std::make_shared<std::mutex>();
        std::shared_ptr<std::atomic_uint64_t> mSessionRevision=
            std::make_shared<std::atomic_uint64_t>(0);
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

        void SetFileButtonsBusy(bool busy,bool cancellable);
        void StartTransfer(fxfile::shelltransfer::Request request);
        winrt::fire_and_forget ConfirmCollision(fxfile::shelltransfer::Request request);
        winrt::fire_and_forget ConfirmRecycle(fxfile::shelltransfer::Request request);
        bool mPopulatingTabs = false;
        std::unique_ptr<fxfile::shellnav::IsolatedShellSupervisor> mSupervisor;
        std::unique_ptr<fxfile::directorychange::DirectoryWatcher> mWatcher;
        std::unique_ptr<fxfile::directorychange::ShellNamespaceWatcher> mShellWatcher;
        bool mOwnedShellNotifyTest=false;
        bool mOwnedComExhaustOnVirtual=false;
        std::array<std::deque<std::pair<size_t,std::wstring>>,2> mRestoreQueue{};
        std::vector<std::wstring> mRecentScopes;
        std::shared_ptr<std::atomic_bool> mSearchCancel;
        std::uint64_t mSearchEpoch=0;
        bool mPopulatingRecents=false;
        bool mRecentEdited=false;
        void EnsureExpandedPanelFits();
        void InitializeM19();
        std::uint64_t mNextWatchToken=1;
        std::array<std::uint64_t,2> mWatchedRoutes{},mWatchTokens{};
        std::array<std::wstring,2> mWatchedPaths{};
        void QueuePath(int side,std::wstring path);
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
        void FillFiles(int side);
        bool OpenFolder(std::wstring const& path);
        void ActivatePane(int side);
        void UpdateActivePaneChrome();
        void OpenSelectedFolder(int side);
        void ApplyWorkspace(fxfile::preview::Workspace&&);
        void QueueNextWorkspaceTab(int side);
        void RefreshRecentSearchOptions();
        void OnSearchCompleted(fxfile::preview::SearchResults&&,
                               std::wstring const& scope,bool remember);
        bool WorkspaceModel(fxfile::preview::Workspace&,std::wstring& reason) const;
    };
}
namespace winrt::FlyExplorerWinUIShell::factory_implementation
{
    struct MainWindow : MainWindowT<MainWindow, implementation::MainWindow> {};
}
