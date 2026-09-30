#include "pch.h"
#include "FileToolbar.xaml.h"
#if __has_include("FileToolbar.g.cpp")
#include "FileToolbar.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorerWinUIShell::implementation {
FileToolbar::FileToolbar(){InitializeComponent();}
void FileToolbar::SetAction(std::function<void(int)> action){action_=std::move(action);}
void FileToolbar::SetSort(std::function<void(int)> sort){sort_=std::move(sort);}
void FileToolbar::SetSortIndex(int value){
 restoring_=true;SortPicker().SelectedIndex(value);restoring_=false;
}
void FileToolbar::OnCreateFolder(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(0);
}
void FileToolbar::OnRenameSelected(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(1);
}
void FileToolbar::OnWindowsCut(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(6);
}
void FileToolbar::OnWindowsCopy(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(7);
}
void FileToolbar::OnWindowsPaste(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(8);
}
void FileToolbar::OnCopy(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(2);
}
void FileToolbar::OnMove(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(3);
}
void FileToolbar::OnRecycle(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(4);
}
void FileToolbar::OnCancel(IInspectable const&,RoutedEventArgs const&){
 if(action_)action_(5);
}
void FileToolbar::OnSortChanged(IInspectable const& sender,
 SelectionChangedEventArgs const&){
 if(!restoring_&&sort_)sort_(sender.as<ComboBox>().SelectedIndex());
}
}
