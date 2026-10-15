#pragma once
// F05: view-only headings and collapse projection for a fully verified model.
// No XAML controls or filesystem operations. Consumers must create independent
// non-selectable headers; only EntryKind::File may become a real selectable row.
#include "file_group_projection.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_set>
#include <vector>

namespace fxfile::filegroup {

enum class EntryKind : std::uint8_t { Heading, File };
struct Entry final {
    EntryKind kind=EntryKind::Heading;
    std::wstring title{};  // non-empty only for a heading
    std::uint64_t logical=0; // native item identity only for File
    std::size_t groupCount=0;
    bool collapsed=false;
};

// An explicit per-pane/per-tab state owner should retain one instance, not
// share it across LeftFiles/RightFiles. Route switches clear stale collapse.
class CollapseState final {
public:
    void resetFor(std::uint64_t route,std::size_t tab,int side=0) {
        if(route_==route&&tab_==tab&&side_==side)return;
        route_=route;
        tab_=tab;
        side_=side;
        collapsed_.clear();
    }
    bool toggle(std::uint64_t route,std::size_t tab,
                std::wstring const& category,int side=0) {
        if(route_!=route||tab_!=tab||side_!=side||category.empty())return false;
        auto found=collapsed_.find(category);
        if(found!=collapsed_.end())collapsed_.erase(found);
        else collapsed_.insert(category);
        return true;
    }
    bool isCollapsed(std::wstring const& category) const {
        return collapsed_.find(category)!=collapsed_.end();
    }
    bool matches(std::uint64_t route,std::size_t tab,int side) const noexcept {
        return route!=0&&route_==route&&tab_==tab&&side_==side;
    }
private:
    std::uint64_t route_=0;
    std::size_t tab_=0;
    int side_=-1;
    std::unordered_set<std::wstring> collapsed_{};
};

struct Page final {
    Status status=Status::Incomplete;
    std::vector<Entry> entries{};
    std::size_t totalFileRows=0;   // expanded, uncollapsed file identities
    std::size_t visibleFileRows=0; // excludes header entries
    bool hasMore=false;
    bool ready() const noexcept {return status==Status::Ready;}
};

inline Page present( Request const& request,Result const& projection,
                     CollapseState const& state,std::size_t maxFileRows) {
    if(!projection.ready())return {projection.status,{}};
    if(!state.matches(request.route,request.tab,request.side) ||
       request.route!=request.visibleRoute || request.tab!=request.visibleTab ||
       projection.route!=request.route || projection.tab!=request.tab ||
       projection.side!=request.side ||
       projection.sourceCount!=request.expectedCount)
        return {Status::MissingRoute,{}};
    if(!request.indexComplete)return {Status::Incomplete,{}};
    if(request.modelLimitReached||request.expectedCount>kMaximumIndexedItems)
        return {Status::LimitReached,{}};
    if(maxFileRows==0)return {Status::WrongCount,{}};
    Page result{Status::Ready,{}};
    for(auto const& group:projection.sections)
        if(!state.isCollapsed(group.title))
            result.totalFileRows+=group.logicalItems.size();
    for(auto const& group:projection.sections){
        if(result.visibleFileRows==maxFileRows)break;
        const bool collapsed=state.isCollapsed(group.title);
        result.entries.push_back({EntryKind::Heading,group.title,0,
                                  group.logicalItems.size(),collapsed});
        if(collapsed)continue;
        for(auto logical:group.logicalItems){
            if(result.visibleFileRows==maxFileRows)break;
            result.entries.push_back({EntryKind::File,{},logical,0,false});
            ++result.visibleFileRows;
        }
    }
    // Empty groups are permitted for an empty indexed directory, but header
    // count must never masquerade as visible file count or native identities.
    if(result.totalFileRows>result.visibleFileRows)result.hasMore=true;
    return result;
}
} // namespace fxfile::filegroup
