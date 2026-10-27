#include "pch.h"
#include "ShellHeader.xaml.h"
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#if __has_include("ShellHeader.g.cpp")
#include "ShellHeader.g.cpp"
#endif
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
ShellHeader::ShellHeader(){InitializeComponent();}
void ShellHeader::PrepareForClose() noexcept{
 if(mClosing)return;
 mClosing=true;
 mHandler={};
 mAddWindowTab={};
 mActivateWindowTab={};
 mCloseWindowTab={};
}
void ShellHeader::SetThemeCallback(std::function<void(int)> handler){
 if(mClosing)return;
 mHandler=std::move(handler);
}
void ShellHeader::ShowChoice(int value){
 if(!ThemeStateText())return;
 ThemeStateText().Text(value==1?L"테마: 라이트":
                       value==2?L"테마: 다크":L"테마: 시스템");
}
void ShellHeader::RestoreTheme(int selection){
 if(mClosing)return;
 if(selection<0||selection>2)selection=0;
 mRestoring=true;
 ThemePicker().SelectedIndex(selection);
 ShowChoice(selection);
 mRestoring=false;
}

void ShellHeader::SetWindowTabCallbacks(std::function<void()> add,
    std::function<void(int)> activate,std::function<void(int)> close){
 if(mClosing)return;
 mAddWindowTab=std::move(add);mActivateWindowTab=std::move(activate);
 mCloseWindowTab=std::move(close);
}
void ShellHeader::SetWindowTabs(std::vector<std::wstring> const& labels,int selected){
 if(mClosing)return;
 mRestoringTabs=true;
 auto tabs=WindowTabStrip();auto items=tabs.TabItems();
 while(items.Size()>labels.size())items.RemoveAtEnd();
 while(items.Size()<labels.size()){
  TabViewItem item;item.IsClosable(true);
  items.Append(item);
 }
 for(uint32_t i=0;i<items.Size();++i){
  auto item=items.GetAt(i).as<TabViewItem>();
  item.Header(winrt::box_value(hstring(labels[i])));
  Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
      item,L"작업 공간 창 탭 "+hstring(labels[i]));
 }
 const int target=labels.empty()?-1:(std::clamp)(selected,0,static_cast<int>(labels.size()-1));
 if(tabs.SelectedIndex()!=target)tabs.SelectedIndex(target);
 mRestoringTabs=false;
}
void ShellHeader::OnWindowTabAdd(TabView const&,IInspectable const&){
 if(mClosing)return;
 auto weak=get_weak();DispatcherQueue().TryEnqueue(Microsoft::UI::Dispatching::DispatcherQueuePriority::Low,[weak]{
  if(auto self=weak.get();self&&!self->mClosing)
   if(self->mAddWindowTab)self->mAddWindowTab();
 });
}
void ShellHeader::OnWindowTabSelectionChanged(
 IInspectable const& sender,SelectionChangedEventArgs const&){
 if(mClosing||mRestoringTabs)return;auto tabs=sender.try_as<TabView>();
 if(tabs&&tabs.SelectedIndex()>=0&&mActivateWindowTab)
  mActivateWindowTab(tabs.SelectedIndex());
}
void ShellHeader::OnWindowTabCloseRequested(
 TabView const& sender,TabViewTabCloseRequestedEventArgs const& args){
 if(mClosing||mRestoringTabs)return;int index=-1;
 for(uint32_t i=0;i<sender.TabItems().Size();++i)
  if(sender.TabItems().GetAt(i)==args.Tab()){index=static_cast<int>(i);break;}
 if(index<0)return;auto weak=get_weak();DispatcherQueue().TryEnqueue(Microsoft::UI::Dispatching::DispatcherQueuePriority::Low,[weak,index]{
  if(auto self=weak.get();self&&!self->mClosing)
   if(self->mCloseWindowTab)self->mCloseWindowTab(index);
 });
}
void ShellHeader::OnThemeSelectionChanged(
 IInspectable const& sender,SelectionChangedEventArgs const&){
 if(mClosing||mRestoring)return;
 const auto n=sender.as<ComboBox>().SelectedIndex();
 if(n<0||n>2)return;
 ShowChoice(n);
 if(mHandler)mHandler(n); // delegate to full-window native settings adapter
}
}
