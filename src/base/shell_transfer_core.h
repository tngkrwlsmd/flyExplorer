// M2.2: MFC-/WinRT-independent, bounded Windows Shell file transfers.
// Run execute() on a dedicated COM STA worker, never on the WinUI thread.
#pragma once
#ifndef FLY_SHELL_TRANSFER_CORE_H
#define FLY_SHELL_TRANSFER_CORE_H
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
namespace fxfile::shelltransfer {
inline constexpr std::size_t kMaxItems=1024;
inline constexpr std::size_t kMaxSourcePathUnits=1024*1024;
enum class Kind { Copy, Move, Recycle };
enum class Collision { Reject, KeepBoth };
// Copy/Move accept ordinary local fixed and removable volumes.
// Recycle intentionally stays fixed-drive-only until separately certified.
bool supportsDriveType(Kind kind,UINT driveType) noexcept;
struct Request {
 Kind kind=Kind::Copy;
 Collision collision=Collision::Reject;
 std::wstring sourceParent; // original accepted *local* filesystem pane path
 std::wstring destination;  // exact other *local* pane path; empty for recycle
 std::vector<std::wstring> sources; // native full paths, direct children only
 bool recycleConfirmed=false; // MUST be explicit user consent
};
struct Report {
 DWORD error=ERROR_INVALID_PARAMETER;
 bool aborted=false;
 std::vector<std::wstring> collisions;
 std::uint32_t queued=0;
};
struct Progress {
 std::atomic_uint32_t percent{0};
 std::atomic_bool cancel{false};
};
Report validate(Request const& task) noexcept; // read-only preflight
Report execute(Request const& task,Progress& progress) noexcept; // STA only
}
#endif
