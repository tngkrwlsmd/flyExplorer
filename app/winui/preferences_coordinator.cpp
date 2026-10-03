#include "preferences_coordinator.h"
#include <thread>
#include <utility>

namespace fxfile::previewprefs {

bool PreferencesCoordinator::load() noexcept
{
    return fxfile::uisettings::load(preferences_);
}

bool PreferencesCoordinator::persist(Post post,FailureCallback failure)
{
    const auto snapshot=preferences_;
    auto guard=writeMutex_;
    auto revision=revision_;
    const auto ticket=revision->fetch_add(1)+1;
    try{
        std::thread([
            snapshot,guard=std::move(guard),revision=std::move(revision),
            ticket,post=std::move(post),failure=std::move(failure)]() mutable {
            std::lock_guard<std::mutex> lock(*guard);
            if(ticket!=revision->load())return;
            if(fxfile::uisettings::save(snapshot))return;
            if(ticket!=revision->load()||!post||!failure)return;
            try{
                post([failure=std::move(failure)]() mutable {failure();});
            }catch(...){}
        }).detach();
    }catch(...){
        return false;
    }
    return true;
}

} // namespace fxfile::previewprefs
