#include "../../app/winui/file_group_presentation.h"
#include <cassert>
#include <iostream>
#include <unordered_set>
using namespace fxfile::filegroup;

int main(){
    auto req=Request{91,91,0,0,5,true,false};
    std::vector<Row> left{
        {301,true,true,true,L""},{807,true,false,true,L".TXT"},
        {5,true,false,true,L".md"},{12,true,false,true,L".txt"},
        {2,true,false,true,L""}};
    auto projection=projectByType(req,left);
    assert(projection.ready()&&projection.sections.size()==4);
    CollapseState leftState,rightState;
    leftState.resetFor(91,0);
    rightState.resetFor(91,0,1);
    auto first=present(req,projection,leftState,160);
    assert(first.ready()&&first.visibleFileRows==5&&!first.hasMore);
    std::unordered_set<std::uint64_t> identities;
    std::size_t headerCount=0;
    for(auto const& row:first.entries){
        if(row.kind==EntryKind::Heading){
            ++headerCount;assert(!row.title.empty());assert(row.groupCount>0);
        }else{
            assert(row.title.empty()&&identities.insert(row.logical).second);
        }
    }
    assert(headerCount==4&&identities.size()==5&&first.entries.size()==9);
    assert(leftState.toggle(91,0,L".txt"));
    auto collapsed=present(req,projection,leftState,160);
    assert(collapsed.visibleFileRows==3&&collapsed.entries.size()==7);
    assert(!rightState.isCollapsed(L".txt")); // independent pane state
    assert(!rightState.toggle(91,0,L".txt",0)); // cross-pane route alias
    assert(!leftState.toggle(92,0,L".md"));   // refuse wrong route
    assert(!leftState.toggle(91,1,L".md"));   // refuse wrong tab
    assert(!leftState.isCollapsed(L".md"));
    auto shortPage=present(req,projection,leftState,2);
    assert(shortPage.ready()&&shortPage.visibleFileRows==2&&shortPage.hasMore);
    // The paging cap counts only selectable real files, never headings.
    assert(shortPage.entries.size()==4);
    auto none=present(req,projection,leftState,0);
    assert(none.status==Status::WrongCount&&none.entries.empty());
    req.indexComplete=false;
    auto unready=projectByType(req,left);
    assert(unready.status==Status::Incomplete);
    assert(present(req,unready,leftState,160).status==Status::Incomplete);
    req.indexComplete=true;
    leftState.resetFor(92,0); // route reset invalidates old collapses
    req.route=92;req.visibleRoute=92;
    auto refreshed=projectByType(req,left);
    assert(present(req,refreshed,leftState,160).visibleFileRows==5);
    // Do not allow a previously classified group on another pane route/tab.
    assert(present(req,refreshed,rightState,160).status==Status::MissingRoute);
    // A completed projection belongs to its exact model identity and count,
    // never to a later tab/route/pane even when a caller reuses the object.
    auto wrongReq=req;
    wrongReq.side=1;
    assert(present(wrongReq,refreshed,rightState,160).status==Status::MissingRoute);
    wrongReq=req;
    wrongReq.expectedCount++;
    assert(present(wrongReq,refreshed,leftState,160).status==Status::MissingRoute);
    wrongReq=req;
    wrongReq.indexComplete=false;
    assert(present(wrongReq,refreshed,leftState,160).status==Status::Incomplete);
    std::vector<Row> bulk;
    bulk.reserve(25000);
    for(std::uint64_t i=0;i<25000;++i)
        bulk.push_back({i,true,false,true,i%2?L".log":L".TXT"});
    req.expectedCount=bulk.size();
    auto full=projectByType(req,bulk);
    assert(full.ready());
    auto firstPage=present(req,full,leftState,160);
    assert(firstPage.visibleFileRows==160&&firstPage.hasMore);
    assert(firstPage.totalFileRows==25000);
    assert(firstPage.entries.size()==161); // only the first represented group
    std::cout<<"F05_NATIVE_COLLAPSIBLE_GROUP_PAGE_PASS\n";
}
