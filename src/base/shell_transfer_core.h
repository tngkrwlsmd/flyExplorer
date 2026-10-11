// M2.2: MFC-/WinRT-independent, bounded Windows Shell file transfers.
// Run execute() on a dedicated COM STA worker, never on the WinUI thread.
#pragma once
#ifndef FLY_SHELL_TRANSFER_CORE_H
#define FLY_SHELL_TRANSFER_CORE_H
#include <windows.h>
#include <atomic>
#include <array>
#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>
namespace fxfile::shelltransfer {
inline constexpr std::size_t kMaxItems=1024;
inline constexpr std::size_t kMaxSourcePathUnits=1024*1024;
inline constexpr std::size_t kMaxProviderParsingUnits=4096;
inline constexpr std::size_t kMaxProviderPidlBytes=32768;
inline constexpr std::size_t kMaxProviderPidlBytesTotal=1024*1024;
enum class Kind { Copy, Move, Recycle };
enum class Collision { Reject, KeepBoth };
enum class SourceMode { Filesystem, ShellProvider };
enum class DestinationMode { Filesystem, ShellProvider };
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
 DestinationMode destinationMode=DestinationMode::Filesystem;
 // Filesystem mode: original accepted pane path. ShellProvider mode:
 // accepted snapshot's desktop-absolute parent parsing name.
 std::wstring sourceParent;
 // Copy/Move destination is always a validated filesystem folder.
 std::wstring destination;
 // Filesystem mode: native full paths. ShellProvider mode: desktop-absolute
 // Shell parsing names. Both remain bounded and direct-child-only.
 std::vector<std::wstring> sources;
 // ShellProvider mode additionally carries the exact accepted snapshot PIDLs.
 // These are value bytes only; no COM interface crosses the process boundary.
 std::vector<unsigned char> sourceParentPidl;
 std::vector<std::vector<unsigned char>> sourcePidls;
 // Exact accepted destination PIDL. First Copy-in target: Pictures Library.
 std::vector<unsigned char> destinationPidl;
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
// Read-only file-object identity probe for an EXACT observed staged Copy path.
// This is NOT an ownership receipt or deletion authorization. A matching
// filename/file ID cannot prove which app/helper created the file.
struct StageFileIdentity {
 std::uint64_t volumeSerial=0;
 std::array<unsigned char,16> fileId{};
};
bool inspectStageFile(std::wstring const& exactPath,
                      StageFileIdentity& identity) noexcept;
bool sameStageFile(StageFileIdentity const& a,
                   StageFileIdentity const& b) noexcept;
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
