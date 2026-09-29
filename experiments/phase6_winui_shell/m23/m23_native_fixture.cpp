#include "../../../src/base/shell_clipboard_core.h"
#include "../../../src/base/preview_session.h"
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
 previewsession::Session session{};
 session.split=true;
 session.paths[0]={left.native()};
 session.paths[1]={right.native()};
 session.width=1240;session.height=810;
 session.sort={{2,3}};
 session.selected={{0,0}};
 check(previewsession::valid(session),
       "private_session_existing_owned_local_korean_paths");
 check(previewsession::save(session),"atomic_private_session_save");
 previewsession::Session restoredSession{};
 check(previewsession::load(restoredSession)&&
       restoredSession.paths==session.paths&&
       restoredSession.sort==session.sort&&
       restoredSession.width==session.width&&
       restoredSession.height==session.height,
       "korean_session_roundtrip_size_sort_both_panes");
 auto rejectedSession=session;
 rejectedSession.width=10;
 check(!previewsession::save(rejectedSession),
       "reject_out_of_bounds_window_without_overwrite");
 rejectedSession=session;
 rejectedSession.paths[0]={L"C:\\outside-m23-do-not-enumerate"};
 check(!previewsession::valid(rejectedSession),
       "reject_unowned_or_nonexistent_session_folder");
 rejectedSession=session;
 rejectedSession.paths[0].assign(9,left.native());
 check(!previewsession::valid(rejectedSession),
       "reject_more_than_eight_tabs_per_pane");
 rejectedSession=session;
 rejectedSession.sort[0]=99;
 check(!previewsession::valid(rejectedSession),
       "reject_unrecognized_saved_sort_mode");
 check(previewsession::clear(),
       "delete_only_explicit_private_session_file");
 previewsession::Session empty{};
 check(!previewsession::load(empty),
       "cleared_session_is_not_implicitly_restored");
 std::printf("M23_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
