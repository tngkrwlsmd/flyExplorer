$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -ne 0) {
    $dirty | ForEach-Object { Write-Output $_ }
    throw "Expected clean checkout before Known Folder artwork patch."
}

$script = Join-Path $env:TEMP "fly_known_folder_patch.py"
@'
from pathlib import Path

ROOT=Path(r"C:\dev\flyExplorer")

def read(rel, enc="utf-8"):
    return (ROOT/rel).read_text(encoding=enc)

def write(rel, content, enc="utf-8"):
    (ROOT/rel).write_text(content, encoding=enc, newline="")
    print("EDITED", rel)

def replace_once(rel, old, new, enc="utf-8"):
    p=ROOT/rel
    s=p.read_text(encoding=enc)
    if old not in s:
        raise RuntimeError(f"{rel}: anchor not found: {old[:140]!r}")
    s=s.replace(old,new,1)
    p.write_text(s,encoding=enc,newline="")
    print("EDITED",rel)

header=r'''// Windows registered file-type names and fixed Known Folder visuals:
// bounded disposable helper process, never on the WinUI UI thread.
#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace fxfile::filetype {
// Extensions are limited to one period followed by 1..16 ASCII alpha/numeric
// characters; no path or command-line metacharacters reach the helper.
bool safeExtension(std::wstring const& ext) noexcept;
// Known Folder helper keys are a fixed product-owned allowlist. No arbitrary
// path is passed on the helper command line.
bool safeKnownFolderKey(std::wstring const& key) noexcept;
std::wstring knownFolderPath(std::wstring const& key) noexcept;

// On failures or timeout returns an empty mapping. The caller's original
// generic extension/folder classification remains a valid safe fallback.
struct Visual {
    std::wstring label;
    // Square BGRA from a disposable OS Shell helper, or empty.
    std::vector<unsigned char> bgra;
    std::uint32_t width=0,height=0;
};
std::unordered_map<std::wstring,Visual> queryVisuals(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& extensions,
    DWORD timeoutMs=2500,std::uint32_t requestedPixels=16) noexcept;
std::unordered_map<std::wstring,Visual> queryKnownFolderVisuals(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& keys,
    DWORD timeoutMs=2500,std::uint32_t requestedPixels=16) noexcept;
std::unordered_map<std::wstring,std::wstring> query(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& extensions,
    DWORD timeoutMs=2500) noexcept;
}
'''
write("src/base/shell_assoc_type_core.h",header)

cpp=r'''#define WIN32_LEAN_AND_MEAN
#include "shell_assoc_type_core.h"
#include <algorithm>
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
'''
write("src/base/shell_assoc_type_core.cpp",cpp)

replace_once(
 "app/winui/helper/FlyShellIsolationHelper.cpp",
 '#include <shellapi.h>\n',
 '#include <shellapi.h>\n#include <shlobj.h>\n'
)

helper=read("app/winui/helper/FlyShellIsolationHelper.cpp")
anchor='''    const bool requestVisuals=argc>=4&&!wcscmp(argv[1],L"--file-visuals");
'''
if anchor not in helper:
    raise RuntimeError("helper visual anchor missing")
