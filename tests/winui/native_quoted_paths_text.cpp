// Host-independent formatting probe; never touches files or an OS clipboard.
#include "../../src/base/quoted_paths_text.h"
#include <cassert>
#include <iostream>
using fxfile::shellclipboard::formatQuotedPaths;

int main(){
 std::wstring result=L"stale";
 assert(!formatQuotedPaths({},100,result)&&result.empty());
 assert(formatQuotedPaths({L"C:\\문서 폴더\\이름.md"},100,result));
 assert(result==L"\"C:\\문서 폴더\\이름.md\"");
 assert(formatQuotedPaths({L"C:\\a.txt",L"D:\\b.md"},100,result));
 assert(result==L"\"C:\\a.txt\"\r\n\"D:\\b.md\"");
 assert(formatQuotedPaths({L"abc"},5,result)&&result==L"\"abc\"");
 assert(!formatQuotedPaths({L"abc"},4,result)&&result.empty());
 assert(formatQuotedPaths({L"a",L"b"},8,result)&&result==L"\"a\"\r\n\"b\"");
 assert(!formatQuotedPaths({L"a",L"b"},7,result)&&result.empty());
 assert(!formatQuotedPaths({L"a"},0,result)&&result.empty());
 for(auto const& path:std::vector<std::wstring>{L"",L"a\"b",L"a\rb",L"a\nb",std::wstring(L"a\0b",3)}){
  result=L"stale";
  assert(!formatQuotedPaths({L"safe",path},100,result)&&result.empty());
 }
 std::cout<<"QUOTED_PATHS_FORMAT_NATIVE_PASS\n";
}
