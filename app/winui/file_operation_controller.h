#pragma once
#include "../../src/base/shell_transfer_core.h"
#include "../../src/base/file_command_core.h"
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace fxfile::previewops {

class FileOperationController final {
public:
    struct Context final {
        // Prevent an async result from targeting a different top-level
        // workspace even if its active pane, route and folder match.
        std::uint64_t windowTabIdentity=0;
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::wstring visibleFolder;
        std::wstring visibleShellFolder;
    };

    enum class StartStatus {
        Started,
        Busy,
        NeedsRecycleConfirmation,
        InvalidVisibleContext,
        StaleConfirmation,
        Cancelled,
        AllSkipped,
        ThreadStartFailed
    };

    enum class TransferDisposition {
        Ignored,
        StaleContext,
        NeedsCollisionConfirmation,
        Failed,
        Succeeded
    };

    enum class CommandDisposition {
        Ignored,
        StaleContext,
        Failed,
        Succeeded
    };

    struct TransferCompletion final {
        std::uint64_t ticket=0;
        Context context{};
        fxfile::shelltransfer::Request request{};
        fxfile::shelltransfer::Report report{};
        std::size_t skippedCollisions=0; // exact preflight-only skip count
        std::vector<std::wstring> touchedFolders{};
    };

    struct FileCommandCompletion final {
        std::uint64_t ticket=0;
        Context context{};
        fxfile::filecommand::Kind kind=fxfile::filecommand::Kind::CreateFolder;
        fxfile::filecommand::Result result{};
        // R07 phase 1: only a successful single-item Rename retains its
        // original path for a future verified receipt. NOT undo authority.
        std::wstring originalRenameSource{};
    };

    // R07-6: one accepted, exact-context rename observation candidate.
    // This value cannot authorize an Undo, a file mutation or persistence.
    struct RenameRestoreCandidate final {
        std::uint64_t ticket=0;
        Context context{};
        std::wstring originalPath{};
        fxfile::filecommand::Result renamed{};
    };

    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using TransferCallback=std::function<void(TransferCompletion)>;
    using FileCommandCallback=std::function<void(FileCommandCompletion)>;

    FileOperationController();
    ~FileOperationController();

    bool busy() const noexcept;
    bool cancellable() const noexcept;
    std::shared_ptr<fxfile::shelltransfer::Progress> progress() const noexcept;
    void cancel() noexcept;
    void prepareForClose() noexcept;
    // A dialog must carry the identity of the exact request it displays.
    // Zero means no live pending confirmation.
    std::uint64_t pendingConfirmationToken() const noexcept;

    StartStatus requestTransfer(
        fxfile::shelltransfer::Request request,Context context,
        Post post,TransferCallback completion);
    StartStatus confirmRecycle(
        bool approved,std::uint64_t expectedToken,Context liveContext,Post post,
        TransferCallback completion);
    StartStatus confirmCollision(
        bool approved,std::uint64_t expectedToken,Context liveContext,Post post,
        TransferCallback completion);
    // A preflight-only choice for ordinary filesystem Copy/Move: omit
    // precisely the destination names already reported as collisions.
    // No filesystem/Shell I/O occurs on the UI thread.
    StartStatus skipCollisions(
        std::uint64_t expectedToken,Context liveContext,Post post,
        TransferCallback completion,std::size_t& skipped);
    TransferDisposition acceptTransfer(
        TransferCompletion const& completion,Context const& liveContext);

    StartStatus startFileCommand(
        fxfile::filecommand::Request request,Context context,
        Post post,FileCommandCallback completion);
    CommandDisposition acceptFileCommand(
        FileCommandCompletion const& completion,Context const& liveContext);

    // R07-7: retrieve the owner-matched candidate at most once.
    // Removes it under the controller lock; NOT an Undo/restore capability.
    // It is not a filesystem check and does not reserve the original name.
    std::optional<RenameRestoreCandidate> takeRenameRestoreCandidate(
        Context const& liveContext);

    // R07-14: one last, single-use identity check of the already-taken
    // candidate at the proposed dispatch boundary. Always retires the
    // pending claim, even on mismatch. NO file I/O and NO restore authority:
    // the actual native operation is not connected to this method.
    bool recheckAndRetireRenameRestoreCandidate(
        RenameRestoreCandidate const& taken,Context const& liveContext) noexcept;

private:
    struct SharedState;
    struct PendingTransfer;
    std::shared_ptr<SharedState> state_;

    static bool sameContext(Context const&,Context const&) noexcept;
    static bool visibleForTransfer(
        fxfile::shelltransfer::Request const&,Context const&) noexcept;
    StartStatus launchTransfer(
        fxfile::shelltransfer::Request request,Context context,
        Post post,TransferCallback completion,
        std::size_t skippedCollisions=0);
};

} // namespace fxfile::previewops
