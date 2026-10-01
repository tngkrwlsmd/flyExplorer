#pragma once
#include "../../src/base/explorer_ui_state.h"
#include "file_list_state.h"
#include <array>
#include <cstdint>

namespace fxfile::previewtabs {
struct WindowTabState final {
    std::uint64_t identity=0;
    fxfile::explorerui::Model model{};
    std::array<fxfile::previewlist::PaneState,2> fileLists{};
    std::uint32_t splitPermille=500;
};
} // namespace fxfile::previewtabs
