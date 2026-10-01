#pragma once
#include "FileToolbar.g.h"
#include <functional>
namespace winrt::FlyExplorer::implementation {
struct FileToolbar : FileToolbarT<FileToolbar> {
 FileToolbar();
 void SetAction(std::function<void(int)> action);
 void SetSort(std::function<void(int)> change);
 void SetSortIndex(int selection);
 void BeginNameEdit(int action,winrt::hstring const& initial);
 void EndNameEdit();
 void OnCreateFolder(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnRenameSelected(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnWindowsCut(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnWindowsCopy(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnWindowsPaste(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnCopy(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnMove(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnRecycle(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnCancel(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnNameKeyDown(IInspectable const&,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);
 void OnToggleLeftFilter(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnToggleRightFilter(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnThemeSystem(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnThemeLight(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnThemeDark(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortChanged(IInspectable const&,
   Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
private:
 std::function<void(int)> action_;
 std::function<void(int)> sort_;
 bool restoring_=false;
 int pendingNameAction_=-1;
};
}
namespace winrt::FlyExplorer::factory_implementation {
struct FileToolbar : FileToolbarT<FileToolbar,implementation::FileToolbar>{};
}