known_branch=r'''    if(argc>=4&&!wcscmp(argv[1],L"--known-folder-visuals")){
        wchar_t* end=nullptr;
        const auto parsed=::wcstoul(argv[2],&end,10);
        if(!end||*end||parsed<16||parsed>64||argc>9)return 18;
        const auto visualPixels=static_cast<std::uint32_t>(parsed);
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!output||output==INVALID_HANDLE_VALUE)return 19;
        for(int i=3;i<argc;++i){
            std::wstring key(argv[i]);
            KNOWNFOLDERID const* id=nullptr;
            if(key==L"desktop")id=&FOLDERID_Desktop;
            else if(key==L"documents")id=&FOLDERID_Documents;
            else if(key==L"downloads")id=&FOLDERID_Downloads;
            else if(key==L"pictures")id=&FOLDERID_Pictures;
            else if(key==L"music")id=&FOLDERID_Music;
            else if(key==L"videos")id=&FOLDERID_Videos;
            else return 20;

            PWSTR path=nullptr;
            const auto pathHr=::SHGetKnownFolderPath(
                *id,KF_FLAG_DEFAULT,nullptr,&path);
            SHFILEINFOW info{};
            const auto result=SUCCEEDED(pathHr)&&path?
                ::SHGetFileInfoW(path,0,&info,sizeof(info),
                    SHGFI_TYPENAME|SHGFI_ICON|
                    (visualPixels<=16?SHGFI_SMALLICON:SHGFI_LARGEICON)):0;
            if(path)::CoTaskMemFree(path);

            std::wstring readable=result?info.szTypeName:L"";
            if(readable.size()>79)readable.clear();
            const int count=readable.empty()?0: ::WideCharToMultiByte(
                CP_UTF8,WC_ERR_INVALID_CHARS,readable.data(),
                static_cast<int>(readable.size()),nullptr,0,nullptr,nullptr);
            if(count<0||count>320)return 22;
            std::string line=std::to_string(i-3)+"\t";
            if(count){
                std::string utf8(static_cast<size_t>(count),'\0');
                if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                      readable.data(),static_cast<int>(readable.size()),
                      utf8.data(),count,nullptr,nullptr)!=count)return 22;
                line+=utf8;
            }
            line+="\t";
            if(result&&info.hIcon){
                BITMAPINFO bitmap{};
                bitmap.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                bitmap.bmiHeader.biWidth=static_cast<LONG>(visualPixels);
                bitmap.bmiHeader.biHeight=-static_cast<LONG>(visualPixels);
                bitmap.bmiHeader.biPlanes=1;
                bitmap.bmiHeader.biBitCount=32;
                bitmap.bmiHeader.biCompression=BI_RGB;
                void* raw=nullptr;
                HDC screen=::GetDC(nullptr);
                HDC memory=screen?::CreateCompatibleDC(screen):nullptr;
                HBITMAP image=memory?::CreateDIBSection(
                    memory,&bitmap,DIB_RGB_COLORS,&raw,nullptr,0):nullptr;
                if(memory&&image&&raw){
                    auto old=::SelectObject(memory,image);
                    std::memset(raw,0,visualPixels*visualPixels*4);
                    if(::DrawIconEx(memory,0,0,info.hIcon,
                                   visualPixels,visualPixels,
                                   0,nullptr,DI_NORMAL)){
                        DWORD required=0;
                        ::CryptBinaryToStringA(static_cast<BYTE*>(raw),
                            visualPixels*visualPixels*4,
                            CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                            nullptr,&required);
                        if(required>0&&required<40000){
                            std::string encoded(required,'\0');
                            if(::CryptBinaryToStringA(
                                static_cast<BYTE*>(raw),
                                visualPixels*visualPixels*4,
                                CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                                encoded.data(),&required)){
                                encoded.resize(std::strlen(encoded.c_str()));
                                line+=encoded;
                            }
                        }
                    }
                    ::SelectObject(memory,old);
                }
                if(image)::DeleteObject(image);
                if(memory)::DeleteDC(memory);
                if(screen)::ReleaseDC(nullptr,screen);
                ::DestroyIcon(info.hIcon);
            }
            line+="\n";
            DWORD sent=0;
            if(!::WriteFile(output,line.data(),
                 static_cast<DWORD>(line.size()),&sent,nullptr)||
               sent!=line.size())return 23;
        }
        return 0;
    }
'''
helper=helper.replace(anchor,known_branch+anchor,1)
write("app/winui/helper/FlyShellIsolationHelper.cpp",helper)

replace_once(
 "app/winui/file_list_state.h",
 '    std::uint32_t iconWidth=0,iconHeight=0;\n',
 '    std::uint32_t iconWidth=0,iconHeight=0;\n'
 '    bool knownFolderVisual=false;\n'
)

detail=read("app/winui/file_detail_controller.cpp")
anchor='''            using FileDetail=fxfile::previewlist::FileDetail;
            using FileViewMode=fxfile::previewlist::FileViewMode;
            std::vector<std::wstring> extensions{L".flyfolder"};
'''
if anchor not in detail:
    raise RuntimeError("file detail worker anchor missing")
