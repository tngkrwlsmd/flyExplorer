// F03 bounded parent-side process supervisor; no COM, WinUI or file reads.
// This code is a fault boundary, not a sandbox. Never invoke on the XAML STA.
#include "file_preview_supervisor.h"
#include <Windows.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace fxfile::previewsupervisor {
namespace {
class Handle final {
public:
    Handle()=default;
    explicit Handle(HANDLE h) noexcept: h_(h) {}
    ~Handle() {reset();}
    Handle(Handle const&)=delete;
    Handle& operator=(Handle const&)=delete;
    Handle(Handle&& other) noexcept:h_(other.release()) {}
    Handle& operator=(Handle&& other) noexcept {
        if(this!=&other)reset(other.release());
        return *this;
    }
    HANDLE get() const noexcept {return h_;}
    explicit operator bool() const noexcept {
        return h_ && h_!=INVALID_HANDLE_VALUE;
    }
    void reset(HANDLE h=nullptr) noexcept {
        if(*this)::CloseHandle(h_);
        h_=h;
    }
    HANDLE* put() noexcept {reset();return &h_;}
    HANDLE release() noexcept {HANDLE h=h_;h_=nullptr;return h;}
private:
    HANDLE h_=nullptr;
};

class Attributes final {
public:
    Attributes() noexcept {
        SIZE_T count=0;
        ::InitializeProcThreadAttributeList(nullptr,1,0,&count);
        if(!count)return;
        memory_=::HeapAlloc(::GetProcessHeap(),0,count);
        if(memory_&&::InitializeProcThreadAttributeList(
            list(),1,0,&count))initialized_=true;
    }
    ~Attributes() {
        if(initialized_)::DeleteProcThreadAttributeList(list());
        if(memory_)::HeapFree(::GetProcessHeap(),0,memory_);
    }
    Attributes(Attributes const&)=delete;
    Attributes& operator=(Attributes const&)=delete;
    LPPROC_THREAD_ATTRIBUTE_LIST list() const noexcept {
        return static_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(memory_);
    }
    bool allow(HANDLE (&handles)[3]) noexcept {
        return initialized_&&::UpdateProcThreadAttribute(
            list(),0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,handles,
            sizeof(handles),nullptr,nullptr)!=FALSE;
    }
private:
    void* memory_=nullptr;
    bool initialized_=false;
};

bool writeAll(HANDLE h,void const* bytes,std::size_t size) noexcept {
    auto* p=static_cast<std::uint8_t const*>(bytes);
    while(size) {
        DWORD sent=0;
        auto chunk=static_cast<DWORD>((std::min)(size,std::size_t{65536}));
        if(!::WriteFile(h,p,chunk,&sent,nullptr)||!sent||sent>chunk)return false;
        p+=sent;size-=sent;
    }
    return true;
}
bool readAll(HANDLE h,void* bytes,std::size_t size) noexcept {
    auto* p=static_cast<std::uint8_t*>(bytes);
    while(size) {
        DWORD got=0;
        auto chunk=static_cast<DWORD>((std::min)(size,std::size_t{65536}));
        if(!::ReadFile(h,p,chunk,&got,nullptr)||!got||got>chunk)return false;
        p+=got;size-=got;
    }
    return true;
}
bool exactHelperPath(std::wstring const& value) noexcept {
    constexpr std::wstring_view suffix=L"\\FlyShellIsolationHelper.exe";
    if(!previewpolicy::canonicalLocalPath(value) ||
       !previewpolicy::endsWithAsciiNoCase(value,suffix))return false;
    wchar_t root[4]={value[0],L':',L'\\',0};
    if(::GetDriveTypeW(root)!=DRIVE_FIXED)return false;
    const DWORD attrs=::GetFileAttributesW(value.c_str());
    return attrs!=INVALID_FILE_ATTRIBUTES &&
        !(attrs&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT));
}
bool jobKillOnClose(HANDLE job) noexcept {
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limit{};
    limit.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    return ::SetInformationJobObject(job,JobObjectExtendedLimitInformation,
           &limit,sizeof(limit))!=FALSE;
}
} // namespace

