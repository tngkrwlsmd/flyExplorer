#include "pch.h"
#include "FileToolbar.xaml.h"
#if __has_include("FileToolbar.g.cpp")
#include "FileToolbar.g.cpp"
#endif
#include <winrt/Windows.System.h>
#include <winrt/Microsoft.UI.Input.h>
#include <string_view>
#include <cstdio>
#include <string>
namespace {
// Diagnostic only: enabled by an explicit variable in the disposable app
// profile; records fixed event names and booleans, no user content.
void R12EventTrace(char const* phase,int value) noexcept {
 wchar_t enabled[2]{};
 if(GetEnvironmentVariableW(L"R12_UI_TRACE",enabled,2)!=1||enabled[0]!=L'1')return;
 wchar_t directory[MAX_PATH+1]{};
 const DWORD length=GetTempPathW(MAX_PATH+1,directory);
 if(!length||length>=MAX_PATH)return;
 std::wstring output(directory,length);
 output+=L"flyExplorer-r12-events.log";
 HANDLE file=CreateFileW(output.c_str(),FILE_APPEND_DATA,
                        FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,
                        FILE_ATTRIBUTE_NORMAL,nullptr);
 if(file==INVALID_HANDLE_VALUE)return;
 char line[128]{};
 const int bytes=std::snprintf(line,sizeof(line),"%llu %s %d\n",
    static_cast<unsigned long long>(GetTickCount64()),phase,value);
 if(bytes>0&&bytes<static_cast<int>(sizeof(line))){
  DWORD written=0;
  WriteFile(file,line,static_cast<DWORD>(bytes),&written,nullptr);
 }
 CloseHandle(file);
}
}
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
FileToolbar::FileToolbar(){
 InitializeComponent();
 // MenuFlyoutItem may consume Tapped without raising Click (R32 physical
 // pointer evidence). Listen even for handled taps; leave Click untouched.
 using Microsoft::UI::Xaml::Input::TappedEventHandler;
 auto tapWeak=get_weak();
 ViewFileInfoPaneItem().AddHandler(UIElement::TappedEvent(),
    box_value(TappedEventHandler{[tapWeak](
        IInspectable const& sender,
        Microsoft::UI::Xaml::Input::TappedRoutedEventArgs const& args){
        if(auto toolbar=tapWeak.get())toolbar->OnViewFileInfoPaneTapped(sender,args);
    }}),true);
 // Diagnostic only: subscribe to handled pointer events before a flyout
 // opens. Do not alter the product's Click / Closed / queue behavior.
 wchar_t enabled[2]{};
 if(GetEnvironmentVariableW(L"R12_UI_TRACE",enabled,2)!=1||enabled[0]!=L'1')
  return;
 using Microsoft::UI::Xaml::Input::PointerEventHandler;
 using Microsoft::UI::Xaml::Input::PointerRoutedEventArgs;
 using Microsoft::UI::Xaml::Input::TappedRoutedEventArgs;
 // Sample state only: enabled=1, checked=2, hit-test-visible=4.
 // Never suppress or synthesize any product pointer/Click action.
 auto traceState=[](IInspectable const& sender,char const* phase){
  if(auto item=sender.try_as<ToggleMenuFlyoutItem>()){
   const int flags=(item.IsEnabled()?1:0)|
       (item.IsChecked()?2:0)|(item.IsHitTestVisible()?4:0);
   R12EventTrace(phase,flags);
  }
 };
 auto attach=[traceState](
     UIElement const& item,char const* pressed,char const* released,
     char const* pressState,char const* releaseState,
     char const* canceled,char const* captureLost,
     char const* entered,char const* exited,char const* tapped){
  item.AddHandler(UIElement::PointerEnteredEvent(),
      box_value(PointerEventHandler{[entered](
          IInspectable const&,PointerRoutedEventArgs const&){
          R12EventTrace(entered,1);
      }}),true);
  item.AddHandler(UIElement::PointerExitedEvent(),
      box_value(PointerEventHandler{[exited](
          IInspectable const&,PointerRoutedEventArgs const&){
          R12EventTrace(exited,1);
      }}),true);
  item.AddHandler(UIElement::TappedEvent(),
      box_value(TappedEventHandler{[tapped](
          IInspectable const&,TappedRoutedEventArgs const&){
          R12EventTrace(tapped,1);
      }}),true);
  item.AddHandler(UIElement::PointerPressedEvent(),
      box_value(PointerEventHandler{[pressed,pressState,traceState](
          IInspectable const& sender,PointerRoutedEventArgs const&){
          R12EventTrace(pressed,1);
          traceState(sender,pressState);
      }}),true);
  item.AddHandler(UIElement::PointerReleasedEvent(),
      box_value(PointerEventHandler{[released,releaseState,traceState](
          IInspectable const& sender,PointerRoutedEventArgs const&){
          R12EventTrace(released,1);
          traceState(sender,releaseState);
      }}),true);
  item.AddHandler(UIElement::PointerCanceledEvent(),
      box_value(PointerEventHandler{[canceled](
          IInspectable const&,PointerRoutedEventArgs const&){
          R12EventTrace(canceled,1);
      }}),true);
  item.AddHandler(UIElement::PointerCaptureLostEvent(),
      box_value(PointerEventHandler{[captureLost](
          IInspectable const&,PointerRoutedEventArgs const&){
          R12EventTrace(captureLost,1);
      }}),true);
 };
 attach(ViewFileInfoPaneItem(), "details_press", "details_release",
        "details_pstate", "details_rstate",
        "details_cancel", "details_capture_lost",
        "details_enter", "details_exit", "details_tap");
 attach(ViewDetailsItem(), "other_press", "other_release",
        "other_pstate", "other_rstate",
        "other_cancel", "other_capture_lost",
        "other_enter", "other_exit", "other_tap");
}
void FileToolbar::SetAction(std::function<void(int)> action){action_=std::move(action);}
void FileToolbar::SetFileInfoPaneContext(std::function<std::optional<std::uint64_t>()> context){
 fileInfoPaneContext_=std::move(context);
}
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
void FileToolbar::SetViewIndex(int value){ViewDetailsItem().IsChecked(value==0);ViewListItem().IsChecked(value==1);ViewSmallIconsItem().IsChecked(value==2);ViewMediumIconsItem().IsChecked(value==3);ViewLargeIconsItem().IsChecked(value==4);ViewExtraLargeIconsItem().IsChecked(value==5);ViewTilesItem().IsChecked(value==6);ViewContentItem().IsChecked(value==7);}
void FileToolbar::SetFileInfoPaneState(bool visible){
 // Cache the actual workspace state. Changing a MenuFlyoutItem while its
 // pointer press or dismissal is in progress can disturb the next click.
 // Synchronize the toggle immediately before the menu is displayed instead.
 fileInfoPaneVisible_=visible;
 R12EventTrace("pane_state",visible?1:0);
}
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
 if(((action==1||action==2||action==3)&&!isFolder||action==4)&&dot!=std::wstring_view::npos&&
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
void FileToolbar::OnNameKeyDown(IInspectable const&,Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const& args){using winrt::Windows::System::VirtualKey;if(args.Key()==VirtualKey::Escape){EndNameEdit();args.Handled(true);return;}if(args.Key()!=VirtualKey::Enter||pendingNameAction_<0)return;if(action_){const int cmd=pendingNameAction_==0?9:pendingNameAction_==1?10:pendingNameAction_==4?22:pendingNameAction_==3?20:pendingNameAction_==2?16:-1;if(cmd>=0)action_(cmd);}args.Handled(true);}
void FileToolbar::OnToggleLeftFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(14);} void FileToolbar::OnToggleRightFilter(IInspectable const&,RoutedEventArgs const&){if(action_)action_(15);} void FileToolbar::OnThemeSystem(IInspectable const&,RoutedEventArgs const&){if(action_)action_(11);} void FileToolbar::OnThemeLight(IInspectable const&,RoutedEventArgs const&){if(action_)action_(12);} void FileToolbar::OnThemeDark(IInspectable const&,RoutedEventArgs const&){if(action_)action_(13);}
void FileToolbar::OnSortNameAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(0);} void FileToolbar::OnSortNameDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(1);} void FileToolbar::OnSortSizeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(2);} void FileToolbar::OnSortDateDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(3);}
void FileToolbar::OnSortTypeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(4);} void FileToolbar::OnSortTypeDescending(IInspectable const&,RoutedEventArgs const&){ChooseSort(5);} void FileToolbar::OnSortSizeAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(6);} void FileToolbar::OnSortDateAscending(IInspectable const&,RoutedEventArgs const&){ChooseSort(7);}
void FileToolbar::OnViewDetails(IInspectable const&,RoutedEventArgs const&){R12EventTrace("other_view_click",1);ChooseView(0);} void FileToolbar::OnViewList(IInspectable const&,RoutedEventArgs const&){ChooseView(1);} void FileToolbar::OnViewSmallIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(2);} void FileToolbar::OnViewMediumIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(3);} void FileToolbar::OnViewLargeIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(4);} void FileToolbar::OnViewExtraLargeIcons(IInspectable const&,RoutedEventArgs const&){ChooseView(5);} void FileToolbar::OnViewTiles(IInspectable const&,RoutedEventArgs const&){ChooseView(6);} void FileToolbar::OnViewContent(IInspectable const&,RoutedEventArgs const&){ChooseView(7);}
void FileToolbar::OnViewFlyoutOpening(IInspectable const&,IInspectable const&){
 // Each opened flyout owns at most one Details command. A queued tap from
 // an earlier menu must never act on a newly opened menu.
 ++viewFlyoutGeneration_;
 viewFlyoutOpen_=true;
 viewFileInfoPaneClaimed_=false;
 pendingFileInfoPaneToggle_=false;
 fileInfoPaneOpenIdentity_=fileInfoPaneContext_?fileInfoPaneContext_():std::nullopt;
 R12EventTrace("flyout_open",fileInfoPaneVisible_?1:0);
 ViewFileInfoPaneItem().IsChecked(fileInfoPaneVisible_);
 auto item=ViewFileInfoPaneItem();
 R12EventTrace("details_ostate",
     (item.IsEnabled()?1:0)|(item.IsChecked()?2:0)|
     (item.IsHitTestVisible()?4:0));
}
void FileToolbar::OnViewFileInfoPane(IInspectable const&,RoutedEventArgs const&){
 // Keep native Click as the primary mouse, keyboard and UIA command path.
 R12EventTrace("details_click",fileInfoPaneVisible_?1:0);
 if(!viewFlyoutOpen_||viewFileInfoPaneClaimed_)return;
 viewFileInfoPaneClaimed_=true;
 pendingFileInfoPaneToggle_=true;
}
void FileToolbar::OnViewFileInfoPaneTapped(
 IInspectable const&,Microsoft::UI::Xaml::Input::TappedRoutedEventArgs const& args){
 // Only rescue the observed mouse path; never replace keyboard or UIA Click.
 if(args.PointerDeviceType()!=winrt::Microsoft::UI::Input::PointerDeviceType::Mouse||
    !viewFlyoutOpen_||viewFileInfoPaneClaimed_)return;
 // Let any native Click in this input turn win before claiming the gesture.
 auto queue=DispatcherQueue();
 if(!queue)return;
 const auto generation=viewFlyoutGeneration_;
 auto weak=get_weak();
 queue.TryEnqueue([weak,generation]{
  if(auto toolbar=weak.get()){
   if(!toolbar->IsLoaded()||!toolbar->viewFlyoutOpen_||
      toolbar->viewFlyoutGeneration_!=generation||
      toolbar->viewFileInfoPaneClaimed_)return;
   auto const item=toolbar->ViewFileInfoPaneItem();
   auto const flyout=toolbar->ViewButton().Flyout();
   if(!item.IsEnabled()||!item.IsHitTestVisible()||
      !flyout||!flyout.IsOpen()||
      !toolbar->fileInfoPaneContext_||!toolbar->fileInfoPaneOpenIdentity_||
      toolbar->fileInfoPaneContext_()!=toolbar->fileInfoPaneOpenIdentity_)return;
   // Claim before Hide: Closed may arrive synchronously or asynchronously.
   toolbar->viewFileInfoPaneClaimed_=true;
   toolbar->pendingFileInfoPaneToggle_=true;
   R12EventTrace("details_tap_fallback",1);
   flyout.Hide();
  }
 });
}
void FileToolbar::OnViewFlyoutClosed(IInspectable const&,IInspectable const&){
 viewFlyoutOpen_=false;
 viewFileInfoPaneClaimed_=true;
 const bool requested=pendingFileInfoPaneToggle_;
 R12EventTrace("flyout_closed",requested?1:0);
 pendingFileInfoPaneToggle_=false;
 if(!requested||!IsLoaded())return;
 // Closed can fire before the flyout finishes restoring pointer/focus state.
 // Change the layout only after that UI event has returned.
 auto queue=DispatcherQueue();
 if(!queue){
  R12EventTrace("queue_missing",0);
  return;
 }
 auto weak=get_weak();
 const auto generation=viewFlyoutGeneration_;
 const auto identity=fileInfoPaneOpenIdentity_;
 const bool queued=queue.TryEnqueue([weak,generation,identity]{
  if(auto toolbar=weak.get()){
   // If another flyout opened, the old deferred command has no safe owner.
   if(toolbar->viewFlyoutGeneration_!=generation||!toolbar->fileInfoPaneContext_||
      !identity||toolbar->fileInfoPaneContext_()!=identity){
    R12EventTrace("action23_stale",0);
    return;
   }
   if(toolbar->IsLoaded()&&toolbar->action_){
    R12EventTrace("action23_dispatch",1);
    toolbar->action_(23);
   }else R12EventTrace("action23_skipped",0);
  }else R12EventTrace("toolbar_gone",0);
 });
 R12EventTrace("queue_added",queued?1:0);
}
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
