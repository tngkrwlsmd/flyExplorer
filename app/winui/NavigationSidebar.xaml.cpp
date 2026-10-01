#include "pch.h"
#include "NavigationSidebar.xaml.h"
#if __has_include("NavigationSidebar.g.cpp")
#include "NavigationSidebar.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
NavigationSidebar::NavigationSidebar(){InitializeComponent();}
void NavigationSidebar::SetNavigateCallback(std::function<void(int)> handler){
 mHandler=std::move(handler);
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
