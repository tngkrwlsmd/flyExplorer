#include <windows.h>
#include <commctrl.h>
#include <shellapi.h>
#include <shlobj.h>
#include <shobjidl.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cwctype>
#include <cstring>
#include "product_version.h"
#include "payload_manifest.h"

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "advapi32.lib")

namespace fs=std::filesystem;
namespace {
constexpr wchar_t kDisplayName[]=L"flyExplorer";
constexpr wchar_t kPublisher[]=L"Leon Lee";
constexpr wchar_t kUninstallKey[]=L"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\flyExplorer";
constexpr wchar_t kTestUninstallKey[]=L"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\flyExplorer-InstallerTest";
constexpr wchar_t kUninstaller[]=L"flyExplorerUninstall.exe";
constexpr wchar_t kManifest[]=L"install-manifest.txt";

struct Options {
    bool silent=false;
    bool uninstall=false;
    bool purgeUserData=false;
    bool desktop=false;
    std::wstring testRoot;
    std::wstring testDisplayVersion;
};

std::wstring lower(std::wstring value) {
    std::transform(value.begin(),value.end(),value.begin(),
        [](wchar_t c){return static_cast<wchar_t>(std::towlower(c));});
    return value;
}
bool eq(std::wstring const& a,wchar_t const* b){return lower(a)==lower(b);}
bool starts(std::wstring const& a,wchar_t const* b){
    const auto la=lower(a),lb=lower(std::wstring(b));
    return la.rfind(lb,0)==0;
}
std::wstring selfPath(){
    std::vector<wchar_t> b(32768);
    const DWORD n=GetModuleFileNameW(nullptr,b.data(),static_cast<DWORD>(b.size()));
    return n&&n<b.size()?std::wstring(b.data(),n):L"";
}
std::wstring quote(std::wstring const& v){
    std::wstring out=L"\"";
    for(auto c:v){if(c==L'"')out+=L'\\';out+=c;}
    out+=L'"';return out;
}

Options optionsFromCommandLine(){
    Options o;
    int argc=0;
    auto argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(!argv)return o;
    for(int i=1;i<argc;++i){
        std::wstring a=argv[i];
        if(eq(a,L"/S")||eq(a,L"/SILENT"))o.silent=true;
        else if(eq(a,L"/UNINSTALL"))o.uninstall=true;
        else if(eq(a,L"/PURGEUSERDATA"))o.purgeUserData=true;
        else if(eq(a,L"/DESKTOP"))o.desktop=true;
        else if(eq(a,L"/NODESKTOP"))o.desktop=false;
        else if(starts(a,L"/TESTROOT="))o.testRoot=a.substr(10);
        else if(starts(a,L"/TESTDISPLAYVERSION="))o.testDisplayVersion=a.substr(20);
    }
    LocalFree(argv);
    return o;
}

bool isAdmin(){
    BOOL member=FALSE;
    SID_IDENTIFIER_AUTHORITY authority=SECURITY_NT_AUTHORITY;
    PSID sid=nullptr;
    if(AllocateAndInitializeSid(&authority,2,SECURITY_BUILTIN_DOMAIN_RID,
        DOMAIN_ALIAS_RID_ADMINS,0,0,0,0,0,0,&sid)){
        CheckTokenMembership(nullptr,sid,&member);
        FreeSid(sid);
    }
    return member!=FALSE;
}
int elevateAndWait(){
    const auto exe=selfPath();
    if(exe.empty())return ERROR_FILE_NOT_FOUND;
    int argc=0;auto argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(!argv)return ERROR_INVALID_PARAMETER;
    std::wstring params;
    for(int i=1;i<argc;++i){if(!params.empty())params+=L" ";params+=quote(argv[i]);}
    LocalFree(argv);
    SHELLEXECUTEINFOW sei{sizeof(sei)};
    sei.fMask=SEE_MASK_NOCLOSEPROCESS;
    sei.lpVerb=L"runas";sei.lpFile=exe.c_str();sei.lpParameters=params.c_str();
    sei.nShow=SW_SHOWNORMAL;
    if(!ShellExecuteExW(&sei))return static_cast<int>(GetLastError());
    WaitForSingleObject(sei.hProcess,INFINITE);
    DWORD code=1;GetExitCodeProcess(sei.hProcess,&code);CloseHandle(sei.hProcess);
    return static_cast<int>(code);
}

bool safeTestRoot(std::wstring const& raw,fs::path& result){
    if(raw.empty())return false;
    std::error_code ec;
    auto p=fs::absolute(fs::path(raw),ec).lexically_normal();
    if(ec||!p.has_parent_path()||p==p.root_path())return false;
    auto text=lower(p.native());
    if(text.find(L"flyexplorer-installer-test-")==std::wstring::npos)return false;
    result=p;return true;
}
fs::path knownFolder(REFKNOWNFOLDERID id){
    PWSTR value=nullptr;
    if(FAILED(SHGetKnownFolderPath(id,KF_FLAG_DEFAULT,nullptr,&value)))return {};
    fs::path p(value);CoTaskMemFree(value);return p;
}
fs::path installRoot(Options const& o){
    if(!o.testRoot.empty()){fs::path p;if(safeTestRoot(o.testRoot,p))return p;return {};}
    auto programFiles=knownFolder(FOLDERID_ProgramFiles);
    return programFiles.empty()?fs::path{}:programFiles/L"flyExplorer";
}

bool writeBytes(fs::path const& path,void const* data,DWORD bytes){
    std::error_code ec;fs::create_directories(path.parent_path(),ec);if(ec)return false;
    HANDLE h=CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,
                         FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    DWORD written=0;
    const bool ok=WriteFile(h,data,bytes,&written,nullptr)!=FALSE&&written==bytes&&
                  FlushFileBuffers(h)!=FALSE;
    CloseHandle(h);return ok;
}
bool extractPayload(fs::path const& root){
    auto module=GetModuleHandleW(nullptr);
    for(auto const& file:kPayloadFiles){
        HRSRC resource=FindResourceW(module,MAKEINTRESOURCEW(file.resourceId),RT_RCDATA);
        if(!resource)return false;
        DWORD size=SizeofResource(module,resource);
        if(size!=file.bytes)return false;
        HGLOBAL loaded=LoadResource(module,resource);if(!loaded)return false;
        void* data=LockResource(loaded);if(!data&&size)return false;
        if(!writeBytes(root/file.relativePath,data,size))return false;
    }
    return true;
}

std::string utf8(std::wstring const& value){
    if(value.empty())return {};
    const int n=WideCharToMultiByte(CP_UTF8,0,value.data(),static_cast<int>(value.size()),
                                   nullptr,0,nullptr,nullptr);
    std::string out(n,'\0');
    WideCharToMultiByte(CP_UTF8,0,value.data(),static_cast<int>(value.size()),
                        out.data(),n,nullptr,nullptr);
    return out;
}
std::wstring wide(std::string const& value){
    if(value.empty())return {};
    const int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),
                                    static_cast<int>(value.size()),nullptr,0);
    if(n<=0)return {};
    std::wstring out(n,L'\0');
    MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.data(),
                        static_cast<int>(value.size()),out.data(),n);
    return out;
}
bool safeRelative(fs::path const& rel){
    if(rel.empty()||rel.is_absolute()||rel.has_root_path())return false;
    for(auto const& part:rel)if(part==L".."||part==L".")return false;
    return true;
}
bool writeInstallManifest(fs::path const& root){
    std::ofstream out(root/kManifest,std::ios::binary|std::ios::trunc);
    if(!out)return false;
    for(auto const& file:kPayloadFiles)out<<utf8(file.relativePath)<<"\r\n";
    return out.good();
}
bool reparsePoint(fs::path const& path){
    const auto attributes=GetFileAttributesW(path.c_str());
    return attributes!=INVALID_FILE_ATTRIBUTES &&
        (attributes&FILE_ATTRIBUTE_REPARSE_POINT)!=0;
}
bool safeManifestTarget(fs::path const& root,fs::path const& relative){
    if(!safeRelative(relative)||reparsePoint(root))return false;
    auto cursor=root;
    for(auto const& part:relative){
        cursor/=part;
        if(reparsePoint(cursor))return false;
    }
    return true;
}
void removeEmptyParents(fs::path parent,fs::path const& root){
    std::error_code ec;
    while(parent!=root&&parent.native().size()>root.native().size()){
        if(!fs::remove(parent,ec))break;
        parent=parent.parent_path();
    }
}
bool removeInstalledPayload(fs::path const& root){
    std::error_code ec;
    if(!fs::exists(root/kManifest,ec))return !ec;
    if(ec||reparsePoint(root/kManifest))return false;
    std::ifstream in(root/kManifest,std::ios::binary);
    if(!in)return false;
    std::vector<fs::path> paths;
    std::string line;
    while(std::getline(in,line)){
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        fs::path relative=wide(line);
        if(!safeManifestTarget(root,relative))return false;
        paths.push_back(relative);
    }
    if(in.bad())return false;
    bool ok=true;
    for(auto it=paths.rbegin();it!=paths.rend();++it){
        const auto target=root/(*it);
        ec.clear();
        fs::remove(target,ec);
        if(ec)ok=false;
        removeEmptyParents(target.parent_path(),root);
    }
    return ok;
}

