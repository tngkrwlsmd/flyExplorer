#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ui_session.h"
#include <array>
#include <vector>
#include <filesystem>
#include <algorithm>
#include <cstring>
namespace fxfile::uisession {
namespace {
namespace fs=std::filesystem;
constexpr size_t MaxSize=524288;
constexpr size_t MaxWindowTabs=10,MaxPaneTabs=8,MaxHistory=16;
constexpr unsigned char Magic[]={'F','X','S','E','S','S','2','3'};
constexpr std::uint32_t DisplayMask=0x0fu;
std::uint32_t displayFlags(PaneState const& pane) noexcept {
 return (pane.showSelectionCheckboxes?1u:0u)|
        (pane.compactRows?2u:0u)|
        (pane.showFileExtensions?4u:0u)|
        (pane.showHiddenItems?8u:0u);
}
void restoreDisplayFlags(PaneState& pane,std::uint32_t flags) noexcept {
 pane.showSelectionCheckboxes=(flags&1u)!=0;
 pane.compactRows=(flags&2u)!=0;
 pane.showFileExtensions=(flags&4u)!=0;
 pane.showHiddenItems=(flags&8u)!=0;
}
std::wstring folder() {
 std::array<wchar_t,32768> buffer{};
 const auto count=::GetEnvironmentVariableW(L"LOCALAPPDATA",
       buffer.data(),static_cast<DWORD>(buffer.size()));
 return count&&count<buffer.size()?
    std::wstring(buffer.data(),count)+L"\\flyExplorer":L"";
}
bool allowed(std::wstring const& value){
 if(value.size()<3||value.size()>2048||value[1]!=L':'||value[2]!=L'\\')return false;
 fs::path p(value);
 if(!p.is_absolute()||p.lexically_normal().native()!=value)return false;
 const auto root=p.root_path().native();
 if(root.size()!=3||::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
 fs::path cursor=p.root_path();
 for(auto const& component:p.relative_path()){
  if(component==L"."||component==L"..")return false;
  cursor/=component;
  const DWORD flags=::GetFileAttributesW(cursor.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||(flags&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 }
 const auto flags=::GetFileAttributesW(value.c_str());
 return flags!=INVALID_FILE_ATTRIBUTES&&(flags&FILE_ATTRIBUTE_DIRECTORY)!=0;
}
void u32(std::vector<unsigned char>& data,std::uint32_t n){
 for(unsigned x=0;x<4;++x)data.push_back(static_cast<unsigned char>((n>>(8*x))&255));
}
bool read32(std::vector<unsigned char> const& d,size_t& pos,std::uint32_t& n){
 if(pos>d.size()||d.size()-pos<4)return false;
 n=0;for(unsigned x=0;x<4;++x)n|=std::uint32_t(d[pos++])<<(8*x);return true;
}
std::uint32_t checksum(std::vector<unsigned char> const& bytes,size_t count){
 std::uint32_t sum=2166136261u;
 for(size_t i=0;i<count;++i)sum=(sum^bytes[i])*16777619u;
 return sum;
}
void putString(std::vector<unsigned char>& bytes,std::wstring const& value){
 u32(bytes,static_cast<std::uint32_t>(value.size()));
 auto const* p=reinterpret_cast<unsigned char const*>(value.data());
 bytes.insert(bytes.end(),p,p+value.size()*sizeof(wchar_t));
}
bool getString(std::vector<unsigned char> const& bytes,size_t& pos,std::wstring& value){
 std::uint32_t count=0;
 if(!read32(bytes,pos,count)||count<3||count>2048||pos>bytes.size()-4||
    size_t(count)*sizeof(wchar_t)>bytes.size()-pos-4)return false;
 value.assign(count,L'\0');
 std::memcpy(value.data(),bytes.data()+pos,count*sizeof(wchar_t));
 pos+=count*sizeof(wchar_t);
 return value.find(L'\0')==std::wstring::npos;
}
bool validLegacy(Session const& value){
 if(value.width<640||value.width>3200||value.height<420||value.height>2200||
    value.splitPermille<300||value.splitPermille>700||
    value.sort[0]>7||value.sort[1]>7||value.activeSide>1||
    (!value.split&&value.activeSide)||value.paths[0].empty()||
    value.paths[0].size()>MaxPaneTabs||value.paths[1].size()>MaxPaneTabs||
    (value.split&&value.paths[1].empty())||(!value.split&&!value.paths[1].empty())||
    value.selected[0]>=value.paths[0].size()||
    (value.split&&value.selected[1]>=value.paths[1].size())||
    (!value.split&&value.selected[1]))return false;
 for(auto const& list:value.paths)for(auto const& path:list)if(!allowed(path))return false;
 return true;
}
bool validPane(PaneState const& pane){
 if(pane.tabs.empty()||pane.tabs.size()>MaxPaneTabs||pane.selected>=pane.tabs.size()||
    pane.sort>7||pane.view>4||pane.nameColumnWidth<80||pane.nameColumnWidth>600)return false;
 for(auto const& tab:pane.tabs){
  if(!allowed(tab.path)||tab.back.size()>MaxHistory||tab.forward.size()>MaxHistory)return false;
  for(auto const& p:tab.back)if(!allowed(p))return false;
  for(auto const& p:tab.forward)if(!allowed(p))return false;
 }
 return true;
}
bool validV2(Session const& value){
 if(value.width<640||value.width>3200||value.height<420||value.height>2200||
    value.windowTabs.empty()||value.windowTabs.size()>MaxWindowTabs||
    value.activeWindow>=value.windowTabs.size())return false;
 for(auto const& tab:value.windowTabs){
  if(tab.splitPermille<300||tab.splitPermille>700||tab.activeSide>1||
     (!tab.split&&tab.activeSide)||!validPane(tab.panes[0])||!validPane(tab.panes[1]))
     return false;
 }
 return true;
}
bool encodeLegacy(Session const& state,std::vector<unsigned char>& bytes){
 if(!validLegacy(state))return false;
 bytes.assign(std::begin(Magic),std::end(Magic));
 for(auto item:{1u,static_cast<unsigned>(state.split),state.width,state.height,
                state.splitPermille,state.sort[0],state.sort[1],
                state.selected[0],state.selected[1],state.activeSide,
                static_cast<std::uint32_t>(state.paths[0].size()),
                static_cast<std::uint32_t>(state.paths[1].size())})u32(bytes,item);
 for(auto const& list:state.paths)for(auto const& path:list)putString(bytes,path);
 if(bytes.size()+4>MaxSize)return false;
 u32(bytes,checksum(bytes,bytes.size()));return true;
}
bool encodeV3(Session const& state,std::vector<unsigned char>& bytes){
 if(!validV2(state))return false;
 bytes.assign(std::begin(Magic),std::end(Magic));
 for(auto item:{3u,state.width,state.height,state.activeWindow,
                static_cast<std::uint32_t>(state.windowTabs.size())})u32(bytes,item);
 for(auto const& window:state.windowTabs){
  u32(bytes,window.split?1u:0u);u32(bytes,window.splitPermille);u32(bytes,window.activeSide);
  for(auto const& pane:window.panes){
   for(auto item:{pane.selected,pane.sort,pane.view,pane.nameColumnWidth,
                  displayFlags(pane),static_cast<std::uint32_t>(pane.tabs.size())})u32(bytes,item);
   for(auto const& tab:pane.tabs){
    putString(bytes,tab.path);
    u32(bytes,static_cast<std::uint32_t>(tab.back.size()));
    for(auto const& p:tab.back)putString(bytes,p);
    u32(bytes,static_cast<std::uint32_t>(tab.forward.size()));
    for(auto const& p:tab.forward)putString(bytes,p);
   }
  }
 }
 if(bytes.size()+4>MaxSize)return false;
 u32(bytes,checksum(bytes,bytes.size()));return true;
}
bool finishChecksum(std::vector<unsigned char> const& bytes,size_t pos){
 std::uint32_t stored=0;
 return bytes.size()-pos==4&&read32(bytes,pos,stored)&&
        stored==checksum(bytes,bytes.size()-4);
}
bool decodeV1(std::vector<unsigned char> const& bytes,size_t pos,Session& out){
 std::array<std::uint32_t,11> h{};
 for(auto& n:h)if(!read32(bytes,pos,n))return false;
 if(h[0]>1||h[9]<1||h[9]>MaxPaneTabs||h[10]>MaxPaneTabs)return false;
 Session value{};value.split=h[0]==1;value.width=h[1];value.height=h[2];
 value.splitPermille=h[3];value.sort={{h[4],h[5]}};
 value.selected={{h[6],h[7]}};value.activeSide=h[8];
 for(size_t side=0;side<2;++side)
  for(size_t i=0;i<h[9+side];++i){std::wstring p;if(!getString(bytes,pos,p))return false;value.paths[side].push_back(std::move(p));}
 if(!finishChecksum(bytes,pos)||!validLegacy(value))return false;
 out=std::move(value);return true;
}
bool decodeWindowTabs(std::vector<unsigned char> const& bytes,size_t pos,
                      Session& out,bool hasDisplayFlags){
 Session value{};std::uint32_t count=0;
 if(!read32(bytes,pos,value.width)||!read32(bytes,pos,value.height)||
    !read32(bytes,pos,value.activeWindow)||!read32(bytes,pos,count)||
    count<1||count>MaxWindowTabs)return false;
 value.windowTabs.reserve(count);
 for(std::uint32_t w=0;w<count;++w){
  WindowTab window{};std::uint32_t split=0;
  if(!read32(bytes,pos,split)||split>1||!read32(bytes,pos,window.splitPermille)||
     !read32(bytes,pos,window.activeSide))return false;
  window.split=split==1;
  for(auto& pane:window.panes){
   std::uint32_t tabs=0;
   if(!read32(bytes,pos,pane.selected)||!read32(bytes,pos,pane.sort)||
      !read32(bytes,pos,pane.view)||!read32(bytes,pos,pane.nameColumnWidth))return false;
   if(hasDisplayFlags){
    std::uint32_t flags=0;
    if(!read32(bytes,pos,flags)||(flags&~DisplayMask))return false;
    restoreDisplayFlags(pane,flags);
   }
   if(!read32(bytes,pos,tabs)||tabs<1||tabs>MaxPaneTabs)return false;
   pane.tabs.reserve(tabs);
   for(std::uint32_t i=0;i<tabs;++i){
    PaneTab tab{};std::uint32_t n=0;
    if(!getString(bytes,pos,tab.path)||!read32(bytes,pos,n)||n>MaxHistory)return false;
    for(std::uint32_t j=0;j<n;++j){std::wstring p;if(!getString(bytes,pos,p))return false;tab.back.push_back(std::move(p));}
    if(!read32(bytes,pos,n)||n>MaxHistory)return false;
    for(std::uint32_t j=0;j<n;++j){std::wstring p;if(!getString(bytes,pos,p))return false;tab.forward.push_back(std::move(p));}
    pane.tabs.push_back(std::move(tab));
   }
  }
  value.windowTabs.push_back(std::move(window));
 }
 if(!finishChecksum(bytes,pos)||!validV2(value))return false;
 out=std::move(value);return true;
}
bool decodeV2(std::vector<unsigned char> const& bytes,size_t pos,Session& out){
 return decodeWindowTabs(bytes,pos,out,false);
}
bool decodeV3(std::vector<unsigned char> const& bytes,size_t pos,Session& out){
 return decodeWindowTabs(bytes,pos,out,true);
}
}
std::wstring privatePath(){auto const dir=folder();return dir.empty()?L"":dir+L"\\winui-session-v1.bin";}
bool valid(Session const& value) noexcept{try{return value.windowTabs.empty()?validLegacy(value):validV2(value);}catch(...){return false;}}
bool save(Session const& state) noexcept{
 try{
  std::vector<unsigned char> bytes{};
  if(!(state.windowTabs.empty()?encodeLegacy(state,bytes):encodeV3(state,bytes)))return false;
  const auto dir=folder();if(dir.empty()||dir.size()>MAX_PATH-45)return false;
  if(!::CreateDirectoryW(dir.c_str(),nullptr)&&::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
  auto attr=::GetFileAttributesW(dir.c_str());
  if(attr==INVALID_FILE_ATTRIBUTES||!(attr&FILE_ATTRIBUTE_DIRECTORY)||(attr&FILE_ATTRIBUTE_REPARSE_POINT))return false;
  wchar_t temp[MAX_PATH]{};if(!::GetTempFileNameW(dir.c_str(),L"fxs",0,temp))return false;
  HANDLE h=::CreateFileW(temp,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(h==INVALID_HANDLE_VALUE){::DeleteFileW(temp);return false;}
  DWORD written=0;bool good=::WriteFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),&written,nullptr)!=FALSE&&written==bytes.size();
  if(good)good=::FlushFileBuffers(h)!=FALSE;if(!::CloseHandle(h))good=false;
  if(good)good=::MoveFileExW(temp,privatePath().c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
  if(!good)::DeleteFileW(temp);return good;
 }catch(...){return false;}
}
bool load(Session& out) noexcept{
 out=Session{};
 try{
  const auto path=privatePath();if(path.empty())return false;
  const auto flags=::GetFileAttributesW(path.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||(flags&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY)))return false;
  HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  if(h==INVALID_HANDLE_VALUE)return false;
  LARGE_INTEGER n{};if(!::GetFileSizeEx(h,&n)||n.QuadPart<28||n.QuadPart>MaxSize){::CloseHandle(h);return false;}
  std::vector<unsigned char> bytes(static_cast<size_t>(n.QuadPart));DWORD got=0;
  const bool ok=::ReadFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),&got,nullptr)!=FALSE&&got==bytes.size();::CloseHandle(h);
  if(!ok||std::memcmp(bytes.data(),Magic,sizeof(Magic)))return false;
  size_t pos=sizeof(Magic);std::uint32_t version=0;if(!read32(bytes,pos,version))return false;
  if(version==1)return decodeV1(bytes,pos,out);
  if(version==2)return decodeV2(bytes,pos,out);
  if(version==3)return decodeV3(bytes,pos,out);
  return false;
 }catch(...){return false;}
}
bool clear() noexcept{
 try{auto path=privatePath();if(path.empty())return false;return ::DeleteFileW(path.c_str())!=FALSE||::GetLastError()==ERROR_FILE_NOT_FOUND;}
 catch(...){return false;}
}
}
