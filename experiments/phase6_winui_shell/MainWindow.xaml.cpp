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
        mWorker=std::make_unique<fxfile::shellnav::AsyncShellWorker>(
            [weak,dispatch](fxfile::shellnav::AsyncResult answer) {
                auto envelope=std::make_shared<fxfile::shellnav::AsyncResult>(
                    std::move(answer));
                dispatch.TryEnqueue([weak,envelope] {
                    if(auto ui=weak.get())
                        ui->OnNativeResult(std::move(*envelope));
                });
            },
            [weak,dispatch](std::uint64_t route,std::uint64_t token) {
                dispatch.TryEnqueue([weak,route,token] {
                    if(auto ui=weak.get())ui->OnNativeChange(route,token);
                });
            });
        if(!mWorker->start())
            throw winrt::hresult_error(E_FAIL,L"Native Shell STA startup failed");
        const auto initial=StartFolder().native();
        for(int side=0;side!=2;++side) {
            auto& pane=mPanes[side];
            pane.tabs.emplace_back();
            pane.routeIds.push_back(mNextRoute++);
            pane.pending.push_back(0);
            QueuePath(side,initial);
        }
        const bool nativeCoreLinked =
            fxfile::fileop::execute(nullptr)==ERROR_INVALID_PARAMETER;
        Refresh(nativeCoreLinked?
            L"Native Shell engine active: async STA loading; file mutations disabled":
            L"Native file-operation null contract FAILED");
    }
    MainWindow::~MainWindow()
    {
        // Never join a Shell extension which might be blocked in COM.
        // Detached State owns all native handles. UI work is guarded
        // by get_weak(), route tokens, and closed DispatcherQueue.
        if(mWorker)mWorker->shutdown();
    }
    int32_t MainWindow::MyProperty() {return 0;}
    void MainWindow::MyProperty(int32_t) {}
    fxfile::shellnav::Session& MainWindow::Current()
    {
        auto& pane=mPanes[static_cast<size_t>(mActivePane)];
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
        auto& pane=mPanes[side];
        const auto route=pane.routeIds[pane.active];
        const auto id=mWorker->submitParsing(route,std::move(path));
        if(id) {
            pane.pending[pane.active]=id;
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
        auto& pane=mPanes[side];
        const auto id=mWorker->submit(
            pane.routeIds[pane.active],std::move(target),action);
        if(id) {
            pane.pending[pane.active]=id;
            StatusText().Text(L"Native Shell engine active: async STA loading");
        } else StatusText().Text(L"Shell worker could not queue request");
    }
    void MainWindow::UpdateWatch(int side,bool force)
    {
        auto& pane=mPanes[side];
        const auto route=pane.routeIds[pane.active];
        std::wstring path;
        if((side==0 || mSplit) &&
           pane.tabs[pane.active].snapshot().folder.valid()) {
            wchar_t buffer[32768]={};
            if(::SHGetPathFromIDListEx(
                 pane.tabs[pane.active].snapshot().folder.get(),
                 buffer,static_cast<DWORD>(std::size(buffer)),0))
                path=buffer;
        }
        if(!force && route==mWatchedRoutes[side] &&
           path==mWatchedPaths[side])return;
        if(mWatchedRoutes[side])
            mWorker->unwatch(mWatchedRoutes[side]);
        mWatchedRoutes[side]=0;
        mWatchTokens[side]=0;
        mWatchedPaths[side].clear();
        if(!path.empty()) {
            const auto token=mNextWatchToken++;
            mWorker->watch(route,token,path);
            mWatchedRoutes[side]=route;
            mWatchTokens[side]=token;
            mWatchedPaths[side]=std::move(path);
        }
    }
    void MainWindow::OnNativeResult(fxfile::shellnav::AsyncResult result)
    {
        for(int side=0;side!=2;++side) {
            auto& pane=mPanes[side];
            for(size_t i=0;i<pane.routeIds.size();++i) {
                if(pane.routeIds[i]!=result.route ||
                   pane.pending[i]!=result.request)continue;
                pane.pending[i]=0;
                if(FAILED(result.hr)) {
                    if(i==pane.active)
                        StatusText().Text(L"Shell operation failed; old folder preserved");
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
                    if(i==pane.active) {
                        Refresh(result.action==Action::Refresh?
                            L"Native Shell engine active: changes refreshed asynchronously":
                            L"Native Shell engine active: async folder loaded");
                        UpdateWatch(side,true);
                    }else RefreshTabs(side);
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
            auto& pane=mPanes[side];
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
        const auto& pane=mPanes[static_cast<size_t>(side)];
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
        const auto& pane=mPanes[static_cast<size_t>(side)];
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
        BackButton().IsEnabled(nav.canBack() && !mPanes[mActivePane].pending[mPanes[mActivePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !mPanes[mActivePane].pending[mPanes[mActivePane].active]);
        UpButton().IsEnabled(nav.snapshot().folder.valid() && !ILIsEmpty(nav.snapshot().folder.get()));
        ActivePaneText().Text(mActivePane==0?L"Active: Left":L"Active: Right");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(mActivePane==0?L"Left pane (active)":L"Left pane")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(mActivePane==1?L"Right pane (active)":L"Right pane")));
        StatusText().Text(status);
        Title(L"flyExplorer - WinUI 3 migration preview - "+
            hstring(nav.snapshot().displayName));
        UpdateWatch(0);
        UpdateWatch(1);
    }
    bool MainWindow::OpenFolder(std::wstring const& path)
    {
        if(path.empty())return false;
        QueuePath(mActivePane,path);
        return true;
    }
    void MainWindow::ActivatePane(int side)
    {
        if (side==1 && !mSplit) return;
        mActivePane=side;
        const auto& nav=Current();
        AddressBox().Text(hstring(nav.snapshot().parsingName));
        BackButton().IsEnabled(nav.canBack() && !mPanes[mActivePane].pending[mPanes[mActivePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !mPanes[mActivePane].pending[mPanes[mActivePane].active]);
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
        QueuePidl(mActivePane,Current().target(
            fxfile::shellnav::HistoryAction::Back),
            fxfile::shellnav::NavigationAction::Back);
    }
    void MainWindow::OnForwardClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canForward()) {
            StatusText().Text(L"No next folder in this tab");return;
        }
        QueuePidl(mActivePane,Current().target(
            fxfile::shellnav::HistoryAction::Forward),
            fxfile::shellnav::NavigationAction::Forward);
    }
    void MainWindow::OnUpClicked(IInspectable const&,RoutedEventArgs const&)
    {
        QueuePidl(mActivePane,Current().target(
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
        auto& pane=mPanes[static_cast<size_t>(mActivePane)];
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
        pane.tabs.emplace_back();
        pane.routeIds.push_back(mNextRoute++);
        pane.pending.push_back(0);
        pane.active=pane.tabs.size()-1;
        QueuePidl(mActivePane,std::move(start),
                  fxfile::shellnav::NavigationAction::Open);
        Refresh(L"Native Shell engine active: new tab loading asynchronously");
    }
    void MainWindow::OnCloseTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=mPanes[static_cast<size_t>(mActivePane)];
        if (pane.tabs.size()<=1) {
            StatusText().Text(L"Keep at least one tab in each pane");
            return;
        }
        const auto dropped=pane.routeIds[pane.active];
        mWorker->forget(dropped);
        pane.tabs.erase(pane.tabs.begin()+pane.active);
        pane.routeIds.erase(pane.routeIds.begin()+pane.active);
        pane.pending.erase(pane.pending.begin()+pane.active);
        if (pane.active>=pane.tabs.size())pane.active=pane.tabs.size()-1;
        Refresh(L"Tab closed");
    }
    void MainWindow::OnSplitClicked(IInspectable const&,RoutedEventArgs const&)
    {
        mSplit=!mSplit;
        if (!mSplit)mActivePane=0;
        SecondaryPane().Visibility(mSplit?Visibility::Visible:Visibility::Collapsed);
        PaneDivider().Visibility(mSplit?Visibility::Visible:Visibility::Collapsed);
        SecondaryColumn().Width(mSplit?
            GridLength{1.0,GridUnitType::Star}:GridLength{0.0,GridUnitType::Pixel});
        SplitButton().Content(winrt::box_value(
            hstring(mSplit?L"Single pane":L"Split panes")));
        Refresh(mSplit?L"Two independent panes":L"Single pane; other state retained");
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
        auto& pane=mPanes[0];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        // WinUI raises deferred SelectionChanged for programmatic strip
        // rebuilds. Only a DIFFERENT selected tab is user navigation.
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        pane.active=static_cast<size_t>(view.SelectedIndex());
        mActivePane=0;
        Refresh(L"Left tab selected");
    }
    void MainWindow::OnRightTabSelectionChanged(
        IInspectable const& sender,SelectionChangedEventArgs const&)
    {
        auto view=sender.as<TabView>();
        if (mPopulatingTabs || view.SelectedIndex()<0 || !mSplit)return;
        auto& pane=mPanes[1];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        pane.active=static_cast<size_t>(view.SelectedIndex());
        mActivePane=1;
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
