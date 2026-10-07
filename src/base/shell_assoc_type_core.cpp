#define WIN32_LEAN_AND_MEAN
#include "shell_assoc_type_core.h"
#include "shell_visual_wire.h"
#include <algorithm>
#include <atomic>
#include <cwctype>
#include <filesystem>
#include <mutex>
#include <shlobj.h>
#include <string>
#include <utility>
#include <wincrypt.h>
#pragma comment(lib,"crypt32.lib")
#pragma comment(lib,"shell32.lib")

namespace fxfile::filetype {
bool safeExtension(std::wstring const& ext) noexcept {
 if(ext.size()<2||ext.size()>17||ext.front()!=L'.')return false;
 return std::all_of(ext.begin()+1,ext.end(),[](wchar_t ch){
  return (ch>=L'a'&&ch<=L'z')||(ch>=L'A'&&ch<=L'Z')||
         (ch>=L'0'&&ch<=L'9');
 });
}
bool safeKnownFolderKey(std::wstring const& key) noexcept {
 return key==L"desktop"||key==L"documents"||key==L"downloads"||
        key==L"pictures"||key==L"music"||key==L"videos";
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
struct KnownFolderSpec {
 wchar_t const* key;
 KNOWNFOLDERID const* id;
};
KnownFolderSpec const* knownFolderSpec(std::wstring const& key) noexcept {
 static const KnownFolderSpec specs[]{
  {L"desktop",&FOLDERID_Desktop},
  {L"documents",&FOLDERID_Documents},
  {L"downloads",&FOLDERID_Downloads},
  {L"pictures",&FOLDERID_Pictures},
  {L"music",&FOLDERID_Music},
  {L"videos",&FOLDERID_Videos},
 };
 for(auto const& spec:specs)if(key==spec.key)return &spec;
 return nullptr;
}
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
std::unordered_map<std::wstring,Visual> runVisualQuery(
   std::wstring const& helper,std::wstring const& mode,
   std::vector<std::wstring> const& keys,
   DWORD timeoutMs,std::uint32_t requestedPixels) noexcept {
 std::unordered_map<std::wstring,Visual> names;
 try{
  static std::mutex visualQueryMutex;
  std::lock_guard<std::mutex> visualQueryLock(visualQueryMutex);
  namespace fs=std::filesystem;
  if(helper.empty()||keys.empty()||keys.size()>24||
     timeoutMs<100||timeoutMs>10000||requestedPixels<16||requestedPixels>64||
     !fs::path(helper).is_absolute()||
     fs::path(helper).filename()!=L"FlyShellIsolationHelper.exe"||
     !fs::is_regular_file(fs::path(helper)))return names;
  std::wstring cmd=L"\""+helper+L"\" "+mode+L" "+
                   std::to_wstring(requestedPixels);
  for(auto const& key:keys)cmd+=L" "+key;
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
    if(out.size()+got>786432)return {};
    out.append(chunk,got);
    continue;
   }
   if(::WaitForSingleObject(process.h,0)==WAIT_OBJECT_0){completed=true;break;}
   ::Sleep(20);
  }
  if(!completed){
   ::TerminateProcess(process.h,ERROR_TIMEOUT);
   ::WaitForSingleObject(process.h,200);
   return {};
  }
  DWORD exitCode=1;
  if(!::GetExitCodeProcess(process.h,&exitCode)||exitCode!=0)return {};
  for(;;){
   DWORD available=0;
   if(!::PeekNamedPipe(read,nullptr,0,nullptr,&available,nullptr)||!available)
     break;
   char chunk[1024]{};
   DWORD got=0;
   if(!::ReadFile(read,chunk,
      (std::min)(available,static_cast<DWORD>(sizeof(chunk))),&got,nullptr)||
      out.size()+got>786432)return {};
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
   if(idx>=keys.size()||names.count(keys[idx]))return {};
   const auto second=out.find('\t',tab+1);
   if(second==std::string::npos||second>newline)return {};
   Visual visual;
   visual.label=unicode(out.substr(tab+1,second-tab-1));
   const auto b64=out.substr(second+1,newline-second-1);
   if(!b64.empty()&&b64.size()<40000){
    DWORD required=0;
    const auto expected=requestedPixels*requestedPixels*4;
    if(::CryptStringToBinaryA(b64.c_str(),
        static_cast<DWORD>(b64.size()),CRYPT_STRING_BASE64,
        nullptr,&required,nullptr,nullptr)&&required==expected){
      visual.bgra.resize(required);
      if(!::CryptStringToBinaryA(b64.c_str(),
        static_cast<DWORD>(b64.size()),CRYPT_STRING_BASE64,
        visual.bgra.data(),&required,nullptr,nullptr)||
        required!=expected)visual.bgra.clear();
      else{visual.width=requestedPixels;visual.height=requestedPixels;}
    }
   }
   if(!visual.label.empty()||visual.bgra.size()==
      static_cast<size_t>(requestedPixels)*requestedPixels*4)
    names[keys[idx]]=std::move(visual);
   cursor=newline+1;
  }
 }catch(...){return {};}
 return names;
}
}
std::wstring knownFolderPath(std::wstring const& input) noexcept {
 try{
  auto key=lowered(input);
  if(!safeKnownFolderKey(key))return {};
  auto spec=knownFolderSpec(key);
  if(!spec)return {};
  PWSTR raw=nullptr;
  if(FAILED(::SHGetKnownFolderPath(*spec->id,KF_FLAG_DEFAULT,nullptr,&raw))||
     !raw)return {};
  std::wstring result(raw);
  ::CoTaskMemFree(raw);
  if(result.empty()||result.size()>1024||
     result.find(L'\0')!=std::wstring::npos)return {};
  namespace fs=std::filesystem;
  fs::path path(result);
  if(!path.is_absolute())return {};
  return path.lexically_normal().native();
 }catch(...){return {};}
}
std::unordered_map<std::wstring,Visual> queryVisuals(
   std::wstring const& helper,std::vector<std::wstring> const& input,
   DWORD timeoutMs,std::uint32_t requestedPixels) noexcept {
 try{
  if(input.empty()||input.size()>24)return {};
  std::vector<std::wstring> extensions;
  extensions.reserve(input.size());
  for(auto item:input){
   if(!safeExtension(item))return {};
   item=lowered(std::move(item));
   if(std::find(extensions.begin(),extensions.end(),item)!=extensions.end())
     return {};
   extensions.push_back(std::move(item));
  }
  return runVisualQuery(helper,L"--file-visuals",extensions,
                        timeoutMs,requestedPixels);
 }catch(...){return {};}
}
std::unordered_map<std::wstring,Visual> queryKnownFolderVisuals(
   std::wstring const& helper,std::vector<std::wstring> const& input,
   DWORD timeoutMs,std::uint32_t requestedPixels) noexcept {
 try{
  if(input.empty()||input.size()>6)return {};
  std::vector<std::wstring> keys;
  keys.reserve(input.size());
  for(auto item:input){
   item=lowered(std::move(item));
   if(!safeKnownFolderKey(item)||
      std::find(keys.begin(),keys.end(),item)!=keys.end())return {};
   keys.push_back(std::move(item));
  }
  return runVisualQuery(helper,L"--known-folder-visuals",keys,
                        timeoutMs,requestedPixels);
 }catch(...){return {};}
}

