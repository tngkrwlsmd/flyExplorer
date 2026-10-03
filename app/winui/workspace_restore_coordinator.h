#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#include <vector>

namespace fxfile::previewrestore {

class WorkspaceRestoreCoordinator final {
public:
    struct Task final {
        std::size_t tab=0;
        std::wstring path{};
    };

    void reset() noexcept;
    void reset(int side) noexcept;
    void begin(
        int side,std::vector<Task> tasks,
        std::uint64_t initialRequest);
    bool settle(int side,std::uint64_t request) noexcept;
    std::optional<Task> takeNext(
        int side,bool paneBusy,std::size_t tabCount);
    bool track(int side,std::uint64_t request) noexcept;

    bool active(int side) const noexcept;
    std::size_t queued(int side) const noexcept;

private:
    struct Lane final {
        std::deque<Task> tasks{};
        std::uint64_t awaitedRequest=0;
    };

    static bool validSide(int side) noexcept;
    std::array<Lane,2> lanes_{};
};

} // namespace fxfile::previewrestore
