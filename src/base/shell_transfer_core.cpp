#define WIN32_LEAN_AND_MEAN
#include "shell_transfer_core.h"
#include "file_command_core.h"
#include "stage_receipt_core.h"
#include <shellapi.h>
#include <shobjidl.h>
#include <shlobj.h>
#include <wrl/client.h>
#include <filesystem>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstring>
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
#include <cstdio>
#endif
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
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
using DirectoryRenameProbe=void (*)(std::wstring const&) noexcept;
std::atomic<DirectoryRenameProbe> g_directoryRenameProbe{nullptr};
#endif

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
bool validPidlBlob(std::vector<unsigned char> const& bytes) noexcept{
 if(bytes.size()<sizeof(USHORT)||bytes.size()>kMaxProviderPidlBytes)return false;
 std::size_t offset=0;
 while(offset+sizeof(USHORT)<=bytes.size()){
  USHORT cb=0;
  std::memcpy(&cb,bytes.data()+offset,sizeof(cb));
  if(cb==0)return offset+sizeof(USHORT)==bytes.size();
  if(cb<sizeof(USHORT)||offset+cb>bytes.size())return false;
  offset+=cb;
 }
 return false;
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
 std::atomic<HRESULT> firstFailure_{S_OK};
 HRESULT completed(HRESULT operationResult) noexcept {
  if(FAILED(operationResult)){
   HRESULT none=S_OK;
   firstFailure_.compare_exchange_strong(none,operationResult);
  }
  // A failed per-item callback must stop the remainder of the batch,
  // rather than allow the Shell to silently claim aggregate success.
  return FAILED(operationResult)?operationResult:S_OK;
 }
 HRESULT alive() const{return state_.cancel.load()?E_ABORT:S_OK;}
public:
 explicit Sink(Progress& s):state_(s){}
 HRESULT firstFailure() const noexcept{return firstFailure_.load();}
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
 HRESULT STDMETHODCALLTYPE FinishOperations(HRESULT hr) override{return completed(hr);}
 HRESULT STDMETHODCALLTYPE PreRenameItem(DWORD,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostRenameItem(DWORD,IShellItem*,LPCWSTR,HRESULT hr,IShellItem*) override{return completed(hr);}
 HRESULT STDMETHODCALLTYPE PreMoveItem(DWORD,IShellItem*,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostMoveItem(DWORD,IShellItem*,IShellItem*,LPCWSTR,HRESULT hr,IShellItem*) override{return completed(hr);}
 HRESULT STDMETHODCALLTYPE PreCopyItem(DWORD,IShellItem*,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostCopyItem(DWORD,IShellItem*,IShellItem*,LPCWSTR,HRESULT hr,IShellItem*) override{return completed(hr);}
 HRESULT STDMETHODCALLTYPE PreDeleteItem(DWORD,IShellItem*) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostDeleteItem(DWORD,IShellItem*,HRESULT hr,IShellItem*) override{return completed(hr);}
 HRESULT STDMETHODCALLTYPE PreNewItem(DWORD,IShellItem*,LPCWSTR) override{return alive();}
 HRESULT STDMETHODCALLTYPE PostNewItem(DWORD,IShellItem*,LPCWSTR,LPCWSTR,DWORD,HRESULT hr,IShellItem*) override{return completed(hr);}
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
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
// This setter exists only in the M22 native fixture binary.
void setDirectoryRenameProbeForTest(
    void (*probe)(std::wstring const&) noexcept) noexcept {
 g_directoryRenameProbe.store(probe,std::memory_order_release);
}
#endif
// Read-only identity evidence for an explicitly supplied stage path.
// A file ID is NOT proof of who created the stage; deletion is forbidden.
bool sameStageFile(StageFileIdentity const& a,
                   StageFileIdentity const& b) noexcept {
 const bool present=std::any_of(a.fileId.begin(),a.fileId.end(),
                               [](unsigned char x){return x!=0;});
 return present&&a.volumeSerial==b.volumeSerial&&a.fileId==b.fileId;
}
bool inspectStageFile(std::wstring const& exactPath,
                      StageFileIdentity& identity) noexcept {
 identity={};
 try {
  if(exactPath.empty()||exactPath.size()>32000||
     exactPath.find(L'\0')!=std::wstring::npos)return false;
  const fs::path path(exactPath);
  if(!path.is_absolute()||path.lexically_normal()!=path||
     path.native()!=exactPath)return false;
  const std::wstring leaf=path.filename().native();
  const std::wstring prefix=L".flyExplorer-copy-";
  const std::wstring suffix=L".partial";
  if(leaf.size()!=prefix.size()+38+suffix.size()||
     leaf.compare(0,prefix.size(),prefix)!=0||
     leaf.compare(leaf.size()-suffix.size(),suffix.size(),suffix)!=0)
   return false;
  const std::wstring token=leaf.substr(prefix.size(),38);
  GUID parsed{};
  wchar_t canonical[40]{};
  if(FAILED(::CLSIDFromString(token.c_str(),&parsed))||
     !::StringFromGUID2(parsed,canonical,40)||
     ::CompareStringOrdinal(token.c_str(),-1,canonical,-1,TRUE)!=CSTR_EQUAL)
   return false;
  std::wstring driveRoot;
  if(!transferDriveRoot(exactPath,driveRoot)||
     ::GetDriveTypeW(driveRoot.c_str())!=DRIVE_FIXED||
     !safeFilesystemFolder(path.parent_path(),Kind::Copy))return false;
  // OPEN_REPARSE_POINT prevents following an untrusted stage leaf.
  // Read attributes only; no DELETE, rename or write access is requested.
  const HANDLE handle=::CreateFileW(
      exactPath.c_str(),FILE_READ_ATTRIBUTES,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
      OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(handle==INVALID_HANDLE_VALUE)return false;
  BY_HANDLE_FILE_INFORMATION attributes{};
  FILE_ID_INFO file{};
  const bool inspected=::GetFileInformationByHandle(handle,&attributes)!=FALSE&&
      ::GetFileInformationByHandleEx(handle,FileIdInfo,&file,sizeof(file))!=FALSE;
  ::CloseHandle(handle);
  if(!inspected||attributes.nNumberOfLinks!=1||
     (attributes.dwFileAttributes&
         (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
   return false;
  const bool validId=std::any_of(
      std::begin(file.FileId.Identifier),std::end(file.FileId.Identifier),
      [](unsigned char byte){return byte!=0;});
  if(!validId)return false;
  identity.volumeSerial=file.VolumeSerialNumber;
  std::copy(std::begin(file.FileId.Identifier),
            std::end(file.FileId.Identifier),identity.fileId.begin());
  return true;
 }catch(...){identity={};return false;}
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
      request.sourceMode!=SourceMode::ShellProvider)||
     (request.destinationMode!=DestinationMode::Filesystem&&
      request.destinationMode!=DestinationMode::ShellProvider)){
   report.error=ERROR_INVALID_PARAMETER;return report;
  }
  if(request.destinationMode==DestinationMode::ShellProvider&&
     (request.sourceMode!=SourceMode::Filesystem||
      request.kind!=Kind::Copy||request.recycleConfirmed||
      !validPidlBlob(request.destinationPidl)||
      request.destination.empty()||
      request.destination.size()>kMaxProviderParsingUnits)){
   report.error=ERROR_NOT_SUPPORTED;return report;
  }
  if(request.destinationMode==DestinationMode::Filesystem&&
     !request.destinationPidl.empty()){
   report.error=ERROR_INVALID_PARAMETER;return report;
  }
  if(request.sourceMode==SourceMode::ShellProvider){
   if(request.kind!=Kind::Copy||request.recycleConfirmed||
      request.sourceParent.empty()||
      request.sourceParent.size()>kMaxProviderParsingUnits||
      request.destination.empty()||request.destination.size()>32000||
      !validPidlBlob(request.sourceParentPidl)||
      request.sourcePidls.size()!=request.sources.size()){
    report.error=request.kind==Kind::Copy?
        ERROR_INVALID_PARAMETER:ERROR_NOT_SUPPORTED;
    return report;
   }
   const auto dest=fs::path(request.destination).lexically_normal();
   if(!safeFilesystemFolder(dest,Kind::Copy)){
    report.error=ERROR_INVALID_NAME;return report;
   }
   std::size_t sourceUnits=0;
   std::size_t pidlBytes=request.sourceParentPidl.size();
   std::vector<std::wstring> seen;
   seen.reserve(request.sources.size());
   for(std::size_t i=0;i<request.sources.size();++i){
    auto const& source=request.sources[i];
    auto const& pidl=request.sourcePidls[i];
    if(source.empty()||source.size()>kMaxProviderParsingUnits||
       source.find(L'\0')!=std::wstring::npos||
       source.size()+1>kMaxSourcePathUnits-sourceUnits||
       !validPidlBlob(pidl)||
       pidl.size()>kMaxProviderPidlBytesTotal-pidlBytes){
      report.error=ERROR_INVALID_NAME;return report;
    }
    sourceUnits+=source.size()+1;
    pidlBytes+=pidl.size();
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

  if(request.sourceParent.size()>32000||
     !request.sourceParentPidl.empty()||!request.sourcePidls.empty()){
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
  if(request.kind!=Kind::Recycle&&
     request.destinationMode==DestinationMode::Filesystem) {
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
   if(request.destinationMode==DestinationMode::Filesystem&&
      sameParent(parent,dest)&&request.kind==Kind::Move){
    report.error=ERROR_INVALID_PARAMETER;return report;
   }
   if(request.destinationMode==DestinationMode::Filesystem&&
      (attrs&FILE_ATTRIBUTE_DIRECTORY)&&descendant(item,dest)){
    report.error=ERROR_INVALID_PARAMETER;return report;
   }
   if(request.destinationMode==DestinationMode::Filesystem){
    auto target=dest/item.filename();
    if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES)
     report.collisions.push_back(target.native());
   }
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
    request.kind!=Kind::Copy||
    !validPidlBlob(request.sourceParentPidl)||
    request.sourcePidls.size()!=request.sources.size())return report;
 try{
  auto parent=reinterpret_cast<PCIDLIST_ABSOLUTE>(
      request.sourceParentPidl.data());
  ComPtr<IShellItem> parentItem;
  if(FAILED(::SHCreateItemFromIDList(
       parent,IID_PPV_ARGS(parentItem.GetAddressOf())))||!parentItem)
   return report;
  SFGAOF parentAttrs=0;
  if(FAILED(parentItem->GetAttributes(SFGAO_FOLDER,&parentAttrs))||
     !(parentAttrs&SFGAO_FOLDER))return report;

  const auto destination=fs::path(request.destination).lexically_normal();
  std::vector<PCIDLIST_ABSOLUTE> seen;
  seen.reserve(request.sourcePidls.size());
  for(auto const& sourceBytes:request.sourcePidls){
   if(!validPidlBlob(sourceBytes))return report;
   auto child=reinterpret_cast<PCIDLIST_ABSOLUTE>(sourceBytes.data());
   if(!::ILIsParent(parent,child,TRUE))return report;
   if(std::any_of(seen.begin(),seen.end(),
      [&](PCIDLIST_ABSOLUTE prior){return ::ILIsEqual(prior,child)!=FALSE;})){
    report.error=ERROR_INVALID_PARAMETER;
    return report;
   }

   ComPtr<IShellItem> item;
   if(FAILED(::SHCreateItemFromIDList(
        child,IID_PPV_ARGS(item.GetAddressOf())))||!item)return report;
   SFGAOF attrs=0;
   if(FAILED(item->GetAttributes(SFGAO_CANCOPY,&attrs))||
      !(attrs&SFGAO_CANCOPY)){
    report.error=ERROR_NOT_SUPPORTED;
    return report;
   }
   PWSTR rawName=nullptr;
   if(FAILED(item->GetDisplayName(
        SIGDN_PARENTRELATIVEEDITING,&rawName))||!rawName){
    if(rawName)::CoTaskMemFree(rawName);
    return report;
   }
   std::wstring leaf(rawName);
   ::CoTaskMemFree(rawName);
   if(!filecommand::validLeaf(leaf))return report;
   auto target=destination/leaf;
   if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES)
    report.collisions.push_back(target.native());
   seen.push_back(child);
  }
  report.queued=static_cast<std::uint32_t>(seen.size());
  report.error=!report.collisions.empty()&&
               request.collision==Collision::Reject?
               ERROR_ALREADY_EXISTS:ERROR_SUCCESS;
 }catch(...){
  report.error=ERROR_INVALID_PARAMETER;
 }
 return report;
}
} // namespace

namespace {
// Copy-in is initially allowed only for the Windows Pictures Library. The
// PIDL must match the system Known Folder; a display name is not authority.
Report verifyPicturesLibraryCopyIn(
    Request const& request,ComPtr<IShellItem>& concrete) noexcept {
 Report report{};report.error=ERROR_NOT_SUPPORTED;
 if(request.destinationMode!=DestinationMode::ShellProvider||
    request.sourceMode!=SourceMode::Filesystem||request.kind!=Kind::Copy||
    !validPidlBlob(request.destinationPidl))return report;
 try{
  PIDLIST_ABSOLUTE known=nullptr;
  if(FAILED(::SHGetKnownFolderIDList(
       FOLDERID_PicturesLibrary,0,nullptr,&known))||!known)return report;
  auto target=reinterpret_cast<PCIDLIST_ABSOLUTE>(
      request.destinationPidl.data());
  bool exact=::ILIsEqual(known,target)!=FALSE;
  ::CoTaskMemFree(known);
  if(!exact)return report;
  ComPtr<IShellItem> libraryItem;
  if(FAILED(::SHCreateItemFromIDList(
       target,IID_PPV_ARGS(libraryItem.GetAddressOf())))||!libraryItem)
   return report;
  SFGAOF attr=0;
  if(FAILED(libraryItem->GetAttributes(SFGAO_FOLDER,&attr))||
     !(attr&SFGAO_FOLDER))return report;
  ComPtr<IShellLibrary> library;
  if(FAILED(::CoCreateInstance(CLSID_ShellLibrary,nullptr,CLSCTX_INPROC_SERVER,
       IID_PPV_ARGS(library.GetAddressOf())))||!library||
     FAILED(library->LoadLibraryFromItem(libraryItem.Get(),STGM_READ)))
   return report;
  ComPtr<IShellItem> saveFolder;
  if(FAILED(library->GetDefaultSaveFolder(
       DSFT_DETECT,IID_PPV_ARGS(saveFolder.GetAddressOf())))||!saveFolder)
   return report;
  PWSTR raw=nullptr;
  if(FAILED(saveFolder->GetDisplayName(SIGDN_FILESYSPATH,&raw))||!raw){
   if(raw)::CoTaskMemFree(raw);
   return report;
  }
  std::wstring targetPath(raw);
  ::CoTaskMemFree(raw);
  if(!safeFilesystemFolder(fs::path(targetPath),Kind::Copy))return report;
  PWSTR pictureRaw=nullptr;
  if(FAILED(::SHGetKnownFolderPath(
       FOLDERID_Pictures,0,nullptr,&pictureRaw))||!pictureRaw){
   if(pictureRaw)::CoTaskMemFree(pictureRaw);
   return report;
  }
  std::wstring knownPictures(pictureRaw);
  ::CoTaskMemFree(pictureRaw);
  // Never silently write into a redirected/custom library save location
  // until that location has its own acceptance and collision contract.
  if(!sameParent(fs::path(targetPath),fs::path(knownPictures)))return report;
  // Verify the effective target, not the library namespace, for collisions.
  for(auto const& source:request.sources){
   const auto name=fs::path(source).filename().native();
   if(!filecommand::validLeaf(name)){
    report.error=ERROR_INVALID_NAME;return report;
   }
   auto targetFile=fs::path(targetPath)/name;
   if(::GetFileAttributesW(targetFile.c_str())!=INVALID_FILE_ATTRIBUTES)
    report.collisions.push_back(targetFile.native());
  }
  report.queued=static_cast<std::uint32_t>(request.sources.size());
  report.error=!report.collisions.empty()&&
               request.collision==Collision::Reject?
               ERROR_ALREADY_EXISTS:ERROR_SUCCESS;
  concrete=std::move(saveFolder);
 }catch(...){report.error=ERROR_INVALID_PARAMETER;}
 return report;
}
} // namespace

namespace {
// Local fixed-disk regular files are copied to a unique sibling first.
// Publishing the filename happens only after CopyFileEx reports completion.
// A terminated worker may leave an explicitly named orphan stage; it must
// never publish a truncated file under the destination's requested name.
// Recycle, folder/provider, remote, removable, Move and KeepBoth retain their
// existing Shell paths and do NOT inherit an atomicity claim.
struct StagedCopyProgress final {
 Progress& progress;
 std::size_t index=0;
 std::size_t count=1;
 std::wstring receiptPath;
 std::wstring stagePath;
 std::wstring targetLeaf;
 bool receiptRequired=false;
 bool receiptWritten=false;
 bool receiptRejected=false;
};
DWORD CALLBACK onStagedCopyProgress(
 LARGE_INTEGER total,LARGE_INTEGER transferred,LARGE_INTEGER,
 LARGE_INTEGER,DWORD,DWORD,HANDLE,HANDLE destination,LPVOID state) noexcept{
 auto& value=*static_cast<StagedCopyProgress*>(state);
 if(value.progress.cancel.load(std::memory_order_relaxed))
  return PROGRESS_CANCEL;
 // CopyFileEx gives the actual destination HANDLE. Bind it on the first
 // callback, not from a guessed GUID/path. Abort without publication if
 // the opt-in protected journal cannot durably accept this exact identity.
 if(value.receiptRequired&&!value.receiptWritten){
  if(!writeBoundStageReceipt(value.receiptPath,value.stagePath,
                             value.targetLeaf,destination)){
   value.receiptRejected=true;
   return PROGRESS_CANCEL;
  }
  value.receiptWritten=true;
 }
 const auto part=total.QuadPart>0?
   static_cast<std::uint64_t>(
     (static_cast<long double>(transferred.QuadPart)*100)/
      static_cast<long double>(total.QuadPart)):0;
 const auto percent=static_cast<std::uint32_t>(
   (value.index*100+(std::min)(part,std::uint64_t{100}))/value.count);
 value.progress.percent.store(percent,std::memory_order_relaxed);
 return PROGRESS_CONTINUE;
}
bool stageEligible(Request const& task) noexcept{
 if(task.kind!=Kind::Copy||task.collision!=Collision::Reject||
    task.sourceMode!=SourceMode::Filesystem||
    task.destinationMode!=DestinationMode::Filesystem)return false;
 try{
  std::wstring sourceRoot,destRoot;
  if(!transferDriveRoot(task.sourceParent,sourceRoot)||
     !transferDriveRoot(task.destination,destRoot)||
     ::GetDriveTypeW(sourceRoot.c_str())!=DRIVE_FIXED||
     ::GetDriveTypeW(destRoot.c_str())!=DRIVE_FIXED)return false;
  for(auto const& path:task.sources){
   const auto attrs=::GetFileAttributesW(path.c_str());
   if(attrs==INVALID_FILE_ATTRIBUTES||
      (attrs&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
    return false;
  }
  return true;
 }catch(...){return false;}
}
// Publish ONLY the stage belonging to the active journalled worker.
// The stage file HANDLE is pinned through the no-replace rename. The
// destination directory is opened and checked but Win32 re-resolves the
// absolute target pathname, so ancestor/path-swap races remain possible.
// A matching pathname alone is not authority; never use this for recovery.
bool publishActiveBoundStage(std::wstring const& stage,
                             std::wstring const& target,
                             StageOwnershipReceipt const& proof,
                             DWORD& error) noexcept {
 error=ERROR_INVALID_DATA;
 try{
  const fs::path source(stage),destination(target);
  if(source.parent_path()!=destination.parent_path()||
     proof.stagePath!=stage||
     proof.targetLeaf!=destination.filename().native()||
     !safeFilesystemFolder(source.parent_path(),Kind::Copy))
   return false;
  // Pin the COMPLETE absolute destination ancestor chain, not just the
  // final directory. Holding each HANDLE without FILE_SHARE_DELETE prevents
  // a competing rename of any component while the absolute target pathname
  // is re-resolved by FileRenameInfo. A conflicting existing DELETE handle
  // makes the pin fail closed (ERROR_SHARING_VIOLATION).
  struct DirectoryPins final {
   std::vector<HANDLE> handles;
   ~DirectoryPins(){for(auto it=handles.rbegin();it!=handles.rend();++it)
      ::CloseHandle(*it);}
  } pins;
  const fs::path parent=source.parent_path();
  if(parent.lexically_normal()!=parent||parent.root_path().empty())
   return false;
  auto pin=[&](fs::path const& expected)->bool {
   const HANDLE handle=::CreateFileW(expected.c_str(),
       FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE,
       nullptr,OPEN_EXISTING,
       FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
   if(handle==INVALID_HANDLE_VALUE){error=::GetLastError();return false;}
   // Own the handle before any throwing allocation or conversion.
   try{pins.handles.push_back(handle);}catch(...){::CloseHandle(handle);throw;}
   BY_HANDLE_FILE_INFORMATION info{};
   if(!::GetFileInformationByHandle(handle,&info)||
      !(info.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)||
      (info.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT))
    return false;
   const DWORD units=::GetFinalPathNameByHandleW(
       handle,nullptr,0,FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);
   if(units<5||units>32000)return false;
   std::wstring resolved(units+1,L'\0');
   const DWORD size=::GetFinalPathNameByHandleW(
       handle,resolved.data(),static_cast<DWORD>(resolved.size()),
       FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);
   if(size!=units){
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
    std::printf("M22_PIN_REJECT=length expectedUnits=%lu actualUnits=%lu\n",
                units,size);
#endif
    return false;
   }
   resolved.resize(size);
   const bool matches=resolved.rfind(L"\\\\?\\",0)==0&&
       ::CompareStringOrdinal(resolved.c_str()+4,-1,
                              expected.c_str(),-1,TRUE)==CSTR_EQUAL;
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
   if(!matches)
    std::printf("M22_PIN_REJECT=resolved_path expected=%ls actual=%ls\n",
                expected.c_str(),resolved.c_str());
#endif
   return matches;
  };
  fs::path component=parent.root_path();
  if(!pin(component))return false;
  for(auto part=parent.begin();part!=parent.end();++part){
   if(*part==parent.root_name()||*part==parent.root_directory())
    continue;
   component/=*part;
   if(!pin(component))return false;
  }
  const HANDLE directory=pins.handles.back();
  BY_HANDLE_FILE_INFORMATION folder{};
  if(!::GetFileInformationByHandle(directory,&folder))
   return false;
#if defined(FLY_M22_TEST_DIRECTORY_RENAME_LOCK)
  if(auto probe=g_directoryRenameProbe.load(std::memory_order_acquire))
   probe(parent.native());
#endif
  const HANDLE active=::CreateFileW(stage.c_str(),
      DELETE|FILE_READ_ATTRIBUTES,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
      OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(active==INVALID_HANDLE_VALUE){
   error=::GetLastError();return false;
  }
  struct ActiveStageGuard final {
   HANDLE value;
   ~ActiveStageGuard(){::CloseHandle(value);}
  } ownedStage{active};
  BY_HANDLE_FILE_INFORMATION basic{};
  FILE_ID_INFO file{};
  const bool sameObject=::GetFileInformationByHandle(active,&basic)!=FALSE&&
      !(basic.dwFileAttributes&
          (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))&&
      basic.nNumberOfLinks==1&&
      ::GetFileInformationByHandleEx(active,FileIdInfo,&file,sizeof(file))!=FALSE&&
      file.VolumeSerialNumber==proof.stageIdentity.volumeSerial&&
      std::equal(std::begin(file.FileId.Identifier),
                 std::end(file.FileId.Identifier),
                 proof.stageIdentity.fileId.begin())&&
      (static_cast<std::uint64_t>(folder.dwVolumeSerialNumber)&0xffffffffu)==
       (file.VolumeSerialNumber&0xffffffffu);
  if(!sameObject)return false;
  // path::native() returns a reference owned by its path. filename()
  // creates a temporary path, so never bind a reference to its native().
  const std::wstring exactTarget=destination.native();
  const std::size_t size=sizeof(FILE_RENAME_INFO)+
                         exactTarget.size()*sizeof(wchar_t);
  std::vector<unsigned char> payload(size);
  auto* rename=reinterpret_cast<FILE_RENAME_INFO*>(payload.data());
  rename->ReplaceIfExists=FALSE;
  rename->RootDirectory=nullptr;
  rename->FileNameLength=static_cast<DWORD>(
      exactTarget.size()*sizeof(wchar_t));
  std::memcpy(rename->FileName,exactTarget.data(),rename->FileNameLength);
  const bool published=::SetFileInformationByHandle(
      active,FileRenameInfo,rename,static_cast<DWORD>(payload.size()))!=FALSE;
  error=published?ERROR_SUCCESS: ::GetLastError();
  return published;
 }catch(...){error=ERROR_INVALID_PARAMETER;return false;}
}
Report copyStagedFiles(Request const& task,Progress& progress,
                       Report report) noexcept{
 try{
  const auto dest=fs::path(task.destination);
  for(std::size_t i=0;i<task.sources.size();++i){
   if(canceled(progress)){
    report.error=ERROR_CANCELLED;report.aborted=true;return report;
   }
   GUID guid{};
   if(FAILED(::CoCreateGuid(&guid))){
    report.error=ERROR_GEN_FAILURE;return report;
   }
   wchar_t guidText[40]{};
   if(!::StringFromGUID2(guid,guidText,40)){
    report.error=ERROR_GEN_FAILURE;return report;
   }
   const auto stage=dest/(std::wstring(L".flyExplorer-copy-")+
                          guidText+L".partial");
   const auto target=dest/fs::path(task.sources[i]).filename();
   if(stage.native().size()>32000||target.native().size()>32000){
    report.error=ERROR_FILENAME_EXCED_RANGE;return report;
   }
   StagedCopyProgress callback{progress,i,task.sources.size()};
   if(!progress.receiptDirectory.empty()){
    if(!isPrivateStageReceiptDirectory(progress.receiptDirectory)){
     report.error=ERROR_ACCESS_DENIED;return report;
    }
    callback.receiptRequired=true;
    callback.receiptPath=(fs::path(progress.receiptDirectory)/
      (std::wstring(L".flyExplorer-receipt-")+guidText+L".bin")).native();
    callback.stagePath=stage.native();
    callback.targetLeaf=target.filename().native();
   }
   // FAIL_IF_EXISTS avoids silently reusing a stale or unowned stage.
   const BOOL copied=::CopyFileExW(
       task.sources[i].c_str(),stage.c_str(),
       &onStagedCopyProgress,&callback,nullptr,COPY_FILE_FAIL_IF_EXISTS);
   const DWORD copyError=copied?ERROR_SUCCESS: ::GetLastError();
   const bool wasCanceled=canceled(progress)||
       copyError==ERROR_REQUEST_ABORTED||
       copyError==ERROR_OPERATION_ABORTED;
   // CopyFileEx is allowed to skip progress callbacks, notably on empty
   // files. A successful completed copy can bind the same stage using
   // an exact read-only handle before any publication. This does not
   // retroactively cover a worker killed before this point.
   if(copied&&!wasCanceled&&callback.receiptRequired&&
      !callback.receiptWritten&&!callback.receiptRejected){
    const HANDLE stageHandle=::CreateFileW(stage.c_str(),
       FILE_READ_ATTRIBUTES,
       FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,
       OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if(stageHandle!=INVALID_HANDLE_VALUE){
     callback.receiptWritten=writeBoundStageReceipt(
       callback.receiptPath,stage.native(),callback.targetLeaf,stageHandle);
     ::CloseHandle(stageHandle);
    }
   }
   StageOwnershipReceipt proof{};
   const bool journalReady=!callback.receiptRequired||
      (callback.receiptWritten&&!callback.receiptRejected&&
       readStageReceipt(callback.receiptPath,proof)&&
       proof.stagePath==stage.native()&&
       proof.targetLeaf==target.filename().native()&&
       receiptMatchesStage(proof));
   // Durable completion marker precedes publication; a failed write
   // cannot be confused with a completed copy or a safe orphan.
   const bool copyRecorded=!callback.receiptRequired||
      (copied&&!wasCanceled&&journalReady&&
       markStageCopyCompleted(callback.receiptPath));
   DWORD renameError=ERROR_INVALID_DATA;
   BOOL published=FALSE;
   if(copied&&!wasCanceled&&journalReady&&copyRecorded){
    if(callback.receiptRequired){
     // Pin the verified source file HANDLE through publication. Win32
     // resolves the full destination pathname; reparse/parent races are
     // still open and must not be mistaken for an authenticated target.
     published=publishActiveBoundStage(
         stage.native(),target.native(),proof,renameError)?TRUE:FALSE;
    }else{
     // Preserve the original legacy behavior outside protected journaling.
     published=::MoveFileExW(
         stage.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH);
     renameError=published?ERROR_SUCCESS: ::GetLastError();
    }
   }
   const DWORD publishError=published?ERROR_SUCCESS:
       copied&&!wasCanceled&&(!journalReady||!copyRecorded)?
         ERROR_INVALID_DATA:
       copied&&!wasCanceled?renameError:copyError;
   if(!published){
    // An unjournaled stage can already contain copy bytes before the
    // first callback. It cannot be proven recoverable: leave it untouched.
    // Journalled failures also remain for explicit human review, not an
    // automatic by-path deletion susceptible to replacement races.
    if(!callback.receiptRequired){
     DWORD attrs=::GetFileAttributesW(stage.c_str());
     if(attrs!=INVALID_FILE_ATTRIBUTES){
      if(attrs&FILE_ATTRIBUTE_READONLY)
       ::SetFileAttributesW(stage.c_str(),attrs&~FILE_ATTRIBUTE_READONLY);
      ::DeleteFileW(stage.c_str());
     }
    }
    report.error=wasCanceled?ERROR_CANCELLED:publishError;
    report.aborted=wasCanceled;
    return report;
   }
   // The rename has already occurred; an unreadable/unwritable
   // publication marker leaves an ambiguous journal. Report the
   // metadata fault without reversing or deleting a completed file.
   if(callback.receiptRequired&&
      !markStageCopyPublished(callback.receiptPath)){
    report.error=ERROR_WRITE_FAULT;
    return report;
   }
   progress.percent.store(static_cast<std::uint32_t>(
      ((i+1)*100)/task.sources.size()),std::memory_order_relaxed);
  }
  report.error=ERROR_SUCCESS;
  return report;
 }catch(...){
  report.error=ERROR_INVALID_PARAMETER;
  return report;
 }
}
} // namespace

Report execute(Request const& task,Progress& progress) noexcept{
 Report report=validate(task);
 if(report.error!=ERROR_SUCCESS)return report;
 if(canceled(progress)){report.error=ERROR_CANCELLED;report.aborted=true;return report;}
 const HRESULT initialized=::CoInitializeEx(nullptr,
          COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
 if(FAILED(initialized)){report.error=code(initialized);return report;}
 if(stageEligible(task)){
  report=copyStagedFiles(task,progress,std::move(report));
  ::CoUninitialize();
  return report;
 }
 if(task.sourceMode==SourceMode::ShellProvider){
  report=validateProviderCopy(task);
  if(report.error!=ERROR_SUCCESS){
   ::CoUninitialize();
   return report;
  }
 }
 ComPtr<IShellItem> providerDestination;
 if(task.destinationMode==DestinationMode::ShellProvider){
  report=verifyPicturesLibraryCopyIn(task,providerDestination);
  if(report.error!=ERROR_SUCCESS){
   ::CoUninitialize();return report;
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
 if(SUCCEEDED(hr)&&task.kind!=Kind::Recycle){
  if(task.destinationMode==DestinationMode::ShellProvider)
   dest=providerDestination;
  else
   hr=::SHCreateItemFromParsingName(task.destination.c_str(),nullptr,
                                    IID_PPV_ARGS(dest.GetAddressOf()));
 }
 bool performed=false;
 if(SUCCEEDED(hr)){
  for(std::size_t i=0;i<task.sources.size();++i){
   if(canceled(progress)){hr=E_ABORT;break;}
   ComPtr<IShellItem> item;
   if(task.sourceMode==SourceMode::ShellProvider){
    if(i>=task.sourcePidls.size()||!validPidlBlob(task.sourcePidls[i])){
     hr=E_INVALIDARG;
    }else{
     auto sourcePidl=reinterpret_cast<PCIDLIST_ABSOLUTE>(
         task.sourcePidls[i].data());
     hr=::SHCreateItemFromIDList(
         sourcePidl,IID_PPV_ARGS(item.GetAddressOf()));
    }
   }else{
    hr=::SHCreateItemFromParsingName(task.sources[i].c_str(),nullptr,
                                     IID_PPV_ARGS(item.GetAddressOf()));
   }
   if(FAILED(hr))break;
   if(task.kind==Kind::Copy)hr=operation->CopyItem(item.Get(),dest.Get(),nullptr,nullptr);
   else if(task.kind==Kind::Move)hr=operation->MoveItem(item.Get(),dest.Get(),nullptr,nullptr);
   else hr=operation->DeleteItem(item.Get(),nullptr);
   if(FAILED(hr))break;
  }
  if(SUCCEEDED(hr)&&!canceled(progress)){
   performed=true;
   hr=operation->PerformOperations();
  }
  else if(SUCCEEDED(hr))hr=E_ABORT;
 }
 BOOL anyAborted=FALSE;
 // Per Microsoft, PerformOperations may return success despite a stopped
 // operation. Query aborted state even when PerformOperations failed.
 if(operation&&performed){
  const auto probe=operation->GetAnyOperationsAborted(&anyAborted);
  if(FAILED(probe)&&SUCCEEDED(hr))hr=probe;
 }
 if(sink&&SUCCEEDED(hr)&&FAILED(sink->firstFailure()))
  hr=sink->firstFailure();
 if(operation&&sink&&cookie)operation->Unadvise(cookie);
 if(sink)sink->Release();
 report.aborted=anyAborted||canceled(progress)||hr==E_ABORT;
 // Preserve concrete access-denied/read/IO failure when a later batch item
 // fails. Aborted does not mean the preceding items were rolled back.
 report.error=canceled(progress)||hr==E_ABORT?ERROR_CANCELLED:
              FAILED(hr)?code(hr):
              anyAborted?ERROR_CANCELLED:ERROR_SUCCESS;
 if(report.error==ERROR_SUCCESS)progress.percent.store(100);
 ::CoUninitialize();
 return report;
}
namespace {
constexpr std::uint32_t kTransferWireMagic=0x31525446u; // FTR1
constexpr std::uint32_t kTransferWireVersion=3;
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
bool appendBlob(std::vector<unsigned char>& body,
                std::vector<unsigned char> const& value,std::size_t maximum){
 if(value.size()>maximum||
    !appendU32(body,static_cast<std::uint32_t>(value.size())))return false;
 return value.empty()||appendBytes(body,value.data(),value.size());
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
     (task.destinationMode!=DestinationMode::Filesystem&&
      task.destinationMode!=DestinationMode::ShellProvider)||
     (task.destinationMode==DestinationMode::ShellProvider&&
       (task.sourceMode!=SourceMode::Filesystem||task.kind!=Kind::Copy||
        !validPidlBlob(task.destinationPidl)))||
     (task.destinationMode==DestinationMode::Filesystem&&
       !task.destinationPidl.empty())||
     task.sources.empty()||task.sources.size()>kMaxItems||
     task.sourceParent.empty()||
     task.sourceParent.size()>(task.sourceMode==SourceMode::ShellProvider?
        kMaxProviderParsingUnits:std::size_t{32000})||
     task.destination.empty()||
     task.destination.size()>(task.destinationMode==DestinationMode::ShellProvider?
       kMaxProviderParsingUnits:std::size_t{32000})||
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
     !appendU32(body,static_cast<std::uint32_t>(task.destinationMode))||
     !appendU32(body,static_cast<std::uint32_t>(task.kind))||
     !appendU32(body,static_cast<std::uint32_t>(task.collision))||
     !appendString(body,task.sourceParent,sourceLimit)||
     !appendString(body,task.destination,
       task.destinationMode==DestinationMode::ShellProvider?
        kMaxProviderParsingUnits:std::size_t{32000})||
     !appendU32(body,static_cast<std::uint32_t>(task.sources.size())))
   return false;
  for(auto const& source:task.sources)
   if(!appendString(body,source,sourceLimit))return false;
  if(task.sourceMode==SourceMode::ShellProvider){
   if(task.sourcePidls.size()!=task.sources.size()||
      !appendBlob(body,task.sourceParentPidl,kMaxProviderPidlBytes)||
      !appendU32(body,static_cast<std::uint32_t>(task.sourcePidls.size())))
    return false;
   for(auto const& pidl:task.sourcePidls)
    if(!appendBlob(body,pidl,kMaxProviderPidlBytes))return false;
  }else{
   if(!task.sourceParentPidl.empty()||!task.sourcePidls.empty()||
      !appendU32(body,0)||!appendU32(body,0))return false;
  }
  if(!appendBlob(body,task.destinationPidl,kMaxProviderPidlBytes))return false;
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
 std::vector<unsigned char> blob(std::size_t maximum){
  const auto bytes=u32();
  if(!valid||bytes>maximum||bytes>body.size()-offset){
   valid=false;return {};
  }
  std::vector<unsigned char> value(bytes);
  if(bytes)std::memcpy(value.data(),body.data()+offset,bytes);
  offset+=bytes;
  return value;
 }
};
bool parseTransfer(std::vector<unsigned char> const& body,
                   Request& task) noexcept{
 try{
  WireReader reader{body};
  const auto sourceMode=reader.u32();
  const auto destinationMode=reader.u32();
  const auto kind=reader.u32();
  const auto collision=reader.u32();
  if(sourceMode>static_cast<std::uint32_t>(SourceMode::ShellProvider)||
     destinationMode>static_cast<std::uint32_t>(DestinationMode::ShellProvider)||
     kind>static_cast<std::uint32_t>(Kind::Move)||
     collision>static_cast<std::uint32_t>(Collision::KeepBoth))
   return false;
  task=Request{};
  task.sourceMode=static_cast<SourceMode>(sourceMode);
  task.destinationMode=static_cast<DestinationMode>(destinationMode);
  task.kind=static_cast<Kind>(kind);
  task.collision=static_cast<Collision>(collision);
  if((task.kind!=Kind::Copy&&task.kind!=Kind::Move)||
     (task.sourceMode==SourceMode::ShellProvider&&task.kind!=Kind::Copy)||
     (task.destinationMode==DestinationMode::ShellProvider&&
      (task.sourceMode!=SourceMode::Filesystem||task.kind!=Kind::Copy)))
   return false;
  const auto sourceLimit=task.sourceMode==SourceMode::ShellProvider?
      kMaxProviderParsingUnits:std::size_t{32000};
  task.sourceParent=reader.string(sourceLimit);
  task.destination=reader.string(
      task.destinationMode==DestinationMode::ShellProvider?
      kMaxProviderParsingUnits:std::size_t{32000});
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
  task.sourceParentPidl=reader.blob(kMaxProviderPidlBytes);
  const auto pidlCount=reader.u32();
  if(!reader.valid||pidlCount>kMaxItems)return false;
  task.sourcePidls.reserve(pidlCount);
  std::size_t pidlBytes=task.sourceParentPidl.size();
  for(std::uint32_t i=0;i<pidlCount;++i){
   auto pidl=reader.blob(kMaxProviderPidlBytes);
   if(!reader.valid||pidl.empty()||
      pidl.size()>kMaxProviderPidlBytesTotal-pidlBytes)return false;
   pidlBytes+=pidl.size();
   task.sourcePidls.push_back(std::move(pidl));
  }
  if(task.sourceMode==SourceMode::ShellProvider){
   if(!validPidlBlob(task.sourceParentPidl)||
      task.sourcePidls.size()!=task.sources.size())return false;
  }else if(!task.sourceParentPidl.empty()||!task.sourcePidls.empty()){
   return false;
  }
  task.destinationPidl=reader.blob(kMaxProviderPidlBytes);
  if(!reader.valid||
     (task.destinationMode==DestinationMode::ShellProvider?
       !validPidlBlob(task.destinationPidl):!task.destinationPidl.empty()))
   return false;
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
  // This branch is never configured by a pane/request-supplied directory.
  // Windows Known Folder + owner-only protected ACL gate can fail closed:
  // legacy staged Copy remains available but gets no recovery receipt.
#if defined(FLY_M22_TEST_ISOLATED_RECEIPT_STORE)
  // TEST BUILD ONLY: the helper's exact executable must be built with the
  // explicit fixture flag. Never accept environment-configured receipt paths
  // in the shipping helper or across the production transfer wire.
  if(stageEligible(task)){
   std::array<wchar_t,32768> owned{};
   const DWORD units=::GetEnvironmentVariableW(
       L"FLY_M22_OWNED_RECEIPT_STORE",owned.data(),
       static_cast<DWORD>(owned.size()));
   if(!units||units>=owned.size()||
      !isPrivateStageReceiptDirectory(std::wstring(owned.data(),units)))
    return 79;
   progress.receiptDirectory.assign(owned.data(),units);
  }
#else
  if(stageEligible(task))
   (void)prepareUserStageReceiptDirectory(progress.receiptDirectory);
#endif
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
