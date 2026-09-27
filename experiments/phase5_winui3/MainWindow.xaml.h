#pragma once
#include "MainWindow.g.h"
#include "NavigationModel.h"
#include "ProductCommandBridge.h"

namespace winrt::FlyExplorerWinUI3NavPoC::implementation
{
    struct MainWindow : MainWindowT<MainWindow>
    {
        MainWindow();
        int32_t MyProperty();
        void MyProperty(int32_t value);

        void OnBackClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnForwardClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnUpClicked(IInspectable const&, Microsoft::UI::Xaml::RoutedEventArgs const&);
        void OnAddressKeyDown(IInspectable const&, Microsoft::UI::Xaml::Input::KeyRoutedEventArgs const&);

    private:
        NavigationModel mNavigation;
        ProductCommandBridge mProductBridge;
        bool TryAttachExplicitProductTestProcess();
        void RunRealProductCommand(std::uint32_t id);
        void RefreshBridge(winrt::hstring const& status);
        void Refresh(winrt::hstring const& status = L"");
    };
}

namespace winrt::FlyExplorerWinUI3NavPoC::factory_implementation
{
    struct MainWindow : MainWindowT<MainWindow, implementation::MainWindow> {};
}