Result run(std::wstring_view helperExe,
           previewpolicy::Candidate const& candidate,
           std::atomic_bool const& cancelled,
           std::uint32_t timeoutMs) noexcept {
    Result output;
    if(cancelled.load()) {output.status=Status::Cancelled;return output;}
    try {
        // Own copies before screening/serializing; the original caller may
        // navigate or clear its selection while this background call runs.
        std::wstring helper(helperExe),path(candidate.absolutePath);
        auto stable=candidate;
        stable.absolutePath=path;
        const auto decision=previewpolicy::screen(stable);
        if(!decision.accepted()||!exactHelperPath(helper))
            return output;
        previewwire::Request request{};
        request.kind=static_cast<std::uint32_t>(decision.kind);
        request.pathUnits=static_cast<std::uint32_t>(path.size());
        request.knownBytes=candidate.knownBytes;
        request.pathChecksum=previewwire::checksum(
            path.data(),path.size()*sizeof(wchar_t));
        if(!previewwire::validHeader(request))return output;

        SECURITY_ATTRIBUTES inherited{sizeof(SECURITY_ATTRIBUTES),nullptr,TRUE};
        Handle inputRead,inputWrite,outputRead,outputWrite;
        if(!::CreatePipe(inputRead.put(),inputWrite.put(),&inherited,0)||
           !::CreatePipe(outputRead.put(),outputWrite.put(),&inherited,0))
            {output.status=Status::LaunchFailed;return output;}
        // The only inheritable descriptors passed to the child are
        // inputRead, outputWrite and the NUL stderr sink.
        if(!::SetHandleInformation(inputWrite.get(),HANDLE_FLAG_INHERIT,0)||
           !::SetHandleInformation(outputRead.get(),HANDLE_FLAG_INHERIT,0))
            {output.status=Status::LaunchFailed;return output;}
        Handle childError(::CreateFileW(L"NUL",GENERIC_WRITE,
            FILE_SHARE_READ|FILE_SHARE_WRITE,&inherited,OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,nullptr));
        if(!childError) {output.status=Status::LaunchFailed;return output;}
        HANDLE allowed[3]={inputRead.get(),outputWrite.get(),childError.get()};
        Attributes attributes;
        if(!attributes.allow(allowed))
            {output.status=Status::LaunchFailed;return output;}

        Handle job(::CreateJobObjectW(nullptr,nullptr));
        if(!job||!jobKillOnClose(job.get()))
            {output.status=Status::LaunchFailed;return output;}

        STARTUPINFOEXW start{};
        start.StartupInfo.cb=sizeof(start);
        start.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
        start.StartupInfo.hStdInput=inputRead.get();
        start.StartupInfo.hStdOutput=outputWrite.get();
        start.StartupInfo.hStdError=childError.get();
        start.lpAttributeList=attributes.list();
        PROCESS_INFORMATION started{};
        std::wstring command=L"\""+helper+L"\" --preview-read";
        const BOOL launched=::CreateProcessW(helper.c_str(),command.data(),
            nullptr,nullptr,TRUE,
            CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT,
            nullptr,nullptr,&start.StartupInfo,&started);
        if(!launched) {output.status=Status::LaunchFailed;return output;}
        Handle child(started.hProcess),primaryThread(started.hThread);
        if(!::AssignProcessToJobObject(job.get(),child.get())) {
            ::TerminateProcess(child.get(),1); // only this suspended child
            output.status=Status::LaunchFailed;return output;
        }
        // Close the child's endpoints in our process so EOF is observable;
        // no child can run outside the owned kill-on-close Job Object.
        inputRead.reset();
        outputWrite.reset();
        childError.reset();
        if(::ResumeThread(primaryThread.get())==DWORD(-1)) {
            ::TerminateJobObject(job.get(),1);
            output.status=Status::LaunchFailed;return output;
        }
        primaryThread.reset();

        Result fromWire;
        std::atomic_bool ioComplete{false};
        // The IO thread owns inputWrite. The supervisor always joins it
        // AFTER stopping the Job on a deadline/cancellation.
        Handle requestPipe(inputWrite.release());
        std::thread io([&,requestPipe=std::move(requestPipe)]() mutable {
            try {
                const bool sent=writeAll(requestPipe.get(),
                    &request,sizeof(request)) &&
                    writeAll(requestPipe.get(),path.data(),
                             path.size()*sizeof(wchar_t));
                requestPipe.reset();
                previewwire::Reply reply{};
                if(sent&&readAll(outputRead.get(),&reply,sizeof(reply)) &&
                   previewwire::validReply(reply) &&
                   (reply.status!=0 ||
                    (reply.kind==request.kind &&
                     reply.byteCount<=decision.maxEncodedBytes))) {
                    std::vector<std::uint8_t> bytes(reply.byteCount);
                    if(bytes.empty()||readAll(outputRead.get(),
                                              bytes.data(),bytes.size())) {
                        if(reply.status==0 &&
                           reply.checksum==previewwire::checksum(
                               bytes.data(),bytes.size())) {
                            fromWire.status=Status::Success;
                            fromWire.kind=decision.kind;
                            fromWire.bytes=std::move(bytes);
                        } else if(reply.status!=0) {
                            fromWire.status=Status::WorkerRejected;
                            fromWire.workerStatus=reply.status;
                        } else fromWire.status=Status::ProtocolError;
                    } else fromWire.status=Status::ProtocolError;
                } else fromWire.status=Status::ProtocolError;
            } catch(...) {fromWire.status=Status::ProtocolError;}
            ioComplete.store(true,std::memory_order_release);
        });

        const auto bounded=(std::max)(50u,(std::min)(timeoutMs,6000u));
        const auto until=std::chrono::steady_clock::now()+
            std::chrono::milliseconds(bounded);
        Status stop=Status::Success;
        bool ended=false;
        while(true) {
            if(cancelled.load()) {stop=Status::Cancelled;break;}
            if(std::chrono::steady_clock::now()>=until)
                {stop=Status::Deadline;break;}
            if(ioComplete.load(std::memory_order_acquire)) {
                DWORD exit=STILL_ACTIVE;
                if(!::GetExitCodeProcess(child.get(),&exit))
                    {stop=Status::ProtocolError;break;}
                if(exit!=STILL_ACTIVE) {
                    ended=true;
                    if(exit!=0)stop=Status::ProtocolError;
                    break;
                }
            }
            ::Sleep(10);
        }
        if(!ended) ::TerminateJobObject(job.get(),1);
        io.join();
        // No worker thread still holds any pipe or result buffer.
        outputRead.reset();
        if(stop!=Status::Success){output.status=stop;return output;}
        return fromWire;
    } catch(...) {
        // This fallback applies only before an IO thread could be joined;
        // all child/job handles are RAII and job closure reaps its own child.
        output.status=Status::LaunchFailed;
        return output;
    }
}
} // namespace fxfile::previewsupervisor
