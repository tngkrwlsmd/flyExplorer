#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "search_preset_store.h"
#include <algorithm>
#include <array>
#include <cwctype>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::searchpresets {
namespace {

std::wstring directory(){
    std::array<wchar_t,32768> b{};
    const auto n=::GetEnvironmentVariableW(
        L"LOCALAPPDATA",b.data(),static_cast<DWORD>(b.size()));
    if(!n||n>=b.size())return {};
    return std::wstring(b.data(),n)+L"\\flyExplorer";
}
bool bad(std::wstring const& v){
    return v.find_first_of(L"\r\n\t")!=std::wstring::npos||
           v.find(L'\0')!=std::wstring::npos;
}
bool sameNoCase(std::wstring const& a,std::wstring const& b){
    return ::CompareStringOrdinal(
        a.c_str(),static_cast<int>(a.size()),
        b.c_str(),static_cast<int>(b.size()),TRUE)==CSTR_EQUAL;
}
bool valid(Preset const& p){
    if(p.name.empty()||p.name.size()>Store::kMaxName||bad(p.name))return false;
    if(p.term.size()>Store::kMaxField||bad(p.term)||
       p.contentTerm.size()>Store::kMaxField||bad(p.contentTerm)||
       p.extension.size()>32||bad(p.extension)||
       p.minSizeKb.size()>20||bad(p.minSizeKb)||
       p.maxSizeKb.size()>20||bad(p.maxSizeKb)||
       p.modifiedAfter.size()>10||bad(p.modifiedAfter)||
       p.modifiedBefore.size()>10||bad(p.modifiedBefore))return false;
    return p.kind>=0&&p.kind<=2;
}
bool toUtf8(std::wstring const& input,std::string& output){
    output.clear();
    if(input.empty())return true;
    const int n=::WideCharToMultiByte(
        CP_UTF8,WC_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),nullptr,0,nullptr,nullptr);
    if(n<=0)return false;
    output.resize(static_cast<std::size_t>(n));
    return ::WideCharToMultiByte(
        CP_UTF8,WC_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),output.data(),n,nullptr,nullptr)==n;
}
bool fromUtf8(std::string const& input,std::wstring& output){
    output.clear();
    if(input.empty())return true;
    const int n=::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),nullptr,0);
    if(n<=0)return false;
    output.resize(static_cast<std::size_t>(n));
    return ::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,input.data(),
        static_cast<int>(input.size()),output.data(),n)==n;
}
bool readBytes(std::wstring const& path,std::vector<unsigned char>& bytes){
    HANDLE h=::CreateFileW(path.c_str(),GENERIC_READ,
        FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    LARGE_INTEGER size{};
    const bool ok=::GetFileSizeEx(h,&size)!=FALSE&&
        size.QuadPart>=0&&size.QuadPart<=256*1024;
    if(!ok){::CloseHandle(h);return false;}
    bytes.assign(static_cast<std::size_t>(size.QuadPart),0);
    DWORD used=0;
    const bool good=bytes.empty()||
        (::ReadFile(h,bytes.data(),static_cast<DWORD>(bytes.size()),
                    &used,nullptr)!=FALSE&&used==bytes.size());
    ::CloseHandle(h);return good;
}
bool writeAtomic(std::wstring const& path,std::string const& body){
    const auto tmp=path+L".tmp."+std::to_wstring(::GetCurrentProcessId())+
                   L"."+std::to_wstring(::GetTickCount64());
    HANDLE h=::CreateFileW(tmp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,
                           FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return false;
    DWORD used=0;
    bool good=body.empty()||
        (::WriteFile(h,body.data(),static_cast<DWORD>(body.size()),
                     &used,nullptr)!=FALSE&&used==body.size());
    if(good)good=::FlushFileBuffers(h)!=FALSE;
    if(!::CloseHandle(h))good=false;
    if(good)good=::MoveFileExW(
        tmp.c_str(),path.c_str(),
        MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
    if(!good)::DeleteFileW(tmp.c_str());
    return good;
}
std::vector<std::wstring> split(std::wstring const& line){
    std::vector<std::wstring> out;
    std::size_t start=0;
    for(;;){
        const auto tab=line.find(L'\t',start);
        out.push_back(line.substr(
            start,tab==std::wstring::npos?std::wstring::npos:tab-start));
        if(tab==std::wstring::npos)break;
        start=tab+1;
    }
    return out;
}

} // namespace

std::wstring Store::privatePath(){
    const auto d=directory();
    return d.empty()?L"":d+L"\\search-presets-v1.txt";
}

MutationResult Store::add(Preset value) noexcept{
    try{
        if(!valid(value))return MutationResult::Invalid;
        if(mItems.size()>=kMaxItems)return MutationResult::Full;
        if(std::any_of(mItems.begin(),mItems.end(),
           [&](Preset const& p){return sameNoCase(p.name,value.name);}))
            return MutationResult::Duplicate;
        mItems.push_back(std::move(value));return MutationResult::Applied;
    }catch(...){return MutationResult::Invalid;}
}
MutationResult Store::update(std::size_t index,Preset value) noexcept{
    try{
        if(index>=mItems.size())return MutationResult::NotFound;
        if(!valid(value))return MutationResult::Invalid;
        for(std::size_t i=0;i<mItems.size();++i)
            if(i!=index&&sameNoCase(mItems[i].name,value.name))
                return MutationResult::Duplicate;
        mItems[index]=std::move(value);return MutationResult::Applied;
    }catch(...){return MutationResult::Invalid;}
}
bool Store::erase(std::size_t index) noexcept{
    try{
        if(index>=mItems.size())return false;
        mItems.erase(mItems.begin()+static_cast<std::ptrdiff_t>(index));
        return true;
    }catch(...){return false;}
}

bool Store::loadFrom(std::wstring const& path) noexcept{
    try{
        std::vector<unsigned char> bytes;
        if(!readBytes(path,bytes))return false;
        std::wstring text;
        if(!fromUtf8(std::string(
            reinterpret_cast<char const*>(bytes.data()),bytes.size()),text))
            return false;
        std::wistringstream lines(text);
        std::wstring line;
        if(!std::getline(lines,line))return false;
        if(!line.empty()&&line.back()==L'\r')line.pop_back();
        const bool schema1=line==L"schema=1";
        const bool schema2=line==L"schema=2";
        if(!schema1&&!schema2)return false;
        Store candidate;
        while(std::getline(lines,line)){
            if(!line.empty()&&line.back()==L'\r')line.pop_back();
            if(line.empty())continue;
            auto f=split(line);
            if((schema1&&f.size()!=10)||(schema2&&f.size()!=11))return false;
            Preset p{};
            p.name=f[0];p.term=f[1];
            std::size_t offset=0;
            if(schema2){p.contentTerm=f[2];offset=1;}
            p.extension=f[2+offset];
            p.regex=f[3+offset]==L"1";p.caseSensitive=f[4+offset]==L"1";
            try{p.kind=std::stoi(f[5+offset]);}catch(...){return false;}
            p.minSizeKb=f[6+offset];p.maxSizeKb=f[7+offset];
            p.modifiedAfter=f[8+offset];p.modifiedBefore=f[9+offset];
            if((f[3+offset]!=L"0"&&f[3+offset]!=L"1")||
               (f[4+offset]!=L"0"&&f[4+offset]!=L"1")||
               candidate.add(std::move(p))!=MutationResult::Applied)
                return false;
        }
        mItems=std::move(candidate.mItems);return true;
    }catch(...){return false;}
}

bool Store::saveTo(std::wstring const& path) const noexcept{
    try{
        Store checked;
        for(auto const& p:mItems)
            if(checked.add(p)!=MutationResult::Applied)return false;
        std::wstring text=L"schema=2\r\n";
        for(auto const& p:mItems){
            text+=p.name+L"\t"+p.term+L"\t"+p.contentTerm+L"\t"+
                p.extension+L"\t"+
                (p.regex?L"1":L"0")+L"\t"+
                (p.caseSensitive?L"1":L"0")+L"\t"+
                std::to_wstring(p.kind)+L"\t"+
                p.minSizeKb+L"\t"+p.maxSizeKb+L"\t"+
                p.modifiedAfter+L"\t"+p.modifiedBefore+L"\r\n";
        }
        std::string utf8;
        return toUtf8(text,utf8)&&writeAtomic(path,utf8);
    }catch(...){return false;}
}

bool Store::load() noexcept{
    mItems.clear();
    const auto p=privatePath();
    if(p.empty())return false;
    const DWORD a=::GetFileAttributesW(p.c_str());
    if(a==INVALID_FILE_ATTRIBUTES){
        const auto e=::GetLastError();
        return e==ERROR_FILE_NOT_FOUND||e==ERROR_PATH_NOT_FOUND;
    }
    if(a&FILE_ATTRIBUTE_DIRECTORY)return false;
    return loadFrom(p);
}
bool Store::save() const noexcept{
    const auto d=directory();
    if(d.empty())return false;
    if(!::CreateDirectoryW(d.c_str(),nullptr)&&
       ::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
    const DWORD a=::GetFileAttributesW(d.c_str());
    if(a==INVALID_FILE_ATTRIBUTES||
       !(a&FILE_ATTRIBUTE_DIRECTORY)||
       (a&FILE_ATTRIBUTE_REPARSE_POINT))return false;
    return saveTo(privatePath());
}

} // namespace fxfile::searchpresets
