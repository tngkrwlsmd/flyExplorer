#include "pch.h"
#include "DetailColumnHandle.h"
#include <winrt/Microsoft.UI.Input.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#if __has_include("DetailColumnHandle.g.cpp")
#include "DetailColumnHandle.g.cpp"
#endif

namespace winrt::FlyExplorer::implementation {
void DetailColumnHandle::PublishCursorDiagnostic() {
    if(!mCursorDiagnosticEnabled)return;
    // Expose only numeric, test-owned evidence through the existing UIA peer.
    // The property remains untouched for normal users and screen readers.
    const auto value=std::wstring(L"L08_LOAD=")+
        std::to_wstring(mCursorDiagnosticLoaded?1:0)+L" ENTER="+
        std::to_wstring(mCursorDiagnosticEntered)+L" EXIT="+
        std::to_wstring(mCursorDiagnosticExited)+L" CURSOR="+
        std::to_wstring(ProtectedCursor()?1:0);
    Microsoft::UI::Xaml::Automation::AutomationProperties::SetHelpText(
        this->as<Microsoft::UI::Xaml::DependencyObject>(),
        winrt::hstring(value.c_str()));
}

DetailColumnHandle::DetailColumnHandle() {
    mCursorDiagnosticEnabled=
        ::GetEnvironmentVariableW(
            L"FLYEXPLORER_COLUMN_RESIZE_DIAGNOSTIC",nullptr,0)>0;
    if(mCursorDiagnosticEnabled){
        PointerEntered([this](auto const&,auto const&){
            ++mCursorDiagnosticEntered;
            PublishCursorDiagnostic();
        });
        PointerExited([this](auto const&,auto const&){
            ++mCursorDiagnosticExited;
            PublishCursorDiagnostic();
        });
    }
    // Keep the existing cursor behavior, with no event-time reset.
    Loaded([this](auto const&,auto const&){
        ProtectedCursor(Microsoft::UI::Input::InputSystemCursor::Create(
            Microsoft::UI::Input::InputSystemCursorShape::SizeWestEast));
        if(mCursorDiagnosticEnabled){
            mCursorDiagnosticLoaded=true;
            PublishCursorDiagnostic();
        }
    });
}
}
