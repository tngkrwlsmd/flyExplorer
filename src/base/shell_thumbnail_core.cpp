#define WIN32_LEAN_AND_MEAN
#include "shell_thumbnail_core.h"
#include <algorithm>
#include <cwctype>
#include <cstring>
#include <filesystem>
namespace fxfile::thumbnail {
namespace {
struct Handle {
 HANDLE value=nullptr;
 Handle()=default;
 explicit Handle(HANDLE h):value(h){}
 Handle(Handle const&)=delete;
 Handle& operator=(Handle const&)=delete;
 ~Handle(){close();}
 void close() noexcept {
  if(value&&value!=INVALID_HANDLE_VALUE)::CloseHandle(value);
  value=nullptr;
 }
};
bool exactWrite(HANDLE h,const void* data,size_t bytes){
 auto p=static_cast<unsigned char const*>(data);
 while(bytes){
  DWORD written=0;
  if(!::WriteFile(h,p,static_cast<DWORD>((std::min)(bytes,size_t{65536})),
                  &written,nullptr)||!written)return false;
  p+=written;bytes-=written;
 }
 return true;
}
bool localCandidate(std::wstring const& value) {
 namespace fs=std::filesystem;
 if(value.size()<5||value.size()>1024||
    value.find(L'\0')!=std::wstring::npos)return false;
 fs::path path(value);
 if(!path.is_absolute()||path.lexically_normal().native()!=value)
   return false;
 auto root=path.root_path().native();
 if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
 auto ext=path.extension().native();
 std::transform(ext.begin(),ext.end(),ext.begin(),[](wchar_t c){
  return static_cast<wchar_t>(::towlower(c));
 });
 return ext==L".png"||ext==L".jpg"||ext==L".jpeg"||
        ext==L".bmp"||ext==L".webp";
}
}
Result query(std::wstring const& helper,std::wstring const& localImagePath,
             DWORD timeoutMs) noexcept{
 Result empty;
 Handle childRead,hostWrite,hostRead,childWrite,process,thread;
 bool childStarted=false;
 try{
  namespace fs=std::filesystem;
  if(!localCandidate(localImagePath)||timeoutMs<200||timeoutMs>10000||
     !fs::path(helper).is_absolute()||
     fs::path(helper).filename()!=L"FlyShellIsolationHelper.exe"||
     !fs::is_regular_file(fs::path(helper)))return {};
  SECURITY_ATTRIBUTES sa{sizeof(sa),nullptr,TRUE};
  HANDLE a=nullptr,b=nullptr;
  if(!::CreatePipe(&a,&b,&sa,0))return {};
  childRead.value=a;hostWrite.value=b;
  if(!::SetHandleInformation(b,HANDLE_FLAG_INHERIT,0))return {};
  a=b=nullptr;
  if(!::CreatePipe(&a,&b,&sa,0))return {};
  hostRead.value=a;childWrite.value=b;
  if(!::SetHandleInformation(a,HANDLE_FLAG_INHERIT,0))return {};
  STARTUPINFOW start{sizeof(start)};
  start.dwFlags=STARTF_USESTDHANDLES;
  start.hStdInput=childRead.value;
  start.hStdOutput=childWrite.value;
  start.hStdError=::GetStdHandle(STD_ERROR_HANDLE);
  PROCESS_INFORMATION info{};
  std::wstring cmd=L"\""+helper+L"\" --file-thumbnail";
  if(!::CreateProcessW(helper.c_str(),cmd.data(),nullptr,nullptr,TRUE,
        CREATE_NO_WINDOW,nullptr,fs::path(helper).parent_path().c_str(),
        &start,&info))return {};
  childStarted=true;
  process.value=info.hProcess;thread.value=info.hThread;
  childRead.close();childWrite.close();
  const std::uint32_t units=static_cast<std::uint32_t>(
    localImagePath.size());
  if(!exactWrite(hostWrite.value,&units,sizeof(units))||
     !exactWrite(hostWrite.value,localImagePath.data(),
                 units*sizeof(wchar_t))){
    ::TerminateProcess(process.value,ERROR_WRITE_FAULT);
    ::WaitForSingleObject(process.value,250);
    return {};
  }
  hostWrite.close();
  std::vector<unsigned char> frame;
  frame.reserve(16396);
  size_t expected=0;
  std::uint32_t width=0,height=0;
  bool failed=false;
  const auto deadline=::GetTickCount64()+timeoutMs;
  for(;;){
   if(::GetTickCount64()>=deadline){failed=true;break;}
   DWORD available=0;
   if(!::PeekNamedPipe(hostRead.value,nullptr,0,nullptr,&available,nullptr)){
    if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0)break;
    failed=true;break;
   }
   if(available){
    if(available>65548-frame.size()){failed=true;break;}
    const auto chunk=(std::min)(available,DWORD{4096});
    const auto old=frame.size();
    frame.resize(old+chunk);
    DWORD got=0;
    if(!::ReadFile(hostRead.value,frame.data()+old,chunk,&got,nullptr)||
       !got){failed=true;break;}
    frame.resize(old+got);
    if(frame.size()>=12&&!expected){
     if(std::memcmp(frame.data(),"THMB",4)){failed=true;break;}
     std::memcpy(&width,frame.data()+4,4);
     std::memcpy(&height,frame.data()+8,4);
     if(width<16||width>128||height<16||height>128){
      failed=true;break;
     }
     expected=12+static_cast<size_t>(width)*height*4;
    }
    if(expected&&frame.size()>expected){failed=true;break;}
    continue;
   }
   if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0)break;
   ::Sleep(18);
  }
  if(failed){
   if(::WaitForSingleObject(process.value,0)!=WAIT_OBJECT_0)
     ::TerminateProcess(process.value,ERROR_TIMEOUT);
   ::WaitForSingleObject(process.value,250);
   return {};
  }
  DWORD exit=1;
  if(!::GetExitCodeProcess(process.value,&exit)||exit!=0||
     !expected||frame.size()!=expected)return {};
  Result done;
  done.width=width;done.height=height;
  done.bgra.assign(frame.begin()+12,frame.end());
  return done.valid()?std::move(done):Result{};
 }catch(...){
  if(childStarted&&process.value&&
     ::WaitForSingleObject(process.value,0)!=WAIT_OBJECT_0){
   ::TerminateProcess(process.value,ERROR_CANCELLED);
   ::WaitForSingleObject(process.value,250);
  }
  return empty;
 }
}
} // namespace fxfile::thumbnail
