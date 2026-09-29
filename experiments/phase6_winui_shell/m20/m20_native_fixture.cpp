// Owned synthetic model contracts; no real user directory traversal.
#include "../../../src/base/explorer_ui_state.h"
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
