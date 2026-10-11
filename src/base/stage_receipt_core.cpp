#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include "stage_receipt_core.h"
#include <objbase.h>
#include <sddl.h>
#include <aclapi.h>
#include <shlobj.h>
#include "file_command_core.h"
#include <filesystem>
#include <algorithm>
#include <cstring>
#include <iterator>
#include <utility>
#include <vector>
#pragma comment(lib,"advapi32.lib")
#pragma comment(lib,"shell32.lib")

namespace fxfile::shelltransfer {
namespace {
namespace fs=std::filesystem;
// v1 is a fixed Windows-only wire format, NOT a signed authenticity proof.
// Checksum detects incomplete/torn writes, not malicious same-user edits.
#pragma pack(push,1)
struct ReceiptWire {
 char magic[8];
 std::uint32_t version;
 std::uint32_t stageUnits;
 std::uint32_t leafUnits;
 std::uint64_t volumeSerial;
 unsigned char fileId[16];
 std::uint32_t creatorPid;
 std::uint64_t creatorStartTime;
 std::uint32_t checksum;
};
#pragma pack(pop)
constexpr char kMagic[8]={'F','L','Y','S','T','G','R','1'};
constexpr std::size_t kMaxRecord=75000;
std::uint32_t checksum(std::vector<unsigned char> const& data) noexcept {
 std::uint32_t hash=2166136261u;
 for(unsigned char b:data){hash^=b;hash*=16777619u;}
 return hash;
}
bool normalized(fs::path const& path,std::wstring const& original) {
 return !original.empty()&&original.size()<=32000&&
        original.find(L'\0')==std::wstring::npos&&
        path.is_absolute()&&path.has_root_directory()&&
        path.lexically_normal()==path&&path.native()==original;
}
bool fixedParent(fs::path const& path){
 const fs::path parent=path.parent_path();
 std::wstring root;
 if(!transferDriveRoot(path.native(),root)||
    ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)return false;
 fs::path current=parent.root_path();
 for(auto it=parent.begin();it!=parent.end();++it){
  if(*it==parent.root_name()||*it==parent.root_directory())continue;
  current/=*it;
  const DWORD flags=::GetFileAttributesW(current.c_str());
  if(flags==INVALID_FILE_ATTRIBUTES||
     (flags&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 }
 const DWORD flags=::GetFileAttributesW(parent.c_str());
 return flags!=INVALID_FILE_ATTRIBUTES&&
        (flags&FILE_ATTRIBUTE_DIRECTORY)!=0&&
        (flags&FILE_ATTRIBUTE_REPARSE_POINT)==0;
}
bool receiptLocation(std::wstring const& file,
                     std::wstring const& stage){
 const fs::path receipt(file),stageFile(stage);
 if(!normalized(receipt,file)||!normalized(stageFile,stage)||
    !fixedParent(receipt)||!fixedParent(stageFile))return false;
 const std::wstring leaf=stageFile.filename().native();
 const std::wstring prefix=L".flyExplorer-copy-";
 const std::wstring suffix=L".partial";
 if(leaf.size()!=prefix.size()+38+suffix.size()||
    leaf.compare(0,prefix.size(),prefix)!=0||
    leaf.compare(leaf.size()-suffix.size(),suffix.size(),suffix)!=0)
  return false;
 const std::wstring token=leaf.substr(prefix.size(),38);
 GUID guid{};wchar_t canonical[40]{};
 if(FAILED(::CLSIDFromString(token.c_str(),&guid))||
    !::StringFromGUID2(guid,canonical,40)||
    ::CompareStringOrdinal(token.c_str(),-1,canonical,-1,TRUE)!=CSTR_EQUAL)
  return false;
 return receipt.filename().native()==
        std::wstring(L".flyExplorer-receipt-")+token+L".bin";
}
bool validReceiptFile(HANDLE file){
 BY_HANDLE_FILE_INFORMATION information{};
 return ::GetFileInformationByHandle(file,&information)!=FALSE&&
   information.nNumberOfLinks==1&&
   !(information.dwFileAttributes&
     (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY));
}
std::uint64_t processStartTime(){
 FILETIME created{},exited{},kernel{},user{};
 if(!::GetProcessTimes(::GetCurrentProcess(),&created,&exited,&kernel,&user))
  return 0;
 ULARGE_INTEGER value{};
 value.LowPart=created.dwLowDateTime;
 value.HighPart=created.dwHighDateTime;
 return value.QuadPart;
}
bool validIdentity(StageFileIdentity const& identity){
 return std::any_of(identity.fileId.begin(),identity.fileId.end(),
                    [](unsigned char b){return b!=0;});
}
// Use a copy of the process token's SID. No global auth state or privileges.
bool currentUserSid(std::vector<unsigned char>& buffer,PSID& userSid) {
 userSid=nullptr;
 HANDLE token=nullptr;
 if(!::OpenProcessToken(::GetCurrentProcess(),TOKEN_QUERY,&token))
  return false;
 DWORD bytes=0;
 ::GetTokenInformation(token,TokenUser,nullptr,0,&bytes);
 bool success=false;
 if(bytes>=sizeof(TOKEN_USER)&&bytes<=65536){
  buffer.resize(bytes);
  success=::GetTokenInformation(token,TokenUser,buffer.data(),
                               bytes,&bytes)!=FALSE;
 }
 ::CloseHandle(token);
 if(!success)return false;
 auto* user=reinterpret_cast<TOKEN_USER*>(buffer.data());
 userSid=user->User.Sid;
 return userSid!=nullptr&&::IsValidSid(userSid)!=FALSE;
}
bool exactPrivateFolderPath(std::wstring const& path){
 const fs::path directory(path);
 if(!normalized(directory,path)||directory.filename().empty()||
    directory==directory.root_path())return false;
 return fixedParent(directory/fs::path(L"receipt-check"));
}
// Separate fixed-size, immutable evidence files are intentionally used
// instead of rewriting the v1 creator record during a transfer.
#pragma pack(push,1)
struct PhaseWire {
 char magic[8];
 std::uint32_t version;
 std::uint32_t phase;
 std::uint64_t volumeSerial;
 unsigned char fileId[16];
 std::uint32_t creatorPid;
 std::uint64_t creatorStartTime;
 std::uint32_t checksum;
};
#pragma pack(pop)
constexpr char kPhaseMagic[8]={'F','L','Y','P','H','A','S','1'};
enum class PhaseRead { Missing, Valid, Invalid };
std::wstring phasePath(std::wstring const& receiptPath,
                       std::uint32_t phase){
 return receiptPath+(phase==1?L".complete":L".published");
}
bool equalMarker(PhaseWire const& record,StageOwnershipReceipt const& receipt,
                 std::uint32_t phase){
 return std::memcmp(record.magic,kPhaseMagic,sizeof(kPhaseMagic))==0&&
  record.version==1&&record.phase==phase&&
  record.volumeSerial==receipt.stageIdentity.volumeSerial&&
  std::equal(std::begin(record.fileId),std::end(record.fileId),
             receipt.stageIdentity.fileId.begin())&&
  record.creatorPid==receipt.creatorPid&&
  record.creatorStartTime==receipt.creatorStartTime;
}
bool markerFileGone(std::wstring const& path){
 const DWORD a=::GetFileAttributesW(path.c_str());
 if(a!=INVALID_FILE_ATTRIBUTES)return false;
 const DWORD error=::GetLastError();
 return error==ERROR_FILE_NOT_FOUND||error==ERROR_PATH_NOT_FOUND;
}
bool exactRegularIdentity(std::wstring const& exactPath,
                          StageFileIdentity& id){
 id={};
 const fs::path path(exactPath);
 if(!normalized(path,exactPath)||!fixedParent(path)||
    !filecommand::validLeaf(path.filename().native()))return false;
 const HANDLE handle=::CreateFileW(exactPath.c_str(),
    FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
    nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
 if(handle==INVALID_HANDLE_VALUE)return false;
 BY_HANDLE_FILE_INFORMATION basic{};
 FILE_ID_INFO file{};
 const bool ok=::GetFileInformationByHandle(handle,&basic)!=FALSE&&
    ::GetFileInformationByHandleEx(handle,FileIdInfo,&file,sizeof(file))!=FALSE&&
    basic.nNumberOfLinks==1&&
    !(basic.dwFileAttributes&
      (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT));
 ::CloseHandle(handle);
 if(!ok)return false;
 id.volumeSerial=file.VolumeSerialNumber;
 std::copy(std::begin(file.FileId.Identifier),
           std::end(file.FileId.Identifier),id.fileId.begin());
 return validIdentity(id);
}
bool publishedTargetMatches(StageOwnershipReceipt const& receipt) {
 StageFileIdentity target{};
 const auto path=(fs::path(receipt.stagePath).parent_path()/
                  fs::path(receipt.targetLeaf)).native();
 return exactRegularIdentity(path,target)&&
        sameStageFile(receipt.stageIdentity,target)&&
        markerFileGone(receipt.stagePath);
}
PhaseRead readPhase(std::wstring const& exactReceiptPath,
                    StageOwnershipReceipt const& receipt,
                    std::uint32_t phase){
 const auto path=phasePath(exactReceiptPath,phase);
 if(path.size()>32000)return PhaseRead::Invalid;
 const HANDLE handle=::CreateFileW(path.c_str(),GENERIC_READ,
   FILE_SHARE_READ,nullptr,OPEN_EXISTING,
   FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
 if(handle==INVALID_HANDLE_VALUE){
  return ::GetLastError()==ERROR_FILE_NOT_FOUND?
         PhaseRead::Missing:PhaseRead::Invalid;
 }
 LARGE_INTEGER length{};
 PhaseWire marker{};
 DWORD read=0;
 const bool ok=validReceiptFile(handle)&&
      ::GetFileSizeEx(handle,&length)!=FALSE&&
      length.QuadPart==sizeof(marker)&&
      ::ReadFile(handle,&marker,sizeof(marker),&read,nullptr)!=FALSE&&
      read==sizeof(marker);
 ::CloseHandle(handle);
 if(!ok||!equalMarker(marker,receipt,phase))return PhaseRead::Invalid;
 const std::uint32_t saved=marker.checksum;
 marker.checksum=0;
 std::vector<unsigned char> raw(sizeof(marker));
 std::memcpy(raw.data(),&marker,sizeof(marker));
 return checksum(raw)==saved?PhaseRead::Valid:PhaseRead::Invalid;
}
bool writePhase(std::wstring const& exactReceiptPath,
                StageOwnershipReceipt const& receipt,
                std::uint32_t phase){
 const auto path=phasePath(exactReceiptPath,phase);
 if(path.size()>32000)return false;
 PhaseWire marker{};
 std::memcpy(marker.magic,kPhaseMagic,sizeof(kPhaseMagic));
 marker.version=1;
 marker.phase=phase;
 marker.volumeSerial=receipt.stageIdentity.volumeSerial;
 std::copy(receipt.stageIdentity.fileId.begin(),
           receipt.stageIdentity.fileId.end(),marker.fileId);
 marker.creatorPid=receipt.creatorPid;
 marker.creatorStartTime=receipt.creatorStartTime;
 std::vector<unsigned char> raw(sizeof(marker));
 std::memcpy(raw.data(),&marker,sizeof(marker));
 marker.checksum=checksum(raw);
 const HANDLE handle=::CreateFileW(path.c_str(),GENERIC_WRITE,
     0,nullptr,CREATE_NEW,
     FILE_ATTRIBUTE_NORMAL|FILE_FLAG_WRITE_THROUGH|FILE_FLAG_OPEN_REPARSE_POINT,
     nullptr);
 if(handle==INVALID_HANDLE_VALUE)return false;
 DWORD written=0;
 const bool ok=validReceiptFile(handle)&&
   ::WriteFile(handle,&marker,sizeof(marker),&written,nullptr)!=FALSE&&
   written==sizeof(marker)&&::FlushFileBuffers(handle)!=FALSE;
 ::CloseHandle(handle);
 return ok&&readPhase(exactReceiptPath,receipt,phase)==PhaseRead::Valid;
}
} // namespace

bool isPrivateStageReceiptDirectory(
    std::wstring const& exactDirectory) noexcept {
 try{
  if(!exactPrivateFolderPath(exactDirectory))return false;
  std::vector<unsigned char> token;
  PSID user=nullptr;
  if(!currentUserSid(token,user))return false;
  const HANDLE handle=::CreateFileW(exactDirectory.c_str(),
      READ_CONTROL|FILE_READ_ATTRIBUTES,
      FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
      nullptr,OPEN_EXISTING,
      FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(handle==INVALID_HANDLE_VALUE)return false;
  BY_HANDLE_FILE_INFORMATION attributes{};
  PSECURITY_DESCRIPTOR security=nullptr;
  PSID owner=nullptr;
  PACL acl=nullptr;
  const bool isDirectory=::GetFileInformationByHandle(
      handle,&attributes)!=FALSE&&
      (attributes.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)!=0&&
      (attributes.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)==0;
  const DWORD result=isDirectory?
      ::GetSecurityInfo(handle,SE_FILE_OBJECT,
          OWNER_SECURITY_INFORMATION|DACL_SECURITY_INFORMATION,
          &owner,nullptr,&acl,nullptr,&security):ERROR_INVALID_PARAMETER;
  ::CloseHandle(handle);
  bool safe=false;
  if(result==ERROR_SUCCESS&&security&&owner&&
     ::EqualSid(owner,user)&&acl&&::IsValidAcl(acl)&&
     acl->AceCount==1){
   SECURITY_DESCRIPTOR_CONTROL control{};
   DWORD revision=0;
   if(::GetSecurityDescriptorControl(security,&control,&revision)&&
      (control&SE_DACL_PROTECTED)){
    void* entry=nullptr;
    if(::GetAce(acl,0,&entry)){
     const auto* ace=static_cast<ACCESS_ALLOWED_ACE*>(entry);
     safe=ace->Header.AceType==ACCESS_ALLOWED_ACE_TYPE&&
         !(ace->Header.AceFlags&INHERITED_ACE)&&
         (ace->Header.AceFlags&
            (OBJECT_INHERIT_ACE|CONTAINER_INHERIT_ACE))==
            (OBJECT_INHERIT_ACE|CONTAINER_INHERIT_ACE)&&
         (ace->Mask&FILE_ALL_ACCESS)==FILE_ALL_ACCESS&&
         ::IsValidSid(const_cast<DWORD*>(&ace->SidStart))&&
         ::EqualSid(const_cast<DWORD*>(&ace->SidStart),user);
    }
   }
  }
  if(security)::LocalFree(security);
  return safe;
 }catch(...){return false;}
}
bool createPrivateStageReceiptDirectory(
    std::wstring const& exactDirectory) noexcept {
 try{
  const fs::path folder(exactDirectory);
  if(!normalized(folder,exactDirectory)||folder.filename().empty()||
     !fixedParent(folder))return false;
  std::vector<unsigned char> token;
  PSID user=nullptr;
  if(!currentUserSid(token,user))return false;
  LPWSTR sidText=nullptr;
  if(!::ConvertSidToStringSidW(user,&sidText)||!sidText)return false;
  const std::wstring sddl=L"O:"+std::wstring(sidText)+
      L"D:P(A;OICI;FA;;;"+std::wstring(sidText)+L")";
  ::LocalFree(sidText);
  PSECURITY_DESCRIPTOR security=nullptr;
  if(!::ConvertStringSecurityDescriptorToSecurityDescriptorW(
      sddl.c_str(),SDDL_REVISION_1,&security,nullptr)||!security)
   return false;
  SECURITY_ATTRIBUTES attributes{sizeof(SECURITY_ATTRIBUTES),security,FALSE};
  // No open-if-exists, no ACL reset; report a pre-existing path as failure.
  const bool created=::CreateDirectoryW(
      exactDirectory.c_str(),&attributes)!=FALSE;
  ::LocalFree(security);
  return created&&isPrivateStageReceiptDirectory(exactDirectory);
 }catch(...){return false;}
}

bool prepareUserStageReceiptDirectory(
    std::wstring& exactDirectory) noexcept {
 exactDirectory.clear();
 try{
  PWSTR raw=nullptr;
  if(FAILED(::SHGetKnownFolderPath(FOLDERID_LocalAppData,0,nullptr,&raw))||
     !raw)return false;
  const std::wstring base(raw);
  ::CoTaskMemFree(raw);
  const fs::path folder=fs::path(base)/L"flyExplorer-transfer-receipts-v1";
  const std::wstring path=folder.native();
  if(!normalized(fs::path(base),base)||!fixedParent(folder))
   return false;
  const DWORD attrs=::GetFileAttributesW(path.c_str());
  if(attrs==INVALID_FILE_ATTRIBUTES){
   if(::GetLastError()!=ERROR_FILE_NOT_FOUND||
      !createPrivateStageReceiptDirectory(path))return false;
  }
  if(!isPrivateStageReceiptDirectory(path))return false;
  exactDirectory=path;
  return true;
 }catch(...){exactDirectory.clear();return false;}
}

bool writeBoundStageReceipt(std::wstring const& exactReceiptPath,
                            std::wstring const& exactStagePath,
                            std::wstring const& targetLeaf,
                            HANDLE copyDestination) noexcept {
 if(!copyDestination||copyDestination==INVALID_HANDLE_VALUE)return false;
 BY_HANDLE_FILE_INFORMATION info{};
 FILE_ID_INFO handleId{};
 if(!::GetFileInformationByHandle(copyDestination,&info)||
    (info.dwFileAttributes&
        (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))||
    info.nNumberOfLinks!=1||
    !::GetFileInformationByHandleEx(copyDestination,FileIdInfo,
                                   &handleId,sizeof(handleId)))return false;
 StageFileIdentity fromHandle{};
 fromHandle.volumeSerial=handleId.VolumeSerialNumber;
 std::copy(std::begin(handleId.FileId.Identifier),
           std::end(handleId.FileId.Identifier),
           fromHandle.fileId.begin());
 StageFileIdentity atPath{};
 if(!inspectStageFile(exactStagePath,atPath)||
    !sameStageFile(atPath,fromHandle))return false;
 // A failed write is not a recoverable receipt. Never remove the stage.
 if(!writeStageReceipt(exactReceiptPath,exactStagePath,targetLeaf))
  return false;
 StageOwnershipReceipt persisted{};
 return readStageReceipt(exactReceiptPath,persisted)&&
        persisted.stagePath==exactStagePath&&
        persisted.targetLeaf==targetLeaf&&
        sameStageFile(persisted.stageIdentity,fromHandle)&&
        receiptMatchesStage(persisted);
}

bool writeStageReceipt(std::wstring const& exactReceiptPath,
                       std::wstring const& exactStagePath,
                       std::wstring const& targetLeaf) noexcept {
 try{
  StageFileIdentity stage{};
  if(!receiptLocation(exactReceiptPath,exactStagePath)||
     !isPrivateStageReceiptDirectory(
         fs::path(exactReceiptPath).parent_path().native())||
     !filecommand::validLeaf(targetLeaf)||targetLeaf.size()>255||
     !inspectStageFile(exactStagePath,stage))return false;
  const auto started=processStartTime();
  if(started==0)return false;
  ReceiptWire header{};
  std::memcpy(header.magic,kMagic,sizeof(kMagic));
  header.version=1;
  header.stageUnits=static_cast<std::uint32_t>(exactStagePath.size());
  header.leafUnits=static_cast<std::uint32_t>(targetLeaf.size());
  header.volumeSerial=stage.volumeSerial;
  std::copy(stage.fileId.begin(),stage.fileId.end(),header.fileId);
  header.creatorPid=::GetCurrentProcessId();
  header.creatorStartTime=started;
  const std::size_t bytes=sizeof(header)+
       (exactStagePath.size()+targetLeaf.size())*sizeof(wchar_t);
  if(bytes>kMaxRecord)return false;
  std::vector<unsigned char> raw(bytes);
  std::memcpy(raw.data(),&header,sizeof(header));
  auto offset=sizeof(header);
  std::memcpy(raw.data()+offset,exactStagePath.data(),
              exactStagePath.size()*sizeof(wchar_t));
  offset+=exactStagePath.size()*sizeof(wchar_t);
  std::memcpy(raw.data()+offset,targetLeaf.data(),
              targetLeaf.size()*sizeof(wchar_t));
  header.checksum=checksum(raw);
  std::memcpy(raw.data(),&header,sizeof(header));
  // CREATE_NEW: never overwrite any existing record, even an invalid one.
  const HANDLE handle=::CreateFileW(exactReceiptPath.c_str(),GENERIC_WRITE,
       0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL|
       FILE_FLAG_WRITE_THROUGH|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(handle==INVALID_HANDLE_VALUE)return false;
  DWORD written=0;
  const bool success=validReceiptFile(handle)&&
       ::WriteFile(handle,raw.data(),static_cast<DWORD>(raw.size()),
                   &written,nullptr)!=FALSE&&
       written==raw.size()&&::FlushFileBuffers(handle)!=FALSE;
  ::CloseHandle(handle);
  // Leave any failed/incomplete record untouched for manual examination.
  return success;
 }catch(...){return false;}
}
bool readStageReceipt(std::wstring const& exactReceiptPath,
                      StageOwnershipReceipt& receipt) noexcept {
 receipt={};
 try{
  const fs::path file(exactReceiptPath);
  if(!normalized(file,exactReceiptPath)||!fixedParent(file)||
     !isPrivateStageReceiptDirectory(file.parent_path().native()))
   return false;
  const HANDLE handle=::CreateFileW(exactReceiptPath.c_str(),GENERIC_READ,
       FILE_SHARE_READ,nullptr,OPEN_EXISTING,
       FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
  if(handle==INVALID_HANDLE_VALUE)return false;
  LARGE_INTEGER length{};
  const bool usable=validReceiptFile(handle)&&
     ::GetFileSizeEx(handle,&length)!=FALSE&&
     length.QuadPart>=static_cast<LONGLONG>(sizeof(ReceiptWire))&&
     length.QuadPart<=static_cast<LONGLONG>(kMaxRecord);
  std::vector<unsigned char> raw;
  bool read=false;
  if(usable){
   raw.resize(static_cast<std::size_t>(length.QuadPart));
   DWORD count=0;
   read=::ReadFile(handle,raw.data(),static_cast<DWORD>(raw.size()),
                   &count,nullptr)!=FALSE&&count==raw.size();
  }
  ::CloseHandle(handle);
  if(!read)return false;
  ReceiptWire header{};
  std::memcpy(&header,raw.data(),sizeof(header));
  if(std::memcmp(header.magic,kMagic,sizeof(kMagic))!=0||
     header.version!=1||!header.stageUnits||
     header.stageUnits>32000||!header.leafUnits||header.leafUnits>255||
     sizeof(header)+
        (static_cast<std::size_t>(header.stageUnits)+header.leafUnits)*
        sizeof(wchar_t)!=raw.size()||
     header.creatorPid==0||header.creatorStartTime==0)return false;
  const auto savedChecksum=header.checksum;
  header.checksum=0;
  std::memcpy(raw.data(),&header,sizeof(header));
  if(checksum(raw)!=savedChecksum)return false;
  const auto* pathData=raw.data()+sizeof(header);
  const auto* leafData=pathData+
          static_cast<std::size_t>(header.stageUnits)*sizeof(wchar_t);
  std::wstring stage(header.stageUnits,L'\0'),leaf(header.leafUnits,L'\0');
  std::memcpy(stage.data(),pathData,
              static_cast<std::size_t>(header.stageUnits)*sizeof(wchar_t));
  std::memcpy(leaf.data(),leafData,
              static_cast<std::size_t>(header.leafUnits)*sizeof(wchar_t));
  if(!receiptLocation(exactReceiptPath,stage)||
     !filecommand::validLeaf(leaf))return false;
  StageOwnershipReceipt candidate{};
  candidate.stagePath=std::move(stage);
  candidate.targetLeaf=std::move(leaf);
  candidate.stageIdentity.volumeSerial=header.volumeSerial;
  std::copy(std::begin(header.fileId),std::end(header.fileId),
            candidate.stageIdentity.fileId.begin());
  candidate.creatorPid=header.creatorPid;
  candidate.creatorStartTime=header.creatorStartTime;
  if(!validIdentity(candidate.stageIdentity))return false;
  receipt=std::move(candidate);
  return true;
 }catch(...){receipt={};return false;}
}
bool markStageCopyCompleted(
    std::wstring const& exactReceiptPath) noexcept {
 try{
  StageOwnershipReceipt receipt{};
  return readStageReceipt(exactReceiptPath,receipt)&&
    receiptMatchesStage(receipt)&&
    readPhase(exactReceiptPath,receipt,1)==PhaseRead::Missing&&
    readPhase(exactReceiptPath,receipt,2)==PhaseRead::Missing&&
    writePhase(exactReceiptPath,receipt,1);
 }catch(...){return false;}
}
bool markStageCopyPublished(
    std::wstring const& exactReceiptPath) noexcept {
 try{
  StageOwnershipReceipt receipt{};
  return readStageReceipt(exactReceiptPath,receipt)&&
    readPhase(exactReceiptPath,receipt,1)==PhaseRead::Valid&&
    readPhase(exactReceiptPath,receipt,2)==PhaseRead::Missing&&
    publishedTargetMatches(receipt)&&
    writePhase(exactReceiptPath,receipt,2);
 }catch(...){return false;}
}
StageReceiptState inspectStageReceiptState(
    std::wstring const& exactReceiptPath) noexcept {
 try{
  StageOwnershipReceipt receipt{};
  if(!readStageReceipt(exactReceiptPath,receipt))
   return StageReceiptState::Invalid;
  const auto complete=readPhase(exactReceiptPath,receipt,1);
  const auto published=readPhase(exactReceiptPath,receipt,2);
  if(complete==PhaseRead::Invalid||published==PhaseRead::Invalid||
     (published==PhaseRead::Valid&&complete!=PhaseRead::Valid))
   return StageReceiptState::Inconsistent;
  const bool stageMatches=receiptMatchesStage(receipt);
  const bool finalMatches=publishedTargetMatches(receipt);
  if(published==PhaseRead::Valid)
   return finalMatches?StageReceiptState::PublishedVerified:
                       StageReceiptState::Inconsistent;
  if(complete==PhaseRead::Valid){
   if(stageMatches)return StageReceiptState::CompletedOnStage;
   return finalMatches?StageReceiptState::PublicationUnconfirmed:
                       StageReceiptState::Inconsistent;
  }
  return stageMatches?StageReceiptState::CopyingOrInterrupted:
                       StageReceiptState::Inconsistent;
 }catch(...){return StageReceiptState::Invalid;}
}
ReceiptCreatorState inspectReceiptCreator(
    StageOwnershipReceipt const& receipt) noexcept {
 if(receipt.creatorPid==0||receipt.creatorStartTime==0)
  return ReceiptCreatorState::Unknown;
 const HANDLE process=::OpenProcess(
     PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE,FALSE,
     receipt.creatorPid);
 if(process==nullptr)return ReceiptCreatorState::Unknown;
 FILETIME creation{},exit{},kernel{},user{};
 const bool inspected=::GetProcessTimes(
     process,&creation,&exit,&kernel,&user)!=FALSE;
 ULARGE_INTEGER start{};
 start.LowPart=creation.dwLowDateTime;
 start.HighPart=creation.dwHighDateTime;
 ReceiptCreatorState result=ReceiptCreatorState::Unknown;
 if(inspected&&start.QuadPart==receipt.creatorStartTime){
  const DWORD observed=::WaitForSingleObject(process,0);
  if(observed==WAIT_TIMEOUT)result=ReceiptCreatorState::Running;
  else if(observed==WAIT_OBJECT_0)result=ReceiptCreatorState::Exited;
 }
 ::CloseHandle(process);
 return result;
}

bool receiptMatchesStage(StageOwnershipReceipt const& receipt) noexcept {
 StageFileIdentity current{};
 return inspectStageFile(receipt.stagePath,current)&&
        sameStageFile(receipt.stageIdentity,current);
}
} // namespace fxfile::shelltransfer
