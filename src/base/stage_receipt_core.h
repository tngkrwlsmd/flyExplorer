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
// Caller must provide an already provisioned, access-controlled private
// receipt directory. Neither this primitive nor a valid receipt authorizes
// deleting, publishing or recovering a file.
bool writeStageReceipt(std::wstring const& exactReceiptPath,
                       std::wstring const& exactStagePath,
                       std::wstring const& targetLeaf) noexcept;
bool readStageReceipt(std::wstring const& exactReceiptPath,
                      StageOwnershipReceipt& receipt) noexcept;
bool receiptMatchesStage(StageOwnershipReceipt const& receipt) noexcept;
// Read-only snapshot of the EXACT PID and process creation time.
// Unknown (including PID reuse/access failure) is never equivalent to Exited.
// Even Exited does NOT confer authority to remove or publish a stage.
enum class ReceiptCreatorState { Unknown, Running, Exited };
ReceiptCreatorState inspectReceiptCreator(
    StageOwnershipReceipt const& receipt) noexcept;
}
#endif
