#include "pch.h"
#include "search_controller.h"
#include <mutex>
#include <thread>
#include <utility>

namespace fxfile::previewsearch {

struct SearchController::SharedState final {
    mutable std::mutex mutex;
    std::uint64_t epoch=0;
    std::uint64_t recentRevision=0;
    bool closing=false;
    std::shared_ptr<std::atomic_bool> cancel{};
    std::vector<std::wstring> recent{};
};

SearchController::SearchController()
    : state_(std::make_shared<SharedState>())
{
}

SearchController::~SearchController()
{
    prepareForClose();
}

SearchController::StartStatus SearchController::validateRequest(
    Request const& request) noexcept
{
    if(request.scope.empty()||request.scope.size()>32700)
        return StartStatus::InvalidRequest;
    switch(fxfile::preview::validateSearchQuery(request.query)){
    case fxfile::preview::SearchQueryValidation::Valid:
        return StartStatus::Started;
    case fxfile::preview::SearchQueryValidation::InvalidExtension:
        return StartStatus::InvalidExtension;
    case fxfile::preview::SearchQueryValidation::InvalidSizeRange:
        return StartStatus::InvalidSizeRange;
    case fxfile::preview::SearchQueryValidation::InvalidDateRange:
        return StartStatus::InvalidDateRange;
    case fxfile::preview::SearchQueryValidation::InvalidContentTerm:
        return StartStatus::InvalidContentTerm;
    case fxfile::preview::SearchQueryValidation::InvalidContentEncoding:
        return StartStatus::InvalidContentEncoding;
    case fxfile::preview::SearchQueryValidation::InvalidContentRegex:
        return StartStatus::InvalidContentPattern;
    case fxfile::preview::SearchQueryValidation::InvalidRegex:
        return StartStatus::InvalidPattern;
    default:
        return StartStatus::InvalidRequest;
    }
}

bool SearchController::sameContext(
    Context const& a,Context const& b) noexcept
{
    return a.windowIdentity==b.windowIdentity&&
           a.side==b.side&&a.tab==b.tab&&a.route==b.route&&
           a.paneFolder==b.paneFolder&&
           a.scope==b.scope&&
           fxfile::preview::sameSearchQuery(a.query,b.query);
}

SearchController::StartStatus SearchController::start(
    Request request,Context context,Post post,
    CompletionCallback completion)
{
    const auto validation=validateRequest(request);
    if(validation!=StartStatus::Started)return validation;
    if(!post||!completion)return StartStatus::ThreadStartFailed;

    auto cancel=std::make_shared<std::atomic_bool>(false);
    std::uint64_t ticket=0;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing)return StartStatus::Closing;
        if(state_->cancel)state_->cancel->store(true);
        ticket=++state_->epoch;
        state_->cancel=cancel;
    }

    auto shared=state_;
    try{
        std::thread([
            shared,cancel,ticket,request=std::move(request),
            context=std::move(context),post=std::move(post),
            completion=std::move(completion)
        ]() mutable {
            Completion value{};
            value.ticket=ticket;
            value.context=std::move(context);
            value.request=std::move(request);
            try{
                value.result=fxfile::preview::scanFiles(
                    value.request.scope,value.request.query,cancel);
            }catch(...){
                value.result.scope=value.request.scope;
                value.result.term=value.request.query.term;
                value.result.valid=false;
            }
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
                    if(shared->epoch==ticket&&shared->cancel==cancel)
                        shared->cancel.reset();
                }catch(...){}
            }
        }).detach();
        return StartStatus::Started;
    }catch(...){
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->epoch==ticket&&state_->cancel==cancel)
            state_->cancel.reset();
        return StartStatus::ThreadStartFailed;
    }
}

SearchController::Acceptance SearchController::accept(
    Completion const& completion,Context const& liveContext)
{
    Acceptance accepted{};
    std::vector<std::wstring> persist;
    bool persistRecent=false;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing||completion.ticket!=state_->epoch)
            return accepted;

        if((state_->cancel&&state_->cancel->load())||
           completion.result.canceled){
            state_->cancel.reset();
            accepted.disposition=Disposition::Canceled;
            return accepted;
        }

        if(!sameContext(completion.context,liveContext)){
            state_->cancel.reset();
            accepted.disposition=Disposition::StaleContext;
            return accepted;
        }

        state_->cancel.reset();
        if(!completion.result.valid){
            accepted.disposition=Disposition::Invalid;
            return accepted;
        }

        accepted.disposition=Disposition::Applied;
        if(completion.request.remember){
            const auto before=state_->recent;
            fxfile::preview::rememberScope(
                state_->recent,completion.request.scope);
            accepted.recentChanged=state_->recent!=before;
            ++state_->recentRevision;
            persist=state_->recent;
            persistRecent=true;
        }
    }

    if(persistRecent)
        accepted.recentSaved=fxfile::preview::writeRecentScopes(persist);
    return accepted;
}

void SearchController::invalidate() noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        ++state_->epoch;
        if(state_->cancel)state_->cancel->store(true);
        state_->cancel.reset();
    }catch(...){}
}

void SearchController::prepareForClose() noexcept
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing)return;
        state_->closing=true;
        ++state_->epoch;
        if(state_->cancel)state_->cancel->store(true);
        state_->cancel.reset();
    }catch(...){}
}

bool SearchController::loadRecents(
    Post post,RecentCallback completion)
{
    if(!post||!completion)return false;
    std::uint64_t revision=0;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing)return false;
        revision=state_->recentRevision;
    }
    auto shared=state_;
    try{
        std::thread([
            shared,revision,post=std::move(post),
            completion=std::move(completion)
        ]() mutable {
            std::vector<std::wstring> loaded;
            const bool readable=fxfile::preview::readRecentScopes(loaded);
            if(!readable)loaded.clear();
            bool applied=false;
            {
                std::lock_guard<std::mutex> lock(shared->mutex);
                if(!shared->closing&&
                   shared->recentRevision==revision){
                    shared->recent=std::move(loaded);
                    applied=true;
                }
            }
            try{
                (void)post([
                    completion=std::move(completion),applied
                ]() mutable {
                    completion(applied);
                });
            }catch(...){}
        }).detach();
        return true;
    }catch(...){
        return false;
    }
}

std::vector<std::wstring> SearchController::recentScopes() const
{
    try{
        std::lock_guard<std::mutex> lock(state_->mutex);
        return state_->recent;
    }catch(...){
        return {};
    }
}

bool SearchController::clearRecent()
{
    std::vector<std::wstring> persist;
    {
        std::lock_guard<std::mutex> lock(state_->mutex);
        if(state_->closing)return false;
        state_->recent.clear();
        ++state_->recentRevision;
        persist=state_->recent;
    }
    return fxfile::preview::writeRecentScopes(persist);
}

} // namespace fxfile::previewsearch
