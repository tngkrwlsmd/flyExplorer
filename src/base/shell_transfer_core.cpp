#define WIN32_LEAN_AND_MEAN
#include "shell_transfer_core.h"
#include "file_command_core.h"
#include <shellapi.h>
#include <shobjidl.h>
#include <shlobj.h>
#include <wrl/client.h>
#include <filesystem>
#include <algorithm>
#include <new>
#pragma comment(lib,"ole32.lib")
#pragma comment(lib,"shell32.lib")
namespace fxfile::shelltransfer {
using Microsoft::WRL::ComPtr;
namespace {
namespace fs=std::filesystem;
bool safeLocalFolder(fs::path const& folder) {
 if(!folder.is_absolute()||!folder.has_root_directory())return false;
 auto root=folder.root_path().native();
 if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
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
  if(request.sources.empty()||request.sources.size()>32||
     request.sourceParent.size()>32000||
     (request.kind!=Kind::Copy&&request.kind!=Kind::Move&&
      request.kind!=Kind::Recycle)||
     (request.collision!=Collision::Reject&&request.collision!=Collision::KeepBoth)){
   report.error=ERROR_INVALID_PARAMETER;return report;
  }
  if(request.kind==Kind::Recycle&&!request.recycleConfirmed){
   report.error=ERROR_CANCELLED;return report;
  }
  const auto parent=fs::path(request.sourceParent).lexically_normal();
  if(!safeLocalFolder(parent)){report.error=ERROR_INVALID_NAME;return report;}
  fs::path dest{};
  if(request.kind!=Kind::Recycle) {
   dest=fs::path(request.destination).lexically_normal();
   if(!safeLocalFolder(dest)){report.error=ERROR_INVALID_NAME;return report;}
  }
  std::vector<std::wstring> seen;
  for(auto const& source:request.sources){
   if(source.empty()||source.size()>32000){
    report.error=ERROR_INVALID_NAME;return report;
   }
   const auto item=fs::path(source).lexically_normal();
   if(!item.is_absolute()||!sameParent(item.parent_path(),parent)||
      !filecommand::validLeaf(item.filename().native())){
    report.error=ERROR_INVALID_NAME;return report;
   }
   const DWORD attrs=::GetFileAttributesW(item.c_str());
   if(attrs==INVALID_FILE_ATTRIBUTES){report.error=ERROR_FILE_NOT_FOUND;return report;}
   if(attrs&FILE_ATTRIBUTE_REPARSE_POINT){report.error=ERROR_NOT_SUPPORTED;return report;}
   const auto normalized=item.native();
   if(std::any_of(seen.begin(),seen.end(),[&](auto const& x){
      return ::CompareStringOrdinal(x.c_str(),-1,normalized.c_str(),-1,TRUE)==CSTR_EQUAL;
   })){report.error=ERROR_INVALID_PARAMETER;return report;}
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
  report.error=report.collisions.size()&&request.collision==Collision::Reject?
              ERROR_ALREADY_EXISTS:ERROR_SUCCESS;
 }catch(...){report.error=ERROR_INVALID_PARAMETER;}
 return report;
}
Report execute(Request const& task,Progress& progress) noexcept{
 Report report=validate(task);
 if(report.error!=ERROR_SUCCESS)return report;
 if(canceled(progress)){report.error=ERROR_CANCELLED;report.aborted=true;return report;}
 const HRESULT initialized=::CoInitializeEx(nullptr,
          COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(initialized)){report.error=code(initialized);return report;}
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
} // namespace fxfile::shelltransfer
