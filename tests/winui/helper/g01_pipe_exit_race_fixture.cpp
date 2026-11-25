// Exercise the actual supervisor with real owned Windows pipes/processes.
// Only the test translation unit intercepts the empty-peek scheduling point.
#include <windows.h>
#include <shlwapi.h>
#include "../../../src/base/shell_isolated_supervisor.h"
#include "../../../src/base/shell_isolation_wire.h"
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
#include <cstdio>
#include <cwchar>

static HANDLE ownedProcess=nullptr, releaseReply=nullptr;
static bool scheduleRace=false, raceObserved=false;
static bool eofMode=false, eofObserved=false, releaseOnPoll=false, cancelOnPoll=false;
static HANDLE eofReady=nullptr, releaseExit=nullptr, testWake=nullptr;
static ULONGLONG eofTick=0;
static unsigned eofPolls=0;
static std::function<void()> cancelLane;
static DWORD WINAPI raceWaitForSingleObject(HANDLE object,DWORD delay);
static BOOL WINAPI raceCreateProcessW(LPCWSTR app,LPWSTR command,
    LPSECURITY_ATTRIBUTES processAttributes,LPSECURITY_ATTRIBUTES threadAttributes,
    BOOL inherit,DWORD flags,LPVOID environment,LPCWSTR directory,
    LPSTARTUPINFOW startup,LPPROCESS_INFORMATION process);
static BOOL WINAPI racePeekNamedPipe(HANDLE pipe,LPVOID buffer,DWORD size,
    LPDWORD read,LPDWORD available,LPDWORD left);
#define CreateProcessW raceCreateProcessW
#define PeekNamedPipe racePeekNamedPipe
#define WaitForSingleObject raceWaitForSingleObject
#include "../../../src/base/shell_isolated_supervisor.cpp"
#undef WaitForSingleObject
#undef PeekNamedPipe
#undef CreateProcessW

