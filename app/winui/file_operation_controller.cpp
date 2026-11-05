#if !defined(FLY_R07_OWNER_NATIVE_CONTRACT)
#include "pch.h"
#endif
#include "file_operation_controller.h"
#include <algorithm>
#include <atomic>
#include <filesystem>
#include <limits>
#include <mutex>
#include <optional>
#include <thread>
#include <utility>

namespace fxfile::previewops {

struct FileOperationController::PendingTransfer final {
    fxfile::shelltransfer::Request request{};
    Context context{};
    // Destination paths from the completed read-only preflight.
    std::vector<std::wstring> collisions{};
    // Keep earlier skip decisions when a reduced batch encounters
    // another destination collision during its fresh worker preflight.
    std::size_t skippedCollisions=0;
    // Unique to the confirmation being displayed, even in the same folder.
    std::uint64_t token=0;
};

struct FileOperationController::SharedState final {
    mutable std::mutex mutex;
    std::uint64_t epoch=0;
    std::uint64_t confirmationSerial=0;
    // R07-16: monotonic owner generation; saturation permanently disables
    // acceptance of further rename receipts instead of wrapping to an old one.
    std::uint64_t navigationGeneration=0;
    std::uint64_t fileCommandNavigationGeneration=0;
    bool busy=false;
    // R07-19: distinguish a native restore from a pending file command.
    // A duplicate completion with the old epoch must not be accepted.
    bool restoreInFlight=false;
    bool closing=false;
    std::shared_ptr<fxfile::shelltransfer::Progress> progress{};
    std::optional<PendingTransfer> pending{};
    // Never persisted or exposed as file mutation authority.
    std::optional<FileOperationController::RenameRestoreCandidate> renameCandidate{};
    // The original candidate is still erased by take(); this private copy
    // binds one subsequent identity recheck and is not an Undo capability.
    std::optional<FileOperationController::RenameRestoreCandidate> pendingRestoreCheck{};
};

FileOperationController::FileOperationController()
    : state_(std::make_shared<SharedState>())
{
}

FileOperationController::~FileOperationController()
{
    prepareForClose();
}

bool FileOperationController::sameContext(
    Context const& a,Context const& b) noexcept
{
    return a.windowTabIdentity==b.windowTabIdentity&&
           a.side==b.side&&a.tab==b.tab&&a.route==b.route&&
           a.visibleFolder==b.visibleFolder&&
           a.visibleShellFolder==b.visibleShellFolder;
}

bool FileOperationController::visibleForTransfer(
    fxfile::shelltransfer::Request const& request,
    Context const& context) noexcept
{
    if(context.side<0||context.side>1)return false;
    if(request.sourceMode==fxfile::shelltransfer::SourceMode::ShellProvider){
        if(!context.visibleShellFolder.empty()&&
           context.visibleShellFolder==request.sourceParent)return true;
    }else if(!context.visibleFolder.empty()&&
             context.visibleFolder==request.sourceParent)return true;
    return request.kind!=fxfile::shelltransfer::Kind::Recycle&&
           (request.destinationMode==
              fxfile::shelltransfer::DestinationMode::ShellProvider?
             !context.visibleShellFolder.empty()&&
             context.visibleShellFolder==request.destination:
             !context.visibleFolder.empty()&&
             context.visibleFolder==request.destination);
}

bool FileOperationController::busy() const noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->busy;
    }catch(...){return true;}
}

bool FileOperationController::cancellable() const noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->busy&&static_cast<bool>(state_->progress);
    }catch(...){return false;}
}

std::shared_ptr<fxfile::shelltransfer::Progress>
FileOperationController::progress() const noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->progress;
    }catch(...){return {};}
}

std::uint64_t FileOperationController::pendingConfirmationToken() const noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->closing||state_->busy||!state_->pending?
            0:state_->pending->token;
    }catch(...){return 0;}
}

void FileOperationController::cancel() noexcept
{
    auto current=progress();
    if(current)current->cancel.store(true);
}

