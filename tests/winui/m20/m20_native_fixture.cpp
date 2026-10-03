// Owned synthetic model contracts; no real user directory traversal.
#include "../../../src/base/explorer_ui_state.h"
#include "../../../app/winui/workspace_restore_coordinator.h"
#include <cstdio>
#include <cstdint>
#include <set>
using namespace fxfile::explorerui;
int main(){
 int passed=0,failed=0;
 auto check=[&](bool value,char const* label){
  std::printf("M20_NATIVE_%s %s\n",value?"PASS":"FAIL",label);
  if(value)++passed;else ++failed;
 };
 Model state;
 check(state.invariant()&&state.split&&state.activePane==0&&
       state.panes[0].tabs.size()==1&&state.panes[1].tabs.size()==1,
       "two_pane_one_tab_start");
 const auto left=state.panes[0].routeIds[0];
 const auto right=state.panes[1].routeIds[0];
 check(left>0&&right>left,"distinct_native_per_lane_routes");
 check(!state.dispatch(Command::ActivatePane,2).accepted&&state.invariant(),
       "reject_unknown_pane");
 check(state.dispatch(Command::ActivatePane,1).accepted&&state.activePane==1,
       "activate_second_pane");
 check(state.dispatch(Command::ToggleSplit).accepted&&!state.split&&
       state.activePane==0&&state.panes[1].routeIds[0]==right&&
       !state.dispatch(Command::ActivatePane,1).accepted,
       "hide_right_without_losing_independent_state");
 check(state.dispatch(Command::ToggleSplit).accepted&&state.split&&
       state.panes[1].routeIds[0]==right,"restore_right_lane_without_reuse");
 const auto added=state.dispatch(Command::AddTab,0);
 check(added.accepted&&added.createdRoute>right&&
       state.panes[0].tabs.size()==2&&state.panes[0].active==1,
       "native_add_tab_unique_route");
 check(state.markPending(0,1,200,true)&&
       !state.completeRequest(0,1,added.createdRoute,199)&&
       state.completeRequest(0,1,added.createdRoute,200),
       "native_requested_completion_matching");
 check(state.markPending(0,1,201,true)&&
       state.markPending(0,1,202,true)&&
       !state.completeRequest(0,1,added.createdRoute,201)&&
       state.completeRequest(0,1,added.createdRoute,202),
       "same_lane_newer_request_wins");
 check(state.markPending(1,0,44,false)&&
       state.markPending(0,1,45,true)&&
       state.completeRequest(1,0,right,44)&&
       state.completeRequest(0,1,added.createdRoute,45),
       "right_left_pending_independent");
 const auto removed=state.dispatch(Command::CloseTab,0);
 check(removed.accepted&&removed.releasedRoute==added.createdRoute&&
       !state.completeRequest(0,0,added.createdRoute,45)&&state.invariant(),
       "close_rejects_old_route_callbacks");
 check(!state.dispatch(Command::CloseTab,0).accepted&&
       state.panes[0].routeIds[0]==left,
       "cannot_close_last_tab");

 using Restore=fxfile::previewrestore::WorkspaceRestoreCoordinator;
 Restore restore;
 restore.begin(0,{{1,L"one"},{2,L"two"}},500);
 check(restore.active(0)&&restore.queued(0)==2&&
       !restore.takeNext(0,false,3).has_value(),
       "restore_waits_for_initial_request");
 check(!restore.settle(0,499)&&restore.active(0)&&
       restore.queued(0)==2,
       "restore_wrong_request_does_not_advance");
 check(restore.settle(0,500),"restore_failure_settle_allows_next");
 auto firstRestore=restore.takeNext(0,false,3);
 check(firstRestore&&firstRestore->tab==1&&firstRestore->path==L"one"&&
       restore.track(0,501),
       "restore_tracks_first_inactive_tab");
 check(!restore.takeNext(0,false,3).has_value()&&
       restore.settle(0,501),
       "restore_waits_for_matching_inactive_completion");
 auto secondRestore=restore.takeNext(0,false,3);
 check(secondRestore&&secondRestore->tab==2&&secondRestore->path==L"two"&&
       restore.track(0,502)&&restore.settle(0,502)&&
       !restore.active(0),
       "restore_continues_after_each_settled_request");
 restore.begin(0,{{99,L"stale"},{1,L"valid"}},0);
 auto skipped=restore.takeNext(0,false,2);
 check(skipped&&skipped->tab==1&&skipped->path==L"valid",
       "restore_skips_invalid_tab_index");
 restore.begin(0,{{1,L"old"}},600);
 restore.reset(0);
 check(!restore.settle(0,600)&&!restore.active(0),
       "restore_reset_rejects_stale_completion");
 restore.begin(0,{{1,L"left"}},700);
 restore.begin(1,{{1,L"right"}},800);
 check(restore.settle(0,700)&&restore.active(1)&&
       !restore.takeNext(1,false,2).has_value()&&
       restore.settle(1,800),
       "restore_two_lanes_are_independent");
 restore.begin(0,{{1,L"retry"}},0);
 check(!restore.takeNext(0,true,2).has_value()&&
       restore.takeNext(0,false,2).has_value(),
       "restore_submit_failure_or_busy_can_resume");

 check(!state.dispatch(Command::SelectTab,0,33).accepted&&
       state.dispatch(Command::SelectTab,1,0).accepted&&state.activePane==1,
       "validate_tab_range_and_selection");
 const auto before=state.panes[0].routeIds[0];
 check(!state.reset(true,{{0,1}},{{0,0}})&&
       state.panes[0].routeIds[0]==before,
       "invalid_workspace_reset_is_atomic");
 check(state.reset(true,{{2,1}},{{1,0}})&&
       state.panes[0].active==1&&state.panes[0].routeIds[0]>added.createdRoute&&
       !state.completeRequest(0,0,before,99)&&state.invariant(),
       "valid_workspace_reset_assigns_fresh_monotonic_routes");
 while(state.panes[0].tabs.size()<kMaxTabsPerPane)
  if(!state.dispatch(Command::AddTab,0).accepted)break;
 check(state.panes[0].tabs.size()==kMaxTabsPerPane&&
       !state.dispatch(Command::AddTab,0).accepted,
       "bounded_max_32_tabs");
 std::printf("M20_NATIVE_SUMMARY %d passed, %d failed.\n",passed,failed);
 return failed?1:0;
}