HRESULT createLink(fs::path const& link,fs::path const& target,fs::path const& work){
    std::error_code ec;fs::create_directories(link.parent_path(),ec);if(ec)return E_FAIL;
    IShellLinkW* shell=nullptr;
    HRESULT hr=CoCreateInstance(CLSID_ShellLink,nullptr,CLSCTX_INPROC_SERVER,
                                IID_PPV_ARGS(&shell));
    if(FAILED(hr))return hr;
    shell->SetPath(target.c_str());shell->SetWorkingDirectory(work.c_str());
    shell->SetIconLocation(target.c_str(),0);
    IPersistFile* persist=nullptr;hr=shell->QueryInterface(IID_PPV_ARGS(&persist));
    if(SUCCEEDED(hr)){hr=persist->Save(link.c_str(),TRUE);persist->Release();}
    shell->Release();return hr;
}
struct ShortcutPaths{fs::path startMenu;fs::path desktop;};
ShortcutPaths shortcutPaths(Options const& o,fs::path const& root){
    if(!o.testRoot.empty()){
        return {root/L"_installer_shortcuts"/L"StartMenu"/L"flyExplorer.lnk",
                root/L"_installer_shortcuts"/L"Desktop"/L"flyExplorer.lnk"};
    }
    auto start=knownFolder(FOLDERID_CommonPrograms)/L"flyExplorer"/L"flyExplorer.lnk";
    auto desktop=knownFolder(FOLDERID_Desktop)/L"flyExplorer.lnk";
    return {start,desktop};
}
bool removeShortcuts(Options const& o,fs::path const& root){
    auto p=shortcutPaths(o,root);
    std::error_code ec;
    bool ok=true;
    for(auto const& path:{p.startMenu,p.desktop}){
        ec.clear();
        fs::remove(path,ec);
        if(ec)ok=false;
    }
    if(!o.testRoot.empty()){
        const auto shortcutRoot=root/L"_installer_shortcuts";
        if(reparsePoint(shortcutRoot))return false;
        ec.clear();
        fs::remove_all(shortcutRoot,ec);
        if(ec)ok=false;
    }else{
        ec.clear();
        fs::remove(p.startMenu.parent_path(),ec);
        if(ec)ok=false;
    }
    return ok;
}

