// R07-18: genuine rename receipts, fixture-owned files and worker-only restore.
#include "../../../app/winui/file_operation_controller.h"
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <future>
#include <functional>
#include <iterator>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <thread>
#include <mutex>
#include <condition_variable>
namespace fs=std::filesystem;
using Controller=fxfile::previewops::FileOperationController;
using Candidate=Controller::RenameRestoreCandidate;
using Context=Controller::Context;
using Result=fxfile::filecommand::RenameRestoreWriteResult;
using Status=fxfile::filecommand::RenameRestoreWriteStatus;
namespace fxfile::shelltransfer {
Report execute(Request const&,Progress&) noexcept { std::abort(); }
Report executeIsolated(Request const&,Progress&) noexcept { std::abort(); }
}
struct NativePause {
    std::mutex mutex;
    std::condition_variable signal;
    bool entered=false;
    bool resume=false;
};
static NativePause* gNativePause=nullptr;
// Invoked only by the test-built file_command_core.cpp, just before the
// native rename syscall. Never compiled into the product application.
extern "C" void FlyR07RestoreRaceHook(unsigned stage) noexcept {
    if(stage!=2||!gNativePause)return;
    try {
        std::unique_lock<std::mutex> lock(gNativePause->mutex);
        gNativePause->entered=true;
        gNativePause->signal.notify_all();
        gNativePause->signal.wait(lock,[]{
            return gNativePause->resume;
        });
    }catch(...){}
}

