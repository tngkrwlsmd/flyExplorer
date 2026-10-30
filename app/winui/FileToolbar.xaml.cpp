#include "pch.h"
#include "FileToolbar.xaml.h"
#if __has_include("FileToolbar.g.cpp")
#include "FileToolbar.g.cpp"
#endif
#include <winrt/Windows.System.h>
#include <string_view>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
FileToolbar::FileToolbar(){InitializeComponent();}
void FileToolbar::SetAction(std::function<void(int)> action){action_=std::move(action);}
void FileToolbar::SetSort(std::function<void(int)> sort){sort_=std::move(sort);}
void FileToolbar::SetSortIndex(int value){
 restoring_=true;SortPicker().SelectedIndex(value);restoring_=false;
 SortNameAscendingItem().IsChecked(value==0);SortNameDescendingItem().IsChecked(value==1);
 SortTypeAscendingItem().IsChecked(value==4);SortTypeDescendingItem().IsChecked(value==5);
 SortSizeAscendingItem().IsChecked(value==6);SortSizeDescendingItem().IsChecked(value==2);
 SortDateAscendingItem().IsChecked(value==7);SortDateDescendingItem().IsChecked(value==3);
}
void FileToolbar::SetView(std::function<void(int)> view){view_=std::move(view);}
void FileToolbar::SetFolderViewAction(std::function<void(bool)> action){
 folderViewAction_=std::move(action);
}
void FileToolbar::SetListDisplay(std::function<void(int)> change){listDisplay_=std::move(change);}
void FileToolbar::SetGroup(std::function<void(int)> change){group_=std::move(change);}
void FileToolbar::SetGroupState(int mode){
 ViewGroupByTypeItem().IsChecked(mode==1);
 ViewGroupByNameItem().IsChecked(mode==2);
 ViewGroupBySizeItem().IsChecked(mode==3);
 ViewGroupByMonthItem().IsChecked(mode==4);
}
void FileToolbar::SetListDisplayState(bool checkboxes,bool compactRows,bool showExtensions,bool showHidden){
 ViewCheckboxesItem().IsChecked(checkboxes);
 ViewCompactRowsItem().IsChecked(compactRows);
 ViewFileExtensionsItem().IsChecked(showExtensions);
 ViewHiddenItemsItem().IsChecked(showHidden);
}
void FileToolbar::SetViewIndex(int value){ViewDetailsItem().IsChecked(value==0);ViewListItem().IsChecked(value==1);ViewSmallIconsItem().IsChecked(value==2);ViewMediumIconsItem().IsChecked(value==3);ViewLargeIconsItem().IsChecked(value==4);}
void FileToolbar::ChooseSort(int index){SetSortIndex(index);if(sort_)sort_(index);}
void FileToolbar::ChooseView(int index){SetViewIndex(index);if(view_)view_(index);}
void FileToolbar::BeginNameEdit(int action,hstring const& initial,bool isFolder){
 pendingNameAction_=action;
 nameFocusAfterMoreClosed_=MoreButton().Flyout().IsOpen();
 auto box=FileNameBox();
 box.Width(180);
 box.Opacity(1.0);
 box.IsHitTestVisible(true);
 box.IsTabStop(true);
 box.Text(initial);
 box.PlaceholderText(action==0?L"\uC0C8 \uD3F4\uB354 \uC774\uB984":L"\uC0C8 \uC774\uB984");
 box.Focus(FocusState::Programmatic);
 // Keep the last extension unselected for regular filesystem files.
 // Select entire names for folders, dotfiles, trailing dots and extensionless files.
 const auto name=std::wstring_view{initial.c_str()};
 const auto dot=name.find_last_of(L'.');
 if((action==1||action==2||action==3)&&!isFolder&&dot!=std::wstring_view::npos&&
    dot>0&&dot+1<name.size())
     box.Select(0,static_cast<int>(dot));
 else box.SelectAll();
}
void FileToolbar::OnMoreFlyoutClosed(IInspectable const&,IInspectable const&){
 // Flyout dismissal restores its opener's focus after the item Click.
 // Complete only the edit opened by that menu, without overriding new input.
 const bool restore=nameFocusAfterMoreClosed_;
 nameFocusAfterMoreClosed_=false;
 if(!restore||pendingNameAction_<0||!IsLoaded())return;
 auto box=FileNameBox();
 if(box.Opacity()<0.5||!box.IsTabStop()||
    Input::FocusManager::GetFocusedElement(XamlRoot())!=MoreButton())return;
 UpdateLayout();
 box.Focus(FocusState::Programmatic);
}
void FileToolbar::EndNameEdit(){nameFocusAfterMoreClosed_=false;pendingNameAction_=-1;auto box=FileNameBox();box.Text(L"");box.Width(1);box.Opacity(0.0);box.IsHitTestVisible(false);box.IsTabStop(false);}
void FileToolbar::OnCreateFolder(IInspectable const&,RoutedEventArgs const&){if(!action_)return;const auto box=FileNameBox();if((box.Opacity()>=0.5&&pendingNameAction_==0)||(box.Opacity()<0.5&&!box.Text().empty()))action_(9);else action_(0);}
void FileToolbar::OnNewFolderMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(0);}
void FileToolbar::OnNewTextFileMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(17);}
void FileToolbar::OnNewMarkdownFileMenu(IInspectable const&,RoutedEventArgs const&){if(action_)action_(21);}
void FileToolbar::OnClearFileSelection(IInspectable const&,RoutedEventArgs const&){if(action_)action_(18);}
void FileToolbar::OnInvertFileSelection(IInspectable const&,RoutedEventArgs const&){if(action_)action_(19);}
void FileToolbar::OnRenameSelected(IInspectable const&,RoutedEventArgs const&){if(!action_)return;const auto box=FileNameBox();if((box.Opacity()>=0.5&&pendingNameAction_==1)||(box.Opacity()<0.5&&!box.Text().empty()))action_(10);else action_(1);}
void FileToolbar::OnWindowsCut(IInspectable const&,RoutedEventArgs const&){if(action_)action_(6);} void FileToolbar::OnWindowsCopy(IInspectable const&,RoutedEventArgs const&){if(action_)action_(7);} void FileToolbar::OnWindowsPaste(IInspectable const&,RoutedEventArgs const&){if(action_)action_(8);} void FileToolbar::OnCopy(IInspectable const&,RoutedEventArgs const&){if(action_)action_(2);} void FileToolbar::OnMove(IInspectable const&,RoutedEventArgs const&){if(action_)action_(3);} void FileToolbar::OnRecycle(IInspectable const&,RoutedEventArgs const&){if(action_)action_(4);} void FileToolbar::OnCancel(IInspectable const&,RoutedEventArgs const&){if(action_)action_(5);}
void FileToolbar::OnNameKeyDown(IInspectable const&,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){using winrt::Windows::System::VirtualKey;if(args.Key()==VirtualKey::Escape){EndNameEdit();args.Handled(true);return;}if(args.Key()!=VirtualKey::Enter||pendingNameAction_<0)return;if(action_){const int cmd=pendingNameAction_==0?9:pendingNameAction_==1?10:pendingNameAction_==3?20:pendingNameAction_==2?16:-1;if(cmd>=0)action_(cmd);}args.Handled(true);}
void FileToolbar::OnToggleLeftFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(14);} void FileToolbar::OnToggleRightFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(15);} void FileToolbar::OnThemeSystem(IInspectable const&,RoutedEventArgs const&){if(action_)action_(11);} void FileToolbar::OnThemeLight(IInspectable const&,RoutedEventArgs const&){if(action_)action_(12);} void FileToolbar::OnThemeDark(IInspectable const&,RoutedEventArgs const&){if(action_)action_(13);}
void FileToolbar::OnSortNameAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(0);} void FileToolbar::OnSortNameDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(1);} void FileToolbar::OnSortSizeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(2);} void FileToolbar::OnSortDateDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(3);}
void FileToolbar::OnSortTypeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(4);} void FileToolbar::OnSortTypeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(5);} void FileToolbar::OnSortSizeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(6);} void FileToolbar::OnSortDateAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(7);}
void FileToolbar::OnViewDetails(IInspectable const&,RoutedEventArgs const&){ChooseView(0);} void FileToolbar::OnViewList(IInspectable const&,RoutedEventArgs const&){ChooseView(1);} void FileToolbar::OnViewSmallIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(2);} void FileToolbar::OnViewMediumIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(3);} void FileToolbar::OnViewLargeIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(4);}
void FileToolbar::OnRememberFolderView(IInspectable const&,RoutedEventArgs const&){
 if(folderViewAction_)folderViewAction_(true);
}
void FileToolbar::OnForgetFolderView(IInspectable const&,RoutedEventArgs const&){
 if(folderViewAction_)folderViewAction_(false);
}
void FileToolbar::OnViewCheckboxes(IInspectable const&,RoutedEventArgs const&){if(listDisplay_)listDisplay_(0);}
void FileToolbar::OnViewCompactRows(IInspectable const&,RoutedEventArgs const&){if(listDisplay_)listDisplay_(1);}
void FileToolbar::OnViewFileExtensions(IInspectable const&,RoutedEventArgs const&){if(listDisplay_)listDisplay_(2);}
void FileToolbar::OnViewHiddenItems(IInspectable const&,RoutedEventArgs const&){if(listDisplay_)listDisplay_(3);}
void FileToolbar::OnViewGroupByType(IInspectable const&,RoutedEventArgs const&){if(group_)group_(1);}
void FileToolbar::OnViewGroupByName(IInspectable const&,RoutedEventArgs const&){if(group_)group_(2);}
void FileToolbar::OnViewGroupBySize(IInspectable const&,RoutedEventArgs const&){if(group_)group_(3);}
void FileToolbar::OnViewGroupByMonth(IInspectable const&,RoutedEventArgs const&){if(group_)group_(4);}
void FileToolbar::OnSortChanged(IInspectable const& sender,SelectionChangedEventArgs const&){if(!restoring_&&sort_)ChooseSort(sender.as<ComboBox>().SelectedIndex());}
}
