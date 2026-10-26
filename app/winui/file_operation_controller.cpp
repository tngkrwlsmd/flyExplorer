#include "pch.h"
#include "file_operation_controller.h"
#include <algorithm>
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
    bool busy=false;
    bool closing=false;
    std::shared_ptr<fxfile::shelltransfer::Progress> progress{};
    std::optional<PendingTransfer> pending{};
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

void FileOperationController::prepareForClose() noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        state_->closing=true;
        ++state_->epoch;
        if(state_->progress)state_->progress->cancel.store(true);
        state_->progress.reset();
        state_->pending.reset();
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
        ticket=++state_->epoch;
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
    if(state_->closing||completion.ticket!=state_->epoch)
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
        ticket=++state_->epoch;
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
            value.result=fxfile::filecommand::execute(request);
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
    if(state_->closing||completion.ticket!=state_->epoch)
        return CommandDisposition::Ignored;
    state_->busy=false;
    if(!sameContext(completion.context,liveContext))
        return CommandDisposition::StaleContext;
    return completion.result.error==ERROR_SUCCESS?
        CommandDisposition::Succeeded:CommandDisposition::Failed;
}

} // namespace fxfile::previewops
