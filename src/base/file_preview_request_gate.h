#pragma once
// F03 UI-independent request-identity gate. No WinUI types or global state.
// One owner per active pane; token invalidation is cooperative and also makes
// any already-completed result stale before it can reach presentation.
#ifndef FXFILE_PREVIEW_REQUEST_GATE_H
#define FXFILE_PREVIEW_REQUEST_GATE_H
#include <atomic>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <utility>

namespace fxfile::previewgate {
struct Key final {
    std::uint64_t window=0;
    std::uint64_t pane=0;
    std::uint64_t tab=0;
    std::uint64_t generation=0;
    std::wstring selectedIdentity;
    bool operator==(Key const&) const = default;
};
struct Ticket final {
    Key key;
    std::shared_ptr<std::atomic_bool> cancel;
};
class Gate final {
public:
    Ticket begin(Key key) {
        std::lock_guard lock(mutex_);
        if(current_.cancel)current_.cancel->store(true);
        current_={std::move(key),std::make_shared<std::atomic_bool>(false)};
        return current_;
    }
    void clear() noexcept {
        std::lock_guard lock(mutex_);
        if(current_.cancel)current_.cancel->store(true);
        current_={};
    }
    bool current(Ticket const& ticket) const noexcept {
        std::lock_guard lock(mutex_);
        return ticket.cancel && current_.cancel==ticket.cancel &&
            !ticket.cancel->load() && current_.key==ticket.key;
    }
    ~Gate() {clear();}
    Gate()=default;
    Gate(Gate const&)=delete;
    Gate& operator=(Gate const&)=delete;
private:
    mutable std::mutex mutex_;
    Ticket current_;
};
} // namespace fxfile::previewgate
#endif
