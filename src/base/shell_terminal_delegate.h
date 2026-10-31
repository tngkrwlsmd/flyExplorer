// Windows Terminal handoff, exclusively for a user-requested local folder.
// No cmd.exe/PowerShell script, command string evaluation, or file changes.
#pragma once
#include <windows.h>
#include <shlobj.h>
#include <shobjidl_core.h>
#include <shellapi.h>
#include <filesystem>
#include <string>

namespace fxfile::shellterminal {
namespace detail {
struct Apartment final {
 bool ready=false;
 ~Apartment() noexcept {if(ready)::CoUninitialize();}
};
struct KnownFolderPath final {
 PWSTR path=nullptr;
 ~KnownFolderPath() noexcept {if(path)::CoTaskMemFree(path);}
};
struct ActivationManager final {
 IApplicationActivationManager* value=nullptr;
 ~ActivationManager() noexcept {if(value)value->Release();}
};
}
inline HRESULT openFolder(std::wstring const& folder) noexcept {
 try {
  if(folder.size()<3||folder.size()>1024||
     folder.find_first_of(L";\r\n\"")!=std::wstring::npos||
     folder.find(L'\0')!=std::wstring::npos)return E_INVALIDARG;
  const auto drive=folder[0];
  if(!((drive>=L'A'&&drive<=L'Z')||(drive>=L'a'&&drive<=L'z'))||
     folder[1]!=L':'||folder[2]!=L'\\')return E_INVALIDARG;
  const std::filesystem::path path(folder);
  if(!path.is_absolute()||path.lexically_normal().native()!=folder)
   return E_INVALIDARG;
  const auto root=path.root_path().native();
  if(root.size()!=3||::GetDriveTypeW(root.c_str())!=DRIVE_FIXED)
   return HRESULT_FROM_WIN32(ERROR_NOT_SUPPORTED);
  const DWORD attributes=::GetFileAttributesW(folder.c_str());
  if(attributes==INVALID_FILE_ATTRIBUTES||
     !(attributes&FILE_ATTRIBUTE_DIRECTORY)||
     (attributes&FILE_ATTRIBUTE_REPARSE_POINT))
   return HRESULT_FROM_WIN32(ERROR_PATH_NOT_FOUND);
  const HRESULT apartment=::CoInitializeEx(
   nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
  if(FAILED(apartment))return apartment;
  detail::Apartment initialized{true};
  detail::KnownFolderPath known;
  const HRESULT result=::SHGetKnownFolderPath(
   FOLDERID_LocalAppData,KF_FLAG_DEFAULT,nullptr,&known.path);
  if(FAILED(result)||!known.path)return FAILED(result)?result:E_FAIL;
  // A full per-user App Execution Alias avoids searching the selected folder
  // for a malicious program named wt.exe.
  std::wstring executable=known.path;
  executable+=L"\\Microsoft\\WindowsApps\\wt.exe";
  // Force a distinct window. The path is one quoted -d argument, not shell
  // code; trailing backslashes must not escape the closing argument quote.
  std::wstring arguments=L"-w new new-tab -d \""+folder;
  if(folder.back()==L'\\')arguments+=L"\\";
  arguments+=L"\"";
  const DWORD alias=::GetFileAttributesW(executable.c_str());
  if(alias==INVALID_FILE_ATTRIBUTES||(alias&FILE_ATTRIBUTE_DIRECTORY)){
   // The Store package may be installed while its per-user wt.exe execution
   // alias is disabled. Activate the signed package through the public
   // Windows app-activation API; never search PATH or invoke a command shell.
   detail::ActivationManager manager;
   const HRESULT created=::CoCreateInstance(
    CLSID_ApplicationActivationManager,nullptr,CLSCTX_INPROC_SERVER,
    IID_PPV_ARGS(&manager.value));
   if(FAILED(created))return created;
   DWORD processId=0;
   const HRESULT activated=manager.value->ActivateApplication(
    L"Microsoft.WindowsTerminal_8wekyb3d8bbwe!App",
    arguments.c_str(),AO_NONE,&processId);
   return SUCCEEDED(activated)&&!processId?E_FAIL:activated;
  }
  SHELLEXECUTEINFOW request{};
  request.cbSize=sizeof(request);
  request.fMask=SEE_MASK_FLAG_NO_UI|SEE_MASK_NOASYNC;
  request.lpVerb=L"open";
  request.lpFile=executable.c_str();
  request.lpParameters=arguments.c_str();
  request.lpDirectory=folder.c_str();
  request.nShow=SW_SHOWNORMAL;
  if(::ShellExecuteExW(&request))return S_OK;
  const DWORD error=::GetLastError();
  return error?HRESULT_FROM_WIN32(error):E_FAIL;
 }catch(...){return E_FAIL;}
}
} // namespace fxfile::shellterminal