void FileOperationController::invalidateRenameOwnerOnNavigation() noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->navigationGeneration<
           (std::numeric_limits<std::uint64_t>::max)())
            ++state_->navigationGeneration;
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        // Do not change the in-flight worker ticket or busy flag. Its
        // completion will be rejected if the generation changed.
    }catch(...){}
}

void FileOperationController::prepareForClose() noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        state_->closing=true;
        ++state_->epoch;
        if(state_->progress)state_->progress->cancel.store(true);
        state_->progress.reset();
        state_->pending.reset();
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        state_->busy=false;
    }catch(...){}
}

FileOperationController::StartStatus FileOperationController::requestTransfer(
    fxfile::shelltransfer::Request request,Context context,
    Post post,TransferCallback completion)
{
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!visibleForTransfer(request,context))
            return StartStatus::InvalidVisibleContext;
        // Any new accepted request supersedes the previous rename receipt,
        // including a transfer that first needs user confirmation.
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        if(request.kind==fxfile::shelltransfer::Kind::Recycle&&
           !request.recycleConfirmed){
            if(state_->confirmationSerial==
               (std::numeric_limits<std::uint64_t>::max)())
                return StartStatus::ThreadStartFailed;
            state_->pending=PendingTransfer{std::move(request),std::move(context)};
            state_->pending->token=++state_->confirmationSerial;
            return StartStatus::NeedsRecycleConfirmation;
        }
        state_->pending.reset();
    }
    return launchTransfer(
        std::move(request),std::move(context),
        std::move(post),std::move(completion));
}

FileOperationController::StartStatus FileOperationController::confirmRecycle(
    bool approved,std::uint64_t expectedToken,Context liveContext,
    Post post,TransferCallback completion)
{
    PendingTransfer pending{};
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!expectedToken||!state_->pending||
           state_->pending->token!=expectedToken||
           state_->pending->request.kind!=fxfile::shelltransfer::Kind::Recycle)
            return StartStatus::StaleConfirmation;
        pending=std::move(*state_->pending);
        state_->pending.reset();
    }
    if(!approved)return StartStatus::Cancelled;
    if(!sameContext(pending.context,liveContext))
        return StartStatus::StaleConfirmation;
    pending.request.recycleConfirmed=true;
    return launchTransfer(
        std::move(pending.request),std::move(pending.context),
        std::move(post),std::move(completion));
}

FileOperationController::StartStatus FileOperationController::confirmCollision(
    bool approved,std::uint64_t expectedToken,Context liveContext,
    Post post,TransferCallback completion)
{
    PendingTransfer pending{};
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!expectedToken||!state_->pending||
           state_->pending->token!=expectedToken||
           state_->pending->request.kind==fxfile::shelltransfer::Kind::Recycle)
            return StartStatus::StaleConfirmation;
        pending=std::move(*state_->pending);
        state_->pending.reset();
    }
    if(!approved)return StartStatus::Cancelled;
    if(!sameContext(pending.context,liveContext))
        return StartStatus::StaleConfirmation;
    pending.request.collision=fxfile::shelltransfer::Collision::KeepBoth;
    return launchTransfer(
        std::move(pending.request),std::move(pending.context),
        std::move(post),std::move(completion),pending.skippedCollisions);
}