bool createShortcuts(Options const& o,fs::path const& root){
    HRESULT init=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
    const bool uninit=SUCCEEDED(init);
    auto p=shortcutPaths(o,root);
    auto exe=root/L"flyExplorer.exe";
    bool ok=SUCCEEDED(createLink(p.startMenu,exe,root));
    if(ok&&o.desktop)ok=SUCCEEDED(createLink(p.desktop,exe,root));
    if(uninit)CoUninitialize();
    return ok;
}

HKEY registryRoot(Options const& o){return o.testRoot.empty()?HKEY_LOCAL_MACHINE:HKEY_CURRENT_USER;}
wchar_t const* registryPath(Options const& o){return o.testRoot.empty()?kUninstallKey:kTestUninstallKey;}
bool setString(HKEY key,wchar_t const* name,std::wstring const& value){
    return RegSetValueExW(key,name,0,REG_SZ,reinterpret_cast<BYTE const*>(value.c_str()),
           static_cast<DWORD>((value.size()+1)*sizeof(wchar_t)))==ERROR_SUCCESS;
}
bool setDword(HKEY key,wchar_t const* name,DWORD value){
    return RegSetValueExW(key,name,0,REG_DWORD,reinterpret_cast<BYTE*>(&value),sizeof(value))==ERROR_SUCCESS;
}
std::wstring effectiveVersion(Options const& o){
    if(!o.testRoot.empty()&&!o.testDisplayVersion.empty())return o.testDisplayVersion;
    std::string source=FLYEXPLORER_VERSION_STRING;
    return wide(source);
}
bool registerUninstall(Options const& o,fs::path const& root){
    HKEY key=nullptr;
    REGSAM access=KEY_SET_VALUE;
    if(o.testRoot.empty())access|=KEY_WOW64_64KEY;
    if(RegCreateKeyExW(registryRoot(o),registryPath(o),0,nullptr,0,access,nullptr,&key,nullptr)!=ERROR_SUCCESS)
        return false;
    auto uninstaller=root/kUninstaller;
    std::wstring uninstallArgs=L" /UNINSTALL";
    if(!o.testRoot.empty())uninstallArgs+=L" /TESTROOT="+quote(root.native());
    std::wstring quietArgs=uninstallArgs+L" /S";
    std::wstring command=quote(uninstaller.native())+uninstallArgs;
    std::wstring quietCommand=quote(uninstaller.native())+quietArgs;
    const DWORD kb=static_cast<DWORD>((kPayloadBytes+1023)/1024);
    SYSTEMTIME now{};GetLocalTime(&now);
    wchar_t date[9]{};swprintf_s(date,L"%04u%02u%02u",now.wYear,now.wMonth,now.wDay);
    bool ok=
      setString(key,L"DisplayName",kDisplayName)&&
      setString(key,L"DisplayVersion",effectiveVersion(o))&&
      setString(key,L"Publisher",kPublisher)&&
      setString(key,L"InstallLocation",root.native())&&
      setString(key,L"DisplayIcon",(root/L"flyExplorer.exe").native())&&
      setString(key,L"UninstallString",command)&&
      setString(key,L"QuietUninstallString",quietCommand)&&
      setString(key,L"InstallDate",date)&&
      setDword(key,L"EstimatedSize",kb)&&
      setDword(key,L"NoModify",1)&&setDword(key,L"NoRepair",1);
    RegCloseKey(key);return ok;
}
bool unregisterUninstall(Options const& o){
    REGSAM access=o.testRoot.empty()?KEY_WOW64_64KEY:0;
    const auto result=RegDeleteKeyExW(registryRoot(o),registryPath(o),access,0);
    return result==ERROR_SUCCESS||result==ERROR_FILE_NOT_FOUND;
}

