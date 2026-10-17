#include "pch.h"
#include "NavigationSidebar.xaml.h"
#include "../../src/base/shell_assoc_type_core.h"
#include <cstring>
#include <filesystem>
#include <thread>
#include <robuffer.h>
#include "folder_tree_worker.h"
#include <algorithm>
#include <winrt/Microsoft.UI.Xaml.Media.Imaging.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#if __has_include("NavigationSidebar.g.cpp")
#include "NavigationSidebar.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
NavigationSidebar::NavigationSidebar(){
 InitializeComponent();
 LoadKnownFolderArtwork();
}
void NavigationSidebar::SetNavigateCallback(std::function<void(int)> handler){
 mHandler=std::move(handler);
}
void NavigationSidebar::LoadKnownFolderArtwork(){
 wchar_t exe[32768]{};
 const auto count=::GetModuleFileNameW(nullptr,exe,32768);
 if(!count||count>=32768)return;
 auto helper=(std::filesystem::path(exe).parent_path()/
              L"FlyShellIsolationHelper.exe").native();
 auto queue=DispatcherQueue();
 auto weak=get_weak();
 std::thread([weak,queue,helper=std::move(helper)]() mutable {
  auto visuals=fxfile::filetype::queryKnownFolderVisuals(
      helper,{L"desktop",L"documents",L"downloads",
              L"pictures",L"music",L"videos"},2500,16);
  if(visuals.empty())return;
  queue.TryEnqueue([weak,visuals=std::move(visuals)]() mutable {
   if(auto self=weak.get()){
    for(auto const& [key,visual]:visuals)
     if(!visual.bgra.empty())
      self->ApplyKnownFolderArtwork(
          key,visual.bgra,visual.width,visual.height);
   }
  });
 }).detach();
}
void NavigationSidebar::ApplyKnownFolderArtwork(
 std::wstring const& key,std::vector<unsigned char> const& bgra,
 std::uint32_t width,std::uint32_t height){
 if(width!=16||height!=16||bgra.size()!=16u*16u*4u)return;
 Image image{nullptr};
 FontIcon fallback{nullptr};
 if(key==L"desktop"){image=DesktopArtwork();fallback=DesktopFallbackIcon();}
 else if(key==L"documents"){image=DocumentsArtwork();fallback=DocumentsFallbackIcon();}
 else if(key==L"downloads"){image=DownloadsArtwork();fallback=DownloadsFallbackIcon();}
 else if(key==L"pictures"){image=PicturesArtwork();fallback=PicturesFallbackIcon();}
 else if(key==L"music"){image=MusicArtwork();fallback=MusicFallbackIcon();}
 else if(key==L"videos"){image=VideosArtwork();fallback=VideosFallbackIcon();}
 else return;
 try{
  Microsoft::UI::Xaml::Media::Imaging::WriteableBitmap pixels(16,16);
  auto backing=pixels.PixelBuffer();
  winrt::com_ptr<::Windows::Storage::Streams::IBufferByteAccess> access;
  if(FAILED(reinterpret_cast<::IUnknown*>(winrt::get_abi(backing))->
      QueryInterface(__uuidof(::Windows::Storage::Streams::IBufferByteAccess),
                     access.put_void())))return;
  BYTE* target=nullptr;
  if(FAILED(access->Buffer(&target))||!target)return;
  std::memcpy(target,bgra.data(),bgra.size());
  pixels.Invalidate();
  image.Source(pixels);
  image.Visibility(Visibility::Visible);
  fallback.Visibility(Visibility::Collapsed);
 }catch(...){}
}
void NavigationSidebar::SetSelected(int target){
 Button buttons[]={HomeButton(),DocumentsButton(),DownloadsButton(),ThisPCButton(),
                   DesktopButton(),PicturesButton(),MusicButton(),VideosButton()};
 Microsoft::UI::Xaml::Media::Brush accent{nullptr};
 try{
  accent=Application::Current().Resources().Lookup(
      winrt::box_value(L"SystemControlHighlightAccentBrush")).try_as<
          Microsoft::UI::Xaml::Media::Brush>();
 }catch(...){ }
 for(int i=0;i<8;++i){
  buttons[i].BorderThickness(i==target?
      Thickness{2.0,0.0,0.0}:Thickness{0.0,0.0,0.0,0.0});
  if(i==target&&accent)buttons[i].BorderBrush(accent);
 }
}
void NavigationSidebar::OnHomeClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(0);
 if(mHandler)mHandler(0);
}
void NavigationSidebar::OnDocumentsClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(1);
 if(mHandler)mHandler(1);
}
void NavigationSidebar::OnDownloadsClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(2);
 if(mHandler)mHandler(2);
}
void NavigationSidebar::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(3);
 if(mHandler)mHandler(3);
}
void NavigationSidebar::OnDesktopClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(4);
 if(mHandler)mHandler(4);
}
void NavigationSidebar::OnPicturesClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(5);
 if(mHandler)mHandler(5);
}
void NavigationSidebar::OnMusicClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(6);
 if(mHandler)mHandler(6);
}
void NavigationSidebar::OnVideosClicked(IInspectable const&,RoutedEventArgs const&){
 SetSelected(7);
 if(mHandler)mHandler(7);
}
void NavigationSidebar::SetTreeCallbacks(
 std::function<TreeContext()> current,
 std::function<void(std::wstring const&)> navigate){
 mTreeCurrent=std::move(current);
 mTreeNavigate=std::move(navigate);
}
bool NavigationSidebar::IsCurrentTreeOwner() const {
 if(!mTreeVisible||!mTreeCurrent)return false;
 auto next=mTreeCurrent();
 return next.side==mTreeOwner.side && next.tab==mTreeOwner.tab &&
        next.route!=0 && next.route==mTreeOwner.route &&
        next.path==mTreeOwner.path;
}
std::wstring NavigationSidebar::TreePath(TreeViewNode const& node) const {
 for(auto const& item:mTreeNodes)if(item.node==node)return item.path;
 return {};
}
void NavigationSidebar::ResetTree(){
 if(mTreeCancel)mTreeCancel->store(true);
 ++mTreeGeneration;
 mTreePending=false;
 FolderTreeView().RootNodes().Clear();
 mTreeNodes.clear();
 mTreeOwner={};
 FolderTreeStatus().Text(L"");
}
void NavigationSidebar::SyncTreeContext(){
 if(!mTreeVisible||!mTreeCurrent)return;
 auto next=mTreeCurrent();
 if(next.side==mTreeOwner.side&&next.tab==mTreeOwner.tab&&
    next.route&&next.route==mTreeOwner.route&&
    next.path==mTreeOwner.path)return;
 ResetTree();
 mTreeOwner=next;
 if(next.side<0||next.side>1||!next.route||
    !fxfile::foldertree::normalizedDrivePath(next.path)){
  FolderTreeStatus().Text(L"로컬 폴더에서만 트리를 사용할 수 있습니다.");
  return;
 }
 TreeViewNode node;
 node.Content(winrt::box_value(hstring(next.path)));
 node.HasUnrealizedChildren(true);
 mTreeNodes.push_back({node,next.path});
 FolderTreeView().RootNodes().Append(node);
 node.IsExpanded(true);
 BeginTreeLoad(node);
}
void NavigationSidebar::OnFolderTreeToggleClicked(
 IInspectable const&,RoutedEventArgs const&){
 mTreeVisible=!mTreeVisible;
 FolderTreePanel().Visibility(mTreeVisible?Visibility::Visible:Visibility::Collapsed);
 FolderTreeToggle().Content(winrt::box_value(
  mTreeVisible?L"폴더 트리 접기":L"폴더 트리 펼치기"));
 Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
  FolderTreeToggle(),mTreeVisible?L"폴더 트리 숨기기":L"폴더 트리 표시");
 ResetTree();
 if(mTreeVisible)SyncTreeContext();
}
void NavigationSidebar::BeginTreeLoad(TreeViewNode const& node){
 if(!IsCurrentTreeOwner()||!node||!node.HasUnrealizedChildren()||
    mTreePending||mTreeBusy->load())return;
 auto path=TreePath(node);
 if(!fxfile::foldertree::normalizedDrivePath(path))return;
 const auto next=mTreeCurrent();
 fxfile::foldertree::RequestIdentity request{
  next.side,next.tab,next.route,++mTreeGeneration};
 auto cancel=std::make_shared<std::atomic_bool>(false);
 mTreeCancel=cancel;
 mTreePending=true;
 mTreeBusy->store(true);
 FolderTreeStatus().Text(L"하위 폴더를 확인하고 있습니다.");
 auto queue=DispatcherQueue();
 auto weak=get_weak();
 auto busy=mTreeBusy;
 std::thread([path=std::move(path),request,cancel,busy,queue,weak]() mutable {
  auto result=fxfile::foldertree::enumerateFixedChildren(path,*cancel);
  busy->store(false);
  queue.TryEnqueue([path=std::move(path),request,cancel,weak,
                    result=std::move(result)]() mutable {
   if(auto self=weak.get()){
    if(request.generation!=self->mTreeGeneration ||
       cancel->load() || !self->IsCurrentTreeOwner()){
      // Another expanded node may have been waiting for the one worker.
      if(!self->mTreePending && self->IsCurrentTreeOwner()){
       for(auto const& candidate:self->mTreeNodes){
        if(candidate.node.IsExpanded()&&
           candidate.node.HasUnrealizedChildren()){
         self->BeginTreeLoad(candidate.node);
         break;
        }
       }
      }
      return;
    }
    self->mTreePending=false;
    TreeViewNode parent{nullptr};
    for(auto const& entry:self->mTreeNodes)
     if(entry.path==path){parent=entry.node;break;}
    if(!parent||!parent.IsExpanded())return;
    if(!result.complete){
     self->FolderTreeStatus().Text(L"폴더를 안전하게 확인할 수 없습니다.");
     return;
    }
    for(auto const& leaf:result.names){
     std::wstring child;
     if(!fxfile::foldertree::childPath(path,leaf,child))continue;
     TreeViewNode next;
     next.Content(winrt::box_value(hstring(leaf)));
     next.HasUnrealizedChildren(true);
     self->mTreeNodes.push_back({next,std::move(child)});
     parent.Children().Append(next);
    }
    parent.HasUnrealizedChildren(false);
    self->FolderTreeStatus().Text(
     result.limited?L"표시 제한에 도달했습니다. 일부 폴더만 표시합니다.":
     result.names.empty()?L"하위 폴더가 없습니다.":L"");
   }
  });
 }).detach();
}
void NavigationSidebar::OnTreeExpanding(
 TreeView const&,TreeViewExpandingEventArgs const& args){
 BeginTreeLoad(args.Node());
}
void NavigationSidebar::OnTreeCollapsed(
 TreeView const&,TreeViewCollapsedEventArgs const& args){
 auto node=args.Node();
 auto path=TreePath(node);
 if(path.empty())return;
 if(mTreeCancel)mTreeCancel->store(true);
 ++mTreeGeneration;
 mTreePending=false;
 const auto prefix=path.back()==L'\\'?path:path+L'\\';
 mTreeNodes.erase(std::remove_if(mTreeNodes.begin(),mTreeNodes.end(),
  [&prefix](TreeEntry const& entry){
   return entry.path.size()>prefix.size() &&
      entry.path.compare(0,prefix.size(),prefix)==0;
  }),mTreeNodes.end());
 node.Children().Clear();
 node.HasUnrealizedChildren(true);
}
void NavigationSidebar::OnTreeItemInvoked(
 TreeView const&,TreeViewItemInvokedEventArgs const& args){
 if(!IsCurrentTreeOwner()||!mTreeNavigate)return;
 auto node=args.InvokedItem().try_as<TreeViewNode>();
 if(!node)return;
 auto path=TreePath(node);
 if(!fxfile::foldertree::normalizedDrivePath(path))return;
 mTreeNavigate(path);
}

}
