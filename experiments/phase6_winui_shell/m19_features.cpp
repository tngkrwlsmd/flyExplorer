#include "pch.h"
#include "MainWindow.xaml.h"
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
namespace winrt::FlyExplorerWinUIShell::implementation {
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
}
void MainWindow::InitializeM19(){
    const auto dispatch=DispatcherQueue();
    const auto weak=get_weak();
    try {
        // Reading preview-only recent scopes never touches legacy
        // APPDATA\fxfile\conf and never blocks the XAML thread.
        std::thread([weak,dispatch]{
            auto items=std::make_shared<std::vector<std::wstring>>();
            if(!fxfile::preview::readRecentScopes(*items))items->clear();
            dispatch.TryEnqueue([weak,items]{
                if(auto ui=weak.get()){
                    if(!ui->mRecentEdited) {
                        ui->mRecentScopes=std::move(*items);
                        ui->RefreshRecentSearchOptions();
                    }
                }
            });
        }).detach();
    }catch(...){}
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
        StatusText().Text(L"Invalid absolute named-workspace path.");
        return;
    }
    StatusText().Text(L"Validating isolated named workspace...");
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
                        hstring(L"Named workspace rejected: "+*reason));
                }
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"Could not launch isolated workspace validation.");
    }
}
void MainWindow::ApplyWorkspace(fxfile::preview::Workspace&& doc) {
    // Validated off-thread BEFORE replacing any live pane. On this child
    // instance only: never mutate a different WinUI or MFC window.
    for(int side=0;side!=2;++side){
        for(auto route:mModel.panes[side].routeIds){
            mSupervisor->forget(route);
            mWatcher->unwatch(route);
            mShellWatcher->unwatch(route);
        }
        mRestoreQueue[side].clear();
        mWatchedRoutes[side]=mWatchTokens[side]=0;
        mWatchedPaths[side].clear();
    }
    std::array<size_t,2> counts{{doc.paths[0].size(),
                                 doc.split?doc.paths[1].size():1}};
    std::array<size_t,2> selected{{doc.selected[0],
                                   doc.split?doc.selected[1]:0}};
    if(!mModel.reset(doc.split,counts,selected)){
        StatusText().Text(L"Unsupported named workspace layout.");
        return;
    }
    SecondaryPane().Visibility(mModel.split?Visibility::Visible:Visibility::Collapsed);
    PaneDivider().Visibility(mModel.split?Visibility::Visible:Visibility::Collapsed);
    SecondaryColumn().Width(mModel.split?
        GridLength{1.0,GridUnitType::Star}:GridLength{0.0,GridUnitType::Pixel});
    SplitButton().Content(box_value(hstring(
        mModel.split?L"Single pane":L"Split panes")));
    for(int side=0;side!=2;++side){
        const auto& paths=(!mModel.split && side==1)?
            doc.paths[0]:doc.paths[side];
        auto& pane=mModel.panes[side];
        const size_t count=pane.tabs.size();
        for(size_t i=0;i<count;++i){
            if(i==pane.active)continue;
            mRestoreQueue[side].emplace_back(i,paths[i]);
        }
        const std::wstring initial=(!mModel.split&&side==1)?
            paths[doc.selected[0]]:paths[pane.active];
        QueuePath(side,initial); // nonblocking, same supervised lane
    }
    Refresh(L"Restoring validated named workspace in this isolated window");
}
void MainWindow::QueueNextWorkspaceTab(int side) {
    auto& pane=mModel.panes[side];
    auto& tasks=mRestoreQueue[side];
    if(std::any_of(pane.pending.begin(),pane.pending.end(),
                   [](std::uint64_t x){return x!=0;}))return;
    while(!tasks.empty()){
        const auto next=std::move(tasks.front());
        tasks.pop_front();
        if(next.first>=pane.routeIds.size())continue;
        const auto id=mSupervisor->submitParsing(
            side,pane.routeIds[next.first],next.second);
        if(id) {
            mModel.markPending(side,next.first,id,false);
            RefreshTabs(side);
            return;
        }
    }
}
bool MainWindow::WorkspaceModel(
    fxfile::preview::Workspace& target,std::wstring& reason) const {
    target=fxfile::preview::Workspace{};
    target.split=mModel.split;
    for(int side=0;side<(mModel.split?2:1);++side){
        auto const& pane=mModel.panes[side];
        if(pane.tabs.empty()||pane.tabs.size()>32 ||
           pane.active>=pane.tabs.size()) {
            reason=L"Unsupported tab layout.";return false;
        }
        for(size_t i=0;i<pane.tabs.size();++i){
            if(pane.pending[i]){
                reason=L"Wait until every folder finishes loading.";return false;
            }
            auto path=pane.filesystemPaths[i];
            if(path.empty())path=pane.tabs[i].snapshot().parsingName;
            if(path.empty()) {
                reason=L"An unloaded tab cannot be saved.";return false;
            }
            target.paths[side].push_back(std::move(path));
        }
        target.selected[side]=pane.active;
    }
    return true;
}
void MainWindow::OnToggleWorkspaces(
    IInspectable const&,RoutedEventArgs const&) {
    const auto next=WorkspacePanel().Visibility()==Visibility::Collapsed?
                    Visibility::Visible:Visibility::Collapsed;
    SearchPanel().Visibility(Visibility::Collapsed);
    WorkspacePanel().Visibility(next);
    if(next==Visibility::Visible)
        StatusText().Text(L"Choose an absolute .fxworkspace file path");
}
void MainWindow::OnSaveWorkspace(
    IInspectable const&,RoutedEventArgs const&) {
    const auto file=std::wstring(WorkspaceFileBox().Text().c_str());
    if(!absoluteFile(file)){
        StatusText().Text(L"Choose an absolute .fxworkspace filename.");
        return;
    }
    fxfile::preview::Workspace snapshot;
    std::wstring reason;
    if(!WorkspaceModel(snapshot,reason)){
        StatusText().Text(hstring(reason));return;
    }
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    StatusText().Text(L"Saving new named workspace without overwriting...");
    try {
        std::thread([weak,dispatch,file,doc=std::move(snapshot)]{
            std::wstring result;
            const bool saved=fxfile::preview::saveWorkspaceNew(
                file,doc,result);
            dispatch.TryEnqueue([weak,saved,result=std::move(result)]{
                if(auto ui=weak.get())ui->StatusText().Text(
                    saved?L"Named workspace saved to the chosen file":
                    hstring(L"Named workspace not saved: "+result));
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"Could not launch workspace writer.");
    }
}
void MainWindow::OnOpenWorkspace(
    IInspectable const&,RoutedEventArgs const&) {
    const auto file=std::wstring(WorkspaceFileBox().Text().c_str());
    if(!absoluteFile(file)){
        StatusText().Text(L"Choose an absolute existing .fxworkspace file.");
        return;
    }
    const auto own=ownExecutable();
    if(own.empty()){
        StatusText().Text(L"Cannot locate the private WinUI preview executable.");
        return;
    }
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    StatusText().Text(L"Validating before opening a separate WinUI window...");
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
                          L"Named workspace opened in a separate WinUI process");
                    else if(!valid)
                        ui->StatusText().Text(
                          hstring(L"Named workspace rejected: "+reason));
                    else ui->StatusText().Text(
                          hstring(L"Could not start isolated workspace window: "+
                                  std::to_wstring(failure)));
                }
            });
        }).detach();
    }catch(...) {
        StatusText().Text(L"Cannot start workspace validation worker.");
    }
}
void MainWindow::RefreshRecentSearchOptions(){
    mPopulatingRecents=true;
    auto items=SearchRecentBox().Items();
    items.Clear();
    for(auto const& path:mRecentScopes){
        ComboBoxItem option;
        option.Content(box_value(hstring(path)));
        items.Append(option);
    }
    SearchRecentBox().SelectedIndex(-1);
    RecentCountText().Text(hstring(
        std::to_wstring(mRecentScopes.size())+L" saved"));
    mPopulatingRecents=false;
}
void MainWindow::OnToggleSearch(
    IInspectable const&,RoutedEventArgs const&) {
    const auto next=SearchPanel().Visibility()==Visibility::Collapsed?
                    Visibility::Visible:Visibility::Collapsed;
    WorkspacePanel().Visibility(Visibility::Collapsed);
    SearchPanel().Visibility(next);
    if(next==Visibility::Visible){
        auto& pane=mModel.panes[static_cast<size_t>(mModel.activePane)];
        auto const& path=pane.filesystemPaths[pane.active];
        if(!path.empty())SearchScopeBox().Text(hstring(path));
        StatusText().Text(L"Read-only bounded filename search; remembering is opt-in");
    }
}
void MainWindow::OnRunSearch(
    IInspectable const&,RoutedEventArgs const&) {
    const auto scope=std::wstring(SearchScopeBox().Text().c_str());
    const auto term=std::wstring(SearchTermBox().Text().c_str());
    if(scope.empty()||term.empty()||scope.size()>32700||term.size()>256) {
        StatusText().Text(
           L"Enter a filesystem scope and a filename term (up to 256 characters).");
        return;
    }
    if(mSearchCancel)mSearchCancel->store(true);
    auto cancel=std::make_shared<std::atomic_bool>(false);
    mSearchCancel=cancel;
    const auto ticket=++mSearchEpoch;
    const bool remember=SearchRememberBox().IsChecked().GetBoolean();
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    SearchRunButton().IsEnabled(false);
    SearchCountText().Text(L"Searching on an independent native thread...");
    SearchMatches().Items().Clear();
    try {
        std::thread([weak,dispatch,cancel,ticket,scope,term,remember]{
            auto result=std::make_shared<fxfile::preview::SearchResults>();
            try{*result=fxfile::preview::scanFiles(scope,term,cancel);}
            catch(...){result->valid=false;}
            dispatch.TryEnqueue(
                [weak,cancel,ticket,scope,remember,result]{
                    if(auto ui=weak.get()){
                        if(ui->mSearchEpoch==ticket && !cancel->load()){
                            ui->SearchRunButton().IsEnabled(true);
                            ui->OnSearchCompleted(std::move(*result),
                                                  scope,remember);
                        }
                    }
                });
        }).detach();
    }catch(...){
        SearchRunButton().IsEnabled(true);
        StatusText().Text(L"Could not start independent search thread.");
    }
}
void MainWindow::OnSearchCompleted(
    fxfile::preview::SearchResults&& result,
    std::wstring const& scope,bool remember){
    if(result.canceled)return;
    if(!result.valid){
        SearchCountText().Text(L"Invalid or inaccessible filesystem folder");
        StatusText().Text(
            L"Search rejected; previous recent locations were not modified");
        return;
    }
    auto items=SearchMatches().Items();
    items.Clear();
    for(auto const& file:result.matches){
        TextBlock row;
        row.Text(hstring(file));
        items.Append(row);
    }
    SearchCountText().Text(hstring(
        L"Found "+std::to_wstring(result.count)+
        (result.truncated?L" matching files (bounded partial search)":
                          L" matching files")));
    if(remember){
        fxfile::preview::rememberScope(mRecentScopes,scope);
        mRecentEdited=true;
        RefreshRecentSearchOptions();
        if(!fxfile::preview::writeRecentScopes(mRecentScopes)) {
            StatusText().Text(
                L"Search completed, but opted-in recent-location save failed.");
            return;
        }
    }
    StatusText().Text(
        remember?L"Search completed; opted-in location saved to preview profile":
                 L"Search completed; location not remembered (default)");
}
void MainWindow::OnSelectSearchRecent(
    IInspectable const&,SelectionChangedEventArgs const&){
    if(mPopulatingRecents)return;
    const auto index=SearchRecentBox().SelectedIndex();
    if(index<0||static_cast<size_t>(index)>=mRecentScopes.size())return;
    SearchScopeBox().Text(hstring(mRecentScopes[static_cast<size_t>(index)]));
    StatusText().Text(L"Selected prior opted-in search scope without saving");
}
void MainWindow::OnClearSearchRecent(
    IInspectable const&,RoutedEventArgs const&){
    mRecentScopes.clear();
    mRecentEdited=true;
    RefreshRecentSearchOptions();
    if(fxfile::preview::writeRecentScopes(mRecentScopes))
        StatusText().Text(L"Preview recent search locations cleared");
    else StatusText().Text(L"Could not persist recent search clearing");
}
} // winrt::FlyExplorerWinUIShell::implementation