FileOperationController::StartStatus
FileOperationController::skipCollisions(
    std::uint64_t expectedToken,Context liveContext,
    Post post,TransferCallback completion,std::size_t& skipped)
{
    skipped=0;
    PendingTransfer pending{};
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!expectedToken||!state_->pending||
           state_->pending->token!=expectedToken)
            return StartStatus::StaleConfirmation;
        auto const& request=state_->pending->request;
        if(request.kind==fxfile::shelltransfer::Kind::Recycle||
           request.sourceMode!=fxfile::shelltransfer::SourceMode::Filesystem||
           request.destinationMode!=fxfile::shelltransfer::DestinationMode::Filesystem||
           state_->pending->collisions.empty())
            return StartStatus::StaleConfirmation;
        pending=std::move(*state_->pending);
        state_->pending.reset();
    }
    if(!sameContext(pending.context,liveContext))
        return StartStatus::StaleConfirmation;

    // Only perform lexical matching against exactly the paths returned by
    // preflight. Never inspect or modify the filesystem on the UI thread.
    // launchTransfer's worker runs a fresh native validate() on the reduced
    // request, so races and new collisions still fail closed.
    try{
        std::vector<std::wstring> remaining;
        remaining.reserve(pending.request.sources.size());
        for(auto const& source:pending.request.sources){
            const auto destination=(
                std::filesystem::path(pending.request.destination)/
                std::filesystem::path(source).filename()).native();
            const bool collision=std::any_of(
                pending.collisions.begin(),pending.collisions.end(),
                [&](std::wstring const& path){
                    return ::CompareStringOrdinal(
                        destination.c_str(),-1,path.c_str(),-1,TRUE)==CSTR_EQUAL;
                });
            if(collision)++skipped;
            else remaining.push_back(source);
        }
        // Ambiguous collision mappings are not permission to copy an
        // unverified subset or silently overwrite an existing target.
        if(skipped!=pending.collisions.size()){
            skipped=0;
            return StartStatus::StaleConfirmation;
        }
        if(pending.skippedCollisions>
            fxfile::shelltransfer::kMaxItems-skipped){
            skipped=0;
            return StartStatus::StaleConfirmation;
        }
        const auto totalSkipped=pending.skippedCollisions+skipped;
        if(remaining.empty()){
            // The confirmation UI needs the total across every preflight
            // round, not only names skipped at the final prompt.
            skipped=totalSkipped;
            return StartStatus::AllSkipped;
        }
        pending.request.sources=std::move(remaining);
        return launchTransfer(std::move(pending.request),
                              std::move(pending.context),
                              std::move(post),std::move(completion),totalSkipped);
    }catch(...){
        skipped=0;
        return StartStatus::StaleConfirmation;
    }
}

FileOperationController::StartStatus FileOperationController::launchTransfer(
    fxfile::shelltransfer::Request request,Context context,
    Post post,TransferCallback completion,std::size_t skippedCollisions)
{
    if(!post||!completion)return StartStatus::ThreadStartFailed;
    auto progress=std::make_shared<fxfile::shelltransfer::Progress>();
    std::uint64_t ticket=0;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!visibleForTransfer(request,context))
            return StartStatus::InvalidVisibleContext;
        if(state_->epoch==(std::numeric_limits<std::uint64_t>::max)())
            return StartStatus::ThreadStartFailed;
        ticket=++state_->epoch;
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        state_->busy=true;
        state_->progress=progress;
    }

    std::vector<std::wstring> touched;
    if(request.sourceMode==fxfile::shelltransfer::SourceMode::Filesystem)
        touched.push_back(request.sourceParent);
    if(request.kind!=fxfile::shelltransfer::Kind::Recycle&&
       (request.sourceMode==fxfile::shelltransfer::SourceMode::ShellProvider||
        request.destination!=request.sourceParent))
        touched.push_back(request.destination);

    auto shared=state_;
    try{
        std::thread([
            shared,progress,ticket,context=std::move(context),
            request=std::move(request),touched=std::move(touched),
            post=std::move(post),completion=std::move(completion),
            skippedCollisions
        ]() mutable {
            auto report=request.kind==fxfile::shelltransfer::Kind::Recycle?
                fxfile::shelltransfer::execute(request,*progress):
                fxfile::shelltransfer::executeIsolated(request,*progress);
            TransferCompletion value{};
            value.ticket=ticket;
            value.context=std::move(context);
            value.request=std::move(request);
            value.report=std::move(report);
            value.skippedCollisions=skippedCollisions;
            value.touchedFolders=std::move(touched);
            bool posted=false;
            try{
                posted=post([
                    completion=std::move(completion),
                    value=std::move(value)
                ]() mutable {
                    completion(std::move(value));
                });
            }catch(...){}
            if(!posted){
                try{
                    std::lock_guard<std::mutex> lock(shared->mutex);
                    if(shared->epoch==ticket){
                        shared->busy=false;
                        shared->progress.reset();
                    }
                }catch(...){}
            }
        }).detach();
        return StartStatus::Started;
    }catch(...){
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->epoch==ticket){
            state_->busy=false;
            state_->progress.reset();
        }
        return StartStatus::ThreadStartFailed;
    }
}

