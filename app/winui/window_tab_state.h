#pragma once
#include "../../src/base/explorer_ui_state.h"
#include "file_list_state.h"
#include <array>
#include <cstdint>

namespace fxfile::previewtabs {
struct WindowTabState final {
    static constexpr std::uint64_t kRouteStride=(std::uint64_t{1}<<32);
    explicit WindowTabState(std::uint64_t id=0):identity(id),model(id*kRouteStride){}
    std::uint64_t identity=0;
    fxfile::explorerui::Model model;
    std::array<fxfile::previewlist::PaneState,2> fileLists{};
    std::uint32_t splitPermille=500;
    bool fileInfoPaneVisible=false; // WindowTab-local, opt-in, not session persisted.
};
} // namespace fxfile::previewtabs