bool copySelf(fs::path const& root){
    auto self=selfPath();if(self.empty())return false;
    return CopyFileW(self.c_str(),(root/kUninstaller).c_str(),FALSE)!=FALSE;
}
bool scheduleSelfCleanup(fs::path const& root){
    wchar_t tempDir[MAX_PATH]{};
    if(!GetTempPathW(MAX_PATH,tempDir))return false;
    wchar_t tempName[MAX_PATH]{};
    if(!GetTempFileNameW(tempDir,L"fxu",0,tempName))return false;
    fs::path script=tempName;script.replace_extension(L".cmd");
    MoveFileExW(tempName,script.c_str(),MOVEFILE_REPLACE_EXISTING);
    const auto uninstaller=root/kUninstaller;
    const auto manifest=root/kManifest;
    std::ofstream out(script,std::ios::binary|std::ios::trunc);
    if(!out)return false;
    out<<"@echo off\r\n";
    out<<"ping 127.0.0.1 -n 2 >nul\r\n";
    out<<"del /f /q "<<utf8(quote(uninstaller.native()))<<" >nul 2>nul\r\n";
    out<<"del /f /q "<<utf8(quote(manifest.native()))<<" >nul 2>nul\r\n";
    out<<"rmdir "<<utf8(quote(root.native()))<<" >nul 2>nul\r\n";
    out<<"del /f /q \"%~f0\" >nul 2>nul\r\n";
    out.close();
    std::wstring cmd=L"cmd.exe /d /c "+quote(script.native());
    STARTUPINFOW si{sizeof(si)};PROCESS_INFORMATION pi{};
    std::vector<wchar_t> buffer(cmd.begin(),cmd.end());buffer.push_back(L'\0');
    if(!CreateProcessW(nullptr,buffer.data(),nullptr,nullptr,FALSE,
        CREATE_NO_WINDOW|DETACHED_PROCESS,nullptr,tempDir,&si,&pi))return false;
    CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return true;
}

