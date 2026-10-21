// F08/EP10. Read-only, deliberately restricted ZIP metadata inspector.
// No decompression or archive extraction: a valid inspection is NOT proof
// that uncompressed file content or its CRC is safe/correct.
#pragma once
#include <windows.h>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cwctype>
#include <filesystem>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::zipinspect {
inline constexpr std::size_t kMaxZipBytes=16u*1024u*1024u;
inline constexpr std::size_t kMaxEntries=128;
inline constexpr std::uint64_t kMaxExpandedBytes=64ull*1024ull*1024ull;
inline constexpr std::uint32_t kMaxSingleBytes=32u*1024u*1024u;

struct Result final {
    enum class Status { Accepted, InvalidPath, CannotRead, TooLarge,
                        UnsafeEntry, Unsupported, Malformed };
    Status status=Status::Malformed;
    std::size_t entries=0;
    std::uint64_t expandedBytes=0;
    std::vector<std::wstring> names{};
};
namespace detail {
struct Handle final {
    HANDLE h=INVALID_HANDLE_VALUE;
    ~Handle(){if(h!=INVALID_HANDLE_VALUE)::CloseHandle(h);}
};
inline std::uint16_t u16(std::vector<unsigned char> const& b,std::size_t p){
    return std::uint16_t(b[p])|(std::uint16_t(b[p+1])<<8);
}
inline std::uint32_t u32(std::vector<unsigned char> const& b,std::size_t p){
    return std::uint32_t(u16(b,p))|(std::uint32_t(u16(b,p+2))<<16);
}
inline bool span(std::size_t start,std::size_t size,std::size_t limit){
    return start<=limit&&size<=limit-start;
}
inline bool same(std::wstring const& a,std::wstring const& b){
    if(a.size()!=b.size())return false;
    for(std::size_t i=0;i<a.size();++i)
        if(std::towlower(a[i])!=std::towlower(b[i]))return false;
    return true;
}
inline bool source(std::wstring const& name){
    if(name.size()<7||name.size()>1024||name.find(L'\0')!=std::wstring::npos||
       !((name[0]>=L'A'&&name[0]<=L'Z')||
         (name[0]>=L'a'&&name[0]<=L'z'))||
       name[1]!=L':'||name[2]!=L'\\')return false;
    try{
        std::filesystem::path path(name);
        auto root=path.root_path().native();
        if(root.size()!=3||::GetDriveTypeW(root.c_str())!=DRIVE_FIXED||
           !path.is_absolute()||path.lexically_normal().native()!=name||
           !same(path.extension().native(),L".zip"))return false;
        std::filesystem::path part=path.root_path();
        for(auto const& segment:path.relative_path()){
            part/=segment;
            const auto a=::GetFileAttributesW(part.c_str());
            if(a==INVALID_FILE_ATTRIBUTES||(a&FILE_ATTRIBUTE_REPARSE_POINT))
                return false;
        }
        const auto a=::GetFileAttributesW(path.c_str());
        return a!=INVALID_FILE_ATTRIBUTES&&!(a&FILE_ATTRIBUTE_DIRECTORY);
    }catch(...){return false;}
}
inline bool decode(std::vector<unsigned char> const& data,
                   std::size_t start,std::size_t length,bool utf8,
                   std::wstring& out){
    if(!length||length>512||!span(start,length,data.size()))return false;
    const char* ptr=reinterpret_cast<char const*>(data.data()+start);
    if(!utf8){
        for(std::size_t i=0;i<length;++i)
            if(static_cast<unsigned char>(ptr[i])>=0x80)return false;
    }
    const int n=::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,
                      ptr,static_cast<int>(length),nullptr,0);
    if(!n||n>260)return false;
    out.resize(n);
    return ::MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,
                      ptr,static_cast<int>(length),out.data(),n)==n;
}
inline bool reserved(std::wstring segment){
    if(segment.empty()||segment==L"."||segment==L".."|| 
       segment.back()==L' '||segment.back()==L'.')return true;
    for(wchar_t c:segment)
        if(c<32||c==127||c==L'\\'||c==L':'||c==L'*'||c==L'?'||
           c==L'"'||c==L'<'||c==L'>'||c==L'|')return true;
    const auto dot=segment.find(L'.');
    if(dot!=std::wstring::npos)segment.resize(dot);
    for(auto& c:segment)c=std::towupper(c);
    if(segment==L"CON"||segment==L"PRN"||segment==L"AUX"||
       segment==L"NUL"||segment==L"CLOCK$")return true;
    if(segment.size()==4&&(segment.substr(0,3)==L"COM"||
                           segment.substr(0,3)==L"LPT")&&
       ((segment[3]>=L'0'&&segment[3]<=L'9')||
        segment[3]==L'\u00b9'||segment[3]==L'\u00b2'||
        segment[3]==L'\u00b3'))return true;
    return false;
}
inline bool safeName(std::wstring const& name,bool& directory){
    if(name.empty()||name.size()>260||name[0]==L'/'||
       name.find(L'\\')!=std::wstring::npos)return false;
    directory=name.back()==L'/';
    std::size_t p=0;
    while(p<name.size()){
        const auto slash=name.find(L'/',p);
        const auto end=slash==std::wstring::npos?name.size():slash;
        if(reserved(name.substr(p,end-p)))return false;
        if(slash==std::wstring::npos)return true;
        p=slash+1;
        if(p==name.size())return directory;
    }
    return false;
}
} // namespace detail

