// F03 native, test-owned anonymous-pipe protocol proof. This test invokes
// the one-shot worker entry in a thread, NOT a separately supervised process.
// Production supervisor/job termination acceptance remains a distinct gate.
#include "../../src/base/file_preview_worker.h"
#include "../../src/base/file_preview_worker_wire.h"
#include <Windows.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

namespace {
using namespace fxfile;
bool writeAll(HANDLE h,void const* data,std::size_t n){
    auto ptr=static_cast<unsigned char const*>(data);
    while(n){
        DWORD count=0;
        if(!::WriteFile(h,ptr,static_cast<DWORD>(n),&count,nullptr)||!count)
            return false;
        n-=count;ptr+=count;
    }
    return true;
}
bool readAll(HANDLE h,void* data,std::size_t n){
    auto ptr=static_cast<unsigned char*>(data);
    while(n){
        DWORD count=0;
        if(!::ReadFile(h,ptr,static_cast<DWORD>(n),&count,nullptr)||!count)
            return false;
        n-=count;ptr+=count;
    }
    return true;
}
struct ReplyData{
    previewwire::Reply header{};
    std::vector<unsigned char> body;
    int exit=999;
    bool complete=false;
};
ReplyData query(std::wstring path,std::uint32_t kind,std::uint64_t expected,
                bool corruptChecksum=false) {
    ReplyData value;
    HANDLE inRead=nullptr,inWrite=nullptr,outRead=nullptr,outWrite=nullptr;
    if(!::CreatePipe(&inRead,&inWrite,nullptr,0) ||
       !::CreatePipe(&outRead,&outWrite,nullptr,0)){
        if(inRead)::CloseHandle(inRead);
        if(inWrite)::CloseHandle(inWrite);
        if(outRead)::CloseHandle(outRead);
        if(outWrite)::CloseHandle(outWrite);
        return value;
    }
    std::thread worker([&]{
        value.exit=previewworker::runOne(inRead,outWrite);
        ::CloseHandle(inRead);
        ::CloseHandle(outWrite);
    });
    previewwire::Request req{};
    req.kind=kind;
    req.pathUnits=static_cast<std::uint32_t>(path.size());
    req.knownBytes=expected;
    req.pathChecksum=previewwire::checksum(path.data(),
                                          path.size()*sizeof(wchar_t));
    if(corruptChecksum)req.pathChecksum^=0xffffffffu;
    const bool sent=writeAll(inWrite,&req,sizeof(req)) &&
        writeAll(inWrite,path.data(),path.size()*sizeof(wchar_t));
    ::CloseHandle(inWrite);
    if(sent&&readAll(outRead,&value.header,sizeof(value.header)) &&
       previewwire::validReply(value.header)) {
        value.body.resize(value.header.byteCount);
        value.complete=value.body.empty() ||
            readAll(outRead,value.body.data(),value.body.size());
        if(value.complete &&
           value.header.checksum!=
               previewwire::checksum(value.body.data(),value.body.size()))
            value.complete=false;
    }
    ::CloseHandle(outRead);
    worker.join();
    return value;
}
} // namespace

bool runPreviewWorkerWireFixture(std::wstring const& path,
                                 std::vector<std::uint8_t> const& bytes) {
    auto good=query(path,static_cast<std::uint32_t>(previewpolicy::Kind::Text),
                    bytes.size());
    if(!good.complete||good.exit!=0||good.header.status!=0||
       good.header.kind!=1||good.body!=bytes)return false;

    auto badChecksum=query(path,1,bytes.size(),true);
    if(!badChecksum.complete||badChecksum.exit!=0||
       badChecksum.header.status!=1||!badChecksum.body.empty())return false;

    auto badKind=query(path,2,bytes.size());
    if(!badKind.complete||badKind.exit!=0||
       badKind.header.status!=1||!badKind.body.empty())return false;

    auto badSize=query(path,1,previewpolicy::kMaxTextBytes+1);
    if(!badSize.complete||badSize.exit!=0||
       badSize.header.status!=1||!badSize.body.empty())return false;

    std::wstring missing=path+L".missing";
    auto absent=query(missing,1,bytes.size());
    if(!absent.complete||absent.exit!=0||
       absent.header.status!=2||!absent.body.empty())return false;

    auto unc=query(L"\\\\server\\share\\payload.txt",1,3);
    if(!unc.complete||unc.exit!=0||
       unc.header.status!=1||!unc.body.empty())return false;
    std::printf("F03_NATIVE_WORKER_WIRE_BOUNDS=PASS\n");
    return true;
}
