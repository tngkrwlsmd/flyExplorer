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
 if(mFileOperations.busy()){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 std::wstring initial;
 bool renameFolder=false;
 if(kind==fxfile::filecommand::Kind::RenameSelected){
  const int side=ActiveWindowTab().model.activePane;
  auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
  const size_t tab=pane.active;
  const auto view=side==0?LeftFiles():RightFiles();
  if(view.SelectedItems().Size()!=1){
   StatusText().Text(L"이름 변경은 파일 또는 폴더 하나만 선택해야 합니다.");
   return;
  }
  const auto picked=view.SelectedItem();
  const auto row=picked.try_as<ListViewItem>();
  if(!row||!row.Tag()){
   StatusText().Text(L"이름을 변경할 파일 또는 폴더를 선택하세요.");
   return;
  }
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=pane.tabs[tab].indexedItem(
      static_cast<std::size_t>(logical));
  if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
   StatusText().Text(L"이 항목은 이름을 변경할 수 없습니다.");
   return;
  }
  renameFolder=indexed->isFolder();
  try{initial=std::filesystem::path(
          indexed->parsingName).filename().wstring();}
  catch(...){initial=indexed->label;}
 }
 fileBar()->BeginNameEdit(kind==fxfile::filecommand::Kind::CreateFolder?0:1,hstring(initial),renameFolder);
 StatusText().Text(kind==fxfile::filecommand::Kind::CreateFolder?
  L"새 폴더 이름을 입력하고 Enter로 확정하거나 Esc로 취소하세요.":
  hstring(L"이름 변경 대상: "+initial+
      L" (Enter 확정, Esc 취소)"));
}
void MainWindow::ExecuteFileCommand(fxfile::filecommand::Kind kind){
 if(mFileOperations.busy()){
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
     if(view.SelectedItems().Size()!=1){
         StatusText().Text(L"이름 변경은 파일 또는 폴더 하나만 선택해야 합니다.");
         return;
     }
     const auto picked=view.SelectedItem();
     const auto row=picked.try_as<ListViewItem>();
     if(!row||!row.Tag()){
         StatusText().Text(L"이름을 변경할 파일 또는 폴더를 선택하세요.");
         return;
     }
     const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
     auto const* indexed=pane.tabs[tab].indexedItem(
         static_cast<std::size_t>(logical));
     if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
         StatusText().Text(L"가상 Shell 항목은 이 파일 작업에서 변경할 수 없습니다.");
         return;
     }
     request.source=indexed->parsingName;
 }
 auto dispatch=DispatcherQueue();
 FileOperationController::Post post=[dispatch](FileOperationController::UiTask task){
     try{
         return dispatch.TryEnqueue([task=std::move(task)]() mutable{task();});
     }catch(...){return false;}
 };
 auto weak=get_weak();
 const auto status=mFileOperations.startFileCommand(
     std::move(request),FileOperationContext(side),std::move(post),
     [weak](FileOperationController::FileCommandCompletion completion){
         if(auto ui=weak.get())ui->OnFileCommandCompleted(std::move(completion));
     });
 if(status==FileOperationController::StartStatus::Started){
     // Do not reassert an earlier failure after this new command finishes.
     ActiveWindowTab().fileOperationNotice.clear();
     SetFileButtonsBusy(true,false);
     StatusText().Text(L"선택한 파일 작업을 별도 스레드에서 처리하는 중입니다...");
 }else if(status==FileOperationController::StartStatus::Busy){
     StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
 }else if(status==FileOperationController::StartStatus::InvalidVisibleContext){
     StatusText().Text(L"파일 작업을 시작한 폴더가 변경됐습니다.");
 }else{
     SetFileButtonsBusy(false,false);
     StatusText().Text(L"파일 작업 스레드를 시작하지 못했습니다.");
 }
}
void MainWindow::OnFileCommandCompleted(
 FileOperationController::FileCommandCompletion completion){
 using Disposition=FileOperationController::CommandDisposition;
 const auto disposition=mFileOperations.acceptFileCommand(
     completion,FileOperationContext(completion.context.side));
 if(disposition==Disposition::Ignored)return;
 const bool originActive=completion.context.windowTabIdentity==
                         ActiveWindowTab().identity;
 auto rememberOrigin=[&](std::wstring const& message){
     for(std::size_t i=0;i<mWorkspace.count();++i){
         auto& state=mWorkspace.state(i);
         if(state.identity==completion.context.windowTabIdentity){
             state.fileOperationNotice=message;
             return;
         }
     }
 };
 SetFileButtonsBusy(false,false);
 if(disposition==Disposition::StaleContext){
     // Switching WindowTab, PaneTab or folder must never update another
     // workspace's visible status. Keep the warning in its original tab.
     const std::wstring notice=
         L"파일 작업이 종료됐지만 화면이 변경됐습니다. 원본 폴더에서 결과를 확인하세요.";
     rememberOrigin(notice);
     if(originActive)StatusText().Text(hstring(notice));
     return;
 }
 if(disposition==Disposition::Failed){
     const std::wstring notice=koreanError(completion.result.error).c_str();
     rememberOrigin(notice);
     if(originActive)StatusText().Text(hstring(notice));
     return;
 }
 fileBar()->EndNameEdit();
 if(originActive)StatusText().Text(
     completion.kind==fxfile::filecommand::Kind::CreateFolder?
     L"새 폴더를 만들었습니다.":L"이름을 변경했습니다.");
 auto const& pane=ActiveWindowTab().model.panes[completion.context.side];
 QueuePidl(completion.context.side,
   fxfile::shellnav::Location(
       pane.tabs[pane.active].snapshot().folder),
   fxfile::shellnav::NavigationAction::Refresh);
}

}
