#pragma once
// F05 additional grouping dimensions. Pure bounded data projection; callers
// still enforce complete Shell enumeration and current-route metadata.
#include "file_group_projection.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace fxfile::filegroup {
enum class Mode : std::uint8_t { Type, Name, Size, ModifiedMonth };
struct ClassifiedRow final {
    Row source{};
    std::wstring name;
    std::uint64_t bytes=0;
    bool sizeKnown=false;
    // Derived by the existing isolated FileMetadata worker in local time,
    // exactly YYYY-MM-DD HH:MM; no directory scan or OS calls here.
    std::wstring dateLabel;
    bool dateKnown=false;
};
namespace detail {
struct Bucket final {std::wstring title; std::uint64_t rank=0;};
inline bool digit(wchar_t c) noexcept {return c>=L'0'&&c<=L'9';}
inline Bucket name(ClassifiedRow const& item) {
    if(item.name.empty())return {L"이름 없음",99};
    auto ch=item.name.front();
    if(ch>=L'a'&&ch<=L'z')ch=static_cast<wchar_t>(ch-32);
    if(ch>=L'A'&&ch<=L'F')return {L"A–F",0};
    if(ch>=L'G'&&ch<=L'L')return {L"G–L",1};
    if(ch>=L'M'&&ch<=L'R')return {L"M–R",2};
    if(ch>=L'S'&&ch<=L'Z')return {L"S–Z",3};
    if(ch>=L'0'&&ch<=L'9')return {L"0–9",4};
    if(ch>=0xac00&&ch<=0xd7a3)return {L"가–힣",5};
    return {L"기타 이름",98};
}
inline Bucket size(ClassifiedRow const& item) noexcept {
    if(!item.sizeKnown)return {L"크기 미상",99};
    if(item.bytes<10ull*1024)return {L"10 KB 미만",0};
    if(item.bytes<1024ull*1024)return {L"10 KB–1 MB",1};
    if(item.bytes<100ull*1024*1024)return {L"1–100 MB",2};
    return {L"100 MB 이상",3};
}
inline Bucket month(ClassifiedRow const& item) {
    auto const& text=item.dateLabel;
    if(!item.dateKnown||text.size()<7||text[4]!=L'-')
        return {L"수정 날짜 미상",0};
    for(auto n:{0,1,2,3,5,6})if(!digit(text[n]))
        return {L"수정 날짜 미상",0};
    const auto year=(text[0]-L'0')*1000+(text[1]-L'0')*100+
                    (text[2]-L'0')*10+(text[3]-L'0');
    const auto month=(text[5]-L'0')*10+(text[6]-L'0');
    if(year<1601||month<1||month>12)
        return {L"수정 날짜 미상",0};
    return {std::to_wstring(year)+L"년 "+std::to_wstring(month)+L"월",
            static_cast<std::uint64_t>(year*12+month)};
}
inline Bucket type(ClassifiedRow const& item) {
    auto title=category(item.source);
    return {title, title.empty()?0:static_cast<std::uint64_t>(title[0])};
}
inline Bucket classify(Mode mode,ClassifiedRow const& item) {
    if(item.source.folder)return {L"폴더",0};
    switch(mode) {
    case Mode::Type:return type(item);
    case Mode::Name:return name(item);
    case Mode::Size:return size(item);
    case Mode::ModifiedMonth:return month(item);
    }
    return {L"기타",99};
}
} // namespace detail

inline Result projectBy(Mode mode,Request const& request,
                        std::vector<ClassifiedRow> const& rows) {
    if(!request.route||request.route!=request.visibleRoute||
       request.tab!=request.visibleTab||request.side<0||request.side>1)
        return {Status::MissingRoute,{}};
    if(request.modelLimitReached||request.expectedCount>kMaximumIndexedItems)
        return {Status::LimitReached,{}};
    if(!request.indexComplete)return {Status::Incomplete,{}};
    if(request.expectedCount!=rows.size())return {Status::WrongCount,{}};
    std::unordered_set<std::uint64_t> seen;
    seen.reserve(rows.size());
    std::unordered_map<std::wstring,std::size_t> position;
    position.reserve((std::min)(rows.size(),std::size_t{256}));
    std::vector<std::uint64_t> ranks;
    Result result{Status::Ready,{}};
    result.route=request.route;
    result.tab=request.tab;
    result.sourceCount=request.expectedCount;
    result.side=request.side;
    for(auto const& row:rows) {
        if(!row.source.filesystem||!row.source.metadataReady)
            return {Status::UnsupportedItem,{}};
        if(!seen.insert(row.source.logical).second)
            return {Status::DuplicateIdentity,{}};
        auto bucket=detail::classify(mode,row);
        auto [it,inserted]=position.try_emplace(bucket.title,
                                                  result.sections.size());
        if(inserted) {
            ranks.push_back(bucket.rank);
            result.sections.push_back({std::move(bucket.title),{}});
        }
        result.sections[it->second].logicalItems.push_back(row.source.logical);
    }
    // Use a stable indexed ordering so bucket ranks always follow their title.
    std::vector<std::size_t> ordered(result.sections.size());
    for(std::size_t i=0;i<ordered.size();++i)ordered[i]=i;
    std::stable_sort(ordered.begin(),ordered.end(),[&](auto a,auto b){
        const bool folderA=result.sections[a].title==L"폴더";
        const bool folderB=result.sections[b].title==L"폴더";
        if(folderA!=folderB)return folderA;
        const bool unknownA=(mode==Mode::Size&&ranks[a]==99)||
            (mode==Mode::ModifiedMonth&&ranks[a]==0);
        const bool unknownB=(mode==Mode::Size&&ranks[b]==99)||
            (mode==Mode::ModifiedMonth&&ranks[b]==0);
        if(unknownA!=unknownB)return !unknownA;
        if(ranks[a]!=ranks[b])
            return mode==Mode::ModifiedMonth?ranks[a]>ranks[b]:ranks[a]<ranks[b];
        return result.sections[a].title<result.sections[b].title;
    });
    std::vector<Section> sorted;
    sorted.reserve(result.sections.size());
    for(auto i:ordered)sorted.push_back(std::move(result.sections[i]));
    result.sections=std::move(sorted);
    return result;
}
} // namespace fxfile::filegroup