FileOperationController::TransferDisposition
FileOperationController::acceptTransfer(
    TransferCompletion const& completion,Context const& liveContext)
{
    std::lock_guard<std::mutex> lock(state_->mutex);
    if(state_->closing||completion.ticket!=state_->epoch||
       state_->restoreInFlight)
        return TransferDisposition::Ignored;
    state_->busy=false;
    state_->progress.reset();

    if(!sameContext(completion.context,liveContext))
        return TransferDisposition::StaleContext;

    // Only the rejected read-only preflight offers a new decision.
    // A failed KeepBoth execution must not reopen a confirmation after
    // Shell work might already have committed earlier items.
    if(completion.report.error==ERROR_ALREADY_EXISTS&&
       !completion.report.aborted&&
       completion.request.collision==fxfile::shelltransfer::Collision::Reject&&
       !completion.report.collisions.empty()&&
       completion.request.kind!=fxfile::shelltransfer::Kind::Recycle){
        if(state_->confirmationSerial==
           (std::numeric_limits<std::uint64_t>::max)())
            return TransferDisposition::Failed;
        state_->pending=PendingTransfer{
            completion.request,completion.context,
            completion.report.collisions,completion.skippedCollisions};
        state_->pending->token=++state_->confirmationSerial;
        return TransferDisposition::NeedsCollisionConfirmation;
    }
    // An aborted native operation can have committed earlier items.
    // Never treat an inconsistent success error code as full completion.
    if(completion.report.aborted||
       completion.report.error!=ERROR_SUCCESS)
        return TransferDisposition::Failed;
    return TransferDisposition::Succeeded;
}

FileOperationController::StartStatus FileOperationController::startFileCommand(
    fxfile::filecommand::Request request,Context context,
    Post post,FileCommandCallback completion)
{
    if(!post||!completion)return StartStatus::ThreadStartFailed;
    std::uint64_t ticket=0;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(context.side<0||context.side>1||context.visibleFolder.empty()||
           request.parent!=context.visibleFolder)
            return StartStatus::InvalidVisibleContext;
        if(state_->epoch==(std::numeric_limits<std::uint64_t>::max)())
            return StartStatus::ThreadStartFailed;
        ticket=++state_->epoch;
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        state_->fileCommandNavigationGeneration=state_->navigationGeneration;
        state_->busy=true;
        state_->progress.reset();
        state_->pending.reset();
    }
    auto shared=state_;
    try{
        std::thread([
            shared,ticket,context=std::move(context),
            request=std::move(request),post=std::move(post),
            completion=std::move(completion)
        ]() mutable {
            FileCommandCompletion value{};
            value.ticket=ticket;
            value.context=std::move(context);
            value.kind=request.kind;
            // Capture a value before the worker mutates the item; never ask
            // another tab's current selection for a post-hoc undo source.
            std::wstring originalRenameSource{};
            if(request.kind==fxfile::filecommand::Kind::RenameSelected)
                originalRenameSource=request.source;
            value.result=fxfile::filecommand::execute(request);
            if(value.kind==fxfile::filecommand::Kind::RenameSelected&&
               value.result.error==ERROR_SUCCESS)
                value.originalRenameSource=std::move(originalRenameSource);
            bool posted=false;
            try{
                posted=post([
                    completion=std::move(completion),
                    value=std::move(value)
                ]() mutable {
                    completion(std::move(value));
                });
            }catch(...){}
            if(!posted){
                try{
                    std::lock_guard<std::mutex> lock(shared->mutex);
                    if(shared->epoch==ticket)shared->busy=false;
                }catch(...){}
            }
        }).detach();
        return StartStatus::Started;
    }catch(...){
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->epoch==ticket)state_->busy=false;
        return StartStatus::ThreadStartFailed;
    }
}

