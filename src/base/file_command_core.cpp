#define WIN32_LEAN_AND_MEAN
#include "file_command_core.h"
#include <filesystem>
#include <cwctype>
namespace fxfile::filecommand {
bool validLeaf(std::wstring const& name) noexcept{
 if(name.empty()||name.size()>240||name==L"."||name==L".."||
    name.back()==L'.'||name.back()==L' ')return false;
 for(wchar_t ch:name)
  if(ch<32||ch==L'/'||ch==L'\\'||ch==L':'||ch==L'*'||ch==L'?'||
     ch==L'"'||ch==L'<'||ch==L'>'||ch==L'|')return false;
 std::wstring stem=name.substr(0,name.find(L'.'));
 for(auto& ch:stem)ch=static_cast<wchar_t>(std::towupper(ch));
 if(stem==L"CON"||stem==L"PRN"||stem==L"AUX"||stem==L"NUL")return false;
 if(stem.size()==4&&((stem.substr(0,3)==L"COM")||
                      (stem.substr(0,3)==L"LPT"))&&
    stem[3]>=L'1'&&stem[3]<=L'9')return false;
 return true;
}
bool validTextDocumentLeaf(std::wstring const& name) noexcept{
 return validLeaf(name)&&name.size()>4&&
  ::CompareStringOrdinal(name.c_str()+name.size()-4,4,L".txt",4,TRUE)==CSTR_EQUAL;
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
  if(task.kind==Kind::CreateTextFile){
   if(!validTextDocumentLeaf(task.name)){
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
  if(task.kind!=Kind::RenameSelected){result.error=ERROR_INVALID_PARAMETER;return result;}
  std::filesystem::path src(task.source);
  if(!src.is_absolute()||
     src.lexically_normal().parent_path()!=folder||
     !validLeaf(src.filename().native())){
   result.error=ERROR_INVALID_NAME;return result;
  }
  if(::CompareStringOrdinal(src.c_str(),-1,target.c_str(),-1,TRUE)==CSTR_EQUAL){
   result.error=ERROR_ALREADY_EXISTS;return result;
  }
  // Native MoveFileW never overwrites an existing destination.
  if(::MoveFileW(src.c_str(),target.c_str()))result.error=ERROR_SUCCESS;
  else result.error=::GetLastError();
 }catch(...){result.error=ERROR_INVALID_PARAMETER;}
 return result;
}
}
