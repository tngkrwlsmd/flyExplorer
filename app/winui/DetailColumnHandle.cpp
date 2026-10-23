#include "pch.h"
#include "DetailColumnHandle.h"
#include <winrt/Microsoft.UI.Input.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <string>
#if __has_include("DetailColumnHandle.g.cpp")
#include "DetailColumnHandle.g.cpp"
#endif

namespace winrt::FlyExplorer::implementation {
DetailColumnHandle::DetailColumnHandle() {
    // Normal resize cursor and drag behavior remain unchanged. This opt-in
    // instrumentation exposes WinUI pointer delivery through UI Automation.
    mL08Diagnostic = GetEnvironmentVariableW(
        L"FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC", nullptr, 0) > 0;
    Loaded([this](auto const&, auto const&) {
        ProtectedCursor(Microsoft::UI::Input::InputSystemCursor::Create(
            Microsoft::UI::Input::InputSystemCursorShape::SizeWestEast));
        if (mL08Diagnostic) PublishL08PointerState(L"loaded");
    });
    if (mL08Diagnostic) {
        PointerEntered([this](auto const&, auto const&) {
            ++mL08PointerEntered;
            PublishL08PointerState(L"enter");
        });
        PointerExited([this](auto const&, auto const&) {
            ++mL08PointerExited;
            PublishL08PointerState(L"exit");
        });
    }
}

void DetailColumnHandle::PublishL08PointerState(wchar_t const* stage) {
    // Native UIA HelpText is read by the existing owned-GUI mouse oracle.
    // Do not reinterpret the configured cursor as the actual OS HCURSOR.
    std::wstring value = L"L08_";
    value += stage;
    value += L" ENTER=";
    value += std::to_wstring(mL08PointerEntered);
    value += L" EXIT=";
    value += std::to_wstring(mL08PointerExited);
    value += L" CURSOR_SET=";
    value += ProtectedCursor() ? L"1" : L"0";
    auto self = get_strong().as<Microsoft::UI::Xaml::DependencyObject>();
    Microsoft::UI::Xaml::Automation::AutomationProperties::SetHelpText(
        self, winrt::hstring(value.c_str()));
}
}
