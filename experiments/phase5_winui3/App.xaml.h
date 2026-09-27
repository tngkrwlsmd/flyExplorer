#pragma once

#include "App.xaml.g.h"

namespace winrt::FlyExplorerWinUI3NavPoC::implementation
{
    struct App : AppT<App>
    {
        App();

        void OnLaunched(Microsoft::UI::Xaml::LaunchActivatedEventArgs const&);

    private:
        winrt::Microsoft::UI::Xaml::Window window{ nullptr };
    };
}
