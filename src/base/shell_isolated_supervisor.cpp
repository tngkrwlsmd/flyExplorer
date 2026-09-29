#include "shell_isolated_supervisor.h"
#include "shell_isolation_wire.h"
#include <windows.h>
#include <shlwapi.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstring>
#include <map>
#include <mutex>
#include <optional>
#include <thread>
#include <utility>
#include <vector>
namespace fxfile { namespace shellnav {
namespace {
using namespace fxfile::isolation;
constexpr DWORD kDeadlineMs=4500;
constexpr DWORD kMaxAttempts=2;
constexpr DWORD kPollMs=20;
constexpr size_t kWireMax=sizeof(Reply)+kMaxBody;
struct Handle {
    HANDLE h=nullptr;
    Handle()=default;
    explicit Handle(HANDLE value):h(value){}
    ~Handle(){reset();}
    Handle(Handle const&)=delete;
    Handle& operator=(Handle const&)=delete;
    void reset(HANDLE value=nullptr){
        if(h&&h!=INVALID_HANDLE_VALUE)::CloseHandle(h);
        h=value;
    }
    HANDLE release(){HANDLE old=h;h=nullptr;return old;}
    bool valid() const{return h&&h!=INVALID_HANDLE_VALUE;}
};
struct Work {
    std::uint64_t route=0,request=0;
    NavigationAction action=NavigationAction::Open;
    std::uint32_t type=kPath;
    std::wstring path;
    std::vector<unsigned char> pidl;
#if defined(_DEBUG)
    bool ownedDelay=false;
    bool ownedComDelay=false;
    bool ownedComExhaust=false;
#endif
};
struct Reader {
    std::vector<unsigned char> const& bytes;
    size_t pos=0;
    bool valid=true;
    explicit Reader(std::vector<unsigned char> const& body):bytes(body){}
    std::uint32_t number(){
        if(!valid||bytes.size()-pos<4){valid=false;return 0;}
        std::uint32_t n=0;
        std::memcpy(&n,bytes.data()+pos,4);pos+=4;return n;
    }
    static bool validUtf16(std::wstring const& value) {
        for(size_t i=0;i<value.size();++i){
            const auto x=static_cast<unsigned>(value[i]);
            if(!x)return false;
            if(x>=0xd800&&x<=0xdbff){
                if(++i==value.size())return false;
                const auto y=static_cast<unsigned>(value[i]);
                if(y<0xdc00||y>0xdfff)return false;
            }else if(x>=0xdc00&&x<=0xdfff)return false;
        }
        return true;
    }
    std::wstring string(size_t maximum=kMaxItemUnits){
        const auto n=number();
        if(!valid||n>maximum||size_t(n)>(bytes.size()-pos)/2){
            valid=false;return {};
        }
        std::wstring result(n,L'\0');
        if(n)std::memcpy(&result[0],bytes.data()+pos,n*2);
        pos+=size_t(n)*2;
        if(!validUtf16(result)){valid=false;return {};}
        return result;
    }
    Location pidl(){
        Location result;
        const auto n=number();
        if(!valid||n<2||n>kMaxPidl||n>bytes.size()-pos||
           !validPidl(bytes.data()+pos,n)){
            valid=false;return result;
        }
        auto* owned=static_cast<PIDLIST_ABSOLUTE>(::CoTaskMemAlloc(n));
        if(!owned){valid=false;return result;}
        std::memcpy(owned,bytes.data()+pos,n);
        pos+=n;
        result.reset(owned);
        return result;
    }
};
HRESULT parse(std::vector<unsigned char> const& all,
              Snapshot& value,std::wstring& filesystemPath){
    if(all.size()<sizeof(Reply))return HRESULT_FROM_WIN32(ERROR_BAD_LENGTH);
    Reply head{};
    std::memcpy(&head,all.data(),sizeof(head));
    if(head.magic!=kMagic||head.version!=kVersion||
       head.count>kMaxEntries||head.bodyBytes>kMaxBody||
       head.flags&~1u||all.size()!=sizeof(head)+head.bodyBytes)
        return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
    std::vector<unsigned char> body(
        all.begin()+sizeof(head),all.end());
    if(checksum(body.data(),body.size())!=head.checksum)
        return HRESULT_FROM_WIN32(ERROR_CRC);
    if(FAILED(static_cast<HRESULT>(head.hr))){
        if(head.count||head.bodyBytes||head.flags)
            return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
        return static_cast<HRESULT>(head.hr);
    }
    if(head.hr!=S_OK)return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
    Reader reader(body);
    Snapshot fresh;
    fresh.displayName=reader.string();
    fresh.parsingName=reader.string();
    std::wstring path=reader.string(kMaxPathUnits);
    fresh.folder=reader.pidl();
    if(!reader.valid||!fresh.folder.valid())
        return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
    fresh.children.reserve(head.count);
    for(std::uint32_t i=0;i<head.count&&reader.valid;++i){
        Item entry;
        entry.attributes=static_cast<SFGAOF>(reader.number());
        entry.label=reader.string();
        entry.parsingName=reader.string();
        entry.id=reader.pidl();
        if(!reader.valid||!entry.id.valid())break;
        fresh.children.push_back(std::move(entry));
    }
    if(!reader.valid||fresh.children.size()!=head.count||
       reader.pos!=body.size())
        return HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
    fresh.truncated=(head.flags&1)!=0;
    value=std::move(fresh);
    filesystemPath=std::move(path);
    return S_OK;
}
} // namespace

struct IsolatedShellSupervisor::State {
    struct Lane {
        std::mutex mutex;
        HANDLE wake=::CreateEventW(nullptr,FALSE,FALSE,nullptr);
        std::optional<Work> pending;
        std::uint64_t generation=0,activeRoute=0;
        HANDLE activeJob=nullptr; // protected by mutex, worker-owned close
        bool stop=false;
        ~Lane(){if(wake)::CloseHandle(wake);}
    };
    std::mutex lock;
    std::array<std::shared_ptr<Lane>,2> lanes{
       std::make_shared<Lane>(),std::make_shared<Lane>()};
    IsolatedCallback complete;
    std::wstring executable;
    std::uint64_t nextTicket=1;
    bool stopped=false,started=false;
    explicit State(IsolatedCallback cb):complete(std::move(cb)) {}
};
IsolatedShellSupervisor::IsolatedShellSupervisor(IsolatedCallback cb):
    state_(std::make_shared<State>(std::move(cb))) {}
IsolatedShellSupervisor::~IsolatedShellSupervisor(){shutdown();}

bool IsolatedShellSupervisor::start(std::wstring executable){
    auto st=state_;
    if(!st||executable.empty()||executable.size()>32700)return false;
    DWORD attrs=::GetFileAttributesW(executable.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES||attrs&FILE_ATTRIBUTE_DIRECTORY)return false;
    {
        std::lock_guard<std::mutex> guard(st->lock);
        if(st->stopped)return false;
        if(st->started)return true;
        st->executable=std::move(executable);
        st->started=true;
    }
    try{
        for(int i=0;i<2;++i)
            std::thread([st,i]{runLane(st,i);}).detach();
        return true;
    }catch(...){shutdown();return false;}
}
namespace {
// One outstanding active request per pane: a newer tab/request replaces it.
// Any in-flight helper is terminated only through the exact lane-owned JOB.
}
std::uint64_t IsolatedShellSupervisor::submitParsing(
    int side,std::uint64_t route,std::wstring path){
    if(side<0||side>1||!route||path.empty()||
       path.size()>kMaxPathUnits)return 0;
    auto st=state_;
    if(!st)return 0;
    try{
        std::lock_guard<std::mutex> lock(st->lock);
        if(st->stopped||!st->started)return 0;
        Work item;
        item.route=route;item.request=st->nextTicket++;
        item.path=std::move(path);
        auto lane=st->lanes[side];
        {
            std::lock_guard<std::mutex> guard(lane->mutex);
            lane->generation=item.request;
            lane->pending=std::move(item);
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        ::SetEvent(lane->wake);
        return st->nextTicket-1;
    }catch(...){return 0;}
}
std::uint64_t IsolatedShellSupervisor::submit(
    int side,std::uint64_t route,Location target,NavigationAction action){
    if(side<0||side>1||!route||!target.valid())return 0;
    const auto length=::ILGetSize(target.get());
    if(length<2||length>kMaxPidl||
       !validPidl(target.get(),length))return 0;
    auto st=state_;
    if(!st)return 0;
    try{
        Work item;
        item.route=route;item.action=action;
        item.type=kAbsolutePidl;
        auto* ptr=static_cast<unsigned char const*>(static_cast<void const*>(target.get()));
        item.pidl.assign(ptr,ptr+length);
        std::lock_guard<std::mutex> lock(st->lock);
        if(st->stopped||!st->started)return 0;
        item.request=st->nextTicket++;
        auto lane=st->lanes[side];
        {
            std::lock_guard<std::mutex> guard(lane->mutex);
            lane->generation=item.request;
            lane->pending=std::move(item);
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        ::SetEvent(lane->wake);
        return st->nextTicket-1;
    }catch(...){return 0;}
}
void IsolatedShellSupervisor::forget(std::uint64_t route){
    auto st=state_;
    if(!st)return;
    for(auto& lane:st->lanes){
        std::lock_guard<std::mutex> guard(lane->mutex);
        if(lane->pending&&lane->pending->route==route){
            lane->pending.reset();
            ++lane->generation;
        }
        if(lane->activeRoute==route){
            ++lane->generation;
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        ::SetEvent(lane->wake);
    }
}
#if defined(_DEBUG)
std::uint64_t IsolatedShellSupervisor::submitOwnedTestDelay(
    int side,std::uint64_t route,std::wstring folder){
    wchar_t env[8]{};
    if(::GetEnvironmentVariableW(
        L"FLY_M16_OWNED_TEST_ONLY",env,8)!=3||
       wcscmp(env,L"YES"))return 0;
    if(side<0||side>1||!route||folder.empty()||
       folder.size()>kMaxPathUnits)return 0;
    auto st=state_;
    if(!st)return 0;
    try {
        std::lock_guard<std::mutex> lock(st->lock);
        if(st->stopped||!st->started)return 0;
        Work item;
        item.route=route;item.request=st->nextTicket++;
        item.path=std::move(folder);
        item.ownedDelay=true; // set BEFORE waking the helper lane
        auto lane=st->lanes[side];
        {
            std::lock_guard<std::mutex> guard(lane->mutex);
            lane->generation=item.request;
            lane->pending=std::move(item);
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        ::SetEvent(lane->wake);
        return st->nextTicket-1;
    }catch(...){return 0;}
}
std::uint64_t IsolatedShellSupervisor::submitOwnedComDelay(
    int side,std::uint64_t route,std::wstring folder,bool exhaust){
    wchar_t env[8]{};
    if(::GetEnvironmentVariableW(
        L"FLY_M18_OWNED_COM_TEST_ONLY",env,8)!=3 ||
        wcscmp(env,L"YES")||side<0||side>1||!route||
        folder.empty()||folder.size()>kMaxPathUnits)return 0;
    auto st=state_;
    if(!st)return 0;
    try {
        std::lock_guard<std::mutex> lock(st->lock);
        if(st->stopped||!st->started)return 0;
        Work item;
        item.route=route;item.request=st->nextTicket++;
        item.path=std::move(folder);
        item.ownedComDelay=true;
        item.ownedComExhaust=exhaust;
        auto lane=st->lanes[side];
        {
            std::lock_guard<std::mutex> guard(lane->mutex);
            lane->generation=item.request;
            lane->pending=std::move(item);
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        ::SetEvent(lane->wake);
        return st->nextTicket-1;
    }catch(...){return 0;}
}
#endif
void IsolatedShellSupervisor::shutdown() noexcept{
    auto st=std::move(state_);
    if(!st)return;
    {
        std::lock_guard<std::mutex> guard(st->lock);
        st->stopped=true;
        st->complete={};
    }
    for(auto& lane:st->lanes){
        {
            std::lock_guard<std::mutex> guard(lane->mutex);
            lane->stop=true;
            lane->pending.reset();
            ++lane->generation;
            if(lane->activeJob)
                ::TerminateJobObject(lane->activeJob,ERROR_CANCELLED);
        }
        if(lane->wake)::SetEvent(lane->wake);
    }
}

// Every attempt uses unique owned child handles. Never process-enumerate,
// OpenProcess-by-name, or terminate the user's Explorer or legacy flyExplorer.
namespace {
struct Attempt {
    HRESULT hr=E_FAIL;
    bool timeout=false,canceled=false;
    Snapshot snapshot;
    std::wstring path;
};
template<typename Lane>
bool current(std::shared_ptr<Lane> lane,Work const& job){
    std::lock_guard<std::mutex> lock(lane->mutex);
    return !lane->stop&&lane->generation==job.request;
}
template<typename Lane>
Attempt oneAttempt(
    std::shared_ptr<Lane> lane,Work const& job,
    std::wstring const& executable,bool artificialBlock){
    Attempt outcome;
    Handle childInRead,hostInWrite,hostOutRead,childOutWrite,childErr;
    SECURITY_ATTRIBUTES inheritable{sizeof(SECURITY_ATTRIBUTES),nullptr,TRUE};
    HANDLE readIn=nullptr,writeIn=nullptr,readOut=nullptr,writeOut=nullptr;
    if(!::CreatePipe(&readIn,&writeIn,&inheritable,131072))
        return {HRESULT_FROM_WIN32(::GetLastError())};
    childInRead.reset(readIn);hostInWrite.reset(writeIn);
    if(!::SetHandleInformation(hostInWrite.h,HANDLE_FLAG_INHERIT,0))
        return {HRESULT_FROM_WIN32(::GetLastError())};
    if(!::CreatePipe(&readOut,&writeOut,&inheritable,131072))
        return {HRESULT_FROM_WIN32(::GetLastError())};
    hostOutRead.reset(readOut);childOutWrite.reset(writeOut);
    if(!::SetHandleInformation(hostOutRead.h,HANDLE_FLAG_INHERIT,0))
        return {HRESULT_FROM_WIN32(::GetLastError())};
    childErr.reset(::CreateFileW(L"NUL",GENERIC_WRITE,
       FILE_SHARE_READ|FILE_SHARE_WRITE,&inheritable,OPEN_EXISTING,0,nullptr));
    if(!childErr.valid())return {HRESULT_FROM_WIN32(::GetLastError())};

    SIZE_T attrBytes=0;
    ::InitializeProcThreadAttributeList(nullptr,1,0,&attrBytes);
    if(!attrBytes)return {HRESULT_FROM_WIN32(ERROR_INVALID_PARAMETER)};
    std::vector<unsigned char> attrs(attrBytes);
    auto* list=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attrs.data());
    if(!::InitializeProcThreadAttributeList(list,1,0,&attrBytes))
        return {HRESULT_FROM_WIN32(::GetLastError())};
    const HANDLE inherited[]={childInRead.h,childOutWrite.h,childErr.h};
    const bool attrOk=::UpdateProcThreadAttribute(list,0,
       PROC_THREAD_ATTRIBUTE_HANDLE_LIST,const_cast<HANDLE*>(inherited),
       sizeof(inherited),nullptr,nullptr)!=FALSE;
    if(!attrOk){
        const auto err=::GetLastError();
        ::DeleteProcThreadAttributeList(list);
        return {HRESULT_FROM_WIN32(err)};
    }
    STARTUPINFOEXW startup{};
    startup.StartupInfo.cb=sizeof(startup);
    startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput=childInRead.h;
    startup.StartupInfo.hStdOutput=childOutWrite.h;
    startup.StartupInfo.hStdError=childErr.h;
    startup.lpAttributeList=list;
    std::wstring args=L"\""+executable+L"\"";
    if(artificialBlock) {
#if defined(_DEBUG)
        args+=job.ownedComDelay?L" --test-com-block":L" --test-block";
#else
        args+=L" --test-block";
#endif
    }
    std::vector<wchar_t> mutableArgs(args.begin(),args.end());
    mutableArgs.push_back(0);
    PROCESS_INFORMATION process{};
    BOOL created=::CreateProcessW(executable.c_str(),mutableArgs.data(),
      nullptr,nullptr,TRUE,
      CREATE_NO_WINDOW|CREATE_SUSPENDED|EXTENDED_STARTUPINFO_PRESENT,
      nullptr,nullptr,&startup.StartupInfo,&process);
    const DWORD spawnError=::GetLastError();
    ::DeleteProcThreadAttributeList(list);
    if(!created)return {HRESULT_FROM_WIN32(spawnError)};
    Handle childProcess(process.hProcess),childThread(process.hThread);
    Handle jobHandle(::CreateJobObjectW(nullptr,nullptr));
    bool registered=false;
    if(jobHandle.valid()){
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
        limits.BasicLimitInformation.LimitFlags=
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
        limits.BasicLimitInformation.ActiveProcessLimit=1;
        registered=::SetInformationJobObject(jobHandle.h,
          JobObjectExtendedLimitInformation,&limits,sizeof(limits))!=FALSE &&
          ::AssignProcessToJobObject(jobHandle.h,childProcess.h)!=FALSE;
    }
    if(!registered){
        const auto err=::GetLastError();
        ::TerminateProcess(childProcess.h,ERROR_ACCESS_DENIED);
        ::WaitForSingleObject(childProcess.h,2000);
        return {HRESULT_FROM_WIN32(err?err:ERROR_ACCESS_DENIED)};
    }
    {
        std::lock_guard<std::mutex> lock(lane->mutex);
        if(!lane->stop&&lane->generation==job.request){
            lane->activeJob=jobHandle.h;
            lane->activeRoute=job.route;
            registered=true;
        }else registered=false;
    }
    if(!registered){
        ::TerminateJobObject(jobHandle.h,ERROR_CANCELLED);
        ::WaitForSingleObject(childProcess.h,2000);
        outcome.canceled=true;return outcome;
    }
    if(::ResumeThread(childThread.h)==DWORD(-1)){
        outcome.hr=HRESULT_FROM_WIN32(::GetLastError());
        goto cleanup;
    }
    childThread.reset();
    childInRead.reset();
    childOutWrite.reset();
    childErr.reset();

    if(!artificialBlock){
        const size_t units=job.type==kPath?job.path.size():job.pidl.size();
        Request req{kMagic,kVersion,job.type,
          static_cast<std::uint32_t>(units)};
        bool sent=true;
        DWORD written=0;
        if(!::WriteFile(hostInWrite.h,&req,sizeof(req),&written,nullptr)||
           written!=sizeof(req))sent=false;
        const void* data=job.type==kPath
            ?static_cast<void const*>(job.path.data())
            :static_cast<void const*>(job.pidl.data());
        const size_t byteCount=job.type==kPath
            ?units*sizeof(wchar_t):units;
        if(sent&&byteCount){
            written=0;
            if(!::WriteFile(hostInWrite.h,data,
               static_cast<DWORD>(byteCount),&written,nullptr)||
               written!=byteCount)sent=false;
        }
        if(!sent){
            outcome.hr=HRESULT_FROM_WIN32(ERROR_WRITE_FAULT);
            goto cleanup;
        }
    }
    hostInWrite.reset();
    {
        const ULONGLONG started=::GetTickCount64();
        std::vector<unsigned char> frame;
        frame.reserve(4096);
        size_t expected=0;
        bool bad=false;
        for(;;){
            if(!current(lane,job)){
                outcome.canceled=true;break;
            }
            if(::GetTickCount64()-started>=kDeadlineMs){
                outcome.timeout=true;
                outcome.hr=HRESULT_FROM_WIN32(ERROR_TIMEOUT);
                break;
            }
            DWORD available=0;
            bool readProgress=false;
            if(!::PeekNamedPipe(hostOutRead.h,nullptr,0,nullptr,
                               &available,nullptr)){
                if(::WaitForSingleObject(childProcess.h,0)!=WAIT_OBJECT_0){
                    outcome.hr=HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE);
                    break;
                }
            }else if(available){
                if(available>kWireMax-frame.size()){
                    bad=true;break;
                }
                const DWORD chunk=std::min<DWORD>(available,65536);
                const size_t start=frame.size();
                frame.resize(start+chunk);
                DWORD received=0;
                if(!::ReadFile(hostOutRead.h,frame.data()+start,
                              chunk,&received,nullptr)){
                    bad=true;break;
                }
                frame.resize(start+received);
                readProgress=(received!=0);
                if(frame.size()>=sizeof(Reply) && !expected){
                    Reply header{};
                    std::memcpy(&header,frame.data(),sizeof(header));
                    if(header.magic!=kMagic||header.version!=kVersion||
                       header.bodyBytes>kMaxBody||header.count>kMaxEntries ||
                       (header.flags&~1u)){bad=true;break;}
                    expected=sizeof(Reply)+header.bodyBytes;
                }
                if(expected&&frame.size()>expected){bad=true;break;}
            }
            if(::WaitForSingleObject(childProcess.h,0)==WAIT_OBJECT_0){
                DWORD exitCode=0;
                ::GetExitCodeProcess(childProcess.h,&exitCode);
                if(expected&&frame.size()==expected&&exitCode==0){
                    outcome.hr=parse(frame,outcome.snapshot,outcome.path);
                    break;
                }
                // Exit is not EOF. A fast helper can finish generating a
                // large response while the pipe still holds unread bytes.
                // Continue bounded draining only after positive progress;
                // an exited helper with an empty pipe and partial reply
                // is a genuine broken response, never a success.
                if(!bad&&exitCode==0&&readProgress&&
                   (!expected||frame.size()<expected))continue;
                outcome.hr=HRESULT_FROM_WIN32(
                    bad?ERROR_INVALID_DATA:ERROR_BROKEN_PIPE);
                break;
            }
            if(bad){
                outcome.hr=HRESULT_FROM_WIN32(ERROR_INVALID_DATA);
                break;
            }
            ::WaitForSingleObject(lane->wake,kPollMs);
        }
    }
cleanup:
    {
        std::lock_guard<std::mutex> lock(lane->mutex);
        // Never close the job while another thread can still refer to it.
        if(lane->activeJob==jobHandle.h){
            lane->activeJob=nullptr;
            lane->activeRoute=0;
        }
    }
    if(::WaitForSingleObject(childProcess.h,0)!=WAIT_OBJECT_0)
        ::TerminateJobObject(jobHandle.h,
          outcome.timeout?ERROR_TIMEOUT:ERROR_CANCELLED);
    ::WaitForSingleObject(childProcess.h,2000);
    return outcome;
}
} // namespace
void IsolatedShellSupervisor::runLane(std::shared_ptr<State> st,
                                     int side) noexcept{
    auto lane=st->lanes[side];
    for(;;){
        Work item;
        {
            std::lock_guard<std::mutex> lock(lane->mutex);
            if(lane->stop)break;
            if(lane->pending){
                item=std::move(*lane->pending);
                lane->pending.reset();
            }
        }
        if(!item.request){
            ::WaitForSingleObject(lane->wake,INFINITE);
            continue;
        }
        IsolatedResult result;
        result.route=item.route;result.request=item.request;
        result.action=item.action;
        result.networkRequest=(item.type==kPath &&
            item.path.size()>=2 && item.path[0]==L'\\' &&
            item.path[1]==L'\\');
        try{
            for(DWORD attempt=0;attempt<kMaxAttempts;++attempt){
                if(!current(lane,item))break;
                bool testBlock=false;
#if defined(_DEBUG)
                testBlock=((item.ownedDelay||item.ownedComDelay)&&attempt==0)
                    ||(item.ownedComDelay&&item.ownedComExhaust);
#endif
                auto outcome=oneAttempt(
                    lane,item,st->executable,testBlock);
                if(outcome.canceled||!current(lane,item))break;
                result.attempts=attempt+1;
                if(outcome.timeout&&attempt+1<kMaxAttempts){
                    result.recovered=true;
                    continue;
                }
                result.hr=outcome.hr;
                result.timedOut=outcome.timeout;
                if(SUCCEEDED(result.hr)){
                    result.snapshot=std::move(outcome.snapshot);
                    result.filesystemPath=std::move(outcome.path);
                }
                IsolatedCallback cb;
                {
                    std::lock_guard<std::mutex> guard(st->lock);
                    if(!st->stopped)cb=st->complete;
                }
                if(cb&&current(lane,item)){
                    try{cb(std::move(result));}catch(...){}
                }
                break;
            }
        }catch(...){
            IsolatedCallback cb;
            {
                std::lock_guard<std::mutex> guard(st->lock);
                if(!st->stopped)cb=st->complete;
            }
            if(cb&&current(lane,item)){
                result.hr=E_OUTOFMEMORY;
                try{cb(std::move(result));}catch(...){}
            }
        }
    }
}
} } // namespace fxfile::shellnav
