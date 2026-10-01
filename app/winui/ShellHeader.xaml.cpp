#include "pch.h"
#include "ShellHeader.xaml.h"
#if __has_include("ShellHeader.g.cpp")
#include "ShellHeader.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
ShellHeader::ShellHeader(){InitializeComponent();}
void ShellHeader::SetThemeCallback(std::function<void(int)> handler){
 mHandler=std::move(handler);
}
void ShellHeader::ShowChoice(int value){
 if(!ThemeStateText())return;
 ThemeStateText().Text(value==1?L"테마: 라이트":
                       value==2?L"테마: 다크":L"테마: 시스템");
}
void ShellHeader::RestoreTheme(int selection){
 if(selection<0||selection>2)selection=0;
 mRestoring=true;
 ThemePicker().SelectedIndex(selection);
 ShowChoice(selection);
 mRestoring=false;
}
void ShellHeader::OnThemeSelectionChanged(
 IInspectable const& sender,SelectionChangedEventArgs const&){
 if(mRestoring)return;
 const auto n=sender.as<ComboBox>().SelectedIndex();
 if(n<0||n>2)return;
 ShowChoice(n);
 if(mHandler)mHandler(n); // delegate to full-window native settings adapter
}
}
