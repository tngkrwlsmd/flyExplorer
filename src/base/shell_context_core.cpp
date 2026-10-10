#define WIN32_LEAN_AND_MEAN
#include "shell_context_core.h"
#include <algorithm>
#include <filesystem>
namespace fxfile::shellcontext {
namespace {
struct Handle {
 HANDLE value=nullptr;
 ~Handle(){close();}
 void close(){if(value&&value!=INVALID_HANDLE_VALUE)::CloseHandle(value);value=nullptr;}
};
bool writeAll(HANDLE handle,void const* body,size_t bytes) {
 auto p=static_cast<unsigned char const*>(body);
 while(bytes){
  DWORD n=0;
  if(!::WriteFile(handle,p,static_cast<DWORD>((std::min)(bytes,size_t{4096})),
           &n,nullptr)||!n)return false;
  p+=n;bytes-=n;
 }
 return true;
}
}
DWORD show(std::wstring const& helper,
           std::vector<std::wstring> const& paths,
           POINT point,DWORD timeoutMs) noexcept {
 namespace fs=std::filesystem;
 Handle childRead,hostWrite,process,thread;
 try{
  if(helper.empty()||paths.empty()||
     paths.size()>kMaxContextSelection||
     timeoutMs<1000||timeoutMs>90000||
     !fs::path(helper).is_absolute()||
     fs::path(helper).filename()!=L"FlyShellIsolationHelper.exe"||
     !fs::is_regular_file(fs::path(helper)))return ERROR_INVALID_PARAMETER;
  std::size_t totalUnits=0;
  auto const parent=fs::path(paths.front()).parent_path().native();
  for(std::size_t i=0;i<paths.size();++i){
   auto const& path=paths[i];
   if(path.size()<4||path.size()>1024||
      path.find(L'\0')!=std::wstring::npos||
      !fs::path(path).is_absolute()||
      fs::path(path).lexically_normal().native()!=path||
      ::CompareStringOrdinal(
          fs::path(path).parent_path().c_str(),-1,
          parent.c_str(),-1,TRUE)!=CSTR_EQUAL||
      path.size()>kMaxContextPathUnits-totalUnits)
       return ERROR_INVALID_PARAMETER;
   totalUnits+=path.size();
   for(std::size_t j=0;j<i;++j)
    if(::CompareStringOrdinal(paths[j].c_str(),-1,
                             path.c_str(),-1,TRUE)==CSTR_EQUAL)
      return ERROR_INVALID_PARAMETER;
  }
  SECURITY_ATTRIBUTES sa{sizeof(sa),nullptr,TRUE};
  HANDLE a=nullptr,b=nullptr;
  if(!::CreatePipe(&a,&b,&sa,0))return ::GetLastError();
  childRead.value=a;hostWrite.value=b;
  if(!::SetHandleInformation(b,HANDLE_FLAG_INHERIT,0))
    return ::GetLastError();
  auto nul=::CreateFileW(L"NUL",GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,
           &sa,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
  Handle out;out.value=nul;
  if(out.value==INVALID_HANDLE_VALUE)return ::GetLastError();
  STARTUPINFOW start{sizeof(start)};
  start.dwFlags=STARTF_USESTDHANDLES;
  start.hStdInput=childRead.value;
  start.hStdOutput=out.value;
  start.hStdError=out.value;
  std::wstring cmd=L"\""+helper+L"\" --context-menu";
  PROCESS_INFORMATION info{};
  if(!::CreateProcessW(helper.c_str(),cmd.data(),nullptr,nullptr,TRUE,
         CREATE_NO_WINDOW,nullptr,fs::path(helper).parent_path().c_str(),
         &start,&info))return ::GetLastError();
  process.value=info.hProcess;thread.value=info.hThread;
  childRead.close();out.close();
  // --context-menu wire: count, length-prefixed UTF-16 paths, x, y.
  // --context-inspect retains its legacy single-path request protocol.
  const auto count=static_cast<std::uint32_t>(paths.size());
  const int x=point.x,y=point.y;
  bool sent=writeAll(hostWrite.value,&count,4);
  for(auto const& path:paths){
   const auto units=static_cast<std::uint32_t>(path.size());
   sent=sent&&writeAll(hostWrite.value,&units,4)&&
        writeAll(hostWrite.value,path.data(),units*sizeof(wchar_t));
  }
  if(!sent||!writeAll(hostWrite.value,&x,4)||
     !writeAll(hostWrite.value,&y,4)){
    ::TerminateProcess(process.value,ERROR_WRITE_FAULT);
    ::WaitForSingleObject(process.value,350);
    return ERROR_WRITE_FAULT;
  }
  hostWrite.close();
  auto waited=::WaitForSingleObject(process.value,timeoutMs);
  if(waited!=WAIT_OBJECT_0){
    ::TerminateProcess(process.value,ERROR_TIMEOUT);
    ::WaitForSingleObject(process.value,350);
    return ERROR_TIMEOUT;
  }
  DWORD exit=ERROR_GEN_FAILURE;
  return ::GetExitCodeProcess(process.value,&exit)?exit:ERROR_GEN_FAILURE;
 }catch(...){
  if(process.value&&::WaitForSingleObject(process.value,0)!=WAIT_OBJECT_0){
   ::TerminateProcess(process.value,ERROR_CANCELLED);
   ::WaitForSingleObject(process.value,350);
  }
  return ERROR_INVALID_PARAMETER;
 }
}
} // namespace fxfile::shellcontext
