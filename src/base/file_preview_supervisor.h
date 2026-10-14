#pragma once
// F03: synchronous isolated Preview IPC. Call ONLY from a background worker,
// never from the WinUI XAML/dispatcher thread. Does not decode or render data.
#ifndef FXFILE_PREVIEW_SUPERVISOR_H
#define FXFILE_PREVIEW_SUPERVISOR_H
#include "file_preview_policy.h"
#include "file_preview_worker_wire.h"
#include <atomic>
#include <cstdint>
#include <string_view>
#include <vector>

namespace fxfile::previewsupervisor {
enum class Status : std::uint8_t {
    Success, Rejected, LaunchFailed, ProtocolError, WorkerRejected,
    Cancelled, Deadline
};
struct Result final {
    Status status=Status::Rejected;
    previewpolicy::Kind kind=previewpolicy::Kind::None;
    std::vector<std::uint8_t> bytes;
    std::uint32_t workerStatus=0;
    bool ok() const noexcept {return status==Status::Success;}
};

// helperExe MUST be the exact application-sibling FlyShellIsolationHelper.exe.
// Only the caller/composition root can establish that trusted identity.
// The worker validates the actual opened file independently. A private
// Job Object closes/kills only this invocation's suspended-created child.
// Caller owns 'cancelled' for the entire synchronous call lifetime.
Result run(std::wstring_view helperExe,
           previewpolicy::Candidate const& candidate,
           std::atomic_bool const& cancelled,
           std::uint32_t timeoutMs=previewwire::kDeadlineMs+800) noexcept;
} // namespace fxfile::previewsupervisor
#endif
