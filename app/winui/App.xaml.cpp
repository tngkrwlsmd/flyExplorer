#include "pch.h"
#include "App.xaml.h"
#include "MainWindow.xaml.h"

using namespace winrt;
using namespace Microsoft::UI::Xaml;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace winrt::FlyExplorer::implementation
{
    // Implemented in MainWindow.xaml.cpp: bounded, opt-in, test-owned only.
    void TraceG01AppLifecycle(char const* stage) noexcept;
    bool G01OwnedAppDiagnosticsEnabled() noexcept;
    void TraceG01AppUnhandledHresult(std::uint32_t code) noexcept;

    /// <summary>
    /// Initializes the singleton application object.  This is the first line of authored code
    /// executed, and as such is the logical equivalent of main() or WinMain().
    /// </summary>
    App::App()
    {
        // Xaml objects should not call InitializeComponent during construction.
        // See https://github.com/microsoft/cppwinrt/tree/master/nuget#initializecomponent

#if defined _DEBUG && !defined DISABLE_XAML_GENERATED_BREAK_ON_UNHANDLED_EXCEPTION
        UnhandledException([](IInspectable const&, UnhandledExceptionEventArgs const& e)
        {
            if (IsDebuggerPresent())
            {
                auto errorMessage = e.Message();
                __debugbreak();
            }
        });
#endif
        // Observe WinUI-routed HRESULTs only for the disposable G01 GUI
        // fixture. Do not read exception messages (they may contain paths),
        // mark exceptions Handled, or alter the normal-user event path.
        if(G01OwnedAppDiagnosticsEnabled()){
            UnhandledException([](
                IInspectable const&,
                Microsoft::UI::Xaml::UnhandledExceptionEventArgs const& e){
                TraceG01AppLifecycle("APP_UNHANDLED_EXCEPTION_ENTER");
                TraceG01AppUnhandledHresult(
                    static_cast<std::uint32_t>(e.Exception().value));
                TraceG01AppLifecycle("APP_UNHANDLED_EXCEPTION_EXIT");
            });
        }
    }

    App::~App()
    {
        // Destruction of App::window follows this destructor body.
        // Distinguish that projected-window release boundary from the
        // already observed MainWindow destructor without changing ownership.
        TraceG01AppLifecycle("APP_DESTRUCTOR_ENTER");
        TraceG01AppLifecycle("APP_DESTRUCTOR_BODY_EXIT");
    }

    /// <summary>
    /// Invoked when the application is launched.
    /// </summary>
    /// <param name="e">Details about the launch request and process.</param>
    void App::OnLaunched([[maybe_unused]] LaunchActivatedEventArgs const& e)
    {
        window = make<MainWindow>();
        window.Activate();
    }
}
