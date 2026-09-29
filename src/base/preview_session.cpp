#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "preview_session.h"
#include <array>
#include <vector>
#include <filesystem>
#include <algorithm>
#include <cstring>
namespace fxfile::previewsession {
namespace {
namespace fs=std::filesystem;
constexpr size_t MaxSize=131072;
constexpr unsigned char Magic[]={'F','X','S','E','S','S','2','3'};
std::wstring folder() {
 std::array<wchar_t,32768> buffer{};
 const auto count=::GetEnvironmentVariableW(L"LOCALAPPDATA",
       buffer.data(),static_cast<DWORD>(buffer.size()));
 return count&&count<buffer.size()?
    std::wstring(buffer.data(),count)+L"\\flyExplorer.WinUI3Preview":L"";
}
bool allowed(std::wstring const& value){
 if(value.size()<3||value.size()>2048||value[1]!=L':'||
    value[2]!=L'\\')return false;
 fs::path p(value);
 if(!p.is_absolute()||p.lexically_normal().native()!=value)return false;
 const auto root=p.root_path().native();
 if(root.size()!=3||::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
 fs::path cursor=p.root_path();
 for(auto const& component:p.relative_path()){
  if(component==L"."||component==L"..")return false;
  cursor/=component;
  const DWORD flags=::GetFileAttributesW(cursor.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||(flags&FILE_ATTRIBUTE_REPARSE_POINT))
   return false;
 }
 const auto flags=::GetFileAttributesW(value.c_str());
 return flags!=INVALID_FILE_ATTRIBUTES&&(flags&FILE_ATTRIBUTE_DIRECTORY)!=0;
}
void u32(std::vector<unsigned char>& data,std::uint32_t n){
 for(unsigned x=0;x<4;++x)data.push_back(static_cast<unsigned char>((n>>(8*x))&255));
}
bool read32(std::vector<unsigned char> const& d,size_t& pos,std::uint32_t& n){
 if(d.size()-pos<4)return false;
 n=0;
 for(unsigned x=0;x<4;++x)n|=std::uint32_t(d[pos++])<<(8*x);
 return true;
}
std::uint32_t checksum(std::vector<unsigned char> const& bytes,size_t count){
 std::uint32_t sum=2166136261u;
 for(size_t i=0;i<count;++i)sum=(sum^bytes[i])*16777619u;
 return sum;
}
bool encode(Session const& state,std::vector<unsigned char>& bytes){
 if(!valid(state))return false;
 bytes.assign(std::begin(Magic),std::end(Magic));
 for(auto item:{1u,static_cast<unsigned>(state.split),state.width,state.height,
                state.splitPermille,state.sort[0],state.sort[1],
                state.selected[0],state.selected[1],state.activeSide,
                static_cast<std::uint32_t>(state.paths[0].size()),
                static_cast<std::uint32_t>(state.paths[1].size())})u32(bytes,item);
 for(auto const& list:state.paths)
  for(auto const& path:list){
   u32(bytes,static_cast<std::uint32_t>(path.size()));
   auto const* p=reinterpret_cast<unsigned char const*>(path.data());
   bytes.insert(bytes.end(),p,p+path.size()*sizeof(wchar_t));
  }
 if(bytes.size()+4>MaxSize)return false;
 u32(bytes,checksum(bytes,bytes.size()));
 return true;
}
}
std::wstring privatePath(){
 auto const dir=folder();
 return dir.empty()?L"":dir+L"\\winui-session-v1.bin";
}
bool valid(Session const& value) noexcept{
 try{
  if(value.width<640||value.width>3200||
     value.height<420||value.height>2200||
     value.splitPermille<300||value.splitPermille>700||
     value.sort[0]>3||value.sort[1]>3||
     value.activeSide>1||(!value.split&&value.activeSide)||
     value.paths[0].empty()||value.paths[0].size()>8||
     value.paths[1].size()>8||
     (value.split&&value.paths[1].empty())||
     (!value.split&&!value.paths[1].empty())||
     value.selected[0]>=value.paths[0].size()||
     (value.split&&value.selected[1]>=value.paths[1].size())||
     (!value.split&&value.selected[1]))return false;
  for(auto const& list:value.paths)
   for(auto const& path:list)
    if(!allowed(path))return false;
  return true;
 }catch(...){return false;}
}
bool save(Session const& state) noexcept{
 try{
  std::vector<unsigned char> bytes{};
  if(!encode(state,bytes))return false;
  const auto dir=folder();
  if(dir.empty()||dir.size()>MAX_PATH-45)return false;
  if(!::CreateDirectoryW(dir.c_str(),nullptr)&&
     ::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
  auto attr=::GetFileAttributesW(dir.c_str());
  if(attr==INVALID_FILE_ATTRIBUTES||
     !(attr&FILE_ATTRIBUTE_DIRECTORY)||
     (attr&FILE_ATTRIBUTE_REPARSE_POINT))return false;
  wchar_t temp[MAX_PATH]{};
  if(!::GetTempFileNameW(dir.c_str(),L"fxs",0,temp))return false;
  HANDLE h=::CreateFileW(temp,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,
                          FILE_ATTRIBUTE_NORMAL,nullptr);
  if(h==INVALID_HANDLE_VALUE){::DeleteFileW(temp);return false;}
  DWORD written=0;
  bool good=::WriteFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),
            &written,nullptr)!=FALSE&&written==bytes.size();
  if(good)good=::FlushFileBuffers(h)!=FALSE;
  if(!::CloseHandle(h))good=false;
  if(good){
   const auto path=privatePath();
   good=::MoveFileExW(temp,path.c_str(),
          MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
  }
  if(!good)::DeleteFileW(temp);
  return good;
 }catch(...){return false;}
}
bool load(Session& out) noexcept{
 out=Session{};
 try{
  const auto path=privatePath();
  if(path.empty())return false;
  const auto flags=::GetFileAttributesW(path.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||
     (flags&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY)))return false;
  HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,
      FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,
      FILE_ATTRIBUTE_NORMAL,nullptr);
  if(h==INVALID_HANDLE_VALUE)return false;
  LARGE_INTEGER n{};
  if(!::GetFileSizeEx(h,&n)||n.QuadPart<60||n.QuadPart>MaxSize){
   ::CloseHandle(h);return false;
  }
  std::vector<unsigned char> bytes(static_cast<size_t>(n.QuadPart));
  DWORD got=0;
  const bool ok=::ReadFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),
                          &got,nullptr)!=FALSE&&got==bytes.size();
  ::CloseHandle(h);
  if(!ok||std::memcmp(bytes.data(),Magic,sizeof(Magic)))return false;
  size_t pos=sizeof(Magic);
  std::array<std::uint32_t,12> header{};
  for(auto& n:header)if(!read32(bytes,pos,n))return false;
  if(header[0]!=1||header[1]>1||header[10]<1||header[10]>8||
     header[11]>8)return false;
  Session value{};
  value.split=header[1]==1;value.width=header[2];
  value.height=header[3];value.splitPermille=header[4];
  value.sort={{header[5],header[6]}};
  value.selected={{header[7],header[8]}};value.activeSide=header[9];
  for(size_t side=0;side<2;++side)
   for(size_t i=0;i<header[10+side];++i){
    std::uint32_t size=0;
    if(!read32(bytes,pos,size)||size<3||size>2048||
       pos>bytes.size()-4||size_t(size)*2>bytes.size()-pos-4)
       return false;
    std::wstring path(size,L'\0');
    std::memcpy(path.data(),bytes.data()+pos,size*2);
    pos+=size*2;
    if(path.find(L'\0')!=std::wstring::npos)return false;
    value.paths[side].push_back(std::move(path));
   }
  std::uint32_t stored=0;
  if(bytes.size()-pos!=4||!read32(bytes,pos,stored)||
     stored!=checksum(bytes,bytes.size()-4)||!valid(value))return false;
  out=std::move(value);
  return true;
 }catch(...){return false;}
}
bool clear() noexcept {
 try{
  auto path=privatePath();
  if(path.empty())return false;
  return ::DeleteFileW(path.c_str())!=FALSE||
         ::GetLastError()==ERROR_FILE_NOT_FOUND;
 }catch(...){return false;}
}
}