FileOperationController::CommandDisposition
FileOperationController::acceptFileCommand(
    FileCommandCompletion const& completion,Context const& liveContext)
{
    std::lock_guard<std::mutex> lock(state_->mutex);
    if(state_->closing||completion.ticket!=state_->epoch||
       completion.ticket==0||!state_->busy||state_->restoreInFlight)
        return CommandDisposition::Ignored;
    state_->busy=false;
    state_->renameCandidate.reset();
    state_->pendingRestoreCheck.reset();
    if(!sameContext(completion.context,liveContext)||
       state_->navigationGeneration==
           (std::numeric_limits<std::uint64_t>::max)()||
       state_->fileCommandNavigationGeneration!=state_->navigationGeneration)
        return CommandDisposition::StaleContext;
    if(completion.result.error!=ERROR_SUCCESS)
        return CommandDisposition::Failed;

    // Only the actually accepted success from this controller's live
    // ticket/context can be remembered. A verified file ID alone is not
    // permission to execute a restore or to reuse the receipt after navigation.
    if(completion.kind==fxfile::filecommand::Kind::RenameSelected&&
       completion.result.renameEvidence.verified&&
       !completion.originalRenameSource.empty()&&
       !completion.result.target.empty()){
        try{
            state_->renameCandidate.emplace(RenameRestoreCandidate{
                completion.ticket,completion.context,
                completion.originalRenameSource,completion.result});
        }catch(...){
            // An allocation failure must not reinterpret an already
            // successful rename as a failed file command.
            state_->renameCandidate.reset();
        }
    }
    return CommandDisposition::Succeeded;
}

std::optional<FileOperationController::RenameRestoreCandidate>
FileOperationController::takeRenameRestoreCandidate(
    Context const& liveContext)
{
    std::lock_guard<std::mutex> lock(state_->mutex);
    if(state_->closing||state_->busy||state_->pending||
       !state_->renameCandidate)
        return std::nullopt;
    if(state_->renameCandidate->ticket==0||
       state_->renameCandidate->ticket!=state_->epoch||
       !sameContext(state_->renameCandidate->context,liveContext)){
        // A stale owner must not become valid again if the user returns
        // to an earlier pane. This check is not a filesystem preflight.
        state_->renameCandidate.reset();
        return std::nullopt;
    }
    // No second retrieval is possible from this controller, including when
    // multiple callers race. The returned value is still not Undo authority.
    try{
        auto taken=std::move(state_->renameCandidate);
        state_->renameCandidate.reset();
        // A private expected-value snapshot protects the subsequent check
        // from a caller changing paths, receipt evidence or the ticket.
        state_->pendingRestoreCheck=taken;
        return taken;
    }catch(...){
        state_->renameCandidate.reset();
        state_->pendingRestoreCheck.reset();
        return std::nullopt;
    }
}

FileOperationController::RestoreOutcomeClass
FileOperationController::classifyRestoreOutcome(
    fxfile::filecommand::RenameRestoreWriteResult const& result) noexcept
{
    using Status=fxfile::filecommand::RenameRestoreWriteStatus;
    if(result.nativeCallAttempted){
        return result.status==Status::CommittedVerified?
            RestoreOutcomeClass::VerifiedCommitted:
            RestoreOutcomeClass::UncertainAfterAttempt;
    }
    switch(result.status){
    case Status::RejectedReceipt:
    case Status::RejectedPaths:
    case Status::OriginalOccupiedOrUnknown:
    case Status::TargetChangedOrUnavailable:
    case Status::AccessUnavailable:
        return RestoreOutcomeClass::NotAttempted;
    case Status::NativeCallFailedUnknownState:
    case Status::CommittedUnverified:
    case Status::CommittedVerified:
        // An impossible nativeCallAttempted/status combination is NOT proof
        // that no changes occurred. Preserve the conservative classification.
        return RestoreOutcomeClass::UncertainAfterAttempt;
    }
    return RestoreOutcomeClass::UncertainAfterAttempt;
}