std::vector<Visual> queryShellItemVisuals(
   std::wstring const& helper,std::vector<std::wstring> const& parsingNames,
   std::atomic_bool const* cancel,DWORD inactivityMs,
   std::uint32_t requestedPixels) noexcept {
 std::vector<Visual> visuals;
 try{
  using namespace fxfile::visualwire;
  static std::mutex shellItemVisualMutex;
  std::lock_guard<std::mutex> lock(shellItemVisualMutex);
  namespace fs=std::filesystem;
  if(parsingNames.empty()||parsingNames.size()>kMaxItems||
     inactivityMs<200||inactivityMs>10000||
     requestedPixels<kMinPixels||requestedPixels>kMaxPixels||
     !fs::path(helper).is_absolute()||
     fs::path(helper).filename()!=L"FlyShellIsolationHelper.exe"||
     !fs::is_regular_file(fs::path(helper)))return {};
  std::vector<unsigned char> body;
  body.reserve(parsingNames.size()*64);
  auto append=[&](void const* source,std::size_t bytes)->bool{
   if(bytes>kMaxBodyBytes||body.size()>kMaxBodyBytes-bytes)return false;
   auto const* ptr=static_cast<unsigned char const*>(source);
   body.insert(body.end(),ptr,ptr+bytes);
   return true;
  };
  for(auto const& name:parsingNames){
   if(name.size()>kMaxNameUnits||
      name.find(L'\0')!=std::wstring::npos)return {};
   const auto units=static_cast<std::uint32_t>(name.size());
   if(!append(&units,sizeof(units))||
      !append(name.data(),name.size()*sizeof(wchar_t)))return {};
  }
  RequestHeader request{
      kMagic,kVersion,static_cast<std::uint32_t>(parsingNames.size()),
      requestedPixels,static_cast<std::uint32_t>(body.size()),
      checksum(body.data(),body.size())};

  SECURITY_ATTRIBUTES inheritable{sizeof(inheritable),nullptr,TRUE};
  HANDLE childInputRaw=nullptr,hostInputRaw=nullptr;
  HANDLE hostOutputRaw=nullptr,childOutputRaw=nullptr;
  if(!::CreatePipe(&childInputRaw,&hostInputRaw,&inheritable,131072))
    return {};
  UniqueHandle childInput(childInputRaw),hostInput(hostInputRaw);
  if(!::SetHandleInformation(hostInput.h,HANDLE_FLAG_INHERIT,0))return {};
  if(!::CreatePipe(&hostOutputRaw,&childOutputRaw,&inheritable,131072))
    return {};
  UniqueHandle hostOutput(hostOutputRaw),childOutput(childOutputRaw);
  if(!::SetHandleInformation(hostOutput.h,HANDLE_FLAG_INHERIT,0))return {};
  UniqueHandle childError(::CreateFileW(
      L"NUL",GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,
      &inheritable,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr));
  if(!childError.valid())return {};

  SIZE_T attributeBytes=0;
  ::InitializeProcThreadAttributeList(nullptr,1,0,&attributeBytes);
  if(!attributeBytes)return {};
  std::vector<unsigned char> attributeStorage(attributeBytes);
  auto* attributes=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(
      attributeStorage.data());
  if(!::InitializeProcThreadAttributeList(
      attributes,1,0,&attributeBytes))return {};
  const HANDLE inherited[]{
      childInput.h,childOutput.h,childError.h};
  if(!::UpdateProcThreadAttribute(
      attributes,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
      const_cast<HANDLE*>(inherited),sizeof(inherited),nullptr,nullptr)){
   ::DeleteProcThreadAttributeList(attributes);
   return {};
  }

  STARTUPINFOEXW startup{};
  startup.StartupInfo.cb=sizeof(startup);
  startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
  startup.StartupInfo.hStdInput=childInput.h;
  startup.StartupInfo.hStdOutput=childOutput.h;
  startup.StartupInfo.hStdError=childError.h;
  startup.lpAttributeList=attributes;
  std::wstring command=L"\""+helper+L"\" --shell-item-visuals";
  std::vector<wchar_t> mutableCommand(command.begin(),command.end());
  mutableCommand.push_back(0);
  PROCESS_INFORMATION info{};
  const BOOL created=::CreateProcessW(
      helper.c_str(),mutableCommand.data(),nullptr,nullptr,TRUE,
      CREATE_NO_WINDOW|CREATE_SUSPENDED|EXTENDED_STARTUPINFO_PRESENT,
      nullptr,fs::path(helper).parent_path().c_str(),
      &startup.StartupInfo,&info);
  ::DeleteProcThreadAttributeList(attributes);
  if(!created)return {};
  UniqueHandle process(info.hProcess),thread(info.hThread);
  UniqueHandle job(::CreateJobObjectW(nullptr,nullptr));
  if(!job.valid()){
   ::TerminateProcess(process.h,ERROR_NOT_ENOUGH_MEMORY);
   ::WaitForSingleObject(process.h,250);
   return {};
  }
  JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
  limits.BasicLimitInformation.LimitFlags=
      JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
  limits.BasicLimitInformation.ActiveProcessLimit=1;
  if(!::SetInformationJobObject(
       job.h,JobObjectExtendedLimitInformation,&limits,sizeof(limits))||
     !::AssignProcessToJobObject(job.h,process.h)){
   const auto error=::GetLastError();
   ::TerminateProcess(process.h,error);
   ::WaitForSingleObject(process.h,250);
   return {};
  }
  if(::ResumeThread(thread.h)==DWORD(-1)){
   ::TerminateJobObject(job.h,::GetLastError());
   ::WaitForSingleObject(process.h,250);
   return {};
  }
  thread.reset();
  childInput.reset();
  childOutput.reset();
  childError.reset();

  auto writeAll=[](HANDLE handle,void const* source,std::size_t bytes)->bool{
   auto const* ptr=static_cast<unsigned char const*>(source);
   while(bytes){
    const auto chunk=static_cast<DWORD>((std::min<std::size_t>)(bytes,65536));
    DWORD used=0;
    if(!::WriteFile(handle,ptr,chunk,&used,nullptr)||!used)return false;
    ptr+=used;bytes-=used;
   }
   return true;
  };
  if(!writeAll(hostInput.h,&request,sizeof(request))||
     (!body.empty()&&!writeAll(hostInput.h,body.data(),body.size()))){
   ::TerminateJobObject(job.h,ERROR_WRITE_FAULT);
   ::WaitForSingleObject(process.h,250);
   return {};
  }
  hostInput.reset();

  auto lastProgress=::GetTickCount64();
  auto stopOwned=[&](DWORD code){
   if(::WaitForSingleObject(process.h,0)!=WAIT_OBJECT_0){
    ::TerminateJobObject(job.h,code);
    ::WaitForSingleObject(process.h,250);
   }
  };
  auto readMonitored=[&](void* target,std::size_t bytes)->bool{
   auto* ptr=static_cast<unsigned char*>(target);
   while(bytes){
    if(cancel&&cancel->load()){
     stopOwned(ERROR_CANCELLED);
     return false;
    }
    DWORD available=0;
    if(!::PeekNamedPipe(hostOutput.h,nullptr,0,nullptr,&available,nullptr)){
     stopOwned(::GetLastError());
     return false;
    }
    if(available){
     const auto chunk=static_cast<DWORD>((std::min<std::size_t>)(
         bytes,(std::min<std::size_t>)(available,65536)));
     DWORD used=0;
     if(!::ReadFile(hostOutput.h,ptr,chunk,&used,nullptr)||!used){
      stopOwned(ERROR_READ_FAULT);
      return false;
     }
     ptr+=used;bytes-=used;
     lastProgress=::GetTickCount64();
     continue;
    }
    if(::WaitForSingleObject(process.h,0)==WAIT_OBJECT_0)return false;
    if(::GetTickCount64()-lastProgress>=inactivityMs){
     stopOwned(ERROR_TIMEOUT);
     return false;
    }
    ::Sleep(18);
   }
   return true;
  };

  visuals.resize(parsingNames.size());
  const auto expectedPixels=requestedPixels*requestedPixels*4u;
  for(std::size_t i=0;i<visuals.size();++i){
   ResultHeader result{};
   if(!readMonitored(&result,sizeof(result))||
      result.magic!=kMagic||result.version!=kVersion||
      result.index!=i||result.labelUnits>kMaxLabelUnits||
      (result.pixelBytes!=0&&result.pixelBytes!=expectedPixels)){
    stopOwned(ERROR_INVALID_DATA);
    return {};
   }
   if(result.labelUnits){
    visuals[i].label.resize(result.labelUnits);
    if(!readMonitored(
         visuals[i].label.data(),
         result.labelUnits*sizeof(wchar_t)))return {};
    if(std::any_of(visuals[i].label.begin(),visuals[i].label.end(),
       [](wchar_t ch){return ch<32||ch==127;})){
      stopOwned(ERROR_INVALID_DATA);
      return {};
    }
   }
   if(result.pixelBytes){
    visuals[i].bgra.resize(result.pixelBytes);
    if(!readMonitored(visuals[i].bgra.data(),result.pixelBytes))return {};
    visuals[i].width=requestedPixels;
    visuals[i].height=requestedPixels;
   }
  }
  if(::WaitForSingleObject(process.h,500)!=WAIT_OBJECT_0){
   stopOwned(ERROR_TIMEOUT);
   return {};
  }
  DWORD exitCode=ERROR_GEN_FAILURE;
  if(!::GetExitCodeProcess(process.h,&exitCode)||exitCode!=0)return {};
  return visuals;
 }catch(...){return {};}
}

std::unordered_map<std::wstring,std::wstring> query(
   std::wstring const& helper,std::vector<std::wstring> const& input,
   DWORD timeoutMs) noexcept {
 auto visuals=queryVisuals(helper,input,timeoutMs);
 std::unordered_map<std::wstring,std::wstring> names;
 for(auto& item:visuals)
  if(!item.second.label.empty())
   names.emplace(std::move(item.first),std::move(item.second.label));
 return names;
}
} // namespace fxfile::filetype
