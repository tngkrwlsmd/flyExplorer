#include "m19_workspace.h"
#include <windows.h>
#include <algorithm>
#include <cwchar>
#include <cwctype>
#include <map>
#include <utility>
#include <vector>
namespace fxfile { namespace preview {
namespace {
constexpr DWORD kMaxBytes=1048576;
constexpr size_t kMaxTabs=32;
struct File {
    HANDLE handle=INVALID_HANDLE_VALUE;
    explicit File(HANDLE h):handle(h){}
    ~File(){if(handle!=INVALID_HANDLE_VALUE)::CloseHandle(handle);}
    File(File const&)=delete;
    File& operator=(File const&)=delete;
    bool valid()const{return handle!=INVALID_HANDLE_VALUE;}
};
using Values=std::map<std::wstring,std::wstring>;
std::wstring lower(std::wstring value) {
    for(auto& c:value)c=static_cast<wchar_t>(std::towlower(c));
    return value;
}
std::wstring trim(std::wstring const& src){
    auto left=src.find_first_not_of(L" \t\r\n");
    if(left==std::wstring::npos)return {};
    const auto right=src.find_last_not_of(L" \t\r\n");
    return src.substr(left,right-left+1);
}
bool extension(std::wstring const& path){
    return path.size()>12&&
       _wcsicmp(path.c_str()+path.size()-12,L".fxworkspace")==0;
}
bool validPath(std::wstring const& path) {
    if(path.empty()||path.size()>32760 ||
       path.find_first_of(L"\r\n")!=std::wstring::npos||
       path.find(L'\0')!=std::wstring::npos)return false;
    if(path.compare(0,2,L"::")==0)return true;
    const auto attrs=::GetFileAttributesW(path.c_str());
    return attrs!=INVALID_FILE_ATTRIBUTES &&
           (attrs&FILE_ATTRIBUTE_DIRECTORY)!=0;
}
bool validUtf16(std::wstring const& src){
    for(size_t i=0;i<src.size();++i) {
        const auto x=static_cast<unsigned>(src[i]);
        if(!x)return false;
        if(x>=0xd800 && x<=0xdbff) {
            if(++i==src.size())return false;
            const auto y=static_cast<unsigned>(src[i]);
            if(y<0xdc00||y>0xdfff)return false;
        } else if(x>=0xdc00&&x<=0xdfff)return false;
    }
    return true;
}
bool validate(Workspace const& w,std::wstring& reason) {
    for(int side=0;side<(w.split?2:1);++side){
        auto const& paths=w.paths[side];
        if(paths.empty()||paths.size()>kMaxTabs ||
           w.selected[side]>=paths.size()){
            reason=L"Invalid pane, number of tabs or selected tab.";
            return false;
        }
        for(auto const& path:paths){
            if(!validUtf16(path)||!validPath(path)){
                reason=L"Workspace refers to a missing or unsupported folder.";
                return false;
            }
        }
    }
    return true;
}
bool readExact(HANDLE handle,unsigned char* data,DWORD count) {
    while(count) {
        DWORD got=0;
        if(!::ReadFile(handle,data,count,&got,nullptr)||!got)return false;
        count-=got;data+=got;
    }
    return true;
}
bool writeExact(HANDLE handle,unsigned char const* data,size_t count) {
    while(count) {
        DWORD sent=0;
        const auto chunk=static_cast<DWORD>(std::min<size_t>(count,65536));
        if(!::WriteFile(handle,data,chunk,&sent,nullptr)||!sent)return false;
        data+=sent;count-=sent;
    }
    return true;
}
bool number(Values const& values,std::wstring const& key,
            unsigned& value) {
    auto i=values.find(key);
    if(i==values.end()||i->second.empty()||i->second.size()>9)return false;
    unsigned result=0;
    for(wchar_t digit:i->second){
        if(digit<L'0'||digit>L'9')return false;
        result=result*10+(digit-L'0');
    }
    value=result;
    return true;
}
} // namespace
bool loadWorkspace(std::wstring const& path,Workspace& output,
                   std::wstring& reason){
    reason.clear();
    if(!extension(path)) {
        reason=L"Choose an existing .fxworkspace file.";return false;
    }
    WIN32_FILE_ATTRIBUTE_DATA attrs{};
    if(!::GetFileAttributesExW(path.c_str(),GetFileExInfoStandard,&attrs) ||
       (attrs.dwFileAttributes&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))||
       attrs.nFileSizeHigh||attrs.nFileSizeLow<4 ||
       attrs.nFileSizeLow>kMaxBytes||attrs.nFileSizeLow%2) {
        reason=L"Invalid, oversized or reparse-point workspace file.";
        return false;
    }
    File file(::CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,
                nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr));
    if(!file.valid()) {
        reason=L"Cannot open workspace for reading.";return false;
    }
    BY_HANDLE_FILE_INFORMATION handleInfo{};
    if(!::GetFileInformationByHandle(file.handle,&handleInfo) ||
       (handleInfo.dwFileAttributes&
          (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)) ||
       handleInfo.nFileSizeHigh ||
       handleInfo.nFileSizeLow!=attrs.nFileSizeLow) {
        reason=L"Workspace changed or is not a regular file.";return false;
    }
    std::vector<unsigned char> raw(attrs.nFileSizeLow);
    if(!readExact(file.handle,raw.data(),attrs.nFileSizeLow)){
        reason=L"Cannot fully read workspace.";return false;
    }
    bool bigEndian=raw[0]==0xfe&&raw[1]==0xff;
    if(!bigEndian && (raw[0]!=0xff||raw[1]!=0xfe)){
        reason=L"Workspace must have a UTF-16 BOM.";return false;
    }
    std::wstring data;
    data.reserve((raw.size()-2)/2);
    for(size_t i=2;i<raw.size();i+=2){
        wchar_t c=bigEndian?
            static_cast<wchar_t>((raw[i]<<8)|raw[i+1]):
            static_cast<wchar_t>(raw[i]|(raw[i+1]<<8));
        data.push_back(c);
    }
    if(!validUtf16(data)){
        reason=L"Invalid UTF-16 workspace text.";return false;
    }
    Values values;
    std::wstring section;
    for(size_t pos=0;pos<data.size();){
        const auto end=data.find(L'\n',pos);
        auto line=trim(data.substr(pos,end==std::wstring::npos?
                                   std::wstring::npos:end-pos));
        pos=end==std::wstring::npos?data.size():end+1;
        if(line.empty()||line[0]==L';'||line[0]==L'#')continue;
        if(line.front()==L'[' && line.back()==L']'){
            section=lower(trim(line.substr(1,line.size()-2)));
            continue;
        }
        if(section!=L"main"&&section!=L"workspace")continue;
        const auto equal=line.find(L'=');
        if(equal==std::wstring::npos){reason=L"Invalid workspace key.";return false;}
        auto key=lower(trim(line.substr(0,equal)));
        auto value=trim(line.substr(equal+1));
        if(key.empty()||!values.emplace(section+L"/"+key,std::move(value)).second){
            reason=L"Duplicate or empty workspace key.";return false;
        }
    }
    unsigned schema=0,rows=0,cols=0;
    if(!number(values,L"workspace/schema",schema)||schema!=1 ||
       !number(values,L"main/main.view.row_count",rows)||
       !number(values,L"main/main.view.column_count",cols) ||
       rows!=1||(cols!=1&&cols!=2)){
        reason=L"Unsupported workspace schema or pane arrangement.";return false;
    }
    Workspace prepared{};
    prepared.split=cols==2;
    for(unsigned pane=0;pane<cols;++pane){
        auto prefix=L"main/main.view"+std::to_wstring(pane+1)+L".";
        unsigned selected=0;
        if(!number(values,prefix+L"current_tab",selected)){
            reason=L"Missing workspace selected tab.";return false;
        }
        for(size_t tab=1;tab<=kMaxTabs+1;++tab){
            auto found=values.find(prefix+L"tab"+std::to_wstring(tab)+L".path");
            if(found==values.end()||found->second.empty()){
                if(tab==1) {
                    reason=L"Workspace pane lacks its first tab.";return false;
                }
                break;
            }
            if(tab>kMaxTabs){
                reason=L"flyExplorer supports at most 32 tabs per pane.";return false;
            }
            prepared.paths[pane].push_back(found->second);
        }
        prepared.selected[pane]=selected;
    }
    if(!validate(prepared,reason))return false;
    output=std::move(prepared);return true;
}
bool saveWorkspaceNew(std::wstring const& path,
                      Workspace const& source,std::wstring& reason){
    reason.clear();
    if(!extension(path)){reason=L"Choose a .fxworkspace filename.";return false;}
    if(!validate(source,reason))return false;
    std::wstring text=L"[main]\r\n"
       L"main.view.row_count = 1\r\nmain.view.column_count = ";
    text+=source.split?L"2\r\n":L"1\r\n";
    for(int pane=0;pane<(source.split?2:1);++pane){
        const auto prefix=L"main.view"+std::to_wstring(pane+1)+L".";
        text+=prefix+L"current_tab = "+std::to_wstring(source.selected[pane])+L"\r\n";
        size_t tab=1;
        for(auto const& folder:source.paths[pane])
            text+=prefix+L"tab"+std::to_wstring(tab++)+L".path = "+folder+L"\r\n";
    }
    text+=L"\r\n[workspace]\r\nschema = 1\r\n";
    if(!validUtf16(text)||(text.size()+1)*2>kMaxBytes) {
        reason=L"Workspace too large or malformed.";return false;
    }
    // Fail if an existing user file already exists: the preview never
    // overwrites a named workspace and never writes to the MFC profile.
    File file(::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,
                 CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr));
    if(!file.valid()){
        reason=::GetLastError()==ERROR_FILE_EXISTS?
              L"Workspace exists. Choose another filename.":
              L"Could not create the requested workspace file.";
        return false;
    }
    const unsigned char bom[]={0xff,0xfe};
    const bool ok=writeExact(file.handle,bom,sizeof(bom)) &&
         writeExact(file.handle,
           reinterpret_cast<unsigned char const*>(text.data()),
           text.size()*sizeof(wchar_t)) &&
         ::FlushFileBuffers(file.handle)!=FALSE;
    if(!ok){
        // File is owned by this CREATE_NEW call, never an existing file.
        ::CloseHandle(file.handle);
        file.handle=INVALID_HANDLE_VALUE;
        ::DeleteFileW(path.c_str());
        reason=L"Workspace write failed; incomplete owned file discarded.";
    }
    return ok;
}
} }