fxfile::filecommand::RenameRestoreWriteResult
FileOperationController::executeTakenRenameRestoreOnState(
    std::shared_ptr<SharedState> const& shared,
    RenameRestoreCandidate const& taken,Context const& liveContext) noexcept
{
    fxfile::filecommand::RenameRestoreWriteResult denied{};
    std::wstring originalCopy{};
    fxfile::filecommand::Result renamedCopy{};
    try{
        {
            std::lock_guard<std::mutex> lock(shared->mutex);
            if(!shared->pendingRestoreCheck)return denied;
            auto const& expected=*shared->pendingRestoreCheck;
            auto const& left=expected.renamed;
            auto const& right=taken.renamed;
            auto const& before=left.renameEvidence;
            auto const& after=right.renameEvidence;
            const bool current=
                !shared->closing&&!shared->busy&&!shared->pending&&
                taken.ticket!=0&&taken.ticket==shared->epoch&&
                taken.ticket==expected.ticket&&
                sameContext(expected.context,liveContext)&&
                sameContext(taken.context,liveContext)&&
                !expected.originalPath.empty()&&
                expected.originalPath==taken.originalPath&&
                left.error==ERROR_SUCCESS&&right.error==left.error&&
                !left.target.empty()&&right.target==left.target&&
                before.verified&&after.verified==before.verified&&
                after.volumeSerial==before.volumeSerial&&
                after.fileId==before.fileId&&
                after.fileSize==before.fileSize&&
                after.lastWriteTime==before.lastWriteTime;
            // A rejected claim must never be replayed, even if its context
            // becomes current again. No native file operation has started.
            if(!current){
                shared->pendingRestoreCheck.reset();
                return denied;
            }
            // Own immutable values before leaving the lock. Allocation
            // failure only drops the claim; never write from a borrowed
            // candidate that its caller might subsequently change.
            originalCopy=taken.originalPath;
            renamedCopy=taken.renamed;
            shared->pendingRestoreCheck.reset();
            shared->busy=true;
            shared->restoreInFlight=true;
        }
    }catch(...){
        try{
            std::lock_guard<std::mutex> lock(shared->mutex);
            shared->pendingRestoreCheck.reset();
        }catch(...){}
        return denied;
    }

    // The ticket is now permanently claimed; new file/transfer operations
    // see busy=true. Navigation and close are never blocked by a held
    // controller mutex while Windows performs a potentially slow rename.
    // Once this call starts, navigation/close cannot cancel its OS mutation.
    auto outcome=fxfile::filecommand::restoreRenameNoReplace(
        originalCopy,renamedCopy);
    try{
        std::lock_guard<std::mutex> lock(shared->mutex);
        shared->restoreInFlight=false;
        if(!shared->closing&&shared->epoch==taken.ticket)
            shared->busy=false;
        // A closed window has already cleared busy and advanced its epoch;
        // preserve the native outcome without resurrecting controller state.
    }catch(...){
        // The native outcome remains truthful, even if cleanup fails.
    }
    return outcome;
}

fxfile::filecommand::RenameRestoreWriteResult
FileOperationController::executeTakenRenameRestore(
    RenameRestoreCandidate const& taken,Context const& liveContext) noexcept
{
    return executeTakenRenameRestoreOnState(state_,taken,liveContext);
}

