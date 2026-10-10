// Disposable Shell helper. Navigation requests remain read-only; the explicit
// --file-transfer mode performs one bounded Copy/Move request in an exact-owned
// child process. Fault boundary ONLY: inherits user token; not a security sandbox.
#include "../../../src/base/shell_navigation_core.h"
#include "../../../src/base/shell_isolation_wire.h"
#include "../../../src/base/shell_transfer_core.h"
#include "../../../src/base/file_metadata_wire.h"
#include "../../../src/base/shell_visual_wire.h"
#include "../../../src/base/indexed_search_wire.h"
#include <atldbcli.h>
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
 // Keep --context-inspect's established one-path wire unchanged.
 // Menu mode accepts a bounded vector for same-parent multi-selection.
 std::uint32_t count=0;
 if(!exactRead(input,&count,sizeof(count)))return 52;
 std::vector<std::wstring> paths;
 if(inspect){
  if(count<4||count>1024)return 52;
  std::wstring source(count,L'\0');
  if(!exactRead(input,source.data(),count*sizeof(wchar_t))||
     source.find(L'\0')!=std::wstring::npos)return 53;
  paths.push_back(std::move(source));
 }else{
  if(!count||count>32)return 52;
  std::size_t totalUnits=0;
  for(std::uint32_t i=0;i<count;++i){
   std::uint32_t length=0;
   if(!exactRead(input,&length,4)||length<4||length>1024||
      length>16*1024-totalUnits)return 52;
   std::wstring source(length,L'\0');
   if(!exactRead(input,source.data(),length*sizeof(wchar_t))||
      source.find(L'\0')!=std::wstring::npos)return 53;
   totalUnits+=length;
   paths.push_back(std::move(source));
  }
 }
 int x=0,y=0;
 if(!inspect&&(!exactRead(input,&x,4)||!exactRead(input,&y,4)))
   return 54;
 std::wstring commonParent;
 for(std::size_t i=0;i<paths.size();++i){
  auto const& source=paths[i];
  std::filesystem::path path(source);
  if(!path.is_absolute()||path.lexically_normal().native()!=source)
    return 55;
  auto root=path.root_path().native();
  if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
     ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return 56;
  auto const parent=path.parent_path().native();
  if(i&&::CompareStringOrdinal(commonParent.c_str(),-1,
                               parent.c_str(),-1,TRUE)!=CSTR_EQUAL)return 55;
  if(!i)commonParent=parent;
  for(std::size_t j=0;j<i;++j)
   if(::CompareStringOrdinal(paths[j].c_str(),-1,
                             source.c_str(),-1,TRUE)==CSTR_EQUAL)return 55;
  std::filesystem::path part=path.root_path();
  for(auto it=path.begin();it!=path.end();++it){
   if(*it==path.root_name()||*it==path.root_directory())continue;
   part/=*it;
   auto attr=::GetFileAttributesW(part.c_str());
   if(attr==INVALID_FILE_ATTRIBUTES||
      (attr&FILE_ATTRIBUTE_REPARSE_POINT))return 57;
  }
 }
 const auto apt=::CoInitializeEx(
     nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(apt))return 58;
 int rc=59;
 std::vector<PIDLIST_ABSOLUTE> absolutes(paths.size(),nullptr);
 std::vector<PCUITEMID_CHILD> children;
 children.reserve(paths.size());
 HWND owner=nullptr;
 HMENU popup=nullptr;
 Microsoft::WRL::ComPtr<IContextMenu> menu;
 Microsoft::WRL::ComPtr<IContextMenu2> two;
 Microsoft::WRL::ComPtr<IContextMenu3> three;
 try {
  Microsoft::WRL::ComPtr<IShellFolder> folder;
  bool bound=true;
  for(std::size_t i=0;i<paths.size();++i){
   auto hr=::SHParseDisplayName(
       paths[i].c_str(),nullptr,&absolutes[i],0,nullptr);
   if(FAILED(hr)||!absolutes[i]){bound=false;break;}
   Microsoft::WRL::ComPtr<IShellFolder> currentFolder;
   PCUITEMID_CHILD child=nullptr;
   hr=::SHBindToParent(
       absolutes[i],IID_PPV_ARGS(&currentFolder),&child);
   if(FAILED(hr)||!currentFolder||!child){bound=false;break;}
   if(!folder)folder=currentFolder;
   children.push_back(child);
  }
  if(bound&&folder&&children.size()==paths.size()){
    owner=::CreateWindowExW(WS_EX_TOOLWINDOW,L"STATIC",
             L"flyExplorer Shell menu (test-owned child)",WS_POPUP,
             x,y,1,1,nullptr,nullptr,::GetModuleHandleW(nullptr),nullptr);
    if(owner){
     const auto hr=folder->GetUIObjectOf(
         owner,static_cast<UINT>(children.size()),children.data(),
         IID_IContextMenu,nullptr,
         reinterpret_cast<void**>(menu.GetAddressOf()));
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
             // For multiple items allow only the well-known
             // nonmutating Properties verb. Native flyExplorer
             // handles clipboard/file operations independently.
             if(paths.size()>1&&verb!="properties")rc=65;
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
 }catch(...){rc=68;}
 if(popup)::DestroyMenu(popup);
 if(owner)::DestroyWindow(owner);
 for(auto item:absolutes)if(item)::CoTaskMemFree(item);
 ::CoUninitialize();
 return rc;
}
} // namespace

