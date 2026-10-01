#include "pch.h"
#include "MainWindow.xaml.h"
#include <thread>
#include <string>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
namespace {
hstring koreanError(DWORD code){
 switch(code){
 case ERROR_ALREADY_EXISTS:
 case ERROR_FILE_EXISTS:return L"같은 이름의 파일 또는 폴더가 이미 존재합니다. 덮어쓰지 않았습니다.";
 case ERROR_ACCESS_DENIED:return L"이 위치를 변경할 권한이 없습니다.";
 case ERROR_INVALID_NAME:
 case ERROR_INVALID_PARAMETER:return L"이름 또는 폴더 경로가 올바르지 않습니다.";
 case ERROR_FILE_NOT_FOUND:
 case ERROR_PATH_NOT_FOUND:return L"원본 파일 또는 폴더를 찾을 수 없습니다.";
 default:return hstring(L"파일 작업에 실패했습니다. Windows 오류: "+
                          std::to_wstring(code));
 }
}
}
void MainWindow::OnCreateFolder(
 IInspectable const&,RoutedEventArgs const&){
 BeginFileNameCommand(fxfile::filecommand::Kind::CreateFolder);
}
void MainWindow::OnRenameSelected(
 IInspectable const&,RoutedEventArgs const&){
 BeginFileNameCommand(fxfile::filecommand::Kind::RenameSelected);
}
void MainWindow::BeginFileNameCommand(fxfile::filecommand::Kind kind){
 if(mFileOperationPending){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 std::wstring initial;
 if(kind==fxfile::filecommand::Kind::RenameSelected){
  const int side=ActiveWindowTab().model.activePane;
  auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
  const size_t tab=pane.active;
  const auto view=side==0?LeftFiles():RightFiles();
  const auto picked=view.SelectedItem();
  const auto row=picked.try_as<ListViewItem>();
  if(!row||!row.Tag()){
   StatusText().Text(L"이름을 변경할 파일 또는 폴더를 선택하세요.");
   return;
  }
  const auto index=winrt::unbox_value<uint32_t>(row.Tag());
  const auto& entries=pane.tabs[tab].snapshot().children;
  if(index>=entries.size()||!entries[index].isFileSystem()||entries[index].parsingName.empty()){
   StatusText().Text(L"이 항목은 이름을 변경할 수 없습니다.");
   return;
  }
  try{initial=std::filesystem::path(entries[index].parsingName).filename().wstring();}
  catch(...){initial=entries[index].label;}
 }
 fileBar()->BeginNameEdit(kind==fxfile::filecommand::Kind::CreateFolder?0:1,hstring(initial));
 StatusText().Text(kind==fxfile::filecommand::Kind::CreateFolder?
  L"새 폴더 이름을 입력하고 Enter를 누르세요.":
  L"새 이름을 입력하고 Enter를 누르세요.");
}
void MainWindow::ExecuteFileCommand(fxfile::filecommand::Kind kind){
 if(mFileOperationPending){
     StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
     return;
 }
 const int side=ActiveWindowTab().model.activePane;
 auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
 const size_t tab=pane.active;
 if(pane.pending[tab]||pane.filesystemPaths[tab].empty()){
     StatusText().Text(L"파일 작업은 불러오기가 끝난 실제 폴더에서만 사용할 수 있습니다.");
     return;
 }
 fxfile::filecommand::Request request{};
 request.kind=kind;
 request.parent=pane.filesystemPaths[tab];
 request.name=std::wstring(FileNameBox().Text().c_str());
 if(request.name.empty()&&kind==fxfile::filecommand::Kind::CreateFolder)
     request.name=L"새 폴더";
 if(!fxfile::filecommand::validLeaf(request.name)){
     StatusText().Text(L"파일 이름만 입력하세요. 경로나 특수 문자는 사용할 수 없습니다.");
     return;
 }
 if(kind==fxfile::filecommand::Kind::RenameSelected){
     const auto view=side==0?LeftFiles():RightFiles();
     const auto picked=view.SelectedItem();
     const auto row=picked.try_as<ListViewItem>();
     if(!row||!row.Tag()){
         StatusText().Text(L"이름을 변경할 파일 또는 폴더를 선택하세요.");
         return;
     }
     const auto index=winrt::unbox_value<uint32_t>(row.Tag());
     const auto& entries=pane.tabs[tab].snapshot().children;
     if(index>=entries.size()||!entries[index].isFileSystem()||
        entries[index].parsingName.empty()){
         StatusText().Text(L"가상 Shell 항목은 이 파일 작업에서 변경할 수 없습니다.");
         return;
     }
     request.source=entries[index].parsingName;
 }
 const auto route=pane.routeIds[tab];
 const auto originalParent=request.parent;
 const auto ticket=++mFileOperationEpoch;
 mFileOperationPending=true;
 SetFileButtonsBusy(true,false);
 StatusText().Text(L"선택한 파일 작업을 별도 스레드에서 처리하는 중입니다...");
 auto dispatch=DispatcherQueue();
 auto weak=get_weak();
 try{
     std::thread([weak,dispatch,side,tab,route,ticket,originalParent,
                  request=std::move(request)]() mutable{
         const auto result=fxfile::filecommand::execute(request);
         dispatch.TryEnqueue([weak,side,tab,route,ticket,originalParent,
                              kind=request.kind,result]{
             if(auto ui=weak.get()){
                 if(ui->mFileOperationEpoch!=ticket)return;
                 ui->mFileOperationPending=false;
                 ui->SetFileButtonsBusy(false,false);
                 const auto& pane=ui->ActiveWindowTab().model.panes[side];
                 // A committed filesystem mutation is not undone if the
                 // user closed/navigated the pane while IO was in flight.
                 // The stale result must NEVER mutate a different tab UI.
                 if(tab>=pane.routeIds.size()||pane.routeIds[tab]!=route||
                    pane.filesystemPaths[tab]!=originalParent||
                    pane.active!=tab)return;
                 if(result.error!=ERROR_SUCCESS){
                     ui->StatusText().Text(koreanError(result.error));
                     return;
                 }
                 ui->fileBar()->EndNameEdit();
                 ui->StatusText().Text(
                     kind==fxfile::filecommand::Kind::CreateFolder?
                     L"새 폴더를 만들었습니다.":L"이름을 변경했습니다.");
                 ui->QueuePidl(side,
                   fxfile::shellnav::Location(
                       pane.tabs[tab].snapshot().folder),
                   fxfile::shellnav::NavigationAction::Refresh);
             }
         });
     }).detach();
 }catch(...){
     mFileOperationPending=false;
     SetFileButtonsBusy(false,false);
     StatusText().Text(L"파일 작업 스레드를 시작하지 못했습니다.");
 }
}
}
