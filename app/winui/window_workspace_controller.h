#pragma once
#include "window_tab_state.h"
#include "../../src/base/explorer_ui_state.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace fxfile::previewtabs {

class WindowWorkspaceController final {
public:
    static constexpr std::size_t kMaxWindowTabs=10;

    WindowWorkspaceController();

    WindowTabState& active();
    WindowTabState const& active() const;
    WindowTabState& state(std::size_t index);
    WindowTabState const& state(std::size_t index) const;
    std::vector<WindowTabState> const& states() const noexcept;

    std::size_t count() const noexcept;
    std::size_t activeIndex() const noexcept;
    bool isActive(std::size_t index) const noexcept;
    bool canCreate() const noexcept;

    bool create();
    bool activate(std::size_t index) noexcept;
    bool close(std::size_t index);
    fxfile::explorerui::Change dispatch(
        fxfile::explorerui::Command command,int side=0,std::size_t tab=0);
    bool resetActive(
        bool split,std::array<std::size_t,2> counts,
        std::array<std::size_t,2> selected);
    bool replace(std::vector<WindowTabState>&& states,std::size_t activeIndex);

private:
    std::vector<WindowTabState> states_;
    std::size_t active_=0;
    std::uint64_t nextIdentity_=1;
};

} // namespace fxfile::previewtabs
