#pragma once
#include "FileToolbar.g.h"
#include <functional>
namespace winrt::FlyExplorerWinUIShell::implementation {
struct FileToolbar : FileToolbarT<FileToolbar> {
 FileToolbar();
 void SetAction(std::function<void(int)> action);
 void SetSort(std::function<void(int)> change);
 void SetSortIndex(int selection);
 void OnCreateFolder(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnRenameSelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnCopy(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnMove(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnRecycle(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnCancel(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortChanged(IInspectable const&,
   Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
private:
 std::function<void(int)> action_;
 std::function<void(int)> sort_;
 bool restoring_=false;
};
}
namespace winrt::FlyExplorerWinUIShell::factory_implementation {
struct FileToolbar : FileToolbarT<FileToolbar,implementation::FileToolbar>{};
}
