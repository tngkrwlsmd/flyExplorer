#pragma once
#include "ShellHeader.g.h"
#include <functional>
#include <string>
#include <vector>
namespace winrt::FlyExplorer::implementation {
 struct ShellHeader : ShellHeaderT<ShellHeader> {
  ShellHeader();
  void SetThemeCallback(std::function<void(int)> handler);
  void RestoreTheme(int selection);
  void SetWindowTabCallbacks(std::function<void()> add,
      std::function<void(int)> activate,std::function<void(int)> close);
  void SetWindowTabs(std::vector<std::wstring> const& labels,int selected);
  Microsoft::UI::Xaml::Controls::TabView WindowTabs(){return WindowTabStrip();}
  Microsoft::UI::Xaml::UIElement DragRegion(){ return TitleBarDragRegion(); }
  void OnThemeSelectionChanged(IInspectable const&,
      Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
  void OnWindowTabAdd(Microsoft::UI::Xaml::Controls::TabView const&,IInspectable const&);
  void OnWindowTabSelectionChanged(IInspectable const&,
      Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
  void OnWindowTabCloseRequested(Microsoft::UI::Xaml::Controls::TabView const&,
      Microsoft::UI::Xaml::Controls::TabViewTabCloseRequestedEventArgs const&);
 private:
  bool mRestoring=false,mRestoringTabs=false;
  std::function<void(int)> mHandler;
  std::function<void()> mAddWindowTab;
  std::function<void(int)> mActivateWindowTab,mCloseWindowTab;
  void ShowChoice(int);
 };
}
namespace winrt::FlyExplorer::factory_implementation {
 struct ShellHeader : ShellHeaderT<ShellHeader,implementation::ShellHeader>{};
}
