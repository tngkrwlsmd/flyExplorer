#include "../../app/winui/file_group_tab_cache.h"
#include "../../app/winui/file_list_state.h"
#include <cassert>
#include <iostream>
using fxfile::filegroup::TabGrouping;
int main() {
    TabGrouping left,right;
    left.switchTo(101,0,0);
    left.choose(fxfile::filegroup::Mode::Size);assert(left.enabled());
    assert(left.toggle(L".txt"));
    left.switchTo(202,1,0);
    assert(!left.enabled()&&!left.pending());
    left.choose(fxfile::filegroup::Mode::ModifiedMonth);assert(left.toggle(L".md"));
    left.switchTo(101,0,0);
    assert(!left.enabled()&&left.pending());
    assert(!left.isCollapsed(L".txt")); // not exposed until metadata ready
    assert(!left.onCompleteModel(false,true));
    assert(!left.onCompleteModel(true,false));
    assert(left.pending());
    assert(left.onCompleteModel(true,true));
    assert(left.mode()==fxfile::filegroup::Mode::Size);
    assert(left.isCollapsed(L".txt")&&!left.isCollapsed(L".md"));
    left.switchTo(202,1,0);
    assert(left.pending());
    assert(left.onCompleteModel(true,true));
    assert(left.mode()==fxfile::filegroup::Mode::ModifiedMonth);
    assert(left.isCollapsed(L".md")&&!left.isCollapsed(L".txt"));
    right.switchTo(101,0,1);
    assert(!right.enabled()&&!right.pending());
    assert(!right.isCollapsed(L".txt"));
    // Navigating to a never-seen route starts ungrouped, not copied.
    left.switchTo(303,1,0);
    assert(!left.enabled()&&!left.pending());
    assert(!left.isCollapsed(L".md"));
    left.switchTo(202,1,0);
    assert(left.pending());
    left.disable(); // explicit opt-out clears this route's remembered state
    left.switchTo(303,1,0);
    left.switchTo(202,1,0);
    assert(!left.enabled()&&!left.pending());
    // The cache cannot grow without a bound after many route transitions.
    TabGrouping many;
    for(std::uint64_t id=1;id<100;++id) {
        many.switchTo(id,0,0);many.enable();
    }
    many.switchTo(100,0,0);
    assert(many.savedRoutes()==TabGrouping::kMaxSavedRoutes);
    assert(!many.pending()&&!many.enabled());
    // Most recent route can be restored, oldest route has been evicted.
    many.switchTo(99,0,0);
    assert(many.pending());
    many.onCompleteModel(true,true);
    many.switchTo(1,0,0);
    assert(!many.pending()&&!many.enabled());
    // A surviving folder's metadata, sorting and collapse state keep their
    // route identity after an earlier inactive tab shifts its index.
    fxfile::previewlist::PaneState pane;
    constexpr std::uint64_t savedRoute=505,closedRoute=606,activeRoute=707;
    pane.groupTabCache.switchTo(savedRoute,2,0);
    pane.groupTabCache.choose(fxfile::filegroup::Mode::Name);
    assert(pane.groupTabCache.toggle(L"saved section"));
    pane.groupTabCache.switchTo(activeRoute,3,0);
    pane.groupTabCache.choose(fxfile::filegroup::Mode::Size);
    assert(pane.groupTabCache.toggle(L"active section"));
    pane.groupCollapse=pane.groupTabCache.collapse();
    pane.visibleRoute=activeRoute;
    pane.visibleTab=3;
    pane.fileCommandReveal.route=activeRoute;
    pane.fileCommandReveal.tab=3;
    pane.fileCommandReveal.target=L"retained-item";
    pane.fileCommandReveal.afterRefresh=true;
    const auto oldMetadata=pane.beginMetadata(activeRoute,3);
    const auto oldDetail=pane.begin(activeRoute,3);
    pane.onTabClosed(1,closedRoute,0);
    assert(pane.visibleRoute==activeRoute&&pane.visibleTab==2);
    assert(pane.fileCommandReveal.route==activeRoute&&
           pane.fileCommandReveal.tab==2&&
           pane.fileCommandReveal.target==L"retained-item"&&
           pane.fileCommandReveal.afterRefresh);
    assert(pane.groupTabCache.route()==activeRoute&&
           pane.groupTabCache.tab()==2&&pane.groupTabCache.enabled()&&
           pane.groupTabCache.isCollapsed(L"active section"));
    assert(pane.groupCollapse.matches(activeRoute,2,0)&&
           pane.groupCollapse.isCollapsed(L"active section"));
    // Neither an old worker's ticket nor old tab index may become current.
    assert(pane.metadataTab==3&&pane.tab==3);
    assert(!pane.acceptsMetadata(oldMetadata,activeRoute,2));
    assert(!pane.accepts(oldDetail,activeRoute,2));
    const auto renewedMetadata=pane.beginMetadata(activeRoute,2);
    const auto renewedDetail=pane.begin(activeRoute,2);
    assert(renewedMetadata!=oldMetadata&&renewedDetail!=oldDetail);
    assert(pane.acceptsMetadata(renewedMetadata,activeRoute,2));
    assert(pane.accepts(renewedDetail,activeRoute,2));
    pane.groupTabCache.switchTo(savedRoute,1,0);
    assert(pane.groupTabCache.pending()&&!pane.groupTabCache.enabled());
    assert(pane.groupTabCache.onCompleteModel(true,true));
    assert(pane.groupTabCache.mode()==fxfile::filegroup::Mode::Name&&
           pane.groupTabCache.isCollapsed(L"saved section"));
    // Removing an active route must forget its worker and reveal identity.
    fxfile::previewlist::PaneState removed;
    removed.visibleRoute=activeRoute;
    removed.visibleTab=1;
    removed.beginMetadata(activeRoute,1);
    removed.begin(activeRoute,1);
    removed.fileCommandReveal.route=activeRoute;
    removed.fileCommandReveal.tab=1;
    removed.fileCommandReveal.target=L"stale";
    removed.groupTabCache.switchTo(activeRoute,1,0);
    removed.groupTabCache.choose(fxfile::filegroup::Mode::Name);
    removed.groupCollapse=removed.groupTabCache.collapse();
    removed.onTabClosed(1,activeRoute,0);
    assert(removed.visibleRoute==0);
    assert(removed.metadataRoute==0&&removed.route==0);
    assert(removed.fileCommandReveal.route==0&&
           removed.fileCommandReveal.target.empty());
    assert(removed.groupTabCache.route()==0&&
           !removed.groupTabCache.enabled()&&!removed.groupTabCache.pending());
    assert(!removed.groupCollapse.matches(activeRoute,1,0));
    std::cout<<"F05_PANE_TAB_REBASE_NATIVE_PASS\n";
    std::cout<<"F05_NATIVE_PER_TAB_GROUPING_PASS\n";
}
