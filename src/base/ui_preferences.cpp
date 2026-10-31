#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "ui_preferences.h"
#include <array>
#include <string>
namespace fxfile::uisettings {
namespace {
std::wstring directory(){
 std::array<wchar_t,32768> buf{};
 const auto n=::GetEnvironmentVariableW(L"LOCALAPPDATA",buf.data(),static_cast<DWORD>(buf.size()));
 if(!n||n>=buf.size())return {};
 return std::wstring(buf.data(),n)+L"\\flyExplorer";
}
std::string themeName(Theme theme){
 switch(theme){case Theme::Light:return "light";case Theme::Dark:return "dark";default:return "system";}
}
std::string viewName(int view){
 switch(view){case 1:return "list";case 2:return "small-icons";case 3:return "medium-icons";case 4:return "large-icons";case 5:return "extra-large-icons";case 6:return "tiles";default:return "details";}
}
std::string legacyText(Theme theme){return "schema=1\r\nlanguage=ko-KR\r\ntheme="+themeName(theme)+"\r\n";}
std::string text(Theme theme,int view){return "schema=2\r\nlanguage=ko-KR\r\ntheme="+themeName(theme)+"\r\nview="+viewName(view)+"\r\n";}
std::string text3(Theme theme,int view,int address,int search){
 return "schema=3\r\nlanguage=ko-KR\r\ntheme="+themeName(theme)+
    "\r\nview="+viewName(view)+"\r\naddress-shortcut="+std::to_string(address)+
    "\r\nsearch-shortcut="+std::to_string(search)+"\r\n";
}
}
std::wstring privatePath(){auto dir=directory();return dir.empty()?L"":dir+L"\\ui-preferences-v1.txt";}
bool load(Preferences& out) noexcept{
 out=Preferences{};
 const auto path=privatePath();if(path.empty())return false;
 HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE)return false;
 LARGE_INTEGER length{};if(!::GetFileSizeEx(h,&length)||length.QuadPart<24||length.QuadPart>512){::CloseHandle(h);return false;}
 char bytes[513]{};DWORD read=0;const bool ok=::ReadFile(h,bytes,static_cast<DWORD>(length.QuadPart),&read,nullptr)!=FALSE;::CloseHandle(h);
 if(!ok||read!=length.QuadPart)return false;std::string data(bytes,read);
 const std::array<Theme,3> themes{{Theme::System,Theme::Light,Theme::Dark}};
 for(auto theme:themes){if(data==legacyText(theme)){out.theme=theme;out.defaultViewMode=0;return true;}}
 for(auto theme:themes)for(int view=0;view<7;++view){
  if(data==text(theme,view)){out.theme=theme;out.defaultViewMode=view;return true;}
  for(int address=0;address<kFocusShortcutCount;++address)
   for(int search=0;search<kFocusShortcutCount;++search){
   if(!validFocusShortcuts(address,search))continue;
   if(data==text3(theme,view,address,search)){
    out.theme=theme;out.defaultViewMode=view;
    out.addressShortcut=address;out.searchShortcut=search;return true;
   }
  }
 }
 return false;
}
bool save(Preferences const& pref) noexcept {
 if(pref.language!=L"ko-KR"||pref.defaultViewMode<0||pref.defaultViewMode>6)return false;
 if(pref.theme!=Theme::System&&pref.theme!=Theme::Light&&pref.theme!=Theme::Dark)return false;
 if(!validFocusShortcuts(pref.addressShortcut,pref.searchShortcut))return false;
 auto dir=directory();if(dir.empty())return false;
 if(!::CreateDirectoryW(dir.c_str(),nullptr)&&::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
 auto attrs=::GetFileAttributesW(dir.c_str());if(attrs==INVALID_FILE_ATTRIBUTES||!(attrs&FILE_ATTRIBUTE_DIRECTORY)||(attrs&FILE_ATTRIBUTE_REPARSE_POINT))return false;
 wchar_t temporary[MAX_PATH]{};if(dir.size()>MAX_PATH-35||!::GetTempFileNameW(dir.c_str(),L"fxp",0,temporary))return false;
 HANDLE h=::CreateFileW(temporary,GENERIC_WRITE,0,nullptr,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE){::DeleteFileW(temporary);return false;}
 const auto body=text3(pref.theme,pref.defaultViewMode,pref.addressShortcut,pref.searchShortcut);DWORD written=0;
 bool good=::WriteFile(h,body.data(),static_cast<DWORD>(body.size()),&written,nullptr)!=FALSE&&written==body.size();
 if(good)good=::FlushFileBuffers(h)!=FALSE;if(!::CloseHandle(h))good=false;
 if(good){auto dest=privatePath();good=::MoveFileExW(temporary,dest.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;}
 if(!good)::DeleteFileW(temporary);return good;
}
}