namespace {
std::wstring sqlQuoted(std::wstring const& s) {
 std::wstring escaped;
 escaped.reserve(s.size()+12);
 for(wchar_t c:s) {
  if(c==L'\'')escaped+=L"''";
  else escaped.push_back(c);
 }
 return escaped;
}
bool insideScope(std::wstring const& scope,std::wstring const& path) {
 if(path.size()<=scope.size())return false;
 if(::CompareStringOrdinal(
    scope.c_str(),static_cast<int>(scope.size()),
    path.c_str(),static_cast<int>(scope.size()),TRUE)!=CSTR_EQUAL)return false;
 return scope.back()==L'\\'||path[scope.size()]==L'\\';
}
int runIndexedFilenameSearch(HANDLE output,
                             std::wstring const& scope,
                             std::wstring const& term,
                             std::wstring extension,
                             std::wstring const& minimumKb,
                             std::wstring const& maximumKb,
                             std::wstring const& modifiedAfter,
                             std::wstring const& modifiedBefore) {
 using namespace fxfile::indexwire;
 if(!extension.empty()&&extension.front()==L'.')extension.erase(0,1);
 bool hasMin=false,hasMax=false;
 std::uint64_t minBytes=0,maxBytes=0;
 std::uint32_t afterDate=0,beforeDate=0;
 if(!output||output==INVALID_HANDLE_VALUE||
    !validScope(scope)||!validTerm(term)||
    (!extension.empty()&&!validExtension(extension))||
    !parseIndexedSizeKb(minimumKb,hasMin,minBytes)||
    !parseIndexedSizeKb(maximumKb,hasMax,maxBytes)||
    (hasMin&&hasMax&&minBytes>maxBytes)||
    !parseIndexedDate(modifiedAfter,afterDate)||
    !parseIndexedDate(modifiedBefore,beforeDate)||
    (afterDate&&beforeDate&&afterDate>beforeDate))return 1;
 DWORD error=ERROR_SUCCESS;
 std::vector<std::wstring> results;
 bool truncated=false;
 const HRESULT apartment=::CoInitializeEx(
     nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(apartment))error=ERROR_SERVICE_NOT_ACTIVE;
 else {
  try {
   // All index-provider and filesystem calls run only in this disposable
   // child. The parent can terminate the owned Job on cancellation/timeout.
   std::filesystem::path path(scope);
   auto const root=path.root_path().native();
   if(root.size()!=3||::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)
     error=ERROR_NOT_SUPPORTED;
   else {
    std::filesystem::path part=path.root_path();
    for(auto it=path.begin();it!=path.end();++it) {
     if(*it==path.root_name()||*it==path.root_directory())continue;
     part/=*it;
     DWORD attrs=::GetFileAttributesW(part.c_str());
     if(attrs==INVALID_FILE_ATTRIBUTES||
        (attrs&FILE_ATTRIBUTE_REPARSE_POINT)) {
      error=ERROR_INVALID_NAME;break;
     }
    }
    const DWORD attrs=::GetFileAttributesW(scope.c_str());
    if(error==ERROR_SUCCESS&&
       (attrs==INVALID_FILE_ATTRIBUTES||!(attrs&FILE_ATTRIBUTE_DIRECTORY)))
       error=ERROR_INVALID_NAME;
   }
   if(error==ERROR_SUCCESS){
    // Search.CollatorDSO queries *only* SystemIndex; never enumerate the
    // directory as a fallback for unindexed scopes.
    std::wstring url=L"file:"+scope;
    std::replace(url.begin(),url.end(),L'\\',L'/');
    if(url.back()!=L'/')url+=L'/';
    std::wstring sql=L"SELECT TOP 1001 System.ItemUrl FROM SystemIndex "
        L"WHERE SCOPE='"+sqlQuoted(url)+L"' AND System.FileName LIKE '%"+
        sqlQuoted(term)+L"%'";
    if(!extension.empty())
     sql+=L" AND System.FileExtension = '."+sqlQuoted(extension)+L"'";
    if(hasMin)sql+=L" AND System.Size >= "+std::to_wstring(minBytes);
    if(hasMax)sql+=L" AND System.Size <= "+std::to_wstring(maxBytes);
    // SQL is a conservative prefilter across local/UTC/DST boundaries.
    // Exact inclusive dates are checked against the live file below.
    std::uint32_t sqlDay=0;
    if(afterDate&&offsetIndexedDate(afterDate,-1,sqlDay))
     sql+=L" AND System.DateModified >= '"+indexedSqlMidnight(sqlDay)+L"'";
    if(beforeDate&&offsetIndexedDate(beforeDate,2,sqlDay))
     sql+=L" AND System.DateModified < '"+indexedSqlMidnight(sqlDay)+L"'";
    ATL::CDataSource data;
    HRESULT hr=data.OpenFromInitializationString(
      L"Provider=Search.CollatorDSO.1;Extended Properties=\"Application=Windows\"");
    if(FAILED(hr))error=ERROR_SERVICE_NOT_ACTIVE;
    else {
     ATL::CSession session;
     hr=session.Open(data);
     if(FAILED(hr))error=ERROR_SERVICE_NOT_ACTIVE;
     else {
      ATL::CCommand<ATL::CDynamicStringAccessorW,ATL::CRowset> rows;
      hr=rows.Open(session,sql.c_str());
      if(FAILED(hr))error=ERROR_INVALID_DATA;
      else {
       for(hr=rows.MoveFirst();hr==S_OK;hr=rows.MoveNext()){
        const wchar_t* raw=rows.GetString(1);
        if(!raw)continue;
        // ItemPathDisplay is a friendly presentation path and may hide
        // extensions. ItemUrl carries the indexed filesystem identity.
        // Convert only local drive file: URLs; never materialize provider,
        // network or extended-device locations from an indexed row.
        std::wstring url(raw);
        if(url.size()<8||::_wcsnicmp(url.c_str(),L"file:",5)!=0)
         continue;
        url.erase(0,5);
        if(url.rfind(L"///",0)==0)url.erase(0,3);
        else if(!url.empty()&&url.front()==L'/')url.erase(0,1);
        std::replace(url.begin(),url.end(),L'/',L'\\');
        if(!fxfile::indexwire::validScope(url))continue;
        const std::wstring result=
            std::filesystem::path(url).lexically_normal().native();
        if(result.size()>fxfile::indexwire::kMaxPathUnits||
           !insideScope(scope,result))continue;
        auto name=std::filesystem::path(result).filename().native();
        std::wstring lowerName=name,lowerTerm=term;
        std::transform(lowerName.begin(),lowerName.end(),lowerName.begin(),
            [](wchar_t x){return static_cast<wchar_t>(::towlower(x));});
        std::transform(lowerTerm.begin(),lowerTerm.end(),lowerTerm.begin(),
            [](wchar_t x){return static_cast<wchar_t>(::towlower(x));});
        if(lowerName.find(lowerTerm)==std::wstring::npos)continue;
        if(!extension.empty()){
         const auto dot=name.find_last_of(L'.');
         if(dot==std::wstring::npos||dot+1>=name.size()||
            ::CompareStringOrdinal(
              name.c_str()+dot+1,static_cast<int>(name.size()-dot-1),
              extension.c_str(),static_cast<int>(extension.size()),
              TRUE)!=CSTR_EQUAL)continue;
        }
        WIN32_FILE_ATTRIBUTE_DATA item{};
        if(!::GetFileAttributesExW(
               result.c_str(),GetFileExInfoStandard,&item)||
           (item.dwFileAttributes&
            (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
         continue;
        // Index records can be stale. Recheck the current size in the helper.
        const std::uint64_t actualSize=
            (static_cast<std::uint64_t>(item.nFileSizeHigh)<<32)|
            item.nFileSizeLow;
        if((hasMin&&actualSize<minBytes)||
           (hasMax&&actualSize>maxBytes))continue;
        if(afterDate||beforeDate){
         FILETIME local{};
         SYSTEMTIME localTime{};
         if(!::FileTimeToLocalFileTime(&item.ftLastWriteTime,&local)||
            !::FileTimeToSystemTime(&local,&localTime))continue;
         const auto actualDate=static_cast<std::uint32_t>(
             localTime.wYear*10000+localTime.wMonth*100+localTime.wDay);
         if((afterDate&&actualDate<afterDate)||
            (beforeDate&&actualDate>beforeDate))continue;
        }
        if(results.size()>=fxfile::indexwire::kMaxResults){truncated=true;break;}
        results.push_back(std::move(result));
       }
       if(FAILED(hr))error=ERROR_INVALID_DATA;
       rows.Close();
      }
      session.Close();
     }
     data.Close();
    }
   }
  }catch(...){error=ERROR_INVALID_DATA;}
  ::CoUninitialize();
 }
 std::vector<unsigned char> body;
 std::uint32_t encodedCount=0;
 if(error==ERROR_SUCCESS){
  for(auto const& result:results){
   const auto units=static_cast<std::uint32_t>(result.size());
   const auto needed=sizeof(units)+units*sizeof(wchar_t);
   if(needed>fxfile::indexwire::kMaxBodyBytes||
      body.size()>fxfile::indexwire::kMaxBodyBytes-needed){
    // Preserve every previously encoded result; the byte budget is an
    // independent cap from the 1,000-item display cap.
    truncated=true;break;
   }
   auto const* start=reinterpret_cast<unsigned char const*>(&units);
   body.insert(body.end(),start,start+sizeof(units));
   start=reinterpret_cast<unsigned char const*>(result.data());
   body.insert(body.end(),start,start+units*sizeof(wchar_t));
   ++encodedCount;
  }
 }
 Header header{fxfile::indexwire::kMagic,fxfile::indexwire::kVersion,error==ERROR_SUCCESS&&truncated?
     ERROR_MORE_DATA:error,encodedCount,
     static_cast<std::uint32_t>(body.size()),fxfile::indexwire::checksum(body.data(),body.size())};
 return exactWrite(output,&header,sizeof(header))&&
        (body.empty()||exactWrite(output,body.data(),body.size()))?0:2;
}
} // namespace

int wmain(int argc,wchar_t** argv) {
    if((argc==4||argc==5||argc==7||argc==9)&&
       !wcscmp(argv[1],L"--indexed-filename-search"))
        return runIndexedFilenameSearch(::GetStdHandle(STD_OUTPUT_HANDLE),
            argv[2],argv[3],argc>=5?argv[4]:L"",
            argc>=7?argv[5]:L"",argc>=7?argv[6]:L"",
            argc==9?argv[7]:L"",argc==9?argv[8]:L"");
    if(argc==2&&!wcscmp(argv[1],L"--file-transfer"))
        return fxfile::shelltransfer::runIsolatedHelper(
            ::GetStdHandle(STD_INPUT_HANDLE),::GetStdHandle(STD_OUTPUT_HANDLE));
    if(argc==2&&!wcscmp(argv[1],L"--shell-item-visuals")){
        auto input=::GetStdHandle(STD_INPUT_HANDLE);
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!input||input==INVALID_HANDLE_VALUE||
           !output||output==INVALID_HANDLE_VALUE)return 90;
        fxfile::visualwire::RequestHeader request{};
        if(!exactRead(input,&request,sizeof(request))||
           request.magic!=fxfile::visualwire::kMagic||
           request.version!=fxfile::visualwire::kVersion||
           !request.count||request.count>fxfile::visualwire::kMaxItems||
           request.pixels<fxfile::visualwire::kMinPixels||
           request.pixels>fxfile::visualwire::kMaxPixels||
           request.bodyBytes>fxfile::visualwire::kMaxBodyBytes)return 91;
        std::vector<unsigned char> body(request.bodyBytes);
        if(request.bodyBytes&&!exactRead(
             input,body.data(),body.size()))return 92;
        if(fxfile::visualwire::checksum(body.data(),body.size())!=
           request.checksum)return 93;
        std::vector<std::wstring> names;
        std::vector<std::uint32_t> itemFlags;
        names.reserve(request.count);
        itemFlags.reserve(request.count);
        std::uint32_t thumbnailCount=0;
        size_t cursor=0;
        for(std::uint32_t i=0;i<request.count;++i){
            if(cursor+sizeof(fxfile::visualwire::ItemHeader)>body.size())
                return 94;
            fxfile::visualwire::ItemHeader item{};
            std::memcpy(&item,body.data()+cursor,sizeof(item));
            cursor+=sizeof(item);
            if(item.flags&~fxfile::visualwire::kWantThumbnail)return 94;
            if(item.flags&fxfile::visualwire::kWantThumbnail)
                ++thumbnailCount;
            if(item.units>fxfile::visualwire::kMaxNameUnits||
               static_cast<size_t>(item.units)>
                   (body.size()-cursor)/sizeof(wchar_t))return 94;
            std::wstring name(
                reinterpret_cast<wchar_t const*>(body.data()+cursor),
                item.units);
            cursor+=static_cast<size_t>(item.units)*sizeof(wchar_t);
            if(name.find(L'\0')!=std::wstring::npos)return 94;
            names.push_back(std::move(name));
            itemFlags.push_back(item.flags);
        }
        if(cursor!=body.size()||
           thumbnailCount>fxfile::visualwire::kMaxThumbnailItems||
           (thumbnailCount&&
             (request.thumbnailPixels<
                 fxfile::visualwire::kMinThumbnailPixels||
              request.thumbnailPixels>
                 fxfile::visualwire::kMaxThumbnailPixels))||
           (!thumbnailCount&&request.thumbnailPixels!=0))return 94;
        const auto apt=::CoInitializeEx(
            nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
        if(FAILED(apt))return 95;
        int resultCode=0;
        for(std::size_t i=0;i<names.size()&&resultCode==0;++i){
            std::wstring label;
            std::vector<unsigned char> pixels;
            std::vector<unsigned char> thumbnail;
            std::uint32_t thumbnailWidth=0,thumbnailHeight=0;
            PIDLIST_ABSOLUTE absolute=nullptr;
            HICON icon=nullptr;
            try{
                if(!names[i].empty()&&
                   SUCCEEDED(::SHParseDisplayName(
                    names[i].c_str(),nullptr,&absolute,0,nullptr))&&absolute){
                    SHFILEINFOW info{};
                    const auto flags=SHGFI_PIDL|SHGFI_TYPENAME|SHGFI_ICON|
                        (request.pixels<=16?SHGFI_SMALLICON:SHGFI_LARGEICON);
                    if(::SHGetFileInfoW(
                        reinterpret_cast<LPCWSTR>(absolute),0,&info,
                        sizeof(info),flags)){
                        label=info.szTypeName;
                        if(label.size()>fxfile::visualwire::kMaxLabelUnits||
                           std::any_of(label.begin(),label.end(),[](wchar_t ch){
                               return ch<32||ch==127;}))
                            label.clear();
                        icon=info.hIcon;
                    }
                    if(itemFlags[i]&fxfile::visualwire::kWantThumbnail){
                        Microsoft::WRL::ComPtr<IShellItem> item;
                        if(SUCCEEDED(::SHCreateItemFromIDList(
                             absolute,IID_PPV_ARGS(&item)))){
                            Microsoft::WRL::ComPtr<IShellItemImageFactory>
                                factory;
                            if(SUCCEEDED(item.As(&factory))){
                                HBITMAP bitmap=nullptr;
                                SIZE requested{
                                    static_cast<LONG>(request.thumbnailPixels),
                                    static_cast<LONG>(request.thumbnailPixels)};
                                if(SUCCEEDED(factory->GetImage(
                                     requested,SIIGBF_THUMBNAILONLY|
                                     SIIGBF_BIGGERSIZEOK,&bitmap))&&bitmap){
                                    BITMAP bm{};
                                    if(::GetObjectW(
                                         bitmap,sizeof(bm),&bm)==sizeof(bm)&&
                                       bm.bmWidth>0&&bm.bmHeight>0&&
                                       bm.bmWidth<=static_cast<LONG>(
                                          fxfile::visualwire::
                                            kMaxThumbnailPixels)&&
                                       bm.bmHeight<=static_cast<LONG>(
                                          fxfile::visualwire::
                                            kMaxThumbnailPixels)){
                                        thumbnailWidth=
                                            static_cast<std::uint32_t>(
                                                bm.bmWidth);
                                        thumbnailHeight=
                                            static_cast<std::uint32_t>(
                                                bm.bmHeight);
                                        BITMAPINFO dib{};
                                        dib.bmiHeader.biSize=
                                            sizeof(BITMAPINFOHEADER);
                                        dib.bmiHeader.biWidth=bm.bmWidth;
                                        dib.bmiHeader.biHeight=-bm.bmHeight;
                                        dib.bmiHeader.biPlanes=1;
                                        dib.bmiHeader.biBitCount=32;
                                        dib.bmiHeader.biCompression=BI_RGB;
                                        thumbnail.resize(
                                            static_cast<size_t>(
                                                thumbnailWidth)*
                                            thumbnailHeight*4);
                                        HDC screen=::GetDC(nullptr);
                                        if(!screen||::GetDIBits(
                                             screen,bitmap,0,thumbnailHeight,
                                             thumbnail.data(),&dib,
                                             DIB_RGB_COLORS)!=
                                               static_cast<int>(
                                                  thumbnailHeight)){
                                            thumbnail.clear();
                                            thumbnailWidth=thumbnailHeight=0;
                                        }else{
                                            bool anyAlpha=false;
                                            for(size_t p=3;
                                                p<thumbnail.size();p+=4)
                                                anyAlpha|=thumbnail[p]!=0;
                                            if(!anyAlpha)
                                                for(size_t p=3;
                                                    p<thumbnail.size();p+=4)
                                                    thumbnail[p]=255;
                                        }
                                        if(screen)
                                            ::ReleaseDC(nullptr,screen);
                                    }
                                    ::DeleteObject(bitmap);
                                }
                            }
                        }
                    }
                }
                if(icon){
                    BITMAPINFO bitmap{};
                    bitmap.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                    bitmap.bmiHeader.biWidth=static_cast<LONG>(request.pixels);
                    bitmap.bmiHeader.biHeight=-static_cast<LONG>(request.pixels);
                    bitmap.bmiHeader.biPlanes=1;
                    bitmap.bmiHeader.biBitCount=32;
                    bitmap.bmiHeader.biCompression=BI_RGB;
                    void* raw=nullptr;
                    HDC screen=::GetDC(nullptr);
                    HDC memory=screen?::CreateCompatibleDC(screen):nullptr;
                    HBITMAP image=memory?::CreateDIBSection(
                        memory,&bitmap,DIB_RGB_COLORS,&raw,nullptr,0):nullptr;
                    if(memory&&image&&raw){
                        auto old=::SelectObject(memory,image);
                        std::memset(raw,0,
                            static_cast<size_t>(request.pixels)*
                            request.pixels*4);
                        if(::DrawIconEx(
                            memory,0,0,icon,request.pixels,request.pixels,
                            0,nullptr,DI_NORMAL)){
                            const auto bytes=static_cast<size_t>(
                                request.pixels)*request.pixels*4;
                            auto* begin=static_cast<unsigned char*>(raw);
                            pixels.assign(begin,begin+bytes);
                        }
                        ::SelectObject(memory,old);
                    }
                    if(image)::DeleteObject(image);
                    if(memory)::DeleteDC(memory);
                    if(screen)::ReleaseDC(nullptr,screen);
                }
            }catch(...){
                label.clear();
                pixels.clear();
                thumbnail.clear();
                thumbnailWidth=thumbnailHeight=0;
            }
            if(icon)::DestroyIcon(icon);
            if(absolute)::CoTaskMemFree(absolute);
            fxfile::visualwire::ResultHeader result{
                fxfile::visualwire::kMagic,fxfile::visualwire::kVersion,
                static_cast<std::uint32_t>(i),
                static_cast<std::uint32_t>(label.size()),
                static_cast<std::uint32_t>(pixels.size()),
                thumbnailWidth,thumbnailHeight,
                static_cast<std::uint32_t>(thumbnail.size())};
            if(!exactWrite(output,&result,sizeof(result))||
               (!label.empty()&&!exactWrite(
                   output,label.data(),label.size()*sizeof(wchar_t)))||
               (!pixels.empty()&&!exactWrite(
                   output,pixels.data(),pixels.size()))||
               (!thumbnail.empty()&&!exactWrite(
                   output,thumbnail.data(),thumbnail.size())))
                resultCode=96;
        }
        ::CoUninitialize();
        return resultCode;
    }
    if(argc==2&&!wcscmp(argv[1],L"--file-metadata")){
        auto input=::GetStdHandle(STD_INPUT_HANDLE);
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!input||input==INVALID_HANDLE_VALUE||
           !output||output==INVALID_HANDLE_VALUE)return 79;
        fxfile::metadatawire::RequestHeader request{};
        if(!exactRead(input,&request,sizeof(request))||
           request.magic!=fxfile::metadatawire::kMagic||
           request.version!=fxfile::metadatawire::kVersion||
           !request.count||request.count>fxfile::metadatawire::kMaxItems||
           request.bodyBytes>fxfile::metadatawire::kMaxBodyBytes)return 80;
        std::vector<unsigned char> body(request.bodyBytes);
        if(request.bodyBytes&&!exactRead(
             input,body.data(),body.size()))return 81;
        if(fxfile::metadatawire::checksum(body.data(),body.size())!=
           request.checksum)return 82;
        auto cancelEvent=reinterpret_cast<HANDLE>(
            static_cast<std::uintptr_t>(request.cancelHandle));
        if(cancelEvent&&cancelEvent!=INVALID_HANDLE_VALUE&&
           ::WaitForSingleObject(cancelEvent,0)==WAIT_FAILED)return 83;
        std::size_t offset=0;
        for(std::uint32_t index=0;index<request.count;++index){
            if(cancelEvent&&
               ::WaitForSingleObject(cancelEvent,0)==WAIT_OBJECT_0)return 84;
            if(body.size()-offset<sizeof(std::uint32_t))return 85;
            std::uint32_t units=0;
            std::memcpy(&units,body.data()+offset,sizeof(units));
            offset+=sizeof(units);
            if(units>32000||
               static_cast<std::size_t>(units)>
                   (body.size()-offset)/sizeof(wchar_t))return 85;
            std::wstring path(units,L'\0');
            if(units)std::memcpy(
                path.data(),body.data()+offset,
                static_cast<std::size_t>(units)*sizeof(wchar_t));
            offset+=static_cast<std::size_t>(units)*sizeof(wchar_t);
            if(path.find(L'\0')!=std::wstring::npos)return 85;

            fxfile::metadatawire::Record record{};
            record.magic=fxfile::metadatawire::kMagic;
            record.version=fxfile::metadatawire::kVersion;
            record.index=index;
            record.error=ERROR_INVALID_NAME;
            try{
                if(!path.empty()){
                    std::filesystem::path native(path);
                    if(native.is_absolute()){
                        WIN32_FILE_ATTRIBUTE_DATA data{};
                        if(::GetFileAttributesExW(
                             path.c_str(),GetFileExInfoStandard,&data)){
                            if(data.dwFileAttributes&
                               FILE_ATTRIBUTE_REPARSE_POINT){
                                record.error=ERROR_CANT_ACCESS_FILE;
                            }else{
                                record.valid=1;
                                record.error=ERROR_SUCCESS;
                                record.attributes=data.dwFileAttributes;
                                record.bytes=(
                                    static_cast<std::uint64_t>(
                                        data.nFileSizeHigh)<<32)|
                                    data.nFileSizeLow;
                                ULARGE_INTEGER stamp{};
                                stamp.HighPart=
                                    data.ftLastWriteTime.dwHighDateTime;
                                stamp.LowPart=
                                    data.ftLastWriteTime.dwLowDateTime;
                                record.modified=stamp.QuadPart;
                            }
                        }else record.error=::GetLastError();
                    }
                }
            }catch(...){
                record.valid=0;
                record.error=ERROR_INVALID_NAME;
            }
            if(!exactWrite(output,&record,sizeof(record)))return 86;
        }
        return offset==body.size()?0:87;
    }
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
        std::wstring root;
        if(!fxfile::shelltransfer::transferDriveRoot(source,root))return 35;
        const auto driveType=::GetDriveTypeW(root.c_str());
        if(driveType!=DRIVE_FIXED&&driveType!=DRIVE_REMOVABLE&&
           driveType!=DRIVE_REMOTE)return 35;
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
