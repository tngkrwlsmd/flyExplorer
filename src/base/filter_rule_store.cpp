#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "filter_rule_store.h"
#include <algorithm>
#include <array>
#include <cwctype>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::filterrules {
namespace {

std::wstring directory()
{
    std::array<wchar_t,32768> buffer{};
    const auto count=::GetEnvironmentVariableW(
        L"LOCALAPPDATA",buffer.data(),static_cast<DWORD>(buffer.size()));
    if(!count||count>=buffer.size())return {};
    return std::wstring(buffer.data(),count)+L"\\flyExplorer";
}

bool forbidden(std::wstring const& value)
{
    return value.find_first_of(L"\r\n\t")!=std::wstring::npos ||
           value.find(L'\0')!=std::wstring::npos;
}

std::wstring trim(std::wstring value)
{
    const auto first=std::find_if_not(value.begin(),value.end(),
        [](wchar_t ch){return std::iswspace(ch);});
    const auto last=std::find_if_not(value.rbegin(),value.rend(),
        [](wchar_t ch){return std::iswspace(ch);}).base();
    if(first>=last)return {};
    return std::wstring(first,last);
}

bool sameNoCase(std::wstring const& a,std::wstring const& b)
{
    return ::CompareStringOrdinal(
        a.c_str(),static_cast<int>(a.size()),
        b.c_str(),static_cast<int>(b.size()),TRUE)==CSTR_EQUAL;
}

bool validName(std::wstring const& name)
{
    if(name.empty()||name.size()>Store::kMaxName||forbidden(name))return false;
    return std::any_of(name.begin(),name.end(),
        [](wchar_t ch){return !std::iswspace(ch);});
}

bool splitMasks(
    std::wstring const& expression,std::vector<std::wstring>& result)
{
    result.clear();
    if(expression.empty()||expression.size()>Store::kMaxMasks||
       forbidden(expression))return false;
    std::size_t begin=0;
    while(begin<=expression.size()){
        const auto end=expression.find(L';',begin);
        auto token=trim(expression.substr(
            begin,end==std::wstring::npos?std::wstring::npos:end-begin));
        if(token.empty()||
           token.find_first_of(L"\\/:\"<>|")!=std::wstring::npos)
            return false;
        result.push_back(std::move(token));
        if(result.size()>20)return false;
        if(end==std::wstring::npos)break;
        begin=end+1;
    }
    return !result.empty();
}

std::wstring normalizeMasks(std::wstring const& expression)
{
    std::vector<std::wstring> tokens;
    if(!splitMasks(expression,tokens))return {};
    std::wstring value;
    for(auto const& token:tokens){
        if(!value.empty())value+=L';';
        value+=token;
    }
    return value;
}

bool wildcardMatch(std::wstring const& value,std::wstring const& pattern)
{
    std::size_t v=0,p=0,star=std::wstring::npos,retry=0;
    while(v<value.size()){
        if(p<pattern.size()&&
           (pattern[p]==L'?'||
            std::towlower(pattern[p])==std::towlower(value[v]))){
            ++p;++v;continue;
        }
        if(p<pattern.size()&&pattern[p]==L'*'){
            star=p++;retry=v;continue;
        }
        if(star!=std::wstring::npos){
            p=star+1;v=++retry;continue;
        }
        return false;
    }
    while(p<pattern.size()&&pattern[p]==L'*')++p;
    return p==pattern.size();
}

bool utf8ToWide(std::string const& input,std::wstring& output)
{
    output.clear();
    if(input.empty())return true;
    const int needed=::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),nullptr,0);
    if(needed<=0)return false;
    output.resize(static_cast<std::size_t>(needed));
    return ::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),output.data(),needed)==needed;
}

bool wideToUtf8(std::wstring const& input,std::string& output)
{
    output.clear();
    if(input.empty())return true;
    const int needed=::WideCharToMultiByte(
        CP_UTF8,WC_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),nullptr,0,nullptr,nullptr);
    if(needed<=0)return false;
    output.resize(static_cast<std::size_t>(needed));
    return ::WideCharToMultiByte(
        CP_UTF8,WC_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),output.data(),needed,
        nullptr,nullptr)==needed;
}

bool readBytes(std::wstring const& path,std::vector<unsigned char>& bytes)
{
    HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,
        FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    LARGE_INTEGER size{};
    const bool sized=::GetFileSizeEx(h,&size)!=FALSE&&
        size.QuadPart>=0&&size.QuadPart<=256*1024;
    if(!sized){::CloseHandle(h);return false;}
    bytes.assign(static_cast<std::size_t>(size.QuadPart),0);
    DWORD used=0;
    const bool good=bytes.empty()||
        (::ReadFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),
                    &used,nullptr)!=FALSE&&used==bytes.size());
    ::CloseHandle(h);
    return good;
}

bool writeAtomic(std::wstring const& path,std::string const& body)
{
    const auto slash=path.find_last_of(L"\\/");
    if(slash==std::wstring::npos)return false;
    const auto temp=path+L".tmp."+std::to_wstring(::GetCurrentProcessId())+
                    L"."+std::to_wstring(::GetTickCount64());
    HANDLE h=::CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,
                           FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    DWORD used=0;
    bool good=body.empty()||
        (::WriteFile(h,body.data(),static_cast<DWORD>(body.size()),
                     &used,nullptr)!=FALSE&&used==body.size());
    if(good)good=::FlushFileBuffers(h)!=FALSE;
    if(!::CloseHandle(h))good=false;
    if(good)good=::MoveFileExW(
        temp.c_str(),path.c_str(),
        MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
    if(!good)::DeleteFileW(temp.c_str());
    return good;
}

} // namespace

