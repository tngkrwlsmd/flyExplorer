#pragma once

#include "App.xaml.g.h"

namespace winrt::FlyExplorer::implementation
{
    // Test-owned native exception observer. Declared before App::window so
    // its destructor runs AFTER the projected Window member is released.
    // Ordinary application launches never install a handler.
    struct G01OwnedNativeExceptionSubscription final
    {
        void* handle{ nullptr };
        ~G01OwnedNativeExceptionSubscription() noexcept;
        G01OwnedNativeExceptionSubscription() = default;
        G01OwnedNativeExceptionSubscription(
            G01OwnedNativeExceptionSubscription const&) = delete;
        G01OwnedNativeExceptionSubscription& operator=(
            G01OwnedNativeExceptionSubscription const&) = delete;
    };

    struct App : AppT<App>
    {
        App();
        ~App();

        void OnLaunched(Microsoft::UI::Xaml::LaunchActivatedEventArgs const&);

    private:
        G01OwnedNativeExceptionSubscription mG01NativeExceptionSubscription{};
        winrt::Microsoft::UI::Xaml::Window window{ nullptr };
    };
}
