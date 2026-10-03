#include "pch.h"
#include "FileToolbar.xaml.h"
#if __has_include("FileToolbar.g.cpp")
#include "FileToolbar.g.cpp"
#endif
#include <winrt/Windows.System.h>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
FileToolbar::FileToolbar(){InitializeComponent();}
void FileToolbar::SetAction(std::function<void(int)> action){action_=std::move(action);}
void FileToolbar::SetSort(std::function<void(int)> sort){sort_=std::move(sort);}
void FileToolbar::SetSortIndex(int value){restoring_=true;SortPicker().SelectedIndex(value);restoring_=false;}
void FileToolbar::SetView(std::function<void(int)> view){view_=std::move(view);}
void FileToolbar::SetViewIndex(int value){ViewDetailsItem().IsChecked(value==0);ViewListItem().IsChecked(value==1);ViewSmallIconsItem().IsChecked(value==2);ViewMediumIconsItem().IsChecked(value==3);ViewLargeIconsItem().IsChecked(value==4);}
void FileToolbar::ChooseSort(int index){restoring_=true;SortPicker().SelectedIndex(index);restoring_=false;if(sort_)sort_(index);}
void FileToolbar::ChooseView(int index){SetViewIndex(index);if(view_)view_(index);}
void FileToolbar::BeginNameEdit(int action,hstring const& initial){pendingNameAction_=action;auto box=FileNameBox();box.Width(180);box.Opacity(1.0);box.IsHitTestVisible(true);box.IsTabStop(true);box.Text(initial);box.PlaceholderText(action==0?L"\uC0C8 \uD3F4\uB354 \uC774\uB984":L"\uC0C8 \uC774\uB984");box.Focus(FocusState::Programmatic);box.SelectAll();}
void FileToolbar::EndNameEdit(){pendingNameAction_=-1;auto box=FileNameBox();box.Text(L"");box.Width(1);box.Opacity(0.0);box.IsHitTestVisible(false);box.IsTabStop(false);}
void FileToolbar::OnCreateFolder(IInspectable const&,RoutedEventArgs const&){if(!action_)return;const auto box=FileNameBox();if((box.Opacity()>=0.5&&pendingNameAction_==0)||(box.Opacity()<0.5&&!box.Text().empty()))action_(9);else action_(0);}
void FileToolbar::OnRenameSelected(IInspectable const&,RoutedEventArgs const&){if(!action_)return;const auto box=FileNameBox();if((box.Opacity()>=0.5&&pendingNameAction_==1)||(box.Opacity()<0.5&&!box.Text().empty()))action_(10);else action_(1);}
void FileToolbar::OnWindowsCut(IInspectable const&,RoutedEventArgs const&){if(action_)action_(6);} void FileToolbar::OnWindowsCopy(IInspectable const&,RoutedEventArgs const&){if(action_)action_(7);} void FileToolbar::OnWindowsPaste(IInspectable const&,RoutedEventArgs const&){if(action_)action_(8);} void FileToolbar::OnCopy(IInspectable const&,RoutedEventArgs const&){if(action_)action_(2);} void FileToolbar::OnMove(IInspectable const&,RoutedEventArgs const&){if(action_)action_(3);} void FileToolbar::OnRecycle(IInspectable const&,RoutedEventArgs const&){if(action_)action_(4);} void FileToolbar::OnCancel(IInspectable const&,RoutedEventArgs const&){if(action_)action_(5);}
void FileToolbar::OnNameKeyDown(IInspectable const&,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){using winrt::Windows::System::VirtualKey;if(args.Key()==VirtualKey::Escape){EndNameEdit();args.Handled(true);return;}if(args.Key()!=VirtualKey::Enter||pendingNameAction_<0)return;if(action_)action_(pendingNameAction_==0?9:10);args.Handled(true);}
void FileToolbar::OnToggleLeftFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(14);} void FileToolbar::OnToggleRightFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(15);} void FileToolbar::OnThemeSystem(IInspectable const&,RoutedEventArgs const&){if(action_)action_(11);} void FileToolbar::OnThemeLight(IInspectable const&,RoutedEventArgs const&){if(action_)action_(12);} void FileToolbar::OnThemeDark(IInspectable const&,RoutedEventArgs const&){if(action_)action_(13);}
void FileToolbar::OnSortNameAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(0);} void FileToolbar::OnSortNameDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(1);} void FileToolbar::OnSortSizeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(2);} void FileToolbar::OnSortDateDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(3);}
void FileToolbar::OnSortTypeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(4);} void FileToolbar::OnSortTypeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(5);} void FileToolbar::OnSortSizeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(6);} void FileToolbar::OnSortDateAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(7);}
void FileToolbar::OnViewDetails(IInspectable const&,RoutedEventArgs const&){ChooseView(0);} void FileToolbar::OnViewList(IInspectable const&,RoutedEventArgs const&){ChooseView(1);} void FileToolbar::OnViewSmallIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(2);} void FileToolbar::OnViewMediumIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(3);} void FileToolbar::OnViewLargeIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(4);}
void FileToolbar::OnSortChanged(IInspectable const& sender,SelectionChangedEventArgs const&){if(!restoring_&&sort_)sort_(sender.as<ComboBox>().SelectedIndex());}
}
