#include "pch.h"
#include "NavigationSidebar.xaml.h"
#if __has_include("NavigationSidebar.g.cpp")
#include "NavigationSidebar.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
namespace winrt::FlyExplorerWinUIShell::implementation {
NavigationSidebar::NavigationSidebar(){InitializeComponent();}
void NavigationSidebar::SetNavigateCallback(std::function<void(int)> handler){
 mHandler=std::move(handler);
}
void NavigationSidebar::OnHomeClicked(IInspectable const&,RoutedEventArgs const&){
 if(mHandler)mHandler(0);
}
void NavigationSidebar::OnDocumentsClicked(IInspectable const&,RoutedEventArgs const&){
 if(mHandler)mHandler(1);
}
void NavigationSidebar::OnDownloadsClicked(IInspectable const&,RoutedEventArgs const&){
 if(mHandler)mHandler(2);
}
void NavigationSidebar::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){
 if(mHandler)mHandler(3);
}
}
