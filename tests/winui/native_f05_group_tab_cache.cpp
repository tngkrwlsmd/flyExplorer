#include "../../app/winui/file_group_tab_cache.h"
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
    std::cout<<"F05_NATIVE_PER_TAB_GROUPING_PASS\n";
}
