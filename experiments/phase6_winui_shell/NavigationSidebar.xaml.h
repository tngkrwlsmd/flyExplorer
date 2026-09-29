#pragma once
#include "NavigationSidebar.g.h"
#include <functional>
namespace winrt::FlyExplorerWinUIShell::implementation {
 struct NavigationSidebar : NavigationSidebarT<NavigationSidebar> {
  NavigationSidebar();
  void SetNavigateCallback(std::function<void(int)> handler);
  void OnHomeClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnDocumentsClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnDownloadsClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnThisPCClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 private:
  std::function<void(int)> mHandler; // 0 home, 1 documents, 2 downloads, 3 virtual This PC
 };
}
namespace winrt::FlyExplorerWinUIShell::factory_implementation {
 struct NavigationSidebar : NavigationSidebarT<NavigationSidebar,implementation::NavigationSidebar>{};
}
