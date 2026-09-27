#include "pch.h"
#include "MainWindow.xaml.h"
#if __has_include("MainWindow.g.cpp")
#include "MainWindow.g.cpp"
#endif
#include <shellapi.h>
#include <string>
#include <cwchar>
#include <cstdint>
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
        if (!TryAttachExplicitProductTestProcess()) Refresh(L"Ready");
    }

    int32_t MainWindow::MyProperty() { return 0; }
    void MainWindow::MyProperty(int32_t) {}

    bool MainWindow::TryAttachExplicitProductTestProcess()
    {
        int count = 0;
        auto argv = ::CommandLineToArgvW(::GetCommandLineW(), &count);
        if (!argv) return false;
        DWORD pid{};
        HWND hwnd{};
        // Both flags are mandatory. Never auto-discover or target user's
        // existing flyExplorer process. Test launcher owns these identifiers.
        if (count == 4) {
            const std::wstring a = argv[2], b = argv[3];
            const std::wstring pidFlag = L"--test-product-pid=";
            const std::wstring hwndFlag = L"--test-product-hwnd=";
            if (a.compare(0, pidFlag.size(), pidFlag) == 0 &&
                b.compare(0, hwndFlag.size(), hwndFlag) == 0) {
                try {
                    const std::wstring pv = a.substr(pidFlag.size());
                    const std::wstring hv = b.substr(hwndFlag.size());
                    size_t pi{}, hi{};
                    const auto parsedPid = std::stoull(pv, &pi, 10);
                    const auto parsedWindow = std::stoull(hv, &hi, 10);
                    if (pi == pv.size() && hi == hv.size() &&
                        parsedPid > 0 && parsedPid <= UINT32_MAX) {
                        pid = static_cast<DWORD>(parsedPid);
                        hwnd = reinterpret_cast<HWND>(static_cast<uintptr_t>(parsedWindow));
                    }
                } catch (...) { /* Fail closed. */ }
            }
        }
        ::LocalFree(argv);
        if (!mProductBridge.Attach(pid, hwnd)) return false;
        AddressBox().IsReadOnly(true);
        AddressBox().PlaceholderText(L"Product title (address editing not bridged)");
        RefreshBridge(L"Bound to explicitly test-owned flyExplorer MainFrame");
        return true;
    }

    void MainWindow::RefreshBridge(hstring const& status)
    {
        AddressBox().Text(hstring(mProductBridge.ProductTitle()));
        // Disabling buttons according to real active-pane state requires a
        // separate read-only state adapter; this proof tests command dispatch.
        BackButton().IsEnabled(mProductBridge.Connected());
        ForwardButton().IsEnabled(mProductBridge.Connected());
        UpButton().IsEnabled(mProductBridge.Connected());
        StatusText().Text(status);
        Title(L"Phase5 bridge - " + hstring(mProductBridge.ProductTitle()));
    }

    void MainWindow::RunRealProductCommand(std::uint32_t id)
    {
        const bool handled = mProductBridge.SendNavCommand(id);
        RefreshBridge(handled ? L"Actual product command handled" :
                                L"Product command rejected or unavailable");
    }

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
        if (mProductBridge.Connected()) { RunRealProductCommand(ID_GO_BACK); return; }
        if (mNavigation.Back()) Refresh(L"Back"); else Refresh(L"Back unavailable");
    }
    void MainWindow::OnForwardClicked(IInspectable const&, RoutedEventArgs const&)
    {
        if (mProductBridge.Connected()) { RunRealProductCommand(ID_GO_FORWARD); return; }
        if (mNavigation.Forward()) Refresh(L"Forward"); else Refresh(L"Forward unavailable");
    }
    void MainWindow::OnUpClicked(IInspectable const&, RoutedEventArgs const&)
    {
        if (mProductBridge.Connected()) { RunRealProductCommand(ID_GO_UP); return; }
        if (mNavigation.Up()) Refresh(L"Up"); else Refresh(L"Up unavailable");
    }
    void MainWindow::OnAddressKeyDown(IInspectable const&, Input::KeyRoutedEventArgs const& eventArgs)
    {
        if (mProductBridge.Connected()) { eventArgs.Handled(true); return; }
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
