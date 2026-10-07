#define WIN32_LEAN_AND_MEAN
#include "shell_transfer_core.h"
#include "file_command_core.h"
#include <shellapi.h>
#include <shobjidl.h>
#include <shlobj.h>
#include <wrl/client.h>
#include <filesystem>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstring>
#include <limits>
#include <new>
#include <thread>
#include <vector>
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"shell32.lib")
namespace fxfile::shelltransfer {
using Microsoft::WRL::ComPtr;
bool supportsDriveType(Kind kind,UINT driveType) noexcept {
 switch(kind){
 case Kind::Copy:
 case Kind::Move:
  return driveType==DRIVE_FIXED||driveType==DRIVE_REMOVABLE||
         driveType==DRIVE_REMOTE;
 case Kind::Recycle:
  return driveType==DRIVE_FIXED||driveType==DRIVE_REMOVABLE;
 default:
  return false;
 }
}
bool transferDriveRoot(std::wstring const& value,
                       std::wstring& root) noexcept {
 root.clear();
 try{
  if(value.empty()||value.find(L'\0')!=std::wstring::npos)return false;
  // Standard UNC only. Extended/device namespaces remain closed so a network
  // provider cannot bypass the ordinary filesystem/reparse validation below.
  if(value.size()>=2&&value[0]==L'\\'&&value[1]==L'\\'){
   if(value.rfind(L"\\\\?\\",0)==0||value.rfind(L"\\\\.\\",0)==0)
    return false;
   const auto serverEnd=value.find(L'\\',2);
   if(serverEnd==std::wstring::npos||serverEnd==2)return false;
   const auto shareStart=serverEnd+1;
   if(shareStart>=value.size())return false;
   const auto shareEnd=value.find(L'\\',shareStart);
   const auto shareLength=(shareEnd==std::wstring::npos?value.size():shareEnd)-
                          shareStart;
   if(!shareLength)return false;
   root=value.substr(0,shareEnd==std::wstring::npos?value.size():shareEnd);
   root.push_back(L'\\');
   return true;
  }
  const std::filesystem::path path(value);
  root=path.root_path().native();
  return root.size()==3&&root[1]==L':'&&root[2]==L'\\';
 }catch(...){root.clear();return false;}
}
namespace {
namespace fs=std::filesystem;

bool safeFilesystemFolder(fs::path const& folder,Kind kind) {
 if(!folder.is_absolute()||!folder.has_root_directory())return false;
 std::wstring root;
 if(!transferDriveRoot(folder.native(),root)||
    !supportsDriveType(kind,::GetDriveTypeW(root.c_str())))return false;
 // Reject junctions/symlinks in EVERY existing path component, not only
 // the leaf; this also avoids accepting direct virtual Shell parsing names.
 fs::path part=folder.root_path();
 for(auto i=folder.begin();i!=folder.end();++i){
  if((*i)==folder.root_name()||(*i)==folder.root_directory())continue;
  part/=*i;
  const DWORD attributes=::GetFileAttributesW(part.c_str());
  if(attributes==INVALID_FILE_ATTRIBUTES||
     (attributes&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 }
 DWORD attrs=::GetFileAttributesW(folder.c_str());
 return attrs!=INVALID_FILE_ATTRIBUTES&&(attrs&FILE_ATTRIBUTE_DIRECTORY)&&
        !(attrs&FILE_ATTRIBUTE_REPARSE_POINT);
}
bool sameParent(fs::path const& lhs,fs::path const& rhs){
 auto a=lhs.lexically_normal().native();
 auto b=rhs.lexically_normal().native();
 return ::CompareStringOrdinal(a.c_str(),-1,b.c_str(),-1,TRUE)==CSTR_EQUAL;
}
bool descendant(fs::path const& ancestor,fs::path const& child){
 auto first=ancestor.begin(),last=child.begin();
 for(;first!=ancestor.end();++first,++last)
  if(last==child.end()||
     ::CompareStringOrdinal(first->c_str(),-1,last->c_str(),-1,TRUE)
          !=CSTR_EQUAL)return false;
 return true;
}
bool canceled(Progress& state){return state.cancel.load(std::memory_order_relaxed);}
class Sink final:public IFileOperationProgressSink {
 std::atomic_ulong refs_{1};
 Progress& state_;
 HRESULT alive() const{return state_.cancel.load()?E_ABORT:S_OK;}
public:
 explicit Sink(Progress& s):state_(s){}
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid,void**value) override{
  if(!value)return E_POINTER;
  *value=nullptr;
  if(IsEqualIID(iid,IID_IUnknown)||IsEqualIID(iid,IID_IFileOperationProgressSink)){
   *value=static_cast<IFileOperationProgressSink*>(this);AddRef();return S_OK;
  }
  return E_NOINTERFACE;
 }
 ULONG STDMETHODCALLTYPE AddRef() override{return ++refs_;}
 ULONG STDMETHODCALLTYPE Release() override{
  auto remaining=--refs_;
  if(!remaining)delete this;
  return remaining;
 }
 HRESULT STDMETHODCALLTYPE StartOperations() override{return alive();}
 HRESULT STDMETHODCALLTYPE FinishOperations(HRESULT) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PreRenameItem(DWORD,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostRenameItem(DWORD,IShellItem*,LPCWSTR,HRESULT,IShellItem*) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PreMoveItem(DWORD,IShellItem*,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostMoveItem(DWORD,IShellItem*,IShellItem*,LPCWSTR,HRESULT,IShellItem*) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PreCopyItem(DWORD,IShellItem*,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostCopyItem(DWORD,IShellItem*,IShellItem*,LPCWSTR,HRESULT,IShellItem*) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PreDeleteItem(DWORD,IShellItem*) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostDeleteItem(DWORD,IShellItem*,HRESULT,IShellItem*) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PreNewItem(DWORD,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostNewItem(DWORD,IShellItem*,LPCWSTR,LPCWSTR,DWORD,HRESULT,IShellItem*) override{return S_OK;}
 HRESULT STDMETHODCALLTYPE UpdateProgress(UINT total,UINT current) override{
  if(total)state_.percent.store(
      static_cast<std::uint32_t>((static_cast<std::uint64_t>(current)*100)/total));
  return alive();
 }
 HRESULT STDMETHODCALLTYPE ResetTimer() override{return S_OK;}
 HRESULT STDMETHODCALLTYPE PauseTimer() override{return S_OK;}
 HRESULT STDMETHODCALLTYPE ResumeTimer() override{return S_OK;}
};
DWORD code(HRESULT value) {
 if(SUCCEEDED(value))return ERROR_SUCCESS;
 return value==E_ABORT?ERROR_CANCELLED:
        HRESULT_FACILITY(value)==FACILITY_WIN32?HRESULT_CODE(value):
        static_cast<DWORD>(value);
}
}
Report validate(Request const& request) noexcept {
 Report report{};
 try {
  if(request.sources.empty()||request.sources.size()>kMaxItems||
     (request.kind!=Kind::Copy&&request.kind!=Kind::Move&&
      request.kind!=Kind::Recycle)||
     (request.collision!=Collision::Reject&&
      request.collision!=Collision::KeepBoth)||
     (request.sourceMode!=SourceMode::Filesystem&&
      request.sourceMode!=SourceMode::ShellProvider)){
   report.error=ERROR_INVALID_PARAMETER;return report;
  }
  if(request.sourceMode==SourceMode::ShellProvider){
   if(request.kind!=Kind::Copy||request.recycleConfirmed||
      request.sourceParent.empty()||
      request.sourceParent.size()>kMaxProviderParsingUnits||
      request.destination.empty()||request.destination.size()>32000){
    report.error=request.kind==Kind::Copy?
        ERROR_INVALID_PARAMETER:ERROR_NOT_SUPPORTED;
    return report;
   }
   const auto dest=fs::path(request.destination).lexically_normal();
   if(!safeFilesystemFolder(dest,Kind::Copy)){
    report.error=ERROR_INVALID_NAME;return report;
   }
   std::size_t sourceUnits=0;
   std::vector<std::wstring> seen;
   seen.reserve(request.sources.size());
   for(auto const& source:request.sources){
    if(source.empty()||source.size()>kMaxProviderParsingUnits||
       source.find(L'\0')!=std::wstring::npos||
       source.size()+1>kMaxSourcePathUnits-sourceUnits){
      report.error=ERROR_INVALID_NAME;return report;
    }
    sourceUnits+=source.size()+1;
    if(std::any_of(seen.begin(),seen.end(),[&](auto const& prior){
       return ::CompareStringOrdinal(
          prior.c_str(),-1,source.c_str(),-1,TRUE)==CSTR_EQUAL;
    })){
      report.error=ERROR_INVALID_PARAMETER;return report;
    }
    seen.push_back(source);
   }
   report.queued=static_cast<std::uint32_t>(request.sources.size());
   report.error=ERROR_SUCCESS;
   return report;
  }

  if(request.sourceParent.size()>32000){
   report.error=ERROR_INVALID_PARAMETER;return report;
  }
  if(request.kind==Kind::Recycle&&!request.recycleConfirmed){
   report.error=ERROR_CANCELLED;return report;
  }
  const auto parent=fs::path(request.sourceParent).lexically_normal();
  if(!safeFilesystemFolder(parent,request.kind)){
   report.error=ERROR_INVALID_NAME;return report;
  }
  fs::path dest{};
  if(request.kind!=Kind::Recycle) {
   dest=fs::path(request.destination).lexically_normal();
   if(!safeFilesystemFolder(dest,request.kind)){
    report.error=ERROR_INVALID_NAME;return report;
   }
  }
  std::vector<std::wstring> seen;
  std::size_t sourcePathUnits=0;
  for(auto const& source:request.sources){
   if(source.empty()||source.size()>32000||
      sourcePathUnits>kMaxSourcePathUnits-source.size()-1){
    report.error=ERROR_INVALID_NAME;return report;
   }
   sourcePathUnits+=source.size()+1;
   const auto item=fs::path(source).lexically_normal();
   if(!item.is_absolute()||!sameParent(item.parent_path(),parent)||
      !filecommand::validLeaf(item.filename().native())){
    report.error=ERROR_INVALID_NAME;return report;
   }
   const DWORD attrs=::GetFileAttributesW(item.c_str());
   if(attrs==INVALID_FILE_ATTRIBUTES){
    report.error=ERROR_FILE_NOT_FOUND;return report;
   }
   if(attrs&FILE_ATTRIBUTE_REPARSE_POINT){
    report.error=ERROR_NOT_SUPPORTED;return report;
   }
   const auto normalized=item.native();
   if(std::any_of(seen.begin(),seen.end(),[&](auto const& x){
      return ::CompareStringOrdinal(
         x.c_str(),-1,normalized.c_str(),-1,TRUE)==CSTR_EQUAL;
   })){
    report.error=ERROR_INVALID_PARAMETER;return report;
   }
   seen.push_back(normalized);
   if(request.kind==Kind::Recycle)continue;
   if(sameParent(parent,dest)&&request.kind==Kind::Move){
    report.error=ERROR_INVALID_PARAMETER;return report;
   }
   if((attrs&FILE_ATTRIBUTE_DIRECTORY)&&descendant(item,dest)){
    report.error=ERROR_INVALID_PARAMETER;return report;
   }
   auto target=dest/item.filename();
   if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES)
    report.collisions.push_back(target.native());
  }
  report.queued=static_cast<std::uint32_t>(request.sources.size());
  report.error=report.collisions.size()&&
               request.collision==Collision::Reject?
               ERROR_ALREADY_EXISTS:ERROR_SUCCESS;
 }catch(...){report.error=ERROR_INVALID_PARAMETER;}
 return report;
}

namespace {
Report validateProviderCopy(Request const& request) noexcept {
 Report report{};
 report.error=ERROR_INVALID_NAME;
 if(request.sourceMode!=SourceMode::ShellProvider||
    request.kind!=Kind::Copy)return report;
 PIDLIST_ABSOLUTE parent=nullptr;
 std::vector<PIDLIST_ABSOLUTE> children;
 auto cleanup=[&]{
  for(auto* item:children)if(item)::CoTaskMemFree(item);
  children.clear();
  if(parent){::CoTaskMemFree(parent);parent=nullptr;}
 };
 try{
  if(FAILED(::SHParseDisplayName(
       request.sourceParent.c_str(),nullptr,&parent,0,nullptr))||!parent){
   cleanup();return report;
  }
  ComPtr<IShellItem> parentItem;
  if(FAILED(::SHCreateItemFromIDList(
       parent,IID_PPV_ARGS(parentItem.GetAddressOf())))||!parentItem){
   cleanup();return report;
  }
  SFGAOF parentAttrs=0;
  if(FAILED(parentItem->GetAttributes(SFGAO_FOLDER,&parentAttrs))||
     !(parentAttrs&SFGAO_FOLDER)){
   cleanup();return report;
  }

  const auto destination=fs::path(request.destination).lexically_normal();
  children.reserve(request.sources.size());
  for(auto const& source:request.sources){
   PIDLIST_ABSOLUTE child=nullptr;
   if(FAILED(::SHParseDisplayName(
        source.c_str(),nullptr,&child,0,nullptr))||!child){
    if(child)::CoTaskMemFree(child);
    cleanup();return report;
   }
   if(!::ILIsParent(parent,child,TRUE)){
    ::CoTaskMemFree(child);cleanup();return report;
   }
   if(std::any_of(children.begin(),children.end(),
      [&](PIDLIST_ABSOLUTE prior){return ::ILIsEqual(prior,child)!=FALSE;})){
    ::CoTaskMemFree(child);
    report.error=ERROR_INVALID_PARAMETER;
    cleanup();return report;
   }

   ComPtr<IShellItem> item;
   if(FAILED(::SHCreateItemFromIDList(
        child,IID_PPV_ARGS(item.GetAddressOf())))||!item){
    ::CoTaskMemFree(child);cleanup();return report;
   }
   SFGAOF attrs=0;
   if(FAILED(item->GetAttributes(SFGAO_CANCOPY,&attrs))||
      !(attrs&SFGAO_CANCOPY)){
    ::CoTaskMemFree(child);
    report.error=ERROR_NOT_SUPPORTED;
    cleanup();return report;
   }
   PWSTR rawName=nullptr;
   if(FAILED(item->GetDisplayName(
        SIGDN_PARENTRELATIVEEDITING,&rawName))||!rawName){
    if(rawName)::CoTaskMemFree(rawName);
    ::CoTaskMemFree(child);cleanup();return report;
   }
   std::wstring leaf(rawName);
   ::CoTaskMemFree(rawName);
   if(!filecommand::validLeaf(leaf)){
    ::CoTaskMemFree(child);cleanup();return report;
   }
   auto target=destination/leaf;
   if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES)
    report.collisions.push_back(target.native());
   children.push_back(child);
  }
  report.queued=static_cast<std::uint32_t>(children.size());
  report.error=!report.collisions.empty()&&
               request.collision==Collision::Reject?
               ERROR_ALREADY_EXISTS:ERROR_SUCCESS;
 }catch(...){
  report.error=ERROR_INVALID_PARAMETER;
 }
 cleanup();
 return report;
}
} // namespace

Report execute(Request const& task,Progress& progress) noexcept{
 Report report=validate(task);
 if(report.error!=ERROR_SUCCESS)return report;
 if(canceled(progress)){report.error=ERROR_CANCELLED;report.aborted=true;return report;}
 const HRESULT initialized=::CoInitializeEx(nullptr,
          COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(initialized)){report.error=code(initialized);return report;}
 if(task.sourceMode==SourceMode::ShellProvider){
  report=validateProviderCopy(task);
  if(report.error!=ERROR_SUCCESS){
   ::CoUninitialize();
   return report;
  }
 }
 ComPtr<IFileOperation> operation;
 HRESULT hr=::CoCreateInstance(CLSID_FileOperation,nullptr,CLSCTX_INPROC_SERVER,
         IID_PPV_ARGS(operation.GetAddressOf()));
 if(SUCCEEDED(hr)){
  DWORD flags=FOF_SILENT|FOF_NOCONFIRMATION|FOF_NOERRORUI|
              FOFX_EARLYFAILURE|FOF_RENAMEONCOLLISION|
              FOFX_PRESERVEFILEEXTENSIONS;
  if(task.kind==Kind::Recycle)flags|=FOF_ALLOWUNDO|FOFX_RECYCLEONDELETE;
  hr=operation->SetOperationFlags(flags);
 }
 DWORD cookie=0;
 Sink* sink=nullptr;
 if(SUCCEEDED(hr)){
  sink=new(std::nothrow) Sink(progress);
  if(!sink)hr=E_OUTOFMEMORY;
  else hr=operation->Advise(sink,&cookie);
 }
 ComPtr<IShellItem> dest;
 if(SUCCEEDED(hr)&&task.kind!=Kind::Recycle)
  hr=::SHCreateItemFromParsingName(task.destination.c_str(),nullptr,
                                   IID_PPV_ARGS(dest.GetAddressOf()));
 if(SUCCEEDED(hr)){
  for(auto const& path:task.sources){
   if(canceled(progress)){hr=E_ABORT;break;}
   ComPtr<IShellItem> item;
   hr=::SHCreateItemFromParsingName(path.c_str(),nullptr,
                                    IID_PPV_ARGS(item.GetAddressOf()));
   if(FAILED(hr))break;
   if(task.kind==Kind::Copy)hr=operation->CopyItem(item.Get(),dest.Get(),nullptr,nullptr);
   else if(task.kind==Kind::Move)hr=operation->MoveItem(item.Get(),dest.Get(),nullptr,nullptr);
   else hr=operation->DeleteItem(item.Get(),nullptr);
   if(FAILED(hr))break;
  }
  if(SUCCEEDED(hr)&&!canceled(progress))hr=operation->PerformOperations();
  else if(SUCCEEDED(hr))hr=E_ABORT;
 }
 BOOL anyAborted=FALSE;
 if(operation&&SUCCEEDED(hr)){
  const auto probe=operation->GetAnyOperationsAborted(&anyAborted);
  if(FAILED(probe))hr=probe;
 }
 if(operation&&sink&&cookie)operation->Unadvise(cookie);
 if(sink)sink->Release();
 report.aborted=anyAborted||canceled(progress)||hr==E_ABORT;
 report.error=report.aborted?ERROR_CANCELLED:code(hr);
 if(report.error==ERROR_SUCCESS)progress.percent.store(100);
 ::CoUninitialize();
 return report;
}
namespace {
constexpr std::uint32_t kTransferWireMagic=0x31525446u; // FTR1
constexpr std::uint32_t kTransferWireVersion=2;
constexpr std::uint32_t kTransferFrameProgress=1;
constexpr std::uint32_t kTransferFrameComplete=2;
constexpr std::uint32_t kTransferFlagAborted=1u;
constexpr std::uint32_t kTransferFlagCollision=2u;
constexpr std::size_t kTransferWireMaxBody=4u*1024u*1024u;
constexpr DWORD kTransferPollMs=20;
constexpr DWORD kTransferCancelGraceMs=1500;
constexpr DWORD kTransferExitGraceMs=2000;

#pragma pack(push,1)
struct TransferWireRequest final {
 std::uint32_t magic=0;
 std::uint32_t version=0;
 std::uint32_t bodyBytes=0;
 std::uint32_t checksum=0;
 std::uint64_t cancelHandle=0;
};
struct TransferWireFrame final {
 std::uint32_t magic=0;
 std::uint32_t version=0;
 std::uint32_t type=0;
 std::uint32_t value=0;
 std::uint32_t queued=0;
 std::uint32_t flags=0;
};
#pragma pack(pop)
static_assert(sizeof(TransferWireRequest)==24,"transfer request wire ABI");
static_assert(sizeof(TransferWireFrame)==24,"transfer frame wire ABI");

struct Handle final {
 HANDLE value=nullptr;
 Handle()=default;
 explicit Handle(HANDLE handle):value(handle){}
 ~Handle(){reset();}
 Handle(Handle const&)=delete;
 Handle& operator=(Handle const&)=delete;
 void reset(HANDLE handle=nullptr){
  if(value&&value!=INVALID_HANDLE_VALUE)::CloseHandle(value);
  value=handle;
 }
 bool valid() const noexcept{return value&&value!=INVALID_HANDLE_VALUE;}
};

std::uint32_t transferChecksum(void const* data,std::size_t size) noexcept{
 auto const* bytes=static_cast<unsigned char const*>(data);
 std::uint32_t hash=2166136261u;
 for(std::size_t i=0;i<size;++i)hash=(hash^bytes[i])*16777619u;
 return hash;
}
bool writeAll(HANDLE handle,void const* data,std::size_t bytes) noexcept{
 auto const* current=static_cast<unsigned char const*>(data);
 while(bytes){
  const auto chunk=static_cast<DWORD>((std::min)(bytes,std::size_t{65536}));
  DWORD written=0;
  if(!::WriteFile(handle,current,chunk,&written,nullptr)||!written)return false;
  current+=written;bytes-=written;
 }
 return true;
}
bool readAll(HANDLE handle,void* data,std::size_t bytes) noexcept{
 auto* current=static_cast<unsigned char*>(data);
 while(bytes){
  const auto chunk=static_cast<DWORD>((std::min)(bytes,std::size_t{65536}));
  DWORD got=0;
  if(!::ReadFile(handle,current,chunk,&got,nullptr)||!got)return false;
  current+=got;bytes-=got;
 }
 return true;
}
bool appendBytes(std::vector<unsigned char>& body,
                 void const* data,std::size_t bytes){
 if(bytes>kTransferWireMaxBody||body.size()>kTransferWireMaxBody-bytes)
  return false;
 auto const* begin=static_cast<unsigned char const*>(data);
 body.insert(body.end(),begin,begin+bytes);
 return true;
}
bool appendU32(std::vector<unsigned char>& body,std::uint32_t value){
 return appendBytes(body,&value,sizeof(value));
}
bool appendString(std::vector<unsigned char>& body,
                  std::wstring const& value,std::size_t maximum){
 if(value.size()>maximum||
    !appendU32(body,static_cast<std::uint32_t>(value.size())))return false;
 return value.empty()||
        appendBytes(body,value.data(),value.size()*sizeof(wchar_t));
}
bool serializeTransfer(Request const& task,
                       TransferWireRequest& head,
                       std::vector<unsigned char>& body) noexcept{
 try{
  body.clear();
  if((task.kind!=Kind::Copy&&task.kind!=Kind::Move)||
     (task.sourceMode!=SourceMode::Filesystem&&
      task.sourceMode!=SourceMode::ShellProvider)||
     (task.sourceMode==SourceMode::ShellProvider&&task.kind!=Kind::Copy)||
     task.sources.empty()||task.sources.size()>kMaxItems||
     task.sourceParent.empty()||
     task.sourceParent.size()>(task.sourceMode==SourceMode::ShellProvider?
        kMaxProviderParsingUnits:std::size_t{32000})||
     task.destination.empty()||task.destination.size()>32000||
     (task.collision!=Collision::Reject&&task.collision!=Collision::KeepBoth))
   return false;
  const auto sourceLimit=task.sourceMode==SourceMode::ShellProvider?
      kMaxProviderParsingUnits:std::size_t{32000};
  std::size_t sourceUnits=0;
  for(auto const& source:task.sources){
   if(source.empty()||source.size()>sourceLimit||
      source.size()+1>kMaxSourcePathUnits-sourceUnits)return false;
   sourceUnits+=source.size()+1;
  }
  if(!appendU32(body,static_cast<std::uint32_t>(task.sourceMode))||
     !appendU32(body,static_cast<std::uint32_t>(task.kind))||
     !appendU32(body,static_cast<std::uint32_t>(task.collision))||
     !appendString(body,task.sourceParent,sourceLimit)||
     !appendString(body,task.destination,32000)||
     !appendU32(body,static_cast<std::uint32_t>(task.sources.size())))
   return false;
  for(auto const& source:task.sources)
   if(!appendString(body,source,32000))return false;
  head.magic=kTransferWireMagic;
  head.version=kTransferWireVersion;
  head.bodyBytes=static_cast<std::uint32_t>(body.size());
  head.checksum=transferChecksum(body.data(),body.size());
  return true;
 }catch(...){body.clear();return false;}
}
struct WireReader final {
 std::vector<unsigned char> const& body;
 std::size_t offset=0;
 bool valid=true;
 std::uint32_t u32(){
  if(!valid||body.size()-offset<sizeof(std::uint32_t)){
   valid=false;return 0;
  }
  std::uint32_t value=0;
  std::memcpy(&value,body.data()+offset,sizeof(value));
  offset+=sizeof(value);
  return value;
 }
 std::wstring string(std::size_t maximum){
  const auto units=u32();
  if(!valid||units>maximum||
     static_cast<std::size_t>(units)>(body.size()-offset)/sizeof(wchar_t)){
   valid=false;return {};
  }
  std::wstring value(units,L'\0');
  if(units)std::memcpy(value.data(),body.data()+offset,
                       static_cast<std::size_t>(units)*sizeof(wchar_t));
  offset+=static_cast<std::size_t>(units)*sizeof(wchar_t);
  if(value.find(L'\0')!=std::wstring::npos)valid=false;
  return value;
 }
};
bool parseTransfer(std::vector<unsigned char> const& body,
                   Request& task) noexcept{
 try{
  WireReader reader{body};
  const auto sourceMode=reader.u32();
  const auto kind=reader.u32();
  const auto collision=reader.u32();
  if(sourceMode>static_cast<std::uint32_t>(SourceMode::ShellProvider)||
     kind>static_cast<std::uint32_t>(Kind::Move)||
     collision>static_cast<std::uint32_t>(Collision::KeepBoth))
   return false;
  task=Request{};
  task.sourceMode=static_cast<SourceMode>(sourceMode);
  task.kind=static_cast<Kind>(kind);
  task.collision=static_cast<Collision>(collision);
  if((task.kind!=Kind::Copy&&task.kind!=Kind::Move)||
     (task.sourceMode==SourceMode::ShellProvider&&task.kind!=Kind::Copy))
   return false;
  const auto sourceLimit=task.sourceMode==SourceMode::ShellProvider?
      kMaxProviderParsingUnits:std::size_t{32000};
  task.sourceParent=reader.string(sourceLimit);
  task.destination=reader.string(32000);
  const auto count=reader.u32();
  if(!reader.valid||task.sourceParent.empty()||task.destination.empty()||
     !count||count>kMaxItems)return false;
  std::size_t sourceUnits=0;
  task.sources.reserve(count);
  for(std::uint32_t i=0;i<count;++i){
   auto source=reader.string(sourceLimit);
   if(!reader.valid||source.empty()||
      source.size()+1>kMaxSourcePathUnits-sourceUnits)return false;
   sourceUnits+=source.size()+1;
   task.sources.push_back(std::move(source));
  }
  return reader.valid&&reader.offset==body.size();
 }catch(...){task=Request{};return false;}
}
bool transferHelperPath(std::wstring& result) noexcept{
 result.clear();
 try{
  std::array<wchar_t,32768> module{};
  const DWORD length=::GetModuleFileNameW(
      nullptr,module.data(),static_cast<DWORD>(module.size()));
  if(!length||length>=module.size())return false;
  auto helper=fs::path(std::wstring(module.data(),length)).parent_path()/
              L"FlyShellIsolationHelper.exe";
  const auto flags=::GetFileAttributesW(helper.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||(flags&FILE_ATTRIBUTE_DIRECTORY))
   return false;
  result=helper.native();
  return true;
 }catch(...){return false;}
}
Report canceledReport() noexcept{
 Report result{};
 result.error=ERROR_CANCELLED;
 result.aborted=true;
 return result;
}
} // namespace

Report executeIsolated(Request const& task,Progress& progress) noexcept{
 Report result{};
 result.error=ERROR_INVALID_PARAMETER;
 try{
  if(task.kind!=Kind::Copy&&task.kind!=Kind::Move)return result;
  if(progress.cancel.load(std::memory_order_relaxed))return canceledReport();

  TransferWireRequest request{};
  std::vector<unsigned char> body;
  if(!serializeTransfer(task,request,body))return result;

  std::wstring helper;
  if(!transferHelperPath(helper)){
   result.error=ERROR_FILE_NOT_FOUND;
   return result;
  }

  SECURITY_ATTRIBUTES inheritable{
      sizeof(SECURITY_ATTRIBUTES),nullptr,TRUE};
  HANDLE childInputRaw=nullptr,hostInputRaw=nullptr;
  HANDLE hostOutputRaw=nullptr,childOutputRaw=nullptr;
  if(!::CreatePipe(&childInputRaw,&hostInputRaw,&inheritable,131072)){
   result.error=::GetLastError();return result;
  }
  Handle childInput(childInputRaw),hostInput(hostInputRaw);
  if(!::SetHandleInformation(hostInput.value,HANDLE_FLAG_INHERIT,0)){
   result.error=::GetLastError();return result;
  }
  if(!::CreatePipe(&hostOutputRaw,&childOutputRaw,&inheritable,131072)){
   result.error=::GetLastError();return result;
  }
  Handle hostOutput(hostOutputRaw),childOutput(childOutputRaw);
  if(!::SetHandleInformation(hostOutput.value,HANDLE_FLAG_INHERIT,0)){
   result.error=::GetLastError();return result;
  }
  Handle childError(::CreateFileW(
      L"NUL",GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,
      &inheritable,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr));
  if(!childError.valid()){
   result.error=::GetLastError();return result;
  }
  Handle cancelEvent(::CreateEventW(&inheritable,TRUE,FALSE,nullptr));
  if(!cancelEvent.valid()){
   result.error=::GetLastError();return result;
  }
  request.cancelHandle=static_cast<std::uint64_t>(
      reinterpret_cast<std::uintptr_t>(cancelEvent.value));

  SIZE_T attributeBytes=0;
  ::InitializeProcThreadAttributeList(nullptr,1,0,&attributeBytes);
  if(!attributeBytes){
   result.error=ERROR_INVALID_PARAMETER;return result;
  }
  std::vector<unsigned char> attributeStorage(attributeBytes);
  auto* attributes=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(
      attributeStorage.data());
  if(!::InitializeProcThreadAttributeList(
      attributes,1,0,&attributeBytes)){
   result.error=::GetLastError();return result;
  }
  const HANDLE inherited[]={
      childInput.value,childOutput.value,childError.value,cancelEvent.value};
  const bool handlesReady=::UpdateProcThreadAttribute(
      attributes,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
      const_cast<HANDLE*>(inherited),sizeof(inherited),nullptr,nullptr)!=FALSE;
  if(!handlesReady){
   result.error=::GetLastError();
   ::DeleteProcThreadAttributeList(attributes);
   return result;
  }

  STARTUPINFOEXW startup{};
  startup.StartupInfo.cb=sizeof(startup);
  startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
  startup.StartupInfo.hStdInput=childInput.value;
  startup.StartupInfo.hStdOutput=childOutput.value;
  startup.StartupInfo.hStdError=childError.value;
  startup.lpAttributeList=attributes;
  std::wstring command=L"\""+helper+L"\" --file-transfer";
  std::vector<wchar_t> mutableCommand(command.begin(),command.end());
  mutableCommand.push_back(0);
  PROCESS_INFORMATION info{};
  const BOOL created=::CreateProcessW(
      helper.c_str(),mutableCommand.data(),nullptr,nullptr,TRUE,
      CREATE_NO_WINDOW|CREATE_SUSPENDED|EXTENDED_STARTUPINFO_PRESENT,
      nullptr,fs::path(helper).parent_path().c_str(),
      &startup.StartupInfo,&info);
  const DWORD createError=::GetLastError();
  ::DeleteProcThreadAttributeList(attributes);
  if(!created){
   result.error=createError;return result;
  }
  Handle process(info.hProcess),thread(info.hThread);
  Handle job(::CreateJobObjectW(nullptr,nullptr));
  if(!job.valid()){
   result.error=::GetLastError();
   ::TerminateProcess(process.value,result.error);
   ::WaitForSingleObject(process.value,kTransferExitGraceMs);
   return result;
  }
  JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
  limits.BasicLimitInformation.LimitFlags=
      JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
  limits.BasicLimitInformation.ActiveProcessLimit=1;
  if(!::SetInformationJobObject(
         job.value,JobObjectExtendedLimitInformation,&limits,sizeof(limits))||
     !::AssignProcessToJobObject(job.value,process.value)){
   result.error=::GetLastError();
   ::TerminateProcess(process.value,result.error);
   ::WaitForSingleObject(process.value,kTransferExitGraceMs);
   return result;
  }
  if(::ResumeThread(thread.value)==DWORD(-1)){
   result.error=::GetLastError();
   ::TerminateJobObject(job.value,result.error);
   ::WaitForSingleObject(process.value,kTransferExitGraceMs);
   return result;
  }
  thread.reset();
  childInput.reset();
  childOutput.reset();
  childError.reset();

  if(!writeAll(hostInput.value,&request,sizeof(request))||
     (!body.empty()&&!writeAll(hostInput.value,body.data(),body.size()))){
   result.error=ERROR_WRITE_FAULT;
   ::TerminateJobObject(job.value,result.error);
   ::WaitForSingleObject(process.value,kTransferExitGraceMs);
   return result;
  }
  hostInput.reset();

  bool cancelSignaled=false;
  ULONGLONG cancelStarted=0;
  bool completed=false;
  for(;;){
   if(progress.cancel.load(std::memory_order_relaxed)&&!cancelSignaled){
    ::SetEvent(cancelEvent.value);
    cancelStarted=::GetTickCount64();
    cancelSignaled=true;
   }
   if(cancelSignaled&&
      ::GetTickCount64()-cancelStarted>=kTransferCancelGraceMs&&
      ::WaitForSingleObject(process.value,0)!=WAIT_OBJECT_0){
    ::TerminateJobObject(job.value,ERROR_CANCELLED);
    ::WaitForSingleObject(process.value,kTransferExitGraceMs);
    return canceledReport();
   }

   DWORD available=0;
   if(!::PeekNamedPipe(hostOutput.value,nullptr,0,nullptr,&available,nullptr)){
    if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0)break;
    result.error=::GetLastError();
    ::TerminateJobObject(job.value,result.error);
    ::WaitForSingleObject(process.value,kTransferExitGraceMs);
    return result;
   }
   if(available>=sizeof(TransferWireFrame)){
    TransferWireFrame frame{};
    if(!readAll(hostOutput.value,&frame,sizeof(frame))||
       frame.magic!=kTransferWireMagic||
       frame.version!=kTransferWireVersion){
     result.error=ERROR_INVALID_DATA;
     ::TerminateJobObject(job.value,result.error);
     ::WaitForSingleObject(process.value,kTransferExitGraceMs);
     return result;
    }
    if(frame.type==kTransferFrameProgress){
     if(frame.value>100||frame.queued||frame.flags){
      result.error=ERROR_INVALID_DATA;
      ::TerminateJobObject(job.value,result.error);
      ::WaitForSingleObject(process.value,kTransferExitGraceMs);
      return result;
     }
     progress.percent.store(frame.value,std::memory_order_relaxed);
    }else if(frame.type==kTransferFrameComplete){
     result.error=frame.value;
     result.queued=frame.queued;
     result.aborted=(frame.flags&kTransferFlagAborted)!=0;
     if(frame.flags&~(kTransferFlagAborted|kTransferFlagCollision)){
      result.error=ERROR_INVALID_DATA;
      ::TerminateJobObject(job.value,result.error);
      ::WaitForSingleObject(process.value,kTransferExitGraceMs);
      return result;
     }
     if(frame.flags&kTransferFlagCollision)result.collisions.emplace_back();
     completed=true;
     break;
    }else{
     result.error=ERROR_INVALID_DATA;
     ::TerminateJobObject(job.value,result.error);
     ::WaitForSingleObject(process.value,kTransferExitGraceMs);
     return result;
    }
   }else if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0){
    break;
   }else{
    ::Sleep(kTransferPollMs);
   }
  }

  if(!completed){
   if(cancelSignaled)return canceledReport();
   result.error=ERROR_GEN_FAILURE;
   return result;
  }
  const auto exited=::WaitForSingleObject(process.value,kTransferExitGraceMs);
  if(exited!=WAIT_OBJECT_0){
   ::TerminateJobObject(job.value,ERROR_TIMEOUT);
   ::WaitForSingleObject(process.value,kTransferExitGraceMs);
   result.error=ERROR_TIMEOUT;
   result.aborted=true;
   return result;
  }
  DWORD exitCode=ERROR_GEN_FAILURE;
  if(!::GetExitCodeProcess(process.value,&exitCode)||exitCode!=0){
   if(result.error==ERROR_SUCCESS)result.error=ERROR_GEN_FAILURE;
   return result;
  }
  if(result.error==ERROR_SUCCESS)
   progress.percent.store(100,std::memory_order_relaxed);
  return result;
 }catch(...){
  result.error=ERROR_INVALID_PARAMETER;
  return result;
 }
}

int runIsolatedHelper(HANDLE input,HANDLE output) noexcept{
 try{
  if(!input||input==INVALID_HANDLE_VALUE||
     !output||output==INVALID_HANDLE_VALUE)return 70;
  TransferWireRequest head{};
  if(!readAll(input,&head,sizeof(head))||
     head.magic!=kTransferWireMagic||
     head.version!=kTransferWireVersion||
     head.bodyBytes>kTransferWireMaxBody)return 71;
  std::vector<unsigned char> body(head.bodyBytes);
  if(head.bodyBytes&&!readAll(input,body.data(),body.size()))return 72;
  if(transferChecksum(body.data(),body.size())!=head.checksum)return 73;
  Request task{};
  if(!parseTransfer(body,task))return 74;
  auto cancelEvent=reinterpret_cast<HANDLE>(
      static_cast<std::uintptr_t>(head.cancelHandle));
  if(!cancelEvent||cancelEvent==INVALID_HANDLE_VALUE||
     ::WaitForSingleObject(cancelEvent,0)==WAIT_FAILED)return 75;

  Progress progress;
  std::atomic_bool done{false};
  std::atomic_bool wireOk{true};
  std::thread reporter([&]{
   std::uint32_t last=(std::numeric_limits<std::uint32_t>::max)();
   while(!done.load(std::memory_order_acquire)){
    if(::WaitForSingleObject(cancelEvent,0)==WAIT_OBJECT_0)
     progress.cancel.store(true,std::memory_order_relaxed);
    const auto current=(std::min)(
        progress.percent.load(std::memory_order_relaxed),100u);
    if(current!=last){
     TransferWireFrame frame{
       kTransferWireMagic,kTransferWireVersion,kTransferFrameProgress,
       current,0,0};
     if(!writeAll(output,&frame,sizeof(frame))){
      wireOk.store(false,std::memory_order_relaxed);
      progress.cancel.store(true,std::memory_order_relaxed);
      break;
     }
     last=current;
    }
    ::Sleep(kTransferPollMs);
   }
   if(::WaitForSingleObject(cancelEvent,0)==WAIT_OBJECT_0)
    progress.cancel.store(true,std::memory_order_relaxed);
  });
  const auto report=execute(task,progress);
  done.store(true,std::memory_order_release);
  reporter.join();
  if(!wireOk.load(std::memory_order_relaxed))return 76;
  TransferWireFrame frame{
    kTransferWireMagic,kTransferWireVersion,kTransferFrameComplete,
    report.error,report.queued,
    (report.aborted?kTransferFlagAborted:0u)|
    (!report.collisions.empty()?kTransferFlagCollision:0u)};
  if(!writeAll(output,&frame,sizeof(frame)))return 77;
  return 0;
 }catch(...){return 78;}
}

} // namespace fxfile::shelltransfer
