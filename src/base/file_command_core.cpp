#define WIN32_LEAN_AND_MEAN
#include "file_command_core.h"
#include <filesystem>
#include <algorithm>
#include <cwctype>
#include <shobjidl.h>
#pragma comment(lib,"ole32.lib")
namespace fxfile::filecommand {
namespace {
// R07-2: read-only evidence for a regular file on a fixed local drive.
// Never issue an undo/redo operation based solely on this snapshot.
bool safeRenameEvidenceParent(std::filesystem::path const& file) noexcept {
 try {
  if(!file.is_absolute()||file.lexically_normal()!=file)return false;
  auto const parent=file.parent_path();
  auto const root=parent.root_path().native();
  if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
     ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
  std::filesystem::path current;
  for(auto const& part:parent){
   current/=part;
   if(!current.has_root_directory())continue;
   DWORD const attrs=::GetFileAttributesW(current.c_str());
   if(attrs==INVALID_FILE_ATTRIBUTES||
      !(attrs&FILE_ATTRIBUTE_DIRECTORY)||
      (attrs&FILE_ATTRIBUTE_REPARSE_POINT))return false;
  }
  return true;
 }catch(...){return false;}
}
bool readRenameEvidence(
 std::filesystem::path const& file,RenameEvidence& evidence) noexcept {
 DWORD const attrs=::GetFileAttributesW(file.c_str());
 if(attrs==INVALID_FILE_ATTRIBUTES||
    (attrs&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
  return false;
 HANDLE const handle=::CreateFileW(
  file.c_str(),FILE_READ_ATTRIBUTES,
  FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
  nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
 if(handle==INVALID_HANDLE_VALUE)return false;
 FILE_ATTRIBUTE_TAG_INFO tag{};
 FILE_ID_INFO identity{};
 FILE_STANDARD_INFO standard{};
 FILE_BASIC_INFO basic{};
 bool const ok=
  ::GetFileInformationByHandleEx(
   handle,FileAttributeTagInfo,&tag,sizeof(tag))&&
  !(tag.FileAttributes&
    (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))&&
  ::GetFileInformationByHandleEx(
   handle,FileIdInfo,&identity,sizeof(identity))&&
  ::GetFileInformationByHandleEx(
   handle,FileStandardInfo,&standard,sizeof(standard))&&
  !standard.Directory&&!standard.DeletePending&&
  standard.NumberOfLinks==1&&standard.EndOfFile.QuadPart>=0&&
  ::GetFileInformationByHandleEx(
   handle,FileBasicInfo,&basic,sizeof(basic));
 bool const closed=::CloseHandle(handle)!=FALSE;
 if(!ok||!closed)return false;
 evidence.volumeSerial=identity.VolumeSerialNumber;
 std::copy_n(identity.FileId.Identifier,evidence.fileId.size(),
             evidence.fileId.begin());
 evidence.fileSize=static_cast<std::uint64_t>(standard.EndOfFile.QuadPart);
 evidence.lastWriteTime=basic.LastWriteTime.QuadPart;
 evidence.verified=true;
 return true;
}
bool sameRenameEvidence(
 RenameEvidence const& before,RenameEvidence const& after) noexcept {
 return before.verified&&after.verified&&
  before.volumeSerial==after.volumeSerial&&
  before.fileId==after.fileId&&
  before.fileSize==after.fileSize&&
  before.lastWriteTime==after.lastWriteTime;
}
} // namespace

RenameRestoreObservation inspectRenameRestore(
 std::wstring const& originalPath,Result const& renamed) noexcept {
 // Do not turn a previous rename success into authority to mutate anything.
 // This function never issues a write, delete, move or retained handle.
 if(renamed.error!=ERROR_SUCCESS||!renamed.renameEvidence.verified)
  return RenameRestoreObservation::UnverifiedReceipt;
 try{
  std::filesystem::path const original(originalPath);
  std::filesystem::path const target(renamed.target);
  if(original.empty()||target.empty()||
     !original.is_absolute()||!target.is_absolute()||
     original.lexically_normal()!=original||
     target.lexically_normal()!=target||
     original.parent_path()!=target.parent_path()||
     !validLeaf(original.filename().native())||
     !validLeaf(target.filename().native())||
     ([](int comparison) noexcept {
       return comparison != CSTR_LESS_THAN && comparison != CSTR_GREATER_THAN;
     })(::CompareStringOrdinal(original.c_str(),-1,target.c_str(),-1,TRUE))||
     !safeRenameEvidenceParent(original)||
     !safeRenameEvidenceParent(target))
   return RenameRestoreObservation::UnsafePaths;

  // Only an explicit FILE_NOT_FOUND on an otherwise verified parent counts
  // as an absent original name. Access denied, path not found, reparse and
  // other uncertain results must fail closed.
  DWORD const prior=::GetFileAttributesW(original.c_str());
  if(prior!=INVALID_FILE_ATTRIBUTES||
     ::GetLastError()!=ERROR_FILE_NOT_FOUND)
   return RenameRestoreObservation::OriginalOccupiedOrUnknown;

  RenameEvidence current{};
  if(!readRenameEvidence(target,current)||
     !sameRenameEvidence(renamed.renameEvidence,current))
   return RenameRestoreObservation::TargetChangedOrUnavailable;

  // Point-in-time observation only. This does NOT close the TOCTOU gap,
  // reserve the original name, hold the target handle or enable Undo/Redo.
  return RenameRestoreObservation::MatchingSnapshotOnly;
 }catch(...){return RenameRestoreObservation::UnsafePaths;}
}


RenameTargetLease::~RenameTargetLease() noexcept {
 reset();
}
void RenameTargetLease::reset() noexcept {
 if(handle_!=INVALID_HANDLE_VALUE){
  ::CloseHandle(handle_);
  handle_=INVALID_HANDLE_VALUE;
 }
 originalPath_.clear();
 targetPath_.clear();
 expected_=RenameEvidence{};
}
RenameRestoreObservation RenameTargetLease::begin(
 std::wstring const& originalPath,Result const& renamed) noexcept {
 reset();
 auto const first=inspectRenameRestore(originalPath,renamed);
 if(first!=RenameRestoreObservation::MatchingSnapshotOnly)return first;
 try{
  // Allocate before acquiring the handle; nothing can throw while it is
  // temporarily owned by a local variable.
  std::wstring originalCopy(originalPath);
  std::wstring targetCopy(renamed.target);
  // FILE_READ_DATA makes Windows sharing checks cover pre-existing writers;
  // FILE_SHARE_READ denies new write/delete/rename opens for this target.
  // No DELETE right and no mutating API is used by this guard.
  HANDLE const acquired=::CreateFileW(
   targetCopy.c_str(),FILE_READ_DATA|FILE_READ_ATTRIBUTES,
   FILE_SHARE_READ,nullptr,OPEN_EXISTING,
   FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(acquired==INVALID_HANDLE_VALUE)
   return RenameRestoreObservation::TargetChangedOrUnavailable;
  handle_=acquired;
  originalPath_.swap(originalCopy);
  targetPath_.swap(targetCopy);
  expected_=renamed.renameEvidence;
  auto const observed=recheck();
  if(observed!=RenameRestoreObservation::MatchingSnapshotOnly)reset();
  return observed;
 }catch(...){
  reset();
  return RenameRestoreObservation::UnsafePaths;
 }
}
RenameRestoreObservation RenameTargetLease::recheck() const noexcept {
 if(handle_==INVALID_HANDLE_VALUE||!expected_.verified)
  return RenameRestoreObservation::UnverifiedReceipt;
 try{
  std::filesystem::path const original(originalPath_);
  std::filesystem::path const target(targetPath_);
  if(original.empty()||target.empty()||
     !original.is_absolute()||!target.is_absolute()||
     original.lexically_normal()!=original||
     target.lexically_normal()!=target||
     original.parent_path()!=target.parent_path()||
     !validLeaf(original.filename().native())||
     !validLeaf(target.filename().native())||
     !safeRenameEvidenceParent(original)||
     !safeRenameEvidenceParent(target))
   return RenameRestoreObservation::UnsafePaths;
  int const comparison=::CompareStringOrdinal(
   original.c_str(),-1,target.c_str(),-1,TRUE);
  if(comparison!=CSTR_LESS_THAN&&comparison!=CSTR_GREATER_THAN)
   return RenameRestoreObservation::UnsafePaths;
  FILE_ID_INFO lockedId{};
  if(!::GetFileInformationByHandleEx(
      handle_,FileIdInfo,&lockedId,sizeof(lockedId))||
     lockedId.VolumeSerialNumber!=expected_.volumeSerial||
     !std::equal_n(lockedId.FileId.Identifier,expected_.fileId.size(),
                   expected_.fileId.begin()))
   return RenameRestoreObservation::TargetChangedOrUnavailable;
  // Check the pathname again, not just the retained handle identity.
  RenameEvidence visible{};
  if(!readRenameEvidence(target,visible)||
     !sameRenameEvidence(expected_,visible))
   return RenameRestoreObservation::TargetChangedOrUnavailable;
  DWORD const originalAttrs=::GetFileAttributesW(original.c_str());
  if(originalAttrs!=INVALID_FILE_ATTRIBUTES||
     ::GetLastError()!=ERROR_FILE_NOT_FOUND)
   return RenameRestoreObservation::OriginalOccupiedOrUnknown;
  // The original name is NOT reserved. This is never a write authorization.
  return RenameRestoreObservation::MatchingSnapshotOnly;
 }catch(...){return RenameRestoreObservation::UnsafePaths;}
}

bool validLeaf(std::wstring const& name) noexcept{
 if(name.empty()||name.size()>240||name==L"."||name==L".."||
    name.back()==L'.'||name.back()==L' ')return false;
 for(wchar_t ch:name)
  if(ch<32||ch==L'/'||ch==L'\\'||ch==L':'||ch==L'*'||ch==L'?'||
     ch==L'"'||ch==L'<'||ch==L'>'||ch==L'|')return false;
 std::wstring stem=name.substr(0,name.find(L'.'));
 for(auto& ch:stem)ch=static_cast<wchar_t>(std::towupper(ch));
 // These names address Win32 devices, not ordinary directory entries.
 // Keep the check on the stem: an extension does not make a device safe.
 if(stem==L"CON"||stem==L"PRN"||stem==L"AUX"||stem==L"NUL"||
    stem==L"CONIN$"||stem==L"CONOUT$")return false;
 if(stem.size()==4&&((stem.substr(0,3)==L"COM")||
                      (stem.substr(0,3)==L"LPT"))){
  const wchar_t digit=stem[3];
  if((digit>=L'1'&&digit<=L'9')||
     digit==L'\u00B9'||digit==L'\u00B2'||digit==L'\u00B3')
   return false;
 }
 return true;
}
bool validTextDocumentLeaf(std::wstring const& name) noexcept{
 return validLeaf(name)&&name.size()>4&&
  ::CompareStringOrdinal(name.c_str()+name.size()-4,4,L".txt",4,TRUE)==CSTR_EQUAL;
}
bool validMarkdownDocumentLeaf(std::wstring const& name) noexcept{
 return validLeaf(name)&&name.size()>3&&
  ::CompareStringOrdinal(name.c_str()+name.size()-3,3,L".md",3,TRUE)==CSTR_EQUAL;
}
bool validShortcutLeaf(std::wstring const& name) noexcept{
 return validLeaf(name)&&name.size()>4&&
  ::CompareStringOrdinal(name.c_str()+name.size()-4,4,L".lnk",4,TRUE)==CSTR_EQUAL;
}
Result execute(Request const& task) noexcept{
 Result result{};
 if(!validLeaf(task.name)||task.parent.empty()||
    task.parent.size()>32000||task.parent[0]==L':'||
    (task.parent.size()>=2&&task.parent.substr(0,2)==L"::")){
  result.error=ERROR_INVALID_NAME;
  return result;
 }
 try{
  std::filesystem::path parent(task.parent);
  if(!parent.is_absolute()||!parent.has_root_directory()){
   result.error=ERROR_INVALID_NAME;return result;
  }
  const auto folder=parent.lexically_normal();
  const auto attrs=::GetFileAttributesW(folder.c_str());
  if(attrs==INVALID_FILE_ATTRIBUTES||!(attrs&FILE_ATTRIBUTE_DIRECTORY)){
   result.error=ERROR_PATH_NOT_FOUND;return result;
  }
  const auto target=(folder/task.name).lexically_normal();
  if(target.parent_path()!=folder){result.error=ERROR_INVALID_NAME;return result;}
  result.target=target.native();
  if(task.kind==Kind::CreateFolder){
   if(::CreateDirectoryW(target.c_str(),nullptr))result.error=ERROR_SUCCESS;
   else result.error=::GetLastError();
   return result;
  }
  if(task.kind==Kind::CreateTextFile||task.kind==Kind::CreateMarkdownFile){
   if(task.kind==Kind::CreateTextFile?!validTextDocumentLeaf(task.name):
                                    !validMarkdownDocumentLeaf(task.name)){
    result.error=ERROR_INVALID_NAME;return result;
   }
   // Limit creation to a local drive and reject reparse ancestors. No UNC,
   // provider or device namespace receives this new mutation command.
   const auto root=folder.root_path().native();
   if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'){
    result.error=ERROR_NOT_SUPPORTED;return result;
   }
   const auto drive=::GetDriveTypeW(root.c_str());
   if(drive!=DRIVE_FIXED&&drive!=DRIVE_REMOVABLE){
    result.error=ERROR_NOT_SUPPORTED;return result;
   }
   std::filesystem::path current;
   for(auto const& part:folder){
    current/=part;
    if(!current.has_root_directory())continue;
    const DWORD flags=::GetFileAttributesW(current.c_str());
    if(flags==INVALID_FILE_ATTRIBUTES){
     result.error=::GetLastError();return result;
    }
    if(!(flags&FILE_ATTRIBUTE_DIRECTORY)||
       (flags&FILE_ATTRIBUTE_REPARSE_POINT)){
     result.error=ERROR_ACCESS_DENIED;return result;
    }
   }
   // Atomic no-replace creation: never overwrite an existing file.
   const HANDLE file=::CreateFileW(target.c_str(),GENERIC_WRITE,
       FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
   if(file==INVALID_HANDLE_VALUE)result.error=::GetLastError();
   else if(!::CloseHandle(file))result.error=::GetLastError();
   else result.error=ERROR_SUCCESS;
   return result;
  }

  if(task.kind==Kind::CreateShortcut){
   if(!validShortcutLeaf(task.name)){
    result.error=ERROR_INVALID_NAME;return result;
   }
   const auto root=folder.root_path().native();
   if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
      ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED){
    result.error=ERROR_NOT_SUPPORTED;return result;
   }
   std::filesystem::path current;
   for(auto const& part:folder){
    current/=part;
    if(!current.has_root_directory())continue;
    const DWORD flags=::GetFileAttributesW(current.c_str());
    if(flags==INVALID_FILE_ATTRIBUTES){
     result.error=::GetLastError();return result;
    }
    if(!(flags&FILE_ATTRIBUTE_DIRECTORY)||
       (flags&FILE_ATTRIBUTE_REPARSE_POINT)){
     result.error=ERROR_ACCESS_DENIED;return result;
    }
   }
   const std::filesystem::path src(task.source);
   if(!src.is_absolute()||src.lexically_normal()!=src||
      src.parent_path()!=folder||!validLeaf(src.filename().native())){
    result.error=ERROR_INVALID_NAME;return result;
   }
   const DWORD sourceAttrs=::GetFileAttributesW(src.c_str());
   if(sourceAttrs==INVALID_FILE_ATTRIBUTES){
    result.error=::GetLastError();return result;
   }
   if(sourceAttrs&FILE_ATTRIBUTE_REPARSE_POINT){
    result.error=ERROR_NOT_SUPPORTED;return result;
   }
   if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
    result.error=ERROR_ALREADY_EXISTS;return result;
   }
   // Write only a randomly named stage owned by this request. The final
   // publication is same-directory and never uses REPLACE_EXISTING.
   GUID guid{};
   if(FAILED(::CoCreateGuid(&guid))){result.error=ERROR_GEN_FAILURE;return result;}
   wchar_t guidText[40]{};
   if(!::StringFromGUID2(guid,guidText,40)){
    result.error=ERROR_GEN_FAILURE;return result;
   }
   const auto stage=folder/(std::wstring(L".flyExplorer-shortcut-")+
                            guidText+L".tmp");
   const HANDLE reserved=::CreateFileW(stage.c_str(),GENERIC_WRITE,0,
       nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);
   if(reserved==INVALID_HANDLE_VALUE){
    result.error=::GetLastError();return result;
   }
   if(!::CloseHandle(reserved)){
    result.error=::GetLastError();::DeleteFileW(stage.c_str());return result;
   }
   const HRESULT initialized=::CoInitializeEx(
       nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
   if(FAILED(initialized)){
    result.error=static_cast<DWORD>(HRESULT_CODE(initialized));
    ::DeleteFileW(stage.c_str());return result;
   }
   IShellLinkW* link=nullptr;
   IPersistFile* persist=nullptr;
   HRESULT hr=::CoCreateInstance(CLSID_ShellLink,nullptr,CLSCTX_INPROC_SERVER,
                                  IID_PPV_ARGS(&link));
   if(SUCCEEDED(hr))hr=link->SetPath(src.c_str());
   if(SUCCEEDED(hr))hr=link->QueryInterface(IID_PPV_ARGS(&persist));
   if(SUCCEEDED(hr))hr=persist->Save(stage.c_str(),TRUE);
   if(persist)persist->Release();
   if(link)link->Release();
   ::CoUninitialize();
   if(FAILED(hr)){
    result.error=static_cast<DWORD>(HRESULT_CODE(hr));
    ::DeleteFileW(stage.c_str());return result;
   }
   if(::MoveFileExW(stage.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH)){
    result.error=ERROR_SUCCESS;return result;
   }
   result.error=::GetLastError();
   ::DeleteFileW(stage.c_str());
   return result;
  }
  if(task.kind!=Kind::RenameSelected){result.error=ERROR_INVALID_PARAMETER;return result;}
  std::filesystem::path src(task.source);
  if(!src.is_absolute()||
     src.lexically_normal().parent_path()!=folder||
     !validLeaf(src.filename().native())){
   result.error=ERROR_INVALID_NAME;return result;
  }
  int const renameComparison=::CompareStringOrdinal(
   src.c_str(),-1,target.c_str(),-1,TRUE);
  if(renameComparison!=CSTR_LESS_THAN&&renameComparison!=CSTR_GREATER_THAN){
   result.error=renameComparison==CSTR_EQUAL?
    ERROR_ALREADY_EXISTS:ERROR_INVALID_NAME;
   return result;
  }
  // Capture only read-only identity evidence before and after a rename.
  // A probe failure never changes ordinary rename success/failure semantics.
  RenameEvidence before{};
  bool const canRecord=safeRenameEvidenceParent(src)&&
                       readRenameEvidence(src,before);
  // Native MoveFileW never overwrites an existing destination.
  if(::MoveFileW(src.c_str(),target.c_str())){
   result.error=ERROR_SUCCESS;
   if(canRecord&&safeRenameEvidenceParent(target)){
    RenameEvidence after{};
    if(readRenameEvidence(target,after)&&
       sameRenameEvidence(before,after))
     result.renameEvidence=after;
   }
  }else result.error=::GetLastError();
 }catch(...){result.error=ERROR_INVALID_PARAMETER;}
 return result;
}
}