replacement='''            using FileDetail=fxfile::previewlist::FileDetail;
            using FileViewMode=fxfile::previewlist::FileViewMode;
            static constexpr wchar_t const* knownFolderKeys[]{
                L"desktop",L"documents",L"downloads",
                L"pictures",L"music",L"videos"
            };
            std::vector<std::pair<std::wstring,std::wstring>> knownFolderPaths;
            knownFolderPaths.reserve(std::size(knownFolderKeys));
            for(auto const* key:knownFolderKeys){
                auto path=fxfile::filetype::knownFolderPath(key);
                if(!path.empty())
                    knownFolderPaths.emplace_back(key,std::move(path));
            }
            std::vector<std::wstring> knownFolderKeyByIndex(
                request.paths.size());
            std::vector<std::wstring> requestedKnownFolderKeys;
            for(std::size_t i=0;i<request.paths.size();++i){
                auto const& candidate=request.paths[i];
                if(candidate.empty())continue;
                for(auto const& known:knownFolderPaths){
                    if(::CompareStringOrdinal(
                         candidate.c_str(),-1,known.second.c_str(),-1,TRUE)
                       !=CSTR_EQUAL)continue;
                    knownFolderKeyByIndex[i]=known.first;
                    if(std::find(requestedKnownFolderKeys.begin(),
                         requestedKnownFolderKeys.end(),known.first)
                       ==requestedKnownFolderKeys.end())
                        requestedKnownFolderKeys.push_back(known.first);
                    break;
                }
            }
            std::vector<std::wstring> extensions{L".flyfolder"};
'''
detail=detail.replace(anchor,replacement,1)

anchor='''            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::wstring visualHelper;
'''
if anchor not in detail:
    raise RuntimeError("visual maps anchor missing")
detail=detail.replace(
    anchor,
    '''            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::unordered_map<std::wstring,fxfile::filetype::Visual>
                knownFolderVisuals;
            std::wstring visualHelper;
''',1)

anchor='''                    for(auto const& ext:recover){
                        auto one=fxfile::filetype::queryVisuals(
                            visualHelper,{ext},1350,request.visualPixels);
                        auto found=one.find(ext);
                        if(found!=one.end())windowsTypes[ext]=std::move(found->second);
                    }
                }
            }
'''
if anchor not in detail:
    raise RuntimeError("visual recovery anchor missing")
detail=detail.replace(
    anchor,
    '''                    for(auto const& ext:recover){
                        auto one=fxfile::filetype::queryVisuals(
                            visualHelper,{ext},1350,request.visualPixels);
                        auto found=one.find(ext);
                        if(found!=one.end())windowsTypes[ext]=std::move(found->second);
                    }
                    if(!requestedKnownFolderKeys.empty())
                        knownFolderVisuals=fxfile::filetype::queryKnownFolderVisuals(
                            visualHelper,requestedKnownFolderKeys,
                            2500,request.visualPixels);
                }
            }
''',1)

old='''                if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                    entry.typeLabel=L"폴더";
                    auto folder=windowsTypes.find(L".flyfolder");
                    if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                        entry.iconBgra=folder->second.bgra;
                        entry.iconWidth=folder->second.width;
                        entry.iconHeight=folder->second.height;
                    }
                }else{
'''
if old not in detail:
    raise RuntimeError("directory visual block missing")
new='''                if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                    entry.typeLabel=L"폴더";
                    auto const& knownKey=knownFolderKeyByIndex[i];
                    auto known=knownKey.empty()?knownFolderVisuals.end():
                        knownFolderVisuals.find(knownKey);
                    if(known!=knownFolderVisuals.end()&&
                       !known->second.bgra.empty()){
                        entry.iconBgra=known->second.bgra;
                        entry.iconWidth=known->second.width;
                        entry.iconHeight=known->second.height;
                        entry.knownFolderVisual=true;
                    }else{
                        auto folder=windowsTypes.find(L".flyfolder");
                        if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                            entry.iconBgra=folder->second.bgra;
                            entry.iconWidth=folder->second.width;
                            entry.iconHeight=folder->second.height;
                        }
                    }
                }else{
'''
detail=detail.replace(old,new,1)
write("app/winui/file_detail_controller.cpp",detail)

main=read("app/winui/MainWindow.xaml.cpp")
old='''                                Microsoft::UI::Xaml::Automation::AutomationProperties::
                                    SetName(image,item.isFolder()?
                                        L"Windows Shell folder icon":
                                        L"Windows system registered file icon");
'''
if old not in main:
    raise RuntimeError("details image automation block missing")
