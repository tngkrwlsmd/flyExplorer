#pragma once
#include "NavigationSidebar.g.h"
#include <cstdint>
#include <string>
#include <vector>
#include <functional>
namespace winrt::FlyExplorer::implementation {
 struct NavigationSidebar : NavigationSidebarT<NavigationSidebar> {
  NavigationSidebar();
  void SetNavigateCallback(std::function<void(int)> handler);
  void OnHomeClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnDocumentsClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnDownloadsClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnThisPCClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnDesktopClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnPicturesClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnMusicClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnVideosClicked(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 private:
  void SetSelected(int target);
  void LoadKnownFolderArtwork();
  void ApplyKnownFolderArtwork(std::wstring const& key,
      std::vector<unsigned char> const& bgra,
      std::uint32_t width,std::uint32_t height);
  std::function<void(int)> mHandler; // 0 home, 1 docs, 2 downloads, 3 This PC, 4..7 known profile folders
 };
}
namespace winrt::FlyExplorer::factory_implementation {
 struct NavigationSidebar : NavigationSidebarT<NavigationSidebar,implementation::NavigationSidebar>{};
}
