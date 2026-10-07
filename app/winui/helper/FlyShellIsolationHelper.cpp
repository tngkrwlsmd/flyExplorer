// M1.7 read-only Shell namespace helper. One request per exact owned process.
// Fault boundary ONLY: inherits user token; not a security sandbox.
#include "../../../src/base/shell_navigation_core.h"
#include "../../../src/base/shell_isolation_wire.h"
#include "../../../src/base/shell_transfer_core.h"
#include <windows.h>
#include <shellapi.h>
#include <shlobj.h>
#include <shlwapi.h>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <new>
#include <wincrypt.h>
#include <shobjidl.h>
#include <wrl/client.h>
#include <filesystem>
#include <cwctype>
#include <cstdio>
#include <algorithm>
#include <cstdlib>
#include <string>
#pragma comment(lib,"gdi32.lib")
#pragma comment(lib,"crypt32.lib")
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

namespace {
IContextMenu2* currentMenuTwo=nullptr;
IContextMenu3* currentMenuThree=nullptr;
WNDPROC originalMenuProc=nullptr;
LRESULT CALLBACK menuWindowProc(HWND h,UINT msg,WPARAM w,LPARAM l){
 if(msg==WM_INITMENUPOPUP||msg==WM_DRAWITEM||
    msg==WM_MEASUREITEM||msg==WM_MENUCHAR){
  LRESULT result=0;
  if(currentMenuThree&&SUCCEEDED(
      currentMenuThree->HandleMenuMsg2(msg,w,l,&result)))
      return result;
  if(currentMenuTwo&&msg!=WM_MENUCHAR&&
     SUCCEEDED(currentMenuTwo->HandleMenuMsg(msg,w,l)))
     return 0;
 }
 return originalMenuProc?::CallWindowProcW(originalMenuProc,h,msg,w,l):
                         ::DefWindowProcW(h,msg,w,l);
}
int inspectOrShowContext(bool inspect){
 // Child reads one bounded UTF-16 path, optional x,y from an anonymous pipe.
 HANDLE input=::GetStdHandle(STD_INPUT_HANDLE);
 HANDLE output=::GetStdHandle(STD_OUTPUT_HANDLE);
 if(!input||input==INVALID_HANDLE_VALUE)return 51;
 std::uint32_t count=0;
 if(!exactRead(input,&count,sizeof(count))||count<4||count>1024)return 52;
 std::wstring source(count,L'\0');
 if(!exactRead(input,source.data(),count*sizeof(wchar_t))||
    source.find(L'\0')!=std::wstring::npos)return 53;
 int x=0,y=0;
 if(!inspect && (!exactRead(input,&x,4)||!exactRead(input,&y,4)))
   return 54;
 std::filesystem::path path(source);
 if(!path.is_absolute()||path.lexically_normal().native()!=source)
   return 55;
 auto root=path.root_path().native();
 if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return 56;
 std::filesystem::path part=path.root_path();
 for(auto it=path.begin();it!=path.end();++it){
  if(*it==path.root_name()||*it==path.root_directory())continue;
  part/=*it;
  auto attr=::GetFileAttributesW(part.c_str());
  if(attr==INVALID_FILE_ATTRIBUTES||
     (attr&FILE_ATTRIBUTE_REPARSE_POINT))return 57;
 }
 const auto apt=::CoInitializeEx(
     nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(apt))return 58;
 int rc=59;
 PIDLIST_ABSOLUTE absolute=nullptr;
 HWND owner=nullptr;
 HMENU popup=nullptr;
 Microsoft::WRL::ComPtr<IContextMenu> menu;
 Microsoft::WRL::ComPtr<IContextMenu2> two;
 Microsoft::WRL::ComPtr<IContextMenu3> three;
 try {
  auto hr=::SHParseDisplayName(source.c_str(),nullptr,&absolute,0,nullptr);
  if(SUCCEEDED(hr)&&absolute){
   Microsoft::WRL::ComPtr<IShellFolder> folder;
   PCUITEMID_CHILD child=nullptr;
   hr=::SHBindToParent(absolute,IID_PPV_ARGS(&folder),&child);
   if(SUCCEEDED(hr)&&folder&&child){
    owner=::CreateWindowExW(WS_EX_TOOLWINDOW,L"STATIC",
             L"flyExplorer Shell menu (test-owned child)",WS_POPUP,
             x,y,1,1,nullptr,nullptr,::GetModuleHandleW(nullptr),nullptr);
    if(owner){
     PCUITEMID_CHILD children[]={child};
     hr=folder->GetUIObjectOf(owner,1,children,IID_IContextMenu,
                             nullptr,reinterpret_cast<void**>(
                                 menu.GetAddressOf()));
     if(SUCCEEDED(hr)&&menu){
      popup=::CreatePopupMenu();
      if(popup){
       const HRESULT added=menu->QueryContextMenu(
           popup,0,1,0x7fff,CMF_NORMAL);
       if(SUCCEEDED(added)){
        const int n=::GetMenuItemCount(popup);
        if(n>0&&n<=200){
         if(inspect){
          if(output&&output!=INVALID_HANDLE_VALUE){
           const auto line="OWNED_CONTEXT_ITEMS="+std::to_string(n)+"\n";
           exactWrite(output,line.data(),line.size());
          }
          rc=0;
         }else{
          menu.As(&three);
          menu.As(&two);
          currentMenuThree=three.Get();
          currentMenuTwo=two.Get();
          ::SetLastError(0);
          auto original=::SetWindowLongPtrW(owner,GWLP_WNDPROC,
                             reinterpret_cast<LONG_PTR>(&menuWindowProc));
          if(original){
           originalMenuProc=reinterpret_cast<WNDPROC>(original);
           ::ShowWindow(owner,SW_SHOWNA);
           ::SetForegroundWindow(owner);
           const UINT chosen=::TrackPopupMenuEx(popup,
              TPM_RETURNCMD|TPM_RIGHTBUTTON|TPM_NONOTIFY,x,y,owner,nullptr);
           ::PostMessageW(owner,WM_NULL,0,0);
           rc=0; // Escape / clicking away is a valid cancel.
           if(chosen>=1&&chosen<=0x7fff){
            // Built-in file mutation must use flyExplorer's native
            // guarded transfer/rename routes, not an opaque Shell verb.
            char name[128]{};
            const auto canonical=menu->GetCommandString(
                chosen-1,GCS_VERBA,nullptr,name,sizeof(name));
            // Fail closed if a provider supplies no stable canonical
            // verb; never execute an unclassified built-in mutation
            // outside our existing native Shell file-operation pipeline.
            if(FAILED(canonical)||!name[0])rc=65;
            else{
             std::string verb(name);
             std::transform(verb.begin(),verb.end(),verb.begin(),[](char c){
              return (c>='A'&&c<='Z')?char(c-'A'+'a'):c;
             });
             if(verb=="delete"||verb=="rename"||verb=="copy"||
                verb=="cut"||verb=="paste"||verb=="move")rc=65;
            }
            if(rc==0){
             CMINVOKECOMMANDINFOEX args{};
             args.cbSize=sizeof(args);
             args.fMask=CMIC_MASK_UNICODE|CMIC_MASK_PTINVOKE;
             args.hwnd=owner;
             args.lpVerb=MAKEINTRESOURCEA(chosen-1);
             args.lpVerbW=MAKEINTRESOURCEW(chosen-1);
             args.nShow=SW_SHOWNORMAL;
             args.ptInvoke={x,y};
             if(FAILED(menu->InvokeCommand(
                 reinterpret_cast<CMINVOKECOMMANDINFO*>(&args))))
                 rc=66;
            }
           }
           ::SetWindowLongPtrW(owner,GWLP_WNDPROC,original);
           originalMenuProc=nullptr;
           currentMenuThree=nullptr;
           currentMenuTwo=nullptr;
          }else rc=67;
         }
        }
       }
      }
     }
    }
   }
  }
 }catch(...){rc=68;}
 if(popup)::DestroyMenu(popup);
 if(owner)::DestroyWindow(owner);
 if(absolute)::CoTaskMemFree(absolute);
 ::CoUninitialize();
 return rc;
}
} // namespace
int wmain(int argc,wchar_t** argv) {
    if(argc==2&&!wcscmp(argv[1],L"--file-transfer"))
        return fxfile::shelltransfer::runIsolatedHelper(
            ::GetStdHandle(STD_INPUT_HANDLE),::GetStdHandle(STD_OUTPUT_HANDLE));
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
    if(argc==2&&!wcscmp(argv[1],L"--context-inspect"))
        return inspectOrShowContext(true);
    if(argc==2&&!wcscmp(argv[1],L"--context-menu"))
        return inspectOrShowContext(false);
    if(argc==2&&!wcscmp(argv[1],L"--file-thumbnail")){
        // Exact 1-shot thumbnail in a disposable Shell process. No file
        // path is passed on the command line, no mutation of input files,
        // no COM/third-party thumbnail provider on the WinUI STA.
        HANDLE input=::GetStdHandle(STD_INPUT_HANDLE);
        HANDLE output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!input||input==INVALID_HANDLE_VALUE||
           !output||output==INVALID_HANDLE_VALUE)return 31;
        std::uint32_t units=0;
        if(!exactRead(input,&units,sizeof(units))||units<4||units>1024)
            return 32;
        std::wstring source(units,L'\0');
        if(!exactRead(input,source.data(),units*sizeof(wchar_t))||
           source.find(L'\0')!=std::wstring::npos)return 33;
        std::uint32_t requestedPixels=0;
        if(!exactRead(input,&requestedPixels,sizeof(requestedPixels))||
           requestedPixels<16||requestedPixels>128)return 33;
        std::filesystem::path path(source);
        if(!path.is_absolute()||path.lexically_normal().native()!=source)
            return 34;
        auto root=path.root_path().native();
        if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
           ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return 35;
        auto ext=path.extension().native();
        for(auto& c:ext)c=static_cast<wchar_t>(::towlower(c));
        if(ext!=L".png"&&ext!=L".jpg"&&ext!=L".jpeg"&&
           ext!=L".bmp"&&ext!=L".webp")return 36;
        std::filesystem::path part=path.root_path();
        for(auto it=path.begin();it!=path.end();++it){
            if(*it==path.root_name()||*it==path.root_directory())continue;
            part/=*it;
            const auto flags=::GetFileAttributesW(part.c_str());
            if(flags==INVALID_FILE_ATTRIBUTES||
               (flags&FILE_ATTRIBUTE_REPARSE_POINT))return 37;
        }
        WIN32_FILE_ATTRIBUTE_DATA attrs{};
        if(!::GetFileAttributesExW(path.c_str(),GetFileExInfoStandard,&attrs)||
           (attrs.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)||
           attrs.nFileSizeHigh||attrs.nFileSizeLow>32*1024*1024)
           return 38;
        const auto apt=::CoInitializeEx(
            nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
        if(FAILED(apt))return 39;
        int resultCode=40;
        try{
            Microsoft::WRL::ComPtr<IShellItem> item;
            if(SUCCEEDED(::SHCreateItemFromParsingName(
                source.c_str(),nullptr,IID_PPV_ARGS(&item)))){
                Microsoft::WRL::ComPtr<IShellItemImageFactory> factory;
                if(SUCCEEDED(item.As(&factory))){
                    HBITMAP bitmap=nullptr;
                    SIZE requested{static_cast<LONG>(requestedPixels),
                                   static_cast<LONG>(requestedPixels)};
                    if(SUCCEEDED(factory->GetImage(
                        requested,SIIGBF_THUMBNAILONLY|
                        SIIGBF_BIGGERSIZEOK,&bitmap))&&bitmap){
                        BITMAP bm{};
                        if(::GetObjectW(bitmap,sizeof(bm),&bm)==sizeof(bm)&&
                           bm.bmWidth>0&&bm.bmHeight>0&&
                           bm.bmWidth<=128&&bm.bmHeight<=128){
                            const auto width=static_cast<std::uint32_t>(bm.bmWidth);
                            const auto height=static_cast<std::uint32_t>(bm.bmHeight);
                            BITMAPINFO dib{};
                            dib.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                            dib.bmiHeader.biWidth=bm.bmWidth;
                            dib.bmiHeader.biHeight=-bm.bmHeight;
                            dib.bmiHeader.biPlanes=1;
                            dib.bmiHeader.biBitCount=32;
                            dib.bmiHeader.biCompression=BI_RGB;
                            std::vector<unsigned char> pixels(width*height*4);
                            HDC screen=::GetDC(nullptr);
                            if(screen&&::GetDIBits(screen,bitmap,0,height,
                                pixels.data(),&dib,DIB_RGB_COLORS)==height){
                                bool anyAlpha=false;
                                for(size_t i=3;i<pixels.size();i+=4)
                                   anyAlpha|=pixels[i]!=0;
                                if(!anyAlpha)
                                   for(size_t i=3;i<pixels.size();i+=4)
                                      pixels[i]=255;
                                const char magic[4]={'T','H','M','B'};
                                if(exactWrite(output,magic,4)&&
                                   exactWrite(output,&width,4)&&
                                   exactWrite(output,&height,4)&&
                                   exactWrite(output,pixels.data(),pixels.size()))
                                    resultCode=0;
                            }
                            if(screen)::ReleaseDC(nullptr,screen);
                        }
                        ::DeleteObject(bitmap);
                    }
                }
            }
        }catch(...){resultCode=41;}
        ::CoUninitialize();
        return resultCode;
    }
    if(argc>=4&&!wcscmp(argv[1],L"--known-folder-visuals")){
        wchar_t* end=nullptr;
        const auto parsed=::wcstoul(argv[2],&end,10);
        if(!end||*end||parsed<16||parsed>64||argc>9)return 18;
        const auto visualPixels=static_cast<std::uint32_t>(parsed);
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!output||output==INVALID_HANDLE_VALUE)return 19;
        const auto apt=::CoInitializeEx(
            nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
        if(FAILED(apt))return 24;
        int resultCode=0;
        for(int i=3;i<argc&&resultCode==0;++i){
            std::wstring key(argv[i]);
            KNOWNFOLDERID const* id=nullptr;
            if(key==L"desktop")id=&FOLDERID_Desktop;
            else if(key==L"documents")id=&FOLDERID_Documents;
            else if(key==L"downloads")id=&FOLDERID_Downloads;
            else if(key==L"pictures")id=&FOLDERID_Pictures;
            else if(key==L"music")id=&FOLDERID_Music;
            else if(key==L"videos")id=&FOLDERID_Videos;
            else {resultCode=20;break;}

            PWSTR path=nullptr;
            const auto pathHr=::SHGetKnownFolderPath(
                *id,KF_FLAG_DEFAULT,nullptr,&path);
            SHFILEINFOW info{};
            const auto typeResult=SUCCEEDED(pathHr)&&path?
                ::SHGetFileInfoW(path,0,&info,sizeof(info),SHGFI_TYPENAME):0;
            std::wstring readable=typeResult?info.szTypeName:L"";
            if(readable.size()>79)readable.clear();
            const int count=readable.empty()?0: ::WideCharToMultiByte(
                CP_UTF8,WC_ERR_INVALID_CHARS,readable.data(),
                static_cast<int>(readable.size()),nullptr,0,nullptr,nullptr);
            if(count<0||count>320){
                if(path)::CoTaskMemFree(path);
                resultCode=22;break;
            }

            std::string line=std::to_string(i-3)+"\t";
            if(count){
                std::string utf8(static_cast<size_t>(count),'\0');
                if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                      readable.data(),static_cast<int>(readable.size()),
                      utf8.data(),count,nullptr,nullptr)!=count){
                    if(path)::CoTaskMemFree(path);
                    resultCode=22;break;
                }
                line+=utf8;
            }
            line+="\t";

            HBITMAP bitmap=nullptr;
            if(SUCCEEDED(pathHr)&&path){
                Microsoft::WRL::ComPtr<IShellItem> item;
                if(SUCCEEDED(::SHCreateItemFromParsingName(
                     path,nullptr,IID_PPV_ARGS(&item)))){
                    Microsoft::WRL::ComPtr<IShellItemImageFactory> factory;
                    if(SUCCEEDED(item.As(&factory))){
                        SIZE requested{static_cast<LONG>(visualPixels),
                                       static_cast<LONG>(visualPixels)};
                        factory->GetImage(
                            requested,SIIGBF_ICONONLY,&bitmap);
                    }
                }
            }
            if(path)::CoTaskMemFree(path);

            if(bitmap){
                BITMAP bm{};
                if(::GetObjectW(bitmap,sizeof(bm),&bm)==sizeof(bm)&&
                   bm.bmWidth==static_cast<LONG>(visualPixels)&&
                   bm.bmHeight==static_cast<LONG>(visualPixels)){
                    BITMAPINFO dib{};
                    dib.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                    dib.bmiHeader.biWidth=bm.bmWidth;
                    dib.bmiHeader.biHeight=-bm.bmHeight;
                    dib.bmiHeader.biPlanes=1;
                    dib.bmiHeader.biBitCount=32;
                    dib.bmiHeader.biCompression=BI_RGB;
                    std::vector<unsigned char> pixels(
                        visualPixels*visualPixels*4);
                    HDC screen=::GetDC(nullptr);
                    if(screen&&::GetDIBits(screen,bitmap,0,visualPixels,
                         pixels.data(),&dib,DIB_RGB_COLORS)==visualPixels){
                        bool anyAlpha=false;
                        for(size_t p=3;p<pixels.size();p+=4)
                            anyAlpha|=pixels[p]!=0;
                        if(!anyAlpha)
                            for(size_t p=3;p<pixels.size();p+=4)
                                pixels[p]=255;
                        DWORD required=0;
                        ::CryptBinaryToStringA(pixels.data(),
                            static_cast<DWORD>(pixels.size()),
                            CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                            nullptr,&required);
                        if(required>0&&required<40000){
                            std::string encoded(required,'\0');
                            if(::CryptBinaryToStringA(pixels.data(),
                                static_cast<DWORD>(pixels.size()),
                                CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                                encoded.data(),&required)){
                                encoded.resize(std::strlen(encoded.c_str()));
                                line+=encoded;
                            }
                        }
                    }
                    if(screen)::ReleaseDC(nullptr,screen);
                }
                ::DeleteObject(bitmap);
            }

            line+="\n";
            DWORD sent=0;
            if(!::WriteFile(output,line.data(),
                 static_cast<DWORD>(line.size()),&sent,nullptr)||
               sent!=line.size())resultCode=23;
        }
        ::CoUninitialize();
        return resultCode;
    }
    const bool requestVisuals=argc>=4&&!wcscmp(argv[1],L"--file-visuals");
    if(requestVisuals || (argc>=3&&!wcscmp(argv[1],L"--file-types"))){
        // Strict isolated one-shot type-name request. Only ASCII extensions
        // from the app are accepted; do not parse paths or touch files.
        const int first=requestVisuals?3:2;
        std::uint32_t visualPixels=16;
        if(requestVisuals){
            wchar_t* end=nullptr;
            const auto parsed=::wcstoul(argv[2],&end,10);
            if(!end||*end||parsed<16||parsed>64)return 18;
            visualPixels=static_cast<std::uint32_t>(parsed);
        }
        if(argc>(requestVisuals?27:26))return 18;
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!output||output==INVALID_HANDLE_VALUE)return 19;
        for(int i=first;i<argc;++i){
            std::wstring ext(argv[i]);
            if(ext.size()<2||ext.size()>17||ext[0]!=L'.')return 20;
            for(auto c:ext.substr(1))
                if(!((c>=L'a'&&c<=L'z')||(c>=L'A'&&c<=L'Z')||
                     (c>=L'0'&&c<=L'9')))return 21;
            const bool folder=requestVisuals&&ext==L".flyfolder";
            SHFILEINFOW info{};
            auto result=::SHGetFileInfoW(folder?L"folder":ext.c_str(),
                     folder?FILE_ATTRIBUTE_DIRECTORY:FILE_ATTRIBUTE_NORMAL,
                     &info,sizeof(info),
                     SHGFI_USEFILEATTRIBUTES|SHGFI_TYPENAME|
                     (requestVisuals?(SHGFI_ICON|
                       (visualPixels<=16?SHGFI_SMALLICON:SHGFI_LARGEICON)):0));
            std::wstring readable=result?info.szTypeName:L"";
            if(readable.size()>79)readable.clear();
            const int count=readable.empty()?0: ::WideCharToMultiByte(
                CP_UTF8,WC_ERR_INVALID_CHARS,readable.data(),
                static_cast<int>(readable.size()),nullptr,0,nullptr,nullptr);
            if(count<0||count>320)return 22;
            std::string line=std::to_string(i-first)+"\t";
            if(count){
                std::string utf8(static_cast<size_t>(count),'\0');
                if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                      readable.data(),static_cast<int>(readable.size()),
                      utf8.data(),count,nullptr,nullptr)!=count)return 22;
                line+=utf8;
            }
            if(requestVisuals){
                // Encode a bounded square BGRA visual in the owned worker;
                // UI receives pixels, never an untrusted HICON.
                // Missing icon => empty field and a generic UI fallback.
                line+="\t";
                if(result&&info.hIcon){
                    BITMAPINFO bitmap{};
                    bitmap.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                    bitmap.bmiHeader.biWidth=static_cast<LONG>(visualPixels);
                    bitmap.bmiHeader.biHeight=-static_cast<LONG>(visualPixels);
                    bitmap.bmiHeader.biPlanes=1;
                    bitmap.bmiHeader.biBitCount=32;
                    bitmap.bmiHeader.biCompression=BI_RGB;
                    void* raw=nullptr;
                    HDC screen=::GetDC(nullptr);
                    HDC memory=screen?::CreateCompatibleDC(screen):nullptr;
                    HBITMAP image=memory?::CreateDIBSection(memory,
                        &bitmap,DIB_RGB_COLORS,&raw,nullptr,0):nullptr;
                    if(memory&&image&&raw){
                        auto old=::SelectObject(memory,image);
                        std::memset(raw,0,visualPixels*visualPixels*4);
                        if(::DrawIconEx(memory,0,0,info.hIcon,visualPixels,visualPixels,
                                        0,nullptr,DI_NORMAL)){
                            DWORD required=0;
                            ::CryptBinaryToStringA(static_cast<BYTE*>(raw),
                                visualPixels*visualPixels*4,CRYPT_STRING_BASE64|
                                CRYPT_STRING_NOCRLF,nullptr,&required);
                            if(required>0&&required<40000){
                                std::string encoded(required,'\0');
                                if(::CryptBinaryToStringA(
                                    static_cast<BYTE*>(raw),visualPixels*visualPixels*4,
                                    CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                                    encoded.data(),&required)){
                                    encoded.resize(std::strlen(encoded.c_str()));
                                    line+=encoded;
                                }
                            }
                        }
                        ::SelectObject(memory,old);
                    }
                    if(image)::DeleteObject(image);
                    if(memory)::DeleteDC(memory);
                    if(screen)::ReleaseDC(nullptr,screen);
                    ::DestroyIcon(info.hIcon);
                }
            }
            line+="\n";
            DWORD sent=0;
            if(!::WriteFile(output,line.data(),static_cast<DWORD>(line.size()),
                            &sent,nullptr)||sent!=line.size())return 23;
        }
        return 0;
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
       (req.type!=kPath && req.type!=kAbsolutePidl)||
       !req.limit||req.limit>kMaxPageEntries||
       req.offset>=kMaxBrowseEntries||
       req.limit>kMaxBrowseEntries-req.offset)return 4;
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
            hr=fxfile::shellnav::enumeratePage(
                requested.get(),snap,
                SHCONTF_FOLDERS|SHCONTF_NONFOLDERS,
                req.offset,req.limit);
        sent=answer(output,hr,SUCCEEDED(hr)?&snap:nullptr);
    }catch(std::bad_alloc const&){sent=answer(output,E_OUTOFMEMORY);}
     catch(...){sent=answer(output,E_FAIL);}
    ::CoUninitialize();
    return sent?0:7;
}
