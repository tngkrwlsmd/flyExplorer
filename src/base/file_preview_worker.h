#pragma once
// F03 one request per disposable helper process; not callable on WinUI STA.
// Read/write only anonymous inherited pipes. Never log or persist file bytes.
#ifndef FXFILE_PREVIEW_WORKER_H
#define FXFILE_PREVIEW_WORKER_H
#include <Windows.h>
#include <cstdint>

namespace fxfile::previewworker {
enum class Status : std::uint32_t {
    Success=0, InvalidRequest=1, UnsafePath=2, ReadRejected=3,
    IoError=4, Cancelled=5, Deadline=6, Internal=7
};
// Caller supervises process lifetime/kill-on-close Job and exact pipe limits.
// Returns zero when a complete validated response was emitted, not when a
// file preview succeeded. Nonzero means unusable/partial reply.
int runOne(HANDLE input,HANDLE output) noexcept;
} // namespace fxfile::previewworker
#endif
