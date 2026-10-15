#pragma once
// F05 bounded per-pane, per-route disclosure cache. UI independent and no I/O.
// The owner must call switchTo() BEFORE changing its visible route/tab.
// When returning to a tab, pending means wait for COMPLETE current-route
// metadata before drawing headers; do not use stale metadata from another tab.
#include "file_group_presentation.h"
#include "file_group_modes.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace fxfile::filegroup {
class TabGrouping final {
public:
    void switchTo(std::uint64_t route, std::size_t tab, int side) {
        if (route_==route && tab_==tab && side_==side) return;
        if (route_!=0 && side_>=0 && side_<=1) {
            eraseSaved(route_,tab_);
            if (enabled_ || pending_) {
                if (saved_.size()==kMaxSavedRoutes) saved_.erase(saved_.begin());
                saved_.push_back({route_,tab_,side_,mode_,collapse_});
            }
        }
        route_=route;tab_=tab;side_=side;
        enabled_=false;pending_=false;
        collapse_.resetFor(0,0,side);
        mode_=Mode::Type;
        for (auto it=saved_.begin(); it!=saved_.end(); ++it) {
            if (it->route!=route || it->tab!=tab || it->side!=side) continue;
            collapse_=it->collapse;
            mode_=it->mode;
            pending_=true;
            saved_.erase(it);
            break;
        }
    }
    // A pending tab resumes only when the exact current model is complete.
    bool onCompleteModel(bool metadataCurrent, bool enumerationComplete) {
        if (pending_ && metadataCurrent && enumerationComplete && route_!=0) {
            pending_=false;
            enabled_=true;
            collapse_.resetFor(route_,tab_,side_);
        }
        return enabled_;
    }
    // Opt-in and opt-out are explicit user actions. Failure to activate a
    // new group must call disable(), not silently preserve the old state.
    void choose(Mode mode) {
        if(mode_!=mode)collapse_.resetFor(0,0,side_);
        mode_=mode;enable();
    }
    Mode mode() const noexcept{return mode_;}
    void enable() { pending_=false;enabled_=route_!=0 && (side_==0||side_==1);
                    if(enabled_) collapse_.resetFor(route_,tab_,side_); }
    void disable() {pending_=false;enabled_=false;collapse_.resetFor(0,0,side_);}
    bool enabled() const noexcept {return enabled_;}
    bool pending() const noexcept {return pending_;}
    bool toggle(std::wstring const& title) {
        return enabled_ && collapse_.toggle(route_,tab_,title,side_);
    }
    bool isCollapsed(std::wstring const& title) const {
        return enabled_ && collapse_.isCollapsed(title);
    }
    CollapseState const& collapse() const noexcept {return collapse_;}
    std::uint64_t route() const noexcept{return route_;}
    std::size_t tab() const noexcept{return tab_;}
    static constexpr std::size_t kMaxSavedRoutes=32;
    std::size_t savedRoutes() const noexcept{return saved_.size();}
private:
    struct Saved final {std::uint64_t route;std::size_t tab;int side;Mode mode;CollapseState collapse;};
    void eraseSaved(std::uint64_t route,std::size_t tab) {
        saved_.erase(std::remove_if(saved_.begin(),saved_.end(),
            [route,tab,this](Saved const& s){return s.route==route&&s.tab==tab&&s.side==side_;}),saved_.end());
    }
    std::uint64_t route_=0;
    std::size_t tab_=0;
    int side_=-1;
    bool enabled_=false,pending_=false;
    CollapseState collapse_{};
    Mode mode_=Mode::Type;
    std::vector<Saved> saved_{};
};
}