bool promptInstall(fs::path const& root,bool& desktop){
    TASKDIALOGCONFIG c{sizeof(c)};
    c.hInstance=GetModuleHandleW(nullptr);
    c.dwFlags=TDF_ALLOW_DIALOG_CANCELLATION;
    c.dwCommonButtons=TDCBF_OK_BUTTON|TDCBF_CANCEL_BUTTON;
    c.pszWindowTitle=L"flyExplorer 설치";
    c.pszMainInstruction=L"flyExplorer를 설치하시겠습니까?";
    std::wstring detail=L"설치 위치: "+root.native();c.pszContent=detail.c_str();
    c.pszVerificationText=L"바탕 화면에 바로가기 만들기";
    int button=0;BOOL checked=FALSE;
    if(FAILED(TaskDialogIndirect(&c,&button,nullptr,&checked)))return false;
    desktop=checked!=FALSE;return button==IDOK;
}
bool promptUninstall(bool& purge){
    TASKDIALOGCONFIG config{sizeof(config)};
    config.hInstance=GetModuleHandleW(nullptr);
    config.dwFlags=TDF_ALLOW_DIALOG_CANCELLATION;
    config.dwCommonButtons=TDCBF_OK_BUTTON|TDCBF_CANCEL_BUTTON;
    config.pszWindowTitle=L"flyExplorer 제거";
    config.pszMainInstruction=L"flyExplorer를 제거하시겠습니까?";
    config.pszContent=L"일반 제거 시 사용자 설정·즐겨찾기·검색 기록은 유지됩니다.";
    config.pszVerificationText=
        L"완전 제거: 현재 사용자의 flyExplorer 설정·캐시도 삭제 (복구 불가)";
    int button=0;
    BOOL checked=FALSE;
    if(FAILED(TaskDialogIndirect(&config,&button,nullptr,&checked)))return false;
    purge=checked!=FALSE;
    return button==IDOK;
}
fs::path privateDataRoot(Options const& o,fs::path const& root){
    if(o.testRoot.empty()){
        const auto local=knownFolder(FOLDERID_LocalAppData);
        return local.empty()?fs::path{}:local/L"flyExplorer";
    }
    const auto filename=root.filename().native();
    const std::wstring prefix=L"flyExplorer-installer-test-";
    if(filename.rfind(prefix,0)!=0||filename.size()<=prefix.size())return {};
    const auto token=filename.substr(prefix.size());
    return root.parent_path()/(L"installer-profile-"+token)/L"localappdata"/L"flyExplorer";
}
bool deleteOwnedDataTree(fs::path const& target){
    if(reparsePoint(target))return false;
    std::error_code ec;
    if(!fs::exists(target,ec))return !ec;
    if(ec)return false;
    if(fs::is_directory(target,ec)){
        if(ec)return false;
        fs::directory_iterator children(target,ec);
        if(ec)return false;
        for(auto const& entry:children)
            if(!deleteOwnedDataTree(entry.path()))return false;
    }else if(ec)return false;
    ec.clear();
    return fs::remove(target,ec)&&!ec;
}
bool removePrivateData(Options const& o,fs::path const& root){
    const auto target=privateDataRoot(o,root);
    if(target.empty()||target.filename()!=L"flyExplorer"||
       reparsePoint(target.parent_path()))return false;
    return deleteOwnedDataTree(target);
}

