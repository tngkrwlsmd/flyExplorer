#include "pch.h"
#include "App.xaml.h"
#include "MainWindow.xaml.h"
#include <cstdio>
#include <cwchar>

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

#if defined(_M_X64)
    namespace {
        // Diagnostic only. The G01 owned fixture installs this observer;
        // no handler is registered during ordinary application startup.
        volatile LONG gG01StowedClaimed = 0;

        char const* G01StowedModule(DWORD64 ip, DWORD64& rva) noexcept
        {
            void* base = nullptr;
            if (!::RtlPcToFileHeader(reinterpret_cast<void*>(ip), &base) || !base)
                return "OTHER";
            rva = ip - reinterpret_cast<DWORD64>(base);
            wchar_t modulePath[MAX_PATH]{};
            auto length = ::GetModuleFileNameW(
                static_cast<HMODULE>(base), modulePath, MAX_PATH);
            if (!length || length >= MAX_PATH) return "OTHER";
            wchar_t const* name = modulePath;
            for (auto it = modulePath; *it; ++it)
                if (*it == L'\\' || *it == L'/') name = it + 1;
            if (_wcsicmp(name, L"flyExplorer.exe") == 0) return "FLY";
            if (_wcsicmp(name, L"Microsoft.UI.Xaml.dll") == 0) return "XAML";
            if (_wcsicmp(name, L"combase.dll") == 0) return "COMBASE";
            if (_wcsicmp(name, L"CoreMessagingXP.dll") == 0) return "COREMSG";
            if (_wcsicmp(name, L"ntdll.dll") == 0) return "NTDLL";
            return "OTHER";
        }

        LONG CALLBACK ObserveG01NativeStowed(
            EXCEPTION_POINTERS* exception) noexcept
        {
            if (!exception || !exception->ExceptionRecord ||
                !exception->ContextRecord ||
                exception->ExceptionRecord->ExceptionCode != 0xC000027B)
                return EXCEPTION_CONTINUE_SEARCH;
            if (::InterlockedCompareExchange(&gG01StowedClaimed, 1, 0))
                return EXCEPTION_CONTINUE_SEARCH;

            TraceG01AppLifecycle("NATIVE_STOWED_ENTER");
            CONTEXT frame = *exception->ContextRecord;
            // Unwind the faulting x64 context, not the observer's own stack.
            // Only approved module labels and 32-bit module-relative RVAs
            // leave the process. Never export raw pointers or stack memory.
            for (unsigned index = 0; index < 8 && frame.Rip; ++index) {
                DWORD64 rva = 0;
                auto const module = G01StowedModule(frame.Rip, rva);
                if (rva <= 0xFFFFFFFFull) {
                    char phase[80]{};
                    auto const length = std::snprintf(
                        phase, sizeof(phase),
                        "NATIVE_STOWED_FRAME_%02u_%s_%08X",
                        index, module, static_cast<unsigned>(rva));
                    if (length > 0 && length < sizeof(phase))
                        TraceG01AppLifecycle(phase);
                }
                DWORD64 imageBase = 0;
                auto const entry = ::RtlLookupFunctionEntry(
                    frame.Rip, &imageBase, nullptr);
                if (!entry) break; // Never guess an unmanaged leaf frame.
                void* handlerData = nullptr;
                DWORD64 establisherFrame = 0;
                auto const previousRip = frame.Rip;
                auto const previousRsp = frame.Rsp;
                ::RtlVirtualUnwind(
                    UNW_FLAG_NHANDLER, imageBase, frame.Rip, entry,
                    &frame, &handlerData, &establisherFrame, nullptr);
                if (!frame.Rip ||
                    (frame.Rip == previousRip && frame.Rsp <= previousRsp))
                    break;
            }
            TraceG01AppLifecycle("NATIVE_STOWED_EXIT");
            return EXCEPTION_CONTINUE_SEARCH;
        }
    }
#endif

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
#if defined(_M_X64)
            mG01NativeExceptionHandler = ::AddVectoredExceptionHandler(
                1, &ObserveG01NativeStowed);
#endif
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
#if defined(_M_X64)
        if (mG01NativeExceptionHandler)
            ::RemoveVectoredExceptionHandler(mG01NativeExceptionHandler);
#endif
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
