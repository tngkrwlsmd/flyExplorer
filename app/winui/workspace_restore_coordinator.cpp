#include "workspace_restore_coordinator.h"
#include <utility>

namespace fxfile::previewrestore {

bool WorkspaceRestoreCoordinator::validSide(int side) noexcept
{
    return side>=0&&side<2;
}

void WorkspaceRestoreCoordinator::reset() noexcept
{
    reset(0);
    reset(1);
}

void WorkspaceRestoreCoordinator::reset(int side) noexcept
{
    if(!validSide(side))return;
    auto& lane=lanes_[static_cast<std::size_t>(side)];
    lane.tasks.clear();
    lane.awaitedRequest=0;
}

void WorkspaceRestoreCoordinator::begin(
    int side,std::vector<Task> tasks,
    std::uint64_t initialRequest)
{
    if(!validSide(side))return;
    reset(side);
    auto& lane=lanes_[static_cast<std::size_t>(side)];
    for(auto& task:tasks)lane.tasks.push_back(std::move(task));
    lane.awaitedRequest=initialRequest;
}

bool WorkspaceRestoreCoordinator::settle(
    int side,std::uint64_t request) noexcept
{
    if(!validSide(side)||!request)return false;
    auto& lane=lanes_[static_cast<std::size_t>(side)];
    if(lane.awaitedRequest!=request)return false;
    lane.awaitedRequest=0;
    return true;
}

std::optional<WorkspaceRestoreCoordinator::Task>
WorkspaceRestoreCoordinator::takeNext(
    int side,bool paneBusy,std::size_t tabCount)
{
    if(!validSide(side)||paneBusy)return std::nullopt;
    auto& lane=lanes_[static_cast<std::size_t>(side)];
    if(lane.awaitedRequest)return std::nullopt;
    while(!lane.tasks.empty()){
        auto task=std::move(lane.tasks.front());
        lane.tasks.pop_front();
        if(task.tab>=tabCount)continue;
        return task;
    }
    return std::nullopt;
}

bool WorkspaceRestoreCoordinator::track(
    int side,std::uint64_t request) noexcept
{
    if(!validSide(side)||!request)return false;
    auto& lane=lanes_[static_cast<std::size_t>(side)];
    if(lane.awaitedRequest)return false;
    lane.awaitedRequest=request;
    return true;
}

bool WorkspaceRestoreCoordinator::active(int side) const noexcept
{
    if(!validSide(side))return false;
    auto const& lane=lanes_[static_cast<std::size_t>(side)];
    return lane.awaitedRequest||!lane.tasks.empty();
}

std::size_t WorkspaceRestoreCoordinator::queued(int side) const noexcept
{
    if(!validSide(side))return 0;
    return lanes_[static_cast<std::size_t>(side)].tasks.size();
}

} // namespace fxfile::previewrestore
