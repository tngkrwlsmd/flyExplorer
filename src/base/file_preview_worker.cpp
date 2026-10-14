#include "file_preview_worker.h"
#include "file_preview_worker_wire.h"
#include "file_preview_safe_open.h"
#include "file_preview_reader.h"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <string>
#include <vector>
#include <utility>

namespace fxfile::previewworker {
namespace {
bool exactRead(HANDLE handle,void* output,std::size_t n) noexcept {
    auto* ptr=static_cast<std::uint8_t*>(output);
    while(n){
        DWORD count=0;
        const DWORD step=static_cast<DWORD>((std::min)(
            n,static_cast<std::size_t>(65536)));
        if(!::ReadFile(handle,ptr,step,&count,nullptr)||count==0||
           count>step)return false;
        ptr+=count;n-=count;
    }
    return true;
}
bool exactWrite(HANDLE handle,void const* bytes,std::size_t n) noexcept {
    auto const* ptr=static_cast<std::uint8_t const*>(bytes);
    while(n){
        DWORD sent=0;
        const DWORD step=static_cast<DWORD>((std::min)(
            n,static_cast<std::size_t>(65536)));
        if(!::WriteFile(handle,ptr,step,&sent,nullptr)||sent==0||
           sent>step)return false;
        ptr+=sent;n-=sent;
    }
    return true;
}
bool validUtf16(std::wstring const& value) noexcept {
    for(std::size_t i=0;i<value.size();++i){
        auto const a=static_cast<std::uint16_t>(value[i]);
        if(a==0||a<0x20||a==0x7f)return false;
        if(a>=0xd800&&a<=0xdbff){
            if(++i==value.size())return false;
            auto const b=static_cast<std::uint16_t>(value[i]);
            if(b<0xdc00||b>0xdfff)return false;
        }else if(a>=0xdc00&&a<=0xdfff)return false;
    }
    return true;
}
bool reply(HANDLE h,Status status,previewpolicy::Kind kind,
           std::vector<std::uint8_t> const& bytes) noexcept {
    const bool ok=status==Status::Success;
    previewwire::Reply header{};
    header.status=static_cast<std::uint32_t>(status);
    if(ok){
        if((kind!=previewpolicy::Kind::Text&&kind!=previewpolicy::Kind::Image)||
           bytes.size()>previewwire::kMaxReplyBytes)return false;
        header.kind=static_cast<std::uint32_t>(kind);
        header.byteCount=static_cast<std::uint32_t>(bytes.size());
        header.checksum=previewwire::checksum(bytes.data(),bytes.size());
    }
    return exactWrite(h,&header,sizeof(header)) &&
        (!ok||bytes.empty()||exactWrite(h,bytes.data(),bytes.size()));
}
} // namespace

int runOne(HANDLE input,HANDLE output) noexcept {
    if(!input||input==INVALID_HANDLE_VALUE||
       !output||output==INVALID_HANDLE_VALUE||
       ::GetFileType(input)!=FILE_TYPE_PIPE||
       ::GetFileType(output)!=FILE_TYPE_PIPE)return 10;
    try {
        previewwire::Request head{};
        if(!exactRead(input,&head,sizeof(head)))return 11;
        if(!previewwire::validHeader(head))
            return reply(output,Status::InvalidRequest,
                         previewpolicy::Kind::None,{})?0:12;
        // At most 64 KiB of user-provided UTF-16 path; no unbounded frames.
        std::wstring path(head.pathUnits,L'\0');
        if(!exactRead(input,path.data(),
                      path.size()*sizeof(wchar_t)))return 13;
        if(!validUtf16(path)||
           previewwire::checksum(path.data(),path.size()*sizeof(wchar_t))!=
             head.pathChecksum ||
           !previewpolicy::canonicalLocalPath(path))
            return reply(output,Status::InvalidRequest,
                         previewpolicy::Kind::None,{})?0:14;
        const auto kind=static_cast<previewpolicy::Kind>(head.kind);
        previewpolicy::Candidate candidate{path,head.knownBytes,
            true,true,true,false,true};
        const auto screened=previewpolicy::screen(candidate);
        if(!screened.accepted()||screened.kind!=kind)
            return reply(output,Status::InvalidRequest,
                         previewpolicy::Kind::None,{})?0:15;

        const auto deadline=std::chrono::steady_clock::now()+
            std::chrono::milliseconds(previewwire::kDeadlineMs);
        std::atomic_bool cancel{false};
        // All filesystem access is within the disposable child. The parent
        // MUST kill this exact-owned process/job at its independent deadline.
        auto file=previewsafe::openLocalRegular(candidate,cancel,deadline);
        if(!file.accepted()){
            auto status=Status::UnsafePath;
            if(file.status==previewsafe::Status::Cancelled)status=Status::Cancelled;
            if(file.status==previewsafe::Status::Deadline)status=Status::Deadline;
            return reply(output,status,previewpolicy::Kind::None,{})?0:16;
        }
        auto bytes=previewread::readVerifiedHandle(
            file.file.get(),path,kind,head.knownBytes,cancel,deadline);
        // RAII ancestor guards remain alive until AFTER the read.
        if(!bytes.ok()){
            auto status=Status::ReadRejected;
            if(bytes.status==previewread::Status::Cancelled)status=Status::Cancelled;
            if(bytes.status==previewread::Status::Deadline)status=Status::Deadline;
            return reply(output,status,previewpolicy::Kind::None,{})?0:17;
        }
        if(std::chrono::steady_clock::now()>=deadline)
            return reply(output,Status::Deadline,previewpolicy::Kind::None,{})?0:18;
        return reply(output,Status::Success,kind,bytes.bytes)?0:19;
    }catch(...){
        return reply(output,Status::Internal,previewpolicy::Kind::None,{})?0:20;
    }
}
} // namespace fxfile::previewworker
