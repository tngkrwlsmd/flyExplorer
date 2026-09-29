// M1.7 read-only Shell namespace helper. One request per exact owned process.
// Fault boundary ONLY: inherits user token; not a security sandbox.
#include "../../../src/base/shell_navigation_core.h"
#include "../../../src/base/shell_isolation_wire.h"
#include <windows.h>
#include <shellapi.h>
#include <shlwapi.h>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <new>
// No registry writes or third-party extension installation: the test object
// has a real IUnknown COM vtable and blocks on its own STA in QueryInterface.
struct OwnedBlockingCom final : IUnknown {
    ULONG refs=1;
    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid,void** out) override {
        if(!out)return E_POINTER;
        *out=nullptr;
        if(iid!=IID_IUnknown)return E_NOINTERFACE;
        ::Sleep(30000);
        *out=this;AddRef();
        return S_OK;
    }
    ULONG STDMETHODCALLTYPE AddRef() override {return ++refs;}
    ULONG STDMETHODCALLTYPE Release() override {return --refs;}
};
#pragma comment(lib,"shell32.lib")
#pragma comment(lib,"shlwapi.lib")
#pragma comment(lib,"ole32.lib")
namespace {
using namespace fxfile::isolation;
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
        if(!valid||len>kMaxBody||bytes.size()>kMaxBody-len) {
            valid=false;return;
        }
        const auto* ptr=static_cast<const unsigned char*>(input);
        bytes.insert(bytes.end(),ptr,ptr+len);
    }
    void u32(std::uint32_t n){append(&n,sizeof(n));}
    void name(std::wstring const& s,size_t maxUnits=kMaxItemUnits) {
        if(s.size()>maxUnits){valid=false;return;}
        u32(static_cast<std::uint32_t>(s.size()));
        if(!s.empty())append(s.data(),s.size()*sizeof(wchar_t));
    }
    void pidl(PCIDLIST_ABSOLUTE id) {
        if(!id){valid=false;return;}
        const auto n=::ILGetSize(id);
        if(!validPidl(id,n)){valid=false;return;}
        u32(n);
        append(id,n);
    }
};
bool answer(HANDLE pipe,HRESULT hr,
            fxfile::shellnav::Snapshot const* snap=nullptr) {
    Buffer body;
    std::uint32_t n=0,flags=0;
    if(SUCCEEDED(hr)&&snap) {
        body.name(snap->displayName);
        body.name(snap->parsingName);
        // SHGetPathFromIDListEx is called ONLY in this disposable child,
        // never on the WinUI STA. Virtual folders legitimately use "".
        wchar_t filesystem[32768]{};
        std::wstring path;
        if(::SHGetPathFromIDListEx(snap->folder.get(),filesystem,
            static_cast<DWORD>(_countof(filesystem)),0))
            path=filesystem;
        if(path.size()>kMaxPathUnits)path.clear();
        body.name(path,kMaxPathUnits);
        body.pidl(snap->folder.get());
        for(auto const& item:snap->children){
            body.u32(static_cast<std::uint32_t>(item.attributes));
            body.name(item.label);
            body.name(item.parsingName);
            body.pidl(item.id.get());
            ++n;
        }
        if(snap->truncated)flags=1;
        if(!body.valid){
            hr=HRESULT_FROM_WIN32(ERROR_MORE_DATA);
            body.bytes.clear();n=flags=0;
        }
    }
    Reply result{kMagic,kVersion,static_cast<std::int32_t>(hr),
                 n,static_cast<std::uint32_t>(body.bytes.size()),
                 checksum(body.bytes.data(),body.bytes.size()),flags};
    return exactWrite(pipe,&result,sizeof(result)) &&
           (body.bytes.empty()||
           exactWrite(pipe,body.bytes.data(),body.bytes.size()));
}
} // namespace

int wmain(int argc,wchar_t** argv) {
    // Only isolated regression launches set this environment & argument.
    if(argc==2&&!wcscmp(argv[1],L"--test-block")){
        wchar_t flag[16]{};
        const auto len=::GetEnvironmentVariableW(
            L"FLY_M16_OWNED_TEST_ONLY",flag,16);
        if(len!=3||wcscmp(flag,L"YES"))return 16;
        ::Sleep(30000);return 42;
    }
    if(argc==2&&!wcscmp(argv[1],L"--test-com-block")){
        wchar_t flag[16]{};
        const auto len=::GetEnvironmentVariableW(
            L"FLY_M18_OWNED_COM_TEST_ONLY",flag,16);
        if(len!=3||wcscmp(flag,L"YES"))return 16;
        const auto hr=::CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
        if(FAILED(hr))return 17;
        OwnedBlockingCom object;
        IUnknown* queried=nullptr;
        object.QueryInterface(IID_IUnknown,
                              reinterpret_cast<void**>(&queried));
        if(queried)queried->Release();
        ::CoUninitialize();
        return 42;
    }
    if(argc!=1)return 2;
    const auto input=::GetStdHandle(STD_INPUT_HANDLE);
    const auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
    if(!input||input==INVALID_HANDLE_VALUE||
       !output||output==INVALID_HANDLE_VALUE)return 3;
    Request req{};
    if(!exactRead(input,&req,sizeof(req))||
       req.magic!=kMagic||req.version!=kVersion)return 4;
    if((req.type==kPath && (!req.length||req.length>kMaxPathUnits)) ||
       (req.type==kAbsolutePidl && (!req.length||req.length>kMaxPidl)) ||
       (req.type!=kPath && req.type!=kAbsolutePidl))return 4;
    std::wstring parsing;
    std::vector<unsigned char> pidlBytes;
    if(req.type==kPath){
        parsing.resize(req.length);
        if(!exactRead(input,&parsing[0],req.length*sizeof(wchar_t))||
           parsing.find(L'\0')!=std::wstring::npos)return 5;
    }else{
        pidlBytes.resize(req.length);
        if(!exactRead(input,pidlBytes.data(),req.length) ||
           !validPidl(pidlBytes.data(),pidlBytes.size()))return 5;
    }

    const auto apt=::CoInitializeEx(nullptr,
        COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
    if(FAILED(apt)){answer(output,apt);return 6;}
    bool sent=false;
    try {
        PIDLIST_ABSOLUTE raw=nullptr;
        HRESULT hr=S_OK;
        if(req.type==kPath)
            hr=::SHParseDisplayName(parsing.c_str(),nullptr,&raw,0,nullptr);
        else{
            raw=static_cast<PIDLIST_ABSOLUTE>(
                ::CoTaskMemAlloc(pidlBytes.size()));
            if(raw)memcpy(raw,pidlBytes.data(),pidlBytes.size());
            else hr=E_OUTOFMEMORY;
        }
        fxfile::shellnav::Location requested;
        requested.reset(raw);
        fxfile::shellnav::Snapshot snap;
        if(SUCCEEDED(hr))
            hr=fxfile::shellnav::enumerate(
                requested.get(),snap,SHCONTF_FOLDERS|SHCONTF_NONFOLDERS,1200);
        sent=answer(output,hr,SUCCEEDED(hr)?&snap:nullptr);
    }catch(std::bad_alloc const&){sent=answer(output,E_OUTOFMEMORY);}
     catch(...){sent=answer(output,E_FAIL);}
    ::CoUninitialize();
    return sent?0:7;
}
