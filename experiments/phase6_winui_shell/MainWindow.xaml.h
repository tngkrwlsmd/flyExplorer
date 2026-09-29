#pragma once
#include "MainWindow.g.h"
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
        void OnNewTabClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnCloseTabClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnSplitClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnActivateLeft(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnActivateRight(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnHomeClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDocumentsClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnDownloadsClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnThisPCClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnThemeSelectionChanged(IInspectable const&,
            Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
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

    private:
        fxfile::explorerui::Model mModel;
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
        void FillFiles(int side);
        bool OpenFolder(std::wstring const& path);
        void ActivatePane(int side);
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