std::wstring Store::privatePath()
{
    const auto dir=directory();
    return dir.empty()?L"":dir+L"\\filter-rules-v1.txt";
}

bool Store::validExpression(std::wstring const& expression) noexcept
{
    try{
        std::vector<std::wstring> tokens;
        return splitMasks(expression,tokens);
    }catch(...){return false;}
}

bool Store::matches(
    std::wstring const& filename,std::wstring const& expression) noexcept
{
    try{
        if(expression.empty())return true;
        const bool masks=expression.find_first_of(L"*?;")!=std::wstring::npos;
        if(!masks){
            return std::search(filename.begin(),filename.end(),
                expression.begin(),expression.end(),
                [](wchar_t a,wchar_t b){
                    return std::towlower(a)==std::towlower(b);
                })!=filename.end();
        }
        std::vector<std::wstring> tokens;
        if(!splitMasks(expression,tokens))return false;
        return std::any_of(tokens.begin(),tokens.end(),
            [&](std::wstring const& token){
                return wildcardMatch(filename,token);
            });
    }catch(...){return false;}
}

MutationResult Store::add(
    std::wstring name,std::wstring masks) noexcept
{
    try{
        masks=normalizeMasks(masks);
        if(!validName(name)||masks.empty())return MutationResult::Invalid;
        if(mItems.size()>=kMaxItems)return MutationResult::Full;
        if(std::any_of(mItems.begin(),mItems.end(),
            [&](Rule const& item){return sameNoCase(item.name,name);}))
            return MutationResult::Duplicate;
        mItems.push_back({std::move(name),std::move(masks)});
        return MutationResult::Applied;
    }catch(...){return MutationResult::Invalid;}
}

MutationResult Store::update(
    std::size_t index,std::wstring name,std::wstring masks) noexcept
{
    try{
        if(index>=mItems.size())return MutationResult::NotFound;
        masks=normalizeMasks(masks);
        if(!validName(name)||masks.empty())return MutationResult::Invalid;
        for(std::size_t i=0;i<mItems.size();++i)
            if(i!=index&&sameNoCase(mItems[i].name,name))
                return MutationResult::Duplicate;
        mItems[index]={std::move(name),std::move(masks)};
        return MutationResult::Applied;
    }catch(...){return MutationResult::Invalid;}
}

bool Store::erase(std::size_t index) noexcept
{
    try{
        if(index>=mItems.size())return false;
        mItems.erase(mItems.begin()+static_cast<std::ptrdiff_t>(index));
        return true;
    }catch(...){return false;}
}

bool Store::loadFrom(std::wstring const& path) noexcept
{
    try{
        std::vector<unsigned char> bytes;
        if(!readBytes(path,bytes))return false;
        std::wstring text;
        const std::string utf8(
            reinterpret_cast<char const*>(bytes.data()),bytes.size());
        if(!utf8ToWide(utf8,text))return false;
        std::wistringstream lines(text);
        std::wstring line;
        if(!std::getline(lines,line))return false;
        if(!line.empty()&&line.back()==L'\r')line.pop_back();
        if(line!=L"schema=1")return false;
        Store candidate;
        while(std::getline(lines,line)){
            if(!line.empty()&&line.back()==L'\r')line.pop_back();
            if(line.empty())continue;
            const auto tab=line.find(L'\t');
            if(tab==std::wstring::npos||
               line.find(L'\t',tab+1)!=std::wstring::npos)return false;
            if(candidate.add(line.substr(0,tab),line.substr(tab+1))!=
               MutationResult::Applied)return false;
        }
        mItems=std::move(candidate.mItems);
        return true;
    }catch(...){return false;}
}

bool Store::saveTo(std::wstring const& path) const noexcept
{
    try{
        Store checked;
        for(auto const& item:mItems)
            if(checked.add(item.name,item.masks)!=MutationResult::Applied)
                return false;
        std::wstring text=L"schema=1\r\n";
        for(auto const& item:mItems)
            text+=item.name+L"\t"+item.masks+L"\r\n";
        std::string utf8;
        return wideToUtf8(text,utf8)&&writeAtomic(path,utf8);
    }catch(...){return false;}
}

bool Store::load() noexcept
{
    mItems.clear();
    const auto path=privatePath();
    if(path.empty())return false;
    const DWORD attrs=::GetFileAttributesW(path.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES){
        const auto error=::GetLastError();
        return error==ERROR_FILE_NOT_FOUND||error==ERROR_PATH_NOT_FOUND;
    }
    if(attrs&FILE_ATTRIBUTE_DIRECTORY)return false;
    return loadFrom(path);
}

bool Store::save() const noexcept
{
    const auto dir=directory();
    if(dir.empty())return false;
    if(!::CreateDirectoryW(dir.c_str(),nullptr)&&
       ::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
    const DWORD attrs=::GetFileAttributesW(dir.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES||
       !(attrs&FILE_ATTRIBUTE_DIRECTORY)||
       (attrs&FILE_ATTRIBUTE_REPARSE_POINT))return false;
    return saveTo(privatePath());
}

} // namespace fxfile::filterrules
