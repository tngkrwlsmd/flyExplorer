// M1.6 experimental read-only Shell fault boundary (NOT a restricted-token sandbox).
#include "../../../src/base/shell_navigation_core.h"
#include <windows.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <new>
#pragma comment(lib,"shell32.lib")
#pragma comment(lib,"shlwapi.lib")
#pragma comment(lib,"ole32.lib")

namespace {
constexpr std::uint32_t kMagic=0x314c5346; // FSL1 little endian
constexpr std::uint32_t kVersion=1;
constexpr std::uint32_t kMaxUnits=16384,kMaxItemUnits=4096;
constexpr std::uint32_t kMaxPidl=65536,kMaxBody=4u*1024u*1024u;
#pragma pack(push,1)
struct Request {std::uint32_t magic,version,pathUnits;};
struct Reply {std::uint32_t magic,version;std::int32_t hr;
              std::uint32_t count,bodyBytes,checksum,flags;};
#pragma pack(pop)
static_assert(sizeof(Request)==12,"request protocol");
static_assert(sizeof(Reply)==28,"reply protocol");

bool exactRead(HANDLE h,void* out,std::uint32_t n) {
    auto* p=static_cast<unsigned char*>(out);
    while(n) {
        DWORD got=0;
        if(!::ReadFile(h,p,n,&got,nullptr)||!got)return false;
        p+=got;n-=got;
    }
    return true;
}
bool exactWrite(HANDLE h,const void* value,size_t n) {
    auto* p=static_cast<const unsigned char*>(value);
    while(n) {
        DWORD sent=0,chunk=static_cast<DWORD>(n<65536?n:65536);
        if(!::WriteFile(h,p,chunk,&sent,nullptr)||!sent)return false;
        p+=sent;n-=sent;
    }
    return true;
}
struct Buffer final {
    bool valid=true;
    std::vector<unsigned char> bytes;
    void append(const void* input,size_t len) {
        if(!valid||len>kMaxBody||bytes.size()>kMaxBody-len){
            valid=false;return;
        }
        const auto* ptr=static_cast<const unsigned char*>(input);
        bytes.insert(bytes.end(),ptr,ptr+len);
    }
    void u32(std::uint32_t n){append(&n,sizeof(n));}
    void name(const std::wstring& s) {
        if(s.size()>kMaxItemUnits){valid=false;return;}
        u32(static_cast<std::uint32_t>(s.size()));
        if(!s.empty())append(s.data(),s.size()*sizeof(wchar_t));
    }
    void pidl(PCIDLIST_ABSOLUTE id) {
        if(!id){valid=false;return;}
        const auto n=::ILGetSize(id);
        if(n<sizeof(USHORT)||n>kMaxPidl){valid=false;return;}
        u32(n);
        append(id,n);
    }
};
std::uint32_t checksum(const std::vector<unsigned char>& payload) {
    std::uint32_t hash=2166136261u;
    for(const auto b:payload)hash=(hash^b)*16777619u;
    return hash;
}
bool answer(HANDLE pipe,HRESULT hr,const fxfile::shellnav::Snapshot* snap=nullptr) {
    Buffer body;
    std::uint32_t n=0,flags=0;
    if(SUCCEEDED(hr)&&snap) {
        body.name(snap->displayName);
        body.name(snap->parsingName);
        body.pidl(snap->folder.get());
        for(const auto& item:snap->children){
            body.u32(static_cast<std::uint32_t>(item.attributes));
            body.name(item.label);
            body.name(item.parsingName);
            body.pidl(item.id.get());
            ++n;
        }
        if(snap->truncated)flags=1;
        if(!body.valid){
            hr=HRESULT_FROM_WIN32(ERROR_MORE_DATA);
            body.bytes.clear();
            n=flags=0;
        }
    }
    Reply result{kMagic,kVersion,static_cast<std::int32_t>(hr),
                 n,static_cast<std::uint32_t>(body.bytes.size()),
                 checksum(body.bytes),flags};
    return exactWrite(pipe,&result,sizeof(result))&&
           (body.bytes.empty()||exactWrite(pipe,body.bytes.data(),body.bytes.size()));
}
}

int wmain(int argc,wchar_t** argv) {
    // Only a test-owned launcher that sets this exact opt-in can delay a child.
    if(argc==2&&!wcscmp(argv[1],L"--test-block")){
        wchar_t flag[16]{};
        const auto len=::GetEnvironmentVariableW(
            L"FLY_M16_OWNED_TEST_ONLY",flag,16);
        if(len!=3||wcscmp(flag,L"YES"))return 16;
        ::Sleep(30000);return 42;
    }
    if(argc!=1)return 2;
    const auto input=::GetStdHandle(STD_INPUT_HANDLE);
    const auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
    if(!input||input==INVALID_HANDLE_VALUE||
       !output||output==INVALID_HANDLE_VALUE)return 3;
    Request req{};
    if(!exactRead(input,&req,sizeof(req))||
       req.magic!=kMagic||req.version!=kVersion||
       !req.pathUnits||req.pathUnits>kMaxUnits)return 4;
    std::wstring path(req.pathUnits,L'\0');
    if(!exactRead(input,&path[0],req.pathUnits*sizeof(wchar_t))||
       path.find(L'\0')!=std::wstring::npos)return 5;
    const auto apt=::CoInitializeEx(nullptr,
        COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
    if(FAILED(apt)){answer(output,apt);return 6;}
    bool sent=false;
    try {
        PIDLIST_ABSOLUTE raw=nullptr;
        auto hr=::SHParseDisplayName(path.c_str(),nullptr,&raw,0,nullptr);
        fxfile::shellnav::Location requested;
        requested.reset(raw);
        fxfile::shellnav::Snapshot snap;
        if(SUCCEEDED(hr))
            hr=fxfile::shellnav::enumerate(
                requested.get(),snap,SHCONTF_FOLDERS|SHCONTF_NONFOLDERS,1200);
        sent=answer(output,hr,SUCCEEDED(hr)?&snap:nullptr);
        // Shell COM pointers stay inside this COM apartment and process.
    }catch(const std::bad_alloc&){sent=answer(output,E_OUTOFMEMORY);}
     catch(...){sent=answer(output,E_FAIL);}
    ::CoUninitialize();
    return sent?0:7;
}
