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
inline constexpr std::size_t kMaxProviderParsingUnits=4096;
enum class Kind { Copy, Move, Recycle };
enum class Collision { Reject, KeepBoth };
enum class SourceMode { Filesystem, ShellProvider };
// Copy/Move accept fixed, removable and Windows network filesystem roots,
// including ordinary UNC shares. Recycle remains local fixed/removable only,
// requires explicit confirmation and uses recycle-only Shell flags.
bool supportsDriveType(Kind kind,UINT driveType) noexcept;
// Pure lexical root extraction used before GetDriveTypeW. Accepts ordinary
// X:\ and \\server\share roots, rejects extended/device namespaces.
bool transferDriveRoot(std::wstring const& path,std::wstring& root) noexcept;
struct Request {
 Kind kind=Kind::Copy;
 Collision collision=Collision::Reject;
 SourceMode sourceMode=SourceMode::Filesystem;
 // Filesystem mode: original accepted pane path. ShellProvider mode:
 // accepted snapshot's desktop-absolute parent parsing name.
 std::wstring sourceParent;
 // Copy/Move destination is always a validated filesystem folder.
 std::wstring destination;
 // Filesystem mode: native full paths. ShellProvider mode: desktop-absolute
 // Shell parsing names. Both remain bounded and direct-child-only.
 std::vector<std::wstring> sources;
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
// App-side bounded process boundary for Copy/Move. Resolves the exact helper
// staged beside flyExplorer, streams progress and kills only that owned child
// on cancellation/host teardown. Recycle intentionally stays on execute().
Report executeIsolated(Request const& task,Progress& progress) noexcept;
// Helper-only stdin/stdout entrypoint used by FlyShellIsolationHelper.exe.
int runIsolatedHelper(HANDLE input,HANDLE output) noexcept;
}
#endif
