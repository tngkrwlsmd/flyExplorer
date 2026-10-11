#include "../../../src/base/shell_transfer_core.h"
#include "../../../src/base/stage_receipt_core.h"
#include <filesystem>
#include <fstream>
#include <cstdio>
#include <thread>
#include <chrono>
#include <algorithm>
#include <iterator>
using namespace fxfile::shelltransfer;
namespace fs=std::filesystem;
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
std::atomic_bool g_directoryProbeAttempted{false};
std::atomic_bool g_directoryProbeBlocked{false};
// Called synchronously inside the active worker's pinned-ancestor window.
// No scan or mutation outside a disposable M22-owned folder.
void attemptTestOwnedParentRename(std::wstring const& exactParent) noexcept {
 if(fs::path(exactParent).filename()!=L"m22-pin-target")return;
 const std::wstring alternate=exactParent+L"-swapped";
 const BOOL renamed=::MoveFileExW(
     exactParent.c_str(),alternate.c_str(),0);
 const DWORD result=renamed?ERROR_SUCCESS: ::GetLastError();
 if(renamed)(void)::MoveFileExW(
     alternate.c_str(),exactParent.c_str(),0);
 g_directoryProbeAttempted.store(true,std::memory_order_release);
 g_directoryProbeBlocked.store(!renamed&&
     (result==ERROR_SHARING_VIOLATION||result==ERROR_ACCESS_DENIED),
     std::memory_order_release);
}
#endif
int wmain(int count,wchar_t**args){
 setvbuf(stdout,nullptr,_IONBF,0);
 if(count==2&&std::wstring(args[1])==L"--receipt-child-exit")return 0;
 if(count==5&&std::wstring(args[1])==L"--owned-stage-race-receipt"){
  // Run only with a disposable test-owned source, destination and
  // owner-only journal. A second test-owned controller creates the final
  // target while CopyFileEx is writing the exact stage.
  const fs::path source(args[2]),destination(args[3]),store(args[4]);
  if(!isPrivateStageReceiptDirectory(store.native())||
     !fs::is_regular_file(source)||!fs::is_directory(destination))return 93;
  Request request{};
  request.kind=Kind::Copy;
  request.collision=Collision::Reject;
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  progress.receiptDirectory=store.native();
  const auto outcome=execute(request,progress);
  bool completedButUnpublished=false;
  std::size_t originalRecords=0;
  for(auto const& record:fs::directory_iterator(store)){
   if(record.path().extension()!=L".bin")continue;
   ++originalRecords;
   StageOwnershipReceipt receipt{};
   if(readStageReceipt(record.path().native(),receipt)&&
      receipt.targetLeaf==source.filename().native()&&
      receiptMatchesStage(receipt)&&
      inspectStageReceiptState(record.path().native())==
         StageReceiptState::CompletedOnStage)
    completedButUnpublished=true;
  }
  const bool denied=(outcome.error==ERROR_ALREADY_EXISTS||
                     outcome.error==ERROR_FILE_EXISTS);
  const bool pass=denied&&originalRecords==1&&completedButUnpublished;
  std::printf("M22_BOUND_PUBLISH_LATE_TARGET_COLLISION=%s error=%lu journal=%d\n",
              pass?"PASS":"FAIL",outcome.error,
              int(completedButUnpublished));
  return pass?0:94;
 }
 if(count==5&&std::wstring(args[1])==L"--owned-helper-ipc-untrusted"){
  // This intentionally inherited ACL folder must never be accepted by the
  // test-only helper. The child exits without touching the source or target.
  const fs::path source(args[2]),destination(args[3]),untrusted(args[4]);
  if(!fs::is_regular_file(source)||!fs::is_directory(destination)||
     !fs::is_directory(untrusted)||
     isPrivateStageReceiptDirectory(untrusted.native()))return 91;
  Request task{};
  task.kind=Kind::Copy;
  task.collision=Collision::Reject;
  task.sourceParent=source.parent_path().native();
  task.destination=destination.native();
  task.sources={source.native()};
  Progress state{};
  const auto result=executeIsolated(task,state);
  bool targetAbsent=!fs::exists(destination/source.filename());
  bool folderUnmodified=fs::directory_iterator(destination)==
                         fs::directory_iterator();
  const bool passed=result.error!=ERROR_SUCCESS&&targetAbsent&&
                    folderUnmodified&&fs::exists(source);
  std::printf("M22_ISOLATED_HELPER_IPC_UNTRUSTED_STORE=%s error=%lu\n",
      passed?"PASS":"FAIL",result.error);
  return passed?0:92;
 }
 if(count==5&&std::wstring(args[1])==L"--owned-helper-ipc-copy"){
  // This test executable and the *explicit fixture-compiled* helper are
  // siblings. The environment points only to this test-owned private store.
  // The production helper has NO environment-controlled receipt root.
  const fs::path source(args[2]),destination(args[3]),store(args[4]);
  if(!fs::is_regular_file(source)||!fs::is_directory(destination)||
     !isPrivateStageReceiptDirectory(store.native()))return 88;
  const auto expected=source.filename();
  Request request{};
  request.kind=Kind::Copy;
  request.collision=Collision::Reject;
  request.sourceMode=SourceMode::Filesystem;
  request.destinationMode=DestinationMode::Filesystem;
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  const auto result=executeIsolated(request,progress);
  bool verified=false;
  int countRecords=0;
  for(auto const& entry:fs::directory_iterator(store)){
   if(entry.path().extension()!=L".bin")continue;
   ++countRecords;
   StageOwnershipReceipt receipt{};
   if(readStageReceipt(entry.path().native(),receipt)&&
      receipt.targetLeaf==expected.native()&&
      inspectStageReceiptState(entry.path().native())==
         StageReceiptState::PublishedVerified)
    verified=true;
  }
  const auto target=destination/expected;
  bool bytesMatch=false;
  if(fs::is_regular_file(target)&&
     fs::file_size(source)==fs::file_size(target)){
   std::ifstream a(source,std::ios::binary),b(target,std::ios::binary);
   bytesMatch=std::equal(std::istreambuf_iterator<char>(a),
                         std::istreambuf_iterator<char>(),
                         std::istreambuf_iterator<char>(b),
                         std::istreambuf_iterator<char>());
  }
  const bool passed=result.error==ERROR_SUCCESS&&!result.aborted&&
     progress.percent==100&&countRecords==1&&verified&&bytesMatch;
  std::printf("M22_ISOLATED_HELPER_IPC_BOUND_RECEIPT=%s error=%lu bytes=%d verified=%d\n",
       passed?"PASS":"FAIL",result.error,int(bytesMatch),int(verified));
  return passed?0:89;
 }

 // Read exactly one known receipt in a freshly launched process, with
 // no enumeration, cleanup, file attribute changes or publication.
 if(count==4&&std::wstring(args[1])==L"--receipt-inspect-state"){
  const auto state=inspectStageReceiptState(args[2]);
  const std::wstring expected(args[3]);
  const bool ok=(expected==L"published"&&
                 state==StageReceiptState::PublishedVerified)||
                (expected==L"ambiguous"&&
                 state==StageReceiptState::PublicationUnconfirmed)||
                (expected==L"inconsistent"&&
                 state==StageReceiptState::Inconsistent)||
                (expected==L"copying"&&
                 state==StageReceiptState::CopyingOrInterrupted);
  std::printf("M22_RESTART_READONLY_RECEIPT_STATE=%s\n",
              ok?"PASS":"FAIL");
  return ok?0:87;
 }
 // Separate test-only commands. The caller supplies only its owned fixture
 // files; no application profile, unrelated PID or user folder is touched.
 if(count==3&&std::wstring(args[1])==L"--receipt-create-private"){
  const bool ok=createPrivateStageReceiptDirectory(args[2]);
  std::printf("M22_OWNED_PRIVATE_RECEIPT_STORE=%s\n",ok?"PASS":"FAIL");
  return ok?0:83;
 }
 if(count==4&&std::wstring(args[1])==L"--receipt-verify-killed"){
  StageOwnershipReceipt entry{};
  const bool read=readStageReceipt(args[2],entry);
  const bool matched=read&&entry.stagePath==args[3]&&
                     receiptMatchesStage(entry);
  const auto state=read?inspectReceiptCreator(entry):
                        ReceiptCreatorState::Unknown;
  const bool inactive=state!=ReceiptCreatorState::Running;
  const bool pending=inspectStageReceiptState(args[2])==
                       StageReceiptState::CopyingOrInterrupted;
  std::printf("M22_KILLED_WORKER_RECEIPT_MATCH=%s CREATOR_NOT_RUNNING=%s STATE_PENDING=%s\n",
              matched?"PASS":"FAIL",inactive?"PASS":"FAIL",
              pending?"PASS":"FAIL");
  return matched&&inactive&&pending?0:84;
 }
 if(count==5&&std::wstring(args[1])==L"--owned-stage-kill-receipt"){
  Request request{};
  request.kind=Kind::Copy;
  const fs::path source(args[2]),destination(args[3]);
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  progress.receiptDirectory=args[4];
  if(!isPrivateStageReceiptDirectory(progress.receiptDirectory))return 85;
  const auto result=execute(request,progress);
  return result.error==ERROR_SUCCESS?0:86;
 }
 if(count==4&&std::wstring(args[1])==L"--owned-stage-cancel"){
  // Cancel only after transfer progress is observed on a disposable file.
  Request request{};
  request.kind=Kind::Copy;
  const fs::path source(args[2]),destination(args[3]);
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  std::atomic_bool done{false},triggered{false};
  std::thread canceler([&]{
   while(!done.load(std::memory_order_acquire)){
    const auto percent=progress.percent.load(std::memory_order_relaxed);
    if(percent>0&&percent<100){
     triggered.store(true,std::memory_order_relaxed);
     progress.cancel.store(true,std::memory_order_relaxed);
     break;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
   }
  });
  const auto outcome=execute(request,progress);
  done.store(true,std::memory_order_release);
  canceler.join();
  if(triggered.load()&&outcome.error==ERROR_CANCELLED&&
     outcome.aborted&&!fs::exists(destination/source.filename())){
   std::puts("M22_OWNED_STAGED_MID_COPY_CANCEL=PASS");
   return 0;
  }
  std::printf("M22_OWNED_STAGED_MID_COPY_CANCEL=FAIL error=%lu cancel=%d done=%u\n",
      outcome.error,int(triggered.load()),progress.percent.load());
  return 24;
 }
 if(count==4&&std::wstring(args[1])==L"--owned-move-deny"){
  // Move failure on a test-owned source and ACL-denied destination folder.
  const fs::path source(args[2]),destination(args[3]);
  Request request{};
  request.kind=Kind::Move;
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  const auto outcome=execute(request,progress);
  const bool failure=outcome.error!=ERROR_SUCCESS;
  std::printf("M22_OWNED_MOVE_DENIED=%s error=%lu\n",
      failure?"PASS":"FAIL",outcome.error);
  return failure?0:27;
 }
 if(count==4&&(std::wstring(args[1])==L"--owned-stage-deny"||
               std::wstring(args[1])==L"--owned-stage-race")){
  // The caller owns both folders; this mode cannot mutate the source,
  // any existing target, or a non-test-owned folder.
  const fs::path source(args[2]),destination(args[3]);
  Request request{};
  request.kind=Kind::Copy;
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  const auto outcome=execute(request,progress);
  const bool denied=std::wstring(args[1])==L"--owned-stage-deny";
  const bool expected=denied?
      (outcome.error==ERROR_ACCESS_DENIED||
       outcome.error==ERROR_WRITE_PROTECT):
      (outcome.error==ERROR_ALREADY_EXISTS||
       outcome.error==ERROR_FILE_EXISTS);
  std::printf("M22_OWNED_STAGE_%s=%s error=%lu\n",
      denied?"DENIED_DESTINATION":"LATE_TARGET_COLLISION",
      expected?"PASS":"FAIL",outcome.error);
  return expected?0:26;
 }
 if(count==4&&std::wstring(args[1])==L"--owned-stage-kill"){
  // Only invoked by test_native.py with its disposable source/destination.
  Request request{};
  request.kind=Kind::Copy;
  const fs::path source(args[2]),destination(args[3]);
  request.sourceParent=source.parent_path().native();
  request.destination=destination.native();
  request.sources={source.native()};
  Progress progress{};
  const auto outcome=execute(request,progress);
  return outcome.error==ERROR_SUCCESS?0:23;
 }
 if(count!=2&&count!=3)return 2;
 const fs::path root(args[1]),left=root/L"왼쪽",right=root/L"오른쪽";
 fs::create_directory(left);fs::create_directory(right);
 int pass=0,fail=0;
 auto test=[&](bool ok,char const*label){
  std::printf("M22_NATIVE_%s %s\n",ok?"PASS":"FAIL",label);
  if(ok)++pass;else ++fail;
 };
 test(supportsDriveType(Kind::Copy,DRIVE_FIXED),
      "copy_accepts_fixed_drive");
 test(supportsDriveType(Kind::Move,DRIVE_FIXED),
      "move_accepts_fixed_drive");
 test(supportsDriveType(Kind::Recycle,DRIVE_FIXED),
      "recycle_accepts_fixed_drive");
 test(supportsDriveType(Kind::Copy,DRIVE_REMOVABLE),
      "copy_accepts_removable_drive");
 test(supportsDriveType(Kind::Move,DRIVE_REMOVABLE),
      "move_accepts_removable_drive");
 test(supportsDriveType(Kind::Recycle,DRIVE_REMOVABLE),
      "recycle_accepts_removable_drive");
 test(!supportsDriveType(Kind::Recycle,DRIVE_REMOTE),
      "recycle_rejects_remote_drive");
 test(supportsDriveType(Kind::Copy,DRIVE_REMOTE),
      "copy_accepts_remote_drive");
 test(supportsDriveType(Kind::Move,DRIVE_REMOTE),
      "move_accepts_remote_drive");
 std::wstring parsedRoot;
 test(transferDriveRoot(L"\\\\server\\share\\folder",parsedRoot)&&
      parsedRoot==L"\\\\server\\share\\",
      "parse_standard_unc_share_root");
 test(transferDriveRoot(L"Z:\\folder",parsedRoot)&&parsedRoot==L"Z:\\",
      "parse_drive_letter_root");
 test(!transferDriveRoot(
        L"\\\\?\\UNC\\server\\share\\folder",parsedRoot)&&
      !transferDriveRoot(L"\\\\.\\C:\\folder",parsedRoot),
      "reject_extended_and_device_roots");
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

 // Recovery identity is read-only evidence, NOT permission to delete.
 // Exercise a standalone stage inside this exact owned disposable root.
 const auto probeFolder=root/L"stage-identity";
 fs::create_directory(probeFolder);
 const auto stage=probeFolder/
     L".flyExplorer-copy-{00000000-0000-0000-0000-000000000001}.partial";
 put(stage,"owned-identity-one");
 StageFileIdentity observed{},unchanged{},other{},rejected{};
 const bool inspected=inspectStageFile(stage.native(),observed);
 test(inspected&&inspectStageFile(stage.native(),unchanged)&&
      sameStageFile(observed,unchanged)&&
      !sameStageFile(StageFileIdentity{},observed),
      "stage_identity_stable_readonly_snapshot");
 const auto hardlink=probeFolder/L"other-hard-link.txt";
 std::error_code linkError{};
 fs::create_hard_link(stage,hardlink,linkError);
 const bool refusedHardlink=!linkError&&
      !inspectStageFile(stage.native(),rejected);
 fs::remove(hardlink,linkError);
 test(refusedHardlink&&!linkError&&
      inspectStageFile(stage.native(),unchanged),
      "stage_identity_refuses_multiple_hardlinks");
 const auto previous=probeFolder/L"original-retained.bin";
 fs::rename(stage,previous);
 put(stage,"replacement-not-original");
 test(inspectStageFile(stage.native(),other)&&
      !sameStageFile(observed,other)&&
      get(previous)=="owned-identity-one"&&
      get(stage)=="replacement-not-original",
      "stage_identity_detects_same_path_replacement");
 StageFileIdentity invalid{};
 const auto invalidName=probeFolder/L"unrelated.txt";
 put(invalidName,"must-not-be-interpreted-as-stage");
 const auto traversal=probeFolder/L"subdir"/L".."/stage.filename();
 test(!inspectStageFile(invalidName.native(),invalid)&&
      !inspectStageFile(traversal.native(),invalid)&&
      !inspectStageFile((probeFolder/L"not-present.partial").native(),invalid),
      "stage_identity_rejects_unowned_names_and_unnormalized_paths");


 // Receipt storage uses only this explicitly created disposable directory.
 // A receipt is evidence, never authorization to delete the stage.
 const auto insecureFolder=root/L"receipt-insecure";
 fs::create_directory(insecureFolder); // normal inherited test DACL
 const auto insecureRecord=insecureFolder/
     L".flyExplorer-receipt-{00000000-0000-0000-0000-000000000001}.bin";
 StageOwnershipReceipt insecureResult{};
 const bool insecureRejected=!isPrivateStageReceiptDirectory(
     insecureFolder.native())&&
     !writeStageReceipt(insecureRecord.native(),stage.native(),
                        L"target-document.txt")&&
     !readStageReceipt(insecureRecord.native(),insecureResult)&&
     !fs::exists(insecureRecord);
 test(insecureRejected&&get(stage)=="replacement-not-original",
      "receipt_refuses_untrusted_inherited_acl_store");
 const auto receiptFolder=root/L"receipt-identity";
 const bool privateCreated=createPrivateStageReceiptDirectory(
     receiptFolder.native());
 const bool privateVerified=isPrivateStageReceiptDirectory(
     receiptFolder.native());
 test(privateCreated&&privateVerified&&
      !createPrivateStageReceiptDirectory(receiptFolder.native()),
      "receipt_private_owner_dacl_created_without_acl_reset");
 const auto record=receiptFolder/
     L".flyExplorer-receipt-{00000000-0000-0000-0000-000000000001}.bin";
 StageOwnershipReceipt saved{};
 const bool wrote=writeStageReceipt(
     record.native(),stage.native(),L"target-document.txt");
 const bool loaded=readStageReceipt(record.native(),saved);
 test(wrote&&loaded&&saved.stagePath==stage.native()&&
      saved.targetLeaf==L"target-document.txt"&&
      saved.creatorPid==::GetCurrentProcessId()&&
      saved.creatorStartTime!=0&&receiptMatchesStage(saved),
      "receipt_roundtrip_flush_and_exact_stage_identity");
 StageOwnershipReceipt bogus=saved;
 bogus.creatorStartTime+=1; // PID is valid, but creation time is not.
 test(inspectReceiptCreator(saved)==ReceiptCreatorState::Running&&
      inspectReceiptCreator(bogus)==ReceiptCreatorState::Unknown&&
      inspectReceiptCreator(StageOwnershipReceipt{})==
          ReceiptCreatorState::Unknown,
      "receipt_creator_alive_and_pid_reuse_fail_closed");
 // Retain the child's PROCESS_INFORMATION handle until the exited-state
 // probe finishes. Only this one fixture-spawned process is observed.
 wchar_t fixturePath[32768]{};
 const DWORD fixtureUnits=::GetModuleFileNameW(nullptr,fixturePath,32768);
 bool exitedProbe=false;
 if(fixtureUnits>0&&fixtureUnits<32768){
  std::wstring command=L"\""+std::wstring(fixturePath)+L"\" --receipt-child-exit";
  STARTUPINFOW info{};info.cb=sizeof(info);
  PROCESS_INFORMATION child{};
  if(::CreateProcessW(fixturePath,command.data(),nullptr,nullptr,FALSE,
                      CREATE_NO_WINDOW,nullptr,nullptr,&info,&child)){
   const DWORD waited=::WaitForSingleObject(child.hProcess,5000);
   FILETIME created{},exited{},kernel{},user{};
   if(waited==WAIT_OBJECT_0&&
      ::GetProcessTimes(child.hProcess,&created,&exited,&kernel,&user)){
    ULARGE_INTEGER start{};
    start.LowPart=created.dwLowDateTime;
    start.HighPart=created.dwHighDateTime;
    StageOwnershipReceipt finished=saved;
    finished.creatorPid=child.dwProcessId;
    finished.creatorStartTime=start.QuadPart;
    exitedProbe=inspectReceiptCreator(finished)==ReceiptCreatorState::Exited;
   }
   ::CloseHandle(child.hThread);
   ::CloseHandle(child.hProcess);
  }
 }
 test(exitedProbe&&receiptMatchesStage(saved),
      "receipt_creator_exited_without_stage_mutation");
 const auto initialReceiptBytes=fs::file_size(record);
 test(!writeStageReceipt(record.native(),stage.native(),
                         L"target-document.txt")&&
      fs::file_size(record)==initialReceiptBytes&&
      readStageReceipt(record.native(),saved),
      "receipt_create_new_never_overwrites_existing");
 const auto oldReceiptStage=probeFolder/L"recorded-but-renamed.bin";
 fs::rename(stage,oldReceiptStage);
 put(stage,"new-file-at-identical-path");
 test(readStageReceipt(record.native(),saved)&&
      !receiptMatchesStage(saved)&&
      get(oldReceiptStage)=="replacement-not-original"&&
      get(stage)=="new-file-at-identical-path",
      "receipt_rejects_same_path_file_replacement");
 {
  std::fstream f(record,std::ios::binary|std::ios::in|std::ios::out);
  char byte=0;
  f.seekg(-1,std::ios::end);f.get(byte);
  f.seekp(-1,std::ios::end);
  f.put(static_cast<char>(byte^0x01));
 }
 StageOwnershipReceipt tampered{};
 test(!readStageReceipt(record.native(),tampered)&&
      !receiptMatchesStage(tampered)&&
      get(oldReceiptStage)=="replacement-not-original"&&
      get(stage)=="new-file-at-identical-path",
      "receipt_corruption_fails_closed_without_file_mutation");

 // Pure exact-receipt, read-only state machine across immutable records.
 // The two stage/target filenames here belong exclusively to this test.
 const auto phaseStage=probeFolder/
     L".flyExplorer-copy-{00000000-0000-0000-0000-000000000002}.partial";
 const auto phaseRecord=receiptFolder/
     L".flyExplorer-receipt-{00000000-0000-0000-0000-000000000002}.bin";
 const auto phaseTarget=probeFolder/L"phase-published-target.txt";
 put(phaseStage,"immutable-phase-test-owned");
 const bool phaseReceipt=writeStageReceipt(
     phaseRecord.native(),phaseStage.native(),phaseTarget.filename().native());
 test(phaseReceipt&&inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::CopyingOrInterrupted,
      "receipt_phase_initial_copying_readonly");
 const bool completed=markStageCopyCompleted(phaseRecord.native());
 test(completed&&inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::CompletedOnStage&&
      !markStageCopyCompleted(phaseRecord.native()),
      "receipt_phase_completed_immutable_write_once");
 fs::rename(phaseStage,phaseTarget);
 test(inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::PublicationUnconfirmed,
      "receipt_phase_rename_without_published_marker_ambiguous");
 const bool publishedMarker=markStageCopyPublished(phaseRecord.native());
 test(publishedMarker&&inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::PublishedVerified&&
      !markStageCopyPublished(phaseRecord.native()),
      "receipt_phase_published_same_identity_write_once");
 const auto formerTarget=probeFolder/L"formerly-published-original.txt";
 fs::rename(phaseTarget,formerTarget);
 put(phaseTarget,"unrelated-target-replacement");
 test(inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::Inconsistent&&
      get(formerTarget)=="immutable-phase-test-owned"&&
      get(phaseTarget)=="unrelated-target-replacement",
      "receipt_phase_published_target_replacement_is_inconsistent");
 {
  const auto completePath=fs::path(phaseRecord.native()+L".complete");
  std::fstream f(completePath,std::ios::binary|std::ios::in|std::ios::out);
  char byte=0;
  f.seekg(-1,std::ios::end);f.get(byte);
  f.seekp(-1,std::ios::end);
  f.put(static_cast<char>(byte^0x01));
 }
 test(inspectStageReceiptState(phaseRecord.native())==
      StageReceiptState::Inconsistent&&
      get(formerTarget)=="immutable-phase-test-owned",
      "receipt_phase_corrupt_transition_rejected_readonly");

 // Exercise the actual CopyFileExW callback and real destination handle.
 // These three paths are strictly inside the unique disposable fixture root;
 // no production Known Folder is provisioned by this direct execute().
 const auto liveStore=root/L"receipt-live-store";
 const bool liveStoreCreated=createPrivateStageReceiptDirectory(
     liveStore.native());
 const auto liveSource=left/L"receipt-live-source.txt";
 const auto liveDest=root/L"receipt-live-destination";
 fs::create_directory(liveDest);
 put(liveSource,"callback-owned-copy-content");
 Request liveRequest{};
 liveRequest.kind=Kind::Copy;
 liveRequest.collision=Collision::Reject;
 liveRequest.sourceParent=left.native();
 liveRequest.destination=liveDest.native();
 liveRequest.sources={liveSource.native()};
 Progress liveProgress{};
 liveProgress.receiptDirectory=liveStore.native();
 const auto liveReport=execute(liveRequest,liveProgress);
 if(liveReport.error!=ERROR_SUCCESS)
  std::printf("M22_BOUND_PUBLISH_LIVE_ERROR=%lu\n",liveReport.error);
 bool durableBinding=false;
 std::size_t journalCount=0;
 if(liveStoreCreated){
  for(auto const& file:fs::directory_iterator(liveStore)){
   if(file.path().extension()!=L".bin")continue;
   ++journalCount;
   StageOwnershipReceipt entry{};
   if(readStageReceipt(file.path().native(),entry)&&
      inspectStageReceiptState(file.path().native())==
          StageReceiptState::PublishedVerified&&
      entry.targetLeaf==liveSource.filename().native()&&
      entry.creatorPid==::GetCurrentProcessId()&&
      inspectReceiptCreator(entry)==ReceiptCreatorState::Running&&
      entry.stagePath.find(liveDest.native()+L"\\")==0&&
      !receiptMatchesStage(entry)&&
      !fs::exists(entry.stagePath))
    durableBinding=true;
  }
 }
 test(liveStoreCreated&&liveReport.error==ERROR_SUCCESS&&
      liveProgress.percent==100&&journalCount==1&&durableBinding&&
      get(liveDest/liveSource.filename())=="callback-owned-copy-content"&&
      get(liveSource)=="callback-owned-copy-content",
      "live_staged_copy_callback_durable_receipt_before_publish");
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
 // Deterministically test the exact narrow rename window: before invoking
 // the active worker, this disposable parent IS renameable; from inside
 // the pinned window its rename MUST be blocked by sharing rules.
 const auto pinDest=root/L"m22-pin-target";
 const auto pinOther=root/L"m22-pin-target-swapped";
 const auto pinStore=root/L"m22-pin-store";
 fs::create_directory(pinDest);
 const bool renameable=::MoveFileExW(pinDest.c_str(),pinOther.c_str(),0)&&
                        ::MoveFileExW(pinOther.c_str(),pinDest.c_str(),0);
 const bool pinStoreReady=createPrivateStageReceiptDirectory(
     pinStore.native());
 bool pinReceiptPublished=false;
 bool pinResultOk=false;
 if(renameable&&pinStoreReady){
  Request pinTask=liveRequest;
  pinTask.destination=pinDest.native();
  Progress pinProgress{};
  pinProgress.receiptDirectory=pinStore.native();
  g_directoryProbeAttempted.store(false,std::memory_order_release);
  g_directoryProbeBlocked.store(false,std::memory_order_release);
  setDirectoryRenameProbeForTest(&attemptTestOwnedParentRename);
  const auto pinnedResult=execute(pinTask,pinProgress);
  setDirectoryRenameProbeForTest(nullptr);
  pinResultOk=pinnedResult.error==ERROR_SUCCESS&&
      get(pinDest/liveSource.filename())=="callback-owned-copy-content";
  for(auto const& entry:fs::directory_iterator(pinStore)){
   if(entry.path().extension()!=L".bin")continue;
   StageOwnershipReceipt receipt{};
   if(readStageReceipt(entry.path().native(),receipt)&&
      inspectStageReceiptState(entry.path().native())==
          StageReceiptState::PublishedVerified)
    pinReceiptPublished=true;
  }
 }
 test(renameable&&pinStoreReady&&pinResultOk&&pinReceiptPublished&&
      g_directoryProbeAttempted.load(std::memory_order_acquire)&&
      g_directoryProbeBlocked.load(std::memory_order_acquire)&&
      fs::is_directory(pinDest)&&!fs::exists(pinOther),
      "receipt_active_publish_pins_ancestor_against_rename");
#endif
 // Empty-file copies may not emit a progress callback, so the exact
 // completed stage handle must still be bound before publication.
 const auto emptySource=left/L"receipt-empty-file.txt";
 put(emptySource,"");
 Request emptyRequest=liveRequest;
 emptyRequest.sources={emptySource.native()};
 Progress emptyProgress{};
 emptyProgress.receiptDirectory=liveStore.native();
 const auto emptyReport=execute(emptyRequest,emptyProgress);
 if(emptyReport.error!=ERROR_SUCCESS)
  std::printf("M22_BOUND_PUBLISH_EMPTY_ERROR=%lu\n",emptyReport.error);
 bool emptyPublished=false;
 std::size_t receiptFiles=0;
 for(auto const& file:fs::directory_iterator(liveStore)){
  if(file.path().extension()!=L".bin")continue;
  ++receiptFiles;
  StageOwnershipReceipt entry{};
  if(readStageReceipt(file.path().native(),entry)&&
     entry.targetLeaf==emptySource.filename().native()&&
     inspectStageReceiptState(file.path().native())==
         StageReceiptState::PublishedVerified)
   emptyPublished=true;
 }
 test(emptyReport.error==ERROR_SUCCESS&&
      fs::exists(liveDest/emptySource.filename())&&
      fs::file_size(liveDest/emptySource.filename())==0&&
      emptyPublished&&receiptFiles==2,
      "receipt_zero_byte_staged_copy_published_with_bound_identity");
 const auto untrustedDest=root/L"receipt-untrusted-destination";
 fs::create_directory(untrustedDest);
 Request untrustedRequest=liveRequest;
 untrustedRequest.destination=untrustedDest.native();
 Progress deniedJournal{};
 deniedJournal.receiptDirectory=insecureFolder.native();
 const auto journalRejected=execute(untrustedRequest,deniedJournal);
 test(journalRejected.error==ERROR_ACCESS_DENIED&&
      !fs::exists(untrustedDest/liveSource.filename())&&
      get(liveSource)=="callback-owned-copy-content"&&
      get(liveDest/liveSource.filename())=="callback-owned-copy-content"&&
      journalCount==1,
      "live_staged_copy_refuses_untrusted_receipt_directory");

 bool noPartial=true;
 for(auto const& item:fs::directory_iterator(right)){
  if(item.path().filename().native().rfind(L".flyExplorer-copy-",0)==0)
   noPartial=false;
 }
 test(noPartial,"committed_local_copy_has_no_partial_stage");
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
 // Hold a test-owned source with an exclusive Windows handle so IFileOperation
 // encounters a real OS sharing failure, not a mocked HRESULT. Never touch
 // unrelated paths or global Shell state.
 put(left/L"잠금 복사.txt","locked-copy-payload");
 HANDLE lockCopy=::CreateFileW((left/L"잠금 복사.txt").c_str(),
     GENERIC_READ,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool copyBlocked=false,copySourceIntact=false;
 if(lockCopy!=INVALID_HANDLE_VALUE){
  Request locked{};
  locked.kind=Kind::Copy;
  locked.sourceParent=left.native();locked.destination=right.native();
  locked.sources={(left/L"잠금 복사.txt").native()};
  Progress attempt{};
  auto outcome=execute(locked,attempt);
  copyBlocked=outcome.error!=ERROR_SUCCESS;
  ::CloseHandle(lockCopy);
  copySourceIntact=get(left/L"잠금 복사.txt")=="locked-copy-payload";
 }
 test(copyBlocked&&copySourceIntact,
      "sharing_violation_copy_reports_failure_and_preserves_source");
 put(left/L"잠금 이동.txt","locked-move-payload");
 HANDLE lockMove=::CreateFileW((left/L"잠금 이동.txt").c_str(),
     GENERIC_READ,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool moveBlocked=false,moveSourceIntact=false;
 if(lockMove!=INVALID_HANDLE_VALUE){
  Request locked{};
  locked.kind=Kind::Move;
  locked.sourceParent=left.native();locked.destination=right.native();
  locked.sources={(left/L"잠금 이동.txt").native()};
  Progress attempt{};
  auto outcome=execute(locked,attempt);
  moveBlocked=outcome.error!=ERROR_SUCCESS;
  ::CloseHandle(lockMove);
  moveSourceIntact=get(left/L"잠금 이동.txt")=="locked-move-payload";
 }
 test(moveBlocked&&moveSourceIntact,
      "sharing_violation_move_reports_failure_and_preserves_source");
 // The first operation may commit before a later item is blocked. The
 // batch must still fail, and earlier results must be inspected rather than
 // erased on the assumption of transactional rollback.
 put(left/L"일괄 복사 먼저.txt","copy-first");
 put(left/L"일괄 복사 잠금.txt","copy-locked");
 HANDLE batchCopyLock=::CreateFileW((left/L"일괄 복사 잠금.txt").c_str(),
     GENERIC_READ,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool partialCopyOk=false;
 if(batchCopyLock!=INVALID_HANDLE_VALUE){
  Request task{};
  task.kind=Kind::Copy;task.sourceParent=left.native();
  task.destination=right.native();
  task.sources={(left/L"일괄 복사 먼저.txt").native(),
                (left/L"일괄 복사 잠금.txt").native()};
  Progress active{};
  const auto result=execute(task,active);
  ::CloseHandle(batchCopyLock);
  partialCopyOk=result.error!=ERROR_SUCCESS&&
      get(left/L"일괄 복사 먼저.txt")=="copy-first"&&
      get(left/L"일괄 복사 잠금.txt")=="copy-locked"&&
      fs::exists(right/L"일괄 복사 먼저.txt")&&
      get(right/L"일괄 복사 먼저.txt")=="copy-first";
 }
 test(partialCopyOk,"batch_partial_copy_failure_preserves_both_sources");

 put(left/L"일괄 이동 먼저.txt","move-first");
 put(left/L"일괄 이동 잠금.txt","move-locked");
 HANDLE batchMoveLock=::CreateFileW((left/L"일괄 이동 잠금.txt").c_str(),
     GENERIC_READ,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool partialMoveOk=false;
 if(batchMoveLock!=INVALID_HANDLE_VALUE){
  Request task{};
  task.kind=Kind::Move;task.sourceParent=left.native();
  task.destination=right.native();
  task.sources={(left/L"일괄 이동 먼저.txt").native(),
                (left/L"일괄 이동 잠금.txt").native()};
  Progress active{};
  const auto result=execute(task,active);
  ::CloseHandle(batchMoveLock);
  partialMoveOk=result.error!=ERROR_SUCCESS&&
      !fs::exists(left/L"일괄 이동 먼저.txt")&&
      get(right/L"일괄 이동 먼저.txt")=="move-first"&&
      get(left/L"일괄 이동 잠금.txt")=="move-locked";
 }
 test(partialMoveOk,"batch_partial_move_failure_preserves_remaining_source");

 // A locked nested child may interrupt Shell's recursive folder Copy.
 // A folder is not a transaction: preserve every original source byte,
 // and never claim that the destination was automatically rolled back.
 const auto folder=left/L"폴더 부분 실패";
 fs::create_directory(folder);
 put(folder/L"a-first.txt","folder-first-original");
 put(folder/L"z-locked.txt","folder-locked-original");
 HANDLE nestedLock=::CreateFileW((folder/L"z-locked.txt").c_str(),
     GENERIC_READ,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 bool recursiveFailurePreserved=false;
 if(nestedLock!=INVALID_HANDLE_VALUE){
  Request task{};
  task.kind=Kind::Copy;task.sourceParent=left.native();
  task.destination=right.native();
  task.sources={folder.native()};
  Progress active{};
  const auto result=execute(task,active);
  ::CloseHandle(nestedLock);
  const auto target=right/folder.filename();
  const bool firstValid=!fs::exists(target/L"a-first.txt")||
      get(target/L"a-first.txt")=="folder-first-original";
  const bool secondValid=!fs::exists(target/L"z-locked.txt")||
      get(target/L"z-locked.txt")=="folder-locked-original";
  recursiveFailurePreserved=result.error!=ERROR_SUCCESS&&
      get(folder/L"a-first.txt")=="folder-first-original"&&
      get(folder/L"z-locked.txt")=="folder-locked-original"&&
      firstValid&&secondValid;
 }
 test(recursiveFailurePreserved,
      "recursive_copy_nested_lock_reports_failure_and_preserves_source");

 fs::create_directory(left/L"폴더 취소");
 put(left/L"폴더 취소"/L"keep.txt","folder-cancel-original");
 Request canceledFolder{};
 canceledFolder.kind=Kind::Copy;
 canceledFolder.sourceParent=left.native();
 canceledFolder.destination=right.native();
 canceledFolder.sources={(left/L"폴더 취소").native()};
 Progress earlyCancel{};
 earlyCancel.cancel=true;
 const auto canceledFolderResult=execute(canceledFolder,earlyCancel);
 test(canceledFolderResult.error==ERROR_CANCELLED&&
      canceledFolderResult.aborted&&
      get(left/L"폴더 취소"/L"keep.txt")=="folder-cancel-original"&&
      !fs::exists(right/L"폴더 취소"),
      "recursive_copy_preflight_cancel_preserves_entire_source");

 test(kMaxItems>=64,"shared_transfer_budget_exceeds_legacy_32");
 const auto bulkLeft=root/L"대량 왼쪽",bulkRight=root/L"대량 오른쪽";
 fs::create_directory(bulkLeft);fs::create_directory(bulkRight);
 Request bulk;bulk.kind=Kind::Copy;
 bulk.sourceParent=bulkLeft.native();bulk.destination=bulkRight.native();
 for(std::size_t i=0;i<64;++i){
  const auto name=L"대량-"+std::to_wstring(i)+L".txt";
  put(bulkLeft/name,"bulk");
  bulk.sources.push_back((bulkLeft/name).native());
 }
 test(validate(bulk).error==0&&validate(bulk).queued==64,
      "validate_more_than_32_items");
 Progress bulkProgress;
 auto bulkDone=execute(bulk,bulkProgress);
 bool allBulk=bulkDone.error==0&&bulkDone.queued==64;
 for(std::size_t i=0;i<64&&allBulk;++i)
  allBulk=fs::exists(bulkRight/(L"대량-"+std::to_wstring(i)+L".txt"));
 test(allBulk,"actual_ifileoperation_64_item_copy");
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
 r=safe;r.sources.assign(kMaxItems+1,(left/L"가.txt").native());
 test(validate(r).error==ERROR_INVALID_PARAMETER,"reject_over_shared_item_budget");

 if(count==3){
  const fs::path uncRoot(args[2]);
  const auto uncSource=uncRoot/L"원격 원본";
  const auto uncDestination=uncRoot/L"원격 대상";
  fs::create_directories(uncSource);
  fs::create_directories(uncDestination);

  put(left/L"UNC복사.txt","unc-copy");
  Request remoteCopy{};
  remoteCopy.kind=Kind::Copy;
  remoteCopy.sourceParent=left.native();
  remoteCopy.destination=uncDestination.native();
  remoteCopy.sources={(left/L"UNC복사.txt").native()};
  Progress remoteCopyProgress;
  auto remoteCopyDone=execute(remoteCopy,remoteCopyProgress);
  test(remoteCopyDone.error==ERROR_SUCCESS&&
       get(uncDestination/L"UNC복사.txt")=="unc-copy"&&
       fs::exists(left/L"UNC복사.txt"),
       "actual_unc_copy_destination");

  put(uncSource/L"UNC이동.txt","unc-move");
  Request remoteMove{};
  remoteMove.kind=Kind::Move;
  remoteMove.sourceParent=uncSource.native();
  remoteMove.destination=right.native();
  remoteMove.sources={(uncSource/L"UNC이동.txt").native()};
  Progress remoteMoveProgress;
  auto remoteMoveDone=execute(remoteMove,remoteMoveProgress);
  test(remoteMoveDone.error==ERROR_SUCCESS&&
       !fs::exists(uncSource/L"UNC이동.txt")&&
       get(right/L"UNC이동.txt")=="unc-move",
       "actual_unc_move_source");

  put(uncSource/L"UNC휴지통.txt","unc-recycle");
  Request remoteRecycle{};
  remoteRecycle.kind=Kind::Recycle;
  remoteRecycle.recycleConfirmed=true;
  remoteRecycle.sourceParent=uncSource.native();
  remoteRecycle.sources={(uncSource/L"UNC휴지통.txt").native()};
  test(validate(remoteRecycle).error==ERROR_INVALID_NAME,
       "unc_recycle_remains_rejected");

  Request extended=remoteCopy;
  extended.destination=
      L"\\\\?\\UNC\\127.0.0.1\\c$\\flyexplorer-owned-never-used";
  test(validate(extended).error==ERROR_INVALID_NAME,
       "reject_extended_unc_namespace");
 }
 std::printf("M22_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
