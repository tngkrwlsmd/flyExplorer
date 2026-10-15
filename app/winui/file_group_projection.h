#pragma once
// F05 initial type grouping projection. No Shell I/O, UI types, or persistence.
// A group is never presented as directory-wide until the indexed model is
// fully known; resident/paged UI rows alone are never a complete model.
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace fxfile::filegroup {
inline constexpr std::size_t kMaximumIndexedItems=25000;
enum class Status : std::uint8_t {
    Ready, MissingRoute, Incomplete, LimitReached, WrongCount,
    UnsupportedItem, DuplicateIdentity
};
struct Row final {
    std::uint64_t logical=0;
    bool filesystem=false;
    bool folder=false;
    bool metadataReady=false;
    std::wstring typeKey{}; // from the existing isolated metadata controller
};
struct Request final {
    std::uint64_t route=0, visibleRoute=0;
    std::size_t tab=0, visibleTab=0;
    std::size_t expectedCount=0;
    bool indexComplete=false;
    bool modelLimitReached=false;
    int side=0; // explicit active file pane; routes may collide across panes
};
struct Section final {
    std::wstring title;
    std::vector<std::uint64_t> logicalItems; // original Shell identities
};
struct Result final {
    Status status=Status::Incomplete;
    std::vector<Section> sections{};
    std::uint64_t route=0;
    std::size_t tab=0;
    std::size_t sourceCount=0;
    int side=-1;
    bool ready() const noexcept { return status==Status::Ready; }
};
inline std::wstring category(Row const& row) {
    if(row.folder)return L"폴더";
    if(row.typeKey.empty())return L"확장자 없음";
    std::wstring key(row.typeKey);
    // Existing metadata.typeKey is a file extension. Avoid treating free-form
    // provider display strings as extensions; return a neutral safe bucket.
    if(key.size()>64||key[0]!=L'.')return L"기타 파일";
    for(auto& c:key){
        if(c>=L'A'&&c<=L'Z')c=static_cast<wchar_t>(c+32);
    }
    return key;
}
inline Result projectByType(Request const& request,
                            std::vector<Row> const& rows) {
    if(!request.route||request.route!=request.visibleRoute||
       request.tab!=request.visibleTab||request.side<0||request.side>1)
        return {Status::MissingRoute,{}};
    if(request.modelLimitReached||request.expectedCount>kMaximumIndexedItems)
        return {Status::LimitReached,{}};
    if(!request.indexComplete)return {Status::Incomplete,{}};
    if(request.expectedCount!=rows.size())return {Status::WrongCount,{}};
    std::unordered_set<std::uint64_t> seen;
    std::unordered_map<std::wstring,std::size_t> positions;
    Result result{Status::Ready,{}};
    result.route=request.route;
    result.tab=request.tab;
    result.sourceCount=request.expectedCount;
    result.side=request.side;
    seen.reserve(rows.size());
    positions.reserve((std::min)(rows.size(),std::size_t{256}));
    for(auto const& row:rows){
        if(!row.filesystem||!row.metadataReady)
            return {Status::UnsupportedItem,{}};
        if(!seen.insert(row.logical).second)
            return {Status::DuplicateIdentity,{}};
        auto title=category(row);
        const auto [at,newGroup]=positions.try_emplace(title,result.sections.size());
        if(newGroup)result.sections.push_back({std::move(title),{}});
        result.sections[at->second].logicalItems.push_back(row.logical);
    }
    // Stable category order: folders first, extensions alphabetical, and
    // unknown/no-extension categories last. Within each group the existing
    // full-model sort order and original logical identities are unchanged.
    std::stable_sort(result.sections.begin(),result.sections.end(),
        [](Section const& a,Section const& b){
            auto priority=[](std::wstring_view title){
                if(title==L"폴더")return 0;
                if(!title.empty()&&title.front()==L'.')return 1;
                return 2;
            };
            const auto pa=priority(a.title),pb=priority(b.title);
            return pa==pb?a.title<b.title:pa<pb;
        });
    return result;
}
} // namespace fxfile::filegroup
