#include "pch.h"
#include "MainWindow.xaml.h"
#include "../../src/base/shell_context_core.h"
#include "../../src/base/shell_explorer_delegate.h"
#include "../../src/base/shell_isolation_wire.h"
#include <winrt/Microsoft.UI.Xaml.Input.h>
#include <winrt/Microsoft.UI.Xaml.Media.h>
#include <winrt/Windows.System.h>
#include <thread>
#include <chrono>
#include <utility>
#include <algorithm>
#include <functional>
#include <memory>
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
void MainWindow::OpenSelectedWith(int side){
 if(mClosing||side<0||side>1||
    ActiveWindowTab().model.activePane!=side||
    mFileOperations.busy())return;
 const auto& state=ActiveWindowTab();
 const auto& pane=state.model.panes[side];
 if(pane.active>=pane.tabs.size()||
    pane.active>=pane.pending.size()||pane.pending[pane.active]||
    pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size()||
    pane.filesystemPaths[pane.active].empty())return;
 const auto& visible=state.fileLists[side];
 if(visible.visibleTab!=pane.active||
    visible.visibleRoute!=pane.routeIds[pane.active])return;
 auto view=side==0?LeftFiles():RightFiles();
 if(view.SelectedItems().Size()!=1){
  StatusText().Text(L"연결 프로그램은 파일 하나를 선택해야 합니다.");
  return;
 }
 auto row=view.SelectedItem().try_as<ListViewItem>();
 if(!row||!row.Tag())return;
 std::uint64_t logical=0;
 try{logical=winrt::unbox_value<std::uint64_t>(row.Tag());}
 catch(...){return;}
 auto const* selected=pane.tabs[pane.active].indexedItem(
     static_cast<std::size_t>(logical));
 if(!selected||!selected->isFileSystem()||selected->isFolder()||
    selected->parsingName.empty()){
  StatusText().Text(L"실제 파일 하나만 연결 프로그램으로 열 수 있습니다.");
  return;
 }
 const auto context=FileOperationContext(side);
 auto weak=get_weak();
 using Open=fxfile::previewops::FileOpenController;
 const auto openedPath=selected->parsingName;
 const auto start=mFileOpen.request(openedPath,DispatcherQueue(),
     [weak,context]{
      auto ui=weak.get();
      if(!ui||ui->mClosing||
         ui->ActiveWindowTab().identity!=context.windowTabIdentity||
         ui->ActiveWindowTab().model.activePane!=context.side)return false;
      const auto live=ui->FileOperationContext(context.side);
      return live.windowTabIdentity==context.windowTabIdentity&&
             live.tab==context.tab&&live.route==context.route&&
             live.visibleFolder==context.visibleFolder&&
             live.visibleShellFolder==context.visibleShellFolder;
     },
     [weak,openedPath](Open::Result result){
      if(auto ui=weak.get()){
       using Result=Open::Result;
       if(result==Result::Opened){
        ui->mRecentActivity.recordFile(openedPath);
        if(ui->RecentActivityPanel().Visibility()==Visibility::Visible)
         ui->RefreshRecentActivityPanel();
       }
       ui->StatusText().Text(
        result==Result::Opened?
         L"선택한 연결 프로그램으로 파일을 열었습니다.":
        result==Result::TimedOut?
         L"연결 프로그램 선택 대기 시간이 초과됐습니다.":
         L"연결 프로그램 선택이 취소됐거나 파일을 열지 못했습니다.");
      }
     },Open::Mode::ChooseApp);
 if(start==Open::Start::Started)
  StatusText().Text(L"Windows 연결 프로그램 선택 창을 여는 중입니다.");
 else if(start==Open::Start::Busy)
  StatusText().Text(L"이전 파일 열기 요청을 처리 중입니다.");
 else
  StatusText().Text(L"이 파일은 연결 프로그램으로 열 수 없습니다.");
}
void MainWindow::ShowAppFileContextMenu(
 int side,ListViewItem const& anchor,Windows::Foundation::Point const& position){
 if(mClosing||side<0||side>1||!anchor||
    ActiveWindowTab().model.activePane!=side)return;
 const auto& workspace=ActiveWindowTab();
 const auto& pane=workspace.model.panes[side];
 if(pane.active>=pane.tabs.size()||pane.active>=pane.pending.size()||
    pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size()||
    pane.pending[pane.active])return;
 const auto tab=pane.active;
 const auto route=pane.routeIds[tab];
 const auto& visible=workspace.fileLists[side];
 if(visible.visibleRoute!=route||visible.visibleTab!=tab)return;
 auto list=side==0?LeftFiles():RightFiles();
 const auto count=list.SelectedItems().Size();
 if(!count||count>fxfile::shelltransfer::kMaxItems){
  StatusText().Text(L"앱 파일 메뉴는 최대 1,024개 항목을 선택할 수 있습니다.");
  return;
 }
 // Bind every action to the exact WindowTab, PaneTab, route and selected
 // logical identities. A delayed click must never mutate a new selection.
 std::vector<std::uint64_t> logicalIds;
 logicalIds.reserve(count);
 // A route can stay unchanged when a refreshed list reuses a logical row
 // index for a different file. Remember both the index and item identity.
 std::vector<std::pair<std::uint64_t,std::wstring>> selectedPaths;
 selectedPaths.reserve(count);
 bool allFilesystem=true;
 bool boundedSources=true;
 std::size_t sourceUnits=0;
 bool canOpen=false;
 bool isFolder=false;
 std::wstring folderPath;
 for(auto const& selected:list.SelectedItems()){
  auto row=selected.try_as<ListViewItem>();
  if(!row||!row.Tag())return;
  std::uint64_t logical{};
  try{logical=unbox_value<std::uint64_t>(row.Tag());}
  catch(...){return;}
  auto const* indexed=pane.tabs[tab].indexedItem(
   static_cast<std::size_t>(logical));
  if(!indexed||indexed->parsingName.empty())return;
  logicalIds.push_back(logical);
  selectedPaths.emplace_back(logical,indexed->parsingName);
  const auto units=indexed->parsingName.size()+1;
  if(units>fxfile::shelltransfer::kMaxSourcePathUnits-sourceUnits)
   boundedSources=false;
  else sourceUnits+=units;
  allFilesystem=allFilesystem&&indexed->isFileSystem();
  if(count==1){
   canOpen=indexed->isFolder()||indexed->isFileSystem();
   isFolder=indexed->isFolder();
   if(isFolder&&indexed->isFileSystem())
    folderPath=indexed->parsingName;
  }
 }
 std::sort(logicalIds.begin(),logicalIds.end());
 if(std::adjacent_find(logicalIds.begin(),logicalIds.end())!=logicalIds.end())
  return;
 auto expected=std::make_shared<const std::vector<std::uint64_t>>(
  std::move(logicalIds));
 std::sort(selectedPaths.begin(),selectedPaths.end());
 auto expectedPaths=std::make_shared<
     const std::vector<std::pair<std::uint64_t,std::wstring>>>(
      std::move(selectedPaths));
 const auto identity=workspace.identity;
 // Collision confirmation is an unfinished file operation even though
 // its worker is idle. Never enable a new file command behind that modal.
 const bool ready=!mFileOperations.busy()&&
                  !mFileOperations.pendingConfirmationToken();
 const bool localSource=!pane.filesystemPaths[tab].empty();
 const bool localSelection=ready&&boundedSources&&
  localSource&&allFilesystem;
 const auto& sourceSnapshot=pane.tabs[tab].snapshot();
 // Route IDs identify a PaneTab, not its current folder. Bind both.
 const auto sourceShellFolder=sourceSnapshot.parsingName;
 const auto sourceFilesystemFolder=pane.filesystemPaths[tab];
 const bool canProviderSource=ready&&boundedSources&&!localSource&&
  sourceSnapshot.folder.valid()&&!sourceSnapshot.parsingName.empty()&&
  sourceSnapshot.parsingName.size()<=
   fxfile::shelltransfer::kMaxProviderParsingUnits;
 const bool canRename=localSelection&&count==1;
 // Derive availability from the destination's current tab and route,
 // rather than offering an operation we already know cannot start.
 bool destinationFilesystem=false;
 bool destinationProvider=false;
 if(ready&&workspace.model.split){
  auto const& other=workspace.model.panes[1-side];
  if(other.active<other.tabs.size()&&
     other.active<other.pending.size()&&
     other.active<other.routeIds.size()&&
     other.active<other.filesystemPaths.size()&&
     !other.pending[other.active]){
   destinationFilesystem=!other.filesystemPaths[other.active].empty();
   if(!destinationFilesystem){
    auto const& target=other.tabs[other.active].snapshot();
    destinationProvider=target.folder.valid()&&
        !target.parsingName.empty()&&
        target.parsingName.size()<=
            fxfile::shelltransfer::kMaxProviderParsingUnits;
   }
  }
 }
 const bool canOppositeCopy=(localSelection||canProviderSource)&&
     (destinationFilesystem||(localSelection&&destinationProvider));
 const bool canOppositeMove=localSelection&&destinationFilesystem;
 const bool canExternal=localSelection&&
  count<=fxfile::shellcontext::kMaxContextSelection;
 // Keep menu availability within the smaller Explorer handoff wire budget.
 // The native worker still revalidates individual paths and their parent.
 const bool canWindowsExplorer=ready&&boundedSources&&
     sourceUnits<=fxfile::shellexplorer::kMaxPathUnits&&
     allFilesystem&&count<=fxfile::shellexplorer::kMaxSelected;
 auto weak=get_weak();
 MenuFlyout menu;
 auto make=[&](wchar_t const* title,wchar_t const* iconGlyph,
               bool enabled,std::function<void(MainWindow&)> action){
  MenuFlyoutItem item;
  item.Text(title);
  item.IsEnabled(enabled);
  if(iconGlyph&&*iconGlyph){
   FontIcon icon;
   icon.Glyph(iconGlyph);
   item.Icon(icon);
  }
  item.Click([weak,side,identity,tab,route,expected,expectedPaths,
              sourceShellFolder,sourceFilesystemFolder,
              action=std::move(action)](IInspectable const&,
                                       RoutedEventArgs const&){
   auto ui=weak.get();
   if(!ui||ui->mClosing)return;
   const auto& state=ui->ActiveWindowTab();
   const auto& pane=state.model.panes[side];
   if(state.identity!=identity||state.model.activePane!=side||
      pane.active!=tab||tab>=pane.tabs.size()||
      tab>=pane.pending.size()||pane.pending[tab]||
      tab>=pane.routeIds.size()||pane.routeIds[tab]!=route||
      tab>=pane.filesystemPaths.size()||
      pane.tabs[tab].snapshot().parsingName!=sourceShellFolder||
      pane.filesystemPaths[tab]!=sourceFilesystemFolder||
      ui->mFileOperations.busy()||
      ui->mFileOperations.pendingConfirmationToken()){
    ui->StatusText().Text(
     L"파일 메뉴를 연 뒤 창이나 작업 상태가 변경됐습니다. 다시 선택하세요.");
    return;
   }
   const auto& viewState=state.fileLists[side];
   if(viewState.visibleRoute!=route||viewState.visibleTab!=tab){
    ui->StatusText().Text(
     L"파일 목록이 갱신됐습니다. 우클릭 메뉴를 다시 여세요.");
    return;
   }
   auto selectedView=side==0?ui->LeftFiles():ui->RightFiles();
   if(selectedView.SelectedItems().Size()!=expected->size()){
    ui->StatusText().Text(
     L"파일 선택이 변경됐습니다. 우클릭 메뉴를 다시 여세요.");
    return;
   }
   std::vector<std::uint64_t> actual;
   actual.reserve(expected->size());
   for(auto const& selected:selectedView.SelectedItems()){
    auto row=selected.try_as<ListViewItem>();
    if(!row||!row.Tag())return;
    try{actual.push_back(unbox_value<std::uint64_t>(row.Tag()));}
    catch(...){return;}
   }
   std::sort(actual.begin(),actual.end());
   if(actual!=*expected){
    ui->StatusText().Text(
     L"파일 선택이 변경됐습니다. 우클릭 메뉴를 다시 여세요.");
    return;
   }
   // Rebind logical IDs to their current parsing names before any file
   // command, Clipboard write or external Shell handoff. This uses only the
   // already visible model; no filesystem or provider query on the UI thread.
   for(auto const& [logical,path]:*expectedPaths){
    auto const* indexed=pane.tabs[tab].indexedItem(
     static_cast<std::size_t>(logical));
    if(!indexed||indexed->parsingName!=path){
     ui->StatusText().Text(
      L"선택한 파일 항목이 갱신됐습니다. 우클릭 메뉴를 다시 여세요.");
     return;
    }
   }
   action(*ui);
  });
  return item;
 };
 // Windows 11-like hierarchy: primary open action, frequently used
 // icon commands, a separate destination submenu, and more options last.
 menu.Items().Append(make(L"열기",L"\uE8E5",
                          ready&&count==1&&canOpen,
     [side](MainWindow& ui){ui.OpenSelectedFolder(side);}));
 menu.Items().Append(make(L"연결 프로그램으로 열기",L"\uE8F2",
                          localSelection&&count==1&&!isFolder,
     [side](MainWindow& ui){ui.OpenSelectedWith(side);}));
 // Windows owns compression, extraction and other Explorer commands.
 // Retired F08 native archive code is not part of this product.
 // Explorer owns user-initiated archive commands in its separate window.
 menu.Items().Append(make(L"Windows 탐색기에서 선택 열기",L"\uE8B7",
                          canWindowsExplorer,
     [side](MainWindow& ui){ui.RevealSelectedInWindowsExplorer(side);}));
 if(count==1&&isFolder&&!folderPath.empty()){
  menu.Items().Append(make(L"새 폴더 탭에서 열기",L"\uE8B7",ready,
     [side,path=std::move(folderPath)](MainWindow& ui){
      ui.OpenFolderInNewPaneTab(side,path);
     }));
 }
 menu.Items().Append(MenuFlyoutSeparator{});
 menu.Items().Append(make(L"잘라내기",L"\uE8C6",localSelection,
     [side](MainWindow& ui){ui.CopySelectedToWindowsClipboard(side,true);}));
 menu.Items().Append(make(L"복사",L"\uE8C8",localSelection,
     [side](MainWindow& ui){ui.CopySelectedToWindowsClipboard(side,false);}));
 menu.Items().Append(make(L"경로 복사",L"\uE8C8",localSelection,
     [side](MainWindow& ui){ui.CopySelectedToWindowsClipboard(side,false,true);}));
 menu.Items().Append(make(L"이름 바꾸기",L"\uE8AC",canRename,
     [](MainWindow& ui){
      ui.BeginFileNameCommand(fxfile::filecommand::Kind::RenameSelected);
     }));
 menu.Items().Append(make(L"삭제",L"\uE74D",localSelection,
     [](MainWindow& ui){ui.RunTransfer(fxfile::shelltransfer::Kind::Recycle);}));
 menu.Items().Append(MenuFlyoutSeparator{});
 MenuFlyoutSubItem sendTo;
 sendTo.Text(L"반대쪽 패널로 보내기");
 sendTo.IsEnabled(canOppositeCopy||canOppositeMove);
 sendTo.Items().Append(make(L"복사",L"\uE8C8",canOppositeCopy,
     [](MainWindow& ui){ui.RunTransfer(fxfile::shelltransfer::Kind::Copy);}));
 sendTo.Items().Append(make(L"이동",L"\uE8C6",canOppositeMove,
     [](MainWindow& ui){ui.RunTransfer(fxfile::shelltransfer::Kind::Move);}));
 menu.Items().Append(sendTo);
 menu.Items().Append(MenuFlyoutSeparator{});
 menu.Items().Append(make(L"속성",L"\uE946",canExternal,
     [side](MainWindow& ui){ui.ShowExternalWindowsContextMenu(side,true);}));
 menu.Items().Append(make(L"추가 옵션 표시",L"\uE712",canExternal,
     [side](MainWindow& ui){ui.ShowExternalWindowsContextMenu(side);}));
 Microsoft::UI::Xaml::Controls::Primitives::FlyoutShowOptions options;
 options.Position(position);
 menu.ShowAt(anchor,options);
}
void MainWindow::ShowAppBackgroundContextMenu(
 int side,FrameworkElement const& anchor,
 Windows::Foundation::Point const& position){
 if(mClosing||side<0||side>1||!anchor||
    ActiveWindowTab().model.activePane!=side)return;
 const auto& state=ActiveWindowTab();
 const auto& pane=state.model.panes[side];
 if(pane.active>=pane.tabs.size()||pane.active>=pane.routeIds.size()||
    pane.active>=pane.pending.size()||
    pane.active>=pane.filesystemPaths.size()||
    pane.pending[pane.active])return;
 const auto identity=state.identity;
 const auto tab=pane.active;
 const auto route=pane.routeIds[tab];
 // A navigation inside one PaneTab preserves its route; remember the
 // actual folder before building a deferred background menu.
 const auto sourceShellFolder=pane.tabs[tab].snapshot().parsingName;
 const auto sourceFilesystemFolder=pane.filesystemPaths[tab];
 const bool ready=!mFileOperations.busy()&&
                  !mFileOperations.pendingConfirmationToken();
 const bool localFolder=ready&&!pane.filesystemPaths[tab].empty();
 const int viewMode=static_cast<int>(state.fileLists[side].viewMode);
 const int sortMode=state.fileLists[side].sortMode;
 const bool grouping=state.fileLists[side].groupByType;
 const int groupMode=static_cast<int>(state.fileLists[side].groupMode);
 auto weak=get_weak();
 auto focusNameEditAfterClose=std::make_shared<bool>(false);
 // Share the same route/WindowTab guard for ordinary commands and checked
 // view/sort items. A delayed menu click cannot change a different pane.
 auto guarded=[weak,side,identity,tab,route,
               sourceShellFolder,sourceFilesystemFolder](
     std::function<void(MainWindow&)> action){
  return [weak,side,identity,tab,route,
          sourceShellFolder,sourceFilesystemFolder,
          action=std::move(action)](IInspectable const&,
                                   RoutedEventArgs const&){
   auto ui=weak.get();
   if(!ui||ui->mClosing||ui->mFileOperations.busy()||
      ui->mFileOperations.pendingConfirmationToken())return;
   const auto& state=ui->ActiveWindowTab();
   if(state.identity!=identity||state.model.activePane!=side)return;
   const auto& pane=state.model.panes[side];
   if(pane.active!=tab||tab>=pane.tabs.size()||
      tab>=pane.routeIds.size()||tab>=pane.pending.size()||
      tab>=pane.filesystemPaths.size()||
      pane.pending[tab]||pane.routeIds[tab]!=route||
      pane.tabs[tab].snapshot().parsingName!=sourceShellFolder||
      pane.filesystemPaths[tab]!=sourceFilesystemFolder){
    ui->StatusText().Text(L"폴더가 변경됐습니다. 메뉴를 다시 여세요.");
    return;
   }
   action(*ui);
  };
 };
 auto make=[&](wchar_t const* text,wchar_t const* glyph,bool enabled,
               std::function<void(MainWindow&)> action){
  MenuFlyoutItem item;
  item.Text(text);
  item.IsEnabled(enabled);
  if(glyph&&*glyph){
   FontIcon icon;
   icon.Glyph(glyph);
   item.Icon(icon);
  }
  item.Click(guarded(std::move(action)));
  return item;
 };
 auto choice=[&](wchar_t const* label,bool checked,int index,bool isView){
  ToggleMenuFlyoutItem item;
  item.Text(label);
  item.IsEnabled(ready);
  item.IsChecked(checked);
  item.Click(guarded([index,isView](MainWindow& ui){
   if(isView)ui.UpdateView(index);
   else ui.UpdateSort(index);
  }));
  return item;
 };
 auto groupChoice=[&](wchar_t const* label,int choiceIndex){
  ToggleMenuFlyoutItem item;
  item.Text(label);
  item.IsEnabled(ready);
  item.IsChecked(grouping&&groupMode==choiceIndex-1);
  item.Click(guarded([choiceIndex](MainWindow& ui){
   ui.ToggleGroupMode(choiceIndex);
  }));
  return item;
 };
 MenuFlyout menu;
 MenuFlyoutSubItem view;
 view.Text(L"보기");
 view.Items().Append(choice(L"자세히",viewMode==0,0,true));
 view.Items().Append(choice(L"목록",viewMode==1,1,true));
 view.Items().Append(choice(L"작은 아이콘",viewMode==2,2,true));
 view.Items().Append(choice(L"중간 아이콘",viewMode==3,3,true));
 view.Items().Append(choice(L"큰 아이콘",viewMode==4,4,true));
 view.Items().Append(choice(L"아주 큰 아이콘",viewMode==5,5,true));
 menu.Items().Append(view);
 MenuFlyoutSubItem sort;
 sort.Text(L"정렬 기준");
 sort.Items().Append(choice(L"이름 오름차순",sortMode==0,0,false));
 sort.Items().Append(choice(L"이름 내림차순",sortMode==1,1,false));
 sort.Items().Append(choice(L"유형 오름차순",sortMode==4,4,false));
 sort.Items().Append(choice(L"유형 내림차순",sortMode==5,5,false));
 sort.Items().Append(choice(L"크기 오름차순",sortMode==6,6,false));
 sort.Items().Append(choice(L"크기 내림차순",sortMode==2,2,false));
 sort.Items().Append(choice(L"수정 날짜 오름차순",sortMode==7,7,false));
 sort.Items().Append(choice(L"수정 날짜 내림차순",sortMode==3,3,false));
 menu.Items().Append(sort);
 MenuFlyoutSubItem group;
 group.Text(L"분류 방법");
 group.Items().Append(groupChoice(L"유형",1));
 group.Items().Append(groupChoice(L"이름",2));
 group.Items().Append(groupChoice(L"크기",3));
 group.Items().Append(groupChoice(L"수정 월",4));
 menu.Items().Append(group);
 menu.Items().Append(make(L"새로 고침",L"\uE72C",ready,
     [side](MainWindow& ui){
      const auto& pane=ui.ActiveWindowTab().model.panes[side];
      const auto& snap=pane.tabs[pane.active].snapshot();
      if(snap.folder.valid()){
       ui.QueuePidl(side,fxfile::shellnav::Location(snap.folder),
                    fxfile::shellnav::NavigationAction::Refresh);
      }else ui.StatusText().Text(L"현재 위치를 새로 고칠 수 없습니다.");
     }));
 // Delegate Windows-native New/archive/background actions to Explorer.
 menu.Items().Append(make(L"Windows 탐색기에서 현재 폴더 열기",L"\uE8B7",
                          localFolder,
     [side](MainWindow& ui){ui.OpenCurrentFolderInWindowsExplorer(side);}));
 menu.Items().Append(MenuFlyoutSeparator{});
 // Root drives keep the existing helper's minimum path boundary. Ordinary
 // local folders use the same isolated Properties verb as selected items.
 menu.Items().Append(make(L"속성",L"\uE946",
                          localFolder&&sourceFilesystemFolder.size()>3,
     [side](MainWindow& ui){ui.ShowCurrentFolderProperties(side);}));
 menu.Items().Append(make(L"붙여넣기",L"\uE77F",localFolder,
     [](MainWindow& ui){ui.PasteFromWindowsClipboard();}));
 MenuFlyoutSubItem create;
 create.Text(L"새로 만들기");
 create.IsEnabled(localFolder);
 create.Items().Append(make(L"폴더",L"\uE8B7",localFolder,
     [focusNameEditAfterClose](MainWindow& ui){
       *focusNameEditAfterClose=true;
       ui.BeginFileNameCommand(fxfile::filecommand::Kind::CreateFolder);
      }));
 create.Items().Append(make(L"텍스트 문서 (.txt)",L"\uE8A5",localFolder,
     [focusNameEditAfterClose](MainWindow& ui){
       *focusNameEditAfterClose=true;
       ui.BeginFileNameCommand(fxfile::filecommand::Kind::CreateTextFile);
      }));
 create.Items().Append(make(L"Markdown 문서 (.md)",L"\uE8A5",localFolder,
     [focusNameEditAfterClose](MainWindow& ui){
       *focusNameEditAfterClose=true;
       ui.BeginFileNameCommand(fxfile::filecommand::Kind::CreateMarkdownFile);
      }));
 menu.Items().Append(create);
 menu.Closed([weak,focusNameEditAfterClose](
     IInspectable const&,IInspectable const&){
  if(!std::exchange(*focusNameEditAfterClose,false))return;
  auto ui=weak.get();
  if(!ui)return;
  auto box=ui->FileNameBox();
  if(box.Opacity()<0.5||!box.IsTabStop()||!ui->ToolbarView().IsLoaded())return;
  ui->ToolbarView().UpdateLayout();
  box.Focus(FocusState::Programmatic);
 });
 Microsoft::UI::Xaml::Controls::Primitives::FlyoutShowOptions options;
 options.Position(position);
 menu.ShowAt(anchor,options);
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
 if(!clicked){
  list.SelectedItems().Clear();
  args.Handled(true);
  QueueSelectionPresentationUpdate();
  ShowAppBackgroundContextMenu(side,list,args.GetPosition(list));
  return;
 }
 // Right-clicking a member keeps the complete selection. Only an unselected
 // row replaces it; the isolated menu retains its bounded multi-item policy.
 if(!clicked.IsSelected()){
  list.SelectedItems().Clear();
  clicked.IsSelected(true);
 }
 args.Handled(true);
 QueueSelectionPresentationUpdate();
 ShowAppFileContextMenu(side,clicked,args.GetPosition(clicked));
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
 if(mFileOperations.pendingConfirmationToken()){
  StatusText().Text(L"기존 파일 충돌 확인을 먼저 완료하거나 취소하세요.");
  return;
 }
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
 context.windowTabIdentity=ActiveWindowTab().identity;
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
  // Do not erase a previous failure when a request is rejected or its
  // confirmation is still pending. Clear only for an actual launch.
  ActiveWindowTab().fileOperationNotice.clear();
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
  ConfirmRecycle(recycleCount,mFileOperations.pendingConfirmationToken());
  return;
 }
 if(status==Start::Busy)
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
 else if(status==Start::InvalidVisibleContext)
  StatusText().Text(L"현재 창이 원본이나 대상 폴더와 일치하지 않습니다.");
 else if(status==Start::StaleConfirmation)
  StatusText().Text(L"확인하는 동안 원본 또는 대상 폴더가 변경됐습니다. 다시 선택하세요.");
 else if(status==Start::Cancelled)
  StatusText().Text(L"파일 작업 확인을 취소했습니다. 확인 전 작업은 실행하지 않았습니다.");
 else if(status==Start::AllSkipped)
  StatusText().Text(L"충돌한 항목을 모두 건너뛰었습니다. 이 요청에서 파일을 변경하지 않았습니다.");
 else if(status==Start::ThreadStartFailed){
  SetFileButtonsBusy(false,false);
  StatusText().Text(L"별도 Shell 파일 작업 스레드를 시작하지 못했습니다.");
 }
 // Cancellation/AllSkipped can settle a confirmation without a worker
 // completion callback. Recompute readiness after its token was cleared.
 UpdateCommandAvailability();
}
void MainWindow::StartTransfer(fxfile::shelltransfer::Request request){
 // A pending confirmation must not be displaced by another transfer on the
 // same visible route while its ContentDialog is awaiting a user decision.
 if(mClosing)return;
 if(mFileOperations.pendingConfirmationToken()){
  StatusText().Text(L"현재 파일 작업 확인창을 완료하거나 취소한 후 다시 시도하세요.");
  return;
 }
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
winrt::fire_and_forget MainWindow::ConfirmRecycle(
 std::size_t count,std::uint64_t token){
 const auto keep=get_strong();
 if(mClosing||!token||mFileOperations.pendingConfirmationToken()!=token)
  co_return;
 // ContentDialog may reject ShowAsync when a different modal is already
 // visible. In that case fail closed as if the user chose Cancel.
 ContentDialogResult decision=ContentDialogResult::None;
 try{
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
  decision=co_await dialog.ShowAsync();
 }catch(...){
  // No dialog response can authorize a Recycle operation.
 }
 if(mClosing||mFileOperations.pendingConfirmationToken()!=token)co_return;
 auto weak=get_weak();
 const auto status=mFileOperations.confirmRecycle(
  decision==ContentDialogResult::Primary,token,
  FileOperationContext(ActiveWindowTab().model.activePane),
  operationPost(DispatcherQueue()),
  [weak](FileOperationController::TransferCompletion completion){
   if(auto ui=weak.get())ui->OnTransferCompleted(std::move(completion));
  });
 ApplyTransferStartStatus(status,count);
}
winrt::fire_and_forget MainWindow::ConfirmCollision(
 std::size_t requested,std::size_t collided,bool allowSkip,
 std::size_t previouslySkipped,std::uint64_t token){
 const auto keep=get_strong();
 if(mClosing||!token||mFileOperations.pendingConfirmationToken()!=token)
  co_return;
 ContentDialogResult choice=ContentDialogResult::None;
 try{
  ContentDialog dialog;
  dialog.XamlRoot(RootShell().XamlRoot());
  dialog.Title(winrt::box_value(hstring(L"동일한 이름이 이미 존재합니다")));
  std::wstring message=L"현재 남은 "+std::to_wstring(requested)+
     L"개 항목 중 "+std::to_wstring(collided)+
     L"개 이름이 대상 폴더와 충돌합니다. 기존 파일은 덮어쓰지 않습니다. "
     L"이름을 바꿔 둘 다 유지하거나 작업을 취소할 수 있습니다.";
  if(previouslySkipped)
   message+=L" 이전 확인에서 충돌 "+std::to_wstring(previouslySkipped)+
            L"개는 이미 건너뛰었습니다.";
  if(allowSkip)
   message+=L" 충돌한 항목만 건너뛰고 나머지를 처리할 수도 있습니다. "
            L"작업 전 확인 결과이므로 아직 파일을 변경하지 않았습니다.";
  dialog.Content(winrt::box_value(hstring(message)));
  dialog.PrimaryButtonText(L"이름 바꿔 둘 다 유지");
  if(allowSkip)dialog.SecondaryButtonText(L"충돌 항목 건너뛰기");
  dialog.CloseButtonText(L"취소");
  dialog.DefaultButton(ContentDialogButton::Close);
  choice=co_await dialog.ShowAsync();
 }catch(...){
  // No Shell mutation or skip decision is permitted without an answer.
 }
 if(mClosing||mFileOperations.pendingConfirmationToken()!=token)co_return;
 auto weak=get_weak();
 const auto context=FileOperationContext(ActiveWindowTab().model.activePane);
 const auto post=operationPost(DispatcherQueue());
 auto completed=[weak](FileOperationController::TransferCompletion completion){
  if(auto ui=weak.get())ui->OnTransferCompleted(std::move(completion));
 };
 if(allowSkip&&choice==ContentDialogResult::Secondary){
  std::size_t skipped=0;
  const auto status=mFileOperations.skipCollisions(
      token,context,post,std::move(completed),skipped);
  ApplyTransferStartStatus(status);
  if(status==FileOperationController::StartStatus::Started)
   StatusText().Text(hstring(L"충돌 항목 "+std::to_wstring(skipped)+
       L"개를 건너뛰었습니다. 나머지를 처리 중입니다."));
  else if(status==FileOperationController::StartStatus::AllSkipped)
   StatusText().Text(hstring(L"충돌한 "+std::to_wstring(skipped)+
       L"개 항목을 모두 건너뛰었습니다. 파일을 변경하지 않았습니다."));
  co_return;
 }
 const auto status=mFileOperations.confirmCollision(
  choice==ContentDialogResult::Primary,token,context,post,
  std::move(completed));
 ApplyTransferStartStatus(status);
}
void MainWindow::OnTransferCompleted(
 FileOperationController::TransferCompletion completion){
 using Disposition=FileOperationController::TransferDisposition;
 const auto disposition=mFileOperations.acceptTransfer(
  completion,FileOperationContext(completion.context.side));
 if(disposition==Disposition::Ignored)return;
 const bool originActive=completion.context.windowTabIdentity==
                         ActiveWindowTab().identity;
 auto rememberOrigin=[&](std::wstring const& message){
  // The same controller owns the request, but the notice belongs to the
  // originating workspace even if its tab is currently inactive.
  for(std::size_t i=0;i<mWorkspace.count();++i){
   auto& state=mWorkspace.state(i);
   if(state.identity==completion.context.windowTabIdentity){
    state.fileOperationNotice=message;
    return;
   }
  }
 };
 if(mTransferTimer)mTransferTimer.Stop();
 SetFileButtonsBusy(false,false);
 if(disposition==Disposition::NeedsCollisionConfirmation){
  const auto& request=completion.request;
  const bool allowSkip=
      request.sourceMode==fxfile::shelltransfer::SourceMode::Filesystem&&
      request.destinationMode==fxfile::shelltransfer::DestinationMode::Filesystem&&
      request.kind!=fxfile::shelltransfer::Kind::Recycle;
  ConfirmCollision(request.sources.size(),
                   completion.report.collisions.size(),allowSkip,
                   completion.skippedCollisions,
                   mFileOperations.pendingConfirmationToken());
  return;
 }
 // Failed or canceled transfers can have committed earlier items. Refresh
 // only the currently visible folders touched by this exact request, even
 // on failure; never infer that the batch was atomic or delete partial data.
 // ShellNavigationController supersedes earlier same-pane navigation.
 // A completed operation may outlive its WindowTab. Do not navigate
 // a different workspace just because it displays the same folder path.
 if(completion.context.windowTabIdentity==ActiveWindowTab().identity){
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
 if(disposition==Disposition::StaleContext){
  // The originating tab or route is no longer active. The controller
  // deliberately rejects further UI decisions, but the worker's result
  // remains available: preserve it in that workspace without navigating
  // or writing another workspace's status bar.
  const bool succeeded=completion.report.error==ERROR_SUCCESS&&
                       !completion.report.aborted;
  std::wstring notice=succeeded?
      L"파일 작업이 완료됐지만 화면이 변경됐습니다. 원본·대상 폴더를 확인하세요.":
      L"파일 작업이 실패하거나 취소됐고 화면이 변경됐습니다. "
      L"일부 항목이 처리됐을 수 있습니다. 원본·대상을 확인하세요. 오류: "+
      std::to_wstring(completion.report.error);
  if(completion.skippedCollisions)
   notice+=L" 충돌 "+std::to_wstring(completion.skippedCollisions)+
           L"개는 건너뛰었습니다.";
  rememberOrigin(notice);
  if(originActive)StatusText().Text(hstring(notice));
  return;
 }
 if(disposition==Disposition::Failed){
  std::wstring detail;
  if(completion.request.kind==fxfile::shelltransfer::Kind::Recycle&&
     removableLocalRoot(completion.request.sourceParent)){
   detail=L"이 이동식 드라이브의 Windows 휴지통으로 이동을 완료하지 못했습니다. "
          L"영구 삭제로 전환하지 않았습니다. 오류: "+
          std::to_wstring(completion.report.error);
  }else if(completion.report.aborted||
           completion.report.error==ERROR_CANCELLED){
   detail=L"파일 작업이 취소됐습니다.";
  }else detail=errorInKorean(completion.report.error).c_str();
  // queued counts accepted requests, NOT completed items. Never invent
  // a success/skip count from aggregate IFileOperation progress.
  detail=L"요청 "+std::to_wstring(completion.request.sources.size()+
                                 completion.skippedCollisions)+
         L"개: "+detail;
  if(completion.skippedCollisions)
   detail+=L" 충돌 "+std::to_wstring(completion.skippedCollisions)+
           L"개는 건너뛰었습니다.";
  detail+=L" 일부 항목이 처리됐을 수 있습니다. 원본·대상을 확인하세요.";
  rememberOrigin(detail);
  if(originActive)StatusText().Text(hstring(detail));
  return;
 }
 const auto count=std::to_wstring(completion.request.sources.size());
 std::wstring message=
  completion.request.kind==fxfile::shelltransfer::Kind::Copy?
    count+L"개 항목의 복사를 완료했습니다.":
  completion.request.kind==fxfile::shelltransfer::Kind::Move?
    count+L"개 항목의 이동을 완료했습니다.":
    count+L"개 항목의 휴지통 이동을 완료했습니다.";
 if(completion.skippedCollisions)
  message+=L" 충돌 "+std::to_wstring(completion.skippedCollisions)+
           L"개는 건너뛰고 기존 항목을 유지했습니다.";
 // Retain accepted success across a Shell Refresh, just as failures are
 // retained, and display it only in the originating workspace.
 rememberOrigin(message);
 if(originActive)StatusText().Text(hstring(message));


}
bool MainWindow::CopySelectedToWindowsClipboard(int side,bool cut,bool pathsOnly){
 if(mClosing||side<0||side>1||(pathsOnly&&cut)||mFileOperations.busy()||
    mFileOperations.pendingConfirmationToken())return false;
 auto const& window=ActiveWindowTab();
 if(window.model.activePane!=side)return false;
 auto const& pane=window.model.panes[side];
 const auto tab=pane.active;
 auto const& shown=window.fileLists[side];
 if(tab>=pane.tabs.size()||tab>=pane.pending.size()||
    tab>=pane.routeIds.size()||tab>=pane.filesystemPaths.size()||
    shown.visibleTab!=tab||shown.visibleRoute!=pane.routeIds[tab]||
    shown.renderedFolder!=pane.tabs[tab].snapshot().parsingName)return false;
 if(pane.pending[pane.active]||pane.filesystemPaths[pane.active].empty()){
  StatusText().Text(L"폴더를 완전히 불러온 후 항목을 선택하세요.");return false;
 }
 const auto view=side==0?LeftFiles():RightFiles();
 try{
  if(!view.Tag()||unbox_value<std::uint64_t>(view.Tag())!=window.identity)return false;
 }catch(...){return false;}
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
 const auto err=pathsOnly?fxfile::shellclipboard::writePathsText(hwnd,item):
                          fxfile::shellclipboard::write(hwnd,item);
 if(err!=ERROR_SUCCESS){
  StatusText().Text(L"Windows 클립보드에 선택 항목을 쓰지 못했습니다.");
  return false;
 }
 StatusText().Text(pathsOnly?L"선택한 파일 경로를 텍스트로 복사했습니다.":cut?
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
void MainWindow::OpenCurrentFolderInWindowsExplorer(int side){
 if(mClosing||side<0||side>1||mFileOperations.busy()||
    ActiveWindowTab().model.activePane!=side)return;
 const auto& workspace=ActiveWindowTab();
 const auto& pane=workspace.model.panes[side];
 if(pane.active>=pane.tabs.size()||pane.active>=pane.pending.size()||
    pane.pending[pane.active]||pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size())return;
 const auto tab=pane.active;
 const auto route=pane.routeIds[tab];
 const auto& visible=workspace.fileLists[side];
 if(visible.visibleRoute!=route||visible.visibleTab!=tab)return;
 const auto folder=pane.filesystemPaths[tab];
 if(folder.empty())return;
 const auto identity=workspace.identity;
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 StatusText().Text(L"현재 폴더를 Windows 탐색기로 열고 있습니다.");
 try{
  std::thread([weak,dispatch,folder,identity,side,tab,route]{
   const auto result=fxfile::shellexplorer::openFolder(folder);
   dispatch.TryEnqueue([weak,result,folder,identity,side,tab,route]{
    auto ui=weak.get();
    if(!ui||ui->mClosing)return;
    const auto& workspace=ui->ActiveWindowTab();
    if(workspace.identity!=identity||
       workspace.model.activePane!=side)return;
    const auto& pane=workspace.model.panes[side];
    if(pane.active!=tab||tab>=pane.routeIds.size()||
       pane.routeIds[tab]!=route||
       tab>=pane.filesystemPaths.size()||
       pane.filesystemPaths[tab]!=folder)return;
    ui->StatusText().Text(SUCCEEDED(result)?
     L"Windows 탐색기에서 현재 폴더를 열었습니다. Windows 기본 메뉴를 이용하세요.":
     L"Windows 탐색기에서 현재 폴더를 열지 못했습니다.");
   });
  }).detach();
 }catch(...){
  StatusText().Text(L"Windows 탐색기 연결 작업을 시작할 수 없습니다.");
 }
}
void MainWindow::RevealSelectedInWindowsExplorer(int side){
 if(mClosing||side<0||side>1||mFileOperations.busy()||
    ActiveWindowTab().model.activePane!=side)return;
 const auto& workspace=ActiveWindowTab();
 const auto& pane=workspace.model.panes[side];
 if(pane.active>=pane.tabs.size()||
    pane.active>=pane.pending.size()||pane.pending[pane.active]||
    pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size())return;
 const auto tab=pane.active;
 const auto route=pane.routeIds[tab];
 const auto& visible=workspace.fileLists[side];
 if(visible.visibleTab!=tab||visible.visibleRoute!=route)return;
 auto view=side==0?LeftFiles():RightFiles();
 const auto count=view.SelectedItems().Size();
 if(!count||count>fxfile::shellexplorer::kMaxSelected)return;
 std::vector<std::wstring> paths;
 paths.reserve(count);
 for(auto const& selected:view.SelectedItems()){
  auto row=selected.try_as<ListViewItem>();
  if(!row||!row.Tag())return;
  std::uint64_t id=0;
  try{id=unbox_value<std::uint64_t>(row.Tag());}catch(...){return;}
  const auto* item=pane.tabs[tab].indexedItem(
      static_cast<std::size_t>(id));
  if(!item||!item->isFileSystem()||item->parsingName.empty())return;
  paths.push_back(item->parsingName);
 }
 const auto identity=workspace.identity;
 const auto folder=pane.filesystemPaths[tab];
 auto weak=get_weak();
 auto dispatch=DispatcherQueue();
 StatusText().Text(L"선택 항목을 Windows 탐색기로 전달하고 있습니다.");
 try{
  std::thread([paths=std::move(paths),weak,dispatch,
               identity,side,tab,route,folder]{
   const auto result=fxfile::shellexplorer::reveal(paths);
   dispatch.TryEnqueue([weak,result,identity,side,tab,route,folder]{
    auto ui=weak.get();
    if(!ui||ui->mClosing)return;
    const auto& workspace=ui->ActiveWindowTab();
    if(workspace.identity!=identity||
       workspace.model.activePane!=side)return;
    const auto& pane=workspace.model.panes[side];
    if(pane.active!=tab||tab>=pane.routeIds.size()||
       pane.routeIds[tab]!=route||
       tab>=pane.filesystemPaths.size()||
       pane.filesystemPaths[tab]!=folder)return;
    ui->StatusText().Text(SUCCEEDED(result)?
     L"Windows 탐색기에서 항목을 선택했습니다. 압축 등 기본 메뉴를 이용하세요.":
     L"Windows 탐색기에서 선택 항목을 열지 못했습니다.");
   });
  }).detach();
 }catch(...){
  StatusText().Text(L"Windows 탐색기 연결 작업을 시작할 수 없습니다.");
 }
}
void MainWindow::ShowCurrentFolderProperties(int side){
 ShowExternalWindowsContextMenu(side,true,true);
}
void MainWindow::ShowExternalWindowsContextMenu(
 int side,bool propertiesOnly,bool currentFolder){
 // A background target is always Properties; never expose arbitrary verbs
 // against the current folder through this internal target option.
 propertiesOnly=propertiesOnly||currentFolder;
 if(mClosing||side<0||side>1||
    ActiveWindowTab().model.activePane!=side)return;

 if(mFileOperations.busy()||mFileOperations.pendingConfirmationToken()){
  StatusText().Text(L"Shell \uC791\uC5C5\uC774 \uB05D\uB09C \uB4A4 \uC2DC\uB3C4\uD558\uC138\uC694.");
  return;
 }
 const auto& workspace=ActiveWindowTab();
 const auto& pane=workspace.model.panes[side];
 if(pane.active>=pane.tabs.size()||
    pane.active>=pane.pending.size()||
    pane.active>=pane.routeIds.size()||
    pane.active>=pane.filesystemPaths.size()||
    workspace.fileLists[side].visibleTab!=pane.active||
    workspace.fileLists[side].visibleRoute!=pane.routeIds[pane.active])
  return;
 const auto tab=pane.active;
 const auto route=pane.routeIds[tab];
 const auto folder=pane.filesystemPaths[tab];
 const auto identity=workspace.identity;
 if(pane.pending[tab]){
  StatusText().Text(L"현재 폴더를 불러온 후 Windows 메뉴를 여세요.");
  return;
 }
 if(folder.empty()){
  StatusText().Text(L"가상 Shell 항목의 외부 메뉴는 아직 지원하지 않습니다.");
  return;
 }
 auto list=side==0?LeftFiles():RightFiles();
 const auto count=currentFolder?1u:list.SelectedItems().Size();
 if(!count||count>fxfile::shellcontext::kMaxContextSelection){
  StatusText().Text(L"외부 Shell 메뉴는 최대 32개 항목을 선택할 수 있습니다.");
  return;
 }
 auto const& session=pane.tabs[tab];
 std::vector<std::wstring> paths{};
 paths.reserve(count);
 // The external popup is asynchronous: capture exactly which files own its
 // eventual status update, not just the WindowTab/PaneTab and folder.
 std::vector<std::wstring> originalSelection;
 originalSelection.reserve(count);
 std::wstring commonParent;
 std::size_t units=0;
 for(std::uint32_t i=0;i<count;++i){
  std::wstring path=folder;
  if(!currentFolder){
   auto row=list.SelectedItems().GetAt(i).try_as<ListViewItem>();
   if(!row||!row.Tag())return;
   const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
   auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
   if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
    StatusText().Text(L"선택한 파일시스템 항목의 Shell 메뉴를 열 수 없습니다.");
    return;
   }
   path=indexed->parsingName;
  }
  const auto value=std::filesystem::path(path);
  if(!value.is_absolute()||value.lexically_normal().native()!=path||
     path.size()<4||path.size()>1024||
     path.size()>fxfile::shellcontext::kMaxContextPathUnits-units)return;
  auto const parent=value.parent_path().native();
  if(i&&::CompareStringOrdinal(commonParent.c_str(),-1,
                               parent.c_str(),-1,TRUE)!=CSTR_EQUAL){
   StatusText().Text(L"Shell 메뉴는 같은 폴더의 항목만 함께 선택할 수 있습니다.");
   return;
  }
  if(!i)commonParent=parent;
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
     (flags&FILE_ATTRIBUTE_REPARSE_POINT)||
     (currentFolder&&!(flags&FILE_ATTRIBUTE_DIRECTORY)))return;
  for(auto const& prior:paths)
   if(::CompareStringOrdinal(prior.c_str(),-1,
                             path.c_str(),-1,TRUE)==CSTR_EQUAL)return;
  units+=path.size();
  paths.push_back(path);
  if(!currentFolder)originalSelection.push_back(path);
 }
 std::sort(originalSelection.begin(),originalSelection.end());
 const auto expectedSelection=
     std::make_shared<const std::vector<std::wstring>>(
         std::move(originalSelection));
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
 StatusText().Text(propertiesOnly?
  currentFolder?L"현재 폴더의 Windows 속성 창을 여는 중입니다.":
                L"선택 항목의 Windows 속성 창을 여는 중입니다.":
  count>1?
   L"여러 항목의 외부 Windows 메뉴는 속성 확인만 지원합니다. "
   L"복사·이동·삭제는 앱 명령을 사용하세요.":
   L"Windows Shell 확장 메뉴를 분리된 프로세스에서 엽니다.");
 try{
  std::thread([helper=std::move(helper),paths=std::move(paths),
               cursor,dispatch,weak,identity,side,tab,route,folder,
               expectedSelection,propertiesOnly,currentFolder]{
    const DWORD code=fxfile::shellcontext::show(
        helper,paths,cursor,45000,propertiesOnly);
    dispatch.TryEnqueue([weak,code,identity,side,tab,route,folder,
                         expectedSelection,propertiesOnly,currentFolder]{
      if(auto ui=weak.get()){
       if(ui->mClosing)return;
       const auto& live=ui->ActiveWindowTab();
       if(live.identity!=identity||
          live.model.activePane!=side||
          ui->mFileOperations.busy()||
          ui->mFileOperations.pendingConfirmationToken())return;
       const auto& pane=live.model.panes[side];
       if(pane.active!=tab||
          tab>=pane.routeIds.size()||
          tab>=pane.filesystemPaths.size()||
          pane.routeIds[tab]!=route||
          pane.filesystemPaths[tab]!=folder||
          live.fileLists[side].visibleTab!=tab||
          live.fileLists[side].visibleRoute!=route)return;
       // A user may change the selection while a native Properties sheet
       // remains open. An older popup must not overwrite the new selection's
       // status even when the same folder tab and route are still active.
       if(tab>=pane.tabs.size()||tab>=pane.pending.size()||
          pane.pending[tab])return;
       // Folder Properties belongs to the committed folder, regardless of
       // which child files happen to be selected while its sheet is open.
       if(!currentFolder){
        auto selection=side==0?ui->LeftFiles():ui->RightFiles();
        if(selection.SelectedItems().Size()!=expectedSelection->size())return;
        std::vector<std::wstring> actualSelection;
        actualSelection.reserve(expectedSelection->size());
        for(auto const& value:selection.SelectedItems()){
         auto row=value.try_as<ListViewItem>();
         if(!row||!row.Tag())return;
         std::uint64_t logical{};
         try{logical=unbox_value<std::uint64_t>(row.Tag());}
         catch(...){return;}
         const auto* indexed=pane.tabs[tab].indexedItem(
             static_cast<std::size_t>(logical));
         if(!indexed||!indexed->isFileSystem())return;
         actualSelection.push_back(indexed->parsingName);
        }
        std::sort(actualSelection.begin(),actualSelection.end());
        if(actualSelection!=*expectedSelection)return;
       }
       if(code==0)ui->StatusText().Text(propertiesOnly?
          L"Windows 속성 창이 닫혔습니다.":
          L"Windows Shell 확장 메뉴가 종료됐습니다.");
       else if(code==65)ui->StatusText().Text(
          L"이 Windows 메뉴 명령은 실행하지 않았습니다. "
          L"복사·이동·삭제·이름 변경은 flyExplorer 명령을 이용하세요. "
          L"여러 항목의 외부 메뉴는 속성 확인만 지원합니다.");
       else if(code==69)ui->StatusText().Text(
          L"외부 속성 창의 종료를 확인하지 못했습니다. 항목을 확인하세요.");
       else ui->StatusText().Text(
          L"Windows Shell 확장 메뉴를 완료하지 못했습니다.");
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
void MainWindow::ChangeFileSelection(bool invert){
 if(mClosing||mPopulatingFileLists||mFileOperations.busy()||
    mFileOperations.pendingConfirmationToken())return;
 auto const& window=ActiveWindowTab();
 const int side=window.model.activePane;
 if(side<0||side>1||(side==1&&!window.model.split))return;
 auto const& pane=window.model.panes[side];
 const auto tab=pane.active;
 auto const& shown=window.fileLists[side];
 if(tab>=pane.tabs.size()||tab>=pane.pending.size()||
    tab>=pane.routeIds.size()||pane.pending[tab]||
    shown.visibleTab!=tab||shown.visibleRoute!=pane.routeIds[tab]||
    shown.renderedFolder!=pane.tabs[tab].snapshot().parsingName)return;
 auto view=side==0?LeftFiles():RightFiles();
 try{
  if(!view.Tag()||unbox_value<std::uint64_t>(view.Tag())!=window.identity)return;
 }catch(...){return;}
 // Snapshot the complement before clearing; group headers have no file Tag.
 // Only rows already in this rendered page participate. Do not fetch pages.
 std::vector<IInspectable> next;
 if(invert){
  next.reserve(view.Items().Size());
  for(auto const& value:view.Items()){
   auto row=value.try_as<ListViewItem>();
   if(!row||!row.Tag())continue;
   std::uint64_t logical{};
   try{logical=unbox_value<std::uint64_t>(row.Tag());}
   catch(...){return;}
   if(!pane.tabs[tab].indexedItem(static_cast<std::size_t>(logical)))return;
   if(!row.IsSelected())next.push_back(value);
  }
 }
 {
  // One selection publication instead of per-row preview/counter updates.
  mPopulatingFileLists=true;
  struct Reset final{bool& flag;~Reset(){flag=false;}} reset{mPopulatingFileLists};
  view.SelectedItems().Clear();
  for(auto const& item:next)view.SelectedItems().Append(item);
 }
 UpdateSelectionChrome();
 UpdateFooterSummary();
 QueueTextPreview();
 view.Focus(Microsoft::UI::Xaml::FocusState::Keyboard);
 StatusText().Text(invert?L"현재 표시된 항목의 선택을 반전했습니다.":
                          L"파일 선택을 해제했습니다.");
}
void MainWindow::HandleFileShortcut(
 int side,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){
 if(side!=ActiveWindowTab().model.activePane)ActivatePane(side);
 const auto vk=args.Key();
 const auto ctrl=(::GetKeyState(VK_CONTROL)&0x8000)!=0;
 const auto shift=(::GetKeyState(VK_SHIFT)&0x8000)!=0;
 const auto alt=(::GetKeyState(VK_MENU)&0x8000)!=0;
 // Explorer Backspace is history navigation only while the file list owns
 // input. Text editors keep their own deletion behavior outside this route.
 if(!ctrl&&!shift&&!alt&&vk==Windows::System::VirtualKey::Back){
  if(mClosing||mFileOperations.pendingConfirmationToken())return;
  OnBackClicked(nullptr,nullptr);
  args.Handled(true);return;
 }
 // Explorer Alt+Enter opens the selected items' canonical, nonmutating
 // Windows Properties verb through the same isolated Shell boundary.
 if(!ctrl&&!shift&&alt&&vk==Windows::System::VirtualKey::Enter){
  auto view=side==0?LeftFiles():RightFiles();
  if(view.SelectedItems().Size()){
   ShowExternalWindowsContextMenu(side,true);
   args.Handled(true);
  }
  return;
 }
 // Keyboard equivalents of right-click: Shift+F10 and the dedicated
 // Application/Menu key open the same native flyExplorer commands menu.
 // Windows extension verbs remain an explicit menu choice.
 const bool contextMenuKey=
  (!ctrl&&shift&&!alt&&vk==Windows::System::VirtualKey::F10)||
  (!ctrl&&!shift&&!alt&&vk==Windows::System::VirtualKey::Application);
 if(contextMenuKey){
  auto view=side==0?LeftFiles():RightFiles();
  if(view.SelectedItems().Size()){
   auto row=view.SelectedItems().GetAt(0).try_as<ListViewItem>();
   if(row)ShowAppFileContextMenu(side,row,Windows::Foundation::Point{0,0});
  }else{
   // With no file selected Shift+F10 is the keyboard equivalent of
   // right-clicking the empty folder background.
   ShowAppBackgroundContextMenu(side,view,Windows::Foundation::Point{0,0});
  }
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
 if(ctrl&&shift&&!alt&&vk==Windows::System::VirtualKey::C){
  CopySelectedToWindowsClipboard(side,false,true);args.Handled(true);return;
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
 // Explorer Ctrl+D uses the same confirmation and current-pane selection
 // validation as Delete. This route is reached only from a file list.
 if(ctrl&&!shift&&!alt&&vk==Windows::System::VirtualKey::D){
  RunTransfer(fxfile::shelltransfer::Kind::Recycle);
  args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::F2){
  BeginFileNameCommand(fxfile::filecommand::Kind::RenameSelected);args.Handled(true);return;
 }
 if(vk==Windows::System::VirtualKey::Delete){
  RunTransfer(fxfile::shelltransfer::Kind::Recycle);args.Handled(true);
 }
}
}
