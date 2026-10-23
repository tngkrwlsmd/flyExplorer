#pragma once
#include "DetailColumnHandle.g.h"

namespace winrt::FlyExplorer::implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle> {
    DetailColumnHandle();

private:
    // The test-only UIA diagnostics are gated by the owned GUI fixture.
    // They must not affect ordinary accessibility properties or cursor input.
    void PublishCursorDiagnostic();
    bool mCursorDiagnosticEnabled=false;
    bool mCursorDiagnosticLoaded=false;
    unsigned mCursorDiagnosticEntered=0;
    unsigned mCursorDiagnosticExited=0;
};
}
namespace winrt::FlyExplorer::factory_implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle,implementation::DetailColumnHandle> {};
}
