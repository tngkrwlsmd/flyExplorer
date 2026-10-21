#pragma once
#include "../../src/base/explorer_ui_state.h"
#include "file_list_state.h"
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace fxfile::previewtabs {
struct WindowTabState final {
    static constexpr std::uint64_t kRouteStride=(std::uint64_t{1}<<32);
    explicit WindowTabState(std::uint64_t id=0):identity(id),model(id*kRouteStride){}
    std::uint64_t identity=0;
    fxfile::explorerui::Model model;
    std::array<fxfile::previewlist::PaneState,2> fileLists{};
    // Active folder tab lives in fileLists; other folder tabs retain their own sort.
    std::array<std::vector<int>,2> tabSortModes{{std::vector<int>{0},std::vector<int>{0}}};
    std::uint32_t splitPermille=500;
    bool fileInfoPaneVisible=false; // WindowTab-local, opt-in, not session persisted.
    // Runtime-only failure feedback belongs to its originating WindowTab,
    // not MainWindow's global status bar or persistent session format.
    std::wstring transferFailureNotice{};
};
} // namespace fxfile::previewtabs
