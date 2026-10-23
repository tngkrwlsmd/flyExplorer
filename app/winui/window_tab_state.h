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
    // PX11: each WindowTab has independent left/right pane-local view,
    // display and column state. Group caches remain transient per route/tab.
    std::array<fxfile::previewlist::PaneState,2> fileLists{};
    // The active PaneTab sort is fileLists[side].sortMode; inactive PaneTab
    // sorts remain here until the next folder-tab transition or v4 save.
    std::array<std::vector<int>,2> tabSortModes{{std::vector<int>{0},std::vector<int>{0}}};
    std::uint32_t splitPermille=500;
    bool fileInfoPaneVisible=false; // WindowTab-local, opt-in, not session persisted.
    // Runtime-only file-operation feedback belongs to its originating WindowTab,
    // not MainWindow's global status bar or persistent session format.
    std::wstring fileOperationNotice{};
};
} // namespace fxfile::previewtabs
