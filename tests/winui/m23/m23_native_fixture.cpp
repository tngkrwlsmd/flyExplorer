#include "../../../src/base/shell_clipboard_core.h"
#include "../../../src/base/ui_session.h"
#include "../../../src/base/shell_transfer_core.h"
#include <windows.h>
#include <shellapi.h>
#include <shlobj.h>
#include <filesystem>
#include <fstream>
#include <cstdio>
using namespace fxfile;
namespace fs=std::filesystem;
int wmain(int argc,wchar_t**argv){
 setvbuf(stdout,nullptr,_IONBF,0);
 if(argc!=2)return 2;
 fs::path root(argv[1]),left=root/L"왼쪽",right=root/L"오른쪽";
 fs::create_directory(left);fs::create_directory(right);
 int pass=0,fail=0;
 auto check=[&](bool ok,char const*why){
  std::printf("M23_%s %s\n",ok?"PASS":"FAIL",why);
  if(ok)++pass;else ++fail;
 };
 auto first=left/L"한글 파일.txt",second=left/L"두 번째.txt";
 std::ofstream(first,std::ios::binary)<<"first";
 std::ofstream(second,std::ios::binary)<<"second";
 shellclipboard::Payload payload;
 payload.paths={first.native(),second.native()};
 check(shellclipboard::valid(payload),"bounded_korean_paths");
 std::vector<unsigned char> bytes;
 check(shellclipboard::encode(payload,bytes)&&
   bytes.size()>sizeof(DROPFILES)&&bytes.size()<=65536,
   "real_cf_hdrop_wire_serialization");
 shellclipboard::Payload restored;
 check(shellclipboard::decode(bytes.data(),bytes.size(),restored)&&
   restored.paths==payload.paths&&!restored.move,
   "korean_os_clipboard_wire_roundtrip_in_memory_only");
 auto const* drop=reinterpret_cast<DROPFILES const*>(bytes.data());
 check(drop->fWide&&drop->pFiles==sizeof(DROPFILES),
   "windows_explorer_compatible_utf16_cf_hdrop_layout");
 auto invalid=bytes;
 reinterpret_cast<DROPFILES*>(invalid.data())->fWide=FALSE;
 check(!shellclipboard::decode(invalid.data(),invalid.size(),restored),
   "reject_legacy_ansi_payload");
 invalid=bytes;
 reinterpret_cast<DROPFILES*>(invalid.data())->pFiles=1;
 check(!shellclipboard::decode(invalid.data(),invalid.size(),restored),
   "reject_unaligned_untrusted_offset");
 invalid=bytes;
 invalid.pop_back();
 check(!shellclipboard::decode(invalid.data(),invalid.size(),restored),
   "reject_odd_byte_payload");
 invalid=bytes;
 invalid.resize(invalid.size()-sizeof(wchar_t));
 check(!shellclipboard::decode(invalid.data(),invalid.size(),restored),
   "reject_missing_second_terminal_unicode_null");
 check(!shellclipboard::decode(bytes.data(),sizeof(DROPFILES),restored),
   "reject_missing_terminal_double_null");
 payload.move=true;
 check(shellclipboard::encode(payload,bytes),"requested_cut_can_encode");
 payload.paths.push_back(first.native());
 check(!shellclipboard::encode(payload,bytes),"reject_duplicate_file_paths");
 payload.paths={L"..\\relative.txt"};
 check(!shellclipboard::valid(payload),"reject_relative_file_path");
 payload.paths.assign(33,first.native());
 check(!shellclipboard::encode(payload,bytes),"limit_32_items");
 payload.paths={first.native(),second.native()};
 check(shellclipboard::encode(payload,bytes),"restore_valid_two_files");
 shelltransfer::Request request;
 request.kind=shelltransfer::Kind::Copy;
 request.sourceParent=left.native();request.destination=right.native();
 request.sources=payload.paths;
 check(shelltransfer::validate(request).error==0,
   "clipboard_files_reuse_strict_native_shell_validation");
 shelltransfer::Progress prog;
 auto done=shelltransfer::execute(request,prog);
 check(done.error==0&&fs::exists(right/first.filename())&&
   fs::exists(right/second.filename()),"actual_owned_korean_two_file_shell_copy");
 prog.cancel=true;
 request.destination=(root/L"다른 폴더").native();
 fs::create_directory(root/L"다른 폴더");
 done=shelltransfer::execute(request,prog);
 check(done.aborted&&done.error==ERROR_CANCELLED&&
   !fs::exists(root/L"다른 폴더"/first.filename()),
   "cancel_before_transfer_preserves_destination");
 // Intentionally NEVER call shellclipboard::write/read in automated
 // tests: the system clipboard belongs to the user, not to the fixture.

 // Private opt-in session is validated against existing test-owned local
 // directories only. Never write/read real user's original profile.
 uisession::Session session{};
 session.split=true;
 session.paths[0]={left.native()};
 session.paths[1]={right.native()};
 session.width=1240;session.height=810;
 session.sort={{2,3}};
 session.selected={{0,0}};
 check(uisession::valid(session),
       "private_session_existing_owned_local_korean_paths");
 check(uisession::save(session),"atomic_private_session_save");
 uisession::Session restoredSession{};
 check(uisession::load(restoredSession)&&
       restoredSession.paths==session.paths&&
       restoredSession.sort==session.sort&&
       restoredSession.width==session.width&&
       restoredSession.height==session.height,
       "korean_session_roundtrip_size_sort_both_panes");
 uisession::Session multi{};
 multi.width=1280;multi.height=820;multi.activeWindow=1;
 uisession::WindowTab window1{};
 window1.split=true;window1.splitPermille=560;window1.activeSide=1;
 window1.panes[0].selected=0;window1.panes[0].sort=6;window1.panes[0].view=3;
 window1.panes[0].nameColumnWidth=176;
 window1.panes[0].tabs.push_back({left.native(),{},{right.native()}});
 window1.panes[1].tabs.push_back({right.native(),{left.native()},{}});
 auto window2=window1;window2.split=false;window2.activeSide=0;window2.splitPermille=430;
 window2.panes[0].view=2;window2.panes[0].sort=7;
 window2.panes[0].tabs[0].path=right.native();
 window2.panes[1].tabs[0].path=left.native();
 multi.windowTabs={window1,window2};
 check(uisession::valid(multi),"v7_multi_window_session_valid");
 check(uisession::save(multi),"v7_multi_window_session_save_v2");
 uisession::Session restoredV2{};
 check(uisession::load(restoredV2)&&restoredV2.windowTabs.size()==2&&
       restoredV2.activeWindow==1&&restoredV2.windowTabs[0].activeSide==1&&
       restoredV2.windowTabs[0].panes[0].view==3&&
       restoredV2.windowTabs[1].split==false&&
       restoredV2.windowTabs[1].panes[0].sort==7&&
       restoredV2.windowTabs[0].panes[0].tabs[0].forward.size()==1,
       "v7_multi_window_session_roundtrip_history_view_sort_split");

 auto rejectedSession=session;
 rejectedSession.width=10;
 check(!uisession::save(rejectedSession),
       "reject_out_of_bounds_window_without_overwrite");
 rejectedSession=session;
 rejectedSession.paths[0]={L"C:\\outside-m23-do-not-enumerate"};
 check(!uisession::valid(rejectedSession),
       "reject_unowned_or_nonexistent_session_folder");
 rejectedSession=session;
 rejectedSession.paths[0].assign(9,left.native());
 check(!uisession::valid(rejectedSession),
       "reject_more_than_eight_tabs_per_pane");
 rejectedSession=session;
 rejectedSession.sort[0]=99;
 check(!uisession::valid(rejectedSession),
       "reject_unrecognized_saved_sort_mode");
 check(uisession::clear(),
       "delete_only_explicit_private_session_file");
 uisession::Session empty{};
 check(!uisession::load(empty),
       "cleared_session_is_not_implicitly_restored");
 std::printf("M23_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
