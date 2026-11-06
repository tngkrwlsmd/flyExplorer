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
#include <deque>
#include <atomic>
#include <memory>
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
// Test-owned substitute for a WinUI dispatcher queue. The Post closure
// owns this queue so detached workers never depend on a stack-only sink.
struct AsyncUiQueue final : std::enable_shared_from_this<AsyncUiQueue> {
    std::mutex mutex;
    std::condition_variable cv;
    std::deque<Controller::UiTask> pending;
    Controller::Post poster(){
        return [self=shared_from_this()](Controller::UiTask task){
            std::lock_guard<std::mutex> lock(self->mutex);
            self->pending.push_back(std::move(task));
            self->cv.notify_all();
            return true;
        };
    }
    std::optional<Controller::UiTask> popFor(
        std::chrono::milliseconds timeout){
        std::unique_lock<std::mutex> lock(mutex);
        if(!cv.wait_for(lock,timeout,[&]{return !pending.empty();}))
            return std::nullopt;
        auto fn=std::move(pending.front());
        pending.pop_front();
        return fn;
    }
};

struct Fixture {
    Controller ctrl;
    Context ctx{};
    fs::path dir,original,target;
    FILE_ID_INFO id{};
    Controller::FileCommandCompletion acceptedCompletion{};
    bool ready=false;
    Fixture(fs::path const& root,wchar_t const* name,
            std::uint64_t windowIdentity=501){
        dir=root/name; original=dir/L"source.txt";target=dir/L"after.txt";
        if(!fs::create_directory(dir))return;
        {std::ofstream f(original,std::ios::binary);
         f<<kBytes;if(!f.good())return;}
        if(!getId(original,id))return;
        ctx.windowTabIdentity=windowIdentity;ctx.side=0;ctx.tab=1;ctx.route=91;
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
    // R07-20: the native worker may finish before the UI task is executed.
    // Delivery is not a mutation authority and never names a global tab.
    {
        Fixture f(owned,L"async-delivery");
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto got=std::make_shared<std::optional<Controller::RestoreCompletion>>();
        auto s=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [got](Controller::RestoreCompletion value){
                *got=std::move(value);
            }):Controller::StartStatus::StaleConfirmation;
        auto task=q->popFor(std::chrono::milliseconds(4500));
        const bool notYet=!got->has_value();
        if(task)(*task)();
        check(f.ready&&claim&&s==Controller::StartStatus::Started&&
              task&&notYet&&got->has_value()&&f.restored()&&
              got->value().outcome==Controller::RestoreOutcomeClass::VerifiedCommitted&&
              got->value().result.nativeCallAttempted&&
              got->value().ticket==claim->ticket,
              "async_restore_delivered_on_owner_queue");
    }
    {
        Fixture f(owned,L"async-bad-owner");
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto live=f.ctx;
        ++live.route;
        auto s=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,live,q->poster(),
            [](Controller::RestoreCompletion){})
            :Controller::StartStatus::ThreadStartFailed;
        check(claim&&s==Controller::StartStatus::StaleConfirmation&&
              f.unchanged(),"async_wrong_live_context_not_started");
    }
    {
        Fixture f(owned,L"async-nav-after-queue");
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto count=std::make_shared<std::atomic<int>>(0);
        auto s=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        auto task=q->popFor(std::chrono::milliseconds(4500));
        f.ctrl.invalidateRenameOwnerOnNavigation();
        f.ctrl.invalidateRenameOwnerOnNavigation();
        if(task)(*task)();
        check(claim&&s==Controller::StartStatus::Started&&task&&
              f.restored()&&count->load()==0,
              "async_navigation_after_enqueue_suppresses_callback");
    }
    {
        Fixture f(owned,L"async-close-after-queue");
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto count=std::make_shared<std::atomic<int>>(0);
        auto s=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        auto task=q->popFor(std::chrono::milliseconds(4500));
        f.ctrl.prepareForClose();
        if(task)(*task)();
        check(claim&&s==Controller::StartStatus::Started&&task&&
              f.restored()&&count->load()==0,
              "async_close_after_enqueue_suppresses_callback");
    }
    {
        Fixture f(owned,L"async-mid-native-nav");
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto count=std::make_shared<std::atomic<int>>(0);
        NativePause pause{};
        gNativePause=&pause;
        auto started=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        bool entered=false;
        {
            std::unique_lock<std::mutex> lock(pause.mutex);
            entered=pause.signal.wait_for(lock,std::chrono::seconds(5),
                [&]{return pause.entered;});
        }
        f.ctrl.invalidateRenameOwnerOnNavigation();
        {
            std::lock_guard<std::mutex> lock(pause.mutex);
            pause.resume=true;
        }
        pause.signal.notify_all();
        for(int i=0;i<120&&!f.restored();++i)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        auto late=q->popFor(std::chrono::milliseconds(300));
        gNativePause=nullptr;
        check(claim&&started==Controller::StartStatus::Started&&
              entered&&f.restored()&&!late&&count->load()==0,
              "async_navigation_during_native_suppresses_callback");
    }
    {
        auto f=std::make_unique<Fixture>(owned,L"async-owner-destroy");
        auto claim=f->ready?f->take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto count=std::make_shared<std::atomic<int>>(0);
        const auto original=f->original;
        NativePause pause{};
        gNativePause=&pause;
        auto started=claim?f->ctrl.startTakenRenameRestoreAsync(
            *claim,f->ctx,q->poster(),
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        bool entered=false;
        {
            std::unique_lock<std::mutex> lock(pause.mutex);
            entered=pause.signal.wait_for(lock,std::chrono::seconds(5),
                [&]{return pause.entered;});
        }
        // The detached worker must have captured SharedState, not &Fixture.
        f.reset();
        {
            std::lock_guard<std::mutex> lock(pause.mutex);
            pause.resume=true;
        }
        pause.signal.notify_all();
        for(int i=0;i<120&&read(original)!=kBytes;++i)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        auto late=q->popFor(std::chrono::milliseconds(300));
        gNativePause=nullptr;
        check(claim&&started==Controller::StartStatus::Started&&
              entered&&read(original)==kBytes&&!late&&count->load()==0,
              "async_destroy_during_native_mutation_is_safe");
    }
    {
        Fixture f(owned,L"async-post-rejected");
        auto claim=f.ready?f.take():std::nullopt;
        auto count=std::make_shared<std::atomic<int>>(0);
        auto started=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,[](Controller::UiTask){return false;},
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        for(int i=0;i<120&&(!f.restored()||f.ctrl.busy());++i)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        check(claim&&started==Controller::StartStatus::Started&&
              f.restored()&&!f.ctrl.busy()&&count->load()==0,
              "async_failed_post_does_not_retry_native_mutation");
    }
    {
        Fixture f(owned,L"async-occupied-outcome");
        auto claim=f.ready?f.take():std::nullopt;
        if(claim){
            std::ofstream occupant(f.original,std::ios::binary);
            occupant<<kCollision;
        }
        auto q=std::make_shared<AsyncUiQueue>();
        auto got=std::make_shared<std::optional<Controller::RestoreCompletion>>();
        auto started=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [got](Controller::RestoreCompletion value){
                *got=std::move(value);
            }):Controller::StartStatus::StaleConfirmation;
        auto task=q->popFor(std::chrono::milliseconds(4500));
        if(task)(*task)();
        check(claim&&started==Controller::StartStatus::Started&&
              got->has_value()&&
              got->value().outcome==Controller::RestoreOutcomeClass::NotAttempted&&
              got->value().result.status==Status::OriginalOccupiedOrUnknown&&
              !got->value().result.nativeCallAttempted&&
              read(f.original)==kCollision&&read(f.target)==kBytes,
              "async_occupied_original_reports_no_native_attempt");
    }
    // R07-23: a claimed rename belongs to exactly one original WindowTab,
    // pane, PaneTab, route and folder. A bad start must not mutate anything.
    auto wrongOwner=[&](wchar_t const* name,char const* label,
        std::function<void(Context&)> modify){
        Fixture f(owned,name);
        auto claim=f.ready?f.take():std::nullopt;
        if(!claim){check(false,label);return;}
        auto context=f.ctx;
        modify(context);
        auto q=std::make_shared<AsyncUiQueue>();
        auto called=std::make_shared<std::atomic<int>>(0);
        auto result=f.ctrl.startTakenRenameRestoreAsync(
            *claim,context,q->poster(),
            [called](Controller::RestoreCompletion){++*called;});
        bool queued=false;
        {
            std::lock_guard<std::mutex> lock(q->mutex);
            queued=!q->pending.empty();
        }
        check(result==Controller::StartStatus::StaleConfirmation&&
              !queued&&called->load()==0&&!f.ctrl.busy()&&f.unchanged(),
              label);
    };
    wrongOwner(L"async-wrong-window","async_foreign_window_not_started",
        [](Context& x){++x.windowTabIdentity;});
    wrongOwner(L"async-wrong-pane","async_foreign_pane_not_started",
        [](Context& x){x.side=1;});
    wrongOwner(L"async-wrong-tab","async_foreign_panetab_not_started",
        [](Context& x){++x.tab;});
    wrongOwner(L"async-wrong-route","async_foreign_route_not_started",
        [](Context& x){++x.route;});
    wrongOwner(L"async-wrong-folder","async_foreign_folder_not_started",
        [](Context& x){x.visibleFolder+=L"-changed";});
    wrongOwner(L"async-wrong-shell-folder","async_foreign_shell_folder_not_started",
        [](Context& x){x.visibleShellFolder+=L"-changed";});
    {
        Fixture a(owned,L"async-queue-window-a",701);
        Fixture b(owned,L"async-queue-window-b",702);
        auto ca=a.ready?a.take():std::nullopt;
        auto cb=b.ready?b.take():std::nullopt;
        auto qa=std::make_shared<AsyncUiQueue>();
        auto qb=std::make_shared<AsyncUiQueue>();
        auto oa=std::make_shared<std::optional<Controller::RestoreCompletion>>();
        auto ob=std::make_shared<std::optional<Controller::RestoreCompletion>>();
        auto sa=ca?a.ctrl.startTakenRenameRestoreAsync(
            *ca,a.ctx,qa->poster(),[oa](Controller::RestoreCompletion x){
                *oa=std::move(x);
            }):Controller::StartStatus::StaleConfirmation;
        auto sb=cb?b.ctrl.startTakenRenameRestoreAsync(
            *cb,b.ctx,qb->poster(),[ob](Controller::RestoreCompletion x){
                *ob=std::move(x);
            }):Controller::StartStatus::StaleConfirmation;
        auto ta=qa->popFor(std::chrono::milliseconds(4500));
        auto tb=qb->popFor(std::chrono::milliseconds(4500));
        if(tb)(*tb)();
        if(ta)(*ta)();
        check(ca&&cb&&ta&&tb&&sa==Controller::StartStatus::Started&&
              sb==Controller::StartStatus::Started&&oa->has_value()&&
              ob->has_value()&&oa->value().ticket==ca->ticket&&
              ob->value().ticket==cb->ticket&&
              oa->value().context.windowTabIdentity==701&&
              ob->value().context.windowTabIdentity==702&&
              oa->value().outcome==
                Controller::RestoreOutcomeClass::VerifiedCommitted&&
              ob->value().outcome==
                Controller::RestoreOutcomeClass::VerifiedCommitted&&
              a.restored()&&b.restored(),
              "async_separate_windows_cannot_exchange_queued_results");
    }
    {
        Fixture f(owned,L"async-queue-replayed",703);
        auto claim=f.ready?f.take():std::nullopt;
        auto q=std::make_shared<AsyncUiQueue>();
        auto count=std::make_shared<std::atomic<int>>(0);
        auto status=claim?f.ctrl.startTakenRenameRestoreAsync(
            *claim,f.ctx,q->poster(),
            [count](Controller::RestoreCompletion){++*count;})
            :Controller::StartStatus::StaleConfirmation;
        auto task=q->popFor(std::chrono::milliseconds(4500));
        if(task){
            auto copied=*task;
            (*task)();
            copied(); // faulty host invokes a copied queued task again
            (*task)();
        }
        check(claim&&task&&status==Controller::StartStatus::Started&&
              f.restored()&&count->load()==1,
              "async_duplicate_queued_task_delivers_callback_once");
    }
    // R07-23E: an actual file command can finish after the UI queue refuses
    // delivery. This must release busy without calling a UI completion or
    // reissuing the mutation. The disposable fixture owns both file paths.
    {
        const auto dir=owned/L"file-command-post-rejected";
        const bool made=fs::create_directory(dir);
        const auto original=dir/L"source.txt",target=dir/L"after.txt";
        if(made){
            std::ofstream out(original,std::ios::binary);
            out<<kBytes;
        }
        FILE_ID_INFO before{},after{};
        const bool sourceReady=made&&getId(original,before);
        Controller controller;
        Context context{};
        context.windowTabIdentity=801;
        context.side=0;
        context.tab=0;
        context.route=92;
        context.visibleFolder=dir.native();
        context.visibleShellFolder=dir.native();
        fxfile::filecommand::Request request{};
        request.kind=fxfile::filecommand::Kind::RenameSelected;
        request.parent=dir.native();
        request.source=original.native();
        request.name=target.filename().native();
        auto postCalls=std::make_shared<std::atomic<int>>(0);
        auto callbackCalls=std::make_shared<std::atomic<int>>(0);
        const auto started=sourceReady?controller.startFileCommand(
            std::move(request),context,
            [postCalls](Controller::UiTask){++*postCalls;return false;},
            [callbackCalls](Controller::FileCommandCompletion){
                ++*callbackCalls;
            }):Controller::StartStatus::InvalidVisibleContext;
        for(int i=0;i<500&&(postCalls->load()==0||controller.busy());++i)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        check(sourceReady&&started==Controller::StartStatus::Started&&
              postCalls->load()==1&&callbackCalls->load()==0&&
              !controller.busy()&&!fs::exists(original)&&
              getId(target,after)&&same(before,after)&&read(target)==kBytes,
              "file_command_post_rejected_releases_busy");
    }
    std::printf("R07_DISPATCH_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
    return fail?1:0;
}
