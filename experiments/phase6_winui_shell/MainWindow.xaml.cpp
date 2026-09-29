#include "pch.h"
#include "MainWindow.xaml.h"
#if __has_include("MainWindow.g.cpp")
#include "MainWindow.g.cpp"
#endif
#include <shellapi.h>
#include "../../src/fxfile/file_operation_core.h"
#include <algorithm>
#include <cwchar>
#include <system_error>
#include <winrt/Windows.System.h>
#include <winrt/Microsoft.UI.Xaml.Input.h>
#pragma comment(lib, "shell32.lib")

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace {
    std::filesystem::path StartFolder()
    {
        int count=0;
        auto argv=::CommandLineToArgvW(::GetCommandLineW(),&count);
        std::filesystem::path result=std::filesystem::current_path();
        if (argv) {
            if (count>1 && argv[1][0]!=L'-')
                result=std::filesystem::path(argv[1]);
            ::LocalFree(argv);
        }
        return result;
    }

}

namespace winrt::FlyExplorerWinUIShell::implementation
{
    MainWindow::MainWindow()
    {
        InitializeComponent();
        const auto dispatch=DispatcherQueue();
        const auto weak=get_weak();
        // The worker owns NO MainWindow/WinRT UI object. Cross-apartment
        // notifications carry only owned native value snapshots/PIDLs and
        // enter the XAML thread through its actual DispatcherQueue.
        mSupervisor=std::make_unique<fxfile::shellnav::IsolatedShellSupervisor>(
            [weak,dispatch](fxfile::shellnav::IsolatedResult answer) {
                auto envelope=std::make_shared<fxfile::shellnav::IsolatedResult>(
                    std::move(answer));
                dispatch.TryEnqueue([weak,envelope] {
                    if(auto ui=weak.get())
                        ui->OnNativeResult(std::move(*envelope));
                });
            });
        mWatcher=std::make_unique<fxfile::directorychange::DirectoryWatcher>(
            [weak,dispatch](std::uint64_t route,std::uint64_t token) {
                dispatch.TryEnqueue([weak,route,token] {
                    if(auto ui=weak.get())ui->OnNativeChange(route,token);
                });
            });
        mShellWatcher=std::make_unique<
            fxfile::directorychange::ShellNamespaceWatcher>(
            [weak,dispatch](std::uint64_t route,std::uint64_t token) {
                dispatch.TryEnqueue([weak,route,token] {
                    if(auto ui=weak.get())ui->OnNativeChange(route,token);
                });
            });
        // Exact sibling of THIS preview binary, never a PATH lookup or
        // arbitrary installed product/Explorer process.
        wchar_t module[32768]{};
        const DWORD chars=::GetModuleFileNameW(nullptr,module,
             static_cast<DWORD>(std::size(module)));
        if(!chars || chars>=std::size(module))
            throw winrt::hresult_error(E_FAIL,L"Own preview EXE path unavailable");
        std::wstring helper(module,chars);
        const auto last=helper.find_last_of(L"\\/");
        if(last==std::wstring::npos)
            throw winrt::hresult_error(E_FAIL,L"Invalid preview EXE path");
        helper.resize(last+1);
        helper+=L"FlyShellIsolationHelper.exe";
        if(!mSupervisor->start(std::move(helper)))
            throw winrt::hresult_error(E_FAIL,L"Owned Shell helper startup failed");
        if(!mWatcher->start())
            throw winrt::hresult_error(E_FAIL,L"Independent native watcher startup failed");
        if(!mShellWatcher->start())
            throw winrt::hresult_error(E_FAIL,L"Shell namespace watcher startup failed");
        const auto initial=StartFolder().native();
        bool testLeftDelay=false;
        bool testLeftComDelay=false;
#if defined(_DEBUG)
        wchar_t notifyFlag[8]{};
        if(::GetEnvironmentVariableW(
             L"FLY_M18_OWNED_SHELL_NOTIFY",notifyFlag,8)==3 &&
             !wcscmp(notifyFlag,L"YES")){
            int argc=0;
            auto argv=::CommandLineToArgvW(::GetCommandLineW(),&argc);
            if(argv){
                for(int i=2;i<argc;++i)
                    if(!wcscmp(argv[i],L"--m18-owned-shell-notification"))
                        mOwnedShellNotifyTest=true;
                ::LocalFree(argv);
            }
        }
#endif
#if defined(_DEBUG)
        // Only a user-owned isolated test process explicitly opting in
        // can inject a synthetic slow helper. No UI path string triggers it.
        wchar_t ownedFlag[8]{};
        if(::GetEnvironmentVariableW(
             L"FLY_M16_OWNED_TEST_ONLY",ownedFlag,8)==3 &&
             !wcscmp(ownedFlag,L"YES")){
            int argc=0;
            auto argv=::CommandLineToArgvW(::GetCommandLineW(),&argc);
            if(argv){
                for(int i=2;i<argc;++i)
                    if(!wcscmp(argv[i],L"--m17-test-left-helper-hang"))
                        testLeftDelay=true;
                ::LocalFree(argv);
            }
        }
        wchar_t comFlag[8]{};
        if(::GetEnvironmentVariableW(
             L"FLY_M18_OWNED_COM_TEST_ONLY",comFlag,8)==3 &&
             !wcscmp(comFlag,L"YES")){
            int argc=0;
            auto argv=::CommandLineToArgvW(::GetCommandLineW(),&argc);
            if(argv){
                for(int i=2;i<argc;++i) {
                    if(!wcscmp(argv[i],L"--m18-test-left-com-hang"))
                        testLeftComDelay=true;
                    if(!wcscmp(argv[i],L"--m18-test-exhaust-com-on-virtual"))
                        mOwnedComExhaustOnVirtual=true;
                }
                ::LocalFree(argv);
            }
        }
#endif
        for(int side=0;side!=2;++side) {
            auto& pane=mModel.panes[side];
#if defined(_DEBUG)
            if(side==0 && testLeftDelay){
                pane.pending[0]=mSupervisor->submitOwnedTestDelay(
                    0,pane.routeIds[0],initial);
                continue;
            }
            if(side==0 && testLeftComDelay){
                pane.pending[0]=mSupervisor->submitOwnedComDelay(
                    0,pane.routeIds[0],initial);
                continue;
            }
#endif
            QueuePath(side,initial);
        }
        const bool nativeCoreLinked =
            fxfile::fileop::execute(nullptr)==ERROR_INVALID_PARAMETER;
        Refresh(nativeCoreLinked?
            L"Native Shell engine active: async STA loading; file mutations disabled":
            L"Native file-operation null contract FAILED");
        InitializeM19();
    }
    MainWindow::~MainWindow()
    {
        // Never join a Shell extension which might be blocked in COM.
        // Detached State owns all native handles. UI work is guarded
        // by get_weak(), route tokens, and closed DispatcherQueue.
        if(mSupervisor)mSupervisor->shutdown();
        if(mWatcher)mWatcher->shutdown();
        if(mShellWatcher)mShellWatcher->shutdown();
        if(mSearchCancel)mSearchCancel->store(true);
    }
    int32_t MainWindow::MyProperty() {return 0;}
    void MainWindow::MyProperty(int32_t) {}
    fxfile::shellnav::Session& MainWindow::Current()
    {
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        return pane.tabs.at(pane.active);
    }
    std::filesystem::path MainWindow::HomePath() const
    {
        wchar_t buffer[32768]={0};
        const auto len=::GetEnvironmentVariableW(L"USERPROFILE",buffer,32768);
        if (len && len<32768)
            return std::filesystem::path(buffer);
        return StartFolder();
    }
    void MainWindow::QueuePath(int side,std::wstring path)
    {
        auto& pane=mModel.panes[side];
        const auto route=pane.routeIds[pane.active];
        std::uint64_t id=0;
#if defined(_DEBUG)
        if(mOwnedComExhaustOnVirtual && side==0 &&
           path==L"shell:MyComputerFolder")
            id=mSupervisor->submitOwnedComDelay(
                side,route,std::move(path),true);
        else
#endif
            id=mSupervisor->submitParsing(side,route,std::move(path));
        if(id) {
            // At most one outstanding helper operation per active pane.
            // Clear the canceled prior tab's UI pending marker too.
            mModel.markPending(side,pane.active,id,true);
            StatusText().Text(L"Native Shell engine active: async STA loading");
        } else StatusText().Text(L"Shell worker could not queue location");
    }
    void MainWindow::QueuePidl(
        int side,fxfile::shellnav::Location target,
        fxfile::shellnav::NavigationAction action)
    {
        if(!target.valid()) {
            StatusText().Text(L"No Shell location for this command");
            return;
        }
        auto& pane=mModel.panes[side];
        const auto id=mSupervisor->submit(
            side,pane.routeIds[pane.active],std::move(target),action);
        if(id) {
            // At most one outstanding helper operation per active pane.
            // Clear the canceled prior tab's UI pending marker too.
            mModel.markPending(side,pane.active,id,true);
            StatusText().Text(L"Native Shell engine active: async STA loading");
        } else StatusText().Text(L"Shell worker could not queue request");
    }
    void MainWindow::UpdateWatch(int side,bool force)
    {
        auto& pane=mModel.panes[side];
        const auto route=pane.routeIds[pane.active];
        // This path is computed by the disposable Shell helper and passed
        // as a bounded wire value. No SHGetPathFromIDListEx on WinUI STA.
        const std::wstring path=(side==0 || mModel.split)?
            pane.filesystemPaths[pane.active]:std::wstring{};
        if(!force && route==mWatchedRoutes[side] &&
           path==mWatchedPaths[side])return;
        if(mWatchedRoutes[side]){
            mWatcher->unwatch(mWatchedRoutes[side]);
            mShellWatcher->unwatch(mWatchedRoutes[side]);
        }
        mWatchedRoutes[side]=0;
        mWatchTokens[side]=0;
        mWatchedPaths[side].clear();
        const auto& location=pane.tabs[pane.active].snapshot().folder;
        if(!path.empty() || location.valid()) {
            const auto token=mNextWatchToken++;
            if(!path.empty() && !(mOwnedShellNotifyTest && side==0))
                mWatcher->watch(route,token,path);
            else if(location.valid())
                mShellWatcher->watch(route,token,location.get());
            mWatchedRoutes[side]=route;
            mWatchTokens[side]=token;
            mWatchedPaths[side]=std::move(path);
        }
    }
    void MainWindow::OnNativeResult(fxfile::shellnav::IsolatedResult result)
    {
        for(int side=0;side!=2;++side) {
            auto& pane=mModel.panes[side];
            for(size_t i=0;i<pane.routeIds.size();++i) {
                if(pane.routeIds[i]!=result.route ||
                   pane.pending[i]!=result.request)continue;
                if(!mModel.completeRequest(side,i,result.route,
                                           result.request))continue;
                if(FAILED(result.hr)) {
                    if(i==pane.active) {
                        if(result.timedOut)
                            StatusText().Text(
                                L"Shell folder did not respond after two 4.5-second attempts. "
                                L"Previous folder preserved; retry or choose another folder.");
                        else if(result.networkRequest)
                            StatusText().Text(
                                L"Network folder unavailable or access denied. "
                                L"Previous folder preserved.");
                        else
                            StatusText().Text(
                                L"Shell folder could not be opened. "
                                L"Previous folder preserved.");
                    }
                    return;
                }
                using Action=fxfile::shellnav::NavigationAction;
                using History=fxfile::shellnav::HistoryAction;
                auto action=History::Open;
                if(result.action==Action::Back)action=History::Back;
                if(result.action==Action::Forward)action=History::Forward;
                if(result.action==Action::Up)action=History::Up;
                if(result.action==Action::Refresh)action=History::Refresh;
                const auto applied=pane.tabs[i].accept(
                    std::move(result.snapshot),action);
                if(applied==S_OK) {
                    pane.filesystemPaths[i]=std::move(result.filesystemPath);
                    if(i==pane.active) {
                        Refresh(result.recovered?
                            L"Native Shell helper recovered from owned timeout":
                            result.action==Action::Refresh?
                            L"Native Shell helper: folder change notifications refreshed":
                            L"Native Shell helper: isolated folder loaded");
                        UpdateWatch(side,true);
                    }else RefreshTabs(side);
                    QueueNextWorkspaceTab(side);
                }else if(FAILED(applied)) {
                    StatusText().Text(L"Stale Shell history result rejected");
                }
                return;
            }
        }
    }
    void MainWindow::OnNativeChange(std::uint64_t route,std::uint64_t token)
    {
        for(int side=0;side!=2;++side) {
            if(route!=mWatchedRoutes[side] ||
               token!=mWatchTokens[side])continue;
            auto& pane=mModel.panes[side];
            if(pane.routeIds[pane.active]!=route ||
               pane.pending[pane.active])return;
            QueuePidl(side,pane.tabs[pane.active].target(
                fxfile::shellnav::HistoryAction::Refresh),
                fxfile::shellnav::NavigationAction::Refresh);
            return;
        }
    }
    void MainWindow::RefreshTabs(int side)
    {
        auto view=side==0?LeftTabs():RightTabs();
        const auto& pane=mModel.panes[static_cast<size_t>(side)];
        mPopulatingTabs=true;
        view.TabItems().Clear();
        for (const auto& tab : pane.tabs) {
            TabViewItem item;
            const auto& folder=tab.snapshot();
            item.Header(winrt::box_value(hstring(
                folder.displayName.empty()?folder.parsingName:folder.displayName)));
            item.IsClosable(false); // explicit shared Close tab action
            view.TabItems().Append(item);
        }
        view.SelectedIndex(static_cast<int32_t>(pane.active));
        mPopulatingTabs=false;
    }
    void MainWindow::FillFiles(int side)
    {
        auto view=side==0?LeftFiles():RightFiles();
        view.Items().Clear();
        const auto& pane=mModel.panes[static_cast<size_t>(side)];
        const auto& items=pane.tabs[pane.active].snapshot().children;
        // Keep each ListViewItem's Tag as the index into the owning
        // per-tab Shell snapshot. Opening folders uses its FULL PIDL,
        // not an unsafe or ambiguous virtual-folder display string.
        std::vector<size_t> order;
        order.reserve(items.size());
        for(size_t i=0;i<items.size();++i)order.push_back(i);
        std::sort(order.begin(),order.end(),[&](size_t a,size_t b) {
            if(items[a].isFolder()!=items[b].isFolder())
                return items[a].isFolder();
            return items[a].label<items[b].label;
        });
        for(const size_t i:order) {
            const auto& entry=items[i];
            ListViewItem row;
            row.Content(winrt::box_value(hstring(
                std::wstring(entry.isFolder()?L"[Folder]  ":L"[File]  ")+
                entry.label)));
            if(entry.isFolder())
                row.Tag(winrt::box_value(static_cast<uint32_t>(i)));
            view.Items().Append(row);
        }
    }
    void MainWindow::Refresh(hstring const& status)
    {
        RefreshTabs(0);
        RefreshTabs(1);
        FillFiles(0);
        FillFiles(1);
        auto& nav=Current();
        AddressBox().Text(hstring(nav.snapshot().parsingName));
        BackButton().IsEnabled(nav.canBack() && !mModel.panes[mModel.activePane].pending[mModel.panes[mModel.activePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !mModel.panes[mModel.activePane].pending[mModel.panes[mModel.activePane].active]);
        UpButton().IsEnabled(nav.snapshot().folder.valid() && !ILIsEmpty(nav.snapshot().folder.get()));
        ActivePaneText().Text(mModel.activePane==0?L"Active: Left":L"Active: Right");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(mModel.activePane==0?L"Left pane (active)":L"Left pane")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(mModel.activePane==1?L"Right pane (active)":L"Right pane")));
        StatusText().Text(status);
        Title(L"flyExplorer - WinUI 3 migration preview - "+
            hstring(nav.snapshot().displayName));
        UpdateWatch(0);
        UpdateWatch(1);
    }
    bool MainWindow::OpenFolder(std::wstring const& path)
    {
        if(path.empty())return false;
        mRestoreQueue[static_cast<size_t>(mModel.activePane)].clear();
        QueuePath(mModel.activePane,path);
        return true;
    }
    void MainWindow::ActivatePane(int side)
    {
        if(!mModel.dispatch(fxfile::explorerui::Command::ActivatePane,side)
                    .accepted)return;
        const auto& nav=Current();
        AddressBox().Text(hstring(nav.snapshot().parsingName));
        BackButton().IsEnabled(nav.canBack() && !mModel.panes[mModel.activePane].pending[mModel.panes[mModel.activePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !mModel.panes[mModel.activePane].pending[mModel.panes[mModel.activePane].active]);
        UpButton().IsEnabled(nav.snapshot().folder.valid() && !ILIsEmpty(nav.snapshot().folder.get()));
        ActivePaneText().Text(side==0?L"Active: Left":L"Active: Right");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(side==0?L"Left pane (active)":L"Left pane")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(side==1?L"Right pane (active)":L"Right pane")));
        Title(L"flyExplorer - WinUI 3 migration preview - "+
              hstring(nav.snapshot().displayName));
    }
    void MainWindow::OnBackClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canBack()) {
            StatusText().Text(L"No previous folder in this tab");return;
        }
        QueuePidl(mModel.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Back),
            fxfile::shellnav::NavigationAction::Back);
    }
    void MainWindow::OnForwardClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canForward()) {
            StatusText().Text(L"No next folder in this tab");return;
        }
        QueuePidl(mModel.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Forward),
            fxfile::shellnav::NavigationAction::Forward);
    }
    void MainWindow::OnUpClicked(IInspectable const&,RoutedEventArgs const&)
    {
        QueuePidl(mModel.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Up),
            fxfile::shellnav::NavigationAction::Up);
    }
    void MainWindow::OnAddressKeyDown(IInspectable const&,
                                     Input::KeyRoutedEventArgs const& args)
    {
        if (args.Key()==Windows::System::VirtualKey::Enter) {
            OpenFolder(std::wstring(AddressBox().Text().c_str()));
            args.Handled(true);
        }
        else if (args.Key()==Windows::System::VirtualKey::Escape) {
            AddressBox().Text(hstring(Current().snapshot().parsingName));
            StatusText().Text(L"Address edit canceled");
            args.Handled(true);
        }
    }
    void MainWindow::OnNewTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        if (pane.tabs.size()>=32) {
            StatusText().Text(L"Maximum of 32 tabs per pane in preview");
            return;
        }
        fxfile::shellnav::Location start(
            pane.tabs[pane.active].snapshot().folder);
        if(!start.valid()) {
            StatusText().Text(L"Wait for the initial Shell folder first");
            return;
        }
        if(!mModel.dispatch(fxfile::explorerui::Command::AddTab,
                            mModel.activePane).accepted)return;
        QueuePidl(mModel.activePane,std::move(start),
                  fxfile::shellnav::NavigationAction::Open);
        Refresh(L"Native Shell engine active: new tab loading asynchronously");
    }
    void MainWindow::OnCloseTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        if (pane.tabs.size()<=1) {
            StatusText().Text(L"Keep at least one tab in each pane");
            return;
        }
        const auto change=mModel.dispatch(
            fxfile::explorerui::Command::CloseTab,mModel.activePane);
        if(!change.accepted)return;
        mSupervisor->forget(change.releasedRoute);
        mWatcher->unwatch(change.releasedRoute);
        mShellWatcher->unwatch(change.releasedRoute);
        mRestoreQueue[static_cast<size_t>(mModel.activePane)].clear();
        Refresh(L"Tab closed");
    }
    void MainWindow::OnSplitClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!mModel.dispatch(fxfile::explorerui::Command::ToggleSplit)
                  .accepted)return;
        SecondaryPane().Visibility(mModel.split?Visibility::Visible:Visibility::Collapsed);
        PaneDivider().Visibility(mModel.split?Visibility::Visible:Visibility::Collapsed);
        SecondaryColumn().Width(mModel.split?
            GridLength{1.0,GridUnitType::Star}:GridLength{0.0,GridUnitType::Pixel});
        SplitButton().Content(winrt::box_value(
            hstring(mModel.split?L"Single pane":L"Split panes")));
        Refresh(mModel.split?L"Two independent panes":L"Single pane; other state retained");
    }
    void MainWindow::OnActivateLeft(IInspectable const&,RoutedEventArgs const&)
    {
        ActivatePane(0);
        StatusText().Text(L"Left pane selected");
    }
    void MainWindow::OnActivateRight(IInspectable const&,RoutedEventArgs const&)
    {
        ActivatePane(1);
        StatusText().Text(L"Right pane selected");
    }
    void MainWindow::OnHomeClicked(IInspectable const&,RoutedEventArgs const&)
    {
        OpenFolder(HomePath().native());
    }
    void MainWindow::OnDocumentsClicked(IInspectable const&,RoutedEventArgs const&)
    {
        OpenFolder((HomePath()/L"Documents").native());
    }
    void MainWindow::OnDownloadsClicked(IInspectable const&,RoutedEventArgs const&)
    {
        OpenFolder((HomePath()/L"Downloads").native());
    }
    void MainWindow::OnLeftTabSelectionChanged(
        IInspectable const& sender,SelectionChangedEventArgs const&)
    {
        auto view=sender.as<TabView>();
        if (mPopulatingTabs || view.SelectedIndex()<0) return;
        auto& pane=mModel.panes[0];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        // WinUI raises deferred SelectionChanged for programmatic strip
        // rebuilds. Only a DIFFERENT selected tab is user navigation.
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        if(!mModel.dispatch(fxfile::explorerui::Command::SelectTab,0,
                 static_cast<size_t>(view.SelectedIndex())).accepted)return;
        Refresh(L"Left tab selected");
    }
    void MainWindow::OnRightTabSelectionChanged(
        IInspectable const& sender,SelectionChangedEventArgs const&)
    {
        auto view=sender.as<TabView>();
        if (mPopulatingTabs || view.SelectedIndex()<0 || !mModel.split)return;
        auto& pane=mModel.panes[1];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        if(!mModel.dispatch(fxfile::explorerui::Command::SelectTab,1,
                 static_cast<size_t>(view.SelectedIndex())).accepted)return;
        Refresh(L"Right tab selected");
    }
    void MainWindow::OpenSelectedFolder(int side)
    {
        ActivatePane(side);
        auto view=side==0?LeftFiles():RightFiles();
        const auto picked=view.SelectedItem();
        if(!picked)return;
        const auto row=picked.try_as<ListViewItem>();
        if(!row || !row.Tag())return;
        const auto index=winrt::unbox_value<uint32_t>(row.Tag());
        auto& session=Current();
        const auto& entries=session.snapshot().children;
        if(index>=entries.size() || !entries[index].isFolder())return;
        // The native engine CLONES this original absolute Shell PIDL
        // before updating session state; no dangling shell pointers.
        QueuePidl(side,fxfile::shellnav::Location(entries[index].id),
                  fxfile::shellnav::NavigationAction::Open);
    }
    void MainWindow::OnLeftFileDoubleTapped(
        IInspectable const&,Input::DoubleTappedRoutedEventArgs const&)
    {OpenSelectedFolder(0);}
    void MainWindow::OnRightFileDoubleTapped(
        IInspectable const&,Input::DoubleTappedRoutedEventArgs const&)
    {OpenSelectedFolder(1);}
    void MainWindow::OnLeftFileKeyDown(
        IInspectable const&,Input::KeyRoutedEventArgs const& a)
    {
        if (a.Key()==Windows::System::VirtualKey::Enter) {
            OpenSelectedFolder(0);a.Handled(true);
        }
    }
    void MainWindow::OnRightFileKeyDown(
        IInspectable const&,Input::KeyRoutedEventArgs const& a)
    {
        if (a.Key()==Windows::System::VirtualKey::Enter) {
            OpenSelectedFolder(1);a.Handled(true);
        }
    }
}
