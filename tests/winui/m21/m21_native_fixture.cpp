#include "../../../src/base/ui_preferences.h"
#include "../../../src/base/file_command_core.h"
#include <windows.h>
#include <shobjidl.h>
#include <filesystem>
#include <cstring>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <string>
using namespace fxfile;
int wmain(int argc,wchar_t**argv){
 setvbuf(stdout,nullptr,_IONBF,0);
 if(argc!=2)return 2;
 const std::filesystem::path root(argv[1]);
 int pass=0,fail=0;
 auto chk=[&](bool ok,const char*why){std::printf("M21_%s %s\n",ok?"PASS":"FAIL",why);
   if(ok)++pass;else ++fail;};
 uisettings::Preferences pref{};
 const auto config=uisettings::privatePath();
 chk(!config.empty()&&config.find(L"flyExplorer")!=std::wstring::npos,"isolated_product_profile");
 chk(!uisettings::load(pref)&&pref.language==L"ko-KR"&&
   pref.theme==uisettings::Theme::System,"korean_system_default_without_settings");
 pref.theme=uisettings::Theme::Dark;
 chk(uisettings::save(pref)&&std::filesystem::exists(config),"atomic_save_ko_dark");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Dark&&
   pref.language==L"ko-KR","reload_ko_dark");
 pref.theme=uisettings::Theme::Light;
 chk(uisettings::save(pref)&&uisettings::load(pref)&&
   pref.theme==uisettings::Theme::Light,"atomic_light_update");
 pref.language=L"en-US";
 chk(!uisettings::save(pref),"unsupported_locale_not_written");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Light&&
   pref.language==L"ko-KR","failed_save_keeps_previous_data");
 // New Ctrl+G / Ctrl+J focus choices persist in the existing schema=3
 // private store; duplicate/out-of-range choices cannot overwrite it.
 pref.addressShortcut=4;pref.searchShortcut=5;
 chk(uisettings::validFocusShortcuts(4,5)&&uisettings::save(pref),
     "extended_focus_choices_save");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Light&&
     pref.addressShortcut==4&&pref.searchShortcut==5,
     "extended_focus_choices_reload");
 pref.searchShortcut=4;
 chk(!uisettings::validFocusShortcuts(4,4)&&!uisettings::save(pref),
     "duplicate_focus_choice_rejected");
 pref.searchShortcut=6;
 chk(!uisettings::validFocusShortcuts(4,6)&&!uisettings::save(pref),
     "out_of_range_focus_choice_rejected");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.addressShortcut==4&&
     pref.searchShortcut==5,"invalid_focus_save_preserves_previous");
 const auto dir=root/L"owned-directory";
 std::filesystem::create_directory(dir);
 filecommand::Request req;
 req.parent=dir.native();req.name=L"새 폴더";
 std::printf("M21_DEBUG_KOREAN_NAME_SAFE=%d PARENT_EXISTS=%d\\n",
  (int)filecommand::validLeaf(req.name),(int)std::filesystem::is_directory(dir));
 chk(filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_SUCCESS&&
   std::filesystem::is_directory(dir/L"새 폴더"),"create_korean_folder");
 chk(filecommand::execute(req).error==ERROR_ALREADY_EXISTS,
   "never_overwrite_existing_directory");
 req.name=L"..";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_parent_traversal");
 req.name=L"CON.txt";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_reserved_device");
 // Keep Win32 console aliases and superscript COM/LPT aliases out of all
 // file-mutating commands, including device stems followed by extensions.
 bool deviceNamesRejected=true;
 for(auto const* leaf:{
      L"CONIN$",L"conout$",L"CONIN$.txt",L"CONOUT$.bak",
      L"COM\u00B9",L"com\u00B2.log",L"LPT\u00B3.txt"}){
  req.name=leaf;
  deviceNamesRejected=deviceNamesRejected&&
     !filecommand::validLeaf(req.name)&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(deviceNamesRejected,"deny_console_and_superscript_device_names");
 chk(filecommand::validLeaf(L"COM10.txt")&&
     filecommand::validLeaf(L"LPT10.txt")&&
     filecommand::validLeaf(L"문서 ¹.txt"),
     "allow_non_device_leaf_names");
 req.name=L"no/paths";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_slash");
 req.name=L"이름.";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_trailing_period");
 req.kind=filecommand::Kind::RenameSelected;
 req.source=(dir/L"새 폴더").native();req.name=L"이름 변경";
 const auto renamedFolder=filecommand::execute(req);
 chk(renamedFolder.error==ERROR_SUCCESS&&
     !renamedFolder.renameEvidence.verified&&
     std::filesystem::is_directory(dir/L"이름 변경"),"rename_owned_korean_directory");
 std::filesystem::create_directory(dir/L"대상 존재");
 req.source=(dir/L"이름 변경").native();req.name=L"대상 존재";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS&&
    std::filesystem::is_directory(dir/L"이름 변경")&&
    std::filesystem::is_directory(dir/L"대상 존재"),"rename_never_replaces_existing");
 // Rejected device destination must not rename/delete the existing
 // test-owned source directory.
 req.source=(dir/L"이름 변경").native();req.name=L"lpt\u00B9";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME&&
     std::filesystem::is_directory(dir/L"이름 변경"),
     "rename_denies_superscript_device_destination");
 req.source=(root/L"foreign-source").native();req.name=L"safe";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,"rename_source_must_be_child");
 req.parent=L"shell:MyComputerFolder";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS,"reject_virtual_folder_mutations");
 // F13: create an empty text document only, never replace existing data.
 req.parent=dir.native();req.source.clear();
 req.kind=filecommand::Kind::CreateTextFile;req.name=L"새 문서.txt";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/L"새 문서.txt")&&
     std::filesystem::file_size(dir/L"새 문서.txt")==0,
     "create_empty_unicode_text_document");
 chk(filecommand::execute(req).error!=ERROR_SUCCESS&&
     std::filesystem::file_size(dir/L"새 문서.txt")==0,
     "text_document_never_overwrites_existing");
 req.name=L"메모.TXT";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::file_size(dir/L"메모.TXT")==0,
     "text_document_case_insensitive_extension");
 // R07-2: the receipt is strictly read-only and restricted to a single
 // local, non-reparse, ordinary file; verify it against independent Win32 IDs.
 const auto srcRename=dir/L"메모.TXT";
 const auto dstRename=dir/L"메모-확인.TXT";
 { std::ofstream payload(srcRename,std::ios::binary);payload<<"owned R07 only"; }
 auto readId=[](std::filesystem::path const& path,FILE_ID_INFO& id)->bool{
  HANDLE const h=::CreateFileW(path.c_str(),FILE_READ_ATTRIBUTES,
   FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
   OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(h==INVALID_HANDLE_VALUE)return false;
  bool const ok=::GetFileInformationByHandleEx(
   h,FileIdInfo,&id,sizeof(id))!=FALSE;
  ::CloseHandle(h);
  return ok;
 };
 FILE_ID_INFO priorId{},currentId{};
 bool const priorFound=readId(srcRename,priorId);
 req.kind=filecommand::Kind::RenameSelected;
 req.source=srcRename.native();req.name=dstRename.filename().native();
 const auto renamedFile=filecommand::execute(req);
 bool const currentFound=readId(dstRename,currentId);
 chk(renamedFile.error==ERROR_SUCCESS&&renamedFile.renameEvidence.verified&&
     !std::filesystem::exists(srcRename)&&std::filesystem::exists(dstRename),
     "r07_regular_file_receipt_verified");
 bool const stableId=priorFound&&currentFound&&
     priorId.VolumeSerialNumber==currentId.VolumeSerialNumber&&
     renamedFile.renameEvidence.volumeSerial==currentId.VolumeSerialNumber&&
     std::memcmp(priorId.FileId.Identifier,currentId.FileId.Identifier,16)==0&&
     std::memcmp(renamedFile.renameEvidence.fileId.data(),
                 currentId.FileId.Identifier,16)==0;
 chk(stableId&&renamedFile.renameEvidence.fileSize==14,
     "r07_128bit_file_id_volume_and_size_match");
 using Observation=filecommand::RenameRestoreObservation;
 chk(filecommand::inspectRenameRestore(srcRename.native(),renamedFile)==
     Observation::MatchingSnapshotOnly&&
     !std::filesystem::exists(srcRename)&&std::filesystem::exists(dstRename),
     "r07_preflight_snapshot_matches_without_restoring");
 // R07-4: hold a read-only target handle and prove that competing writes
 // and renames are denied. Never use the lease to restore a real file.
 {
  filecommand::RenameTargetLease guard;
  chk(guard.begin(srcRename.native(),renamedFile)==
       Observation::MatchingSnapshotOnly&&
      guard.recheck()==Observation::MatchingSnapshotOnly,
      "r07_guard_acquires_and_rechecks_exact_identity");
  HANDLE const blockedParentDelete=::CreateFileW(
      dir.c_str(),DELETE,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,
      FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  // Directory DELETE access is not reliably excluded by this read-only
  // parent handle on all Windows filesystems. Never treat it as an Undo lock.
  if(blockedParentDelete!=INVALID_HANDLE_VALUE)::CloseHandle(blockedParentDelete);
  chk(guard.recheck()==Observation::MatchingSnapshotOnly&&
      !std::filesystem::exists(srcRename)&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_parent_delete_access_not_assumed_blocked");
  HANDLE const blockedWrite=::CreateFileW(
      dstRename.c_str(),FILE_WRITE_DATA,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  bool const writeDenied=blockedWrite==INVALID_HANDLE_VALUE&&
      ::GetLastError()==ERROR_SHARING_VIOLATION;
  if(blockedWrite!=INVALID_HANDLE_VALUE)::CloseHandle(blockedWrite);
  chk(writeDenied&&std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_competing_writer_without_change");
  HANDLE const blockedDelete=::CreateFileW(
      dstRename.c_str(),DELETE,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  bool const deleteDenied=blockedDelete==INVALID_HANDLE_VALUE&&
      ::GetLastError()==ERROR_SHARING_VIOLATION;
  if(blockedDelete!=INVALID_HANDLE_VALUE)::CloseHandle(blockedDelete);
  chk(deleteDenied&&std::filesystem::exists(dstRename),
      "r07_guard_denies_competing_delete_without_change");
  { std::ofstream occupied(srcRename,std::ios::binary);occupied<<"occupied"; }
  bool const collisionSeen=guard.recheck()==Observation::OriginalOccupiedOrUnknown&&
      std::filesystem::file_size(srcRename)==8;
  std::filesystem::remove(srcRename);
  chk(collisionSeen&&guard.recheck()==Observation::MatchingSnapshotOnly,
      "r07_guard_rechecks_reoccupied_original_without_restoring");
  guard.reset();
  HANDLE const writableAfterReset=::CreateFileW(
      dstRename.c_str(),FILE_WRITE_DATA,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  bool const resetReleased=writableAfterReset!=INVALID_HANDLE_VALUE;
  if(resetReleased)::CloseHandle(writableAfterReset);
  chk(resetReleased&&guard.recheck()==Observation::UnverifiedReceipt&&
      std::filesystem::file_size(dstRename)==14&&
      !std::filesystem::exists(srcRename),
      "r07_guard_reset_releases_lock_and_invalidates_receipt");
  HANDLE const parentAfterReset=::CreateFileW(
      dir.c_str(),DELETE,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,
      FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  bool const parentReleased=parentAfterReset!=INVALID_HANDLE_VALUE;
  if(parentReleased)::CloseHandle(parentAfterReset);
  chk(parentReleased,"r07_guard_reset_releases_parent_directory_handle");
 }
 // An existing DELETE-capable directory handle is not guaranteed to block
 // observation leases. Neither outcome is permission to restore a file.
 {
  HANDLE const priorParentDelete=::CreateFileW(
      dir.c_str(),DELETE,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,
      FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  bool observed=priorParentDelete!=INVALID_HANDLE_VALUE;
  if(observed){
   filecommand::RenameTargetLease blocked;
   auto const status=blocked.begin(srcRename.native(),renamedFile);
   observed=(status==Observation::UnsafePaths&&
             blocked.recheck()==Observation::UnverifiedReceipt)||
            (status==Observation::MatchingSnapshotOnly&&
             blocked.recheck()==Observation::MatchingSnapshotOnly);
   blocked.reset();
   ::CloseHandle(priorParentDelete);
  }
  chk(observed&&std::filesystem::file_size(dstRename)==14&&
      !std::filesystem::exists(srcRename),
      "r07_guard_preexisting_parent_delete_is_not_authority");
 }
 // An already opened writer must make exclusive lease acquisition fail.
 HANDLE const preexistingWriter=::CreateFileW(
     dstRename.c_str(),FILE_WRITE_DATA,
     FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
     nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool writerGuarded=preexistingWriter!=INVALID_HANDLE_VALUE;
 if(writerGuarded){
  filecommand::RenameTargetLease blocked;
  writerGuarded=blocked.begin(srcRename.native(),renamedFile)==
                  Observation::TargetChangedOrUnavailable&&
                blocked.recheck()==Observation::UnverifiedReceipt;
  ::CloseHandle(preexistingWriter);
 }
 { filecommand::RenameTargetLease fresh;
   writerGuarded=writerGuarded&&
      fresh.begin(srcRename.native(),renamedFile)==
          Observation::MatchingSnapshotOnly;
   fresh.reset(); }
 chk(writerGuarded&&std::filesystem::file_size(dstRename)==14,
     "r07_guard_denies_prior_writer_and_releases_cleanly");
 // R07-4: a failed lease acquisition must not retain a target lock or
 // change either file. The caller may not treat a stale receipt as authority.
 {
  { std::ofstream occupied(srcRename,std::ios::binary);occupied<<"lease collision"; }
  filecommand::RenameTargetLease denied;
  bool const rejected=denied.begin(srcRename.native(),renamedFile)==
      Observation::OriginalOccupiedOrUnknown&&
      denied.recheck()==Observation::UnverifiedReceipt;
  HANDLE const writable=::CreateFileW(dstRename.c_str(),FILE_WRITE_DATA,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
      OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  bool const released=writable!=INVALID_HANDLE_VALUE;
  if(released)::CloseHandle(writable);
  chk(rejected&&released&&std::filesystem::file_size(srcRename)==15&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_occupied_original_without_locking_target");
  std::filesystem::remove(srcRename);
 }
 {
  auto stale=renamedFile;
  stale.renameEvidence.fileId[0]^=1;
  filecommand::RenameTargetLease denied;
  chk(denied.begin(srcRename.native(),stale)==
          Observation::TargetChangedOrUnavailable&&
      denied.recheck()==Observation::UnverifiedReceipt&&
      !std::filesystem::exists(srcRename)&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_stale_identity_without_restoring");
 }
 // A forged size in an otherwise valid receipt must never authorize a lease.
 {
  auto wrongSize=renamedFile;
  ++wrongSize.renameEvidence.fileSize;
  filecommand::RenameTargetLease denied;
  chk(denied.begin(srcRename.native(),wrongSize)==
          Observation::TargetChangedOrUnavailable&&
      denied.recheck()==Observation::UnverifiedReceipt&&
      !std::filesystem::exists(srcRename)&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_forged_size_without_restoring");
 }
 // A missing renamed target must not leave a lease or recreate the source.
 {
  auto missing=renamedFile;
  missing.target=(dir/L"r07-lease-missing.txt").native();
  filecommand::RenameTargetLease denied;
  chk(denied.begin(srcRename.native(),missing)==
          Observation::TargetChangedOrUnavailable&&
      denied.recheck()==Observation::UnverifiedReceipt&&
      !std::filesystem::exists(srcRename)&&
      !std::filesystem::exists(missing.target)&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_missing_target_without_restoring");
 }
 auto unverifiedReceipt=renamedFile;
 unverifiedReceipt.renameEvidence.verified=false;
 // A receipt without verified identity must not acquire a protective lock.
 {
  filecommand::RenameTargetLease denied;
  bool const rejected=denied.begin(srcRename.native(),unverifiedReceipt)==
      Observation::UnverifiedReceipt&&
      denied.recheck()==Observation::UnverifiedReceipt;
  HANDLE const writable=::CreateFileW(dstRename.c_str(),FILE_WRITE_DATA,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
      OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  bool const released=writable!=INVALID_HANDLE_VALUE;
  if(released)::CloseHandle(writable);
  chk(rejected&&released&&!std::filesystem::exists(srcRename)&&
      std::filesystem::file_size(dstRename)==14,
      "r07_guard_denies_unverified_receipt_without_locking_target");
 }
 chk(filecommand::inspectRenameRestore(
       srcRename.native(),unverifiedReceipt)==Observation::UnverifiedReceipt,
     "r07_preflight_rejects_unverified_receipt");
 chk(filecommand::inspectRenameRestore(
       (root/L"foreign-original.txt").native(),renamedFile)==
       Observation::UnsafePaths&&
     filecommand::inspectRenameRestore(dstRename.native(),renamedFile)==
       Observation::UnsafePaths,
     "r07_preflight_rejects_other_parent_and_same_name");
 { std::ofstream occupied(srcRename,std::ios::binary);occupied<<"do not modify"; }
 chk(filecommand::inspectRenameRestore(srcRename.native(),renamedFile)==
     Observation::OriginalOccupiedOrUnknown&&
     std::filesystem::file_size(srcRename)==13&&
     std::filesystem::file_size(dstRename)==14,
     "r07_preflight_rejects_reoccupied_source_preserves_files");
 std::filesystem::remove(srcRename);
 auto changedIdentity=renamedFile;
 changedIdentity.renameEvidence.fileId[0]^=1;
 chk(filecommand::inspectRenameRestore(srcRename.native(),changedIdentity)==
     Observation::TargetChangedOrUnavailable,
     "r07_preflight_rejects_changed_file_id");
 auto lostTarget=renamedFile;
 lostTarget.target=(dir/L"missing-target.txt").native();
 chk(filecommand::inspectRenameRestore(srcRename.native(),lostTarget)==
     Observation::TargetChangedOrUnavailable,
     "r07_preflight_rejects_missing_target");
 req.source=dstRename.native();req.name=L"새 문서.txt";
 const auto failedRename=filecommand::execute(req);
 { std::ifstream retained(dstRename,std::ios::binary);std::string payload;
   std::getline(retained,payload);
   chk(failedRename.error!=ERROR_SUCCESS&&
       !failedRename.renameEvidence.verified&&
       std::filesystem::exists(dir/L"새 문서.txt")&&
       payload=="owned R07 only",
       "r07_conflict_does_not_issue_receipt_or_overwrite"); }
 // An external content change must invalidate the old point-in-time ID
 // snapshot even though the same renamed pathname and file ID still exist.
 { std::ofstream changed(dstRename,std::ios::binary|std::ios::app);changed<<"!"; }
 chk(filecommand::inspectRenameRestore(srcRename.native(),renamedFile)==
     Observation::TargetChangedOrUnavailable&&
     std::filesystem::file_size(dstRename)==15&&
     !std::filesystem::exists(srcRename),
     "r07_preflight_rejects_external_content_change");

 // R07-8: exercise the isolated restore primitive ONLY on these fixture-owned
 // files. It has no UI/ticket caller; the native result is not Undo acceptance.
 {
  using WriteStatus=filecommand::RenameRestoreWriteStatus;
  const auto restoreOriginal=dir/L"r07-복원-원본.txt";
  const auto restoreTarget=dir/L"r07-복원-변경.txt";
  const std::string ownedBytes="r07-only-test-payload";
  { std::ofstream out(restoreOriginal,std::ios::binary);
    out.write(ownedBytes.data(),static_cast<std::streamsize>(ownedBytes.size())); }
  filecommand::Request restoreReq{};
  restoreReq.kind=filecommand::Kind::RenameSelected;
  restoreReq.parent=dir.native();
  restoreReq.source=restoreOriginal.native();
  restoreReq.name=restoreTarget.filename().native();
  const auto receipt=filecommand::execute(restoreReq);
  FILE_ID_INFO restoredBefore{},restoredAfter{};
  const bool originalRenamed=receipt.error==ERROR_SUCCESS&&
      receipt.renameEvidence.verified&&
      readId(restoreTarget,restoredBefore)&&
      !std::filesystem::exists(restoreOriginal)&&
      std::filesystem::exists(restoreTarget);
  chk(originalRenamed,"r07_restore_owned_verified_rename_receipt");

  auto missingProof=receipt;
  missingProof.renameEvidence.verified=false;
  const auto rejectedUnverified=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),missingProof);
  chk(rejectedUnverified.status==WriteStatus::RejectedReceipt&&
      !rejectedUnverified.nativeCallAttempted&&
      !std::filesystem::exists(restoreOriginal)&&
      std::filesystem::exists(restoreTarget),
      "r07_restore_rejects_unverified_receipt_without_mutation");

  auto forgedProof=receipt;
  forgedProof.renameEvidence.fileId[0]^=1;
  const auto rejectedId=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),forgedProof);
  chk(rejectedId.status==WriteStatus::TargetChangedOrUnavailable&&
      !rejectedId.nativeCallAttempted&&
      !std::filesystem::exists(restoreOriginal)&&
      std::filesystem::exists(restoreTarget),
      "r07_restore_rejects_forged_file_id_without_mutation");

  auto missingTarget=receipt;
  missingTarget.target=(dir/L"r07-복원-없는파일.txt").native();
  const auto rejectedMissing=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),missingTarget);
  chk(rejectedMissing.status==WriteStatus::TargetChangedOrUnavailable&&
      !rejectedMissing.nativeCallAttempted&&
      !std::filesystem::exists(restoreOriginal)&&
      std::filesystem::exists(restoreTarget),
      "r07_restore_rejects_missing_target_without_mutation");

  const std::string occupiedBytes="collision-owned-payload";
  { std::ofstream occupied(restoreOriginal,std::ios::binary);
    occupied.write(occupiedBytes.data(),
                   static_cast<std::streamsize>(occupiedBytes.size())); }
  const auto rejectedCollision=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),receipt);
  std::string retainedCollision{};
  { std::ifstream original(restoreOriginal,std::ios::binary);
    retainedCollision.assign(std::istreambuf_iterator<char>(original),
                             std::istreambuf_iterator<char>{}); }
  chk(rejectedCollision.status==WriteStatus::OriginalOccupiedOrUnknown&&
      !rejectedCollision.nativeCallAttempted&&
      retainedCollision==occupiedBytes&&std::filesystem::exists(restoreTarget),
      "r07_restore_rejects_original_collision_preserves_bytes");
  std::filesystem::remove(restoreOriginal); // fixture-owned collision only

  const HANDLE priorWriter=::CreateFileW(
      restoreTarget.c_str(),FILE_WRITE_DATA,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  bool writerRejected=priorWriter!=INVALID_HANDLE_VALUE;
  if(writerRejected){
   const auto rejectedWriter=filecommand::restoreRenameNoReplace(
       restoreOriginal.native(),receipt);
   writerRejected=rejectedWriter.status==WriteStatus::AccessUnavailable&&
       !rejectedWriter.nativeCallAttempted;
   ::CloseHandle(priorWriter);
  }
  chk(writerRejected&&std::filesystem::exists(restoreTarget)&&
      !std::filesystem::exists(restoreOriginal),
      "r07_restore_rejects_preexisting_writer_without_mutation");

  const auto restored=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),receipt);
  std::string restoredBytes{};
  if(std::filesystem::exists(restoreOriginal)){
   std::ifstream original(restoreOriginal,std::ios::binary);
   restoredBytes.assign(std::istreambuf_iterator<char>(original),
                             std::istreambuf_iterator<char>{});
  }
  const bool identityKept=readId(restoreOriginal,restoredAfter)&&
      restoredBefore.VolumeSerialNumber==restoredAfter.VolumeSerialNumber&&
      std::memcmp(restoredBefore.FileId.Identifier,
                  restoredAfter.FileId.Identifier,16)==0;
  if(restored.status!=WriteStatus::CommittedVerified){
   // Test-owned checkout only: isolate whether the relative name resolved
   // against the process CWD instead of the opened file's parent.
   const auto cwdLeaf=std::filesystem::current_path()/restoreOriginal.filename();
   FILE_ID_INFO cwdId{};
   const bool cwdMatchesFile=readId(cwdLeaf,cwdId)&&
       restoredBefore.VolumeSerialNumber==cwdId.VolumeSerialNumber&&
       std::memcmp(restoredBefore.FileId.Identifier,cwdId.FileId.Identifier,16)==0;
   std::printf("M21_DEBUG_R07_RESTORE status=%u error=%lu attempted=%d orig=%d target=%d identity=%d bytes=%d cwd_id_match=%d\\n",
     static_cast<unsigned>(restored.status),static_cast<unsigned long>(restored.error),
     static_cast<int>(restored.nativeCallAttempted),
     static_cast<int>(std::filesystem::exists(restoreOriginal)),
     static_cast<int>(std::filesystem::exists(restoreTarget)),
     static_cast<int>(identityKept),static_cast<int>(restoredBytes==ownedBytes),
     static_cast<int>(cwdMatchesFile));
  }
  chk(restored.status==WriteStatus::CommittedVerified&&
      restored.nativeCallAttempted&&restored.error==ERROR_SUCCESS&&
      identityKept&&restoredBytes==ownedBytes&&
      !std::filesystem::exists(restoreTarget),
      "r07_restore_owned_no_replace_commits_exact_file");

  const auto replay=filecommand::restoreRenameNoReplace(
      restoreOriginal.native(),receipt);
  if(replay.status!=WriteStatus::OriginalOccupiedOrUnknown){
   std::printf("M21_DEBUG_R07_REPLAY status=%u error=%lu attempted=%d orig=%d target=%d\\n",
     static_cast<unsigned>(replay.status),static_cast<unsigned long>(replay.error),
     static_cast<int>(replay.nativeCallAttempted),
     static_cast<int>(std::filesystem::exists(restoreOriginal)),
     static_cast<int>(std::filesystem::exists(restoreTarget)));
  }
  chk(replay.status==WriteStatus::OriginalOccupiedOrUnknown&&
      !replay.nativeCallAttempted&&
      std::filesystem::exists(restoreOriginal)&&
      !std::filesystem::exists(restoreTarget)&&restoredBytes==ownedBytes,
      "r07_restore_replay_rejected_and_original_preserved");
 }
 req.kind=filecommand::Kind::CreateTextFile;
 req.source.clear();
 req.name=L"메모.md";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME&&
     !std::filesystem::exists(dir/L"메모.md"),
     "text_document_denies_other_extensions");
 req.name=L"..\\escape.txt";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,
     "text_document_denies_traversal");
 req.name=L"CON.txt";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,
     "text_document_denies_reserved_device");
 bool textDevicesRejected=true;
 for(auto const* leaf:{L"CONIN$.txt",L"conout$.TXT",
                       L"COM\u00B3.txt",L"lpt\u00B2.TXT"}){
  req.name=leaf;
  textDevicesRejected=textDevicesRejected&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(textDevicesRejected,"text_document_denies_console_device_names");
 req.parent=L"shell:MyComputerFolder";req.name=L"virtual.txt";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS,
     "text_document_denies_virtual_parent");
 // Markdown uses the same no-replace local creation path, with its own suffix.
 req.parent=dir.native();req.kind=filecommand::Kind::CreateMarkdownFile;
 req.name=L"새 문서.md";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/req.name)&&
     std::filesystem::file_size(dir/req.name)==0,
     "create_empty_unicode_markdown_document");
 { std::ofstream existing(dir/req.name,std::ios::binary);existing<<"owned markdown"; }
 const auto duplicateMarkdown=filecommand::execute(req);
 { std::ifstream existing(dir/req.name,std::ios::binary);std::string retained;
   std::getline(existing,retained);
   chk(duplicateMarkdown.error!=ERROR_SUCCESS&&retained=="owned markdown",
       "markdown_never_overwrites_existing"); }
 req.name=L"메모.MD";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::file_size(dir/req.name)==0,
     "markdown_case_insensitive_extension");
 bool markdownNamesRejected=true;
 for(auto const* leaf:{L".md",L"wrong.txt",L"..\\escape.md",L"CON.md",L"a.md ",L"a.md.exe"}){
  req.name=leaf;
  markdownNamesRejected=markdownNamesRejected&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(markdownNamesRejected,"markdown_rejects_unsafe_or_other_suffix_names");

 // R04 selected file shortcut: preserve source and never replace a link.
 req.parent=dir.native();req.kind=filecommand::Kind::CreateShortcut;
 req.source=(dir/L"메모.MD").native();req.name=L"메모 - 바로 가기.lnk";
 const auto linkResult=filecommand::execute(req);
 chk(linkResult.error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/req.name)&&
     std::filesystem::file_size(dir/req.name)>0&&
     std::filesystem::file_size(dir/L"메모.MD")==0,
     "shortcut_creates_nonempty_link_preserves_source");
 // Verify the actual Shell link payload refers to the exact selected
 // file, not merely that a nonempty .lnk-looking file was written.
 bool linkTargetsSource=false;
 const HRESULT apartment=::CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
 if(SUCCEEDED(apartment)){
  IShellLinkW* link=nullptr;
  if(SUCCEEDED(::CoCreateInstance(CLSID_ShellLink,nullptr,CLSCTX_INPROC_SERVER,
                                  IID_PPV_ARGS(&link)))){
   IPersistFile* persist=nullptr;
   if(SUCCEEDED(link->QueryInterface(IID_PPV_ARGS(&persist)))){
    if(SUCCEEDED(persist->Load((dir/req.name).c_str(),STGM_READ))){
     wchar_t resolved[32768]{};
     WIN32_FIND_DATAW data{};
     if(SUCCEEDED(link->GetPath(resolved,32768,&data,SLGP_RAWPATH))){
      linkTargetsSource=::CompareStringOrdinal(
          resolved,-1,req.source.c_str(),-1,TRUE)==CSTR_EQUAL;
     }
    }
    persist->Release();
   }
   link->Release();
  }
  ::CoUninitialize();
 }
 chk(linkTargetsSource,"shortcut_resolves_exact_selected_source");
 { std::ofstream existing(dir/req.name,std::ios::binary);existing<<"owned link"; }
 const auto collision=filecommand::execute(req);
 { std::ifstream existing(dir/req.name,std::ios::binary);std::string retained;
   std::getline(existing,retained);
   chk(collision.error!=ERROR_SUCCESS&&retained=="owned link",
       "shortcut_never_overwrites_existing_link"); }
 req.name=L"링크.LNK";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/req.name),
     "shortcut_accepts_uppercase_extension");
 bool rejectsBadLinks=true;
 for(auto const* leaf:{L".lnk",L"wrong.txt",L"..\\escape.lnk",
                       L"CON.lnk",L"trailing.lnk ",L"double.lnk.exe"}){
  req.name=leaf;
  rejectsBadLinks=rejectsBadLinks&&
      filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(rejectsBadLinks,"shortcut_denies_unsafe_link_names");
 req.name=L"foreign.lnk";req.source=(root/L"foreign-source").native();
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,
     "shortcut_denies_nonchild_source");
 req.source=(dir/L"missing.txt").native();
 chk(filecommand::execute(req).error!=ERROR_SUCCESS,
     "shortcut_denies_missing_source");
 req.parent=dir.native();req.kind=static_cast<filecommand::Kind>(99);
 chk(filecommand::execute(req).error==ERROR_INVALID_PARAMETER,"unknown_mutation_denied");
 std::printf("M21_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
