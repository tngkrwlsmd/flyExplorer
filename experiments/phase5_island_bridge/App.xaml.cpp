#include "pch.h"
#include "App.xaml.h"
#if __has_include("App.g.cpp")
#include "App.g.cpp"
#endif
namespace winrt::FlyExplorerIslandBridge::implementation {
App::App() { m_manager = Microsoft::UI::Xaml::Hosting::WindowsXamlManager::InitializeForCurrentThread(); }
void App::OnLaunched(Microsoft::UI::Xaml::LaunchActivatedEventArgs const&) {}
}
