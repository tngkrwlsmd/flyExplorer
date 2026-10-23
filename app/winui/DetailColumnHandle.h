#pragma once
#include "DetailColumnHandle.g.h"

namespace winrt::FlyExplorer::implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle> {
    DetailColumnHandle();

private:
    // L08 owned-GUI diagnostics only: never alter normal cursor/resize state.
    void PublishL08PointerState(wchar_t const* stage);
    bool mL08Diagnostic = false;
    unsigned mL08PointerEntered = 0;
    unsigned mL08PointerExited = 0;
};
}
namespace winrt::FlyExplorer::factory_implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle,implementation::DetailColumnHandle> {};
}
