#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Windows.Graphics.h>
#include <shellapi.h>
#include <thread>
#include <mutex>
#include <algorithm>
#include <cmath>
#include <utility>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
namespace {
template<class Callback>
void enqueueNoThrow(Microsoft::UI::Dispatching::DispatcherQueue const& dispatch,
                    Callback&& callback) noexcept {
 try{(void)dispatch.TryEnqueue(std::forward<Callback>(callback));}catch(...){}
}bool defaultStartupOrOwnedOptIn(){
 int argc=0;
 auto argv=::CommandLineToArgvW(::GetCommandLineW(),&argc);
 if(!argv)return false;
 bool explicitPath=argc>1&&argv[1][0]!=L'-';
 bool testOverride=false;
 wchar_t guard[8]{};
 const bool owned=::GetEnvironmentVariableW(L"FLY_M23_OWNED_SESSION",guard,8)==3&&
                  !wcscmp(guard,L"YES");
 if(owned)for(int i=1;i<argc;++i)
   if(!wcscmp(argv[i],L"--m23-owned-auto-restore"))
      testOverride=true;
 // A user's explicit positional startup folder or named workspace always
 // wins over saved session. The isolated test flag cannot bypass this
 // unless the owned fixture environment is explicitly configured.
 const bool allowed=argc==1||testOverride||
                    (!explicitPath&&argc==1);
 ::LocalFree(argv);
 return allowed;
}
}
void MainWindow::InitializePrivateSession(){
 if(!defaultStartupOrOwnedOptIn())return;
 // Only an explicitly saved private profile opt-in restores on future
 // default starts. Empty/nonexistent/invalid sessions have no effect.
 LoadPrivateSession();
}
void MainWindow::OnSavePrivateSession(
 IInspectable const&,RoutedEventArgs const&){
 if(mFileOperationPending){
  StatusText().Text(L"진행 중인 파일 작업이 끝난 후 세션을 저장하세요.");return;
 }
 try{
  if(ActiveWindowTab().model.split){
   const auto total=PrimaryColumn().ActualWidth()+SecondaryColumn().ActualWidth();
   if(total>1)ActiveWindowTab().splitPermille=static_cast<std::uint32_t>(
      (std::clamp)(PrimaryColumn().ActualWidth()/total*1000.,300.,700.));
  }
 }catch(...){}
 fxfile::uisession::Session data{};
 data.activeWindow=static_cast<std::uint32_t>(mActiveWindowTab);
 try{
  const auto current=AppWindow().Size();
  data.width=static_cast<std::uint32_t>((std::max)(current.Width,0));
  data.height=static_cast<std::uint32_t>((std::max)(current.Height,0));
 }catch(...){
  StatusText().Text(L"현재 창 크기를 확인하지 못해 세션을 저장하지 않았습니다.");return;
 }
 using CapturedHistory=std::array<std::vector<fxfile::shellnav::HistoryLocations>,2>;
 std::vector<CapturedHistory> histories;
 data.windowTabs.reserve(mWindowTabs.size());histories.reserve(mWindowTabs.size());
 for(auto const& state:mWindowTabs){
  CapturedHistory captured{};
  fxfile::uisession::WindowTab saved{};
  saved.split=state.model.split;saved.splitPermille=state.splitPermille;
  saved.activeSide=static_cast<std::uint32_t>(state.model.activePane);
  for(int side=0;side<2;++side){
   auto const& pane=state.model.panes[side];
   auto& target=saved.panes[side];
   target.selected=static_cast<std::uint32_t>(pane.active);
   target.sort=static_cast<std::uint32_t>(state.fileLists[side].sortMode);
   target.view=static_cast<std::uint32_t>(state.fileLists[side].viewMode);
   target.nameColumnWidth=static_cast<std::uint32_t>((std::clamp)(
       std::lround(state.fileLists[side].nameColumnWidth),80l,600l));
   target.tabs.reserve(pane.tabs.size());captured[side].reserve(pane.tabs.size());
   for(size_t i=0;i<pane.tabs.size();++i){
    fxfile::uisession::PaneTab tab{};
    tab.path=i<pane.filesystemPaths.size()?pane.filesystemPaths[i]:L"";
    if(tab.path.empty())tab.path=pane.tabs[i].snapshot().parsingName;
    fxfile::shellnav::HistoryLocations history{};
    if(!pane.tabs[i].historyLocations(history)){
     StatusText().Text(L"탐색 기록을 안전하게 저장할 수 없어 세션을 저장하지 않았습니다.");return;
    }
    captured[side].push_back(std::move(history));
    target.tabs.push_back(std::move(tab));
   }
  }
  data.windowTabs.push_back(std::move(saved));
  histories.push_back(std::move(captured));
 }
 if(!fxfile::uisession::valid(data)){
  StatusText().Text(L"개인 세션은 기존 로컬 폴더와 제한된 창/폴더 탭만 저장할 수 있습니다.");return;
 }
 ++mSessionEpoch;auto ticket=mSessionRevision->fetch_add(1)+1;
 auto lock=mSessionMutation;auto revision=mSessionRevision;
 auto weak=get_weak();auto dispatch=DispatcherQueue();
 StatusText().Text(L"WinUI 개인 세션을 별도 스레드에서 안전하게 저장하는 중입니다...");
 try{
  std::thread([data=std::move(data),histories=std::move(histories),ticket,lock,revision,weak,dispatch]() mutable {
   std::lock_guard<std::mutex> guarded(*lock);
   if(ticket!=revision->load())return;
   bool ok=histories.size()==data.windowTabs.size();
   for(size_t w=0;ok&&w<histories.size();++w){
    for(int side=0;ok&&side<2;++side){
     auto& tabs=data.windowTabs[w].panes[side].tabs;
     if(histories[w][side].size()!=tabs.size()){ok=false;break;}
     for(size_t i=0;ok&&i<tabs.size();++i){
      fxfile::shellnav::HistoryPaths paths{};
      ok=fxfile::shellnav::historyPathsFromLocations(histories[w][side][i],paths);
      if(ok){tabs[i].back=std::move(paths.back);tabs[i].forward=std::move(paths.forward);}
     }
    }
   }
   if(ok)ok=fxfile::uisession::save(data);
   if(ticket!=revision->load())return;
   enqueueNoThrow(dispatch,[weak,ticket,ok]{
    if(auto ui=weak.get()){
     if(ticket!=ui->mSessionRevision->load())return;
     ui->StatusText().Text(ok?
       L"개인 WinUI 세션을 저장했습니다. 다음 기본 실행에서 자동 복원합니다.":
       L"개인 세션을 저장하지 못했습니다. 실제 로컬 폴더만 지원합니다.");
    }
   });
  }).detach();
 }catch(...){StatusText().Text(L"개인 세션 저장 스레드를 시작하지 못했습니다.");}
}
void MainWindow::LoadPrivateSession(){
 const auto ticket=++mSessionEpoch;auto weak=get_weak();auto dispatch=DispatcherQueue();
 auto revision=mSessionRevision;const auto revisionTicket=revision->load();
 try{
  std::thread([ticket,weak,dispatch,revision,revisionTicket]{
   auto session=std::make_shared<fxfile::uisession::Session>();
   bool ok=fxfile::uisession::load(*session);
   auto restored=std::make_shared<std::vector<fxfile::previewtabs::WindowTabState>>();
   if(ok){
    std::vector<fxfile::uisession::WindowTab> windows=session->windowTabs;
    if(windows.empty()){
     fxfile::uisession::WindowTab legacy{};legacy.split=session->split;
     legacy.splitPermille=session->splitPermille;legacy.activeSide=session->activeSide;
     for(int side=0;side<2;++side){
      auto paths=session->paths[side];
      if(side==1&&!legacy.split)paths={session->paths[0][session->selected[0]]};
      legacy.panes[side].selected=side==1&&!legacy.split?0:session->selected[side];
      legacy.panes[side].sort=session->sort[side];
      for(auto const& path:paths){fxfile::uisession::PaneTab t{};t.path=path;legacy.panes[side].tabs.push_back(std::move(t));}
     }
     windows.push_back(std::move(legacy));session->activeWindow=0;
    }
    const HRESULT co=::CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
    const bool uninit=SUCCEEDED(co);
    if(FAILED(co)&&co!=RPC_E_CHANGED_MODE)ok=false;
    for(size_t w=0;ok&&w<windows.size();++w){
     auto const& source=windows[w];
     fxfile::previewtabs::WindowTabState state(static_cast<std::uint64_t>(w+1));
     std::array<size_t,2> counts{{source.panes[0].tabs.size(),source.panes[1].tabs.size()}};
     std::array<size_t,2> selected{{source.panes[0].selected,source.panes[1].selected}};
     ok=state.model.reset(source.split,counts,selected);
     state.splitPermille=source.splitPermille;
     if(ok&&source.activeSide)ok=state.model.dispatch(
        fxfile::explorerui::Command::ActivatePane,static_cast<int>(source.activeSide)).accepted;
     for(int side=0;ok&&side<2;++side){
      state.fileLists[side].sortMode=static_cast<int>(source.panes[side].sort);
      state.fileLists[side].viewMode=static_cast<fxfile::previewlist::FileViewMode>(source.panes[side].view);
      state.fileLists[side].nameColumnWidth=source.panes[side].nameColumnWidth;
      auto& pane=state.model.panes[side];
      for(size_t i=0;ok&&i<source.panes[side].tabs.size();++i){
       auto const& saved=source.panes[side].tabs[i];
       pane.filesystemPaths[i]=saved.path;
       ok=SUCCEEDED(pane.tabs[i].open(saved.path));
       if(ok)ok=pane.tabs[i].restoreHistoryPaths({saved.back,saved.forward});
      }
     }
     if(ok)restored->push_back(std::move(state));
    }
    if(uninit)::CoUninitialize();
   }
   if(revisionTicket!=revision->load())return;
   enqueueNoThrow(dispatch,[ticket,weak,session,restored,ok]{
    if(auto ui=weak.get()){
     if(ticket!=ui->mSessionEpoch||!ok||restored->empty()||ui->mFileOperationPending)return;
     ui->SuspendActiveWindowTab();
     for(auto& old:ui->mWindowTabs)ui->ReleaseWindowTabRoutes(old);
     ui->mWindowTabs=std::move(*restored);
     ui->mActiveWindowTab=(std::min)(static_cast<size_t>(session->activeWindow),ui->mWindowTabs.size()-1);
     ui->mNextWindowTabIdentity=static_cast<std::uint64_t>(ui->mWindowTabs.size()+1);
     try{ui->AppWindow().Resize({static_cast<int>(session->width),static_cast<int>(session->height)});}catch(...){}
     ui->ApplyActiveWindowTab(L"저장한 개인 WinUI 세션을 복원했습니다.");
     ui->RefreshWindowTabs();
    }
   });
  }).detach();
 }catch(...){StatusText().Text(L"개인 세션 복원 스레드를 시작하지 못했습니다.");}
}
void MainWindow::OnRestorePrivateSession(
 IInspectable const&,RoutedEventArgs const&){
 if(mFileOperationPending){
  StatusText().Text(L"진행 중인 작업이 끝난 후 세션을 복원하세요.");return;
 }
 LoadPrivateSession();
}
void MainWindow::OnClearPrivateSession(
 IInspectable const&,RoutedEventArgs const&){
 ++mSessionEpoch;
 const auto ticket=mSessionRevision->fetch_add(1)+1;
 auto lock=mSessionMutation;
 auto revision=mSessionRevision;
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 try{
  std::thread([ticket,lock,revision,weak,dispatch]{
   std::lock_guard<std::mutex> guarded(*lock);
   if(ticket!=revision->load())return;
   const bool ok=fxfile::uisession::clear();
   if(ticket!=revision->load())return;
   enqueueNoThrow(dispatch,[weak,ticket,ok]{
    if(auto ui=weak.get()){
     if(ticket!=ui->mSessionRevision->load())return;
     ui->StatusText().Text(ok?
       L"저장된 개인 세션을 지웠습니다. 다음 실행에서는 자동 복원하지 않습니다.":
       L"개인 세션 파일을 지우지 못했습니다.");
    }
   });
  }).detach();
 }catch(...){StatusText().Text(L"개인 세션 삭제를 시작하지 못했습니다.");}
}
}
