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

    std::cout<<"WORKSPACE_REPLACE_INVARIANT_NATIVE_PASS\n";
}
