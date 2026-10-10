#include "pch.h"
#include "MainWindow.xaml.h"
#include "../../src/base/shell_context_core.h"
#include "../../src/base/shell_isolation_wire.h"
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Microsoft.UI.Xaml.Media.h>
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
bool copyPidlBytes(PCIDLIST_ABSOLUTE value,
                   std::vector<unsigned char>& out) noexcept{
 out.clear();
 if(!value)return false;
 const auto bytes=static_cast<std::size_t>(::ILGetSize(value));
 if(bytes<sizeof(USHORT)||bytes>fxfile::shelltransfer::kMaxProviderPidlBytes)
  return false;
 try{
  out.resize(bytes);
  std::memcpy(out.data(),value,bytes);
  return true;
 }catch(...){out.clear();return false;}
}
bool removableLocalRoot(std::wstring const& value) noexcept{
 try{
  const auto root=std::filesystem::path(value).root_path().native();
  return root.size()==3&&root[1]==L':'&&root[2]==L'\\'&&
         ::GetDriveTypeW(root.c_str())==DRIVE_REMOVABLE;
 }catch(...){return false;}
}
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
 IInspectable const& sender,Microsoft::UI::Xaml::Input::RightTappedRoutedEventArgs const& args){
 auto list=sender.try_as<ListView>();
 if(!list)return;
 const int side=list==LeftFiles()?0:list==RightFiles()?1:-1;
 if(side<0)return;
 ActivatePane(side);

 ListViewItem clicked{nullptr};
 auto current=args.OriginalSource().try_as<DependencyObject>();
 while(current){
  if(auto row=current.try_as<ListViewItem>()){clicked=row;break;}
  current=Microsoft::UI::Xaml::Media::VisualTreeHelper::GetParent(current);
 }
 if(!clicked)return;
 if(list.SelectedItems().Size()!=1||!clicked.IsSelected()){
  list.SelectedItems().Clear();
  clicked.IsSelected(true);
 }
 args.Handled(true);
 QueueSelectionPresentationUpdate();
 ShowExternalWindowsContextMenu(side);
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
 // Only local fixed-drive items qualify for the bounded metadata index.
 std::wstring root;
 auto const& folder=pane.filesystemPaths[pane.active];
 const bool fixedLocal=
  selection>1&&fxfile::shelltransfer::transferDriveRoot(folder,root)&&
  root.size()==3&&root[1]==L':'&&root[2]==L'\\'&&
  ::GetDriveTypeW(root.c_str())==DRIVE_FIXED;
 const bool metadataIndexEligible=fixedLocal&&
  snapshot.nextOffset<=fxfile::previewmetadata::kMaxIndexedMetadataEntries;
 if(beyondComplete&&selection>1&&!metadataIndexEligible){
  fileBar()->SetSortIndex(state.sortMode);
  StatusText().Text(
   L"유형·크기·수정일의 20,000개 초과 정렬은 로컬 고정 디스크에서 "
   L"최대 25,000개까지 지원합니다. 현재 정렬은 유지됩니다.");
  return;
 }
 state.sortMode=selection;
 state.indexedNameSort=selection<=1;
 state.indexedMetadataSort=selection>1&&metadataIndexEligible;
 state.indexedNameProjection=beyondComplete&&
  (state.indexedNameSort||state.indexedMetadataSort);
 state.indexToComplete=state.indexedNameProjection&&
  (snapshot.residentEndOffset()<snapshot.nextOffset||snapshot.truncated);
 state.visibleCount=160;
 fileBar()->SetSortIndex(selection);
 UpdateSortPresentation(side);
 FillFiles(side);
 if(state.indexedNameProjection){
  if(state.indexToComplete){
   QueueNextFolderPage(side,true);
  }else if(state.indexedMetadataSort){
   ScheduleFileMetadata(side);
   if(state.metadataCurrent(
       pane.routeIds[pane.active],pane.active,session.nameIndex().size()))
    StatusText().Text(L"전체 메타데이터 인덱스로 정렬했습니다.");
   else
    StatusText().Text(L"인덱스 기반 파일 메타데이터 정렬을 준비합니다.");
  }else{
   StatusText().Text(L"전체 이름 인덱스로 정렬했습니다.");
  }
  return;
 }
 const bool incomplete=
  state.indexedMetadataSort&&state.indexedNameProjection?
   (state.indexToComplete||snapshot.truncated||
    session.indexedFrontier()!=snapshot.nextOffset):
   (snapshot.baseOffset||
    snapshot.residentEndOffset()<snapshot.nextOffset||
    snapshot.truncated);
 if(selection>1){
  if(incomplete){
   if(QueueNextFolderPage(side,true))
    StatusText().Text(L"정렬을 위해 전체 폴더 항목을 불러오는 중입니다.");
   return;
  }
  ScheduleFileMetadata(side);
  if(state.metadataCurrent(
       pane.routeIds[pane.active],pane.active,snapshot.children.size()))
   StatusText().Text(L"파일 메타데이터 정렬을 적용했습니다.");
  else
   StatusText().Text(L"정렬을 위해 파일 메타데이터를 준비하는 중입니다.");
  return;
 }
 if(incomplete)QueueNextFolderPage(side,true);
}
void MainWindow::RunTransfer(fxfile::shelltransfer::Kind kind){
 if(mFileOperations.busy()){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 const int side=ActiveWindowTab().model.activePane;
 auto const& pane=ActiveWindowTab().model.panes[side];
 const auto tab=pane.active;
 if(pane.pending[tab]){
  StatusText().Text(L"현재 위치를 완전히 불러온 후 파일 작업을 시작하세요.");
  return;
 }
 auto const& session=pane.tabs[tab];
 auto const& snapshot=session.snapshot();
 auto list=side==0?LeftFiles():RightFiles();
 struct Selected final {
  fxfile::shellnav::IndexedItem const* item=nullptr;
  std::uint64_t logical=0;
 };
 std::vector<Selected> chosen;
 chosen.reserve(list.SelectedItems().Size());
 bool providerSource=pane.filesystemPaths[tab].empty();
 for(auto const& value:list.SelectedItems()){
  const auto row=value.try_as<ListViewItem>();
  if(!row||!row.Tag()){
   StatusText().Text(L"선택한 항목을 읽지 못했습니다.");
   return;
  }
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
  if(!indexed||indexed->parsingName.empty()){
   StatusText().Text(L"선택한 Shell 항목의 원본 정보를 읽지 못했습니다.");
   return;
  }
  if(!indexed->isFileSystem())providerSource=true;
  chosen.push_back(Selected{indexed,logical});
 }
 if(chosen.empty()){
  StatusText().Text(L"작업할 파일 또는 폴더를 선택하세요.");
  return;
 }

 if(providerSource&&kind!=fxfile::shelltransfer::Kind::Copy){
  StatusText().Text(
   L"가상 Shell/provider 항목은 현재 반대쪽 실제 폴더로 복사만 지원합니다.");
  return;
 }

 fxfile::shelltransfer::Request req{};
 req.kind=kind;
 req.sourceMode=providerSource?
   fxfile::shelltransfer::SourceMode::ShellProvider:
   fxfile::shelltransfer::SourceMode::Filesystem;
 if(providerSource){
  if(!snapshot.folder.valid()||snapshot.parsingName.empty()||
     snapshot.parsingName.size()>fxfile::shelltransfer::kMaxProviderParsingUnits){
   StatusText().Text(L"현재 Shell provider 위치의 원본 정보를 사용할 수 없습니다.");
   return;
  }
  req.sourceParent=snapshot.parsingName;
  if(!copyPidlBytes(snapshot.folder.get(),req.sourceParentPidl)){
   StatusText().Text(L"현재 Shell provider 위치의 PIDL 정보를 사용할 수 없습니다.");
   return;
  }
 }else{
  if(pane.filesystemPaths[tab].empty()){
   StatusText().Text(L"실제 원본 폴더를 완전히 불러온 후 다시 시도하세요.");
   return;
  }
  req.sourceParent=pane.filesystemPaths[tab];
 }

 if(kind!=fxfile::shelltransfer::Kind::Recycle){
  if(!ActiveWindowTab().model.split){
   StatusText().Text(L"좌우 창을 모두 연 뒤 반대쪽 폴더로 복사하거나 이동하세요.");
   return;
  }
  const auto& other=ActiveWindowTab().model.panes[1-side];
  if(other.pending[other.active]){
   StatusText().Text(L"반대쪽 창의 폴더를 완전히 불러오세요.");
   return;
  }
  if(!other.filesystemPaths[other.active].empty()){
   req.destination=other.filesystemPaths[other.active];
  }else if(!providerSource&&kind==fxfile::shelltransfer::Kind::Copy){
   auto const& target=other.tabs[other.active].snapshot();
   if(!target.folder.valid()||target.parsingName.empty()||
      target.parsingName.size()>fxfile::shelltransfer::kMaxProviderParsingUnits||
      !copyPidlBytes(target.folder.get(),req.destinationPidl)){
    StatusText().Text(L"대상 Shell provider의 식별자를 사용할 수 없습니다.");
    return;
   }
   req.destinationMode=fxfile::shelltransfer::DestinationMode::ShellProvider;
   req.destination=target.parsingName;
  }else{
   StatusText().Text(L"가상 Shell/provider 대상에는 실제 폴더의 파일 복사만 지원합니다.");
   return;
  }
 }

 std::size_t sourceUnits=0;
 std::size_t providerPidlBytes=req.sourceParentPidl.size();
 for(auto const& picked:chosen){
  auto const* indexed=picked.item;
  if(providerSource){
   // Navigation snapshots do not request SFGAO_CANCOPY. Keep provider
   // capability probing inside the exact-owned transfer helper for only the
   // selected items immediately before Shell mutation.
   if(indexed->parsingName.size()>
      fxfile::shelltransfer::kMaxProviderParsingUnits){
    StatusText().Text(L"선택한 Shell provider 항목의 식별자가 너무 깁니다.");
    return;
   }
   std::size_t resident=0;
   if(!snapshot.residentIndex(picked.logical,resident)||
      resident>=snapshot.children.size()){
    StatusText().Text(L"선택한 Shell provider 항목이 현재 snapshot에 없습니다.");
    return;
   }
   std::vector<unsigned char> childPidl;
   if(!copyPidlBytes(snapshot.children[resident].id.get(),childPidl)||
      childPidl.size()>fxfile::shelltransfer::kMaxProviderPidlBytesTotal-
                       providerPidlBytes){
    StatusText().Text(L"선택한 Shell provider PIDL 크기 제한을 초과했습니다.");
    return;
   }
   providerPidlBytes+=childPidl.size();
   req.sourcePidls.push_back(std::move(childPidl));
  }else if(!indexed->isFileSystem()){
   StatusText().Text(L"가상 Shell/provider 항목은 별도 Copy-out 경로가 필요합니다.");
   return;
  }
  const auto identityUnits=indexed->parsingName.size()+1;
  if(req.sources.size()>=fxfile::shelltransfer::kMaxItems||
     identityUnits>fxfile::shelltransfer::kMaxSourcePathUnits-sourceUnits){
   StatusText().Text(hstring(L"파일 작업은 최대 "+
      std::to_wstring(fxfile::shelltransfer::kMaxItems)+
      L"개 항목과 제한된 전체 원본 식별자 크기 안에서 실행할 수 있습니다."));
   return;
  }
  sourceUnits+=identityUnits;
  req.sources.push_back(indexed->parsingName);
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
 context.visibleShellFolder=
     pane.tabs[pane.active].snapshot().parsingName;
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
     L"개를 Windows 휴지통으로 이동할까요? 삭제할 항목을 확인하세요. "
     L"휴지통을 사용할 수 없으면 영구 삭제로 전환하지 않고 작업을 중단합니다.")));
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
  if(completion.request.kind==fxfile::shelltransfer::Kind::Recycle&&
     removableLocalRoot(completion.request.sourceParent)){
   StatusText().Text(hstring(
    L"이 이동식 드라이브의 Windows 휴지통으로 이동을 완료하지 못했습니다. "
    L"영구 삭제로 전환하지 않았습니다. 오류: "+
    std::to_wstring(completion.report.error)));
  }else StatusText().Text(errorInKorean(completion.report.error));
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
  const auto& shellVisible=pane.tabs[pane.active].snapshot().parsingName;
  const bool providerTarget=completion.request.destinationMode==
      fxfile::shelltransfer::DestinationMode::ShellProvider;
  const bool touched=std::any_of(
   completion.touchedFolders.begin(),completion.touchedFolders.end(),
   [&](std::wstring const& folder){
    return folder==visible||(providerTarget&&folder==shellVisible);
   });
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
 std::size_t clipboardPathUnits=0;
 for(auto const& selected:view.SelectedItems()){
  auto const row=selected.try_as<ListViewItem>();
  if(!row||!row.Tag())return false;
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
  if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty())return false;
  const auto pathUnits=indexed->parsingName.size()+1;
  if(item.paths.size()>=fxfile::shelltransfer::kMaxItems||
     pathUnits>fxfile::shelltransfer::kMaxSourcePathUnits-clipboardPathUnits)
   return false;
  clipboardPathUnits+=pathUnits;
  item.paths.push_back(indexed->parsingName);
 }
 if(!fxfile::shellclipboard::valid(item)){
  StatusText().Text(hstring(L"Windows 클립보드 파일 목록은 최대 "+
      std::to_wstring(fxfile::shelltransfer::kMaxItems)+
      L"개이며 전체 경로 크기 제한을 넘지 않아야 합니다."));
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
void MainWindow::ShowExternalWindowsContextMenu(int side){
 if(side<0||side>1)return;

 if(mFileOperations.busy()){
  StatusText().Text(L"Shell \uC791\uC5C5\uC774 \uB05D\uB09C \uB4A4 \uC2DC\uB3C4\uD558\uC138\uC694.");
  return;
 }
 auto const& pane=ActiveWindowTab().model.panes[side];
 if(pane.pending[pane.active]){
  StatusText().Text(L"현재 폴더를 불러온 후 Windows 메뉴를 여세요.");
  return;
 }
 if(pane.filesystemPaths[pane.active].empty()){
  StatusText().Text(L"가상 Shell 항목의 외부 메뉴는 아직 지원하지 않습니다.");
  return;
 }
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
 if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
  StatusText().Text(L"선택한 파일시스템 항목의 Shell 메뉴를 열 수 없습니다.");
  return;
 }
 auto path=indexed->parsingName;
 auto const value=std::filesystem::path(path);
 if(!value.is_absolute()||value.lexically_normal().native()!=path||
    path.size()>1024)return;
 const auto root=value.root_path().native();
 if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED){
  StatusText().Text(
   L"외부 Shell 메뉴는 로컬 고정 디스크만 지원합니다. "
   L"이동식·네트워크·가상 공급자 작업은 아직 제한됩니다.");
  return;
 }
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
void MainWindow::OnExternalWindowsContextMenu(
 IInspectable const&,RoutedEventArgs const&){
 ShowExternalWindowsContextMenu(ActiveWindowTab().model.activePane);
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
 const auto alt=(::GetKeyState(VK_MENU)&0x8000)!=0;
 // Keyboard equivalent of right-click for the selected filesystem row.
 // Reuse the fixed-drive single-item isolated-child safety checks.
 if(!ctrl&&shift&&!alt&&vk==Windows::System::VirtualKey::F10){
  ShowExternalWindowsContextMenu(side);
  args.Handled(true);return;
 }
 if(ctrl&&shift&&!alt&&vk==Windows::System::VirtualKey::F){
  auto box=side==0?LeftNameFilterBox():RightNameFilterBox();
  if(box.Opacity()<0.5)ToggleNameFilter(side);
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
 if(vk==Windows::System::VirtualKey::Delete){
  RunTransfer(fxfile::shelltransfer::Kind::Recycle);args.Handled(true);
 }
}
}
