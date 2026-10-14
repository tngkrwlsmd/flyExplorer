#pragma once
// F03 read-only byte reader for an ALREADY OPENED, caller-owned file handle.
// This library never opens paths, spawns threads or executes preview handlers.
// Call ONLY inside a supervised, cancellable worker process; synchronous
// ReadFile can block and MUST NOT execute on a WinUI/XAML thread.
#ifndef FXFILE_FILE_PREVIEW_READER_H
#define FXFILE_FILE_PREVIEW_READER_H

#include "file_preview_policy.h"
#include <Windows.h>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <string_view>
#include <vector>

namespace fxfile::previewread {

enum class Status : std::uint8_t {
    Success, InvalidRequest, InvalidHandle, UnsafeHandle, ChangedFile,
    TooLarge, Cancelled, Deadline, ShortRead, InvalidText, IoError
};

struct Result final {
    Status status=Status::InvalidRequest;
    previewpolicy::Kind kind=previewpolicy::Kind::None;
    std::vector<std::uint8_t> bytes{};
    bool ok() const noexcept { return status==Status::Success; }
};

// Ownership: caller retains and closes HANDLE; worker must NOT share its file
// pointer while reading. A valid non-overlapped, synchronous FILE_READ_DATA
// handle is required. This function DOES NOT authorize opening a path or prove
// ancestor traversal was reparse-free. An independent safe-open stage must do
// that before this handle is handed to an isolated worker.
// If cancelled/changed/invalid, returns no user bytes.
Result readVerifiedHandle(
    HANDLE file, std::wstring_view expectedAbsolutePath,
    previewpolicy::Kind kind, std::uint64_t expectedBytes,
    std::atomic_bool const& cancelled,
    std::chrono::steady_clock::time_point deadline) noexcept;

} // namespace fxfile::previewread
#endif
