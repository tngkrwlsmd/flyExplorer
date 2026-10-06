#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Windows.Graphics.h>
#include <shellapi.h>
#include <algorithm>
#include <atomic>
#include <cwchar>
#include <memory>
#include <thread>
#include <utility>
#include <winrt/Windows.System.h>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
using SearchController=fxfile::previewsearch::SearchController;
namespace {
bool absoluteFile(std::wstring const& path) {
    if(path.size()<3||path.size()>32700 ||
       path.find_first_of(L"\"\r\n")!=std::wstring::npos ||
       path.find(L'\0')!=std::wstring::npos)return false;
    // Drive-root absolute or absolute UNC. Never let a child silently
    // resolve a relative user snapshot against its EXE working directory.
    return ((path[1]==L':' && (path[2]==L'\\'||path[2]==L'/')) ||
            (path[0]==L'\\' && path[1]==L'\\'));
}
std::wstring ownExecutable() {
    wchar_t buffer[32768]{};
    const auto n=::GetModuleFileNameW(nullptr,buffer,
                                     static_cast<DWORD>(_countof(buffer)));
    return n&&n<_countof(buffer)?
           std::wstring(buffer,n):std::wstring{};
}
SearchController::Post searchPost(
    Microsoft::UI::Dispatching::DispatcherQueue const& dispatch)
{
    return [dispatch](SearchController::UiTask task){
        try{
            return dispatch.TryEnqueue([
                task=std::move(task)
            ]() mutable {
                task();
            });
        }catch(...){return false;}
    };
}
}
void MainWindow::InitializeM19(){
    const auto dispatch=DispatcherQueue();
    const auto weak=get_weak();
    // Reading preview-only recent scopes never touches legacy
    // APPDATA\fxfile\conf and remains owned by SearchController off the UI thread.
    (void)mSearchController.loadRecents(
        searchPost(dispatch),
        [weak](bool applied){
            if(!applied)return;
            if(auto ui=weak.get())ui->RefreshRecentSearchOptions();
        });
    int count=0;
    auto argv=::CommandLineToArgvW(::GetCommandLineW(),&count);
    std::wstring requested;
    if(argv) {
        if(count>=3 && !wcscmp(argv[1],L"--m19-workspace"))
            requested=argv[2];
        ::LocalFree(argv);
    }
    if(requested.empty())return;
    if(!absoluteFile(requested)){
        StatusText().Text(L"작업 공간 파일의 절대 경로가 필요합니다.");
        return;
    }
    StatusText().Text(L"작업 공간 파일을 안전하게 검사하는 중입니다...");
    try {
        std::thread([weak,dispatch,requested=std::move(requested)]{
            auto prepared=std::make_shared<fxfile::preview::Workspace>();
            auto reason=std::make_shared<std::wstring>();
            const bool good=fxfile::preview::loadWorkspace(
                requested,*prepared,*reason);
            dispatch.TryEnqueue([weak,prepared,reason,good]{
                if(auto ui=weak.get()){
                    if(good)ui->ApplyWorkspace(std::move(*prepared));
                    else ui->StatusText().Text(
                        hstring(L"작업 공간 파일이 올바르지 않습니다: "+*reason));
                }
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"작업 공간 파일 검사를 시작할 수 없습니다.");
    }
}
void MainWindow::ApplyWorkspace(fxfile::preview::Workspace&& doc) {
    // Validated off-thread BEFORE replacing any live pane. On this child
    // instance only: never mutate a different WinUI or MFC window.
    mShellNavigation->release(ActiveWindowTab().model);
    mWorkspaceRestore.reset();
    std::array<size_t,2> counts{{doc.paths[0].size(),
                                 doc.split?doc.paths[1].size():1}};
    std::array<size_t,2> selected{{doc.selected[0],
                                   doc.split?doc.selected[1]:0}};
    if(!mWorkspace.resetActive(doc.split,counts,selected)){
        StatusText().Text(L"지원하지 않는 작업 공간 배치입니다.");
        return;
    }
    SecondaryPane().Visibility(ActiveWindowTab().model.split?Visibility::Visible:Visibility::Collapsed);
    PaneDivider().Visibility(ActiveWindowTab().model.split?Visibility::Visible:Visibility::Collapsed);
    SecondaryColumn().Width(ActiveWindowTab().model.split?
        GridLength{1.0,GridUnitType::Star}:GridLength{0.0,GridUnitType::Pixel});
    SplitButton().Content(box_value(hstring(
        ActiveWindowTab().model.split?L"단일 창":L"분할 창")));
    for(int side=0;side!=2;++side){
        const auto& paths=(!ActiveWindowTab().model.split && side==1)?
            doc.paths[0]:doc.paths[side];
        auto& pane=ActiveWindowTab().model.panes[side];
        const size_t count=pane.tabs.size();
        std::vector<fxfile::previewrestore::WorkspaceRestoreCoordinator::Task>
            tasks;
        tasks.reserve(count?count-1:0);
        for(size_t i=0;i<count;++i){
            if(i==pane.active)continue;
            tasks.push_back({i,paths[i]});
        }
        const std::wstring initial=(!ActiveWindowTab().model.split&&side==1)?
            paths[doc.selected[0]]:paths[pane.active];
        const auto initialRequest=QueuePath(
            side,initial); // nonblocking, same supervised lane
        mWorkspaceRestore.begin(side,std::move(tasks),initialRequest);
        if(!initialRequest)QueueNextWorkspaceTab(side);
    }
    Refresh(L"검증한 작업 공간을 독립된 창에서 복원하는 중입니다.");
}
void MainWindow::QueueNextWorkspaceTab(int side) {
    auto& pane=ActiveWindowTab().model.panes[side];
    const bool paneBusy=std::any_of(
        pane.pending.begin(),pane.pending.end(),
        [](std::uint64_t x){return x!=0;});
    while(auto next=mWorkspaceRestore.takeNext(
              side,paneBusy,pane.routeIds.size())){
        const auto id=mShellNavigation->submitParsing(
            ActiveWindowTab().model,side,next->tab,next->path,false);
        if(id) {
            mWorkspaceRestore.track(side,id);
            RefreshTabs(side);
            return;
        }
    }
}
bool MainWindow::WorkspaceModel(
    fxfile::preview::Workspace& target,std::wstring& reason) const {
    target=fxfile::preview::Workspace{};
    target.split=ActiveWindowTab().model.split;
    for(int side=0;side<(ActiveWindowTab().model.split?2:1);++side){
        auto const& pane=ActiveWindowTab().model.panes[side];
        if(pane.tabs.empty()||pane.tabs.size()>32 ||
           pane.active>=pane.tabs.size()) {
            reason=L"지원하지 않는 탭 배치입니다.";return false;
        }
        for(size_t i=0;i<pane.tabs.size();++i){
            if(pane.pending[i]){
                reason=L"모든 폴더가 로드될 때까지 기다려 주세요.";return false;
            }
            auto path=pane.filesystemPaths[i];
            if(path.empty())path=pane.tabs[i].snapshot().parsingName;
            if(path.empty()) {
                reason=L"아직 로드되지 않은 탭은 저장할 수 없습니다.";return false;
            }
            target.paths[side].push_back(std::move(path));
        }
        target.selected[side]=pane.active;
    }
    return true;
}
void MainWindow::EnsureExpandedPanelFits() {
    // Expanded search/workspace panels must not consume the entire file pane
    // on compact displays. Bound growth to the actual monitor work area.
    const auto size=AppWindow().Size();
    const auto position=AppWindow().Position();
    const POINT center{position.X+size.Width/2,position.Y+size.Height/2};
    MONITORINFO monitor{sizeof(monitor)};
    if(!::GetMonitorInfoW(::MonitorFromPoint(center,MONITOR_DEFAULTTONEAREST),
                          &monitor))return;
    const int available=monitor.rcWork.bottom-position.Y-8;
    const int desired=(std::min)(700,available);
    if(desired>=560&&desired>size.Height+40){
        try{AppWindow().Resize({size.Width,desired});}catch(...){
            // The sidebar is independently scrollable when size is constrained.
        }
    }
}
void MainWindow::OnToggleWorkspaces(
    IInspectable const&,RoutedEventArgs const&) {
    const auto next=WorkspacePanel().Visibility()==Visibility::Collapsed?
                    Visibility::Visible:Visibility::Collapsed;
    SearchPanel().Visibility(Visibility::Collapsed);
    BookmarkPanel().Visibility(Visibility::Collapsed);
    FilterRulePanel().Visibility(Visibility::Collapsed);
    WorkspacePanel().Visibility(next);
    if(next==Visibility::Visible)EnsureExpandedPanelFits();
    if(next==Visibility::Visible)
        StatusText().Text(L"작업 공간 파일의 절대 경로를 입력하세요.");
}
void MainWindow::OnSaveWorkspace(
    IInspectable const&,RoutedEventArgs const&) {
    const auto file=std::wstring(WorkspaceFileBox().Text().c_str());
    if(!absoluteFile(file)){
        StatusText().Text(L"작업 공간 파일 이름을 절대 경로로 입력하세요.");
        return;
    }
    fxfile::preview::Workspace snapshot;
    std::wstring reason;
    if(!WorkspaceModel(snapshot,reason)){
        StatusText().Text(hstring(reason));return;
    }
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    StatusText().Text(L"기존 파일을 덮어쓰지 않고 새 작업 공간을 저장하는 중입니다...");
    try {
        std::thread([weak,dispatch,file,doc=std::move(snapshot)]{
            std::wstring result;
            const bool saved=fxfile::preview::saveWorkspaceNew(
                file,doc,result);
            dispatch.TryEnqueue([weak,saved,result=std::move(result)]{
                if(auto ui=weak.get())ui->StatusText().Text(
                    saved?L"선택한 파일에 작업 공간을 새로 저장했습니다.":
                    hstring(L"작업 공간을 저장하지 못했습니다: "+result));
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"작업 공간 저장 작업을 시작할 수 없습니다.");
    }
}
void MainWindow::OnOpenWorkspace(
    IInspectable const&,RoutedEventArgs const&) {
    const auto file=std::wstring(WorkspaceFileBox().Text().c_str());
    if(!absoluteFile(file)){
        StatusText().Text(L"존재하는 작업 공간 파일의 절대 경로를 입력하세요.");
        return;
    }
    const auto own=ownExecutable();
    if(own.empty()){
        StatusText().Text(L"현재 WinUI 실행 파일을 찾지 못했습니다.");
        return;
    }
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    StatusText().Text(L"별도 WinUI 창을 열기 전에 파일을 검사하고 있습니다...");
    try {
        std::thread([weak,dispatch,file,own]{
            fxfile::preview::Workspace candidate;
            std::wstring reason;
            bool valid=fxfile::preview::loadWorkspace(
                file,candidate,reason);
            DWORD failure=0;
            bool created=false;
            if(valid){
                // Only the exact binary of this preview, no ShellExecute
                // associations, legacy MFC process or arbitrary commands.
                std::wstring args=L"\""+own+L"\" --m19-workspace \""+
                                   file+L"\"";
                std::vector<wchar_t> command(args.begin(),args.end());
                command.push_back(0);
                STARTUPINFOW startup{};
                startup.cb=sizeof(startup);
                PROCESS_INFORMATION process{};
                created=::CreateProcessW(
                    own.c_str(),command.data(),nullptr,nullptr,FALSE,0,
                    nullptr,nullptr,&startup,&process)!=FALSE;
                if(created){
                    ::CloseHandle(process.hThread);
                    ::CloseHandle(process.hProcess);
                }else failure=::GetLastError();
            }
            dispatch.TryEnqueue([weak,valid,created,
                                 reason=std::move(reason),failure]{
                if(auto ui=weak.get()){
                    if(created)
                        ui->StatusText().Text(
                          L"작업 공간을 별도 WinUI 프로세스에서 열었습니다.");
                    else if(!valid)
                        ui->StatusText().Text(
                          hstring(L"작업 공간 파일이 올바르지 않습니다: "+reason));
                    else ui->StatusText().Text(
                          hstring(L"독립 작업 공간 창을 시작할 수 없습니다. 오류: "+
                                  std::to_wstring(failure)));
                }
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"작업 공간 파일 검사 작업자를 시작할 수 없습니다.");
    }
}
SearchController::Context MainWindow::SearchContext(){
    SearchController::Context context{};
    auto const& state=ActiveWindowTab();
    context.windowIdentity=state.identity;
    context.side=state.model.activePane;
    auto const& pane=state.model.panes[static_cast<std::size_t>(context.side)];
    context.tab=pane.active;
    if(context.tab<pane.routeIds.size())
        context.route=pane.routeIds[context.tab];
    if(context.tab<pane.filesystemPaths.size())
        context.paneFolder=pane.filesystemPaths[context.tab];
    context.scope=std::wstring(SearchScopeBox().Text().c_str());
    context.query.term=std::wstring(SearchTermBox().Text().c_str());
    context.query.contentTerm=std::wstring(SearchContentBox().Text().c_str());
    switch(SearchContentEncodingBox().SelectedIndex()){
    case 1:
        context.query.contentEncoding=fxfile::preview::SearchContentEncoding::Korean949;
        break;
    case 2:
        context.query.contentEncoding=fxfile::preview::SearchContentEncoding::Windows1252;
        break;
    default:
        context.query.contentEncoding=fxfile::preview::SearchContentEncoding::AutoUtf;
        break;
    }
    context.query.extension=std::wstring(SearchExtensionBox().Text().c_str());
    context.query.minSizeKb=std::wstring(SearchMinSizeBox().Text().c_str());
    context.query.maxSizeKb=std::wstring(SearchMaxSizeBox().Text().c_str());
    context.query.modifiedAfter=std::wstring(SearchModifiedAfterBox().Text().c_str());
    context.query.modifiedBefore=std::wstring(SearchModifiedBeforeBox().Text().c_str());
    context.query.regex=SearchRegexBox().IsChecked().GetBoolean();
    context.query.caseSensitive=SearchCaseBox().IsChecked().GetBoolean();
    switch(SearchTargetBox().SelectedIndex()){
    case 1:
        context.query.kind=fxfile::preview::SearchEntryKind::Folders;
        break;
    case 2:
        context.query.kind=fxfile::preview::SearchEntryKind::FilesAndFolders;
        break;
    default:
        context.query.kind=fxfile::preview::SearchEntryKind::Files;
        break;
    }
    return context;
}
void MainWindow::RefreshRecentSearchOptions(){
    mPopulatingRecents=true;
    const auto recent=mSearchController.recentScopes();
    auto items=SearchRecentBox().Items();
    items.Clear();
    for(auto const& path:recent){
        ComboBoxItem option;
        option.Content(box_value(hstring(path)));
        items.Append(option);
    }
    SearchRecentBox().SelectedIndex(-1);
    RecentCountText().Text(hstring(
        L"저장 "+std::to_wstring(recent.size())+L"개"));
    mPopulatingRecents=false;
}
void MainWindow::OnToggleSearch(
    IInspectable const&,RoutedEventArgs const&) {
    const auto next=SearchPanel().Visibility()==Visibility::Collapsed?
                    Visibility::Visible:Visibility::Collapsed;
    WorkspacePanel().Visibility(Visibility::Collapsed);
    BookmarkPanel().Visibility(Visibility::Collapsed);
    FilterRulePanel().Visibility(Visibility::Collapsed);
    SearchPanel().Visibility(next);
    if(next==Visibility::Collapsed){
        mSearchController.invalidate();
        SearchRunButton().IsEnabled(true);
        return;
    }
    EnsureExpandedPanelFits();
    auto& pane=ActiveWindowTab().model.panes[
        static_cast<size_t>(ActiveWindowTab().model.activePane)];
    auto const& path=pane.filesystemPaths[pane.active];
    if(!path.empty())SearchScopeBox().Text(hstring(path));
    StatusText().Text(
        L"이름/정규식/확장자/크기/수정일/텍스트 내용 조건을 조합하고 저장할 수 있습니다.");
}
void MainWindow::OnRunSearch(
    IInspectable const&,RoutedEventArgs const&) {
    SearchController::Request request{};
    auto context=SearchContext();
    request.scope=context.scope;
    request.query=context.query;
    request.remember=SearchRememberBox().IsChecked().GetBoolean();
    const auto weak=get_weak();
    const auto status=mSearchController.start(
        std::move(request),std::move(context),
        searchPost(DispatcherQueue()),
        [weak](SearchController::Completion completion){
            if(auto ui=weak.get())
                ui->OnSearchCompleted(std::move(completion));
        });
    using Start=SearchController::StartStatus;
    if(status==Start::Started){
        SearchRunButton().IsEnabled(false);
        SearchCountText().Text(
            L"독립 스레드에서 최대 20,000개 항목을 검색하고 있습니다...");
        SearchMatches().Items().Clear();
        return;
    }
    SearchRunButton().IsEnabled(true);
    if(status==Start::InvalidRequest){
        StatusText().Text(
           L"검색 폴더와 하나 이상의 이름/확장자/크기/수정일/내용 조건을 입력하세요.");
    }else if(status==Start::InvalidExtension){
        SearchCountText().Text(L"확장자 조건이 올바르지 않습니다.");
        StatusText().Text(
           L"확장자는 .txt처럼 한 줄의 확장자 이름만 입력하세요.");
    }else if(status==Start::InvalidSizeRange){
        SearchCountText().Text(L"파일 크기 범위가 올바르지 않습니다.");
        StatusText().Text(
           L"크기는 0 이상의 KB 정수로 입력하고 최소값이 최대값보다 크지 않아야 합니다.");
    }else if(status==Start::InvalidDateRange){
        SearchCountText().Text(L"수정일 범위가 올바르지 않습니다.");
        StatusText().Text(
           L"수정일은 YYYY-MM-DD로 입력하고 이후 날짜가 이전 날짜보다 늦지 않아야 합니다.");
    }else if(status==Start::InvalidContentTerm){
        SearchCountText().Text(L"파일 내용 조건이 올바르지 않습니다.");
        StatusText().Text(
           L"내용 검색은 256자 이하의 한 줄 literal 텍스트이며 폴더 전용 검색과 함께 사용할 수 없습니다.");
    }else if(status==Start::InvalidContentEncoding){
        SearchCountText().Text(L"파일 내용 인코딩 조건이 올바르지 않습니다.");
        StatusText().Text(
           L"내용 인코딩은 자동 UTF, 한국어 CP949, 서유럽 Windows-1252 중 하나여야 합니다.");
    }else if(status==Start::InvalidPattern){
        SearchCountText().Text(L"정규식이 올바르지 않습니다.");
        StatusText().Text(
           L"정규식 문법을 확인하세요. 잘못된 정규식은 검색을 시작하지 않습니다.");
    }else if(status==Start::ThreadStartFailed){
        StatusText().Text(L"독립 검색 스레드를 시작할 수 없습니다.");
    }
}
void MainWindow::OnSearchCompleted(
    SearchController::Completion completion){
    const auto accepted=mSearchController.accept(
        completion,SearchContext());
    using Disposition=SearchController::Disposition;
    if(accepted.disposition==Disposition::Ignored)return;

    SearchRunButton().IsEnabled(true);
    if(accepted.disposition==Disposition::Canceled)return;
    if(accepted.disposition==Disposition::StaleContext){
        SearchCountText().Text(
            L"검색 컨텍스트가 변경되어 이전 결과를 무시했습니다.");
        StatusText().Text(
            L"검색 중 폴더, 탭 또는 검색 입력이 변경됐습니다.");
        return;
    }
    if(accepted.disposition==Disposition::Invalid){
        SearchCountText().Text(
            L"검색할 폴더가 올바르지 않거나 접근할 수 없습니다.");
        StatusText().Text(
            L"검색을 시작할 수 없습니다. 최근 검색 위치는 변경하지 않았습니다.");
        return;
    }

    auto items=SearchMatches().Items();
    items.Clear();
    for(auto const& file:completion.result.matches){
        TextBlock row;
        row.Text(hstring(file));
        items.Append(row);
    }
    auto summary=L"검색 결과 "+std::to_wstring(completion.result.count)+L"개";
    if(completion.result.resultLimited)
        summary+=L" · 처음 "+std::to_wstring(completion.result.matches.size())+
                 L"개 표시";
    if(completion.result.traversalLimited)
        summary+=L" · 탐색 한도 도달("+std::to_wstring(completion.result.visited)+
                 L"개 검사)";
    if(!completion.request.query.contentTerm.empty()){
        summary+=L" · 내용 "+std::to_wstring(completion.result.contentFilesScanned)+L"개 검사";
        if(completion.result.contentFilesSkipped)
            summary+=L" · "+std::to_wstring(completion.result.contentFilesSkipped)+L"개 건너뜀";
        if(completion.result.contentLimited)summary+=L" · 16 MiB I/O 제한 도달";
    }
    SearchCountText().Text(hstring(summary));
    if(completion.request.remember){
        RefreshRecentSearchOptions();
        if(!accepted.recentSaved){
            StatusText().Text(
                L"검색은 완료됐지만 선택한 최근 위치를 저장하지 못했습니다.");
            return;
        }
    }
    StatusText().Text(
        completion.request.remember?
          L"검색 완료 · 선택한 위치를 미리보기 프로필에 저장했습니다.":
          L"검색 완료 · 위치를 저장하지 않았습니다(기본값).");
}
void MainWindow::OnSelectSearchRecent(
    IInspectable const&,SelectionChangedEventArgs const&){
    if(mPopulatingRecents)return;
    const auto recent=mSearchController.recentScopes();
    const auto index=SearchRecentBox().SelectedIndex();
    if(index<0||static_cast<size_t>(index)>=recent.size())return;
    SearchScopeBox().Text(hstring(recent[static_cast<size_t>(index)]));
    StatusText().Text(L"저장된 위치를 선택했습니다. 기록은 변경하지 않았습니다.");
}
void MainWindow::OnClearSearchRecent(
    IInspectable const&,RoutedEventArgs const&){
    const bool saved=mSearchController.clearRecent();
    RefreshRecentSearchOptions();
    if(saved)
        StatusText().Text(L"최근 검색 위치를 모두 지웠습니다.");
    else StatusText().Text(L"최근 검색 위치 삭제를 저장하지 못했습니다.");
}
} // winrt::FlyExplorer::implementation