FileOperationController::StartStatus
FileOperationController::startTakenRenameRestoreAsync(
    RenameRestoreCandidate taken,Context liveContext,
    Post post,RestoreCallback completion)
{
    if(!post||!completion)return StartStatus::ThreadStartFailed;
    auto shared=state_;
    std::uint64_t generation=0;
    {
        std::lock_guard<std::mutex> lock(shared->mutex);
        if(shared->closing||shared->busy)return StartStatus::Busy;
        if(!shared->pendingRestoreCheck||taken.ticket==0||
           taken.ticket!=shared->epoch||
           !sameContext(taken.context,liveContext))
            return StartStatus::StaleConfirmation;
        generation=shared->navigationGeneration;
    }
    try{
        std::thread([
            shared,generation,taken=std::move(taken),
            liveContext=std::move(liveContext),post=std::move(post),
            completion=std::move(completion)
        ]() mutable {
            RestoreCompletion value{};
            value.ticket=taken.ticket;
            value.context=liveContext;
            value.result=executeTakenRenameRestoreOnState(
                shared,taken,liveContext);
            value.outcome=classifyRestoreOutcome(value.result);

            // A file mutation may have succeeded even though the owner
            // navigated or closed. Drop only the UI notification, NEVER
            // rewrite the native outcome or retry it.
            try{
                std::lock_guard<std::mutex> lock(shared->mutex);
                if(shared->closing||shared->epoch!=value.ticket||
                   shared->navigationGeneration!=generation)
                    return;
            }catch(...){return;}
            try{
                // Even a faulty host Post that replays or copies one task
                // must not deliver a restore result more than once.
                // The native mutation itself remains single-use as well.
                auto delivered=std::make_shared<std::atomic_bool>(false);
                post([shared,generation,delivered,
                      completion=std::move(completion),
                      value=std::move(value)]() mutable {
                    if(delivered->exchange(true,std::memory_order_acq_rel))
                        return;
                    // Revalidate AT DISPATCH, not just when it was queued.
                    // The callback must be executed on the host UI queue,
                    // where tab/close notifications are also serialized.
                    {
                        std::lock_guard<std::mutex> lock(shared->mutex);
                        if(shared->closing||shared->epoch!=value.ticket||
                           shared->navigationGeneration!=generation)
                            return;
                    }
                    completion(std::move(value));
                });
            }catch(...){
                // Post/callback delivery failures do not authorize a retry.
            }
        }).detach();
        return StartStatus::Started;
    }catch(...){
        return StartStatus::ThreadStartFailed;
    }
}

bool FileOperationController::recheckAndRetireRenameRestoreCandidate(
    RenameRestoreCandidate const& taken,Context const& liveContext) noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(!state_->pendingRestoreCheck)return false;
        auto const& expected=*state_->pendingRestoreCheck;
        auto const& left=expected.renamed;
        auto const& right=taken.renamed;
        auto const& before=left.renameEvidence;
        auto const& after=right.renameEvidence;
        const bool current=
            !state_->closing&&!state_->busy&&!state_->pending&&
            taken.ticket!=0&&taken.ticket==state_->epoch&&
            taken.ticket==expected.ticket&&
            sameContext(expected.context,liveContext)&&
            sameContext(taken.context,liveContext)&&
            !expected.originalPath.empty()&&
            expected.originalPath==taken.originalPath&&
            left.error==ERROR_SUCCESS&&right.error==left.error&&
            !left.target.empty()&&right.target==left.target&&
            before.verified&&after.verified==before.verified&&
            after.volumeSerial==before.volumeSerial&&
            after.fileId==before.fileId&&
            after.fileSize==before.fileSize&&
            after.lastWriteTime==before.lastWriteTime;
        // Consume the claim in the SAME lock whether it matched or not.
        // A copied/stale candidate must never pass this check twice.
        state_->pendingRestoreCheck.reset();
        return current;
    }catch(...){
        try{
            std::lock_guard<std::mutex> lock(state_->mutex);
            state_->pendingRestoreCheck.reset();
        }catch(...){}
        return false;
    }
}

} // namespace fxfile::previewops
