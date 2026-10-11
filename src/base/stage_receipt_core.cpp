#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include "stage_receipt_core.h"
#include <objbase.h>
#include "file_command_core.h"
#include <filesystem>
#include <algorithm>
#include <cstring>
#include <iterator>
#include <utility>
#include <vector>

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
} // namespace

bool writeStageReceipt(std::wstring const& exactReceiptPath,
                       std::wstring const& exactStagePath,
                       std::wstring const& targetLeaf) noexcept {
 try{
  StageFileIdentity stage{};
  if(!receiptLocation(exactReceiptPath,exactStagePath)||
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
  if(!normalized(file,exactReceiptPath)||!fixedParent(file))
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
bool receiptMatchesStage(StageOwnershipReceipt const& receipt) noexcept {
 StageFileIdentity current{};
 return inspectStageFile(receipt.stagePath,current)&&
        sameStageFile(receipt.stageIdentity,current);
}
} // namespace fxfile::shelltransfer