inline Result inspect(std::wstring const& source) noexcept {
    using Status=Result::Status;
    Result out{};
    try{
        if(!detail::source(source)){out.status=Status::InvalidPath;return out;}
        detail::Handle file;
        file.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,
                 OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,
                 nullptr);
        if(file.h==INVALID_HANDLE_VALUE){
            out.status=Status::CannotRead;return out;
        }
        LARGE_INTEGER size{};
        if(!::GetFileSizeEx(file.h,&size)||size.QuadPart<22){
            out.status=Status::Malformed;return out;
        }
        if(static_cast<std::uint64_t>(size.QuadPart)>kMaxZipBytes){
            out.status=Status::TooLarge;return out;
        }
        const std::size_t count=static_cast<std::size_t>(size.QuadPart);
        std::vector<unsigned char> bytes(count);
        std::size_t pos=0;
        while(pos<count){
            DWORD read=0;
            const DWORD needed=static_cast<DWORD>((std::min)(count-pos,std::size_t{65536}));
            if(!::ReadFile(file.h,bytes.data()+pos,needed,&read,nullptr)||read==0){
                out.status=Status::CannotRead;return out;
            }
            pos+=read;
        }
        LARGE_INTEGER again{};
        if(!::GetFileSizeEx(file.h,&again)||again.QuadPart!=size.QuadPart){
            out.status=Status::CannotRead;return out;
        }
        // EOCD must end at EOF, including its bounded optional comment.
        std::size_t eocd=count;
        const std::size_t bottom=count>(65535u+22u)?count-(65535u+22u):0;
        for(std::size_t i=count-22;;--i){
            if(detail::u32(bytes,i)==0x06054b50u&&
               detail::span(i,22u+detail::u16(bytes,i+20),count)&&
               i+22u+detail::u16(bytes,i+20)==count){
                eocd=i;break;
            }
            if(i==bottom)break;
        }
        if(eocd==count){out.status=Status::Malformed;return out;}
        if(detail::u16(bytes,eocd+4)!=0||detail::u16(bytes,eocd+6)!=0||
           detail::u16(bytes,eocd+8)!=detail::u16(bytes,eocd+10)){
            out.status=Status::Unsupported;return out;
        }
        const auto entries=detail::u16(bytes,eocd+10);
        if(entries==0||entries>kMaxEntries||entries==0xffffu){
            out.status=Status::Unsupported;return out;
        }
        const auto cdBytes=detail::u32(bytes,eocd+12);
        const auto cdStart=detail::u32(bytes,eocd+16);
        if(cdBytes==0xffffffffu||cdStart==0xffffffffu||
           !detail::span(cdStart,cdBytes,eocd)||cdStart+cdBytes!=eocd){
            out.status=Status::Unsupported;return out;
        }
        std::size_t cursor=cdStart;
        std::vector<std::pair<std::size_t,std::size_t>> intervals;
        std::vector<std::pair<std::wstring,bool>> names;
        for(std::size_t n=0;n<entries;++n){
            if(!detail::span(cursor,46,cdStart+cdBytes)||
               detail::u32(bytes,cursor)!=0x02014b50u){
                out.status=Status::Malformed;return out;
            }
            const auto flags=detail::u16(bytes,cursor+8);
            const auto method=detail::u16(bytes,cursor+10);
            const auto crc=detail::u32(bytes,cursor+16);
            const auto compressed=detail::u32(bytes,cursor+20);
            const auto expanded=detail::u32(bytes,cursor+24);
            const auto nameLen=detail::u16(bytes,cursor+28);
            const auto extra=detail::u16(bytes,cursor+30);
            const auto comment=detail::u16(bytes,cursor+32);
            const auto startDisk=detail::u16(bytes,cursor+34);
            const auto extAttrs=detail::u32(bytes,cursor+38);
            const auto localOffset=detail::u32(bytes,cursor+42);
            const bool utf8=(flags&(1u<<11))!=0;
            if(flags&~(1u<<11) || (method!=0&&method!=8) ||
               startDisk||localOffset==0xffffffffu||
               compressed==0xffffffffu||expanded==0xffffffffu){
                out.status=Status::Unsupported;return out;
            }
            const std::size_t span=46u+nameLen+extra+comment;
            if(!detail::span(cursor,span,cdStart+cdBytes)){
                out.status=Status::Malformed;return out;
            }
            std::wstring decoded;
            if(!detail::decode(bytes,cursor+46,nameLen,utf8,decoded)){
                out.status=Status::Unsupported;return out;
            }
            bool directory=false;
            if(!detail::safeName(decoded,directory)){
                out.status=Status::UnsafeEntry;return out;
            }
            const auto unixMode=(extAttrs>>16)&0170000u;
            const auto origin=(detail::u16(bytes,cursor+4)>>8);
            if((origin==3&&unixMode!=0&&unixMode!=0100000u&&
                unixMode!=0040000u)||
               (extAttrs&FILE_ATTRIBUTE_REPARSE_POINT)){
                out.status=Status::UnsafeEntry;return out;
            }
            if(expanded>kMaxSingleBytes||compressed>kMaxZipBytes||
               out.expandedBytes>kMaxExpandedBytes-expanded||
               (expanded&&(!compressed||expanded>std::uint64_t(compressed)*100u))||
               (method==0&&compressed!=expanded)||
               (directory&&(compressed||expanded))||
               (origin==3&&unixMode==0040000u&&!directory)||
               (origin==3&&unixMode==0100000u&&directory)){
                out.status=Status::TooLarge;return out;
            }
            // Verify that each local header names exactly the same entry and
            // no local data overlaps another entry or the central directory.
            if(!detail::span(localOffset,30u,cdStart)||
               detail::u32(bytes,localOffset)!=0x04034b50u||
               detail::u16(bytes,localOffset+6)!=flags||
               detail::u16(bytes,localOffset+8)!=method||
               detail::u32(bytes,localOffset+14)!=crc||
               detail::u32(bytes,localOffset+18)!=compressed||
               detail::u32(bytes,localOffset+22)!=expanded||
               detail::u16(bytes,localOffset+26)!=nameLen){
                out.status=Status::Malformed;return out;
            }
            const auto localName=std::size_t(localOffset)+30u;
            const auto localExtra=detail::u16(bytes,localOffset+28);
            const std::size_t dataBegin=localName+nameLen+localExtra;
            if(!detail::span(localName,nameLen+localExtra,cdStart)||
               !std::equal(bytes.begin()+cursor+46,
                           bytes.begin()+cursor+46+nameLen,
                           bytes.begin()+localName)||
               !detail::span(dataBegin,compressed,cdStart)){
                out.status=Status::Malformed;return out;
            }
            intervals.push_back({localOffset,dataBegin+compressed});
            names.push_back({std::move(decoded),directory});
            out.expandedBytes+=expanded;
            cursor+=span;
        }
        if(cursor!=cdStart+cdBytes){
            out.status=Status::Malformed;return out;
        }
        std::sort(intervals.begin(),intervals.end());
        for(std::size_t i=1;i<intervals.size();++i)
            if(intervals[i].first<intervals[i-1].second){
                out.status=Status::UnsafeEntry;return out;
            }
        // Windows is case-insensitive for the supported paths. Reject both
        // duplicate destinations and entries beneath a file-shaped parent.
        for(std::size_t i=0;i<names.size();++i){
            auto const& a=names[i].first;
            for(std::size_t j=0;j<i;++j){
                auto const& b=names[j].first;
                if(detail::same(a,b)){
                    out.status=Status::UnsafeEntry;return out;
                }
                if(!names[j].second&&a.size()>b.size()&&
                   a[b.size()]==L'/'&&
                   detail::same(a.substr(0,b.size()),b)){
                    out.status=Status::UnsafeEntry;return out;
                }
                if(!names[i].second&&b.size()>a.size()&&
                   b[a.size()]==L'/'&&
                   detail::same(b.substr(0,a.size()),a)){
                    out.status=Status::UnsafeEntry;return out;
                }
            }
        }
        out.entries=names.size();
        out.names.reserve(names.size());
        for(auto& item:names)out.names.push_back(std::move(item.first));
        out.status=Status::Accepted;
        return out;
    }catch(...){
        out=Result{};
        out.status=Status::Malformed;
        return out;
    }
}
} // namespace fxfile::zipinspect