void cleanupPartial(fs::path const& root){
    for(auto const& file:kPayloadFiles){
        std::error_code ec;fs::remove(root/file.relativePath,ec);
    }
}
int install(Options o,fs::path const& root){
    if(!o.silent&&!promptInstall(root,o.desktop))return ERROR_CANCELLED;
    std::error_code ec;fs::create_directories(root,ec);if(ec)return ERROR_CANNOT_MAKE;
    if(!removeInstalledPayload(root))return ERROR_ACCESS_DENIED;
    if(!extractPayload(root)){cleanupPartial(root);return ERROR_WRITE_FAULT;}
    if(!copySelf(root)){cleanupPartial(root);return ERROR_WRITE_FAULT;}
    if(!writeInstallManifest(root)){cleanupPartial(root);return ERROR_WRITE_FAULT;}
    if(!createShortcuts(o,root))return ERROR_CREATE_FAILED;
    if(!registerUninstall(o,root))return ERROR_REGISTRY_CORRUPT;
    return 0;
}
bool onlySelfAndManifestRemain(fs::path const& root){
    std::error_code ec;
    fs::directory_iterator remaining(root,ec);
    if(ec)return false;
    for(auto const& item:remaining){
        if(reparsePoint(item.path()))return false;
        const auto name=item.path().filename();
        if(name!=kUninstaller&&name!=kManifest)return false;
        if(!item.is_regular_file(ec)||ec)return false;
    }
    return true;
}
int uninstall(Options o,fs::path const& root){
    if(!o.silent&&!promptUninstall(o.purgeUserData))return ERROR_CANCELLED;
    if(!removeShortcuts(o,root))return ERROR_ACCESS_DENIED;
    if(!removeInstalledPayload(root))return ERROR_ACCESS_DENIED;
    if(!onlySelfAndManifestRemain(root))return ERROR_DIR_NOT_EMPTY;
    const auto installedUninstaller=root/kUninstaller;
    const auto current=fs::path(selfPath());
    std::error_code ec;
    if(!fs::equivalent(current,installedUninstaller,ec)){
        ec.clear();
        fs::remove(installedUninstaller,ec);
        if(ec)return ERROR_ACCESS_DENIED;
        ec.clear();
        fs::remove(root/kManifest,ec);
        if(ec)return ERROR_ACCESS_DENIED;
        ec.clear();
        if(!fs::remove(root,ec)||ec)return ERROR_DIR_NOT_EMPTY;
        if(o.purgeUserData&&!removePrivateData(o,root))return ERROR_ACCESS_DENIED;
        return unregisterUninstall(o)?0:ERROR_ACCESS_DENIED;
    }
    // Self-deletion is deferred until this executable handle is released.
    // The caller-owned profile is purged only after installed payload cleanup.
    if(o.purgeUserData&&!removePrivateData(o,root))return ERROR_ACCESS_DENIED;
    if(!scheduleSelfCleanup(root))return ERROR_ACCESS_DENIED;
    return unregisterUninstall(o)?0:ERROR_ACCESS_DENIED;
}

} // namespace

int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int){
    auto o=optionsFromCommandLine();
    // A script can request destructive profile cleanup only with an explicit
    // silent uninstall; interactive uninstall uses an unchecked checkbox.
    if(o.purgeUserData&&(!o.uninstall||!o.silent))return ERROR_INVALID_PARAMETER;
    fs::path root=installRoot(o);
    if(root.empty()){
        MessageBoxW(nullptr,L"안전한 설치 경로를 결정할 수 없습니다.",L"flyExplorer Setup",MB_OK|MB_ICONERROR);
        return ERROR_INVALID_PARAMETER;
    }
    if(o.testRoot.empty()&&!isAdmin())return elevateAndWait();
    const int rc=o.uninstall?uninstall(o,root):install(o,root);
    if(rc&&!o.silent){
        std::wstring message=L"작업을 완료하지 못했습니다. 오류 코드: "+std::to_wstring(rc);
        MessageBoxW(nullptr,message.c_str(),L"flyExplorer Setup",MB_OK|MB_ICONERROR);
    }else if(!rc&&!o.silent&&!o.uninstall){
        MessageBoxW(nullptr,L"flyExplorer 설치가 완료되었습니다.",L"flyExplorer Setup",MB_OK|MB_ICONINFORMATION);
    }
    return rc;
}
