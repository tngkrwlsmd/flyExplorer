#pragma once
#include "../../src/base/shell_transfer_core.h"
#include "../../src/base/file_command_core.h"
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
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

    StartStatus requestTransfer(
        fxfile::shelltransfer::Request request,Context context,
        Post post,TransferCallback completion);
    StartStatus confirmRecycle(
        bool approved,Context liveContext,Post post,
        TransferCallback completion);
    StartStatus confirmCollision(
        bool approved,Context liveContext,Post post,
        TransferCallback completion);
    // A preflight-only choice for ordinary filesystem Copy/Move: omit
    // precisely the destination names already reported as collisions.
    // No filesystem/Shell I/O occurs on the UI thread.
    StartStatus skipCollisions(
        Context liveContext,Post post,TransferCallback completion,
        std::size_t& skipped);
    TransferDisposition acceptTransfer(
        TransferCompletion const& completion,Context const& liveContext);

    StartStatus startFileCommand(
        fxfile::filecommand::Request request,Context context,
        Post post,FileCommandCallback completion);
    CommandDisposition acceptFileCommand(
        FileCommandCompletion const& completion,Context const& liveContext);

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
