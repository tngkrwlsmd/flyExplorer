#include "pch.h"
#include "NavigationSidebar.xaml.h"
#include "../../src/base/shell_assoc_type_core.h"
#include <cstring>
#include <filesystem>
#include <thread>
#include <robuffer.h>
#include <winrt/Microsoft.UI.Xaml.Media.Imaging.h>
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
}
