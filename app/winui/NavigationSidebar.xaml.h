#pragma once
#include "NavigationSidebar.g.h"
#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <atomic>
#include <memory>
#include "folder_tree_path.h"
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
  struct TreeContext final {
    std::wstring path;
    int side=-1;
    std::size_t tab=0;
    std::uint64_t route=0;
  };
  void SetTreeCallbacks(std::function<TreeContext()> current,
                        std::function<void(std::wstring const&)> navigate);
  void SyncTreeContext();
  void OnFolderTreeToggleClicked(IInspectable const&,
                               Microsoft::UI::Xaml::RoutedEventArgs const&);
  void OnTreeExpanding(Microsoft::UI::Xaml::Controls::TreeView const&,
                       Microsoft::UI::Xaml::Controls::TreeViewExpandingEventArgs const&);
  void OnTreeCollapsed(Microsoft::UI::Xaml::Controls::TreeView const&,
                       Microsoft::UI::Xaml::Controls::TreeViewCollapsedEventArgs const&);
  void OnTreeItemInvoked(Microsoft::UI::Xaml::Controls::TreeView const&,
                         Microsoft::UI::Xaml::Controls::TreeViewItemInvokedEventArgs const&);

 private:
  void SetSelected(int target);
  void LoadKnownFolderArtwork();
  void ApplyKnownFolderArtwork(std::wstring const& key,
      std::vector<unsigned char> const& bgra,
      std::uint32_t width,std::uint32_t height);
  std::function<void(int)> mHandler; // 0 home, 1 docs, 2 downloads, 3 This PC, 4..7 known profile folders
  struct TreeEntry final {
    Microsoft::UI::Xaml::Controls::TreeViewNode node{nullptr};
    std::wstring path;
  };
  void BeginTreeLoad(Microsoft::UI::Xaml::Controls::TreeViewNode const& node);
  void ResetTree();
  bool IsCurrentTreeOwner() const;
  std::wstring TreePath(Microsoft::UI::Xaml::Controls::TreeViewNode const& node) const;
  std::function<TreeContext()> mTreeCurrent;
  std::function<void(std::wstring const&)> mTreeNavigate;
  TreeContext mTreeOwner;
  std::vector<TreeEntry> mTreeNodes;
  std::shared_ptr<std::atomic_bool> mTreeBusy=std::make_shared<std::atomic_bool>(false);
  std::shared_ptr<std::atomic_bool> mTreeCancel;
  std::uint64_t mTreeGeneration=1;
  bool mTreeVisible=false;
  bool mTreePending=false;
 };
}
namespace winrt::FlyExplorer::factory_implementation {
 struct NavigationSidebar : NavigationSidebarT<NavigationSidebar,implementation::NavigationSidebar>{};
}
