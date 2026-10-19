#include "pch.h"
#include "DetailColumnHandle.h"
#include <winrt/Microsoft.UI.Input.h>
#if __has_include("DetailColumnHandle.g.cpp")
#include "DetailColumnHandle.g.cpp"
#endif

namespace winrt::FlyExplorer::implementation {
DetailColumnHandle::DetailColumnHandle() {
    // Set the public cursor after loading, before pointer hit-testing.
    // WinUI owns entry/exit; the root handler still owns the actual resize.
    Loaded([this](auto const&,auto const&){
        ProtectedCursor(Microsoft::UI::Input::InputSystemCursor::Create(
            Microsoft::UI::Input::InputSystemCursorShape::SizeWestEast));
    });
}
}
