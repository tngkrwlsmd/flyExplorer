// R07-15 actual FileOperationController.cpp linked into an isolated native fixture.
// Synthetic rename completion is used ONLY to test controller ownership.
#include "../../../app/winui/file_operation_controller.h"
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <functional>
#include <future>
#include <iostream>
#include <string>
#include <thread>

using Controller=fxfile::previewops::FileOperationController;
using Candidate=Controller::RenameRestoreCandidate;
using Context=Controller::Context;

// Abort rather than allow accidental Shell transfers from this fixture.
namespace fxfile::shelltransfer {
Report execute(Request const&,Progress&) noexcept { std::abort(); }
Report executeIsolated(Request const&,Progress&) noexcept { std::abort(); }
}

struct Scenario {
    Controller controller;
    Context context{};

    Scenario(){
        context.windowTabIdentity=501;
        context.side=0;
        context.tab=2;
        context.route=71;
        context.visibleFolder=L"C:\\__r07_virtual_owner_fixture__";
        context.visibleShellFolder=L"shell:Downloads";
    }

    bool prime(){
        // An invalid leaf returns ERROR_INVALID_NAME BEFORE any disk access.
        // The worker only advances the real controller's ticket.
        fxfile::filecommand::Request request{};
        request.kind=fxfile::filecommand::Kind::CreateFolder;
        request.parent=context.visibleFolder;
        request.name=L"invalid\\leaf";
        auto signal=std::make_shared<std::promise<void>>();
        auto ready=signal->get_future();
        const auto status=controller.startFileCommand(
            request,context,
            [signal](Controller::UiTask){
                signal->set_value(); // discard the worker's invalid result
                return true;
            },
            [](Controller::FileCommandCompletion){});
        if(status!=Controller::StartStatus::Started||
           ready.wait_for(std::chrono::seconds(10))!=std::future_status::ready)
            return false;
        // A synthetic successful rename is accepted only into controller state.
        // No file was renamed, created, read or restored.
        Controller::FileCommandCompletion completion{};
        completion.ticket=1; // first command of a fresh controller
        completion.context=context;
        completion.kind=fxfile::filecommand::Kind::RenameSelected;
        completion.originalRenameSource=L"C:\\__r07_virtual_owner_fixture__\\original.txt";
        completion.result.error=ERROR_SUCCESS;
        completion.result.target=L"C:\\__r07_virtual_owner_fixture__\\renamed.txt";
        auto& e=completion.result.renameEvidence;
        e.verified=true;e.volumeSerial=29;
        e.fileId[0]=0xAB;e.fileId[15]=0xCD;
        e.fileSize=42;e.lastWriteTime=987654;
        return controller.acceptFileCommand(completion,context)==
               Controller::CommandDisposition::Succeeded;
    }
    std::optional<Candidate> take(){
        return controller.takeRenameRestoreCandidate(context);
    }
};