static BOOL WINAPI raceCreateProcessW(LPCWSTR app,LPWSTR command,
    LPSECURITY_ATTRIBUTES processAttributes,LPSECURITY_ATTRIBUTES threadAttributes,
    BOOL inherit,DWORD flags,LPVOID environment,LPCWSTR directory,
    LPSTARTUPINFOW startup,LPPROCESS_INFORMATION process) {
    BOOL ok=::CreateProcessW(app,command,processAttributes,threadAttributes,
        inherit,flags,environment,directory,startup,process);
    if(ok)ownedProcess=process->hProcess;
    return ok;
}
static BOOL WINAPI racePeekNamedPipe(HANDLE pipe,LPVOID buffer,DWORD size,
    LPDWORD read,LPDWORD available,LPDWORD left) {
    BOOL ok=::PeekNamedPipe(pipe,buffer,size,read,available,left);
    if(ok&&available&&!*available&&scheduleRace){
        scheduleRace=false;
        if(!::SetEvent(releaseReply))::ExitProcess(90);
        // Original cases force the empty-peek/child-exit ordering.
        // New cases keep the exact child alive after it closes stdout.
        if(::WaitForSingleObject(eofMode?eofReady:ownedProcess,2000)!=WAIT_OBJECT_0)
            ::ExitProcess(91);
        raceObserved=true;
        if(eofMode)ok=::PeekNamedPipe(pipe,buffer,size,read,available,left);
    }
    const DWORD error=::GetLastError();
    if(eofMode&&!ok&&error==ERROR_BROKEN_PIPE&&!eofObserved){
        if(::WaitForSingleObject(ownedProcess,0)!=WAIT_TIMEOUT)::ExitProcess(92);
        eofObserved=true;
        eofTick=::GetTickCount64();
    }
    ::SetLastError(error);
    return ok;
}
static DWORD WINAPI raceWaitForSingleObject(HANDLE object,DWORD delay){
    if(eofMode&&eofObserved&&object==testWake){
        ++eofPolls;
        if(eofPolls==1){
            if(cancelOnPoll){cancelLane();return WAIT_OBJECT_0;}
            if(releaseOnPoll&&!::SetEvent(releaseExit))::ExitProcess(93);
        }
    }
    return ::WaitForSingleObject(object,delay);
}
struct TestLane {
    std::mutex mutex;
    bool stop=false;
    std::uint64_t generation=1,activeRoute=0;
    HANDLE activeJob=nullptr,wake=nullptr;
    TestLane():wake(::CreateEventW(nullptr,FALSE,FALSE,nullptr)){}
    ~TestLane(){if(wake)::CloseHandle(wake);}
};
using namespace fxfile::isolation;
static void number(std::vector<unsigned char>& bytes,std::uint32_t value){
    auto p=reinterpret_cast<unsigned char const*>(&value);
    bytes.insert(bytes.end(),p,p+sizeof(value));
}
static void stringValue(std::vector<unsigned char>& bytes,std::wstring const& value){
    number(bytes,static_cast<std::uint32_t>(value.size()));
    auto p=reinterpret_cast<unsigned char const*>(value.data());
    bytes.insert(bytes.end(),p,p+value.size()*sizeof(wchar_t));
}
static void emptyPidl(std::vector<unsigned char>& bytes){
    number(bytes,2);bytes.push_back(0);bytes.push_back(0);
}
static int helper(){
    wchar_t eventName[160]{},mode[40]{};
    if(!::GetEnvironmentVariableW(L"FLY_G01_REPLY_EVENT",eventName,160)||
       !::GetEnvironmentVariableW(L"FLY_G01_REPLY_MODE",mode,40))return 80;
    HANDLE event=::OpenEventW(SYNCHRONIZE,FALSE,eventName);
    if(!event)return 81;
    Request request{};DWORD got=0;
    auto input=::GetStdHandle(STD_INPUT_HANDLE);
    if(!::ReadFile(input,&request,sizeof(request),&got,nullptr)||got!=sizeof(request))return 82;
    std::vector<wchar_t> path(request.length);
    if(!::ReadFile(input,path.data(),request.length*2,&got,nullptr)||got!=request.length*2)return 83;
    if(::WaitForSingleObject(event,2000)!=WAIT_OBJECT_0)return 84;
    ::CloseHandle(event);
    std::vector<unsigned char> body;
    bool large=wcscmp(mode,L"large")==0;
    const bool closeEarly=wcsncmp(mode,L"eof-",4)==0;
    bool success=large||wcscmp(mode,L"success")==0||wcscmp(mode,L"eof-body")==0;
    if(success){
        stringValue(body,large?std::wstring(4096,L'x'):L"owned");
        stringValue(body,L"");stringValue(body,L"");emptyPidl(body);
        if(large)for(int i=0;i<300;++i){
            number(body,0);stringValue(body,std::wstring(100,L'a'));
            stringValue(body,L"");emptyPidl(body);
        }
    }
    Reply reply{kMagic,kVersion,success?S_OK:E_ACCESSDENIED,
        large?300u:0u,static_cast<std::uint32_t>(body.size()),
        checksum(body.data(),body.size()),0};
    if(wcscmp(mode,L"malformed")==0)reply.magic=0;
    auto output=::GetStdHandle(STD_OUTPUT_HANDLE);DWORD sent=0;
    const bool empty=wcscmp(mode,L"empty")==0||
        (closeEarly&&wcscmp(mode,L"eof-header")!=0&&wcscmp(mode,L"eof-body")!=0);
    if(!empty){
        DWORD count=(wcscmp(mode,L"truncated")==0||wcscmp(mode,L"eof-header")==0)?10:sizeof(reply);
        if(!::WriteFile(output,&reply,count,&sent,nullptr)||sent!=count)return 85;
        if(!body.empty()&&wcscmp(mode,L"eof-body")!=0&&(!::WriteFile(output,body.data(),
            static_cast<DWORD>(body.size()),&sent,nullptr)||sent!=body.size()))return 86;
    }
    if(closeEarly){
        wchar_t readyName[160]{},exitName[160]{};
        if(!::GetEnvironmentVariableW(L"FLY_G01_EOF_READY",readyName,160)||
           !::GetEnvironmentVariableW(L"FLY_G01_EXIT_EVENT",exitName,160))return 87;
        HANDLE ready=::OpenEventW(EVENT_MODIFY_STATE,FALSE,readyName);
        HANDLE finish=::OpenEventW(SYNCHRONIZE,FALSE,exitName);
        if(!ready||!finish||!::CloseHandle(output)||!::SetEvent(ready))return 88;
        ::CloseHandle(ready);
        if(::WaitForSingleObject(finish,3000)!=WAIT_OBJECT_0)return 89;
        ::CloseHandle(finish);
        return (wcscmp(mode,L"eof-empty-7")==0||wcscmp(mode,L"eof-header")==0)?7:0;
    }
    return wcscmp(mode,L"nonzero")==0?7:0;
}
int wmain(int argc,wchar_t** argv){
    if(argc==1)return helper();
    if(argc!=2||wcscmp(argv[1],L"--run-tests"))return 2;
    wchar_t executable[32768]{};
    if(!::GetModuleFileNameW(nullptr,executable,32768))return 3;
    struct Case {wchar_t const* mode;HRESULT expected;};
    Case cases[]={{L"success",S_OK},{L"error-reply",E_ACCESSDENIED},
        {L"large",S_OK},{L"empty",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"truncated",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"malformed",HRESULT_FROM_WIN32(ERROR_INVALID_DATA)},
        {L"nonzero",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-empty-7",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-empty-0",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-header",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-body",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-hang",HRESULT_FROM_WIN32(ERROR_BROKEN_PIPE)},
        {L"eof-cancel",E_FAIL}};
    int failed=0,index=0;
    for(auto const& test:cases){
        wchar_t eventName[160]{};
        swprintf_s(eventName,L"Local\\FlyG01Reply-%lu-%d",::GetCurrentProcessId(),index++);
        releaseReply=::CreateEventW(nullptr,TRUE,FALSE,eventName);
        if(!releaseReply||::GetLastError()==ERROR_ALREADY_EXISTS)return 4;
        wchar_t readyName[160]{},exitName[160]{};
        swprintf_s(readyName,L"Local\\FlyG01Ready-%lu-%d",::GetCurrentProcessId(),index);
        swprintf_s(exitName,L"Local\\FlyG01Exit-%lu-%d",::GetCurrentProcessId(),index);
        eofReady=::CreateEventW(nullptr,TRUE,FALSE,readyName);
        if(!eofReady||::GetLastError()==ERROR_ALREADY_EXISTS)return 5;
        releaseExit=::CreateEventW(nullptr,TRUE,FALSE,exitName);
        if(!releaseExit||::GetLastError()==ERROR_ALREADY_EXISTS)return 6;
        if(!::SetEnvironmentVariableW(L"FLY_G01_REPLY_EVENT",eventName)||
           !::SetEnvironmentVariableW(L"FLY_G01_REPLY_MODE",test.mode)||
           !::SetEnvironmentVariableW(L"FLY_G01_EOF_READY",readyName)||
           !::SetEnvironmentVariableW(L"FLY_G01_EXIT_EVENT",exitName))return 7;
        auto lane=std::make_shared<TestLane>();
        fxfile::shellnav::Work work;work.route=1;work.request=1;work.path=L"C:\\owned";
        scheduleRace=true;raceObserved=false;
        eofMode=wcsncmp(test.mode,L"eof-",4)==0;
        eofObserved=false;eofPolls=0;eofTick=0;testWake=lane->wake;
        const bool hanging=wcscmp(test.mode,L"eof-hang")==0;
        cancelOnPoll=wcscmp(test.mode,L"eof-cancel")==0;
        releaseOnPoll=eofMode&&!hanging&&!cancelOnPoll;
        cancelLane=[lane]{std::lock_guard<std::mutex> lock(lane->mutex);++lane->generation;};
        auto result=fxfile::shellnav::oneAttempt(lane,work,executable,false,0,kMaxPageEntries);
        const auto elapsed=eofObserved?::GetTickCount64()-eofTick:0;
        bool ok=raceObserved&&!result.timeout&&result.canceled==cancelOnPoll&&
            result.hr==test.expected;
        if(SUCCEEDED(test.expected))ok=ok&&result.snapshot.folder.valid()&&
            result.snapshot.children.size()==(wcscmp(test.mode,L"large")==0?300u:0u);
        const DWORD expectedExit=(wcscmp(test.mode,L"nonzero")==0||
            wcscmp(test.mode,L"eof-empty-7")==0||wcscmp(test.mode,L"eof-header")==0)?7:0;
        // Allow one clock-resolution/scheduling poll beyond the nominal five.
        // The local deterministic test separately asserts the exact 100ms deadline.
        if(eofMode)ok=ok&&eofObserved&&eofPolls<=6&&elapsed<2000&&
            result.helperExitKnown==releaseOnPoll&&
            (!releaseOnPoll||result.helperExitCode==expectedExit);
        else ok=ok&&result.helperExitKnown&&result.helperExitCode==expectedExit;
        std::printf("G01_PIPE_%s case=%ls hr=%08lX race=%d exit_known=%d exit=%lu eof=%d polls=%u elapsed=%llu canceled=%d\n",
            ok?"PASS":"FAIL",test.mode,static_cast<unsigned long>(result.hr),
            raceObserved,result.helperExitKnown,result.helperExitCode,eofObserved,
            eofPolls,static_cast<unsigned long long>(elapsed),result.canceled);
        if(!ok)++failed;
        cancelLane={};testWake=nullptr;ownedProcess=nullptr;
        ::CloseHandle(releaseReply);releaseReply=nullptr;
        ::CloseHandle(eofReady);eofReady=nullptr;
        ::CloseHandle(releaseExit);releaseExit=nullptr;
    }
    ::SetEnvironmentVariableW(L"FLY_G01_REPLY_EVENT",nullptr);
    ::SetEnvironmentVariableW(L"FLY_G01_REPLY_MODE",nullptr);
    ::SetEnvironmentVariableW(L"FLY_G01_EOF_READY",nullptr);
    ::SetEnvironmentVariableW(L"FLY_G01_EXIT_EVENT",nullptr);
    std::printf("G01_PIPE_TOTAL=13 FAILED=%d\n",failed);
    return failed?1:0;
}
