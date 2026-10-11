// Exact-file, durable receipt primitive. No stage scanning or cleanup.
#pragma once
#ifndef FLY_STAGE_RECEIPT_CORE_H
#define FLY_STAGE_RECEIPT_CORE_H
#include "shell_transfer_core.h"
namespace fxfile::shelltransfer {
struct StageOwnershipReceipt {
 std::wstring stagePath;
 std::wstring targetLeaf;
 StageFileIdentity stageIdentity{};
 DWORD creatorPid=0;
 std::uint64_t creatorStartTime=0;
};
// Creates ONLY an absent, exact fixed-drive directory with a protected
// owner-only DACL. Does not change ACLs on any existing folder or file.
// Caller must choose a trusted test-owned/app-owned parent; never scan.
bool createPrivateStageReceiptDirectory(
    std::wstring const& exactDirectory) noexcept;
// Read-only strict DACL/owner gate, also enforced on receipt read/write.
// This mitigates other-user access, not hostile code running as same user.
bool isPrivateStageReceiptDirectory(
    std::wstring const& exactDirectory) noexcept;
// Caller must provide an already provisioned, access-controlled private
// receipt directory. Neither this primitive nor a valid receipt authorizes
// deleting, publishing or recovering a file.
bool writeStageReceipt(std::wstring const& exactReceiptPath,
                       std::wstring const& exactStagePath,
                       std::wstring const& targetLeaf) noexcept;
// Bind the actual CopyFileEx destination HANDLE to the exact stage identity
// BEFORE writing, and re-check after the durable write. No close/mutation.
bool writeBoundStageReceipt(std::wstring const& exactReceiptPath,
                            std::wstring const& exactStagePath,
                            std::wstring const& targetLeaf,
                            HANDLE copyDestination) noexcept;
// Resolve a per-user Windows Known Folder location and provision only an
// absent owner-only protected directory; never reset an existing directory.
// A failure returns an empty directory (caller decides whether to opt in).
bool prepareUserStageReceiptDirectory(
    std::wstring& exactDirectory) noexcept;
bool readStageReceipt(std::wstring const& exactReceiptPath,
                      StageOwnershipReceipt& receipt) noexcept;
bool receiptMatchesStage(StageOwnershipReceipt const& receipt) noexcept;
// Immutable per-operation transition records next to the original receipt.
// Completion is written only after full CopyFileEx success and cancellation
// checks; publication is recorded only after a verified same-file rename.
// Both fail closed, use CREATE_NEW + write-through + flush, never overwrite.
bool markStageCopyCompleted(std::wstring const& exactReceiptPath) noexcept;
bool markStageCopyPublished(std::wstring const& exactReceiptPath) noexcept;
// Read-only explicit receipt-path inspection, including across new processes.
// Inconsistent also covers missing/changed target, incomplete marker, phase
// gaps, and other ambiguity. No state confers cleanup/restore permission.
enum class StageReceiptState {
 Invalid, CopyingOrInterrupted, CompletedOnStage,
 PublicationUnconfirmed, PublishedVerified, Inconsistent
};
StageReceiptState inspectStageReceiptState(
    std::wstring const& exactReceiptPath) noexcept;
// Read-only snapshot of the EXACT PID and process creation time.
// Unknown (including PID reuse/access failure) is never equivalent to Exited.
// Even Exited does NOT confer authority to remove or publish a stage.
enum class ReceiptCreatorState { Unknown, Running, Exited };
ReceiptCreatorState inspectReceiptCreator(
    StageOwnershipReceipt const& receipt) noexcept;
}
#endif