int main(){
    int passed=0,failed=0;
    auto check=[&](bool ok,char const* label){
        if(ok){++passed;std::cout<<"R07_OWNER_PASS "<<label<<"\n";}
        else {++failed;std::cout<<"R07_OWNER_FAIL "<<label<<"\n";}
    };
    {
        Scenario s;
        const bool ready=s.prime();
        auto c=ready?s.take():std::nullopt;
        check(ready&&c.has_value(),"accepted_verified_receipt");
        check(!s.take().has_value(),"single_take");
        check(c&&s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context),
              "valid_recheck");
        check(c&&!s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context),
              "recheck_consumes_lease");
    }
    auto reject=[&](char const* label,
                    std::function<void(Candidate&,Context&)> alter){
        Scenario s;
        const bool ready=s.prime();
        auto taken=ready?s.take():std::nullopt;
        if(taken){
            auto live=s.context;
            alter(*taken,live);
            const bool first=s.controller.recheckAndRetireRenameRestoreCandidate(*taken,live);
            const bool replay=s.controller.recheckAndRetireRenameRestoreCandidate(*taken,s.context);
            check(!first&&!replay,label);
        }else check(false,label);
    };
    reject("window_tab_changed",[](Candidate&,Context& c){++c.windowTabIdentity;});
    reject("pane_changed",[](Candidate&,Context& c){c.side=1;});
    reject("folder_tab_changed",[](Candidate&,Context& c){++c.tab;});
    reject("route_changed",[](Candidate&,Context& c){++c.route;});
    reject("visible_folder_changed",[](Candidate&,Context& c){c.visibleFolder+=L"2";});
    reject("visible_shell_changed",[](Candidate&,Context& c){c.visibleShellFolder+=L"2";});
    reject("ticket_mutated",[](Candidate& c,Context&){++c.ticket;});
    reject("original_path_mutated",[](Candidate& c,Context&){c.originalPath+=L"2";});
    reject("target_path_mutated",[](Candidate& c,Context&){c.renamed.target+=L"2";});
    reject("file_id_mutated",[](Candidate& c,Context&){++c.renamed.renameEvidence.fileId[0];});
    reject("volume_mutated",[](Candidate& c,Context&){++c.renamed.renameEvidence.volumeSerial;});
    reject("size_mutated",[](Candidate& c,Context&){++c.renamed.renameEvidence.fileSize;});
    reject("mtime_mutated",[](Candidate& c,Context&){++c.renamed.renameEvidence.lastWriteTime;});
    reject("verification_dropped",[](Candidate& c,Context&){c.renamed.renameEvidence.verified=false;});
    {
        Scenario s;
        auto c=s.prime()?s.take():std::nullopt;
        if(c){
            fxfile::shelltransfer::Request transfer{};
            transfer.kind=fxfile::shelltransfer::Kind::Recycle;
            transfer.sourceParent=s.context.visibleFolder;
            auto result=s.controller.requestTransfer(
                transfer,s.context,[](Controller::UiTask){return true;},
                [](Controller::TransferCompletion){});
            check(result==Controller::StartStatus::NeedsRecycleConfirmation&&
                  !s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context),
                  "pending_transfer_invalidates");
        }else check(false,"pending_transfer_invalidates");
    }
    {
        Scenario s;
        auto c=s.prime()?s.take():std::nullopt;
        if(c){
            fxfile::filecommand::Request req{};
            req.kind=fxfile::filecommand::Kind::CreateFolder;
            req.parent=s.context.visibleFolder;req.name=L"invalid\\leaf";
            auto status=s.controller.startFileCommand(
                req,s.context,[](Controller::UiTask){return true;},
                [](Controller::FileCommandCompletion){});
            check(status==Controller::StartStatus::Started&&
                  !s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context),
                  "new_file_command_invalidates");
        }else check(false,"new_file_command_invalidates");
    }
    {
        Scenario s;
        auto c=s.prime()?s.take():std::nullopt;
        s.controller.prepareForClose();
        check(c&&!s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context),
              "close_invalidates");
    }
    {
        Scenario s;
        auto c=s.prime()?s.take():std::nullopt;
        if(c){
            std::atomic<int> accepted{0};
            auto compete=[&](){
                if(s.controller.recheckAndRetireRenameRestoreCandidate(*c,s.context))
                    accepted.fetch_add(1);
            };
            std::thread left(compete),right(compete);
            left.join();right.join();
            check(accepted.load()==1,"racing_claimers_at_most_one");
        }else check(false,"racing_claimers_at_most_one");
    }
    {
        Scenario s;
        const bool ready=s.prime();
        auto other=s.context;++other.route;
        const auto stolen=ready?s.controller.takeRenameRestoreCandidate(other):std::nullopt;
        check(ready&&!stolen&&!s.take(),"stale_initial_owner_discarded");
    }
    std::cout<<"R07_OWNER_NATIVE_SUMMARY "<<passed<<" passed, "<<failed<<" failed.\n";
    return failed?1:0;
}
