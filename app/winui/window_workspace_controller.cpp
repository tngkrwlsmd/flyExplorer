#include "window_workspace_controller.h"
#include <algorithm>
#include <utility>

namespace fxfile::previewtabs {
namespace {
constexpr std::uint64_t kMaxWindowTabIdentity=0xffffffffull;
}

WindowWorkspaceController::WindowWorkspaceController()
{
    states_.emplace_back(0);
}

WindowTabState& WindowWorkspaceController::active()
{
    return states_.at(active_);
}

WindowTabState const& WindowWorkspaceController::active() const
{
    return states_.at(active_);
}

WindowTabState& WindowWorkspaceController::state(std::size_t index)
{
    return states_.at(index);
}

WindowTabState const& WindowWorkspaceController::state(std::size_t index) const
{
    return states_.at(index);
}

std::vector<WindowTabState> const& WindowWorkspaceController::states() const noexcept
{
    return states_;
}

std::size_t WindowWorkspaceController::count() const noexcept
{
    return states_.size();
}

std::size_t WindowWorkspaceController::activeIndex() const noexcept
{
    return active_;
}

bool WindowWorkspaceController::isActive(std::size_t index) const noexcept
{
    return index<states_.size()&&index==active_;
}

bool WindowWorkspaceController::canCreate() const noexcept
{
    return states_.size()<kMaxWindowTabs&&nextIdentity_<=kMaxWindowTabIdentity;
}

bool WindowWorkspaceController::create()
{
    if(!canCreate())return false;
    states_.emplace_back(nextIdentity_++);
    active_=states_.size()-1;
    return true;
}

bool WindowWorkspaceController::activate(std::size_t index) noexcept
{
    if(index>=states_.size())return false;
    active_=index;
    return true;
}

bool WindowWorkspaceController::close(std::size_t index)
{
    if(states_.size()<=1||index>=states_.size())return false;
    const bool closingActive=index==active_;
    states_.erase(states_.begin()+static_cast<std::ptrdiff_t>(index));
    if(index<active_)--active_;
    else if(closingActive&&active_>=states_.size())active_=states_.size()-1;
    return true;
}

fxfile::explorerui::Change WindowWorkspaceController::dispatch(
    fxfile::explorerui::Command command,int side,std::size_t tab)
{
    auto& state=active();
    if(command!=fxfile::explorerui::Command::SelectTab&&
       command!=fxfile::explorerui::Command::AddTab&&
       command!=fxfile::explorerui::Command::CloseTab)
        return state.model.dispatch(command,side,tab);
    if(side<0||side>1)return {};
    auto& pane=state.model.panes[side];
    auto& modes=state.tabSortModes[side];
    if(modes.size()!=pane.tabs.size()||pane.active>=modes.size())return {};
    const auto previous=pane.active;
    const int current=state.fileLists[side].sortMode;
    const auto result=state.model.dispatch(command,side,tab);
    if(!result.accepted)return result;
    modes[previous]=current;
    if(command==fxfile::explorerui::Command::AddTab){
        modes.push_back(0);
    }else if(command==fxfile::explorerui::Command::CloseTab){
        modes.erase(modes.begin()+static_cast<std::ptrdiff_t>(previous));
    }
    state.fileLists[side].sortMode=modes[pane.active];
    return result;
}

bool WindowWorkspaceController::resetActive(
    bool split,std::array<std::size_t,2> counts,
    std::array<std::size_t,2> selected)
{
    auto& state=active();
    if(!state.model.reset(split,counts,selected))return false;
    for(int side=0;side<2;++side){
        state.tabSortModes[side].assign(counts[side],0);
        state.fileLists[side].sortMode=0;
    }
    return true;
}

bool WindowWorkspaceController::replace(
    std::vector<WindowTabState>&& states,std::size_t activeIndex)
{
    if(states.empty()||states.size()>kMaxWindowTabs||activeIndex>=states.size())
        return false;
    std::uint64_t maxIdentity=0;
    for(std::size_t i=0;i<states.size();++i){
        if(states[i].identity>kMaxWindowTabIdentity)return false;
        for(int side=0;side<2;++side){
            auto const& pane=states[i].model.panes[side];
            auto const& modes=states[i].tabSortModes[side];
            if(modes.size()!=pane.tabs.size()||pane.active>=modes.size()||
               modes[pane.active]!=states[i].fileLists[side].sortMode)
                return false;
            if(std::any_of(modes.begin(),modes.end(),
                           [](int mode){return mode<0||mode>7;}))return false;
        }
        maxIdentity=(std::max)(maxIdentity,states[i].identity);
        for(std::size_t j=i+1;j<states.size();++j)
            if(states[i].identity==states[j].identity)return false;
    }
    states_=std::move(states);
    active_=activeIndex;
    nextIdentity_=maxIdentity+1;
    return true;
}

} // namespace fxfile::previewtabs
