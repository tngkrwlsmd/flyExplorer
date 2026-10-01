#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Windows.Graphics.h>
#include <shellapi.h>
#include <thread>
#include <mutex>
#include <algorithm>
#include <utility>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
namespace {
bool defaultStartupOrOwnedOptIn(){
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
  StatusText().Text(L"진행 중인 파일 작업이 끝난 후 세션을 저장하세요.");
  return;
 }
 fxfile::preview::Workspace snapshot{};
 std::wstring why{};
 if(!WorkspaceModel(snapshot,why)){
  StatusText().Text(hstring(L"세션을 저장할 수 없습니다: "+why));
  return;
 }
 fxfile::uisession::Session data{};
 data.split=snapshot.split;
 data.selected[0]=static_cast<std::uint32_t>(snapshot.selected[0]);
 data.selected[1]=snapshot.split?
      static_cast<std::uint32_t>(snapshot.selected[1]):0u;
 for(size_t side=0;side<2;++side){
  if(!snapshot.split&&side==1)continue;
  data.paths[side]=snapshot.paths[side];
 }
 data.activeSide=static_cast<std::uint32_t>(mModel.activePane);
 data.sort={{static_cast<std::uint32_t>(mFileLists[0].sortMode),
             static_cast<std::uint32_t>(mFileLists[1].sortMode)}};
 try{
  const auto current=AppWindow().Size();
  data.width=static_cast<std::uint32_t>((std::max)(current.Width,0));
  data.height=static_cast<std::uint32_t>((std::max)(current.Height,0));
  const auto primary=PrimaryColumn().ActualWidth();
  const auto secondary=SecondaryColumn().ActualWidth();
  const auto total=primary+secondary;
  if(mModel.split&&total>1)
   data.splitPermille=static_cast<std::uint32_t>(
       (std::clamp)(primary/total*1000.,300.,700.));
 }catch(...){
  StatusText().Text(L"현재 창 크기를 확인하지 못해 세션을 저장하지 않았습니다.");
  return;
 }
 // Fail closed before starting a filesystem worker: only existing local
 // non-reparse folders, bounded tab count and sensible geometry.
 if(data.paths[0].size()>8||data.paths[1].size()>8){
  StatusText().Text(L"개인 세션에는 각 창의 탭을 최대 8개까지 저장할 수 있습니다.");
  return;
 }
 ++mSessionEpoch;
 auto ticket=mSessionRevision->fetch_add(1)+1;
 auto lock=mSessionMutation;
 auto revision=mSessionRevision;
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 StatusText().Text(L"WinUI 개인 세션을 별도 스레드에서 안전하게 저장하는 중입니다...");
 try{
  std::thread([data=std::move(data),ticket,lock,revision,weak,dispatch]{
   std::lock_guard<std::mutex> guarded(*lock);
   if(ticket!=revision->load())return;
   const bool ok=fxfile::uisession::save(data);
   dispatch.TryEnqueue([weak,ticket,ok]{
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
 const auto ticket=++mSessionEpoch;
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 try{
  std::thread([ticket,weak,dispatch]{
   auto session=std::make_shared<fxfile::uisession::Session>();
   const bool ok=fxfile::uisession::load(*session);
   dispatch.TryEnqueue([ticket,weak,session,ok]{
    if(auto ui=weak.get()){
     if(ticket!=ui->mSessionEpoch)return;
     if(!ok){
      // No unsolicited error toast on normal first run with no opt-in.
      return;
     }
     if(ui->mFileOperationPending)return;
     fxfile::preview::Workspace target{};
     target.split=session->split;
     target.paths=session->paths;
     target.selected={{
         static_cast<size_t>(session->selected[0]),
         static_cast<size_t>(session->selected[1])}};
     ui->mFileLists[0].sortMode=static_cast<int>(session->sort[0]);
     ui->mFileLists[1].sortMode=static_cast<int>(session->sort[1]);
     ui->ApplyWorkspace(std::move(target));
     if(ui->mModel.split){
      const auto ratio=static_cast<double>(session->splitPermille);
      ui->PrimaryColumn().Width(GridLength{ratio,GridUnitType::Star});
      ui->SecondaryColumn().Width(GridLength{1000.-ratio,GridUnitType::Star});
     }
     ui->mModel.dispatch(fxfile::explorerui::Command::ActivatePane,
         static_cast<int>(session->activeSide));
     ui->fileBar()->SetSortIndex(ui->mFileLists[ui->mModel.activePane].sortMode);
     try{
      ui->AppWindow().Resize({static_cast<int>(session->width),
                               static_cast<int>(session->height)});
     }catch(...){/* Safe defaults already applied if resize is unavailable. */}
     ui->StatusText().Text(L"저장한 개인 WinUI 세션을 복원하는 중입니다...");
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
   dispatch.TryEnqueue([weak,ticket,ok]{
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
