// M2.1 initial safe local-filesystem command boundary (no MFC/WinRT).
#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <string>
namespace fxfile::filecommand {
enum class Kind { CreateFolder, RenameSelected, CreateTextFile, CreateMarkdownFile, CreateShortcut };
struct Request {
 Kind kind=Kind::CreateFolder;
 std::wstring parent; // exact accepted filesystem folder from isolated helper
 std::wstring source; // full selected native filesystem parsing path for rename
 std::wstring name;   // single leaf only, never a path or virtual Shell GUID
};
// R07-2: read-only, single local regular-file rename evidence.
// Never treat this snapshot as permission to undo/redo or overwrite a path.
struct RenameEvidence {
    bool verified=false;
    std::uint64_t volumeSerial=0;
    std::array<unsigned char,16> fileId{};
    std::uint64_t fileSize=0;
    std::int64_t lastWriteTime=0;
};
struct Result {
    DWORD error=ERROR_INVALID_PARAMETER;
    std::wstring target;
    RenameEvidence renameEvidence{};
};
// R07-3 is a momentary, read-only observation, NOT undo authorization.
// No target handle is retained: checks can become stale immediately.
enum class RenameRestoreObservation {
    UnverifiedReceipt,
    UnsafePaths,
    OriginalOccupiedOrUnknown,
    TargetChangedOrUnavailable,
    MatchingSnapshotOnly
};
RenameRestoreObservation inspectRenameRestore(
    std::wstring const& originalPath,Result const& renamed) noexcept;

// R07-4: temporary read-attribute handle with no WRITE/DELETE sharing.
// Non-copyable, never stores Undo authority, and does not reserve a name.
// A MatchingSnapshotOnly response cannot authorize a subsequent mutation.
class RenameTargetLease final {
public:
    RenameTargetLease() noexcept = default;
    ~RenameTargetLease() noexcept;
    RenameTargetLease(RenameTargetLease const&) = delete;
    RenameTargetLease& operator=(RenameTargetLease const&) = delete;
    RenameRestoreObservation begin(
        std::wstring const& originalPath,Result const& renamed) noexcept;
    RenameRestoreObservation recheck() const noexcept;
    void reset() noexcept;
private:
    HANDLE handle_=INVALID_HANDLE_VALUE;
    HANDLE parentHandle_=INVALID_HANDLE_VALUE; // retain directory identity; not an Undo lock
    FILE_ID_INFO parentId_{}; // directory identity, not filename reservation
    std::wstring originalPath_;
    std::wstring targetPath_;
    RenameEvidence expected_{};
};
// R07-8: isolated native primitive, NOT connected to the UI or an Undo
// command. Caller must independently verify a live one-shot owner ticket.
// Failed native calls may leave uncertain state; only CommittedVerified
// confirms the observed postcondition. Never overwrite an occupied name.
enum class RenameRestoreWriteStatus {
    RejectedReceipt,
    RejectedPaths,
    OriginalOccupiedOrUnknown,
    TargetChangedOrUnavailable,
    AccessUnavailable,
    NativeCallFailedUnknownState,
    CommittedUnverified,
    CommittedVerified
};
struct RenameRestoreWriteResult {
    RenameRestoreWriteStatus status=RenameRestoreWriteStatus::RejectedReceipt;
    DWORD error=ERROR_INVALID_PARAMETER;
    bool nativeCallAttempted=false;
};
RenameRestoreWriteResult restoreRenameNoReplace(
    std::wstring const& originalPath,Result const& renamed) noexcept;

bool validLeaf(std::wstring const& name) noexcept;
bool validTextDocumentLeaf(std::wstring const& name) noexcept;
bool validMarkdownDocumentLeaf(std::wstring const& name) noexcept;
bool validShortcutLeaf(std::wstring const& name) noexcept;
Result execute(Request const& request) noexcept; // invoke off the UI thread
}
