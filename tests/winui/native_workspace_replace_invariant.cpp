// Focused native regression for the workspace restore validation boundary.
// This fixture never opens folders, modifies user files, or creates UI windows.
// It must be compiled/run separately before claiming C++ runtime acceptance.
#include "../../app/winui/window_workspace_controller.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <utility>
#include <vector>

using fxfile::previewtabs::WindowTabState;
using fxfile::previewtabs::WindowWorkspaceController;

int main()
{
    WindowWorkspaceController controller;
    std::vector<WindowTabState> valid;
    valid.emplace_back(7);
    valid.emplace_back(8);
    assert(valid[0].model.invariant());
    assert(valid[1].model.invariant());
    assert(controller.replace(std::move(valid),1));
    assert(controller.count()==2);
    assert(controller.activeIndex()==1);
    assert(controller.active().identity==8);

    auto rejectedWithoutMutation=[&controller](
        std::vector<WindowTabState>&& proposed) {
        const auto oldCount=controller.count();
        const auto oldActive=controller.activeIndex();
        const auto oldIdentity=controller.active().identity;
        assert(!controller.replace(std::move(proposed),0));
        assert(controller.count()==oldCount);
        assert(controller.activeIndex()==oldActive);
        assert(controller.active().identity==oldIdentity);
    };

    {
        std::vector<WindowTabState> bad;
        bad.emplace_back(9);
        bad[0].model.panes[0].routeIds.clear();
        assert(!bad[0].model.invariant());
        rejectedWithoutMutation(std::move(bad));
    }
    {
        std::vector<WindowTabState> bad;
        bad.emplace_back(9);
        bad[0].model.panes[1].pending.clear();
        assert(!bad[0].model.invariant());
        rejectedWithoutMutation(std::move(bad));
    }
    {
        std::vector<WindowTabState> bad;
        bad.emplace_back(9);
        bad[0].model.panes[0].filesystemPaths.clear();
        assert(!bad[0].model.invariant());
        rejectedWithoutMutation(std::move(bad));
    }
    {
        std::vector<WindowTabState> bad;
        bad.emplace_back(9);
        bad[0].model.panes[0].active=bad[0].model.panes[0].tabs.size();
        assert(!bad[0].model.invariant());
        rejectedWithoutMutation(std::move(bad));
    }
    {
        std::vector<WindowTabState> bad;
        bad.emplace_back(9);
        bad[0].model.split=false;
        bad[0].model.activePane=1;
        assert(!bad[0].model.invariant());
        rejectedWithoutMutation(std::move(bad));
    }

    // Split-off restores with left-pane activation are valid; rejecting the
    // above malformed state must not reject an ordinary unsplit workspace.
    std::vector<WindowTabState> unsplit;
    unsplit.emplace_back(10);
    unsplit[0].model.split=false;
    assert(unsplit[0].model.invariant());
    assert(controller.replace(std::move(unsplit),0));
    assert(controller.count()==1);
    assert(controller.activeIndex()==0);
    assert(controller.active().identity==10);

    // The live sort survives removal of an inactive PaneTab before it.
    using fxfile::explorerui::Command;
    WindowWorkspaceController tabs;
    const auto middle=tabs.dispatch(Command::AddTab,0);
    const auto tail=tabs.dispatch(Command::AddTab,0);
    assert(middle.accepted&&tail.accepted);
    assert(tabs.dispatch(Command::SelectTab,0,1).accepted);
    tabs.active().fileLists[0].sortMode=6;
    const auto activeRoute=tabs.active().model.panes[0].routeIds[1];
    auto& list=tabs.active().fileLists[0];
    list.visibleRoute=activeRoute;
    list.visibleTab=1;
    list.metadataRoute=activeRoute;
    list.metadataTab=1;
    list.route=activeRoute;
    list.tab=1;
    list.fileCommandReveal.route=activeRoute;
    list.fileCommandReveal.tab=1;
    list.fileCommandReveal.target=L"owned-reveal";
    list.groupTabCache.switchTo(activeRoute,1,0);
    list.groupTabCache.choose(fxfile::filegroup::Mode::Name);
    assert(list.groupTabCache.toggle(L"A-F"));
    list.groupCollapse=list.groupTabCache.collapse();
    const auto activePane=tabs.active().model.activePane;
    const auto removedBackground=tabs.dispatch(Command::CloseTabAt,0,0);
    assert(removedBackground.accepted);
    assert(tabs.active().model.panes[0].active==0);
    assert(tabs.active().model.panes[0].routeIds[0]==activeRoute);
    assert(tabs.active().model.activePane==activePane);
    assert(tabs.active().fileLists[0].sortMode==6);
    assert(tabs.active().tabSortModes[0].size()==2);
    assert(tabs.active().tabSortModes[0][0]==6);
    assert(list.visibleRoute==activeRoute&&list.visibleTab==0);
    assert(list.groupTabCache.route()==activeRoute&&list.groupTabCache.tab()==0);
    assert(list.groupTabCache.enabled()&&
           list.groupTabCache.collapse().isCollapsed(L"A-F"));
    assert(list.groupCollapse.matches(activeRoute,0,0)&&
           list.groupCollapse.isCollapsed(L"A-F"));
    assert(list.fileCommandReveal.route==activeRoute&&
           list.fileCommandReveal.tab==0&&
           list.fileCommandReveal.target==L"owned-reveal");
    // The old request indices remain stale so new requests are scheduled
    // for index zero; an old worker never becomes a new valid completion.
    assert(list.metadataTab==1&&list.tab==1);
    assert(!list.acceptsMetadata(list.metadataEpoch,activeRoute,0));
    assert(!list.accepts(list.epoch,activeRoute,0));
    assert(tabs.active().model.invariant());
    const auto removedTail=tabs.dispatch(Command::CloseTabAt,0,1);
    assert(removedTail.accepted&&removedTail.releasedRoute==tail.createdRoute);
    assert(tabs.active().model.panes[0].active==0);
    assert(tabs.active().fileLists[0].sortMode==6);
    assert(tabs.active().tabSortModes[0].size()==1);
    assert(!tabs.dispatch(Command::CloseTabAt,0,0).accepted);
    assert(!tabs.dispatch(Command::CloseTabAt,0,42).accepted);

    std::cout<<"WORKSPACE_REPLACE_INVARIANT_NATIVE_PASS\n";
}
