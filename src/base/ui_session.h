// M2.3/v7 private, opt-in saved WinUI session. No legacy MFC config read/write.
#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile::uisession {
struct PaneTab {
 std::wstring path;
 std::vector<std::wstring> back,forward;
 std::uint32_t sort=0; // v4: folder-tab sort; old formats inherit pane sort.
};
struct PaneState {
 std::vector<PaneTab> tabs;
 std::uint32_t selected=0,sort=0,view=0,nameColumnWidth=168;
 // F01 view-only flags belong to each WindowTab/pane, not global Explorer.
 bool showSelectionCheckboxes=false,compactRows=false;
 bool showFileExtensions=true,showHiddenItems=false;
};
struct WindowTab {
 bool split=true;
 std::array<PaneState,2> panes;
 std::uint32_t splitPermille=500,activeSide=0;
};
struct Session {
 // Legacy schema=1 fields are retained so old callers/tests and old private
 // files remain readable. WindowTabs save as v4; v1/v2/v3 still load.
 bool split=true;
 std::array<std::vector<std::wstring>,2> paths;
 std::array<std::uint32_t,2> selected{{0,0}},sort{{0,0}};
 std::uint32_t width=1160,height=760,splitPermille=500,activeSide=0;
 std::vector<WindowTab> windowTabs;
 std::uint32_t activeWindow=0;
};
std::wstring privatePath();
bool valid(Session const&) noexcept;
bool save(Session const&) noexcept;
bool load(Session&) noexcept;
bool clear() noexcept;
}
