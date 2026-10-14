#pragma once
#include "FileToolbar.g.h"
#include <functional>
namespace winrt::FlyExplorer::implementation {
struct FileToolbar : FileToolbarT<FileToolbar> {
 FileToolbar();
 void SetAction(std::function<void(int)> action);
 void SetSort(std::function<void(int)> change);
 void SetSortIndex(int selection);
 void SetView(std::function<void(int)> change);
 void SetViewIndex(int selection);
 void SetListDisplay(std::function<void(int)> change);
 void SetListDisplayState(bool checkboxes,bool compactRows,bool showExtensions,bool showHidden);
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
 void OnSortNameAscending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortNameDescending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortSizeDescending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortDateDescending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortTypeAscending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortTypeDescending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortSizeAscending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortDateAscending(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewDetails(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewList(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewSmallIcons(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewMediumIcons(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewLargeIcons(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewCheckboxes(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewCompactRows(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewFileExtensions(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnViewHiddenItems(IInspectable const&,Microsoft::UI::Xaml::RoutedEventArgs const&);
 void OnSortChanged(IInspectable const&,Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
private:
 void ChooseSort(int index);
 void ChooseView(int index);
 std::function<void(int)> action_;
 std::function<void(int)> sort_;
 std::function<void(int)> view_;
 std::function<void(int)> listDisplay_;
 bool restoring_=false;
 int pendingNameAction_=-1;
};
}
namespace winrt::FlyExplorer::factory_implementation { struct FileToolbar : FileToolbarT<FileToolbar,implementation::FileToolbar>{}; }
