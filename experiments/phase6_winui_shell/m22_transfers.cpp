#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Windows.System.h>
#include <thread>
#include <chrono>
#include <utility>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorerWinUIShell::implementation {
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
 mFileOperationPending=busy;
 CreateFolderButton().IsEnabled(!busy);
 RenameButton().IsEnabled(!busy);
 fileBar()->CopyButton().IsEnabled(!busy);
 fileBar()->MoveButton().IsEnabled(!busy);
 fileBar()->RecycleButton().IsEnabled(!busy);
 fileBar()->CancelButton().IsEnabled(busy&&cancellable);
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
 if(mTransferProgress){
  mTransferProgress->cancel.store(true);
  StatusText().Text(L"Shell 파일 작업 취소를 요청했습니다.");
 }
}
void MainWindow::OnFileRightTapped(
 IInspectable const& sender,Microsoft::UI::Xaml::Input::RightTappedRoutedEventArgs const&){
 auto list=sender.try_as<ListView>();
 if(!list)return;
 if(list==LeftFiles())ActivatePane(0);
 else if(list==RightFiles())ActivatePane(1);
}
void MainWindow::UpdateSort(int selection){
 if(selection<0||selection>3)return;
 mSortMode[mModel.activePane]=selection;
 FillFiles(mModel.activePane);
}
void MainWindow::RunTransfer(fxfile::shelltransfer::Kind kind){
 if(mFileOperationPending){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 const int side=mModel.activePane;
 auto const& pane=mModel.panes[side];
 auto const tab=pane.active;
 if(pane.pending[tab]||pane.filesystemPaths[tab].empty()){
  StatusText().Text(L"실제 폴더를 완전히 불러온 후 파일 작업을 시작하세요.");
  return;
 }
 fxfile::shelltransfer::Request req{};
 req.kind=kind;
 req.sourceParent=pane.filesystemPaths[tab];
 if(kind!=fxfile::shelltransfer::Kind::Recycle){
  if(!mModel.split){
   StatusText().Text(L"좌우 창을 모두 연 뒤 반대쪽 폴더로 복사하거나 이동하세요.");
   return;
  }
  const auto& other=mModel.panes[1-side];
  if(other.pending[other.active]||other.filesystemPaths[other.active].empty()){
   StatusText().Text(L"반대쪽 창의 실제 폴더를 먼저 불러오세요.");
   return;
  }
  req.destination=other.filesystemPaths[other.active];
 }
 auto list=side==0?LeftFiles():RightFiles();
 auto const& items=pane.tabs[tab].snapshot().children;
 for(auto const& value:list.SelectedItems()){
  const auto row=value.try_as<ListViewItem>();
  if(!row||!row.Tag()){StatusText().Text(L"선택한 항목을 읽지 못했습니다.");return;}
  auto index=winrt::unbox_value<uint32_t>(row.Tag());
  if(index>=items.size()||!items[index].isFileSystem()||
     items[index].parsingName.empty()){
   StatusText().Text(L"가상 Shell 항목은 이 파일 작업에서 지원하지 않습니다.");
   return;
  }
  req.sources.push_back(items[index].parsingName);
  if(req.sources.size()>32){
   StatusText().Text(L"파일 작업 한 번에 최대 32개 항목을 선택할 수 있습니다.");
   return;
  }
 }
 if(req.sources.empty()){
  StatusText().Text(L"작업할 파일 또는 폴더를 선택하세요.");
  return;
 }
 if(kind==fxfile::shelltransfer::Kind::Recycle){
  ConfirmRecycle(std::move(req));return;
 }
 StartTransfer(std::move(req));
}
winrt::fire_and_forget MainWindow::ConfirmRecycle(fxfile::shelltransfer::Request req){
 const auto keep=get_strong();
 ContentDialog dialog;
 dialog.XamlRoot(RootShell().XamlRoot());
 dialog.Title(winrt::box_value(hstring(L"휴지통으로 보내기")));
 dialog.Content(winrt::box_value(hstring(
     L"선택한 항목 "+std::to_wstring(req.sources.size())+
     L"개를 Windows 휴지통으로 이동할까요? 삭제할 항목을 확인하세요.")));
 dialog.PrimaryButtonText(L"휴지통으로 보내기");
 dialog.CloseButtonText(L"취소");
 dialog.DefaultButton(ContentDialogButton::Close);
 if(co_await dialog.ShowAsync()!=ContentDialogResult::Primary)co_return;
 const auto& pane=mModel.panes[mModel.activePane];
 if(pane.pending[pane.active]||
    pane.filesystemPaths[pane.active]!=req.sourceParent){
  StatusText().Text(L"확인하는 동안 원본 폴더가 변경됐습니다. 다시 선택하세요.");
  co_return;
 }
 req.recycleConfirmed=true;
 StartTransfer(std::move(req));
}
winrt::fire_and_forget MainWindow::ConfirmCollision(fxfile::shelltransfer::Request req){
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
 if(co_await dialog.ShowAsync()!=ContentDialogResult::Primary)co_return;
 const auto& source=mModel.panes[mModel.activePane];
 if(source.pending[source.active]||
    source.filesystemPaths[source.active]!=req.sourceParent){
  StatusText().Text(L"확인하는 동안 원본 폴더가 변경됐습니다. 다시 선택하세요.");
  co_return;
 }
 req.collision=fxfile::shelltransfer::Collision::KeepBoth;
 StartTransfer(std::move(req));
}
void MainWindow::StartTransfer(fxfile::shelltransfer::Request request){
 if(mFileOperationPending)return;
 using fxfile::shelltransfer::Progress;
 auto progress=std::make_shared<Progress>();
 mTransferProgress=progress;
 const auto epoch=++mTransferEpoch;
 auto const side=mModel.activePane;
 auto const& pane=mModel.panes[side];
 const auto tab=pane.active,route=pane.routeIds[tab];
 const auto originalParent=request.sourceParent;
 SetFileButtonsBusy(true,true);
 StatusText().Text(L"Windows Shell에서 파일 작업을 처리하고 있습니다...");
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 if(mTransferTimer)mTransferTimer.Stop();
 auto timer=dispatch.CreateTimer();
 mTransferTimer=timer;
 timer.Interval(std::chrono::milliseconds(160));
 timer.Tick([weak,progress](auto const&,auto const&){
  if(auto ui=weak.get())
   if(ui->mTransferProgress==progress)
    ui->fileBar()->OperationProgress().Value(progress->percent.load());
 });
 timer.Start();
 try{
  std::thread([weak,dispatch,progress,request=std::move(request),
               epoch,side,tab,route,originalParent]() mutable{
   const auto result=fxfile::shelltransfer::execute(request,*progress);
   dispatch.TryEnqueue([weak,progress,epoch,side,tab,route,originalParent,
                        result,request=std::move(request)]() mutable{
    if(auto ui=weak.get()){
     if(ui->mTransferEpoch!=epoch||ui->mTransferProgress!=progress)return;
     if(ui->mTransferTimer)ui->mTransferTimer.Stop();
     ui->mTransferProgress.reset();
     ui->SetFileButtonsBusy(false,false);
     auto const& pane=ui->mModel.panes[side];
     // Native data mutation is a user-approved action. A stale callback
     // must not update an unrelated pane/tab after user navigation.
     if(tab>=pane.routeIds.size()||pane.routeIds[tab]!=route||
        pane.filesystemPaths[tab]!=originalParent||pane.active!=tab){
      ui->StatusText().Text(L"파일 작업 종료: 작업 이후 화면이 변경됐습니다.");
      return;
     }
     if(result.error==ERROR_ALREADY_EXISTS&&!result.collisions.empty()&&
        request.kind!=fxfile::shelltransfer::Kind::Recycle){
      ui->ConfirmCollision(std::move(request));return;
     }
     if(result.error!=ERROR_SUCCESS){
      ui->StatusText().Text(errorInKorean(result.error));return;
     }
     ui->StatusText().Text(
      request.kind==fxfile::shelltransfer::Kind::Copy?
        L"복사를 완료했습니다.":
      request.kind==fxfile::shelltransfer::Kind::Move?
        L"이동을 완료했습니다.":L"휴지통 이동을 완료했습니다.");
     ui->QueuePidl(side,
       fxfile::shellnav::Location(pane.tabs[tab].snapshot().folder),
       fxfile::shellnav::NavigationAction::Refresh);
     // Independent watchers refresh the destination pane; force a
     // preview refresh if the other route is still active and stable.
     if(request.kind!=fxfile::shelltransfer::Kind::Recycle){
      auto const& other=ui->mModel.panes[1-side];
      if(!other.pending[other.active]&&
          other.filesystemPaths[other.active]==request.destination){
       ui->QueuePidl(1-side,
         fxfile::shellnav::Location(other.tabs[other.active].snapshot().folder),
         fxfile::shellnav::NavigationAction::Refresh);
      }
     }
    }
   });
  }).detach();
 }catch(...){
  if(mTransferTimer)mTransferTimer.Stop();
  mTransferProgress.reset();
  SetFileButtonsBusy(false,false);
  StatusText().Text(L"별도 Shell 파일 작업 스레드를 시작하지 못했습니다.");
 }
}
void MainWindow::StartInternalPaste(){
 if(mClipboardSources.empty()||mFileOperationPending){
  StatusText().Text(L"앱 내부에 붙여넣을 항목이 없습니다.");return;
 }
 auto const& pane=mModel.panes[mModel.activePane];
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
 if(side!=mModel.activePane)ActivatePane(side);
 const auto vk=args.Key();
 const auto ctrl=(::GetKeyState(VK_CONTROL)&0x8000)!=0;
 auto view=side==0?LeftFiles():RightFiles();
 if(ctrl&&vk==Windows::System::VirtualKey::A){
  view.SelectAll();args.Handled(true);return;
 }
 if(ctrl&&(vk==Windows::System::VirtualKey::C||
           vk==Windows::System::VirtualKey::X)){
  auto const& pane=mModel.panes[side];
  auto const& items=pane.tabs[pane.active].snapshot().children;
  std::vector<std::wstring> picked{};
  for(auto const& value:view.SelectedItems()){
   auto row=value.try_as<ListViewItem>();
   if(!row||!row.Tag())return;
   auto index=winrt::unbox_value<uint32_t>(row.Tag());
   if(index>=items.size()||!items[index].isFileSystem())return;
   picked.push_back(items[index].parsingName);
  }
  if(picked.empty()||picked.size()>32)return;
  mClipboardSources=std::move(picked);
  mClipboardParent=pane.filesystemPaths[pane.active];
  mClipboardMove=vk==Windows::System::VirtualKey::X;
  StatusText().Text(mClipboardMove?
   L"앱 내부에서 이동할 항목을 선택했습니다. Ctrl+V로 붙여넣으세요.":
   L"앱 내부에서 복사할 항목을 선택했습니다. Ctrl+V로 붙여넣으세요.");
  args.Handled(true);return;
 }
 if(ctrl&&vk==Windows::System::VirtualKey::V){
  StartInternalPaste();args.Handled(true);return;
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
