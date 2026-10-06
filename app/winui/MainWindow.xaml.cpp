#include "pch.h"
#include <winrt/Microsoft.UI.Input.h>
#include "MainWindow.xaml.h"
#include "../../src/base/shell_assoc_type_core.h"
#include "../../src/base/shell_thumbnail_core.h"
#if __has_include("MainWindow.g.cpp")
#include "MainWindow.g.cpp"
#endif
#include <shellapi.h>
#include "../../src/base/file_operation_core.h"
#include "../../src/base/shell_isolation_wire.h"
#include <algorithm>
#include <cmath>
#include <cwchar>
#include <cwctype>
#include <thread>
#include <numeric>
#include <iterator>
#include <system_error>
#include <winrt/Windows.System.h>
#include <winrt/Windows.UI.Text.h>
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <winrt/Microsoft.UI.Xaml.Media.h>
#include <winrt/Microsoft.UI.Xaml.Media.Imaging.h>
#include <robuffer.h>
#include <cstring>
#pragma comment(lib, "shell32.lib")

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace {
    std::wstring FriendlyAddress(std::wstring value)
    {
        auto lower=value;
        std::transform(lower.begin(),lower.end(),lower.begin(),
            [](wchar_t c){ return static_cast<wchar_t>(::towlower(c)); });
        if(lower==L"shell:mycomputerfolder" ||
           lower.find(L"20d04fe0-3aea-1069-a2d8-08002b30309d")!=std::wstring::npos)
            return L"\uB0B4 PC";
        return value;
    }

    std::wstring CompactAddress(std::wstring const& value)
    {
        const auto friendly=FriendlyAddress(value);
        if(friendly!=value || value.rfind(L"shell:",0)==0)return friendly;
        try{
            std::vector<std::wstring> parts;
            for(auto const& part:std::filesystem::path(value)){
                auto text=part.native();
                if(text.empty()||text==L"\\")continue;
                if(text.size()==3&&text[1]==L':'&&text[2]==L'\\')text.resize(2);
                parts.push_back(std::move(text));
            }
            if(parts.empty())return friendly;
            const auto start=parts.size()>3?parts.size()-3:0;
            std::wstring result=start?L"\u2026  >  ":L"";
            for(size_t i=start;i<parts.size();++i){
                if(i!=start)result+=L"  >  ";
                result+=parts[i];
            }
            return result;
        }catch(...){return friendly;}
    }

    std::wstring ResolveFriendlyAddress(std::wstring value)
    {
        if(value==L"\uB0B4 PC")return L"shell:MyComputerFolder";
        return value;
    }

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

namespace winrt::FlyExplorer::implementation
{
    MainWindow::MainWindow()
    {
        InitializeComponent();
        using Microsoft::UI::Xaml::Input::PointerEventHandler;
        RootShell().AddHandler(
            UIElement::PointerPressedEvent(),
            winrt::box_value(PointerEventHandler{
                this,&MainWindow::OnDetailColumnResizePointerPressed}),
            true);
        RootShell().AddHandler(
            UIElement::PointerReleasedEvent(),
            winrt::box_value(PointerEventHandler{
                this,&MainWindow::OnDetailColumnResizePointerReleased}),
            true);
        RootShell().AddHandler(
            UIElement::PointerCaptureLostEvent(),
            winrt::box_value(PointerEventHandler{
                this,&MainWindow::OnDetailColumnResizePointerCaptureLost}),
            true);
        // M2.6 uses the public WinUI 3 custom-titlebar/backdrop path only.
        // Pane-local folder TabViews remain inside each pane; the titlebar now
        // hosts a separate functional WindowTab workspace strip.
        try{
            ExtendsContentIntoTitleBar(true);
            auto titleHeader=winrt::get_self<
                winrt::FlyExplorer::implementation::ShellHeader>(
                    HeaderView());
            SetTitleBar(titleHeader->DragRegion());
            SystemBackdrop(Microsoft::UI::Xaml::Media::MicaBackdrop{});
        }catch(...){
            // Older/runtime-restricted hosts retain an opaque theme fallback.
            try{
                auto brush=Application::Current().Resources().Lookup(
                    winrt::box_value(L"ApplicationPageBackgroundThemeBrush"))
                    .try_as<Microsoft::UI::Xaml::Media::Brush>();
                if(brush)RootShell().Background(brush);
            }catch(...){ }
        }
        mColumnControlsReady=true;
        // Each reusable XAML control forwards intent; the window owns the
        // shared native state/settings. Never attach a permanent MFC host.
        const auto nativeWeak=get_weak();
        Closed([nativeWeak](IInspectable const&,WindowEventArgs const&){
            if(auto ui=nativeWeak.get())ui->PrepareForClose();
        });
        auto titleHeader=winrt::get_self<
            winrt::FlyExplorer::implementation::ShellHeader>(HeaderView());
        titleHeader->SetWindowTabCallbacks(
            [nativeWeak]{if(auto ui=nativeWeak.get()){
                ui->CreateWindowTab(L"shell:MyComputerFolder");
            }},
            [nativeWeak](int index){if(auto ui=nativeWeak.get()){
                struct Reset final{bool& flag;~Reset(){flag=false;}};
                ui->mSuppressWindowTabRefresh=true;
                Reset reset{ui->mSuppressWindowTabRefresh};
                ui->ActivateWindowTab(static_cast<size_t>(index));
            }},
            [nativeWeak](int index){if(auto ui=nativeWeak.get()){
                if(ui->mWorkspace.count()==1){ui->Close();return;}
                ui->CloseWindowTab(static_cast<size_t>(index));
            }});
        RootShell().PreviewKeyDown(
            Microsoft::UI::Xaml::Input::KeyEventHandler(
            [nativeWeak](IInspectable const&,
                Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){
                const bool control=(::GetKeyState(VK_CONTROL)&0x8000)!=0;
                const bool shift=(::GetKeyState(VK_SHIFT)&0x8000)!=0;
                const bool alt=(::GetKeyState(VK_MENU)&0x8000)!=0;
                const auto key=args.Key();
                if(!control&&!shift&&!alt&&
                   key==Windows::System::VirtualKey::F5){
                    if(auto ui=nativeWeak.get()){
                        const int side=ui->ActiveWindowTab().model.activePane;
                        auto const& pane=ui->ActiveWindowTab().model.panes[side];
                        auto const& current=pane.tabs[pane.active].snapshot();
                        if(current.folder.valid()){
                            ui->QueuePidl(side,
                                fxfile::shellnav::Location(current.folder),
                                fxfile::shellnav::NavigationAction::Refresh);
                        }else{
                            ui->StatusText().Text(
                                L"현재 위치를 새로 고칠 수 없습니다.");
                        }
                        args.Handled(true);
                    }
                    return;
                }
                if(!control&&!shift&&!alt&&
                   key==Windows::System::VirtualKey::F6){
                    if(auto ui=nativeWeak.get()){
                        auto const& model=ui->ActiveWindowTab().model;
                        if(model.split){
                            const int other=1-model.activePane;
                            ui->ActivatePane(other);
                            auto otherView=other==0?
                                ui->LeftFiles():ui->RightFiles();
                            otherView.Focus(
                                Microsoft::UI::Xaml::FocusState::Keyboard);
                            ui->StatusText().Text(
                                other==0?
                                L"왼쪽 창으로 포커스를 이동했습니다.":
                                L"오른쪽 창으로 포커스를 이동했습니다.");
                            args.Handled(true);
                        }
                    }
                    return;
                }
                const bool createFolderShortcut=
                    !alt&&control&&shift&&key==Windows::System::VirtualKey::N;
                if(createFolderShortcut){
                    if(auto ui=nativeWeak.get()){
                        ui->BeginFileNameCommand(
                            fxfile::filecommand::Kind::CreateFolder);
                        args.Handled(true);
                    }
                    return;
                }
                if(!control)return;
                if(key!=Windows::System::VirtualKey::T&&
                   key!=Windows::System::VirtualKey::W&&
                   key!=Windows::System::VirtualKey::Tab)return;
                if(auto ui=nativeWeak.get()){
                    if(key==Windows::System::VirtualKey::T){
                        if(ui->CreateWindowTab(L"shell:MyComputerFolder"))ui->RefreshWindowTabs();
                    }else if(key==Windows::System::VirtualKey::W){
                        if(ui->mWorkspace.count()==1)ui->Close();
                        else if(ui->CloseWindowTab(ui->mWorkspace.activeIndex()))ui->RefreshWindowTabs();
                    }else if(ui->mWorkspace.count()>1){
                        const auto count=ui->mWorkspace.count();
                        const auto active=ui->mWorkspace.activeIndex();
                        const auto next=shift?(active+count-1)%count:
                            (active+1)%count;
                        if(ui->ActivateWindowTab(next))ui->RefreshWindowTabs();
                    }
                    args.Handled(true);
                }
            }));
        RefreshWindowTabs();
        winrt::get_self<winrt::FlyExplorer::implementation::NavigationSidebar>(
            SidebarView())->SetNavigateCallback([nativeWeak](int target){
            if(auto ui=nativeWeak.get()){
                if(target==0)ui->OpenFolder(ui->HomePath().native());
                else if(target==1)ui->OpenFolder(
                    (ui->HomePath()/L"Documents").native());
                else if(target==2)ui->OpenFolder(
                    (ui->HomePath()/L"Downloads").native());
                else if(target==3)ui->OpenFolder(L"shell:MyComputerFolder");
                else if(target==4)ui->OpenFolder(
                    (ui->HomePath()/L"Desktop").native());
                else if(target==5)ui->OpenFolder(
                    (ui->HomePath()/L"Pictures").native());
                else if(target==6)ui->OpenFolder(
                    (ui->HomePath()/L"Music").native());
                else if(target==7)ui->OpenFolder(
                    (ui->HomePath()/L"Videos").native());
            }
        });
        mPreferencesCoordinator.load();
        InitializeBookmarks();
        InitializeFilterRules();
        InitializeSearchPresets();
        auto const& preferences=mPreferencesCoordinator.current();
        const auto initialView=(std::clamp)(preferences.defaultViewMode,0,4);
        for(auto& state:ActiveWindowTab().fileLists)state.viewMode=static_cast<FileViewMode>(initialView);
        winrt::get_self<winrt::FlyExplorer::implementation::ShellHeader>(
            HeaderView())->RestoreTheme(static_cast<int>(preferences.theme));
        RootShell().RequestedTheme(
            preferences.theme==fxfile::uisettings::Theme::Dark?
                ElementTheme::Dark:
            preferences.theme==fxfile::uisettings::Theme::Light?
                ElementTheme::Light:ElementTheme::Default);
        winrt::get_self<winrt::FlyExplorer::implementation::ShellHeader>(
            HeaderView())->SetThemeCallback([nativeWeak](int selection){
                if(auto ui=nativeWeak.get())ui->ApplyThemeChoice(selection);
            });
        // Newly extracted real file toolbar and status footer share
        // the M2.0 native command model; callbacks hold only weak UI refs.
        fileBar()->SetAction([nativeWeak](int command){
            if(auto ui=nativeWeak.get()){
                if(command==0)ui->BeginFileNameCommand(
                    fxfile::filecommand::Kind::CreateFolder);
                else if(command==1)ui->BeginFileNameCommand(
                    fxfile::filecommand::Kind::RenameSelected);
                else if(command==2)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Copy);
                else if(command==3)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Move);
                else if(command==4)ui->RunTransfer(
                    fxfile::shelltransfer::Kind::Recycle);
                else if(command==5 && ui->mFileOperations.cancellable())
                    ui->mFileOperations.cancel();
                else if(command==6)
                    ui->CopySelectedToWindowsClipboard(ui->ActiveWindowTab().model.activePane,true);
                else if(command==7)
                    ui->CopySelectedToWindowsClipboard(ui->ActiveWindowTab().model.activePane,false);
                else if(command==8)
                    ui->PasteFromWindowsClipboard();
                else if(command==9)ui->ExecuteFileCommand(
                    fxfile::filecommand::Kind::CreateFolder);
                else if(command==10)ui->ExecuteFileCommand(
                    fxfile::filecommand::Kind::RenameSelected);
                else if(command>=11&&command<=13){
                    const int theme=command-11;
                    ui->ApplyThemeChoice(theme);
                    winrt::get_self<winrt::FlyExplorer::implementation::ShellHeader>(
                        ui->HeaderView())->RestoreTheme(theme);
                }
                else if(command==14)ui->ToggleNameFilter(0);
                else if(command==15)ui->ToggleNameFilter(1);
            }
        });
        fileBar()->SetSort([nativeWeak](int index){
            if(auto ui=nativeWeak.get())ui->UpdateSort(index);
        });
        fileBar()->SetView([nativeWeak](int index){
            if(auto ui=nativeWeak.get())ui->UpdateView(index);
        });
        fileBar()->SetViewIndex(initialView);
        const auto dispatch=DispatcherQueue();
        const auto weak=get_weak();
        // The worker owns NO MainWindow/WinRT UI object. Cross-apartment
        // notifications carry only owned native value snapshots/PIDLs and
        // enter the XAML thread through its actual DispatcherQueue.
        mShellNavigation=std::make_unique<fxfile::previewnav::ShellNavigationController>(
            [weak,dispatch](fxfile::shellnav::IsolatedResult answer) {
                auto envelope=std::make_shared<fxfile::shellnav::IsolatedResult>(
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
        using StartFailure=fxfile::previewnav::ShellNavigationController::StartFailure;
        const auto startFailure=mShellNavigation->start(std::move(helper));
        if(startFailure==StartFailure::Supervisor)
            throw winrt::hresult_error(E_FAIL,L"독립 Shell 작업자를 시작할 수 없습니다.");
        if(startFailure==StartFailure::DirectoryWatcher)
            throw winrt::hresult_error(E_FAIL,L"독립 파일 변경 감시를 시작할 수 없습니다.");
        if(startFailure==StartFailure::ShellNamespaceWatcher)
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
            auto& pane=ActiveWindowTab().model.panes[side];
#if defined(_DEBUG)
            if(side==0 && testLeftDelay){
                mShellNavigation->submitOwnedTestDelay(
                    ActiveWindowTab().model,0,0,initial,true);
                continue;
            }
            if(side==0 && testLeftComDelay){
                mShellNavigation->submitOwnedComDelay(
                    ActiveWindowTab().model,0,0,initial,false,true);
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
    void MainWindow::PrepareForClose() noexcept
    {
        if(mClosing)return;
        mClosing=true;
        mWorkspaceRestore.reset();
        mSessionCoordinator.prepareForClose();
        mFileOperations.prepareForClose();
        mFileMetadata.prepareForClose();
        mFileDetails.prepareForClose();
        for(std::size_t i=0;i<mWorkspace.count();++i)
            for(auto& files:mWorkspace.state(i).fileLists)files.invalidate();
        try{if(mTransferTimer)mTransferTimer.Stop();}catch(...){}
        if(mShellNavigation)mShellNavigation->shutdown();
        mSearchController.prepareForClose();
    }
    MainWindow::~MainWindow()
    {
        PrepareForClose();
    }
    int32_t MainWindow::MyProperty() {return 0;}
    void MainWindow::MyProperty(int32_t) {}
    fxfile::shellnav::Session& MainWindow::Current()
    {
        auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(ActiveWindowTab().model.activePane)];
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
    std::uint64_t MainWindow::QueuePath(int side,std::wstring path)
    {
        mSearchController.invalidate();
        auto& model=ActiveWindowTab().model;
        auto& pane=model.panes[side];
        std::uint64_t id=0;
#if defined(_DEBUG)
        if(mOwnedComExhaustOnVirtual && side==0 &&
           path==L"shell:MyComputerFolder")
            id=mShellNavigation->submitOwnedComDelay(
                model,side,pane.active,std::move(path),true,true);
        else
#endif
            id=mShellNavigation->submitParsing(
                model,side,pane.active,std::move(path),true);
        if(id)StatusText().Text(L"폴더를 불러오는 중입니다.");
        else StatusText().Text(L"이 위치로 이동할 수 없습니다.");
        return id;
    }
    void MainWindow::QueuePidl(
        int side,fxfile::shellnav::Location target,
        fxfile::shellnav::NavigationAction action)
    {
        if(action!=fxfile::shellnav::NavigationAction::Refresh){
            mSearchController.invalidate();
            mWorkspaceRestore.reset(side);
        }
        if(!target.valid()) {
            StatusText().Text(L"이 위치를 열 수 없습니다.");
            return;
        }
        const auto id=mShellNavigation->submitActive(
            ActiveWindowTab().model,side,std::move(target),action);
        if(id)StatusText().Text(L"폴더를 불러오는 중입니다.");
        else StatusText().Text(L"폴더를 불러올 수 없습니다.");
    }
    bool MainWindow::QueueNextFolderPage(int side,bool completeFolder)
    {
        if(side<0||side>1)return false;
        auto& pane=ActiveWindowTab().model.panes[static_cast<std::size_t>(side)];
        if(pane.active>=pane.tabs.size()||
           pane.active>=pane.pending.size())return false;
        auto& state=ActiveWindowTab().fileLists[side];
        auto const& snapshot=pane.tabs[pane.active].snapshot();
        if(completeFolder){
            state.streamToComplete=true;
            state.fullModelLimitReached=false;
            const auto completeLimit=static_cast<std::size_t>(
                fxfile::isolation::kMaxCompleteModelEntries);
            const bool atCompleteLimit=
                snapshot.nextOffset>completeLimit||
                (snapshot.nextOffset==completeLimit&&snapshot.truncated);
            const bool nameIndexEligible=
                state.sortMode<=1&&
                (state.indexedNameSort||!state.filenameFilter.empty());
            if(!state.indexToComplete&&atCompleteLimit&&nameIndexEligible){
                state.indexToComplete=true;
                state.indexedNameProjection=true;
            }
            const auto limit=static_cast<std::size_t>(
                state.indexToComplete?
                    fxfile::isolation::kMaxBrowseEntries:
                    fxfile::isolation::kMaxCompleteModelEntries);
            if(snapshot.nextOffset>limit||
               (snapshot.nextOffset==limit&&snapshot.truncated)){
                state.streamToComplete=false;
                state.indexToComplete=false;
                state.fullModelLimitReached=true;
                if(state.indexedNameProjection){
                    state.indexedNameProjection=false;
                    state.indexedNameSort=false;
                    state.sortMode=0;
                    if(!state.filenameFilter.empty()){
                        state.filenameFilter.clear();
                        auto filter=side==0?LeftNameFilterBox():RightNameFilterBox();
                        if(!filter.Text().empty())filter.Text(L"");
                    }
                    if(side==ActiveWindowTab().model.activePane)
                        fileBar()->SetSortIndex(0);
                    UpdateSortPresentation(side);
                    FillFiles(side);
                    UpdateSelectionChrome();
                    if(side==ActiveWindowTab().model.activePane)UpdateFooterSummary();
                    StatusText().Text(
                        L"이름 인덱스는 현재 최대 100,000개 항목까지 지원합니다. "
                        L"일반 순차 탐색은 현재 창을 유지합니다.");
                }else{
                    state.sortMode=0;
                    if(!state.filenameFilter.empty()){
                        state.filenameFilter.clear();
                        auto filter=side==0?LeftNameFilterBox():RightNameFilterBox();
                        if(!filter.Text().empty())filter.Text(L"");
                    }
                    if(side==ActiveWindowTab().model.activePane)
                        fileBar()->SetSortIndex(0);
                    UpdateSortPresentation(side);
                    FillFiles(side);
                    UpdateSelectionChrome();
                    if(side==ActiveWindowTab().model.activePane)UpdateFooterSummary();
                    StatusText().Text(
                        L"유형/크기/날짜 전역 정렬은 현재 최대 20,000개 항목까지 지원합니다. "
                        L"이름 정렬/필터는 인덱스 경로를 사용하세요.");
                }
                return false;
            }
        }
        if(pane.pending[pane.active])return false;
        if(completeFolder&&!state.indexToComplete&&snapshot.baseOffset){
            const auto id=mShellNavigation->submitPreviousPage(
                ActiveWindowTab().model,side);
            if(id){
                StatusText().Text(
                    L"정확한 정렬을 위해 이전 폴더 항목을 다시 불러오는 중입니다.");
                return true;
            }
            state.streamToComplete=false;
            StatusText().Text(
                L"전체 폴더 모델을 복원할 수 없습니다. 현재 항목은 유지됩니다.");
            return false;
        }
        const bool hasForward=
            snapshot.residentEndOffset()<snapshot.nextOffset||
            snapshot.truncated;
        if(!hasForward){
            state.streamToComplete=false;
            state.indexToComplete=false;
            return false;
        }
        const auto ceiling=completeFolder?
            static_cast<std::size_t>(
                state.indexToComplete?
                    fxfile::isolation::kMaxBrowseEntries:
                    fxfile::isolation::kMaxCompleteModelEntries):
            static_cast<std::size_t>(fxfile::isolation::kMaxBrowseEntries);
        const auto id=mShellNavigation->submitNextPage(
            ActiveWindowTab().model,side,ceiling);
        if(id){
            StatusText().Text(completeFolder?
                (state.indexToComplete?
                    L"전체 이름 인덱스를 완성하는 중입니다.":
                    L"정확한 정렬을 위해 남은 폴더 항목을 불러오는 중입니다."):
                L"폴더의 다음 항목 페이지를 불러오는 중입니다.");
            return true;
        }
        state.streamToComplete=false;
        state.indexToComplete=false;
        StatusText().Text(
            L"이 폴더의 추가 항목을 더 불러올 수 없습니다. 현재 항목은 유지됩니다.");
        return false;
    }
    void MainWindow::UpdateWatch(int side,bool force)
    {
        mShellNavigation->updateWatch(
            ActiveWindowTab().model,side,force,mOwnedShellNotifyTest);
    }
    void MainWindow::OnNativeResult(fxfile::shellnav::IsolatedResult result)
    {
        using Kind=fxfile::previewnav::ShellNavigationController::CompletionKind;
        using Action=fxfile::shellnav::NavigationAction;
        const auto completed=mShellNavigation->accept(
            ActiveWindowTab().model,std::move(result));
        if(completed.kind==Kind::Ignored)return;
        const bool continuation=completed.action==Action::Continue;
        const bool restoreSettled=continuation?false:mWorkspaceRestore.settle(
            completed.side,completed.request);
        auto continueRestore=[&]{
            if(restoreSettled)QueueNextWorkspaceTab(completed.side);
        };
        if(completed.kind==Kind::NoChange){
            continueRestore();
            return;
        }
        if(completed.kind==Kind::Failed){
            if(completed.active&&continuation){
                auto& state=ActiveWindowTab().fileLists[completed.side];
                auto const& pane=ActiveWindowTab().model.panes[completed.side];
                state.streamToComplete=false;
                state.indexToComplete=false;
                state.visibleCount=(std::min)(
                    state.visibleCount,
                    pane.tabs[pane.active].snapshot().children.size());
                FillFiles(completed.side);
                UpdateFooterSummary();
                StatusText().Text(
                    L"추가 폴더 항목을 불러오지 못했습니다. 이미 불러온 항목은 유지됩니다.");
                return;
            }
            if(completed.active){
                if(completed.timedOut)
                    StatusText().Text(
                        L"Shell 폴더가 4.5초씩 두 번 응답하지 않았습니다. "
                        L"기존 폴더는 유지됩니다. 다시 시도하거나 다른 폴더를 선택하세요.");
                else if(completed.networkRequest)
                    StatusText().Text(
                        L"네트워크 폴더에 접근할 수 없거나 권한이 없습니다. "
                        L"기존 폴더는 유지됩니다.");
                else
                    StatusText().Text(
                        L"Shell 폴더를 열지 못했습니다. "
                        L"기존 폴더는 유지됩니다.");
            }
            continueRestore();
            return;
        }
        if(completed.kind==Kind::Rejected){
            if(completed.active&&continuation){
                auto& state=ActiveWindowTab().fileLists[completed.side];
                state.streamToComplete=false;
                state.indexToComplete=false;
                FillFiles(completed.side);
                UpdateFooterSummary();
                StatusText().Text(
                    L"폴더 상태가 바뀌어 추가 페이지를 무시했습니다. 새로 고침 후 다시 시도하세요.");
                return;
            }
            StatusText().Text(L"이전 탐색 결과를 무시했습니다.");
            continueRestore();
            return;
        }
        if(completed.kind==Kind::Extended){
            if(completed.active){
                using PageDirection=
                    fxfile::previewnav::ShellNavigationController::PageDirection;
                auto& state=ActiveWindowTab().fileLists[completed.side];
                auto& pane=ActiveWindowTab().model.panes[completed.side];
                auto& session=pane.tabs[pane.active];
                const bool boundedResident=
                    state.indexToComplete||
                    (!state.streamToComplete&&state.sortMode==0&&
                     state.filenameFilter.empty());
                if(boundedResident){
                    if(completed.pageDirection==PageDirection::Forward){
                        const auto evicted=session.trimResidentFront(
                            fxfile::shellnav::kResidentWindowEntries);
                        if(evicted&&!state.indexedNameProjection){
                            state.visibleCount=state.visibleCount>evicted?
                                state.visibleCount-evicted:
                                (std::min)(
                                    static_cast<std::size_t>(160),
                                    session.snapshot().children.size());
                        }
                    }else if(completed.pageDirection==PageDirection::Backward){
                        session.trimResidentBack(
                            fxfile::shellnav::kResidentWindowEntries);
                        if(!state.indexedNameProjection)
                            state.visibleCount=(std::min)(
                                state.visibleCount,
                                session.snapshot().children.size());
                    }
                }
                auto const& snapshot=session.snapshot();
                const bool incomplete=state.indexToComplete?
                    (snapshot.residentEndOffset()<snapshot.nextOffset||
                     snapshot.truncated):
                    (snapshot.baseOffset||
                     snapshot.residentEndOffset()<snapshot.nextOffset||
                     snapshot.truncated);
                if(state.streamToComplete&&!incomplete){
                    state.streamToComplete=false;
                    state.indexToComplete=false;
                }
                ClearFileDetails(completed.side);
                FillFiles(completed.side);
                UpdateSelectionChrome();
                UpdateFooterSummary();
                if(state.streamToComplete&&incomplete){
                    if(QueueNextFolderPage(completed.side,true))return;
                    if(state.fullModelLimitReached)return;
                    state.streamToComplete=false;
                    state.indexToComplete=false;
                }
                StatusText().Text(
                    completed.pageDirection==PageDirection::Backward?
                    L"폴더의 이전 항목 창을 불러왔습니다.":
                    snapshot.truncated?
                    L"폴더의 다음 항목 페이지를 불러왔습니다.":
                    L"폴더의 현재 스트리밍 항목을 불러왔습니다.");
            }
            return;
        }
        if(completed.active){
            ClearFileDetails(completed.side);
            Refresh(completed.recovered?
                L"응답 지연 후 폴더를 불러왔습니다.":
                completed.action==Action::Refresh?
                L"폴더 변경 알림을 반영했습니다.":
                L"폴더를 불러왔습니다.");
            UpdateWatch(completed.side,true);
        }else RefreshTabs(completed.side);
        continueRestore();
    }
    void MainWindow::OnNativeChange(std::uint64_t route,std::uint64_t token)
    {
        using Change=fxfile::previewnav::ShellNavigationController::ChangeDisposition;
        const auto changed=mShellNavigation->handleChange(
            ActiveWindowTab().model,route,token);
        if(changed==Change::Queued)
            StatusText().Text(L"폴더를 불러오는 중입니다.");
        else if(changed==Change::InvalidTarget)
            StatusText().Text(L"이 위치를 열 수 없습니다.");
        else if(changed==Change::SubmitFailed)
            StatusText().Text(L"폴더를 불러올 수 없습니다.");
    }
    void MainWindow::RefreshTabs(int side)
    {
        auto view=side==0?LeftTabs():RightTabs();
        const auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
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
        mFileMetadata.cancel(side);
        mFileDetails.cancel(side);
        ActiveWindowTab().fileLists[side].invalidate();
    }
    void MainWindow::ScheduleFileMetadata(int side,bool force){
        auto const& pane=ActiveWindowTab().model.panes[side];
        if(pane.pending[pane.active])return;
        const auto route=pane.routeIds[pane.active];
        const auto tab=pane.active;
        auto const& snapshot=pane.tabs[tab].snapshot();
        auto const& items=snapshot.children;
        auto& listState=ActiveWindowTab().fileLists[side];
        if(!force&&listState.metadataCurrent(route,tab,items.size()))return;
        if(snapshot.baseOffset||snapshot.truncated||
           items.size()>fxfile::isolation::kMaxCompleteModelEntries)return;
        auto const& folder=pane.filesystemPaths[tab];
        if(folder.size()<3||folder[1]!=L':'||folder[2]!=L'\\')return;
        const std::wstring root=folder.substr(0,3);
        if(::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return;
        std::vector<std::wstring> paths{};
        paths.reserve(items.size());
        for(auto const& item:items)
            paths.push_back(item.isFileSystem()?item.parsingName:std::wstring{});
        const auto ticket=listState.beginMetadata(route,tab);
        fxfile::previewmetadata::FileMetadataController::Request request{};
        request.side=side;request.tab=tab;request.route=route;request.ticket=ticket;
        request.paths=std::move(paths);
        auto dispatch=DispatcherQueue();
        auto weak=get_weak();
        const bool started=mFileMetadata.start(
            std::move(request),
            [dispatch](fxfile::previewmetadata::FileMetadataController::UiTask task){
                try{return dispatch.TryEnqueue(
                    [task=std::move(task)]() mutable {task();});}
                catch(...){return false;}
            },
            [weak](fxfile::previewmetadata::FileMetadataController::Completion completed){
                if(auto ui=weak.get()){
                    const int side=completed.side;
                    const auto tab=completed.tab;
                    const auto route=completed.route;
                    const auto ticket=completed.ticket;
                    const auto count=completed.metadata.size();
                    auto const& pane=ui->ActiveWindowTab().model.panes[side];
                    auto const& snapshot=pane.tabs[tab].snapshot();
                    if(!ui->ActiveWindowTab().fileLists[side].acceptsMetadata(
                           ticket,route,tab)||
                       pane.active!=tab||pane.pending[tab]||
                       pane.routeIds[tab]!=route||
                       snapshot.baseOffset||snapshot.truncated||
                       snapshot.children.size()!=count)return;
                    auto& state=ui->ActiveWindowTab().fileLists[side];
                    state.metadata=std::move(completed.metadata);
                    ui->FillFiles(side);
                    if(state.sortMode>1)
                        ui->StatusText().Text(
                            L"파일 메타데이터 정렬을 적용했습니다.");
                }
            });
        if(!started)listState.invalidateMetadata();
    }
    void MainWindow::ScheduleFileDetails(int side,bool force){
        auto const& pane=ActiveWindowTab().model.panes[side];
        if(pane.pending[pane.active])return;
        auto const route=pane.routeIds[pane.active];
        auto const tab=pane.active;
        auto const& snapshot=pane.tabs[tab].snapshot();
        auto const& items=snapshot.children;
        const auto requestedView=ActiveWindowTab().fileLists[side].viewMode;
        double raster=1.0;
        try{if(auto xr=RootShell().XamlRoot())raster=xr.RasterizationScale();}
        catch(...){raster=1.0;}
        const std::uint32_t baseVisual=requestedView==FileViewMode::LargeIcons?64:
            requestedView==FileViewMode::MediumIcons?32:
            requestedView==FileViewMode::SmallIcons?20:16;
        const auto visualPixels=static_cast<std::uint32_t>((std::min)(64.0,
            (std::max)(16.0,baseVisual*raster+0.5)));
        const double thumbnailBase=requestedView==FileViewMode::LargeIcons?96.0:48.0;
        const auto thumbnailPixels=static_cast<std::uint32_t>((std::min)(128.0,
            (std::max)(32.0,thumbnailBase*raster+0.5)));
        auto& listState=ActiveWindowTab().fileLists[side];
        if(!force&&listState.isCurrent(route,tab,items.size())&&
           listState.visualPixels==visualPixels)return;
        auto const& folder=pane.filesystemPaths[tab];
        if(folder.size()<3||folder[1]!=L':'||folder[2]!=L'\\')return;
        if(snapshot.truncated||items.size()>1200)return;
        const std::wstring root=folder.substr(0,3);
        if(::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return;
        std::vector<std::wstring> paths{};
        paths.reserve(items.size());
        for(auto const& item:items)
            paths.push_back(item.isFileSystem()?item.parsingName:std::wstring{});
        const auto ticket=listState.begin(route,tab);
        listState.visualPixels=visualPixels;
        fxfile::previewdetail::FileDetailController::Request request{};
        request.side=side;request.tab=tab;request.route=route;request.ticket=ticket;
        request.viewMode=requestedView;request.visualPixels=visualPixels;
        request.thumbnailPixels=thumbnailPixels;request.paths=std::move(paths);
        auto dispatch=DispatcherQueue();
        auto weak=get_weak();
        const bool started=mFileDetails.start(
            std::move(request),
            [dispatch](fxfile::previewdetail::FileDetailController::UiTask task){
                try{return dispatch.TryEnqueue(
                    [task=std::move(task)]() mutable {task();});}
                catch(...){return false;}
            },
            [weak](fxfile::previewdetail::FileDetailController::Completion completed){
                if(auto ui=weak.get()){
                    const int side=completed.side;
                    const auto tab=completed.tab;
                    const auto route=completed.route;
                    const auto ticket=completed.ticket;
                    auto const count=completed.details.size();
                    auto const& pane=ui->ActiveWindowTab().model.panes[side];
                    if(!ui->ActiveWindowTab().fileLists[side].accepts(
                           ticket,route,tab)||
                       pane.active!=tab||pane.pending[tab]||
                       pane.routeIds[tab]!=route||
                       pane.tabs[tab].snapshot().children.size()!=count)return;
                    ui->ActiveWindowTab().fileLists[side].details=
                        std::move(completed.details);
                    ui->FillFiles(side);
                }
            });
        if(!started)listState.invalidateDetails();
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
        if(width<120||width>360)return;
        ActiveWindowTab().fileLists[side].nameColumnWidth=width;
        if(mColumnControlsReady)ApplyDetailColumnLayout(side);
    }
    void MainWindow::OnDetailColumnResizePointerPressed(
        IInspectable const&,
        Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const& args){
        const auto point=args.GetCurrentPoint(RootShell());
        const auto position=point.Position();
        const bool diagnostic=
            ::GetEnvironmentVariableW(
                L"FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC",nullptr,0)>0;
        if(diagnostic)StatusText().Text(L"RESIZE_PRESS");
        int side=-1;
        int column=-1;
        auto hitThumb=[&](
            int candidateSide,
            int candidateColumn,
            Microsoft::UI::Xaml::Controls::Primitives::Thumb const& thumb){
            if(thumb.Visibility()!=Visibility::Visible||
               thumb.ActualWidth()<=0.0||thumb.ActualHeight()<=0.0)return false;
            const auto origin=thumb.TransformToVisual(RootShell()).TransformPoint(
                Windows::Foundation::Point{0.0f,0.0f});
            constexpr double pad=2.0;
            if(position.X<origin.X-pad||
               position.X>origin.X+thumb.ActualWidth()+pad||
               position.Y<origin.Y-pad||
               position.Y>origin.Y+thumb.ActualHeight()+pad)return false;
            side=candidateSide;
            column=candidateColumn;
            return true;
        };
        if(!hitThumb(0,0,LeftNameColumnResizeThumb())&&
           !hitThumb(0,1,LeftTypeColumnResizeThumb())&&
           !hitThumb(0,2,LeftSizeColumnResizeThumb())&&
           !hitThumb(1,0,RightNameColumnResizeThumb())&&
           !hitThumb(1,1,RightTypeColumnResizeThumb())&&
           !hitThumb(1,2,RightSizeColumnResizeThumb())){
            if(diagnostic)StatusText().Text(L"RESIZE_MISS");
            return;
        }
        if(diagnostic)StatusText().Text(
            hstring(L"RESIZE_HIT "+std::to_wstring(side)+L","+
                std::to_wstring(column)));
        POINT cursor{};
        if(!::GetCursorPos(&cursor)){
            if(diagnostic)StatusText().Text(L"RESIZE_CURSOR_FAIL");
            return;
        }
        if(ActiveWindowTab().model.activePane!=side)ActivatePane(side);
        mDetailColumnPointerDrag=true;
        mDetailColumnPointerSide=side;
        mDetailColumnPointerColumn=column;
        mDetailColumnPointerLastScreenX=cursor.x;
        if(mDetailColumnDragTimer)mDetailColumnDragTimer.Stop();
        auto timer=DispatcherQueue().CreateTimer();
        mDetailColumnDragTimer=timer;
        timer.Interval(std::chrono::milliseconds(16));
        auto weak=get_weak();
        timer.Tick([weak](auto const&,auto const&){
            auto ui=weak.get();
            if(!ui)return;
            if(!ui->mDetailColumnPointerDrag){
                if(ui->mDetailColumnDragTimer)ui->mDetailColumnDragTimer.Stop();
                return;
            }
            if((::GetAsyncKeyState(VK_LBUTTON)&0x8000)==0){
                ui->mDetailColumnPointerDrag=false;
                ui->mDetailColumnPointerSide=-1;
                ui->mDetailColumnPointerColumn=-1;
                if(ui->mDetailColumnDragTimer)ui->mDetailColumnDragTimer.Stop();
                return;
            }
            POINT next{};
            if(!::GetCursorPos(&next))return;
            double raster=1.0;
            try{
                if(auto xr=ui->RootShell().XamlRoot())
                    raster=xr.RasterizationScale();
            }catch(...){raster=1.0;}
            if(raster<=0.0)raster=1.0;
            const auto delta=
                static_cast<double>(next.x-ui->mDetailColumnPointerLastScreenX)/
                raster;
            if(std::abs(delta)<0.25)return;
            ui->mDetailColumnPointerLastScreenX=next.x;
            auto& state=ui->ActiveWindowTab().fileLists[
                ui->mDetailColumnPointerSide];
            if(ui->mDetailColumnPointerColumn==0)
                state.nameColumnWidth=(std::clamp)(
                    state.nameColumnWidth+delta,120.0,360.0);
            else if(ui->mDetailColumnPointerColumn==1)
                state.typeColumnWidth=(std::clamp)(
                    state.typeColumnWidth+delta,96.0,320.0);
            else if(ui->mDetailColumnPointerColumn==2)
                state.sizeColumnWidth=(std::clamp)(
                    state.sizeColumnWidth+delta,64.0,180.0);
            ui->ApplyDetailColumnLayout(ui->mDetailColumnPointerSide);
            if(::GetEnvironmentVariableW(
                   L"FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC",nullptr,0)>0)
                ui->StatusText().Text(
                    hstring(L"RESIZE_MOVE "+std::to_wstring(delta)));
        });
        timer.Start();
        args.Handled(true);
    }
    void MainWindow::OnDetailColumnResizePointerMoved(
        IInspectable const&,
        Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const&){
        // Physical mouse resize is driven by mDetailColumnDragTimer because
        // WinUI does not reliably route PointerMoved during this owned drag.
    }
    void MainWindow::OnDetailColumnResizePointerReleased(
        IInspectable const&,
        Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const& args){
        if(!mDetailColumnPointerDrag)return;
        mDetailColumnPointerDrag=false;
        mDetailColumnPointerSide=-1;
        mDetailColumnPointerColumn=-1;
        if(mDetailColumnDragTimer)mDetailColumnDragTimer.Stop();
        args.Handled(true);
    }
    void MainWindow::OnDetailColumnResizePointerCaptureLost(
        IInspectable const&,
        Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const&){
        if(!mDetailColumnPointerDrag&&mDetailColumnDragTimer)
            mDetailColumnDragTimer.Stop();
    }
    void MainWindow::OnNameFilterChanged(
        IInspectable const& sender,
        Microsoft::UI::Xaml::Controls::TextChangedEventArgs const&){
        if(!mColumnControlsReady)return;
        const auto input=sender.try_as<TextBox>();
        if(!input)return;
        const auto name=input.Name();
        const int side=name==L"LeftNameFilterBox"?0:
                       name==L"RightNameFilterBox"?1:-1;
        if(side<0)return;
        auto text=std::wstring(input.Text().c_str());
        if(text.size()>64)return;
        auto& state=ActiveWindowTab().fileLists[side];
        auto const& pane=ActiveWindowTab().model.panes[side];
        auto const& session=pane.tabs[pane.active];
        auto const& snapshot=session.snapshot();
        if(state.filenameFilter==text)return;
        const auto completeLimit=static_cast<std::size_t>(
            fxfile::isolation::kMaxCompleteModelEntries);
        const bool beyondComplete=
            snapshot.nextOffset>completeLimit||
            (snapshot.nextOffset==completeLimit&&snapshot.truncated);
        state.filenameFilter=std::move(text);
        state.visibleCount=160;
        if(beyondComplete&&!state.filenameFilter.empty()){
            state.indexedNameProjection=true;
            state.indexToComplete=
                snapshot.residentEndOffset()<snapshot.nextOffset||
                snapshot.truncated;
        }else if(state.filenameFilter.empty()){
            state.indexedNameProjection=
                beyondComplete&&state.indexedNameSort;
            state.indexToComplete=state.indexedNameProjection&&
                (snapshot.residentEndOffset()<snapshot.nextOffset||
                 snapshot.truncated);
        }else{
            state.indexedNameProjection=false;
            state.indexToComplete=false;
        }
        FillFiles(side);
        UpdateSelectionChrome();
        if(side==ActiveWindowTab().model.activePane)UpdateFooterSummary();
        if(state.indexedNameProjection){
            if(state.indexToComplete)
                QueueNextFolderPage(side,true);
            else
                StatusText().Text(L"전체 이름 인덱스에 필터를 적용했습니다.");
        }else if(!state.filenameFilter.empty()&&
                (snapshot.baseOffset||
                 snapshot.residentEndOffset()<snapshot.nextOffset||
                 snapshot.truncated)){
            QueueNextFolderPage(side,true);
        }else if(state.filenameFilter.empty()&&state.sortMode==0){
            state.streamToComplete=false;
            state.indexToComplete=false;
        }
    }
    void MainWindow::OnLoadMoreFiles(
        IInspectable const& sender,Microsoft::UI::Xaml::RoutedEventArgs const&){
        auto const button=sender.try_as<Button>();
        if(!button)return;
        const auto label=button.Name();
        const int side=label==L"LeftLoadMoreButton"?0:
                       label==L"RightLoadMoreButton"?1:-1;
        if(side<0)return;
        auto const& pane=ActiveWindowTab().model.panes[side];
        if(pane.pending[pane.active])return;
        auto& state=ActiveWindowTab().fileLists[side];
        if(state.visibleRoute!=pane.routeIds[pane.active]||
           state.visibleTab!=pane.active)return;
        const auto available=state.filteredCount;
        auto const& snapshot=pane.tabs[pane.active].snapshot();
        const bool hasForward=
            snapshot.residentEndOffset()<snapshot.nextOffset||
            snapshot.truncated;
        if(state.visibleCount<available){
            state.visibleCount=(std::min)(available,state.visibleCount+160);
            FillFiles(side); // Selection is restored using real parsing paths.
            if(state.visibleCount>=available&&hasForward)
                QueueNextFolderPage(side,state.indexToComplete);
            return;
        }
        if(hasForward){
            state.visibleCount+=160;
            if(!QueueNextFolderPage(side,state.indexToComplete))
                state.visibleCount=available;
        }
    }
    void MainWindow::OnLoadPreviousFiles(
        IInspectable const& sender,Microsoft::UI::Xaml::RoutedEventArgs const&){
        auto const button=sender.try_as<Button>();
        if(!button)return;
        const auto label=button.Name();
        const int side=label==L"LeftLoadPreviousButton"?0:
                       label==L"RightLoadPreviousButton"?1:-1;
        if(side<0)return;
        auto& pane=ActiveWindowTab().model.panes[side];
        if(pane.pending[pane.active])return;
        auto& state=ActiveWindowTab().fileLists[side];
        if(state.visibleRoute!=pane.routeIds[pane.active]||
           state.visibleTab!=pane.active)return;
        auto const& snapshot=pane.tabs[pane.active].snapshot();
        if(!snapshot.baseOffset)return;
        state.streamToComplete=false;
        const auto id=mShellNavigation->submitPreviousPage(
            ActiveWindowTab().model,side);
        if(id)
            StatusText().Text(L"폴더의 이전 항목 창을 불러오는 중입니다.");
        else
            StatusText().Text(L"이전 항목 창을 불러올 수 없습니다.");
    }
    int MainWindow::DetailLayoutProfile() const
    {
        const double nav=mShellWidth<1040.0?156.0:188.0;
        const double content=(std::max)(0.0,mShellWidth-nav-17.0);
        const double pane=ActiveWindowTab().model.split?(std::max)(0.0,(content-1.0)/2.0):content;
        if(pane<250.0)return 0;
        if(pane<340.0)return 1;
        if(pane<500.0)return 2;
        return 3;
    }
    std::array<GridLength,4> MainWindow::DetailColumnWidths(int side) const
    {
        const int profile=DetailLayoutProfile();
        auto const& state=ActiveWindowTab().fileLists[side];
        const auto name=(std::clamp)(state.nameColumnWidth,120.0,360.0);
        const auto type=(std::clamp)(state.typeColumnWidth,96.0,320.0);
        const auto size=(std::clamp)(state.sizeColumnWidth,64.0,180.0);
        if(profile==0)return {GridLength{1.0,GridUnitType::Star},GridLength{0.0,GridUnitType::Pixel},GridLength{0.0,GridUnitType::Pixel},GridLength{0.0,GridUnitType::Pixel}};
        if(profile==1)return {GridLength{1.0,GridUnitType::Star},GridLength{0.0,GridUnitType::Pixel},GridLength{size,GridUnitType::Pixel},GridLength{0.0,GridUnitType::Pixel}};
        if(profile==2)return {GridLength{(std::min)(name,220.0),GridUnitType::Pixel},GridLength{1.0,GridUnitType::Star},GridLength{size,GridUnitType::Pixel},GridLength{0.0,GridUnitType::Pixel}};
        return {GridLength{name,GridUnitType::Pixel},GridLength{type,GridUnitType::Pixel},GridLength{size,GridUnitType::Pixel},GridLength{1.0,GridUnitType::Star}};
    }
    void MainWindow::ApplyDetailColumnLayout(int side)
    {
        const auto widths=DetailColumnWidths(side);
        auto name=side==0?LeftNameHeaderColumn():RightNameHeaderColumn();
        auto type=side==0?LeftTypeHeaderColumn():RightTypeHeaderColumn();
        auto size=side==0?LeftSizeHeaderColumn():RightSizeHeaderColumn();
        auto date=side==0?LeftDateHeaderColumn():RightDateHeaderColumn();
        name.Width(widths[0]);type.Width(widths[1]);size.Width(widths[2]);date.Width(widths[3]);

        const auto profile=DetailLayoutProfile();
        auto setThumbVisibility=[&](
            auto const& nameThumb,auto const& typeThumb,auto const& sizeThumb){
            nameThumb.Visibility(
                profile>=2?Visibility::Visible:Visibility::Collapsed);
            typeThumb.Visibility(
                profile>=3?Visibility::Visible:Visibility::Collapsed);
            sizeThumb.Visibility(
                profile>=1?Visibility::Visible:Visibility::Collapsed);
        };
        if(side==0)setThumbVisibility(
            LeftNameColumnResizeThumb(),LeftTypeColumnResizeThumb(),
            LeftSizeColumnResizeThumb());
        else setThumbVisibility(
            RightNameColumnResizeThumb(),RightTypeColumnResizeThumb(),
            RightSizeColumnResizeThumb());

        auto view=side==0?LeftFiles():RightFiles();
        for(auto const& item:view.Items()){
            auto row=item.try_as<ListViewItem>();
            if(!row)continue;
            auto grid=row.Content().try_as<Grid>();
            if(!grid||grid.ColumnDefinitions().Size()!=4)continue;
            for(std::uint32_t column=0;column<4;++column)
                grid.ColumnDefinitions().GetAt(column).Width(widths[column]);
        }
    }

    void MainWindow::UpdateViewPresentation(int side)
    {
        auto view=side==0?LeftFiles():RightFiles();
        auto header=side==0?LeftDetailsHeader():RightDetailsHeader();
        const auto viewMode=ActiveWindowTab().fileLists[side].viewMode;
        const bool details=viewMode==FileViewMode::Details;
        header.Height(details?24.0:0.0);
        const auto visibility=details?Visibility::Visible:Visibility::Collapsed;
        if(side==0){
            LeftNameSortButton().Visibility(visibility);LeftTypeSortButton().Visibility(visibility);
            LeftSizeSortButton().Visibility(visibility);LeftDateSortButton().Visibility(visibility);
        }else{
            RightNameSortButton().Visibility(visibility);RightTypeSortButton().Visibility(visibility);
            RightSizeSortButton().Visibility(visibility);RightDateSortButton().Visibility(visibility);
        }
        const int panel=viewMode==FileViewMode::SmallIcons?1:
                        viewMode==FileViewMode::MediumIcons?2:
                        viewMode==FileViewMode::LargeIcons?3:0;
        if(ActiveWindowTab().fileLists[side].appliedItemsPanel!=panel){
            const wchar_t* key=panel==1?L"ExplorerSmallIconsItemsPanel":
                               panel==2?L"ExplorerMediumIconsItemsPanel":
                               panel==3?L"ExplorerLargeIconsItemsPanel":
                                        L"ExplorerVerticalItemsPanel";
            try{
                view.ItemsPanel(RootShell().Resources().Lookup(
                    winrt::box_value(key)).as<ItemsPanelTemplate>());
                ActiveWindowTab().fileLists[side].appliedItemsPanel=panel;
            }catch(...){ }
        }
        if(details)ApplyDetailColumnLayout(side);
    }
    void MainWindow::UpdateSortPresentation(int side)
    {
        const int sort=ActiveWindowTab().fileLists[side].sortMode;
        auto decorate=[&](Button const& button,std::wstring label,int asc,int desc){
            if(sort==asc)label+=L" \u2191";else if(sort==desc)label+=L" \u2193";
            button.Content(winrt::box_value(hstring(label)));
            Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(button,hstring(label+L" \uC815\uB82C"));
        };
        if(side==0){
            decorate(LeftNameSortButton(),L"\uC774\uB984",0,1);decorate(LeftTypeSortButton(),L"\uC720\uD615",4,5);
            decorate(LeftSizeSortButton(),L"\uD06C\uAE30",6,2);decorate(LeftDateSortButton(),L"\uC218\uC815 \uB0A0\uC9DC",7,3);
        }else{
            decorate(RightNameSortButton(),L"\uC774\uB984",0,1);decorate(RightTypeSortButton(),L"\uC720\uD615",4,5);
            decorate(RightSizeSortButton(),L"\uD06C\uAE30",6,2);decorate(RightDateSortButton(),L"\uC218\uC815 \uB0A0\uC9DC",7,3);
        }
    }
    void MainWindow::OnHeaderSortClicked(IInspectable const& sender,RoutedEventArgs const&)
    {
        auto button=sender.try_as<Button>();if(!button||!button.Tag())return;
        const auto tag=std::wstring(winrt::unbox_value<hstring>(button.Tag()).c_str());
        if(tag.size()!=3||tag[1]!=L','||tag[0]<L'0'||tag[0]>L'1'||tag[2]<L'0'||tag[2]>L'3')return;
        const int side=tag[0]-L'0',column=tag[2]-L'0';if(ActiveWindowTab().model.activePane!=side)ActivatePane(side);
        const int current=ActiveWindowTab().fileLists[side].sortMode;int next=0;
        if(column==0)next=current==0?1:0;
        else if(column==1)next=current==4?5:4;
        else if(column==2)next=current==6?2:6;
        else next=current==7?3:7;
        UpdateSort(next);
    }

    void MainWindow::FillFiles(int side)
    {
        mPopulatingFileLists=true;
        UpdateViewPresentation(side);
        UpdateSortPresentation(side);
        auto view=side==0?LeftFiles():RightFiles();
        const auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
        const auto& session=pane.tabs[pane.active];
        const auto& snapshot=session.snapshot();
        const auto& items=snapshot.children;
        const auto& nameIndex=session.nameIndex();
        auto& state=ActiveWindowTab().fileLists[side];
        const auto nextRoute=pane.routeIds[pane.active];
        if(state.visibleRoute!=nextRoute||state.visibleTab!=pane.active){
            state.visibleRoute=nextRoute;
            state.visibleTab=pane.active;
            state.visibleCount=160;
            state.streamToComplete=false;
            state.indexToComplete=false;
            state.indexedNameSort=state.sortMode<=1;
            state.indexedNameProjection=false;
            state.fullModelLimitReached=false;
        }
        auto previous=side==0?LeftLoadPreviousButton():RightLoadPreviousButton();
        auto button=side==0?LeftLoadMoreButton():RightLoadMoreButton();
        std::vector<std::wstring> selected;
        for(auto const& old:view.SelectedItems()){
            auto row=old.try_as<ListViewItem>();
            if(!row||!row.Tag())continue;
            const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
            auto const& renderedState=ActiveWindowTab().fileLists[side];
            auto found=std::find(
                renderedState.renderedLogical.begin(),
                renderedState.renderedLogical.end(),logical);
            if(found!=renderedState.renderedLogical.end()){
                const auto position=static_cast<std::size_t>(
                    std::distance(renderedState.renderedLogical.begin(),found));
                if(position<renderedState.renderedPaths.size())
                    selected.push_back(renderedState.renderedPaths[position]);
            }
        }
        view.Items().Clear();
        state.renderedLogical.clear();
        state.renderedPaths.clear();
        state.renderedBaseOffset=snapshot.baseOffset;
        const bool metadataReady=state.metadataCurrent(
             pane.routeIds[pane.active],pane.active,items.size());
        const bool detailReady=state.isCurrent(
             pane.routeIds[pane.active],pane.active,items.size());
        const int mode=state.sortMode;
        const bool indexedProjection=
            state.indexedNameProjection&&!state.indexToComplete&&mode<=1&&
            session.indexedFrontier()==snapshot.nextOffset;
        const auto sourceCount=indexedProjection?nameIndex.size():items.size();
        std::vector<size_t> order(sourceCount);
        std::iota(order.begin(),order.end(),size_t{0});
        auto labelAt=[&](size_t index)->std::wstring const&{
            return indexedProjection?nameIndex[index].label:items[index].label;
        };
        auto parsingAt=[&](size_t index)->std::wstring const&{
            return indexedProjection?nameIndex[index].parsingName:
                                     items[index].parsingName;
        };
        auto folderAt=[&](size_t index)->bool{
            return indexedProjection?nameIndex[index].isFolder():
                                     items[index].isFolder();
        };
        auto logicalAt=[&](size_t index)->std::uint64_t{
            return indexedProjection?static_cast<std::uint64_t>(index):
                snapshot.logicalIndex(index);
        };
        auto residentAt=[&](size_t index,std::size_t& resident)->bool{
            if(!indexedProjection){resident=index;return true;}
            return snapshot.residentIndex(
                static_cast<std::uint64_t>(index),resident);
        };
        auto lessName=[&](size_t lhs,size_t rhs){
            const auto& a=labelAt(lhs);
            const auto& b=labelAt(rhs);
            return ::CompareStringOrdinal(
                a.c_str(),-1,b.c_str(),-1,TRUE)==CSTR_LESS_THAN;
        };
        if(mode<=1||metadataReady)
            std::stable_sort(order.begin(),order.end(),[&](size_t lhs,size_t rhs){
                if(folderAt(lhs)!=folderAt(rhs))return folderAt(lhs);
                if(metadataReady&&(mode==4||mode==5)){
                    const auto& a=state.metadata[lhs].typeKey;
                    const auto& b=state.metadata[rhs].typeKey;
                    const auto cmp=::CompareStringOrdinal(
                        a.c_str(),-1,b.c_str(),-1,TRUE);
                    if(cmp!=CSTR_EQUAL)
                        return mode==5?cmp==CSTR_GREATER_THAN:cmp==CSTR_LESS_THAN;
                }else if(metadataReady&&(mode==2||mode==6)){
                    const auto& x=state.metadata[lhs];
                    const auto& y=state.metadata[rhs];
                    if(x.sizeKnown!=y.sizeKnown)return x.sizeKnown;
                    if(x.sizeKnown&&x.bytes!=y.bytes)
                        return mode==2?x.bytes>y.bytes:x.bytes<y.bytes;
                }else if(metadataReady&&(mode==3||mode==7)){
                    const auto& x=state.metadata[lhs];
                    const auto& y=state.metadata[rhs];
                    if(x.dateKnown!=y.dateKnown)return x.dateKnown;
                    if(x.dateKnown&&x.modified!=y.modified)
                        return mode==3?x.modified>y.modified:x.modified<y.modified;
                }
                return mode==1?lessName(rhs,lhs):lessName(lhs,rhs);
            });
        if(!state.filenameFilter.empty()){
            order.erase(std::remove_if(order.begin(),order.end(),
                [&](size_t index){
                    return !fxfile::filterrules::Store::matches(
                        labelAt(index),state.filenameFilter);
                }),order.end());
        }
        state.filteredCount=order.size();
        const bool hasPrevious=
            !indexedProjection&&snapshot.baseOffset!=0&&!state.streamToComplete;
        const bool hasForward=indexedProjection?
            state.indexToComplete&&
                (snapshot.residentEndOffset()<snapshot.nextOffset||
                 snapshot.truncated):
            (snapshot.residentEndOffset()<snapshot.nextOffset||
             snapshot.truncated);
        const bool hasMore=order.size()>state.visibleCount||hasForward;
        previous.Visibility(hasPrevious?Visibility::Visible:Visibility::Collapsed);
        button.Visibility(hasMore?Visibility::Visible:Visibility::Collapsed);
        auto detailsHeader=side==0?LeftDetailsHeader():RightDetailsHeader();
        if(state.viewMode!=FileViewMode::Details)
            detailsHeader.Height((hasPrevious||hasMore)?24.0:0.0);
        const bool sequential=
            !indexedProjection&&state.filenameFilter.empty()&&mode==0;
        const auto shown=sequential?
            snapshot.baseOffset+(std::min)(order.size(),state.visibleCount):
            (std::min)(order.size(),state.visibleCount);
        const auto total=sequential?snapshot.nextOffset:order.size();
        const bool incomplete=indexedProjection?
            state.indexToComplete:
            (snapshot.baseOffset||
             snapshot.residentEndOffset()<snapshot.nextOffset||
             snapshot.truncated);
        const auto progress=std::to_wstring(shown)+
            L"/"+std::to_wstring(total)+(incomplete?L"+":L"");
        button.Content(winrt::box_value(hstring(progress)));
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
            previous,hstring(std::wstring(
               side==0?L"\uC67C\uCABD \uC774\uC804 \uD56D\uBAA9 \uCC3D, \uD604\uC7AC \uC2DC\uC791 ":
                       L"\uC624\uB978\uCABD \uC774\uC804 \uD56D\uBAA9 \uCC3D, \uD604\uC7AC \uC2DC\uC791 ")+
               std::to_wstring(snapshot.baseOffset+1)));
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
            button,hstring(std::wstring(
               side==0?L"\uC67C\uCABD \uB354 \uD45C\uC2DC ":L"\uC624\uB978\uCABD \uB354 \uD45C\uC2DC ")+progress));
        for(size_t visible=0;visible<(std::min)(order.size(),state.visibleCount);++visible){
            const auto index=order[visible];
            const auto logical=logicalAt(index);
            std::size_t resident=0;
            const bool residentReady=residentAt(index,resident);
            const auto& itemLabel=labelAt(index);
            const auto& itemParsing=parsingAt(index);
            const bool itemFolder=folderAt(index);
            auto const* meta=residentReady&&detailReady?
                &state.details[resident]:nullptr;
            ListViewItem row;
            auto label=std::wstring(itemFolder?L"[폴더]  ":L"[파일]  ")+
                       itemLabel;
            if(meta){
                if(!meta->typeLabel.empty())label+=L"   |   "+meta->typeLabel;
                if(meta->sizeKnown)label+=L"   |   "+meta->bytesLabel;
                if(meta->dateKnown)label+=L"   |   "+meta->dateLabel;
            }
            if(state.viewMode==FileViewMode::Details){
            Grid columns;
            const auto widths=DetailColumnWidths(side);
            const int detailProfile=DetailLayoutProfile();
            const auto displayNameWidth=detailProfile>=2?
                (detailProfile==2?(std::min)(ActiveWindowTab().fileLists[side].nameColumnWidth,168.0):ActiveWindowTab().fileLists[side].nameColumnWidth):168.0;
            auto addColumn=[&](GridLength const& width){
                ColumnDefinition def;def.Width(width);columns.ColumnDefinitions().Append(def);
            };
            for(auto const& width:widths)addColumn(width);
            StackPanel nameCell;
            nameCell.Orientation(Orientation::Horizontal);
            nameCell.Spacing(7);
            nameCell.VerticalAlignment(VerticalAlignment::Center);
            bool localDrive=false;
            ULARGE_INTEGER freeBytes{},totalBytes{},freeTotal{};
            const auto& parsing=itemParsing;
            if(parsing.size()==3&&parsing[1]==L':'&&
               (parsing[2]==L'\\'||parsing[2]==L'/')){
                const auto driveType=::GetDriveTypeW(parsing.c_str());
                if((driveType==DRIVE_FIXED||driveType==DRIVE_REMOVABLE)&&
                   ::GetDiskFreeSpaceExW(parsing.c_str(),&freeBytes,
                                         &totalBytes,&freeTotal)&&
                   totalBytes.QuadPart>0)
                    localDrive=true;
            }
            auto const* iconMeta=meta;
            bool actualVisual=false;
            if(iconMeta){
                const auto& data=iconMeta->iconBgra;
                const int width=static_cast<int>(iconMeta->iconWidth);
                const int height=static_cast<int>(iconMeta->iconHeight);
                if(width>=16&&height>=16&&
                   data.size()==static_cast<size_t>(width)*height*4){
                    try{
                        Microsoft::UI::Xaml::Media::Imaging::WriteableBitmap pixels(
                            width,height);
                        auto backing=pixels.PixelBuffer();
                        winrt::com_ptr<::Windows::Storage::Streams::IBufferByteAccess>
                            access;
                        if(SUCCEEDED(reinterpret_cast<::IUnknown*>(
                            winrt::get_abi(backing))->QueryInterface(
                                __uuidof(::Windows::Storage::Streams::IBufferByteAccess),
                                access.put_void()))){
                            BYTE* target=nullptr;
                            if(SUCCEEDED(access->Buffer(&target))&&target){
                                std::memcpy(target,data.data(),data.size());
                                pixels.Invalidate();
                                Image image;
                                image.Source(pixels);
                                image.Width(16);image.Height(16);
                                Microsoft::UI::Xaml::Automation::AutomationProperties::
                                    SetName(image,itemFolder?
                                        (iconMeta->knownFolderVisual?
                                            L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):
                                        L"Windows system registered file icon");
                                nameCell.Children().Append(image);
                                actualVisual=true;
                            }
                        }
                    }catch(...){actualVisual=false;}
                }
            }
            if(!actualVisual){
                FontIcon glyph;
                glyph.FontFamily(Microsoft::UI::Xaml::Media::FontFamily{
                    L"Segoe Fluent Icons"});
                glyph.Glyph(hstring(localDrive?L"\uEDA2":
                    itemFolder?L"\uE8B7":L"\uE8A5"));
                glyph.FontSize(localDrive?20.0:16.0);
                nameCell.Children().Append(glyph);
            }
            TextBlock filename;
            filename.Text(itemLabel);
            filename.TextTrimming(TextTrimming::CharacterEllipsis);
            if(localDrive){
                StackPanel drive;
                drive.Spacing(2);
                drive.Children().Append(filename);
                ProgressBar usage;
                usage.Width((std::max)(115.0,
                    displayNameWidth-42.0));
                usage.Height(3);
                usage.Minimum(0);usage.Maximum(100);
                const auto used=totalBytes.QuadPart-freeBytes.QuadPart;
                usage.Value(static_cast<double>(used)*100.0/
                            static_cast<double>(totalBytes.QuadPart));
                drive.Children().Append(usage);
                TextBlock capacity;
                capacity.FontSize(10.0);
                capacity.Opacity(0.62);
                const auto gib=1024ull*1024ull*1024ull;
                capacity.Text(hstring(std::to_wstring(
                    freeBytes.QuadPart/gib)+L" GB 사용 가능 / "+
                    std::to_wstring(totalBytes.QuadPart/gib)+L" GB"));
                drive.Children().Append(capacity);
                nameCell.Children().Append(drive);
                row.MinHeight(58);
            }else nameCell.Children().Append(filename);
            Grid::SetColumn(nameCell,0);
            columns.Children().Append(nameCell);
            auto addText=[&](std::wstring const& text,int col){
                TextBlock field;
                field.Text(hstring(text));
                field.TextTrimming(TextTrimming::CharacterEllipsis);
                Grid::SetColumn(field,col);
                columns.Children().Append(field);
            };
            addText(meta?meta->typeLabel:L"",1);
            addText(meta&&meta->sizeKnown?meta->bytesLabel:L"",2);
            addText(meta&&meta->dateKnown?meta->dateLabel:L"",3);
            row.Content(columns);
            }else{
                const bool medium=state.viewMode==FileViewMode::MediumIcons;
                const bool large=state.viewMode==FileViewMode::LargeIcons;
                const bool iconGrid=medium||large;
                const bool smallIcons=state.viewMode==FileViewMode::SmallIcons;
                StackPanel cell;cell.Orientation(iconGrid?Orientation::Vertical:Orientation::Horizontal);
                cell.Spacing(large?7.0:(medium?5.0:7.0));cell.VerticalAlignment(VerticalAlignment::Center);
                if(iconGrid)cell.HorizontalAlignment(HorizontalAlignment::Center);
                auto const* iconMeta=detailReady?&ActiveWindowTab().fileLists[side].details[index]:nullptr;
                bool actualVisual=false;bool realThumb=false;
                if(iconMeta){
                    const auto& thumb=iconMeta->thumbnailBgra;
                    realThumb=iconMeta->thumbnailWidth>=16&&iconMeta->thumbnailWidth<=128&&iconMeta->thumbnailHeight>=16&&iconMeta->thumbnailHeight<=128&&thumb.size()==static_cast<size_t>(iconMeta->thumbnailWidth)*iconMeta->thumbnailHeight*4;
                    const auto& data=iconGrid&&realThumb?thumb:iconMeta->iconBgra;
                    const int width=iconGrid&&realThumb?static_cast<int>(iconMeta->thumbnailWidth):
                        static_cast<int>(iconMeta->iconWidth);
                    const int height=iconGrid&&realThumb?static_cast<int>(iconMeta->thumbnailHeight):
                        static_cast<int>(iconMeta->iconHeight);
                    if(data.size()==static_cast<size_t>(width)*height*4){
                        try{
                            Microsoft::UI::Xaml::Media::Imaging::WriteableBitmap pixels(width,height);auto backing=pixels.PixelBuffer();
                            winrt::com_ptr<::Windows::Storage::Streams::IBufferByteAccess> access;
                            if(SUCCEEDED(reinterpret_cast<::IUnknown*>(winrt::get_abi(backing))->QueryInterface(__uuidof(::Windows::Storage::Streams::IBufferByteAccess),access.put_void()))){
                                BYTE* target=nullptr;if(SUCCEEDED(access->Buffer(&target))&&target){
                                    std::memcpy(target,data.data(),data.size());pixels.Invalidate();Image image;image.Source(pixels);
                                    const double targetSize=large?64.0:(medium?(realThumb?40.0:32.0):(smallIcons?20.0:16.0));image.Width(targetSize);image.Height(targetSize);
                                    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(image,realThumb?L"Windows Shell image thumbnail":
                                        itemFolder?(iconMeta->knownFolderVisual?L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):L"Windows system registered file icon");
                                    cell.Children().Append(image);actualVisual=true;
                                }
                            }
                        }catch(...){actualVisual=false;}
                    }
                }
                if(!actualVisual){
                    FontIcon glyph;glyph.FontFamily(Microsoft::UI::Xaml::Media::FontFamily{L"Segoe Fluent Icons"});
                    glyph.Glyph(hstring(itemFolder?L"\uE8B7":L"\uE8A5"));glyph.FontSize(large?60.0:(medium?36.0:(smallIcons?20.0:16.0)));cell.Children().Append(glyph);
                }
                TextBlock filename;filename.Text(itemLabel);
                if(iconGrid){filename.FontSize(12.0);filename.Width(large?104.0:84.0);filename.TextAlignment(TextAlignment::Center);filename.TextWrapping(TextWrapping::WrapWholeWords);filename.MaxLines(2);filename.TextTrimming(TextTrimming::CharacterEllipsis);}
                else{filename.TextTrimming(TextTrimming::CharacterEllipsis);if(smallIcons){filename.FontSize(12.0);filename.Width(120);}}
                cell.Children().Append(filename);row.Content(cell);
                if(state.viewMode==FileViewMode::List){row.MinHeight(32);row.Padding(Thickness{5.0,0.0,5.0,0.0});}
                else if(smallIcons){row.Width(160);row.Height(32);row.Padding(Thickness{5.0,0.0,5.0,0.0});}
                else if(large){row.Width(112);row.Height(128);row.Padding(Thickness{2.0});row.HorizontalContentAlignment(HorizontalAlignment::Center);}
                else{row.Width(92);row.Height(92);row.Padding(Thickness{2.0});row.HorizontalContentAlignment(HorizontalAlignment::Center);}
            }
            Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
                row,hstring(label));
            row.Tag(winrt::box_value(logical));
            const auto weak=get_weak();
            row.Tapped([weak,side](IInspectable const&,
                Microsoft::UI::Xaml::Input::TappedRoutedEventArgs const&){
                if(auto ui=weak.get()){
                    if(ui->ActiveWindowTab().model.activePane!=side)ui->ActivatePane(side);
                    ui->QueueSelectionPresentationUpdate();
                }
            });
            row.KeyDown([weak,side](IInspectable const&,
                Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){
                if(args.Key()!=Windows::System::VirtualKey::Enter)return;
                if(auto ui=weak.get())ui->OpenSelectedFolder(side);
                args.Handled(true);
            });
            row.CanDrag(true);
            using Microsoft::UI::Xaml::Input::PointerEventHandler;
            row.AddHandler(UIElement::PointerPressedEvent(),
                box_value(PointerEventHandler{[weak,side](
                    IInspectable const& sender,
                    Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const& args){
                    if(auto ui=weak.get())
                        ui->OnFileRowPointerPressed(side,sender,args);
                }}),true);
            row.AddHandler(UIElement::PointerReleasedEvent(),
                box_value(PointerEventHandler{[weak,side](
                    IInspectable const& sender,
                    Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const& args){
                    if(auto ui=weak.get())
                        ui->OnFileRowPointerReleased(side,sender,args);
                }}),true);
            row.AddHandler(UIElement::PointerCanceledEvent(),
                box_value(PointerEventHandler{[weak,side](
                    IInspectable const& sender,
                    Microsoft::UI::Xaml::Input::PointerRoutedEventArgs const& args){
                    if(auto ui=weak.get())
                        ui->OnFileRowPointerReleased(side,sender,args);
                }}),true);
            row.DragStarting([weak,side](
                Microsoft::UI::Xaml::UIElement const& sender,
                Microsoft::UI::Xaml::DragStartingEventArgs const& args){
                if(auto ui=weak.get())ui->OnFileRowDragStarting(side,sender,args);
            });
            view.Items().Append(row);
            state.renderedLogical.push_back(logical);
            state.renderedPaths.push_back(itemParsing);
            if(!itemParsing.empty()&&
               std::find(selected.begin(),selected.end(),itemParsing)
                  !=selected.end()){
                // Restore selection by native parsing path, never stale
                // pre-sort row index (including real multiple selection).
                if(side!=ActiveWindowTab().model.activePane)row.Opacity(0.78);
                view.SelectedItems().Append(row);
            }
        }
        mPopulatingFileLists=false;
    }
    std::wstring MainWindow::WindowTabLabel(
        fxfile::previewtabs::WindowTabState const& state) const
    {
        const int side=state.model.activePane;
        auto const& pane=state.model.panes[side];
        if(pane.active<pane.tabs.size()){
            auto const& snap=pane.tabs[pane.active].snapshot();
            if(!snap.displayName.empty())return snap.displayName;
            if(!snap.parsingName.empty()){
                try{
                    auto name=std::filesystem::path(snap.parsingName).filename().native();
                    if(!name.empty())return name;
                }catch(...){ }
            }
        }
        return L"새 창 탭";
    }
    void MainWindow::RefreshWindowTabs()
    {
        if(mSuppressWindowTabRefresh)return;
        std::vector<std::wstring> labels;labels.reserve(mWorkspace.count());
        for(auto const& state:mWorkspace.states())labels.push_back(WindowTabLabel(state));
        winrt::get_self<winrt::FlyExplorer::implementation::ShellHeader>(HeaderView())
            ->SetWindowTabs(labels,static_cast<int>(mWorkspace.activeIndex()));
    }
    void MainWindow::ReleaseWindowTabRoutes(
        fxfile::previewtabs::WindowTabState& state)
    {
        mShellNavigation->release(state.model);
        for(int side=0;side<2;++side)state.fileLists[side].invalidate();
    }
    void MainWindow::SuspendActiveWindowTab()
    {
        mSearchController.invalidate();
        auto& state=ActiveWindowTab();
        mShellNavigation->suspend(state.model);
        for(int side=0;side<2;++side){
            mFileDetails.cancel(side);
            state.fileLists[side].invalidate();
            mWorkspaceRestore.reset(side);
        }
        if(state.model.split){
            try{
                const auto total=PrimaryColumn().ActualWidth()+SecondaryColumn().ActualWidth();
                if(total>1)state.splitPermille=static_cast<std::uint32_t>(
                    (std::clamp)(PrimaryColumn().ActualWidth()/total*1000.,300.,700.));
            }catch(...){ }
        }
    }
    void MainWindow::ApplyActiveWindowTab(hstring const& status)
    {
        auto& state=ActiveWindowTab();
        const bool split=state.model.split;
        SecondaryPane().Visibility(split?Visibility::Visible:Visibility::Collapsed);
        PaneDivider().Visibility(split?Visibility::Visible:Visibility::Collapsed);
        const auto ratio=static_cast<double>((std::clamp)(state.splitPermille,300u,700u));
        PrimaryColumn().Width(GridLength{split?ratio:1000.0,GridUnitType::Star});
        SecondaryColumn().Width(split?GridLength{1000.0-ratio,GridUnitType::Star}:
            GridLength{0.0,GridUnitType::Pixel});
        const auto splitLabel=hstring(split?L"\uB2E8\uC77C \uCC3D":L"\uBD84\uD560 \uCC3D");
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(SplitButton(),splitLabel);
        ToolTipService::SetToolTip(SplitButton(),winrt::box_value(splitLabel));
        mDetailLayoutProfiles={{-1,-1}};
        Refresh(status);
        for(int side=0;side<2;++side){
            if(side==1&&!split)continue;
            auto& pane=state.model.panes[side];
            auto const& current=pane.tabs[pane.active].snapshot();
            if(current.folder.valid()){
                QueuePidl(side,fxfile::shellnav::Location(current.folder),
                    fxfile::shellnav::NavigationAction::Refresh);
            }
        }
    }
    bool MainWindow::CreateWindowTab(std::wstring const& startPath)
    {
        if(!mWorkspace.canCreate())return false;
        SuspendActiveWindowTab();
        if(!mWorkspace.create())return false;
        const auto defaultView=static_cast<FileViewMode>(
            (std::clamp)(mPreferencesCoordinator.current().defaultViewMode,0,3));
        for(auto& list:ActiveWindowTab().fileLists)list.viewMode=defaultView;
        ApplyActiveWindowTab(L"새 창 탭을 준비하는 중입니다.");
        const auto seed=startPath.empty()?HomePath().native():startPath;
        QueuePath(0,seed);
        QueuePath(1,seed);
        return true;
    }
    bool MainWindow::ActivateWindowTab(std::size_t index)
    {
        if(index>=mWorkspace.count())return false;
        if(mWorkspace.isActive(index))return true;
        SuspendActiveWindowTab();
        if(!mWorkspace.activate(index))return false;
        ApplyActiveWindowTab(L"창 탭을 전환했습니다.");
        return true;
    }
    bool MainWindow::CloseWindowTab(std::size_t index)
    {
        if(mWorkspace.count()<=1||index>=mWorkspace.count())return false;
        const bool closingActive=mWorkspace.isActive(index);
        if(closingActive)SuspendActiveWindowTab();
        ReleaseWindowTabRoutes(mWorkspace.state(index));
        if(!mWorkspace.close(index))return false;
        if(closingActive)ApplyActiveWindowTab(L"창 탭을 닫았습니다.");
        else RefreshWindowTabs();
        return true;
    }
    void MainWindow::Refresh(hstring const& status)
    {
        RefreshTabs(0);
        RefreshTabs(1);
        FillFiles(0);
        FillFiles(1);
        auto& nav=Current();
        const auto address=nav.snapshot().parsingName;
        AddressBox().Text(hstring(FriendlyAddress(address)));
        UpdateBreadcrumb(address);
        BackButton().IsEnabled(nav.canBack() && !ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].pending[ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].pending[ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].active]);
        UpButton().IsEnabled(nav.snapshot().folder.valid() && !ILIsEmpty(nav.snapshot().folder.get()));
        ActivePaneText().Text(ActiveWindowTab().model.activePane==0?L"활성: 왼쪽":L"활성: 오른쪽");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(ActiveWindowTab().model.activePane==0?L"왼쪽 창 (활성)":L"왼쪽 창")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(ActiveWindowTab().model.activePane==1?L"오른쪽 창 (활성)":L"오른쪽 창")));
        UpdateActivePaneChrome();
        UpdateSelectionChrome();
        UpdateFooterSummary();
        fileBar()->SetSortIndex(ActiveWindowTab().fileLists[ActiveWindowTab().model.activePane].sortMode);
        fileBar()->SetViewIndex(static_cast<int>(ActiveWindowTab().fileLists[ActiveWindowTab().model.activePane].viewMode));
        UpdateSortPresentation(ActiveWindowTab().model.activePane);
        StatusText().Text(status);
        Title(L"flyExplorer · "+hstring(nav.snapshot().displayName));
        RefreshWindowTabs();
        UpdateWatch(0);
        UpdateWatch(1);
        ScheduleFileMetadata(0);
        ScheduleFileMetadata(1);
        ScheduleFileDetails(0);
        ScheduleFileDetails(1);
    }
    bool MainWindow::OpenFolder(std::wstring const& path)
    {
        if(path.empty())return false;
        mWorkspaceRestore.reset(ActiveWindowTab().model.activePane);
        QueuePath(ActiveWindowTab().model.activePane,path);
        return true;
    }
    void MainWindow::ActivatePane(int side)
    {
        if(!mWorkspace.dispatch(fxfile::explorerui::Command::ActivatePane,side)
                    .accepted)return;
        mSearchController.invalidate();
        const auto& nav=Current();
        const auto address=nav.snapshot().parsingName;
        AddressBox().Text(hstring(FriendlyAddress(address)));
        UpdateBreadcrumb(address);
        BackButton().IsEnabled(nav.canBack() && !ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].pending[ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].active]);
        ForwardButton().IsEnabled(nav.canForward() && !ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].pending[ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane].active]);
        UpButton().IsEnabled(nav.snapshot().folder.valid() && !ILIsEmpty(nav.snapshot().folder.get()));
        ActivePaneText().Text(side==0?L"활성: 왼쪽":L"활성: 오른쪽");
        PrimaryPaneTitle().Content(winrt::box_value(
            hstring(side==0?L"왼쪽 창 (활성)":L"왼쪽 창")));
        SecondaryPaneTitle().Content(winrt::box_value(
            hstring(side==1?L"오른쪽 창 (활성)":L"오른쪽 창")));
        UpdateActivePaneChrome();
        fileBar()->SetSortIndex(ActiveWindowTab().fileLists[side].sortMode);
        fileBar()->SetViewIndex(static_cast<int>(ActiveWindowTab().fileLists[side].viewMode));
        UpdateSortPresentation(side);
        UpdateSelectionChrome();
        UpdateFooterSummary();
        Title(L"flyExplorer · "+hstring(nav.snapshot().displayName));
    }
    void MainWindow::UpdateActivePaneChrome()
    {
        const bool left=ActiveWindowTab().model.activePane==0;
        PrimaryPane().BorderThickness(Thickness{0.0,2.0,0.0,0.0});
        SecondaryPane().BorderThickness(Thickness{0.0,2.0,0.0,0.0});
        PrimaryPane().Opacity(1.0);
        SecondaryPane().Opacity(1.0);
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
            PrimaryPane(),left?L"왼쪽 창 (활성)":L"왼쪽 창");
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
            SecondaryPane(),left?L"오른쪽 창":L"오른쪽 창 (활성)");
        try{
            auto resources=Application::Current().Resources();
            auto accent=resources.Lookup(winrt::box_value(
                L"SystemControlHighlightAccentBrush")).try_as<
                    Microsoft::UI::Xaml::Media::Brush>();
            auto normal=resources.Lookup(winrt::box_value(
                L"SystemControlForegroundBaseLowBrush")).try_as<
                    Microsoft::UI::Xaml::Media::Brush>();
            if(normal){
                PrimaryPane().BorderBrush(left&&accent?accent:normal);
                SecondaryPane().BorderBrush(!left&&accent?accent:normal);
            }
        }catch(...){ }
    }
    void MainWindow::UpdateSelectionChrome()
    {
        for(int side=0;side<2;++side){
            auto view=side==0?LeftFiles():RightFiles();
            for(auto const& item:view.Items()){
                if(auto row=item.try_as<ListViewItem>())row.Opacity(1.0);
            }
            if(side!=ActiveWindowTab().model.activePane){
                for(auto const& item:view.SelectedItems()){
                    if(auto row=item.try_as<ListViewItem>())row.Opacity(0.78);
                }
            }
        }
    }
    void MainWindow::UpdateCommandAvailability()
    {
        // Keep selection commands reachable to keyboard/UIA selection patterns.
        // Each command validates the current native selection before mutating.
        const bool ready=!mFileOperations.busy();
        fileBar()->WindowsCutButton().IsEnabled(ready);
        fileBar()->WindowsCopyButton().IsEnabled(ready);
        RenameButton().IsEnabled(ready);
        fileBar()->RecycleButton().IsEnabled(ready);
        fileBar()->CopyButton().IsEnabled(ready);
        fileBar()->MoveButton().IsEnabled(ready);
    }
    void MainWindow::UpdateFooterSummary()
    {
        const int side=ActiveWindowTab().model.activePane;
        auto view=side==0?LeftFiles():RightFiles();
        const auto& pane=ActiveWindowTab().model.panes[side];
        const auto& state=ActiveWindowTab().fileLists[side];
        auto const& snapshot=pane.tabs[pane.active].snapshot();
        std::size_t count=snapshot.children.size();
        bool incomplete=snapshot.truncated;
        if(state.visibleRoute==pane.routeIds[pane.active]&&state.visibleTab==pane.active){
            const auto& session=pane.tabs[pane.active];
            const bool indexedComplete=
                state.indexedNameProjection&&!state.indexToComplete&&
                session.indexedFrontier()==snapshot.nextOffset;
            if(state.filenameFilter.empty()){
                count=snapshot.nextOffset;
                if(indexedComplete)incomplete=false;
            }else{
                count=state.filteredCount;
                incomplete=indexedComplete?false:
                    incomplete||snapshot.baseOffset||
                    snapshot.residentEndOffset()<snapshot.nextOffset;
            }
        }
        const auto selected=view.SelectedItems().Size();
        ItemCountText().Text(hstring(
            std::to_wstring(count)+(incomplete?L"+\uAC1C \uD56D\uBAA9":L"\uAC1C \uD56D\uBAA9")));
        SelectionCountText().Text(selected?
            hstring(std::to_wstring(selected)+L"\uAC1C \uC120\uD0DD\uB428"):hstring{});
        UpdateCommandAvailability();
    }
    void MainWindow::QueueSelectionPresentationUpdate()
    {
        const auto weak=get_weak();
        DispatcherQueue().TryEnqueue([weak]{
            if(auto ui=weak.get()){
                ui->UpdateSelectionChrome();
                ui->UpdateFooterSummary();
            }
        });
    }
    void MainWindow::OnFileSelectionChanged(IInspectable const& sender,
        SelectionChangedEventArgs const&)
    {
        if(mPopulatingFileLists)return;
        auto view=sender.try_as<ListView>();
        if(!view)return;
        UpdateSelectionChrome();
        if((view==LeftFiles()&&ActiveWindowTab().model.activePane==0)||
           (view==RightFiles()&&ActiveWindowTab().model.activePane==1))
            UpdateFooterSummary();
    }
    void MainWindow::OnFileSelectionKeyUp(IInspectable const&,
        Input::KeyRoutedEventArgs const&)
    {
        QueueSelectionPresentationUpdate();
    }
    void MainWindow::ToggleNameFilter(int side)
    {
        auto box=side==0?LeftNameFilterBox():RightNameFilterBox();
        const bool show=box.Opacity()<0.5;
        if(show){
            box.Width(125);box.Height(32);box.Opacity(1.0);
            box.IsHitTestVisible(true);box.IsTabStop(true);
            box.Focus(FocusState::Programmatic);box.SelectAll();
            StatusText().Text(side==0?L"왼쪽 이름 필터를 표시했습니다.":L"오른쪽 이름 필터를 표시했습니다.");
        }else{
            box.Text(L"");box.Width(1);box.Height(1);box.Opacity(0.0);
            box.IsHitTestVisible(false);box.IsTabStop(false);
            StatusText().Text(L"이름 필터를 닫았습니다.");
        }
    }
    void MainWindow::OnBackClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canBack()) {
            StatusText().Text(L"이 탭에 이전 폴더가 없습니다.");return;
        }
        QueuePidl(ActiveWindowTab().model.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Back),
            fxfile::shellnav::NavigationAction::Back);
    }
    void MainWindow::OnForwardClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!Current().canForward()) {
            StatusText().Text(L"이 탭에 다음 폴더가 없습니다.");return;
        }
        QueuePidl(ActiveWindowTab().model.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Forward),
            fxfile::shellnav::NavigationAction::Forward);
    }
    void MainWindow::OnUpClicked(IInspectable const&,RoutedEventArgs const&)
    {
        QueuePidl(ActiveWindowTab().model.activePane,Current().target(
            fxfile::shellnav::HistoryAction::Up),
            fxfile::shellnav::NavigationAction::Up);
    }
    void MainWindow::OnAddressKeyDown(IInspectable const&,
                                     Input::KeyRoutedEventArgs const& args)
    {
        if (args.Key()==Windows::System::VirtualKey::Enter) {
            OpenFolder(ResolveFriendlyAddress(std::wstring(AddressBox().Text().c_str())));
            AddressBox().Opacity(0.0);
            AddressDisplayButton().Visibility(Visibility::Visible);
            args.Handled(true);
        }
        else if (args.Key()==Windows::System::VirtualKey::Escape) {
            const auto address=Current().snapshot().parsingName;
            AddressBox().Text(hstring(FriendlyAddress(address)));
            UpdateBreadcrumb(address);
            AddressBox().Opacity(0.0);
            AddressDisplayButton().Visibility(Visibility::Visible);
            StatusText().Text(L"주소 입력을 취소했습니다.");
            args.Handled(true);
        }
    }
    void MainWindow::OnAddressGotFocus(IInspectable const&,RoutedEventArgs const&)
    {
        AddressDisplayButton().Visibility(Visibility::Collapsed);
        AddressBox().Opacity(1.0);
        AddressBox().SelectAll();
    }
    void MainWindow::OnAddressLostFocus(IInspectable const&,RoutedEventArgs const&)
    {
        const auto address=Current().snapshot().parsingName;
        AddressBox().Text(hstring(FriendlyAddress(address)));
        UpdateBreadcrumb(address);
        AddressBox().Opacity(0.0);
        AddressDisplayButton().Visibility(Visibility::Visible);
    }
    void MainWindow::OnAddressDisplayClicked(IInspectable const&,RoutedEventArgs const&)
    {
        AddressDisplayButton().Visibility(Visibility::Collapsed);
        AddressBox().Opacity(1.0);
        AddressBox().Focus(FocusState::Programmatic);
        AddressBox().SelectAll();
    }
    void MainWindow::UpdateBreadcrumb(std::wstring const& address)
    {
        auto panel=BreadcrumbPanel();panel.Children().Clear();
        struct Segment{std::wstring label,target;};std::vector<Segment> segments;
        const auto friendly=FriendlyAddress(address);
        if(address.rfind(L"shell:",0)==0||friendly!=address){segments.push_back({friendly,address});}
        else{
            try{
                std::filesystem::path built;
                for(auto const& part:std::filesystem::path(address)){
                    built/=part;auto label=part.native();
                    while(label.size()>1&&(label.back()==L'\\'||label.back()==L'/'))label.pop_back();
                    if(!label.empty())segments.push_back({label,built.native()});
                }
            }catch(...){segments.push_back({friendly,address});}
        }
        auto add=[&](Segment const& seg,bool current){
            Button button;button.Height(28);button.MinWidth(0);button.Padding(Thickness{6.0,0.0,6.0,0.0});
            button.CornerRadius(CornerRadius{4.0});button.BorderThickness(Thickness{0.0});button.Background(nullptr);
            button.Content(winrt::box_value(hstring(seg.label)));button.Tag(winrt::box_value(hstring(seg.target)));
            button.FontWeight(current?Windows::UI::Text::FontWeights::SemiBold():Windows::UI::Text::FontWeights::Normal());
            Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(button,L"\uC8FC\uC18C \uACBD\uB85C: "+hstring(seg.label));
            button.Click({this,&MainWindow::OnBreadcrumbSegmentClicked});panel.Children().Append(button);
        };
        auto separator=[&](){TextBlock glyph;glyph.Text(L"\u203A");glyph.Opacity(0.52);glyph.VerticalAlignment(VerticalAlignment::Center);panel.Children().Append(glyph);};
        if(segments.empty())segments.push_back({friendly,address});
        if(segments.size()>4){
            add(segments.front(),false);separator();
            Segment ellipsis{L"\u2026",segments[segments.size()-4].target};add(ellipsis,false);separator();
            for(size_t i=segments.size()-3;i<segments.size();++i){add(segments[i],i+1==segments.size());if(i+1<segments.size())separator();}
        }else for(size_t i=0;i<segments.size();++i){add(segments[i],i+1==segments.size());if(i+1<segments.size())separator();}
    }
    void MainWindow::OnBreadcrumbSegmentClicked(IInspectable const& sender,RoutedEventArgs const&)
    {
        auto button=sender.try_as<Button>();if(!button||!button.Tag())return;
        OpenFolder(std::wstring(winrt::unbox_value<hstring>(button.Tag()).c_str()));
    }
    void MainWindow::OnQuickSearchKeyDown(IInspectable const&,
        Input::KeyRoutedEventArgs const& args)
    {
        if(args.Key()!=Windows::System::VirtualKey::Enter)return;
        const auto term=std::wstring(QuickSearchBox().Text().c_str());
        if(term.empty()){
            StatusText().Text(L"검색어를 입력하세요.");
            args.Handled(true);
            return;
        }
        auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(ActiveWindowTab().model.activePane)];
        const auto& path=pane.filesystemPaths[pane.active];
        if(path.empty()){
            StatusText().Text(L"현재 파일 시스템 폴더에서만 빠른 검색을 실행할 수 있습니다.");
            args.Handled(true);
            return;
        }
        WorkspacePanel().Visibility(Visibility::Collapsed);
        SearchPanel().Visibility(Visibility::Visible);
        SearchScopeBox().Text(hstring(path));
        SearchTermBox().Text(hstring(term));
        EnsureExpandedPanelFits();
        OnRunSearch(nullptr,nullptr);
        args.Handled(true);
    }
    void MainWindow::OnShellSizeChanged(IInspectable const&,
        SizeChangedEventArgs const& args)
    {
        const auto width=args.NewSize().Width;mShellWidth=width;
        NavigationColumn().Width(GridLength{width<1040?156.0:188.0,GridUnitType::Pixel});
        QuickSearchBox().Width(width<820?120.0:(width<1060?150.0:220.0));
        const int profile=DetailLayoutProfile();
        for(int side=0;side<2;++side){
            if(mDetailLayoutProfiles[side]!=profile){
                mDetailLayoutProfiles[side]=profile;
                if(mColumnControlsReady&&!ActiveWindowTab().model.panes[side].tabs.empty())FillFiles(side);
            }else ApplyDetailColumnLayout(side);
        }
    }
    void MainWindow::OnNewTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(ActiveWindowTab().model.activePane)];
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
        if(!mWorkspace.dispatch(fxfile::explorerui::Command::AddTab,
                            ActiveWindowTab().model.activePane).accepted)return;
        QueuePidl(ActiveWindowTab().model.activePane,std::move(start),
                  fxfile::shellnav::NavigationAction::Open);
        Refresh(L"새 탭의 폴더를 불러오는 중입니다.");
    }
    void MainWindow::OnCloseTabClicked(IInspectable const&,RoutedEventArgs const&)
    {
        auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(ActiveWindowTab().model.activePane)];
        if (pane.tabs.size()<=1) {
            StatusText().Text(L"각 창에는 탭을 최소 한 개 유지해야 합니다.");
            return;
        }
        const auto change=mWorkspace.dispatch(
            fxfile::explorerui::Command::CloseTab,ActiveWindowTab().model.activePane);
        if(!change.accepted)return;
        mSearchController.invalidate();
        mShellNavigation->forget(change.releasedRoute);
        mWorkspaceRestore.reset(ActiveWindowTab().model.activePane);
        Refresh(L"탭을 닫았습니다.");
    }
    void MainWindow::OnSplitClicked(IInspectable const&,RoutedEventArgs const&)
    {
        if(!mWorkspace.dispatch(fxfile::explorerui::Command::ToggleSplit)
                  .accepted)return;
        SecondaryPane().Visibility(ActiveWindowTab().model.split?Visibility::Visible:Visibility::Collapsed);
        PaneDivider().Visibility(ActiveWindowTab().model.split?Visibility::Visible:Visibility::Collapsed);
        SecondaryColumn().Width(ActiveWindowTab().model.split?
            GridLength{1.0,GridUnitType::Star}:GridLength{0.0,GridUnitType::Pixel});
        auto splitButton=SplitButton();
        auto splitLabel=hstring(ActiveWindowTab().model.split?
            L"\uB2E8\uC77C \uCC3D":L"\uBD84\uD560 \uCC3D");
        Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
            splitButton,splitLabel);
        ToolTipService::SetToolTip(splitButton,winrt::box_value(splitLabel));
        Refresh(ActiveWindowTab().model.split?L"두 창이 독립적으로 열렸습니다.":L"단일 창으로 표시합니다. 다른 창의 상태는 유지됩니다.");
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
        auto& pane=ActiveWindowTab().model.panes[0];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        // WinUI raises deferred SelectionChanged for programmatic strip
        // rebuilds. Only a DIFFERENT selected tab is user navigation.
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        if(!mWorkspace.dispatch(fxfile::explorerui::Command::SelectTab,0,
                 static_cast<size_t>(view.SelectedIndex())).accepted)return;
        mSearchController.invalidate();
        Refresh(L"왼쪽 탭을 선택했습니다.");
    }
    void MainWindow::OnRightTabSelectionChanged(
        IInspectable const& sender,SelectionChangedEventArgs const&)
    {
        auto view=sender.as<TabView>();
        if (mPopulatingTabs || view.SelectedIndex()<0 || !ActiveWindowTab().model.split)return;
        auto& pane=ActiveWindowTab().model.panes[1];
        if (static_cast<size_t>(view.SelectedIndex())>=pane.tabs.size())return;
        if (static_cast<size_t>(view.SelectedIndex())==pane.active)return;
        if(!mWorkspace.dispatch(fxfile::explorerui::Command::SelectTab,1,
                 static_cast<size_t>(view.SelectedIndex())).accepted)return;
        mSearchController.invalidate();
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
        const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
        auto& session=Current();
        auto const* indexed=session.indexedItem(
            static_cast<std::size_t>(logical));
        if(!indexed||!indexed->isFolder())return;
        const auto& snapshot=session.snapshot();
        std::size_t resident=0;
        if(snapshot.residentIndex(logical,resident)){
            const auto& entries=snapshot.children;
            // The native engine CLONES this original absolute Shell PIDL
            // before updating session state; no dangling shell pointers.
            QueuePidl(side,fxfile::shellnav::Location(entries[resident].id),
                      fxfile::shellnav::NavigationAction::Open);
        }else if(!indexed->parsingName.empty()){
            QueuePath(side,indexed->parsingName);
        }
    }
    void MainWindow::OnLeftFileDoubleTapped(
        IInspectable const&,Input::DoubleTappedRoutedEventArgs const&)
    {OpenSelectedFolder(0);}
    void MainWindow::OnRightFileDoubleTapped(
        IInspectable const&,Input::DoubleTappedRoutedEventArgs const&)
    {OpenSelectedFolder(1);}
    void MainWindow::OnLeftPaneTapped(
        IInspectable const&,Input::TappedRoutedEventArgs const&)
    {
        if(ActiveWindowTab().model.activePane!=0)ActivatePane(0);
        QueueSelectionPresentationUpdate();
    }
    void MainWindow::OnRightPaneTapped(
        IInspectable const&,Input::TappedRoutedEventArgs const&)
    {
        if(ActiveWindowTab().model.activePane!=1)ActivatePane(1);
        QueueSelectionPresentationUpdate();
    }
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
