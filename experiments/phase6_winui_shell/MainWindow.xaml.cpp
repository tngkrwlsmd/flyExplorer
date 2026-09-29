#include "pch.h"
#include "MainWindow.xaml.h"
#include "../../src/base/shell_assoc_type_core.h"
#if __has_include("MainWindow.g.cpp")
#include "MainWindow.g.cpp"
#endif
#include <shellapi.h>
#include "../../src/fxfile/file_operation_core.h"
#include <algorithm>
#include <cwchar>
#include <cwctype>
#include <thread>
#include <numeric>
#include <iterator>
#include <system_error>
#include <winrt/Windows.System.h>
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <winrt/Microsoft.UI.Xaml.Media.h>
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
        mColumnControlsReady=true;
        // Each reusable XAML control forwards intent; the window owns the
        // shared native state/settings. Never attach a permanent MFC host.
        const auto nativeWeak=get_weak();
        winrt::get_self<winrt::FlyExplorerWinUIShell::implementation::NavigationSidebar>(
            SidebarView())->SetNavigateCallback([nativeWeak](int target){
            if(auto ui=nativeWeak.get()){
                if(target==0)ui->OpenFolder(ui->HomePath().native());
                else if(target==1)ui->OpenFolder(
                    (ui->HomePath()/L"Documents").native());
                else if(target==2)ui->OpenFolder(
                    (ui->HomePath()/L"Downloads").native());
                else if(target==3)ui->OpenFolder(L"shell:MyComputerFolder");
            }
        });
        fxfile::previewsettings::load(mPreferences);
        winrt::get_self<winrt::FlyExplorerWinUIShell::implementation::ShellHeader>(
            HeaderView())->RestoreTheme(static_cast<int>(mPreferences.theme));
        RootShell().RequestedTheme(
            mPreferences.theme==fxfile::previewsettings::Theme::Dark?
                ElementTheme::Dark:
            mPreferences.theme==fxfile::previewsettings::Theme::Light?
                ElementTheme::Light:ElementTheme::Default);
        winrt::get_self<winrt::FlyExplorerWinUIShell::implementation::ShellHeader>(
            HeaderView())->SetThemeCallback([nativeWeak](int selection){
                if(auto ui=nativeWeak.get())ui->ApplyThemeChoice(selection);
            });
        // Newly extracted real file toolbar and status footer share
        // the M2.0 native command model; callbacks hold only weak UI refs.
        fileBar()->SetAction([nativeWeak](int command){
            if(auto ui=nativeWeak.get()){
                if(command==0)ui->ExecuteFileCommand(
                    fxfile::filecommand::Kind::CreateFolder);
                else if(command==1)ui->ExecuteFileCommand(
                    fxfile::filecommand::Kind::RenameSelected);
                else if(command==2)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Copy);
                else if(command==3)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Move);
                else if(command==4)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Recycle);
                else if(command==5 && ui->mTransferProgress)
                    ui->mTransferProgress->cancel.store(true);
            }
        });
        fileBar()->SetSort([nativeWeak](int index){
            if(auto ui=nativeWeak.get())ui->UpdateSort(index);
        });
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
            throw winrt::hresult_error(E_FAIL,L"현재 실행 파일 경로를 확인할 수 없습니다.");
        std::wstring helper(module,chars);
        const auto last=helper.find_last_of(L"\\/");
        if(last==std::wstring::npos)
            throw winrt::hresult_error(E_FAIL,L"현재 실행 파일 경로가 올바르지 않습니다.");
        helper.resize(last+1);
        helper+=L"FlyShellIsolationHelper.exe";
        if(!mSupervisor->start(std::move(helper)))
            throw winrt::hresult_error(E_FAIL,L"독립 Shell 작업자를 시작할 수 없습니다.");
        if(!mWatcher->start())
            throw winrt::hresult_error(E_FAIL,L"독립 파일 변경 감시를 시작할 수 없습니다.");
        if(!mShellWatcher->start())
            throw winrt::hresult_error(E_FAIL,L"Shell 폴더 변경 감시를 시작할 수 없습니다.");
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
            L"독립 Shell 탐색 준비 중 · 파일 작업은 명시적 요청만 처리합니다.":
            L"기본 파일 작업 엔진을 연결하지 못했습니다.");
        InitializeM19();
        InitializePrivateSession();
    }
    MainWindow::~MainWindow()
    {
        if(mTransferProgress)mTransferProgress->cancel.store(true);
        if(mTransferTimer)mTransferTimer.Stop();
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
            StatusText().Text(L"독립 Shell 작업자가 폴더를 불러오는 중입니다.");
        } else StatusText().Text(L"Shell 폴더 이동을 요청할 수 없습니다.");
    }
    void MainWindow::QueuePidl(
        int side,fxfile::shellnav::Location target,
        fxfile::shellnav::NavigationAction action)
    {
        if(!target.valid()) {
            StatusText().Text(L"이 명령에 사용할 Shell 위치가 없습니다.");
            return;
        }
        auto& pane=mModel.panes[side];
        const auto id=mSupervisor->submit(
            side,pane.routeIds[pane.active],std::move(target),action);
        if(id) {
            // At most one outstanding helper operation per active pane.
            // Clear the canceled prior tab's UI pending marker too.
            mModel.markPending(side,pane.active,id,true);
            StatusText().Text(L"독립 Shell 작업자가 폴더를 불러오는 중입니다.");
        } else StatusText().Text(L"Shell 작업을 요청할 수 없습니다.");
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
                                L"Shell 폴더가 4.5초씩 두 번 응답하지 않았습니다. "
                                L"기존 폴더는 유지됩니다. 다시 시도하거나 다른 폴더를 선택하세요.");
                        else if(result.networkRequest)
                            StatusText().Text(
                                L"네트워크 폴더에 접근할 수 없거나 권한이 없습니다. "
                                L"기존 폴더는 유지됩니다.");
                        else
                            StatusText().Text(
                                L"Shell 폴더를 열지 못했습니다. "
                                L"기존 폴더는 유지됩니다.");
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
                        ClearFileDetails(side);
                        Refresh(result.recovered?
                            L"독립 Shell 작업자가 응답 지연 후 복구됐습니다.":
                            result.action==Action::Refresh?
                            L"폴더 변경 알림을 반영했습니다.":
                            L"독립 Shell 작업자로 폴더를 불러왔습니다.");
                        UpdateWatch(side,true);
                    }else RefreshTabs(side);
                    QueueNextWorkspaceTab(side);
                }else if(FAILED(applied)) {
                    StatusText().Text(L"오래된 Shell 탐색 결과를 무시했습니다.");
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
    void MainWindow::ClearFileDetails(int side){
        mFileLists[side].invalidate();
    }
    void MainWindow::ScheduleFileDetails(int side,bool force){
        auto const& pane=mModel.panes[side];
        if(pane.pending[pane.active])return;
        auto const route=pane.routeIds[pane.active];
        auto const tab=pane.active;
        auto const& items=pane.tabs[tab].snapshot().children;
        if(!force&&mFileLists[side].isCurrent(route,tab,items.size()))
            return;
        auto const& folder=pane.filesystemPaths[tab];
        if(folder.size()<3||folder[1]!=L':'||folder[2]!=L'\\')return;
        if(items.size()>1200)return;
        const std::wstring root=folder.substr(0,3);
        if(::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return;
        std::vector<std::wstring> paths{};
        paths.reserve(items.size());
        for(auto const& item:items){
            // Values copied from the supervised native Shell snapshot;
            // never retain a Shell COM pointer on this worker.
            paths.push_back(item.isFileSystem()?item.parsingName:std::wstring{});
        }
        const auto ticket=mFileLists[side].begin(route,tab);
        auto dispatch=DispatcherQueue();
        auto weak=get_weak();
        try{
            std::thread([side,tab,route,ticket,paths=std::move(paths),
                         dispatch,weak]{
                // Batch 24 distinct registered extensions in one disposable
                // helper subprocess. A timeout preserves the existing type
                // fallback and cannot block the WinUI UI thread.
                std::vector<std::wstring> extensions;
                for(auto const& path:paths){
                    const auto dot=path.find_last_of(L'.');
                    const auto slash=path.find_last_of(L"\\/");
                    if(dot==std::wstring::npos||
                       (slash!=std::wstring::npos&&dot<slash))continue;
                    auto ext=path.substr(dot);
                    if(!fxfile::filetype::safeExtension(ext))continue;
                    std::transform(ext.begin(),ext.end(),ext.begin(),
                       [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                    if(std::find(extensions.begin(),extensions.end(),ext)==extensions.end()
                         &&extensions.size()<24)extensions.push_back(ext);
                }
                std::unordered_map<std::wstring,std::wstring> windowsTypes;
                if(!extensions.empty()){
                    wchar_t exe[32768]{};
                    const auto count=::GetModuleFileNameW(nullptr,exe,32768);
                    if(count&&count<32768){
                        auto helper=(std::filesystem::path(exe).parent_path()/
                            L"FlyShellIsolationHelper.exe").native();
                        windowsTypes=fxfile::filetype::query(helper,extensions,2500);
                    }
                }
                std::vector<FileDetail> details(paths.size());
                for(size_t i=0;i<paths.size();++i){
                    if(paths[i].empty()||paths[i].size()>32000)continue;
                    WIN32_FILE_ATTRIBUTE_DATA data{};
                    if(!::GetFileAttributesExW(paths[i].c_str(),
                        GetFileExInfoStandard,&data))continue;
                    if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)continue;
                    auto& entry=details[i];
                    // Pure filename extension classification on the
                    // already validated local worker: no untrusted Shell
                    // extension or COM type handler runs on the UI thread.
                    if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)
                        entry.typeLabel=L"폴더";
                    else{
                        const auto dot=paths[i].find_last_of(L'.');
                        const auto slash=paths[i].find_last_of(L"\\/");
                        entry.typeLabel=dot!=std::wstring::npos&&
                             (slash==std::wstring::npos||dot>slash)&&
                             dot+1<paths[i].size()&&paths[i].size()-dot<=17?
                             paths[i].substr(dot+1)+L" 파일":L"파일";
                        if(dot!=std::wstring::npos&&
                           (slash==std::wstring::npos||dot>slash)){
                            auto ext=paths[i].substr(dot);
                            std::transform(ext.begin(),ext.end(),ext.begin(),
                               [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                            auto found=windowsTypes.find(ext);
                            if(found!=windowsTypes.end()&&!found->second.empty())
                                entry.typeLabel+=L" (Windows \uC720\uD615: "+found->second+L")";
                        }
                    }
                    if(!(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)){
                        entry.bytes=(static_cast<std::uint64_t>(
                            data.nFileSizeHigh)<<32)|data.nFileSizeLow;
                        entry.sizeKnown=true;
                        entry.bytesLabel=entry.bytes<1024?
                          std::to_wstring(entry.bytes)+L" B":
                          entry.bytes<1048576?
                          std::to_wstring(entry.bytes/1024)+L" KB":
                          std::to_wstring(entry.bytes/1048576)+L" MB";
                    }
                    ULARGE_INTEGER timestamp{};
                    timestamp.HighPart=data.ftLastWriteTime.dwHighDateTime;
                    timestamp.LowPart=data.ftLastWriteTime.dwLowDateTime;
                    entry.modified=timestamp.QuadPart;
                    FILETIME local{};
                    SYSTEMTIME stamp{};
                    if(::FileTimeToLocalFileTime(&data.ftLastWriteTime,&local)&&
                       ::FileTimeToSystemTime(&local,&stamp)){
                        wchar_t date[32]{},time[24]{};
                        if(::GetDateFormatEx(L"ko-KR",0,&stamp,
                              L"yyyy-MM-dd",date,32,nullptr)&&
                           ::GetTimeFormatEx(L"ko-KR",0,&stamp,
                              L"HH:mm",time,24)){
                            entry.dateLabel=std::wstring(date)+L" "+time;
                            entry.dateKnown=true;
                        }
                    }
                }
                auto payload=std::make_shared<std::vector<FileDetail>>(
                    std::move(details));
                dispatch.TryEnqueue([weak,payload,side,tab,route,ticket]{
                    if(auto ui=weak.get()){
                        auto const& pane=ui->mModel.panes[side];
                        if(!ui->mFileLists[side].accepts(ticket,route,tab)||
                           pane.active!=tab||pane.pending[tab]||
                           pane.routeIds[tab]!=route||
                           pane.tabs[tab].snapshot().children.size()!=payload->size())
                            return; // never apply stale metadata to a new folder
                        ui->mFileLists[side].details=std::move(*payload);
                        ui->FillFiles(side);
                    }
                });
            }).detach();
        }catch(...){
            mFileLists[side].invalidate();
        }
    }
    void MainWindow::OnNameColumnWidthChanged(
        IInspectable const& sender,
        Microsoft::UI::Xaml::Controls::Primitives::RangeBaseValueChangedEventArgs const&){
        auto slider=sender.try_as<Slider>();
        if(!slider)return;
        const auto name=slider.Name();
        int side=name==L"LeftNameWidthSlider"?0:
                 name==L"RightNameWidthSlider"?1:-1;
        if(side<0)return;
        auto width=slider.Value();
        if(width<120||width>320)return;
        mFileLists[side].nameColumnWidth=width;
        if(mColumnControlsReady)FillFiles(side);
    }
    void MainWindow::FillFiles(int side)
    {
        auto view=side==0?LeftFiles():RightFiles();
        const auto& pane=mModel.panes[static_cast<size_t>(side)];
        const auto& items=pane.tabs[pane.active].snapshot().children;
        std::vector<std::wstring> selected;
        for(auto const& old:view.SelectedItems()){
            auto row=old.try_as<ListViewItem>();
            if(!row||!row.Tag())continue;
            auto index=winrt::unbox_value<uint32_t>(row.Tag());
            if(index<mFileLists[side].renderedPaths.size())
                selected.push_back(mFileLists[side].renderedPaths[index]);
        }
        view.Items().Clear();
        mFileLists[side].renderedPaths.clear();
        mFileLists[side].renderedPaths.reserve(items.size());
        for(auto const& item:items)
            mFileLists[side].renderedPaths.push_back(item.parsingName);
        const bool detailReady=mFileLists[side].isCurrent(
             pane.routeIds[pane.active],pane.active,items.size());
        std::vector<size_t> order(items.size());
        std::iota(order.begin(),order.end(),size_t{0});
        const int mode=mFileLists[side].sortMode;
        auto lessName=[&](size_t lhs,size_t rhs){
            const auto& a=items[lhs].label;
            const auto& b=items[rhs].label;
            return ::CompareStringOrdinal(a.c_str(),-1,b.c_str(),-1,TRUE)==CSTR_LESS_THAN;
        };
        std::stable_sort(order.begin(),order.end(),[&](size_t lhs,size_t rhs){
            if(items[lhs].isFolder()!=items[rhs].isFolder())
                return items[lhs].isFolder();
            if(detailReady&&mode==2){
                const auto& x=mFileLists[side].details[lhs];
                const auto& y=mFileLists[side].details[rhs];
                if(x.sizeKnown!=y.sizeKnown)return x.sizeKnown;
                if(x.sizeKnown&&x.bytes!=y.bytes)return x.bytes>y.bytes;
            }else if(detailReady&&mode==3){
                const auto& x=mFileLists[side].details[lhs];
                const auto& y=mFileLists[side].details[rhs];
                if(x.dateKnown!=y.dateKnown)return x.dateKnown;
                if(x.dateKnown&&x.modified!=y.modified)
                    return x.modified>y.modified;
            }
            return mode==1?lessName(rhs,lhs):lessName(lhs,rhs);
        });
        for(const auto index:order){
            const auto& item=items[index];
            ListViewItem row;
            auto label=std::wstring(item.isFolder()?L"[폴더]  ":L"[파일]  ")+
                       item.label;
            if(detailReady){
                const auto& meta=mFileLists[side].details[index];
                if(!meta.typeLabel.empty())label+=L"   |   "+meta.typeLabel;
                if(meta.sizeKnown)label+=L"   |   "+meta.bytesLabel;
                if(meta.dateKnown)label+=L"   |   "+meta.dateLabel;
            }
            Grid columns;
            auto addColumn=[&](double width){
                ColumnDefinition def;
                def.Width(GridLength{width,GridUnitType::Pixel});
                columns.ColumnDefinitions().Append(def);
            };
            addColumn(mFileLists[side].nameColumnWidth);
            addColumn(165);addColumn(80);addColumn(155);
            StackPanel nameCell;
            nameCell.Orientation(Orientation::Horizontal);
            nameCell.Spacing(6);
            FontIcon glyph;
            glyph.FontFamily(Microsoft::UI::Xaml::Media::FontFamily{
                L"Segoe Fluent Icons"});
            glyph.Glyph(hstring(item.isFolder()?L"\uE8B7":L"\uE8A5"));
            nameCell.Children().Append(glyph);
            TextBlock filename;
            filename.Text(item.label);
            filename.TextTrimming(TextTrimming::CharacterEllipsis);
            nameCell.Children().Append(filename);
            Grid::SetColumn(nameCell,0);
            columns.Children().Append(nameCell);
            auto addText=[&](std::wstring const& text,int col){
                TextBlock field;
                field.Text(hstring(text));
                field.TextTrimming(TextTrimming::CharacterEllipsis);
                Grid::SetColumn(field,col);
                columns.Children().Append(field);
            };
            auto const* meta=detailReady?&mFileLists[side].details[index]:nullptr;
            addText(meta?meta->typeLabel:L"",1);
            addText(meta&&meta->sizeKnown?meta->bytesLabel:L"",2);
            addText(meta&&meta->dateKnown?meta->dateLabel:L"",3);
            row.Content(columns);
            Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
                row,hstring(label));
            row.Tag(winrt::box_value(static_cast<uint32_t>(index)));
            row.CanDrag(true);
            const auto weak=get_weak();
            row.DragStarting([weak,side](
                Microsoft::UI::Xaml::UIElement const& sender,
                Microsoft::UI::Xaml::DragStartingEventArgs const& args){
                if(auto ui=weak.get())ui->OnFileRowDragStarting(side,sender,args);
            });
            view.Items().Append(row);
            if(!item.parsingName.empty()&&
               std::find(selected.begin(),selected.end(),item.parsingName)
                  !=selected.end()){
                // Restore selection by native parsing path, never stale
                // pre-sort row index (including real multiple selection).
                view.SelectedItems().Append(row);
            }
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
        ActivePaneText().Text(mModel.activePane==0?L"활성: 왼쪽":L"활성: 오른쪽");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(mModel.activePane==0?L"왼쪽 창 (활성)":L"왼쪽 창")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(mModel.activePane==1?L"오른쪽 창 (활성)":L"오른쪽 창")));
        StatusText().Text(status);
        Title(L"flyExplorer - WinUI 3 전환 미리보기 - "+
            hstring(nav.snapshot().displayName));
        UpdateWatch(0);
        UpdateWatch(1);
        ScheduleFileDetails(0);
        ScheduleFileDetails(1);
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
        ActivePaneText().Text(side==0?L"활성: 왼쪽":L"활성: 오른쪽");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(side==0?L"왼쪽 창 (활성)":L"왼쪽 창")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(side==1?L"오른쪽 창 (활성)":L"오른쪽 창")));
        Title(L"flyExplorer - WinUI 3 전환 미리보기 - "+
              hstring(nav.snapshot().displayName));
    }
    void MainWindow::OnBackClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canBack()) {
            StatusText().Text(L"이 탭에 이전 폴더가 없습니다.");return;
        }
        QueuePidl(mModel.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Back),
            fxfile::shellnav::NavigationAction::Back);
    }
    void MainWindow::OnForwardClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canForward()) {
            StatusText().Text(L"이 탭에 다음 폴더가 없습니다.");return;
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
            StatusText().Text(L"주소 입력을 취소했습니다.");
            args.Handled(true);
        }
    }
    void MainWindow::OnNewTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        if (pane.tabs.size()>=32) {
            StatusText().Text(L"창마다 탭은 최대 32개까지 지원합니다.");
            return;
        }
        fxfile::shellnav::Location start(
            pane.tabs[pane.active].snapshot().folder);
        if(!start.valid()) {
            StatusText().Text(L"먼저 현재 폴더를 불러와 주세요.");
            return;
        }
        if(!mModel.dispatch(fxfile::explorerui::Command::AddTab,
                            mModel.activePane).accepted)return;
        QueuePidl(mModel.activePane,std::move(start),
                  fxfile::shellnav::NavigationAction::Open);
        Refresh(L"새 탭의 폴더를 불러오는 중입니다.");
    }
    void MainWindow::OnCloseTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        if (pane.tabs.size()<=1) {
            StatusText().Text(L"각 창에는 탭을 최소 한 개 유지해야 합니다.");
            return;
        }
        const auto change=mModel.dispatch(
            fxfile::explorerui::Command::CloseTab,mModel.activePane);
        if(!change.accepted)return;
        mSupervisor->forget(change.releasedRoute);
        mWatcher->unwatch(change.releasedRoute);
        mShellWatcher->unwatch(change.releasedRoute);
        mRestoreQueue[static_cast<size_t>(mModel.activePane)].clear();
        Refresh(L"탭을 닫았습니다.");
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
            hstring(mModel.split?L"단일 창":L"분할 창")));
        Refresh(mModel.split?L"두 창이 독립적으로 열렸습니다.":L"단일 창으로 표시합니다. 다른 창의 상태는 유지됩니다.");
    }
    void MainWindow::OnActivateLeft(IInspectable const&,RoutedEventArgs const&)
    {
        ActivatePane(0);
        StatusText().Text(L"왼쪽 창을 선택했습니다.");
    }
    void MainWindow::OnActivateRight(IInspectable const&,RoutedEventArgs const&)
    {
        ActivatePane(1);
        StatusText().Text(L"오른쪽 창을 선택했습니다.");
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
        Refresh(L"왼쪽 탭을 선택했습니다.");
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
        Refresh(L"오른쪽 탭을 선택했습니다.");
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
            OpenSelectedFolder(0);a.Handled(true);return;
        }
        HandleFileShortcut(0,a);
    }
    void MainWindow::OnRightFileKeyDown(
        IInspectable const&,Input::KeyRoutedEventArgs const& a)
    {
        if (a.Key()==Windows::System::VirtualKey::Enter) {
            OpenSelectedFolder(1);a.Handled(true);return;
        }
        HandleFileShortcut(1,a);
    }
}
