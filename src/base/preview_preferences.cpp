#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "preview_preferences.h"
#include <array>
#include <string>
namespace fxfile::previewsettings {
namespace {
std::wstring directory(){
 std::array<wchar_t,32768> buf{};
 const auto n=::GetEnvironmentVariableW(L"LOCALAPPDATA",buf.data(),
                                      static_cast<DWORD>(buf.size()));
 if(!n||n>=buf.size())return {};
 return std::wstring(buf.data(),n)+L"\\flyExplorer.WinUI3Preview";
}
std::string text(Theme theme){
 switch(theme){
 case Theme::Light:return "schema=1\r\nlanguage=ko-KR\r\ntheme=light\r\n";
 case Theme::Dark:return "schema=1\r\nlanguage=ko-KR\r\ntheme=dark\r\n";
 default:return "schema=1\r\nlanguage=ko-KR\r\ntheme=system\r\n";
 }
}
}
std::wstring privatePath(){
 auto dir=directory();
 if(dir.empty())return {};
 return dir+L"\\ui-preferences-v1.txt";
}
bool load(Preferences& out) noexcept{
 out=Preferences{}; // explicit Korean, regardless of Windows display locale
 const auto path=privatePath();
 if(path.empty())return false;
 HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,
           FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
           nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE)return false;
 LARGE_INTEGER length{};
 if(!::GetFileSizeEx(h,&length)||length.QuadPart<24||
     length.QuadPart>256){::CloseHandle(h);return false;}
 char bytes[257]{};
 DWORD read=0;
 const bool ok=::ReadFile(h,bytes,static_cast<DWORD>(length.QuadPart),
                           &read,nullptr)!=FALSE;
 ::CloseHandle(h);
 if(!ok||read!=length.QuadPart)return false;
 std::string data(bytes,read);
 // Exact bounded UTF-8-compatible ASCII grammar; reject extra fields
 // rather than accidentally accepting or writing malicious paths.
 if(data==text(Theme::System))out.theme=Theme::System;
 else if(data==text(Theme::Light))out.theme=Theme::Light;
 else if(data==text(Theme::Dark))out.theme=Theme::Dark;
 else return false;
 return true;
}
bool save(Preferences const& pref) noexcept {
 if(pref.language!=L"ko-KR")return false;
 if(pref.theme!=Theme::System&&pref.theme!=Theme::Light&&
    pref.theme!=Theme::Dark)return false;
 auto dir=directory();
 if(dir.empty())return false;
 if(!::CreateDirectoryW(dir.c_str(),nullptr)&&
    ::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
 // Reject existing path that is not a real directory.
 auto attrs=::GetFileAttributesW(dir.c_str());
 if(attrs==INVALID_FILE_ATTRIBUTES||!(attrs&FILE_ATTRIBUTE_DIRECTORY)||
    (attrs&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 wchar_t temporary[MAX_PATH]{};
 if(dir.size()>MAX_PATH-35||
    !::GetTempFileNameW(dir.c_str(),L"fxp",0,temporary))return false;
 HANDLE h=::CreateFileW(temporary,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,
                         FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE){::DeleteFileW(temporary);return false;}
 const auto body=text(pref.theme);
 DWORD written=0;
 bool good=::WriteFile(h,body.data(),static_cast<DWORD>(body.size()),
                       &written,nullptr)!=FALSE&&written==body.size();
 if(good)good=::FlushFileBuffers(h)!=FALSE;
 if(!::CloseHandle(h))good=false;
 if(good){
  auto dest=privatePath();
  good=::MoveFileExW(temporary,dest.c_str(),
      MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
 }
 if(!good)::DeleteFileW(temporary);
 return good;
}
}
