#pragma once

#include "App.xaml.g.h"

namespace winrt::FlyExplorer::implementation
{
    struct App : AppT<App>
    {
        App();
        ~App();

        void OnLaunched(Microsoft::UI::Xaml::LaunchActivatedEventArgs const&);

    private:
        // C++ destroys members in reverse declaration order: the Window
        // releases before this diagnostic-only witness is destroyed.
        struct WindowReleaseWitness
        {
            ~WindowReleaseWitness() noexcept;
        };
        WindowReleaseWitness mWindowReleaseWitness{};
        winrt::Microsoft::UI::Xaml::Window window{ nullptr };
    };
}
