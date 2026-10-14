// F03 test-owned, actual MSVC/Win32 CreateProcess supervisor acceptance.
// Call with exactly one private temporary test folder and two known executables.
#include "../../src/base/file_preview_supervisor.h"
#include "../../src/base/file_preview_request_gate.h"
#include <Windows.h>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <string>
#include <thread>
#include <vector>

using fxfile::previewsupervisor::Status;
namespace {
bool fail(char const* stage) {
    std::fprintf(stderr,"F03_SUPERVISOR_FAILED_STAGE=%s\n",stage);
    return false;
}
bool writeOwned(std::wstring const& path) {
    const char message[]="flyExplorer preview child IPC owned fixture\n";
    const HANDLE raw=::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,
                                  CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(raw==INVALID_HANDLE_VALUE)return false;
    DWORD sent=0;
    const bool ok=::WriteFile(raw,message,sizeof(message)-1,&sent,nullptr)&&
        sent==sizeof(message)-1;
    ::CloseHandle(raw);
    return ok;
}
bool run(std::wstring const& helper,std::wstring const& stub,
         std::wstring const& directory) {
    const auto source=directory+L"\\preview-owned-한글.txt";
    if(!writeOwned(source))return fail("owned-input");
    const auto attrs=::GetFileAttributesW(source.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES)return fail("owned-attributes");
    LARGE_INTEGER size{};
    {
        HANDLE h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
            nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(h==INVALID_HANDLE_VALUE)return fail("owned-open");
        const bool sized=::GetFileSizeEx(h,&size)!=FALSE;
        ::CloseHandle(h);
        if(!sized)return fail("owned-size");
    }
    fxfile::previewpolicy::Candidate candidate{source,
        static_cast<std::uint64_t>(size.QuadPart),
        true,true,true,false,true};
    std::atomic_bool cancel{false};
    const auto good=fxfile::previewsupervisor::run(helper,candidate,cancel);
    constexpr char expected[]="flyExplorer preview child IPC owned fixture\n";
    if(!good.ok()||good.kind!=fxfile::previewpolicy::Kind::Text||
       good.bytes!=std::vector<std::uint8_t>(
           reinterpret_cast<std::uint8_t const*>(expected),
           reinterpret_cast<std::uint8_t const*>(expected)+sizeof(expected)-1))
        return fail("real-child-bytes");
    std::printf("F03_SUPERVISOR_REAL_CHILD_WIRE=PASS\n");

    std::wstring missing=directory+L"\\missing-f03.txt";
    candidate.absolutePath=missing;
    auto absent=fxfile::previewsupervisor::run(helper,candidate,cancel);
    if(absent.status!=Status::WorkerRejected||absent.workerStatus!=2||
       !absent.bytes.empty())return fail("missing-file");
    candidate.absolutePath=source;
    candidate.knownBytes=fxfile::previewpolicy::kMaxTextBytes+1;
    auto invalid=fxfile::previewsupervisor::run(helper,candidate,cancel);
    if(invalid.status!=Status::Rejected)return fail("oversized");
    candidate.knownBytes=static_cast<std::uint64_t>(size.QuadPart);
    cancel.store(true);
    auto stopped=fxfile::previewsupervisor::run(helper,candidate,cancel);
    if(stopped.status!=Status::Cancelled)return fail("pre-cancel");
    cancel.store(false);
    std::printf("F03_SUPERVISOR_NEGATIVES=PASS\n");

    if(!::SetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",L"corrupt"))
        return fail("test-env");
    auto corrupt=fxfile::previewsupervisor::run(stub,candidate,cancel);
    if(corrupt.status!=Status::ProtocolError||!corrupt.bytes.empty())
        return fail("corrupt-reply");
    if(!::SetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",L"hang"))
        return fail("hang-env");
    const auto started=std::chrono::steady_clock::now();
    auto deadline=fxfile::previewsupervisor::run(stub,candidate,cancel,200);
    const auto duration=std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now()-started);
    ::SetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",nullptr);
    if(deadline.status!=Status::Deadline||duration.count()>1600)
        return fail("owned-hung-child");
    // Cancel after the child is running, with a bounded owned-only kill.
    if(!::SetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",L"hang"))
        return fail("cancel-env");
    std::atomic_bool midCancel{false};
    std::thread cancelRequest([&] {
        ::Sleep(120);
        midCancel.store(true);
    });
    const auto cancelStart=std::chrono::steady_clock::now();
    auto canceled=fxfile::previewsupervisor::run(
        stub,candidate,midCancel,3000);
    cancelRequest.join();
    const auto cancelMs=std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now()-cancelStart);
    ::SetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",nullptr);
    if(canceled.status!=Status::Cancelled||cancelMs.count()>1500)
        return fail("owned-midflight-cancel");
    std::printf("F03_SUPERVISOR_ACTIVE_CANCEL_JOB_REAP=PASS\n");

    std::printf("F03_SUPERVISOR_JOB_TIMEOUT_AND_CORRUPT_WIRE=PASS\n");

    using namespace fxfile::previewgate;
    Gate gate;
    auto first=gate.begin({1,1,6,100,L"selection-one"});
    if(!gate.current(first))return fail("gate-first");
    auto next=gate.begin({1,1,6,101,L"selection-two"});
    if(gate.current(first)||!first.cancel->load()||!gate.current(next))
        return fail("gate-replaced");
    auto changedTab=gate.begin({1,2,7,102,L"selection-two"});
    if(gate.current(next)||!next.cancel->load()||!gate.current(changedTab))
        return fail("gate-changed-tab");
    gate.clear();
    if(gate.current(changedTab)||!changedTab.cancel->load())
        return fail("gate-cleared");
    std::printf("F03_SUPERVISOR_STALE_ROUTE_CANCEL_GATE=PASS\n");

    if(!std::filesystem::remove(source))return fail("owned-cleanup");
    std::printf("F03_SUPERVISOR_ALL_OWNED_ACCEPTANCE=PASS\n");
    return true;
}
}
int wmain(int argc,wchar_t** argv) {
    if(argc!=4)return 2;
    return run(argv[1],argv[2],argv[3])?0:1;
}
