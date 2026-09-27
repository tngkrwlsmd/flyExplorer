#include "pch.h"
#include "MainWindow.xaml.h"
#if __has_include("MainWindow.g.cpp")
#include "MainWindow.g.cpp"
#endif
#include <shellapi.h>
#include <winrt/Windows.System.h>
#include <winrt/Microsoft.UI.Xaml.Input.h>
#pragma comment(lib, "shell32.lib")

using namespace winrt;
using namespace Microsoft::UI::Xaml;

namespace {
    std::filesystem::path StartFolder()
    {
        int count = 0;
        auto args = CommandLineToArgvW(GetCommandLineW(), &count);
        if (!args) return std::filesystem::current_path();
        std::filesystem::path result = count > 1 ? std::filesystem::path(args[1]) : std::filesystem::current_path();
        LocalFree(args);
        return result;
    }
}

namespace winrt::FlyExplorerWinUI3NavPoC::implementation
{
    MainWindow::MainWindow() : mNavigation(StartFolder())
    {
        InitializeComponent();
        Refresh(L"Ready");
    }

    int32_t MainWindow::MyProperty() { return 0; }
    void MainWindow::MyProperty(int32_t) {}

    void MainWindow::Refresh(hstring const& status)
    {
        AddressBox().Text(hstring(mNavigation.current.native()));
        BackButton().IsEnabled(!mNavigation.previous.empty());
        ForwardButton().IsEnabled(!mNavigation.next.empty());
        UpButton().IsEnabled(mNavigation.current.parent_path() != mNavigation.current);
        StatusText().Text(status);
        Title(L"Phase5 WinUI3 - " + hstring(mNavigation.current.native()));
    }

    void MainWindow::OnBackClicked(IInspectable const&, RoutedEventArgs const&)
    {
        if (mNavigation.Back()) Refresh(L"Back"); else Refresh(L"Back unavailable");
    }
    void MainWindow::OnForwardClicked(IInspectable const&, RoutedEventArgs const&)
    {
        if (mNavigation.Forward()) Refresh(L"Forward"); else Refresh(L"Forward unavailable");
    }
    void MainWindow::OnUpClicked(IInspectable const&, RoutedEventArgs const&)
    {
        if (mNavigation.Up()) Refresh(L"Up"); else Refresh(L"Up unavailable");
    }
    void MainWindow::OnAddressKeyDown(IInspectable const&, Input::KeyRoutedEventArgs const& eventArgs)
    {
        switch (eventArgs.Key()) {
        case Windows::System::VirtualKey::Enter: {
            // Never create directories: only navigate to an existing folder.
            std::filesystem::path requested(AddressBox().Text().c_str());
            if (mNavigation.Open(requested)) Refresh(L"Opened path");
            else if (requested == mNavigation.current) Refresh(L"Already here");
            else StatusText().Text(L"Not a folder (current path unchanged)");
            eventArgs.Handled(true);
            break;
        }
        case Windows::System::VirtualKey::Escape:
            Refresh(L"Address edit canceled");
            eventArgs.Handled(true);
            break;
        default: break;
        }
    }
}
