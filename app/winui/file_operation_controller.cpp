#include "pch.h"
#include "file_operation_controller.h"
#include <mutex>
#include <optional>
#include <thread>
#include <utility>

namespace fxfile::previewops {

struct FileOperationController::PendingTransfer final {
    fxfile::shelltransfer::Request request{};
    Context context{};
};

struct FileOperationController::SharedState final {
    mutable std::mutex mutex;
    std::uint64_t epoch=0;
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
    return a.side==b.side&&a.tab==b.tab&&a.route==b.route&&
           a.visibleFolder==b.visibleFolder;
}

bool FileOperationController::visibleForTransfer(
    fxfile::shelltransfer::Request const& request,
    Context const& context) noexcept
{
    if(context.side<0||context.side>1||context.visibleFolder.empty())
        return false;
    if(context.visibleFolder==request.sourceParent)return true;
    return request.kind!=fxfile::shelltransfer::Kind::Recycle&&
           context.visibleFolder==request.destination;
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
            state_->pending=PendingTransfer{std::move(request),std::move(context)};
            return StartStatus::NeedsRecycleConfirmation;
        }
        state_->pending.reset();
    }
    return launchTransfer(
        std::move(request),std::move(context),
        std::move(post),std::move(completion));
}

FileOperationController::StartStatus FileOperationController::confirmRecycle(
    bool approved,Context liveContext,Post post,
    TransferCallback completion)
{
    PendingTransfer pending{};
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!state_->pending||
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
    bool approved,Context liveContext,Post post,
    TransferCallback completion)
{
    PendingTransfer pending{};
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||state_->busy)return StartStatus::Busy;
        if(!state_->pending||
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
        std::move(post),std::move(completion));
}

FileOperationController::StartStatus FileOperationController::launchTransfer(
    fxfile::shelltransfer::Request request,Context context,
    Post post,TransferCallback completion)
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
    touched.push_back(request.sourceParent);
    if(request.kind!=fxfile::shelltransfer::Kind::Recycle&&
       request.destination!=request.sourceParent)
        touched.push_back(request.destination);

    auto shared=state_;
    try{
        std::thread([
            shared,progress,ticket,context=std::move(context),
            request=std::move(request),touched=std::move(touched),
            post=std::move(post),completion=std::move(completion)
        ]() mutable {
            auto report=fxfile::shelltransfer::execute(request,*progress);
            TransferCompletion value{};
            value.ticket=ticket;
            value.context=std::move(context);
            value.request=std::move(request);
            value.report=std::move(report);
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

    if(completion.report.error==ERROR_ALREADY_EXISTS&&
       !completion.report.collisions.empty()&&
       completion.request.kind!=fxfile::shelltransfer::Kind::Recycle){
        state_->pending=PendingTransfer{
            completion.request,completion.context};
        return TransferDisposition::NeedsCollisionConfirmation;
    }
    if(completion.report.error!=ERROR_SUCCESS)
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
