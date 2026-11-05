// R07-17: deterministic, fixture-owned races around the real native restore.
// Only this executable defines FLY_R07_RESTORE_RACE_NATIVE_TEST.
// Never supply a personal folder, invoke this from GUI or enable Undo.
#include "../../../src/base/file_command_core.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <system_error>

namespace fs=std::filesystem;
namespace fc=fxfile::filecommand;
using Status=fc::RenameRestoreWriteStatus;

enum class RaceKind { None, OccupyBeforeFinalCheck, OccupyAfterFinalCheck,
                      TryWriter, MoveParentBeforeFinalCheck };
struct RaceState final {
    RaceKind kind=RaceKind::None;
    fs::path original,target,parent,movedParent;
    int early=0,late=0;
    bool injected=false,blocked=false,moved=false,rebound=false;
    DWORD error=ERROR_SUCCESS;
};
static RaceState* gRace=nullptr;
static constexpr char kOriginalPayload[]="r07-race-original-owned-payload";
static constexpr char kIntruderPayload[]="r07-race-external-name-occupant";

static std::string readOwned(fs::path const& path) {
    std::ifstream input(path,std::ios::binary);
    if(!input)return {};
    return std::string(std::istreambuf_iterator<char>(input),
                       std::istreambuf_iterator<char>());
}
static bool readId(fs::path const& path,FILE_ID_INFO& id) noexcept {
    const HANDLE handle=::CreateFileW(path.c_str(),FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
        OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if(handle==INVALID_HANDLE_VALUE)return false;
    const bool ok=::GetFileInformationByHandleEx(
        handle,FileIdInfo,&id,sizeof(id))!=FALSE;
    return ::CloseHandle(handle)!=FALSE&&ok;
}
static bool sameId(FILE_ID_INFO const& a,FILE_ID_INFO const& b) noexcept {
    return a.VolumeSerialNumber==b.VolumeSerialNumber&&
           std::memcmp(a.FileId.Identifier,b.FileId.Identifier,16)==0;
}
extern "C" void FlyR07RestoreRaceHook(unsigned stage) noexcept {
    if(!gRace)return;
    RaceState& s=*gRace;
    if(stage==1u)++s.early;
    else if(stage==2u)++s.late;
    else {s.error=ERROR_INVALID_PARAMETER;return;}
    try{
        if((stage==1u&&s.kind==RaceKind::OccupyBeforeFinalCheck)||
           (stage==2u&&s.kind==RaceKind::OccupyAfterFinalCheck)){
            std::ofstream out(s.original,std::ios::binary|std::ios::trunc);
            out<<kIntruderPayload;
            out.close();
            s.injected=out.good()&&
                       readOwned(s.original)==kIntruderPayload;
        }else if(stage==1u&&s.kind==RaceKind::TryWriter){
            const HANDLE writer=::CreateFileW(
                s.target.c_str(),FILE_WRITE_DATA,
                FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(writer==INVALID_HANDLE_VALUE){
                s.error=::GetLastError();
                s.blocked=s.error==ERROR_SHARING_VIOLATION;
            }else{
                ::CloseHandle(writer);
                s.blocked=false;
            }
        }else if(stage==1u&&s.kind==RaceKind::MoveParentBeforeFinalCheck){
            std::error_code error;
            fs::rename(s.parent,s.movedParent,error);
            s.error=static_cast<DWORD>(error.value());
            s.moved=!error;
            if(s.moved){
                std::error_code createError;
                s.rebound=fs::create_directory(s.parent,createError)&&
                          !createError;
            }else s.blocked=true;
        }
    }catch(...){
        s.error=ERROR_UNHANDLED_EXCEPTION;
    }
}

struct OwnedCase final {
    fs::path parent,original,target;
    fc::Result receipt{};
    FILE_ID_INFO identity{};
    bool ready=false;
    explicit OwnedCase(fs::path root,wchar_t const* suffix) {
        parent=root/suffix;
        if(!fs::create_directory(parent))return;
        original=parent/L"original.txt";
        target=parent/L"renamed.txt";
        {
            std::ofstream file(original,std::ios::binary);
            file<<kOriginalPayload;
            if(!file.good())return;
        }
        fc::Request req{};
        req.kind=fc::Kind::RenameSelected;
        req.parent=parent.native();
        req.source=original.native();
        req.name=target.filename().native();
        receipt=fc::execute(req);
        ready=receipt.error==ERROR_SUCCESS&&receipt.renameEvidence.verified&&
              !fs::exists(original)&&fs::exists(target)&&
              readOwned(target)==kOriginalPayload&&readId(target,identity);
    }
    RaceState hook(RaceKind kind) const {
        RaceState state{};
        state.kind=kind;
        state.parent=parent;state.original=original;state.target=target;
        state.movedParent=parent.parent_path()/
            (parent.filename().native()+L"-moved");
        return state;
    }
};
static fc::RenameRestoreWriteResult run(OwnedCase const& c,RaceState& state) {
    gRace=&state;
    const auto outcome=fc::restoreRenameNoReplace(
        c.original.native(),c.receipt);
    gRace=nullptr;
    return outcome;
}
int wmain(int argc,wchar_t** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    if(argc!=2)return 2;
    const fs::path owned(argv[1]);
    if(!fs::is_directory(owned)||fs::is_symlink(owned))return 3;
    int pass=0,fail=0;
    auto chk=[&](bool ok,char const* what){
        std::printf("R07_RACE_%s %s\n",ok?"PASS":"FAIL",what);
        if(ok)++pass;else ++fail;
    };

    {
        OwnedCase c(owned,L"baseline");
        if(c.ready){
            auto hook=c.hook(RaceKind::None);
            const auto first=run(c,hook);
            FILE_ID_INFO id{};
            chk(first.status==Status::CommittedVerified&&
                first.nativeCallAttempted&&
                readId(c.original,id)&&sameId(c.identity,id)&&
                readOwned(c.original)==kOriginalPayload&&!fs::exists(c.target),
                "baseline_commits_same_id_and_bytes");
            const auto replay=run(c,hook);
            chk(replay.status==Status::OriginalOccupiedOrUnknown&&
                !replay.nativeCallAttempted&&
                readOwned(c.original)==kOriginalPayload,
                "replay_no_mutation");
            chk(hook.early==1&&hook.late==1,
                "both_test_hook_stages_once_on_first_commit");
        }else{
            chk(false,"baseline_commits_same_id_and_bytes");
            chk(false,"replay_no_mutation");
            chk(false,"both_test_hook_stages_once_on_first_commit");
        }
    }
    {
        OwnedCase c(owned,L"before-check");
        if(c.ready){
            auto hook=c.hook(RaceKind::OccupyBeforeFinalCheck);
            const auto outcome=run(c,hook);
            FILE_ID_INFO id{};
            chk(hook.injected&&hook.early==1&&hook.late==0&&
                outcome.status==Status::OriginalOccupiedOrUnknown&&
                !outcome.nativeCallAttempted&&
                readOwned(c.original)==kIntruderPayload&&
                readOwned(c.target)==kOriginalPayload&&
                readId(c.target,id)&&sameId(c.identity,id),
                "injected_original_before_final_guard_rejected");
        }else chk(false,"injected_original_before_final_guard_rejected");
    }
    {
        OwnedCase c(owned,L"before-native");
        if(c.ready){
            auto hook=c.hook(RaceKind::OccupyAfterFinalCheck);
            const auto outcome=run(c,hook);
            FILE_ID_INFO id{};
            chk(hook.injected&&hook.early==1&&hook.late==1&&
                outcome.status==Status::NativeCallFailedUnknownState&&
                outcome.nativeCallAttempted&&
                readOwned(c.original)==kIntruderPayload&&
                readOwned(c.target)==kOriginalPayload&&
                readId(c.target,id)&&sameId(c.identity,id),
                "native_atomic_no_replace_after_last_check");
        }else chk(false,"native_atomic_no_replace_after_last_check");
    }
    {
        OwnedCase c(owned,L"held-target");
        if(c.ready){
            auto hook=c.hook(RaceKind::TryWriter);
            const auto outcome=run(c,hook);
            FILE_ID_INFO id{};
            chk(hook.early==1&&hook.late==1&&hook.blocked&&
                outcome.status==Status::CommittedVerified&&
                readId(c.original,id)&&sameId(c.identity,id)&&
                readOwned(c.original)==kOriginalPayload&&
                !fs::exists(c.target),
                "held_target_denies_external_write_before_commit");
        }else chk(false,"held_target_denies_external_write_before_commit");
    }
    {
        OwnedCase c(owned,L"parent-move");
        if(c.ready){
            auto hook=c.hook(RaceKind::MoveParentBeforeFinalCheck);
            const auto outcome=run(c,hook);
            FILE_ID_INFO id{};
            bool condition=false;
            if(hook.moved){
                const auto movedTarget=hook.movedParent/c.target.filename();
                condition=hook.early==1&&hook.late==0&&
                    outcome.status==Status::RejectedPaths&&
                    !outcome.nativeCallAttempted&&
                    readId(movedTarget,id)&&sameId(c.identity,id)&&
                    readOwned(movedTarget)==kOriginalPayload;
            }else{
                // A denied directory move is NOT evidence that a parent
                // relocation during the final syscall was exercised.
                condition=hook.blocked&&hook.early==1&&hook.late==1&&
                    outcome.status==Status::CommittedVerified&&
                    readId(c.original,id)&&sameId(c.identity,id)&&
                    readOwned(c.original)==kOriginalPayload;
            }
            std::printf("R07_RACE_PARENT_MOVE_ATTEMPT moved=%d rebound=%d error=%lu\n",
                static_cast<int>(hook.moved),static_cast<int>(hook.rebound),
                static_cast<unsigned long>(hook.error));
            chk(condition,"parent_move_before_final_guard_handled_or_blocked");
        }else chk(false,"parent_move_before_final_guard_handled_or_blocked");
    }
    {
        OwnedCase c(owned,L"unverified");
        if(c.ready){
            auto forged=c.receipt;
            forged.renameEvidence.verified=false;
            auto hook=c.hook(RaceKind::OccupyAfterFinalCheck);
            gRace=&hook;
            const auto outcome=fc::restoreRenameNoReplace(
                c.original.native(),forged);
            gRace=nullptr;
            chk(outcome.status==Status::RejectedReceipt&&
                !outcome.nativeCallAttempted&&hook.early==0&&hook.late==0&&
                !fs::exists(c.original)&&
                readOwned(c.target)==kOriginalPayload,
                "forged_receipt_never_reaches_race_or_mutation");
        }else chk(false,"forged_receipt_never_reaches_race_or_mutation");
    }
    std::printf("R07_RACE_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
    return fail?1:0;
}
