#pragma once
#include "App.xaml.g.h"
#include <winrt/Microsoft.UI.Xaml.Hosting.h>
namespace winrt::FlyExplorerIslandBridge::implementation {
struct App : AppT<App> {
  App();
  winrt::Microsoft::UI::Xaml::Hosting::WindowsXamlManager m_manager{nullptr};
  void OnLaunched(Microsoft::UI::Xaml::LaunchActivatedEventArgs const&);
};
}
