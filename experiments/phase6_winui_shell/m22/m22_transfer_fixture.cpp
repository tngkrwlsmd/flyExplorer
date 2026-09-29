#include "../../../src/base/shell_transfer_core.h"
#include <filesystem>
#include <fstream>
#include <cstdio>
using namespace fxfile::shelltransfer;
namespace fs=std::filesystem;
int wmain(int count,wchar_t**args){
 setvbuf(stdout,nullptr,_IONBF,0);
 if(count!=2)return 2;
 const fs::path root(args[1]),left=root/L"왼쪽",right=root/L"오른쪽";
 fs::create_directory(left);fs::create_directory(right);
 int pass=0,fail=0;
 auto test=[&](bool ok,char const*label){
  std::printf("M22_NATIVE_%s %s\n",ok?"PASS":"FAIL",label);
  if(ok)++pass;else ++fail;
 };
 auto put=[](fs::path const&p,std::string const&s){
  std::ofstream f(p,std::ios::binary);f<<s;
 };
 auto get=[](fs::path const&p){
  std::ifstream f(p,std::ios::binary);
  return std::string(std::istreambuf_iterator<char>(f),{});
 };
 put(left/L"자료.txt","old");
 Request r;Progress progress;r.kind=Kind::Copy;
 r.sourceParent=left.native();r.destination=right.native();
 r.sources={(left/L"자료.txt").native()};
 test(validate(r).error==0&&validate(r).queued==1,"local_ko_preflight");
 auto done=execute(r,progress);
 test(done.error==0&&get(right/L"자료.txt")=="old"&&
      get(left/L"자료.txt")=="old","actual_ifileoperation_korean_copy");
 test(progress.percent==100,"copy_progress_complete");
 test(validate(r).error==ERROR_ALREADY_EXISTS&&
      validate(r).collisions.size()==1,"detect_collision_without_mutation");
 test(execute(r,progress).error==ERROR_ALREADY_EXISTS,
      "reject_unconfirmed_conflict");
 put(right/L"자료.txt","preserve_me");
 r.collision=Collision::KeepBoth;
 auto keep=execute(r,progress);
 size_t copies=0;
 for(auto const& item:fs::directory_iterator(right))
  if(item.path().filename().native().find(L"자료")!=std::wstring::npos)++copies;
 test(keep.error==0&&copies>=2&&get(right/L"자료.txt")=="preserve_me",
      "keep_both_never_overwrites");
 put(left/L"이동.txt","moving");
 r.kind=Kind::Move;r.collision=Collision::Reject;
 r.sources={(left/L"이동.txt").native()};
 auto moving=execute(r,progress);
 test(moving.error==0&&!fs::exists(left/L"이동.txt")&&
      get(right/L"이동.txt")=="moving","actual_ifileoperation_korean_move");
 put(left/L"가.txt","one");put(left/L"나.txt","two");
 r.kind=Kind::Copy;r.sources={(left/L"가.txt").native(),(left/L"나.txt").native()};
 auto multi=execute(r,progress);
 test(multi.error==0&&get(right/L"가.txt")=="one"&&
      get(right/L"나.txt")=="two","actual_multi_selection_copy");
 auto safe=r;
 r.sources.push_back(r.sources[0]);
 test(validate(r).error==ERROR_INVALID_PARAMETER,"reject_duplicate_source");
 r=safe;r.sources={L"C:\\other\\untrusted.txt"};
 test(validate(r).error!=0,"reject_outside_original_parent");
 r=safe;r.kind=Kind::Move;r.destination=left.native();
 test(validate(r).error==ERROR_INVALID_PARAMETER,"reject_same_folder_move");
 r.kind=Kind::Copy;r.destination=L"shell:MyComputerFolder";
 test(validate(r).error==ERROR_INVALID_NAME,"reject_virtual_destination");
 r=safe;r.kind=Kind::Recycle;r.destination.clear();
 test(validate(r).error==ERROR_CANCELLED,"recycle_requires_explicit_consent");
 r.recycleConfirmed=true;
 test(validate(r).error==0,"validate_recycle_only_no_real_recycle_bin_mutation");
 r=safe;r.destination=(root/L"새 대상").native();
 fs::create_directory(root/L"새 대상");
 Progress canceled;canceled.cancel=true;
 auto no=execute(r,canceled);
 test(no.aborted&&no.error==ERROR_CANCELLED&&
      !fs::exists(root/L"새 대상"/L"가.txt"),"cancellation_before_staging");
 fs::create_directory(left/L"중첩");
 r.sources={(left/L"중첩").native()};r.destination=(left/L"중첩").native();
 test(validate(r).error!=0,"reject_recursive_folder_copy");
 r=safe;r.sources.clear();
 test(validate(r).error==ERROR_INVALID_PARAMETER,"reject_empty_selection");
 r=safe;r.sources.assign(33,(left/L"가.txt").native());
 test(validate(r).error==ERROR_INVALID_PARAMETER,"max_32_selected_items");
 std::printf("M22_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