main=main.replace(
    old,
    '''                                Microsoft::UI::Xaml::Automation::AutomationProperties::
                                    SetName(image,item.isFolder()?
                                        (iconMeta->knownFolderVisual?
                                            L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):
                                        L"Windows system registered file icon");
''',1)

old='''                                    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(image,realThumb?L"Windows Shell image thumbnail":
                                        item.isFolder()?L"Windows Shell folder icon":L"Windows system registered file icon");
'''
if old not in main:
    raise RuntimeError("icon-grid image automation block missing")
main=main.replace(
    old,
    '''                                    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(image,realThumb?L"Windows Shell image thumbnail":
                                        item.isFolder()?(iconMeta->knownFolderVisual?L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):L"Windows system registered file icon");
''',1)
write("app/winui/MainWindow.xaml.cpp",main)

test=r'''"""Path-specific Known Folder artwork stays bounded and isolated."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT/path).read_text(encoding="utf-8")

class KnownFolderArtworkContract(unittest.TestCase):
    def test_fixed_known_folder_key_allowlist_and_os_resolution(self):
        header=source("src/base/shell_assoc_type_core.h")
        core=source("src/base/shell_assoc_type_core.cpp")
        self.assertIn("safeKnownFolderKey",header)
        self.assertIn("knownFolderPath",header)
        self.assertIn("queryKnownFolderVisuals",header)
        for key in ("desktop","documents","downloads","pictures","music","videos"):
            self.assertIn('L"'+key+'"',core)
        for token in (
            "FOLDERID_Desktop","FOLDERID_Documents","FOLDERID_Downloads",
            "FOLDERID_Pictures","FOLDERID_Music","FOLDERID_Videos",
            "SHGetKnownFolderPath",
        ):
            self.assertIn(token,core)

    def test_helper_accepts_only_fixed_tokens_and_returns_pixels(self):
        helper=source("app/winui/helper/FlyShellIsolationHelper.cpp")
        self.assertIn('L"--known-folder-visuals"',helper)
        self.assertIn("argc>9",helper)
        self.assertIn("SHGetKnownFolderPath",helper)
        self.assertIn("SHGetFileInfoW(path,0",helper)
        self.assertIn("SHGFI_ICON",helper)
        self.assertIn("DrawIconEx",helper)
        self.assertIn("CryptBinaryToStringA",helper)
        self.assertNotIn("argv[i],0,&info",helper)

    def test_file_detail_prefers_known_artwork_and_keeps_generic_fallback(self):
        worker=source("app/winui/file_detail_controller.cpp")
        state=source("app/winui/file_list_state.h")
        app=source("app/winui/MainWindow.xaml.cpp")
        self.assertIn("knownFolderKeyByIndex",worker)
        self.assertIn("queryKnownFolderVisuals(",worker)
        self.assertIn('windowsTypes.find(L".flyfolder")',worker)
        self.assertIn("entry.knownFolderVisual=true",worker)
        self.assertIn("bool knownFolderVisual=false",state)
        self.assertIn('L"Windows Known Folder artwork"',app)
        self.assertNotIn("SHGetFileInfoW",worker)
        self.assertNotIn("SHGetKnownFolderPath",app)

if __name__=="__main__":
    unittest.main()
'''
write("tests/winui/test_known_folder_artwork_contract.py",test)

# Guard against accidental direct Shell visual calls in UI/worker.
for rel, token in [
    ("app/winui/MainWindow.xaml.cpp","SHGetFileInfoW"),
    ("app/winui/file_detail_controller.cpp","SHGetFileInfoW"),
]:
    if token in read(rel):
        raise RuntimeError(f"{rel}: direct Shell visual call leaked: {token}")

print("KNOWN_FOLDER_ARTWORK_PATCH_COMPLETE")
'@ | Set-Content -LiteralPath $script -Encoding utf8

python -X utf8 $script
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue

git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -X utf8 -m unittest tests.winui.test_known_folder_artwork_contract tests.winui.test_registered_file_type_contract tests.winui.test_file_detail_controller_contract tests.winui.test_m26_fluent_contract
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

test.bat source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

build.bat Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "KNOWN_FOLDER_ARTWORK_BUILD_PASS"
git diff --stat
git status --short
