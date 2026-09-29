#define WIN32_LEAN_AND_MEAN
#include "shell_assoc_type_core.h"
#include <algorithm>
#include <chrono>
#include <cwctype>
#include <filesystem>
#include <string>
#include <utility>

namespace fxfile::filetype {
bool safeExtension(std::wstring const& ext) noexcept {
 if(ext.size()<2||ext.size()>17||ext.front()!=L'.')return false;
 return std::all_of(ext.begin()+1,ext.end(),[](wchar_t ch){
  return (ch>=L'a'&&ch<=L'z')||(ch>=L'A'&&ch<=L'Z')||
         (ch>=L'0'&&ch<=L'9');
 });
}
namespace {
struct UniqueHandle {
 HANDLE h=nullptr;
 ~UniqueHandle(){if(h&&h!=INVALID_HANDLE_VALUE)::CloseHandle(h);}
 UniqueHandle()=default;
 explicit UniqueHandle(HANDLE x):h(x){}
 UniqueHandle(UniqueHandle const&)=delete;
 UniqueHandle& operator=(UniqueHandle const&)=delete;
};
std::wstring lowered(std::wstring x){
 std::transform(x.begin(),x.end(),x.begin(),[](wchar_t ch){
  return static_cast<wchar_t>(::towlower(ch));
 });
 return x;
}
std::wstring unicode(std::string const& source){
 if(source.empty()||source.size()>320)return {};
 auto count=::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,
       source.data(),static_cast<int>(source.size()),nullptr,0);
 if(count<=0||count>80)return {};
 std::wstring text(count,L'\0');
 if(::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,source.data(),
       static_cast<int>(source.size()),text.data(),count)!=count)return {};
 if(std::any_of(text.begin(),text.end(),[](wchar_t ch){
    return ch<32||ch==127;}))return {};
 return text;
}
}
std::unordered_map<std::wstring,std::wstring> query(
   std::wstring const& helper,std::vector<std::wstring> const& input,
   DWORD timeoutMs) noexcept{
 std::unordered_map<std::wstring,std::wstring> names;
 try{
  namespace fs=std::filesystem;
  if(helper.empty()||input.empty()||input.size()>24||
     timeoutMs<100||timeoutMs>10000||
     !fs::path(helper).is_absolute()||
     fs::path(helper).filename()!=L"FlyShellIsolationHelper.exe"||
     !fs::is_regular_file(fs::path(helper)))return names;
  std::vector<std::wstring> extensions;
  for(auto s:input){
   if(!safeExtension(s))return {};
   s=lowered(std::move(s));
   if(std::find(extensions.begin(),extensions.end(),s)!=extensions.end())
     return {};
   extensions.push_back(std::move(s));
  }
  std::wstring cmd=L"\""+helper+L"\" --file-types";
  for(auto const& ext:extensions)cmd+=L" "+ext;
  SECURITY_ATTRIBUTES sec{sizeof(sec),nullptr,TRUE};
  HANDLE read=nullptr,write=nullptr;
  if(!::CreatePipe(&read,&write,&sec,0))return {};
  UniqueHandle inputRead(read),inputWrite(write);
  if(!::SetHandleInformation(read,HANDLE_FLAG_INHERIT,0))return {};
  STARTUPINFOW start{sizeof(start)};
  start.dwFlags=STARTF_USESTDHANDLES;
  start.hStdInput=::GetStdHandle(STD_INPUT_HANDLE);
  start.hStdOutput=write;
  start.hStdError=::GetStdHandle(STD_ERROR_HANDLE);
  PROCESS_INFORMATION info{};
  if(!::CreateProcessW(helper.c_str(),cmd.data(),nullptr,nullptr,TRUE,
             CREATE_NO_WINDOW,nullptr,fs::path(helper).parent_path().c_str(),
             &start,&info))return {};
  UniqueHandle process(info.hProcess),thread(info.hThread);
  // Only the helper may retain write now. The parent never blocks on
  // a full stdout pipe: read available chunks until exit/timeout.
  ::CloseHandle(inputWrite.h);inputWrite.h=nullptr;
  const auto end=::GetTickCount64()+timeoutMs;
  std::string out;
  bool completed=false;
  while(::GetTickCount64()<end){
   DWORD available=0;
   if(!::PeekNamedPipe(read,nullptr,0,nullptr,&available,nullptr)){
    if(::WaitForSingleObject(process.h,0)==WAIT_OBJECT_0){completed=true;break;}
    return {};
   }
   if(available){
    char chunk[1024]{};
    DWORD got=0;
    if(!::ReadFile(read,chunk,
          (std::min)(available,static_cast<DWORD>(sizeof(chunk))),
          &got,nullptr))return {};
    if(out.size()+got>16384)return {};
    out.append(chunk,got);
    continue;
   }
   if(::WaitForSingleObject(process.h,0)==WAIT_OBJECT_0){completed=true;break;}
   ::Sleep(20);
  }
  if(!completed){
   // Exact owned helper process handle. Never terminate a user app.
   ::TerminateProcess(process.h,ERROR_TIMEOUT);
   ::WaitForSingleObject(process.h,200);
   return {};
  }
  DWORD exitCode=1;
  if(!::GetExitCodeProcess(process.h,&exitCode)||exitCode!=0)return {};
  // Drain the final stdout tail without blocking.
  for(;;){
   DWORD available=0;
   if(!::PeekNamedPipe(read,nullptr,0,nullptr,&available,nullptr)||!available)
     break;
   char chunk[1024]{};
   DWORD got=0;
   if(!::ReadFile(read,chunk,
      (std::min)(available,static_cast<DWORD>(sizeof(chunk))),&got,nullptr)||
      out.size()+got>16384)return {};
   out.append(chunk,got);
  }
  size_t cursor=0;
  while(cursor<out.size()){
   auto newline=out.find('\n',cursor);
   if(newline==std::string::npos)return {};
   auto tab=out.find('\t',cursor);
   if(tab==std::string::npos||tab>newline||tab-cursor>2)return {};
   const auto number=out.substr(cursor,tab-cursor);
   if(number.empty()||!std::all_of(number.begin(),number.end(),
       [](char ch){return ch>='0'&&ch<='9';}))return {};
   auto idx=static_cast<size_t>(std::stoul(number));
   if(idx>=extensions.size()||names.count(extensions[idx]))return {};
   std::string value(out,tab+1,newline-tab-1);
   auto readable=unicode(value);
   if(!readable.empty())names[extensions[idx]]=std::move(readable);
   cursor=newline+1;
  }
 }catch(...){return {};}
 return names;
}
} // namespace fxfile::filetype
