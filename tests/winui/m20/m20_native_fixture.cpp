// Owned synthetic model contracts; no real user directory traversal.
#include "../../../src/base/explorer_ui_state.h"
#include "../../../app/winui/workspace_restore_coordinator.h"
#include "../../../src/base/bookmark_store.h"
#include "../../../src/base/filter_rule_store.h"
#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <set>
#include <string>
#include <vector>
using namespace fxfile::explorerui;
namespace {
bool writeOwned(std::wstring const& path, void const* data, DWORD size) {
 HANDLE h=::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,
                        FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE)return false;
 DWORD written=0;
 const bool good=::WriteFile(h,data,size,&written,nullptr)!=FALSE&&written==size;
 ::CloseHandle(h);
 return good;
}
}
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

 using BookmarkStore=fxfile::bookmarks::Store;
 using BookmarkResult=fxfile::bookmarks::MutationResult;
 wchar_t tempBase[MAX_PATH]{};
 std::wstring bookmarkRoot;
 const auto tempLength=::GetTempPathW(MAX_PATH,tempBase);
 if(tempLength&&tempLength<MAX_PATH){
  bookmarkRoot=std::wstring(tempBase)+L"fly-bookmark-native-"+
               std::to_wstring(::GetCurrentProcessId());
  ::CreateDirectoryW(bookmarkRoot.c_str(),nullptr);
 }
 BookmarkStore bookmarks;
 const DWORD bookmarkAttrs=bookmarkRoot.empty()?INVALID_FILE_ATTRIBUTES:
      ::GetFileAttributesW(bookmarkRoot.c_str());
 const bool ownedTemp=bookmarkAttrs!=INVALID_FILE_ATTRIBUTES&&
      (bookmarkAttrs&FILE_ATTRIBUTE_DIRECTORY);
 check(ownedTemp&&bookmarks.items().empty(),"bookmark_owned_temp_and_empty");
 check(bookmarks.add(L"한글 즐겨찾기",L"C:\\Alpha")==BookmarkResult::Applied&&
       bookmarks.items().size()==1,"bookmark_add_utf16");
 check(bookmarks.add(L"중복",L"c:/alpha")==BookmarkResult::Duplicate&&
       bookmarks.items().size()==1,"bookmark_case_insensitive_duplicate");
 check(bookmarks.add(L"상대",L"relative\\path")==BookmarkResult::Invalid,
       "bookmark_reject_relative_path");
 check(bookmarks.rename(0,L"이름 변경")==BookmarkResult::Applied&&
       bookmarks.items()[0].name==L"이름 변경","bookmark_rename");

 const auto bookmarkFile=bookmarkRoot+L"\\bookmarks.txt";
 BookmarkStore reloaded;
 check(ownedTemp&&bookmarks.saveTo(bookmarkFile)&&
       reloaded.loadFrom(bookmarkFile)&&reloaded.items().size()==1&&
       reloaded.items()[0].path==L"C:\\Alpha",
       "bookmark_atomic_save_reload");

 const auto corruptFile=bookmarkRoot+L"\\corrupt.txt";
 const char corrupt[]="schema=9\r\nbad";
 const auto beforeCorrupt=reloaded.items().size();
 check(writeOwned(corruptFile,corrupt,sizeof(corrupt)-1)&&
       !reloaded.loadFrom(corruptFile)&&
       reloaded.items().size()==beforeCorrupt,
       "bookmark_corrupt_load_preserves_model");

 const auto importedDir=bookmarkRoot+L"\\가져온폴더";
 ::CreateDirectoryW(importedDir.c_str(),nullptr);
 const auto legacyFile=bookmarkRoot+L"\\legacy.conf";
 const std::wstring legacy=
     L"[bookmark]\r\nbookmark.item1.name=가져온 북마크\r\n"
     L"bookmark.item1.path="+importedDir+
     L"\r\nbookmark.item2.name=중복\r\n"
     L"bookmark.item2.path=c:/alpha\r\n";
 std::vector<unsigned char> legacyBytes(2+legacy.size()*sizeof(wchar_t));
 legacyBytes[0]=0xff;legacyBytes[1]=0xfe;
 std::memcpy(legacyBytes.data()+2,legacy.data(),legacy.size()*sizeof(wchar_t));
 const bool legacyWritten=writeOwned(
     legacyFile,legacyBytes.data(),static_cast<DWORD>(legacyBytes.size()));
 const auto importedResult=reloaded.importLegacy(legacyFile);
 check(legacyWritten&&importedResult.loaded&&importedResult.added==1&&
       importedResult.skipped==1&&reloaded.items().size()==2,
       "bookmark_explicit_legacy_import");
 check(reloaded.erase(0)&&reloaded.items().size()==1&&
       reloaded.items()[0].name==L"가져온 북마크",
       "bookmark_delete");

 BookmarkStore capacity;
 bool filled=true;
 for(std::size_t i=0;i<BookmarkStore::kMaxItems;++i){
  if(capacity.add(L"항목 "+std::to_wstring(i),
                  L"C:\\Cap\\"+std::to_wstring(i))!=BookmarkResult::Applied){
   filled=false;break;
  }
 }
 check(filled&&capacity.items().size()==BookmarkStore::kMaxItems&&
       capacity.add(L"초과",L"C:\\Cap\\overflow")==BookmarkResult::Full,
       "bookmark_bounded_100_items");

 using FilterStore=fxfile::filterrules::Store;
 using FilterResult=fxfile::filterrules::MutationResult;
 FilterStore filters;
 check(filters.items().empty(),"filter_rule_empty_store");
 check(filters.add(L"코드 파일",L" *.cpp ; *.h ")==FilterResult::Applied&&
       filters.items().size()==1&&filters.items()[0].masks==L"*.cpp;*.h",
       "filter_rule_add_and_normalize");
 check(filters.add(L"코드 파일",L"*.txt")==FilterResult::Duplicate,
       "filter_rule_duplicate_name_rejected");
 check(filters.add(L"잘못됨",L"*.cpp;;*.h")==FilterResult::Invalid,
       "filter_rule_reject_empty_mask");
 check(FilterStore::matches(L"Quarterly-REPORT.txt",L"report")&&
       !FilterStore::matches(L"Quarterly-REPORT.txt",L"photo"),
       "filter_rule_literal_substring_compat");
 check(FilterStore::matches(L"sample.CPP",L"*.cpp;*.h")&&
       FilterStore::matches(L"sample.h",L"*.cpp;*.h")&&
       !FilterStore::matches(L"sample.txt",L"*.cpp;*.h"),
       "filter_rule_wildcard_set_case_insensitive");
 check(FilterStore::matches(L"photo1.JPG",L"photo?.jpg")&&
       !FilterStore::matches(L"photo10.JPG",L"photo?.jpg"),
       "filter_rule_question_wildcard");
 check(filters.update(0,L"문서",L"*.txt;*.md")==FilterResult::Applied&&
       filters.items()[0].name==L"문서"&&
       filters.items()[0].masks==L"*.txt;*.md",
       "filter_rule_update");

 const auto filterFile=bookmarkRoot+L"\\filter-rules.txt";
 FilterStore filterReloaded;
 check(filters.saveTo(filterFile)&&filterReloaded.loadFrom(filterFile)&&
       filterReloaded.items().size()==1&&
       filterReloaded.items()[0].name==L"문서"&&
       filterReloaded.items()[0].masks==L"*.txt;*.md",
       "filter_rule_atomic_save_reload");

 check(filters.update(0,L"문서",L"*.txt;*.md",2,3)==FilterResult::Applied&&
       filters.items()[0].color==2&&filters.items()[0].icon==3,
       "filter_rule_color_icon_bounded_choices");
 check(filters.update(0,L"문서",L"*.txt;*.md",9,0)==FilterResult::Invalid&&
       filters.items()[0].color==2&&filters.items()[0].icon==3,
       "filter_rule_invalid_style_does_not_mutate");
 FilterStore styledReloaded;
 check(filters.saveTo(filterFile)&&styledReloaded.loadFrom(filterFile)&&
       styledReloaded.items().size()==1&&
       styledReloaded.items()[0].color==2&&styledReloaded.items()[0].icon==3,
       "filter_rule_v2_styled_atomic_reload");
 const auto filterCorrupt=bookmarkRoot+L"\\filter-corrupt.txt";
 const char filterBad[]="schema=9\r\nbad";
 const auto filterBefore=filterReloaded.items().size();
 check(writeOwned(filterCorrupt,filterBad,sizeof(filterBad)-1)&&
       !filterReloaded.loadFrom(filterCorrupt)&&
       filterReloaded.items().size()==filterBefore,
       "filter_rule_corrupt_load_preserves_model");
 check(filterReloaded.erase(0)&&filterReloaded.items().empty(),
       "filter_rule_delete");
 const char badStyle[]="schema=2\r\nA\t*.cpp\t8\t0\r\n";
 const auto previousColor=styledReloaded.items()[0].color;
 check(writeOwned(filterCorrupt,badStyle,sizeof(badStyle)-1)&&
       !styledReloaded.loadFrom(filterCorrupt)&&
       styledReloaded.items()[0].color==previousColor,
       "filter_rule_v2_invalid_style_fail_closed");

 FilterStore filterCapacity;
 bool filterFilled=true;
 for(std::size_t i=0;i<FilterStore::kMaxItems;++i){
  if(filterCapacity.add(L"규칙 "+std::to_wstring(i),
       L"*.x"+std::to_wstring(i))!=FilterResult::Applied){
   filterFilled=false;break;
  }
 }
 check(filterFilled&&
       filterCapacity.items().size()==FilterStore::kMaxItems&&
       filterCapacity.add(L"초과",L"*.overflow")==FilterResult::Full,
       "filter_rule_bounded_20_items");

 ::DeleteFileW(filterFile.c_str());
 ::DeleteFileW(filterCorrupt.c_str());
 ::DeleteFileW(bookmarkFile.c_str());
 ::DeleteFileW(corruptFile.c_str());
 ::DeleteFileW(legacyFile.c_str());
 ::RemoveDirectoryW(importedDir.c_str());
 ::RemoveDirectoryW(bookmarkRoot.c_str());

 std::printf("M20_NATIVE_SUMMARY %d passed, %d failed.\n",passed,failed);
 return failed?1:0;
}
