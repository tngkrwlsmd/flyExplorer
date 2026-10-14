#pragma once
// F03 worker-only conservative path opening. Never call from a XAML thread.
// Holds every ancestor directory HANDLE without FILE_SHARE_WRITE/DELETE until
// after its file HANDLE has been fully read. This is not an OS sandbox and
// not a substitute for process-level timeout/termination/route identity.
#ifndef FXFILE_PREVIEW_SAFE_OPEN_H
#define FXFILE_PREVIEW_SAFE_OPEN_H
#include "file_preview_policy.h"
#include <Windows.h>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <string_view>
#include <vector>

namespace fxfile::previewsafe {

inline constexpr std::size_t kMaxAncestors=64;

enum class Status : std::uint8_t {
    Accepted, RejectedCandidate, InvalidPath, NonLocal, Reparse,
    NotRegular, Changed, IoError, Cancelled, Deadline, TooDeep
};

class UniqueHandle final {
public:
    UniqueHandle() noexcept = default;
    explicit UniqueHandle(HANDLE h) noexcept : h_(h) {}
    ~UniqueHandle() noexcept { reset(); }
    UniqueHandle(UniqueHandle const&) = delete;
    UniqueHandle& operator=(UniqueHandle const&) = delete;
    UniqueHandle(UniqueHandle&& other) noexcept : h_(other.release()) {}
    UniqueHandle& operator=(UniqueHandle&& other) noexcept {
        if(this!=&other)reset(other.release());
        return *this;
    }
    HANDLE get() const noexcept { return h_; }
    explicit operator bool() const noexcept {
        return h_!=INVALID_HANDLE_VALUE && h_!=nullptr;
    }
    HANDLE release() noexcept {
        HANDLE out=h_;
        h_=INVALID_HANDLE_VALUE;
        return out;
    }
    void reset(HANDLE next=INVALID_HANDLE_VALUE) noexcept {
        if(*this)::CloseHandle(h_);
        h_=next;
    }
private:
    HANDLE h_=INVALID_HANDLE_VALUE;
};

struct Result final {
    Status status=Status::RejectedCandidate;
    previewpolicy::Kind kind=previewpolicy::Kind::None;
    std::uint64_t knownBytes=0;
    UniqueHandle file;
    // Lifetime invariant: KEEP these guards open while readVerifiedHandle()
    // consumes file, then release all guards and the file together.
    std::vector<UniqueHandle> lockedAncestors{};
    bool accepted() const noexcept {
        return status==Status::Accepted && static_cast<bool>(file);
    }
};

// Candidate flags are only a cheap admission screen, NEVER trust for opening.
// This API is NOT called from WinUI and never decodes content. The worker
// must enforce process timeouts and stale request filtering separately.
// Opened file and ancestor guards are RAII returned only on full success.
Result openLocalRegular(
    previewpolicy::Candidate const& candidate,
    std::atomic_bool const& cancelled,
    std::chrono::steady_clock::time_point deadline) noexcept;

} // namespace fxfile::previewsafe
#endif
