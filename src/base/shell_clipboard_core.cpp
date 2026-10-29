#define WIN32_LEAN_AND_MEAN
#include "shell_clipboard_core.h"
#include "shell_transfer_core.h"
#include "file_command_core.h"
#include "quoted_paths_text.h"
#include <shellapi.h>
#include <shlobj.h>
#include <filesystem>
#include <algorithm>
#include <cstring>
namespace fxfile::shellclipboard {
namespace {
constexpr size_t MaxBytes=sizeof(DROPFILES)+
    (shelltransfer::kMaxSourcePathUnits+1)*sizeof(wchar_t);
constexpr size_t MaxItems=shelltransfer::kMaxItems;
bool full(std::wstring const& s){
 if(s.empty()||s.size()>32000)return false;
 std::filesystem::path p(s);
 return p.is_absolute()&&p.has_root_directory()&&
    filecommand::validLeaf(p.filename().native())&&
    p.lexically_normal().native()==s;
}
}
bool valid(Payload const& payload) noexcept{
 try{
  if(payload.paths.empty()||payload.paths.size()>MaxItems)return false;
  std::vector<std::wstring> seen;
  size_t pathUnits=0;
  for(auto const& s:payload.paths){
   if(!full(s)||s.size()+1>shelltransfer::kMaxSourcePathUnits-pathUnits)
    return false;
   pathUnits+=s.size()+1;
   if(std::any_of(seen.begin(),seen.end(),[&](auto const& existing){
      return ::CompareStringOrdinal(existing.c_str(),-1,s.c_str(),-1,TRUE)==CSTR_EQUAL;
   }))return false;
   seen.push_back(s);
  }
  return true;
 }catch(...){return false;}
}
bool encode(Payload const& payload,std::vector<unsigned char>& buffer) noexcept{
 buffer.clear();
 if(!valid(payload))return false;
 try{
  size_t units=1; // extra terminal NUL
  for(auto const& path:payload.paths){
   if(path.size()>((MaxBytes-sizeof(DROPFILES))/(sizeof(wchar_t)))-units-1)
     return false;
   units+=path.size()+1;
  }
  const size_t size=sizeof(DROPFILES)+units*sizeof(wchar_t);
  if(size>MaxBytes)return false;
  buffer.assign(size,0);
  DROPFILES drop{};
  drop.pFiles=sizeof(DROPFILES);
  drop.fWide=TRUE;
  std::memcpy(buffer.data(),&drop,sizeof(drop));
  unsigned char* dest=buffer.data()+sizeof(drop);
  for(auto const& path:payload.paths){
   const size_t bytes=path.size()*sizeof(wchar_t);
   std::memcpy(dest,path.data(),bytes);
   dest+=bytes+sizeof(wchar_t);
  }
  return true;
 }catch(...){buffer.clear();return false;}
}
bool decode(void const* raw,size_t bytes,Payload& result) noexcept {
 result=Payload{};
 try{
  if(!raw||bytes<sizeof(DROPFILES)+4||bytes>MaxBytes)return false;
  DROPFILES drop{};
  std::memcpy(&drop,raw,sizeof(drop));
  if(!drop.fWide||drop.pFiles<sizeof(DROPFILES)||
      drop.pFiles%alignof(wchar_t)||drop.pFiles>bytes-4||
      (bytes-drop.pFiles)%sizeof(wchar_t))return false;
  auto const* p=static_cast<unsigned char const*>(raw)+drop.pFiles;
  const size_t count=(bytes-drop.pFiles)/sizeof(wchar_t);
  size_t i=0;
  bool terminated=false;
  while(i<count){
   wchar_t current{};
   std::memcpy(&current,p+i*sizeof(wchar_t),sizeof(wchar_t));
   if(current==0){
    if(result.paths.empty())return false;
    terminated=true;
    // Demand terminal *double* NUL and no opaque trailing payload.
    for(size_t k=i;k<count;++k){
     wchar_t c{};std::memcpy(&c,p+k*sizeof(wchar_t),sizeof(wchar_t));
     if(c)return false;
    }
    break;
   }
   auto start=i;
   for(;i<count;++i){
    wchar_t c{};std::memcpy(&c,p+i*sizeof(wchar_t),sizeof(wchar_t));
    if(!c)break;
   }
   if(i==count||i==start||result.paths.size()>=MaxItems)return false;
   std::wstring s;
   s.resize(i-start);
   std::memcpy(s.data(),p+start*sizeof(wchar_t),s.size()*sizeof(wchar_t));
   result.paths.push_back(std::move(s));
   ++i;
  }
  if(!terminated||!valid(result))return false;
  return true;
 }catch(...){result=Payload{};return false;}
}
DWORD write(HWND owner,Payload const& payload) noexcept{
 std::vector<unsigned char> bytes;
 if(!owner||!::IsWindow(owner)||!encode(payload,bytes))return ERROR_INVALID_PARAMETER;
 HGLOBAL file=::GlobalAlloc(GMEM_MOVEABLE,bytes.size());
 HGLOBAL effect=::GlobalAlloc(GMEM_MOVEABLE,sizeof(DWORD));
 if(!file||!effect){
  if(file)::GlobalFree(file);
  if(effect)::GlobalFree(effect);
  return ERROR_NOT_ENOUGH_MEMORY;
 }
 void* dest=::GlobalLock(file);
 if(!dest){::GlobalFree(file);::GlobalFree(effect);return ERROR_NOT_ENOUGH_MEMORY;}
 std::memcpy(dest,bytes.data(),bytes.size());::GlobalUnlock(file);
 DWORD dropEffect=payload.move?DROPEFFECT_MOVE:DROPEFFECT_COPY;
 dest=::GlobalLock(effect);
 if(!dest){::GlobalFree(file);::GlobalFree(effect);return ERROR_NOT_ENOUGH_MEMORY;}
 std::memcpy(dest,&dropEffect,sizeof(dropEffect));::GlobalUnlock(effect);
 const UINT dropFormat=::RegisterClipboardFormatW(L"Preferred DropEffect");
 if(!dropFormat){::GlobalFree(file);::GlobalFree(effect);return ERROR_NOT_SUPPORTED;}
 if(!::OpenClipboard(owner)){::GlobalFree(file);::GlobalFree(effect);return ERROR_BUSY;}
 if(!::EmptyClipboard()){
  DWORD error=::GetLastError();::CloseClipboard();
  ::GlobalFree(file);::GlobalFree(effect);return error;
 }
 // After EmptyClipboard we own the OS mutation. CF_HDROP must succeed;
 // never substitute text or overwrite arbitrary formats on read failures.
 DWORD answer=ERROR_SUCCESS;
 if(!::SetClipboardData(CF_HDROP,file)){answer=::GetLastError();::GlobalFree(file);}
 else file=nullptr;
 if(::SetClipboardData(dropFormat,effect))effect=nullptr;
 else {
  if(answer==ERROR_SUCCESS)answer=::GetLastError();
  ::GlobalFree(effect); // never report cut succeeded as copy
 }
 ::CloseClipboard();
 return answer;
}
DWORD writePathsText(HWND owner,Payload const& payload) noexcept{
 std::wstring text;
 if(!owner||!::IsWindow(owner)||payload.move||!valid(payload)||
    !formatQuotedPaths(payload.paths,
        shelltransfer::kMaxSourcePathUnits+4*MaxItems,text))
  return ERROR_INVALID_PARAMETER;
 // Allocate and populate before opening/emptying the user's clipboard.
 const auto bytes=(text.size()+1)*sizeof(wchar_t);
 HGLOBAL memory=::GlobalAlloc(GMEM_MOVEABLE,bytes);
 if(!memory)return ERROR_NOT_ENOUGH_MEMORY;
 auto dest=::GlobalLock(memory);
 if(!dest){::GlobalFree(memory);return ERROR_NOT_ENOUGH_MEMORY;}
 std::memcpy(dest,text.c_str(),bytes);
 ::GlobalUnlock(memory);
 if(!::OpenClipboard(owner)){::GlobalFree(memory);return ERROR_BUSY;}
 DWORD answer=ERROR_SUCCESS;
 if(!::EmptyClipboard()){
  answer=::GetLastError();
  if(answer==ERROR_SUCCESS)answer=ERROR_ACCESS_DENIED;
 }else if(!::SetClipboardData(CF_UNICODETEXT,memory)){
  answer=::GetLastError();
  if(answer==ERROR_SUCCESS)answer=ERROR_WRITE_FAULT;
 }else memory=nullptr; // Windows owns the successfully published handle.
 ::CloseClipboard();
 if(memory)::GlobalFree(memory);
 return answer;
}
DWORD read(Payload& payload) noexcept{
 payload=Payload{};
 if(!::OpenClipboard(nullptr))return ERROR_BUSY;
 DWORD answer=ERROR_INVALID_DATA;
 if(::IsClipboardFormatAvailable(CF_HDROP)){
  HANDLE global=::GetClipboardData(CF_HDROP);
  if(global&&::GlobalSize(global)>=sizeof(DROPFILES)+4&&
     ::GlobalSize(global)<=MaxBytes){
   // Windows Explorer may pad GlobalAlloc beyond the double-NUL.
   // The platform-owned DragQueryFileW parses external CF_HDROP;
   // decode() remains strict for our own in-memory wire tests.
   const UINT count=::DragQueryFileW(static_cast<HDROP>(global),0xFFFFFFFF,nullptr,0);
   if(count>0&&count<=MaxItems){
    Payload candidate;
    for(UINT index=0;index<count;++index){
     const UINT chars=::DragQueryFileW(static_cast<HDROP>(global),index,nullptr,0);
     if(!chars||chars>32000){candidate.paths.clear();break;}
     std::wstring path(chars+1,L'\0');
     if(::DragQueryFileW(static_cast<HDROP>(global),index,path.data(),chars+1)!=chars){
      candidate.paths.clear();break;
     }
     path.resize(chars);
     candidate.paths.push_back(std::move(path));
    }
    if(candidate.paths.size()==count&&valid(candidate)){
     payload=std::move(candidate);
     answer=ERROR_SUCCESS;
    }
   }
  }
 }
 if(answer==ERROR_SUCCESS){
  const UINT fmt=::RegisterClipboardFormatW(L"Preferred DropEffect");
  HANDLE raw=fmt?::GetClipboardData(fmt):nullptr;
  if(raw&&::GlobalSize(raw)>=sizeof(DWORD)){
   const void* data=::GlobalLock(raw);
   if(data){
    DWORD value=0;std::memcpy(&value,data,sizeof(value));
    // Ambiguous or missing effects always mean Copy, never Move.
    payload.move=value==DROPEFFECT_MOVE;
    ::GlobalUnlock(raw);
   }
  }
 }
 ::CloseClipboard();
 return answer;
}
} // namespace fxfile::shellclipboard