static constexpr char kBytes[]="r07-18-owned-unique-payload";
static constexpr char kCollision[]="r07-18-test-occupant";
static std::string read(fs::path const& p) {
    std::ifstream file(p,std::ios::binary);
    return file?std::string(std::istreambuf_iterator<char>(file),
                            std::istreambuf_iterator<char>()):std::string{};
}
static bool getId(fs::path const& p,FILE_ID_INFO& id) {
    HANDLE h=::CreateFileW(p.c_str(),FILE_READ_ATTRIBUTES,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    bool ok=::GetFileInformationByHandleEx(h,FileIdInfo,&id,sizeof(id))!=FALSE;
    return ::CloseHandle(h)!=FALSE&&ok;
}
static bool same(FILE_ID_INFO const& a,FILE_ID_INFO const& b) {
    return a.VolumeSerialNumber==b.VolumeSerialNumber&&
           std::memcmp(a.FileId.Identifier,b.FileId.Identifier,16)==0;
}
struct Fixture {
    Controller ctrl;
    Context ctx{};
    fs::path dir,original,target;
    FILE_ID_INFO id{};
    Controller::FileCommandCompletion acceptedCompletion{};
    bool ready=false;
    Fixture(fs::path const& root,wchar_t const* name){
        dir=root/name; original=dir/L"source.txt";target=dir/L"after.txt";
        if(!fs::create_directory(dir))return;
        {std::ofstream f(original,std::ios::binary);
         f<<kBytes;if(!f.good())return;}
        if(!getId(original,id))return;
        ctx.windowTabIdentity=501;ctx.side=0;ctx.tab=1;ctx.route=91;
        ctx.visibleFolder=dir.native();ctx.visibleShellFolder=dir.native();
        fxfile::filecommand::Request req{};
        req.kind=fxfile::filecommand::Kind::RenameSelected;
        req.parent=dir.native();req.source=original.native();
        req.name=target.filename().native();
        auto signal=std::make_shared<std::promise<Controller::FileCommandCompletion>>();
        auto future=signal->get_future();
        const auto status=ctrl.startFileCommand(
            req,ctx,[](Controller::UiTask fn){fn();return true;},
            [signal](Controller::FileCommandCompletion value){
                signal->set_value(std::move(value));
            });
        if(status!=Controller::StartStatus::Started||
           future.wait_for(std::chrono::seconds(10))!=std::future_status::ready)
            return;
        const auto value=future.get();
        if(value.result.error!=ERROR_SUCCESS||
           !value.result.renameEvidence.verified||
           value.result.target!=target.native()||
           value.originalRenameSource!=original.native()||
           ctrl.acceptFileCommand(value,ctx)!=
               Controller::CommandDisposition::Succeeded)return;
        acceptedCompletion=value;
        FILE_ID_INFO after{};
        ready=!fs::exists(original)&&fs::exists(target)&&
              getId(target,after)&&same(id,after)&&read(target)==kBytes;
    }
    std::optional<Candidate> take(){
        return ctrl.takeRenameRestoreCandidate(ctx);
    }
    Result run(Candidate const& candidate,Context const& live){
        return std::async(std::launch::async,[this,candidate,live]{
            return ctrl.executeTakenRenameRestore(candidate,live);
        }).get();
    }
    bool unchanged() const {
        FILE_ID_INFO now{};
        return !fs::exists(original)&&getId(target,now)&&
               same(id,now)&&read(target)==kBytes;
    }
    bool restored() const {
        FILE_ID_INFO now{};
        return !fs::exists(target)&&getId(original,now)&&
               same(id,now)&&read(original)==kBytes;
    }
};
int wmain(int argc,wchar_t** argv){
    setvbuf(stdout,nullptr,_IONBF,0);
    if(argc!=2)return 2;
    fs::path owned(argv[1]);
    if(!fs::is_directory(owned)||fs::is_symlink(owned))return 3;
    int pass=0,fail=0;
    auto check=[&](bool ok,char const* label){
        std::printf("R07_DISPATCH_%s %s\n",ok?"PASS":"FAIL",label);
        if(ok)++pass;else ++fail;
    };
    {
        Fixture f(owned,L"accepted");
        auto c=f.ready?f.take():std::nullopt;
        check(f.ready&&c.has_value(),"real_verified_rename_accepted");
        auto r=c?f.run(*c,f.ctx):Result{};
        check(r.status==Status::CommittedVerified&&r.nativeCallAttempted&&
              f.restored(),"actual_restore_preserves_file_identity_and_bytes");
        auto replay=c?f.run(*c,f.ctx):Result{};
        check(replay.status==Status::RejectedReceipt&&
              !replay.nativeCallAttempted&&f.restored(),"replay_denied");
    }
    {
        Fixture f(owned,L"read-only");
        auto c=f.ready?f.take():std::nullopt;
        const bool observed=c&&f.ctrl.recheckAndRetireRenameRestoreCandidate(*c,f.ctx);
        auto r=c?f.run(*c,f.ctx):Result{};
        check(observed&&r.status==Status::RejectedReceipt&&
              !r.nativeCallAttempted&&f.unchanged(),
              "read_only_recheck_consumes_claim");
    }
    auto tamper=[&](wchar_t const* name,char const* label,
        std::function<void(Candidate&,Context&)> fn){
        Fixture f(owned,name);
        auto c=f.ready?f.take():std::nullopt;
        if(!c){check(false,label);return;}
        Context live=f.ctx;fn(*c,live);
        auto first=f.run(*c,live),again=f.run(*c,f.ctx);
        check(first.status==Status::RejectedReceipt&&
              !first.nativeCallAttempted&&
              again.status==Status::RejectedReceipt&&
              !again.nativeCallAttempted&&f.unchanged(),label);
    };
    tamper(L"ticket","forged_ticket_denied",
        [](Candidate& c,Context&){++c.ticket;});
    tamper(L"source","forged_original_denied",
        [](Candidate& c,Context&){c.originalPath+=L"x";});
    tamper(L"target","forged_target_denied",
        [](Candidate& c,Context&){c.renamed.target+=L"x";});
    tamper(L"file-id","forged_file_id_denied",
        [](Candidate& c,Context&){c.renamed.renameEvidence.fileId[0]^=1;});
    tamper(L"context","wrong_live_route_denied",
        [](Candidate&,Context& c){++c.route;});
    {
        Fixture f(owned,L"navigation");
        auto c=f.ready?f.take():std::nullopt;
        f.ctrl.invalidateRenameOwnerOnNavigation();
        f.ctrl.invalidateRenameOwnerOnNavigation();
        auto r=c?f.run(*c,f.ctx):Result{};
        check(c&&r.status==Status::RejectedReceipt&&
              !r.nativeCallAttempted&&f.unchanged(),
              "navigation_aba_denied");
    }
    {
        Fixture f(owned,L"close");
        auto c=f.ready?f.take():std::nullopt;
        f.ctrl.prepareForClose();
        auto r=c?f.run(*c,f.ctx):Result{};
        check(c&&r.status==Status::RejectedReceipt&&
              !r.nativeCallAttempted&&f.unchanged(),
              "closed_window_denied");
    }
    {
        Fixture f(owned,L"occupied");
        auto c=f.ready?f.take():std::nullopt;
        if(c){std::ofstream out(f.original,std::ios::binary);out<<kCollision;}
        auto r=c?f.run(*c,f.ctx):Result{};
        auto again=c?f.run(*c,f.ctx):Result{};
        check(c&&r.status==Status::OriginalOccupiedOrUnknown&&
              !r.nativeCallAttempted&&
              again.status==Status::RejectedReceipt&&
              !again.nativeCallAttempted&&
              read(f.original)==kCollision&&read(f.target)==kBytes,
              "occupied_original_preserved_without_native_call");
    }
    {
        Fixture f(owned,L"concurrent");
        auto c=f.ready?f.take():std::nullopt;
        if(c){
            auto run=[&]{return f.ctrl.executeTakenRenameRestore(*c,f.ctx);};
            auto first=std::async(std::launch::async,run);
            auto second=std::async(std::launch::async,run);
            const auto a=first.get(),b=second.get();
            const bool once=(a.status==Status::CommittedVerified&&
                             b.status==Status::RejectedReceipt)||
                            (b.status==Status::CommittedVerified&&
                             a.status==Status::RejectedReceipt);
            check(once&&a.nativeCallAttempted!=b.nativeCallAttempted&&
                  f.restored(),"concurrent_claim_exactly_once");
        }else check(false,"concurrent_claim_exactly_once");
    }
    {
        Fixture f(owned,L"native-paused-navigation");
        auto c=f.ready?f.take():std::nullopt;
        if(!c){
            check(false,"inflight_navigation_returns_before_native");
            check(false,"inflight_new_file_command_remains_busy");
            check(false,"inflight_duplicate_file_completion_rejected");
            check(false,"inflight_duplicate_transfer_completion_rejected");
        }else{
            NativePause pause{};
            gNativePause=&pause;
            auto worker=std::async(std::launch::async,[&]{
                return f.ctrl.executeTakenRenameRestore(*c,f.ctx);
            });
            bool entered=false;
            {
                std::unique_lock<std::mutex> lock(pause.mutex);
                entered=pause.signal.wait_for(lock,std::chrono::seconds(5),
                    [&]{return pause.entered;});
            }
            auto navigation=std::async(std::launch::async,[&]{
                f.ctrl.invalidateRenameOwnerOnNavigation();
            });
            auto checkBusy=std::async(std::launch::async,[&]{
                return f.ctrl.busy();
            });
            auto request=std::async(std::launch::async,[&]{
                fxfile::filecommand::Request req{};
                req.kind=fxfile::filecommand::Kind::CreateFolder;
                req.parent=f.dir.native();
                req.name=L"invalid\\leaf";
                return f.ctrl.startFileCommand(
                    req,f.ctx,[](Controller::UiTask){return true;},
                    [](Controller::FileCommandCompletion){});
            });
            auto duplicateFile=std::async(std::launch::async,[&]{
                return f.ctrl.acceptFileCommand(f.acceptedCompletion,f.ctx);
            });
            auto duplicateTransfer=std::async(std::launch::async,[&]{
                Controller::TransferCompletion fake{};
                fake.ticket=f.acceptedCompletion.ticket;
                fake.context=f.ctx;
                fake.report.error=ERROR_SUCCESS;
                return f.ctrl.acceptTransfer(fake,f.ctx);
            });
            const bool quickNav=navigation.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            const bool quickBusy=checkBusy.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            const bool quickRequest=request.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            const bool quickFile=duplicateFile.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            const bool quickTransfer=duplicateTransfer.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            {
                std::lock_guard<std::mutex> lock(pause.mutex);
                pause.resume=true;
            }
            pause.signal.notify_all();
            navigation.get();
            const bool wasBusy=checkBusy.get();
            const auto start=request.get();
            const auto duplicateFileResult=duplicateFile.get();
            const auto duplicateTransferResult=duplicateTransfer.get();
            const auto out=worker.get();
            gNativePause=nullptr;
            check(entered&&quickNav&&out.status==Status::CommittedVerified&&
                  out.nativeCallAttempted&&f.restored()&&!f.ctrl.busy()&&
                  !f.take(),"inflight_navigation_returns_before_native");
            check(quickBusy&&quickRequest&&wasBusy&&
                  start==Controller::StartStatus::Busy,
                  "inflight_new_file_command_remains_busy");
            check(quickFile&&
                  duplicateFileResult==Controller::CommandDisposition::Ignored,
                  "inflight_duplicate_file_completion_rejected");
            check(quickTransfer&&
                  duplicateTransferResult==Controller::TransferDisposition::Ignored,
                  "inflight_duplicate_transfer_completion_rejected");
        }
    }
    {
        Fixture f(owned,L"native-paused-close");
        auto c=f.ready?f.take():std::nullopt;
        if(!c){
            check(false,"inflight_close_prompt_preserves_native_outcome");
        }else{
            NativePause pause{};
            gNativePause=&pause;
            auto worker=std::async(std::launch::async,[&]{
                return f.ctrl.executeTakenRenameRestore(*c,f.ctx);
            });
            bool entered=false;
            {
                std::unique_lock<std::mutex> lock(pause.mutex);
                entered=pause.signal.wait_for(lock,std::chrono::seconds(5),
                    [&]{return pause.entered;});
            }
            auto close=std::async(std::launch::async,[&]{
                f.ctrl.prepareForClose();
            });
            const bool quick=close.wait_for(
                std::chrono::milliseconds(750))==std::future_status::ready;
            {
                std::lock_guard<std::mutex> lock(pause.mutex);
                pause.resume=true;
            }
            pause.signal.notify_all();
            close.get();
            const auto out=worker.get();
            gNativePause=nullptr;
            check(entered&&quick&&out.status==Status::CommittedVerified&&
                  out.nativeCallAttempted&&f.restored()&&!f.ctrl.busy()&&
                  !f.take(),"inflight_close_prompt_preserves_native_outcome");
        }
    }
    // For future UI result messages, source-native status and "attempted"
    // must be considered together. Nothing here activates an Undo command.
    using Category=Controller::RestoreOutcomeClass;
    {
        Result r{};
        bool all=true;
        for(auto code:{
            Status::RejectedReceipt,Status::RejectedPaths,
            Status::OriginalOccupiedOrUnknown,
            Status::TargetChangedOrUnavailable,Status::AccessUnavailable
        }){
            r.status=code;
            r.nativeCallAttempted=false;
            all=all&&Controller::classifyRestoreOutcome(r)==
                Category::NotAttempted;
        }
        check(all,"all_pre_native_rejections_classified_not_attempted");
    }
    {
        Result r{};
        r.status=Status::CommittedVerified;
        r.nativeCallAttempted=true;
        check(Controller::classifyRestoreOutcome(r)==
              Category::VerifiedCommitted,
              "verified_commit_requires_native_attempt");
    }
    {
        Result r{};
        r.nativeCallAttempted=true;
        r.status=Status::NativeCallFailedUnknownState;
        const bool first=Controller::classifyRestoreOutcome(r)==
            Category::UncertainAfterAttempt;
        r.status=Status::CommittedUnverified;
        check(first&&Controller::classifyRestoreOutcome(r)==
              Category::UncertainAfterAttempt,
              "native_failure_and_unverified_commit_classified_uncertain");
    }
    {
        Result r{};
        r.status=Status::CommittedVerified;
        r.nativeCallAttempted=false;
        const bool impossible=Controller::classifyRestoreOutcome(r)==
            Category::UncertainAfterAttempt;
        r.status=Status::RejectedReceipt;
        r.nativeCallAttempted=true;
        check(impossible&&Controller::classifyRestoreOutcome(r)==
              Category::UncertainAfterAttempt,
              "contradictory_flags_fail_closed_for_reporting");
    }
    std::printf("R07_DISPATCH_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
    return fail?1:0;
}
