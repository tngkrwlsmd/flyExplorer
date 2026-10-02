#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Windows.ApplicationModel.DataTransfer.h>
#include <winrt/Windows.Storage.h>
#include <winrt/Windows.Foundation.h>
#include <shobjidl.h>
#include <filesystem>
#include <utility>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
using namespace Windows::ApplicationModel::DataTransfer;
namespace winrt::FlyExplorer::implementation {
namespace {
constexpr wchar_t const* PrivateFormat=L"FlyExplorer.M23.OwnedListDrag.v1";
bool traceOwnedDrag(){
 wchar_t flag[16]{};
 const DWORD n=::GetEnvironmentVariableW(
    L"FLY_M23_OWNED_DRAG_TRACE",flag,16);
 return n==3&&::CompareStringOrdinal(flag,-1,L"YES",-1,FALSE)==CSTR_EQUAL;
}

}
void MainWindow::OnFileDragItemsStarting(
 IInspectable const& sender,DragItemsStartingEventArgs const& args){
 auto view=sender.try_as<ListView>();
 const int side=view==LeftFiles()?0:view==RightFiles()?1:-1;
 if(side<0||mFileOperations.busy()||args.Items().Size()==0||
    args.Items().Size()>32){args.Cancel(true);return;}
 auto const& pane=ActiveWindowTab().model.panes[side];
 const auto tab=pane.active;
 if(pane.pending[tab]||pane.filesystemPaths[tab].empty()){
  args.Cancel(true);return;
 }
 auto const& entries=pane.tabs[tab].snapshot().children;
 std::vector<std::wstring> paths{};
 for(auto const& item:args.Items()){
  auto row=item.try_as<ListViewItem>();
  if(!row||!row.Tag()){args.Cancel(true);return;}
  const auto index=unbox_value<uint32_t>(row.Tag());
  if(index>=entries.size()||!entries[index].isFileSystem()||
     entries[index].parsingName.empty()){args.Cancel(true);return;}
  paths.push_back(entries[index].parsingName);
 }
 GUID id{};
 if(FAILED(::CoCreateGuid(&id))){args.Cancel(true);return;}
 wchar_t unique[48]{};
 if(!::StringFromGUID2(id,unique,48)){args.Cancel(true);return;}
 mPrivateDragToken=unique;
 mPrivateDragParent=pane.filesystemPaths[tab];
 mPrivateDragRoute=pane.routeIds[tab];
 mPrivateDragSide=side;
 mPrivateDragSources=std::move(paths);
 StatusText().Text(traceOwnedDrag()?L"끌기 진단: 목록 시작 이벤트 도착":
                        L"앱 내부 파일 끌기를 시작했습니다.");
 args.Data().SetData(hstring(PrivateFormat),
                     box_value(hstring(mPrivateDragToken)));
 args.Data().RequestedOperation(DataPackageOperation::Copy);
}
void MainWindow::OnFileRowDragStarting(
 int side,UIElement const& sender,DragStartingEventArgs const& args){
 auto row=sender.try_as<ListViewItem>();
 if(!row||!row.Tag()||side<0||side>1||mFileOperations.busy()){
  args.Cancel(true);return;
 }
 auto const& pane=ActiveWindowTab().model.panes[side];
 const auto tab=pane.active;
 if(pane.pending[tab]||pane.filesystemPaths[tab].empty()){
  args.Cancel(true);return;
 }
 const auto view=side==0?LeftFiles():RightFiles();
 auto const& entries=pane.tabs[tab].snapshot().children;
 std::vector<ListViewItem> chosen;
 bool rowSelected=false;
 for(auto const& item:view.SelectedItems()){
  const auto current=item.try_as<ListViewItem>();
  if(current){
   chosen.push_back(current);
   if(current==row)rowSelected=true;
  }
 }
 if(!rowSelected)chosen={row};
 if(chosen.empty()||chosen.size()>32){args.Cancel(true);return;}
 std::vector<std::wstring> paths;
 for(auto const& entry:chosen){
  if(!entry.Tag()){args.Cancel(true);return;}
  const auto index=unbox_value<uint32_t>(entry.Tag());
  if(index>=entries.size()||!entries[index].isFileSystem()||
     entries[index].parsingName.empty()){
   args.Cancel(true);return;
  }
  paths.push_back(entries[index].parsingName);
 }
 GUID id{};
 if(FAILED(::CoCreateGuid(&id))){args.Cancel(true);return;}
 wchar_t unique[48]{};
 if(!::StringFromGUID2(id,unique,48)){args.Cancel(true);return;}
 mPrivateDragToken=unique;
 mPrivateDragParent=pane.filesystemPaths[tab];
 mPrivateDragRoute=pane.routeIds[tab];
 mPrivateDragSide=side;
 mPrivateDragSources=std::move(paths);
 args.Data().SetData(hstring(PrivateFormat),
                     box_value(hstring(mPrivateDragToken)));
 args.Data().RequestedOperation(DataPackageOperation::Copy);
 StatusText().Text(traceOwnedDrag()?L"끌기 진단: 항목 시작 이벤트 도착":
                        L"선택한 내부 파일 끌기 데이터를 준비했습니다.");
}
void MainWindow::OnFileDragOver(
 IInspectable const& sender,DragEventArgs const& args){
 auto list=sender.try_as<ListView>();
 const int side=list==LeftFiles()?0:list==RightFiles()?1:-1;
 if(side<0||mFileOperations.busy()||mDropReading){
  args.AcceptedOperation(DataPackageOperation::None);return;
 }
 auto const& pane=ActiveWindowTab().model.panes[side];
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty()){
  args.AcceptedOperation(DataPackageOperation::None);return;
 }
 auto data=args.DataView();
 if(data.Contains(hstring(PrivateFormat))||
    data.Contains(StandardDataFormats::StorageItems()))
  {
    args.AcceptedOperation(DataPackageOperation::Copy);
    if(traceOwnedDrag())
      StatusText().Text(L"끌기 진단: 대상 진입 이벤트 도착");
  }
 else args.AcceptedOperation(DataPackageOperation::None);
}
fire_and_forget MainWindow::OnFileDrop(
 IInspectable const& sender,DragEventArgs const& args){
 auto keep=get_strong(); // only while the user's drop is being interpreted
 auto list=sender.try_as<ListView>();
 const int side=list==LeftFiles()?0:list==RightFiles()?1:-1;
 if(side<0||mFileOperations.busy()||mDropReading)co_return;
 auto const& target=ActiveWindowTab().model.panes[side];
 if(target.pending[target.active]||target.filesystemPaths[target.active].empty())
  co_return;
 const auto tab=target.active,route=target.routeIds[tab];
 const auto destination=target.filesystemPaths[tab];
 mDropReading=true;
 StatusText().Text(traceOwnedDrag()?L"끌기 진단: 놓기 이벤트 도착":
                        L"파일 놓기 요청을 확인하고 있습니다...");
 auto deferral=args.GetDeferral();
 try{
  fxfile::shelltransfer::Request request{};
  request.kind=fxfile::shelltransfer::Kind::Copy; // Never infer Move
  request.destination=destination;
  const auto view=args.DataView();
  if(view.Contains(hstring(PrivateFormat))){
   auto value=co_await view.GetDataAsync(hstring(PrivateFormat));
   auto token=value.try_as<Windows::Foundation::IPropertyValue>();
   if(!token||token.GetString()!=mPrivateDragToken||
      mPrivateDragSide<0||mPrivateDragSide==side||
      mPrivateDragSources.empty()){
    StatusText().Text(L"다른 창에서 시작하지 않은 내부 파일 끌기를 거부했습니다.");
    mDropReading=false;deferral.Complete();co_return;
   }
   auto const& source=ActiveWindowTab().model.panes[mPrivateDragSide];
   if(source.pending[source.active]||
      source.routeIds[source.active]!=mPrivateDragRoute||
      source.filesystemPaths[source.active]!=mPrivateDragParent){
    StatusText().Text(L"끌기를 시작한 원본 폴더가 변경됐습니다.");
    mDropReading=false;deferral.Complete();co_return;
   }
   request.sourceParent=mPrivateDragParent;
   request.sources=mPrivateDragSources;
   mPrivateDragToken.clear();
   mPrivateDragSources.clear(); // replay protection after consumption
  }else if(view.Contains(StandardDataFormats::StorageItems())){
   auto items=co_await view.GetStorageItemsAsync();
   if(items.Size()==0||items.Size()>32){
    StatusText().Text(L"한 번에 끌 수 있는 항목은 최대 32개입니다.");
    mDropReading=false;deferral.Complete();co_return;
   }
   for(auto const& item:items){
    auto path=std::wstring(item.Path().c_str());
    if(path.empty()||path.size()>32000){
     StatusText().Text(L"끌어온 항목의 실제 경로를 확인하지 못했습니다.");
     mDropReading=false;deferral.Complete();co_return;
    }
    auto parent=std::filesystem::path(path).parent_path().native();
    if(request.sources.empty())request.sourceParent=parent;
    else if(::CompareStringOrdinal(request.sourceParent.c_str(),-1,
                      parent.c_str(),-1,TRUE)!=CSTR_EQUAL){
     StatusText().Text(L"서로 다른 원본 폴더의 항목을 함께 놓을 수 없습니다.");
     mDropReading=false;deferral.Complete();co_return;
    }
    request.sources.push_back(std::move(path));
   }
  }else{
   mDropReading=false;deferral.Complete();co_return;
  }
  const auto& live=ActiveWindowTab().model.panes[side];
  if(mFileOperations.busy()||live.active!=tab||
     live.pending[tab]||live.routeIds[tab]!=route||
     live.filesystemPaths[tab]!=destination){
   StatusText().Text(L"파일을 놓는 동안 대상 폴더가 변경됐습니다.");
  }else{
   ActivatePane(side);
   StartTransfer(std::move(request)); // common C++ STA revalidates all paths
  }
 }catch(...){
  StatusText().Text(L"파일 놓기 데이터를 읽지 못했습니다. 다시 시도해 주세요.");
 }
 mDropReading=false;
 deferral.Complete();
}
}
