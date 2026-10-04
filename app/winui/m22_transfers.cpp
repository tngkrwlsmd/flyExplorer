#include "pch.h"
#include "MainWindow.xaml.h"
#include "../../src/base/shell_context_core.h"
#include "../../src/base/shell_isolation_wire.h"
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Windows.System.h>
#include <thread>
#include <chrono>
#include <utility>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
using FileOperationController=fxfile::previewops::FileOperationController;
namespace {
hstring errorInKorean(DWORD err){
 switch(err){
 case ERROR_ALREADY_EXISTS:return L"같은 이름의 항목이 있습니다. 덮어쓰지 않았습니다.";
 case ERROR_CANCELLED:return L"파일 작업을 취소했습니다.";
 case ERROR_ACCESS_DENIED:return L"파일 작업을 수행할 권한이 없습니다.";
 case ERROR_NOT_SUPPORTED:return L"연결 지점 또는 지원하지 않는 경로에서는 사용할 수 없습니다.";
 case ERROR_INVALID_NAME:
 case ERROR_INVALID_PARAMETER:return L"원본 또는 대상 경로가 올바르지 않습니다.";
 default:return hstring(L"Shell 파일 작업을 완료하지 못했습니다. 오류: "+
                              std::to_wstring(err));
 }
}
}
void MainWindow::SetFileButtonsBusy(bool busy,bool cancellable){
 CreateFolderButton().IsEnabled(!busy);
 fileBar()->WindowsPasteButton().IsEnabled(!busy);
 fileBar()->CancelButton().IsEnabled(busy&&cancellable);
 UpdateCommandAvailability();
 if(!busy)fileBar()->OperationProgress().Value(0);
}
void MainWindow::OnCopySelected(IInspectable const&,RoutedEventArgs const&){
 RunTransfer(fxfile::shelltransfer::Kind::Copy);
}
void MainWindow::OnMoveSelected(IInspectable const&,RoutedEventArgs const&){
 RunTransfer(fxfile::shelltransfer::Kind::Move);
}
void MainWindow::OnRecycleSelected(IInspectable const&,RoutedEventArgs const&){
 RunTransfer(fxfile::shelltransfer::Kind::Recycle);
}
void MainWindow::OnCancelTransfer(IInspectable const&,RoutedEventArgs const&){
 if(mFileOperations.cancellable()){
  mFileOperations.cancel();
  StatusText().Text(L"Shell 파일 작업 취소를 요청했습니다.");
 }
}
void MainWindow::OnFileRightTapped(
 IInspectable const& sender,Microsoft::UI::Xaml::Input::RightTappedRoutedEventArgs const&){
 auto list=sender.try_as<ListView>();
 if(!list)return;
 if(list==LeftFiles())ActivatePane(0);
 else if(list==RightFiles())ActivatePane(1);
 QueueSelectionPresentationUpdate();
}
void MainWindow::UpdateSort(int selection){
 if(selection<0||selection>7)return;
 const int side=ActiveWindowTab().model.activePane;
 auto& state=ActiveWindowTab().fileLists[side];
 auto const& pane=ActiveWindowTab().model.panes[side];
 auto const& session=pane.tabs[pane.active];
 auto const& snapshot=session.snapshot();
 const auto completeLimit=static_cast<std::size_t>(
  fxfile::isolation::kMaxCompleteModelEntries);
 const bool beyondComplete=
  snapshot.nextOffset>completeLimit||
  (snapshot.nextOffset==completeLimit&&snapshot.truncated);
 if(beyondComplete&&selection>1){
  fileBar()->SetSortIndex(state.sortMode);
  StatusText().Text(
   L"유형/크기/수정 날짜 전역 정렬은 현재 최대 20,000개 항목까지 지원합니다. "
   L"이름 정렬은 경량 인덱스를 사용합니다.");
  return;
 }
 state.sortMode=selection;
 state.indexedNameSort=selection<=1;
 state.indexedNameProjection=beyondComplete&&state.indexedNameSort;
 state.indexToComplete=state.indexedNameProjection&&
  (snapshot.residentEndOffset()<snapshot.nextOffset||snapshot.truncated);
 state.visibleCount=160;
 fileBar()->SetSortIndex(selection);
 UpdateSortPresentation(side);
 FillFiles(side);
 if(state.indexedNameProjection){
  if(state.indexToComplete)
   QueueNextFolderPage(side,true);
  else
   StatusText().Text(L"전체 이름 인덱스로 정렬했습니다.");
  return;
 }
 if(snapshot.baseOffset||
    snapshot.residentEndOffset()<snapshot.nextOffset||
    snapshot.truncated)
  QueueNextFolderPage(side,true);
}
void MainWindow::RunTransfer(fxfile::shelltransfer::Kind kind){
 if(mFileOperations.busy()){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 const int side=ActiveWindowTab().model.activePane;
 auto const& pane=ActiveWindowTab().model.panes[side];
 auto const tab=pane.active;
 if(pane.pending[tab]||pane.filesystemPaths[tab].empty()){
  StatusText().Text(L"실제 폴더를 완전히 불러온 후 파일 작업을 시작하세요.");
  return;
 }
 fxfile::shelltransfer::Request req{};
 req.kind=kind;
 req.sourceParent=pane.filesystemPaths[tab];
 if(kind!=fxfile::shelltransfer::Kind::Recycle){
  if(!ActiveWindowTab().model.split){
   StatusText().Text(L"좌우 창을 모두 연 뒤 반대쪽 폴더로 복사하거나 이동하세요.");
   return;
  }
  const auto& other=ActiveWindowTab().model.panes[1-side];
  if(other.pending[other.active]||other.filesystemPaths[other.active].empty()){
   StatusText().Text(L"반대쪽 창의 실제 폴더를 먼저 불러오세요.");
   return;
  }
  req.destination=other.filesystemPaths[other.active];
 }
 auto list=side==0?LeftFiles():RightFiles();
 auto const& session=pane.tabs[tab];
 for(auto const& value:list.SelectedItems()){
  const auto row=value.try_as<ListViewItem>();
  if(!row||!row.Tag()){StatusText().Text(L"선택한 항목을 읽지 못했습니다.");return;}
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
  if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
   StatusText().Text(L"가상 Shell 항목은 이 파일 작업에서 지원하지 않습니다.");
   return;
  }
  req.sources.push_back(indexed->parsingName);
  if(req.sources.size()>32){
   StatusText().Text(L"파일 작업 한 번에 최대 32개 항목을 선택할 수 있습니다.");
   return;
  }
 }
 if(req.sources.empty()){
  StatusText().Text(L"작업할 파일 또는 폴더를 선택하세요.");
  return;
 }
 StartTransfer(std::move(req));
}
FileOperationController::Context MainWindow::FileOperationContext(int side) const{
 FileOperationController::Context context{};
 if(side<0||side>1)return context;
 auto const& pane=ActiveWindowTab().model.panes[static_cast<std::size_t>(side)];
 if(pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size())return context;
 context.side=side;
 context.tab=pane.active;
 context.route=pane.routeIds[pane.active];
 context.visibleFolder=pane.filesystemPaths[pane.active];
 return context;
}
namespace {
FileOperationController::Post operationPost(
 Microsoft::UI::Dispatching::DispatcherQueue const& dispatch){
 return [dispatch](FileOperationController::UiTask task){
  try{
   return dispatch.TryEnqueue([task=std::move(task)]() mutable{task();});
  }catch(...){return false;}
 };
}
}
void MainWindow::ApplyTransferStartStatus(
 FileOperationController::StartStatus status,std::size_t recycleCount){
 using Start=FileOperationController::StartStatus;
 if(status==Start::Started){
  SetFileButtonsBusy(true,true);
  StatusText().Text(L"Windows Shell에서 파일 작업을 처리하고 있습니다...");
  auto progress=mFileOperations.progress();
  if(mTransferTimer)mTransferTimer.Stop();
  auto timer=DispatcherQueue().CreateTimer();
  mTransferTimer=timer;
  timer.Interval(std::chrono::milliseconds(160));
  auto weak=get_weak();
  timer.Tick([weak,progress](auto const&,auto const&){
   if(auto ui=weak.get())
    if(progress&&ui->mFileOperations.progress()==progress)
     ui->fileBar()->OperationProgress().Value(progress->percent.load());
  });
  timer.Start();
  return;
 }
 if(status==Start::NeedsRecycleConfirmation){
  ConfirmRecycle(recycleCount);
  return;
 }
 if(status==Start::Busy)
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
 else if(status==Start::InvalidVisibleContext)
  StatusText().Text(L"현재 창이 원본이나 대상 폴더와 일치하지 않습니다.");
 else if(status==Start::StaleConfirmation)
  StatusText().Text(L"확인하는 동안 원본 또는 대상 폴더가 변경됐습니다. 다시 선택하세요.");
 else if(status==Start::ThreadStartFailed){
  SetFileButtonsBusy(false,false);
  StatusText().Text(L"별도 Shell 파일 작업 스레드를 시작하지 못했습니다.");
 }
}
void MainWindow::StartTransfer(fxfile::shelltransfer::Request request){
 const auto side=ActiveWindowTab().model.activePane;
 const auto count=request.sources.size();
 auto weak=get_weak();
 const auto status=mFileOperations.requestTransfer(
  std::move(request),FileOperationContext(side),
  operationPost(DispatcherQueue()),
  [weak](FileOperationController::TransferCompletion completion){
   if(auto ui=weak.get())ui->OnTransferCompleted(std::move(completion));
  });
 ApplyTransferStartStatus(status,count);
}
winrt::fire_and_forget MainWindow::ConfirmRecycle(std::size_t count){
 const auto keep=get_strong();
 ContentDialog dialog;
 dialog.XamlRoot(RootShell().XamlRoot());
 dialog.Title(winrt::box_value(hstring(L"휴지통으로 보내기")));
 dialog.Content(winrt::box_value(hstring(
     L"선택한 항목 "+std::to_wstring(count)+
     L"개를 Windows 휴지통으로 이동할까요? 삭제할 항목을 확인하세요.")));
 dialog.PrimaryButtonText(L"휴지통으로 보내기");
 dialog.CloseButtonText(L"취소");
 dialog.DefaultButton(ContentDialogButton::Close);
 const bool approved=co_await dialog.ShowAsync()==ContentDialogResult::Primary;
 auto weak=get_weak();
 const auto status=mFileOperations.confirmRecycle(
  approved,FileOperationContext(ActiveWindowTab().model.activePane),
  operationPost(DispatcherQueue()),
  [weak](FileOperationController::TransferCompletion completion){
   if(auto ui=weak.get())ui->OnTransferCompleted(std::move(completion));
  });
 ApplyTransferStartStatus(status,count);
}
winrt::fire_and_forget MainWindow::ConfirmCollision(){
 const auto keep=get_strong();
 ContentDialog dialog;
 dialog.XamlRoot(RootShell().XamlRoot());
 dialog.Title(winrt::box_value(hstring(L"동일한 이름이 이미 존재합니다")));
 dialog.Content(winrt::box_value(hstring(
    L"대상 폴더에 같은 이름이 있습니다. 기존 항목을 덮어쓰지 않고 "
    L"새 항목의 이름을 자동으로 바꿔 둘 다 유지할까요?")));
 dialog.PrimaryButtonText(L"이름 변경 후 계속");
 dialog.CloseButtonText(L"취소");
 dialog.DefaultButton(ContentDialogButton::Close);
 const bool approved=co_await dialog.ShowAsync()==ContentDialogResult::Primary;
 auto weak=get_weak();
 const auto status=mFileOperations.confirmCollision(
  approved,FileOperationContext(ActiveWindowTab().model.activePane),
  operationPost(DispatcherQueue()),
  [weak](FileOperationController::TransferCompletion completion){
   if(auto ui=weak.get())ui->OnTransferCompleted(std::move(completion));
  });
 ApplyTransferStartStatus(status);
}
void MainWindow::OnTransferCompleted(
 FileOperationController::TransferCompletion completion){
 using Disposition=FileOperationController::TransferDisposition;
 const auto disposition=mFileOperations.acceptTransfer(
  completion,FileOperationContext(completion.context.side));
 if(disposition==Disposition::Ignored)return;
 if(mTransferTimer)mTransferTimer.Stop();
 SetFileButtonsBusy(false,false);
 if(disposition==Disposition::StaleContext){
  StatusText().Text(L"파일 작업 종료: 작업 이후 화면이 변경됐습니다.");
  return;
 }
 if(disposition==Disposition::NeedsCollisionConfirmation){
  ConfirmCollision();
  return;
 }
 if(disposition==Disposition::Failed){
  StatusText().Text(errorInKorean(completion.report.error));
  return;
 }
 StatusText().Text(
  completion.request.kind==fxfile::shelltransfer::Kind::Copy?
    L"복사를 완료했습니다.":
  completion.request.kind==fxfile::shelltransfer::Kind::Move?
    L"이동을 완료했습니다.":L"휴지통 이동을 완료했습니다.");

 // A watcher may already have a request in flight. Always submit a new
 // Refresh for every currently visible touched folder; ShellNavigationController
 // supersedes older same-pane work and the model rejects stale request IDs.
 for(int side=0;side<2;++side){
  if(side==1&&!ActiveWindowTab().model.split)continue;
  auto const& pane=ActiveWindowTab().model.panes[side];
  if(pane.active>=pane.filesystemPaths.size())continue;
  const auto& visible=pane.filesystemPaths[pane.active];
  const bool touched=std::any_of(
   completion.touchedFolders.begin(),completion.touchedFolders.end(),
   [&](std::wstring const& folder){return folder==visible;});
  if(!touched)continue;
  QueuePidl(side,
   fxfile::shellnav::Location(pane.tabs[pane.active].snapshot().folder),
   fxfile::shellnav::NavigationAction::Refresh);
 }
}
bool MainWindow::CopySelectedToWindowsClipboard(int side,bool cut){
 auto const& pane=ActiveWindowTab().model.panes[side];
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty()){
  StatusText().Text(L"폴더를 완전히 불러온 후 항목을 선택하세요.");return false;
 }
 const auto view=side==0?LeftFiles():RightFiles();
 const auto& session=pane.tabs[pane.active];
 fxfile::shellclipboard::Payload item{};
 item.move=cut;
 for(auto const& selected:view.SelectedItems()){
  auto const row=selected.try_as<ListViewItem>();
  if(!row||!row.Tag())return false;
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
  if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty())return false;
  item.paths.push_back(indexed->parsingName);
  if(item.paths.size()>32)return false;
 }
 if(!fxfile::shellclipboard::valid(item)){
  StatusText().Text(L"Windows 클립보드에 넣을 파일 1~32개를 선택하세요.");
  return false;
 }
 // OpenClipboard owner must be a live app-owned HWND. GetActiveWindow()
 // addresses only windows attached to THIS UI thread. If the event is
 // somehow dispatched in the background, do NOT take the user's clipboard.
 HWND hwnd=::GetActiveWindow();
 DWORD ownerPid=0;
 if(hwnd)::GetWindowThreadProcessId(hwnd,&ownerPid);
 if(!hwnd||ownerPid!=::GetCurrentProcessId()){
  StatusText().Text(L"현재 WinUI 창을 활성화한 후 다시 시도하세요.");
  return false;
 }
 const auto err=fxfile::shellclipboard::write(hwnd,item);
 if(err!=ERROR_SUCCESS){
  StatusText().Text(L"Windows 클립보드에 파일 목록을 쓰지 못했습니다.");
  return false;
 }
 StatusText().Text(cut?
  L"선택한 파일을 Windows 클립보드에 잘라내기로 저장했습니다.":
  L"선택한 파일을 Windows 클립보드에 복사했습니다.");
 return true;
}
void MainWindow::PasteFromWindowsClipboard(){
 if(mFileOperations.busy()){
  StatusText().Text(L"이전 파일 작업이 끝난 후 붙여넣으세요.");return;
 }
 const auto& pane=ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane];
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty()){
  StatusText().Text(L"먼저 실제 대상 폴더를 불러오세요.");return;
 }
 fxfile::shellclipboard::Payload data;
 if(fxfile::shellclipboard::read(data)!=ERROR_SUCCESS){
  StatusText().Text(L"Windows 클립보드에 지원하는 로컬 파일 목록이 없습니다.");
  return;
 }
 // M2.3 accepted native core supports ONE verified source parent per
 // operation. Do NOT try to silently copy arbitrary mixed origin folders.
 std::filesystem::path origin(data.paths.front());
 auto const parent=origin.parent_path().native();
 for(auto const& full:data.paths)
  if(!std::filesystem::path(full).has_parent_path()||
      ::CompareStringOrdinal(
        std::filesystem::path(full).parent_path().c_str(),-1,
        parent.c_str(),-1,TRUE)!=CSTR_EQUAL){
   StatusText().Text(
     L"서로 다른 원본 폴더에서 복사한 항목은 한 번에 붙여넣을 수 없습니다.");
   return;
  }
 fxfile::shelltransfer::Request request{};
 request.kind=data.move?fxfile::shelltransfer::Kind::Move:
                        fxfile::shelltransfer::Kind::Copy;
 request.sourceParent=parent;
 request.destination=pane.filesystemPaths[pane.active];
 request.sources=std::move(data.paths);
 // The common C++ layer always revalidates every current source and
 // destination path immediately before COM STA Shell mutation.
 StartTransfer(std::move(request));
}
void MainWindow::OnWindowsCopy(IInspectable const&,RoutedEventArgs const&){
 CopySelectedToWindowsClipboard(ActiveWindowTab().model.activePane,false);
}
void MainWindow::OnWindowsCut(IInspectable const&,RoutedEventArgs const&){
 CopySelectedToWindowsClipboard(ActiveWindowTab().model.activePane,true);
}
void MainWindow::OnWindowsPaste(IInspectable const&,RoutedEventArgs const&){
 PasteFromWindowsClipboard();
}
void MainWindow::OnExternalWindowsContextMenu(
 IInspectable const&,RoutedEventArgs const&){
 if(mFileOperations.busy()){
  StatusText().Text(L"Shell \uC791\uC5C5\uC774 \uB05D\uB09C \uB4A4 \uC2DC\uB3C4\uD558\uC138\uC694.");
  return;
 }
 const auto side=ActiveWindowTab().model.activePane;
 auto const& pane=ActiveWindowTab().model.panes[side];
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty())
  return;
 auto list=side==0?LeftFiles():RightFiles();
 if(list.SelectedItems().Size()!=1){
  StatusText().Text(L"\uC678\uBD80 Shell \uBA54\uB274\uB294 \uD56D\uBAA9 1\uAC1C\uB97C \uC120\uD0DD\uD558\uC138\uC694.");
  return;
 }
 auto row=list.SelectedItems().GetAt(0).try_as<ListViewItem>();
 if(!row||!row.Tag())return;
 const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
 auto const& session=pane.tabs[pane.active];
 auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
 if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty())return;
 auto path=indexed->parsingName;
 auto const value=std::filesystem::path(path);
 if(!value.is_absolute()||value.lexically_normal().native()!=path||
    path.size()>1024)return;
 const auto root=value.root_path().native();
 if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return;
 const auto flags=::GetFileAttributesW(path.c_str());
 if(flags==INVALID_FILE_ATTRIBUTES||
    (flags&FILE_ATTRIBUTE_REPARSE_POINT))return;
 HWND hwnd=::GetActiveWindow();
 DWORD owner=0;
 if(hwnd)::GetWindowThreadProcessId(hwnd,&owner);
 if(!hwnd||owner!=::GetCurrentProcessId())return;
 wchar_t exe[32768]{};
 DWORD length=::GetModuleFileNameW(nullptr,exe,32768);
 if(!length||length>=32768)return;
 auto helper=(std::filesystem::path(exe).parent_path()/
               L"FlyShellIsolationHelper.exe").native();
 POINT cursor{};
 if(!::GetCursorPos(&cursor))return;
 auto dispatch=DispatcherQueue();
 auto weak=get_weak();
 StatusText().Text(L"Windows Shell \uD655\uC7A5 \uBA54\uB274\uB97C \uBD84\uB9AC\uB41C \uD504\uB85C\uC138\uC2A4\uC5D0\uC11C \uC5FD\uB2C8\uB2E4.");
 try{
  std::thread([helper=std::move(helper),path=std::move(path),
               cursor,dispatch,weak]{
    const DWORD code=fxfile::shellcontext::show(helper,path,cursor,45000);
    dispatch.TryEnqueue([weak,code]{
      if(auto ui=weak.get()){
       if(code==0)ui->StatusText().Text(
          L"Windows Shell \uD655\uC7A5 \uBA54\uB274\uAC00 \uC885\uB8CC\uB410\uC2B5\uB2C8\uB2E4.");
       else ui->StatusText().Text(
          L"Windows Shell \uD655\uC7A5 \uBA54\uB274\uB97C \uC644\uB8CC\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.");
      }
    });
  }).detach();
 }catch(...){
  StatusText().Text(L"Shell \uBA54\uB274 \uB3C5\uB9BD \uC791\uC5C5\uC790\uB97C \uC2DC\uC791\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.");
 }
}
void MainWindow::StartInternalPaste(){
 if(mClipboardSources.empty()||mFileOperations.busy()){
  StatusText().Text(L"앱 내부에 붙여넣을 항목이 없습니다.");return;
 }
 auto const& pane=ActiveWindowTab().model.panes[ActiveWindowTab().model.activePane];
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty()){
  StatusText().Text(L"붙여넣을 대상 폴더를 먼저 불러오세요.");return;
 }
 fxfile::shelltransfer::Request request{};
 request.sourceParent=mClipboardParent;
 request.sources=mClipboardSources;
 request.destination=pane.filesystemPaths[pane.active];
 request.kind=mClipboardMove?fxfile::shelltransfer::Kind::Move:
                             fxfile::shelltransfer::Kind::Copy;
 StartTransfer(std::move(request));
}
void MainWindow::HandleFileShortcut(
 int side,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){
 if(side!=ActiveWindowTab().model.activePane)ActivatePane(side);
 const auto vk=args.Key();
 const auto ctrl=(::GetKeyState(VK_CONTROL)&0x8000)!=0;
 const auto shift=(::GetKeyState(VK_SHIFT)&0x8000)!=0;
 if(ctrl&&shift&&vk==Windows::System::VirtualKey::F){
  auto box=side==0?LeftNameFilterBox():RightNameFilterBox();
  box.Focus(Microsoft::UI::Xaml::FocusState::Keyboard);
  box.SelectAll();
  args.Handled(true);return;
 }
 auto view=side==0?LeftFiles():RightFiles();
 if(ctrl&&vk==Windows::System::VirtualKey::A){
  view.SelectAll();args.Handled(true);return;
 }
 if(ctrl&&(vk==Windows::System::VirtualKey::C||
           vk==Windows::System::VirtualKey::X)){
  CopySelectedToWindowsClipboard(
    side,vk==Windows::System::VirtualKey::X);
  args.Handled(true);return;
 }
 if(ctrl&&vk==Windows::System::VirtualKey::V){
  PasteFromWindowsClipboard();args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::F2){
  BeginFileNameCommand(fxfile::filecommand::Kind::RenameSelected);args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::F5){
  RunTransfer(fxfile::shelltransfer::Kind::Copy);args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::F6){
  RunTransfer(fxfile::shelltransfer::Kind::Move);args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::Delete){
  RunTransfer(fxfile::shelltransfer::Kind::Recycle);args.Handled(true);
 }
}
}
