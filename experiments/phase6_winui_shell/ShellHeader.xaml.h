#pragma once
#include "ShellHeader.g.h"
#include <functional>
namespace winrt::FlyExplorerWinUIShell::implementation {
 struct ShellHeader : ShellHeaderT<ShellHeader> {
  ShellHeader();
  void SetThemeCallback(std::function<void(int)> handler);
  void RestoreTheme(int selection);
  void OnThemeSelectionChanged(IInspectable const&,
      Microsoft::UI::Xaml::Controls::SelectionChangedEventArgs const&);
 private:
  bool mRestoring=false;
  std::function<void(int)> mHandler;
  void ShowChoice(int);
 };
}
namespace winrt::FlyExplorerWinUIShell::factory_implementation {
 struct ShellHeader : ShellHeaderT<ShellHeader,implementation::ShellHeader>{};
}
