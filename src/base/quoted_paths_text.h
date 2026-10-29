// Pure bounded formatting only: this never reads files or touches a clipboard.
#pragma once
#include <cstddef>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::shellclipboard {
inline bool formatQuotedPaths(std::vector<std::wstring> const& paths,
                              std::size_t maxUnits,std::wstring& result) noexcept {
 result.clear();
 try{
  std::wstring text;
  for(auto const& path:paths){
   if(path.empty()||path.find_first_of(L"\"\r\n")!=std::wstring::npos||
      path.find(L'\0')!=std::wstring::npos)return false;
   const std::size_t extra=text.empty()?2:4; // quotes, plus CRLF between items
   if(text.size()>maxUnits||extra>maxUnits-text.size()||
      path.size()>maxUnits-text.size()-extra)return false;
   if(!text.empty())text+=L"\r\n";
   text+=L'"';text+=path;text+=L'"';
  }
  if(text.empty())return false;
  result=std::move(text);
  return true;
 }catch(...){result.clear();return false;}
}
} // namespace fxfile::shellclipboard
