#include "pch.h"
#include "preview_controller.h"
#include "../../src/base/file_preview_policy.h"
#include <Windows.h>
#include <thread>
#include <utility>

namespace fxfile::previewctrl {
bool PreviewController::start(Request request,Post post,Done done) {
    if(closing_.load()||!post||!done||request.side<0||request.side>1||
       request.key.window==0||request.key.pane==0||
       request.key.tab==0||request.key.generation==0||
       request.filePath!=request.key.selectedIdentity||
       !previewpolicy::canonicalLocalPath(request.filePath)){
        cancel();
        return false;
    }
    cancel();
    // Selection storms must not launch an unbounded number of children.
    auto active=inFlight_;
    auto value=active->load();
    while(value<3&&!active->compare_exchange_weak(value,value+1)){}
    if(value>=3)return false;
    auto ticket=gate_.begin(std::move(request.key));
    try {
        std::thread([request=std::move(request),ticket,
                     active,post=std::move(post),
                     done=std::move(done)]() mutable {
            struct Decrement final {
                std::shared_ptr<std::atomic_uint> count;
                ~Decrement(){count->fetch_sub(1);}
            } doneCounter{active};
            if(ticket.cancel->load())return;
            previewsupervisor::Result result{};
            try{
                std::wstring root;
                if(previewpolicy::canonicalLocalPath(request.filePath)){
                    const wchar_t drive[]={
                        request.filePath[0],L':',L'\\',L'\0'};
                    if(::GetDriveTypeW(drive)==DRIVE_FIXED){
                        WIN32_FILE_ATTRIBUTE_DATA attr{};
                        if(::GetFileAttributesExW(request.filePath.c_str(),
                                GetFileExInfoStandard,&attr) &&
                           !(attr.dwFileAttributes&
                            (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT|
                             FILE_ATTRIBUTE_OFFLINE))){
                            const std::uint64_t bytes=
                                (static_cast<std::uint64_t>(attr.nFileSizeHigh)<<32)|
                                attr.nFileSizeLow;
                            previewpolicy::Candidate candidate{
                                request.filePath,bytes,true,true,true,false,true};
                            const auto screened=previewpolicy::screen(candidate);
                            if(screened.accepted()&&
                               screened.kind==previewpolicy::Kind::Text&&
                               !ticket.cancel->load())
                                result=previewsupervisor::run(
                                    request.siblingHelper,candidate,
                                    *ticket.cancel);
                        }
                    }
                }
            }catch(...){result={};}
            if(ticket.cancel->load())return;
            try {
                Completion completed{};
                completed.side=request.side;
                completed.ticket=ticket;
                completed.result=std::move(result);
                post([done=std::move(done),
                      completed=std::move(completed)]() mutable {
                    done(std::move(completed));
                });
            }catch(...){}
        }).detach();
    }catch(...){
        ticket.cancel->store(true);
        active->fetch_sub(1);
        return false;
    }
    return true;
}
} // namespace fxfile::previewctrl
