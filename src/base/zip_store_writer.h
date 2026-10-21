// F08/EP10: explicit one-file ZIP/Store creation (no compression).
// Bounded, same-directory, no overwrite, no Shell extension or extraction.
// Results are NOT acceptance until native Windows execution is authorized.
#pragma once
#include "zip_inspection.h"
#include <windows.h>
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace fxfile::zipstore {
inline constexpr std::uint32_t kMaxInputBytes=8u*1024u*1024u;

enum class Status { Created, InvalidSource, TooLarge, CannotRead,
                    AlreadyExists, CannotWrite };
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
};

namespace detail {
inline void word(std::vector<unsigned char>& b,std::uint16_t n) {
    b.push_back(static_cast<unsigned char>(n));
    b.push_back(static_cast<unsigned char>(n>>8));
}
inline void dword(std::vector<unsigned char>& b,std::uint32_t n) {
    word(b,static_cast<std::uint16_t>(n));
    word(b,static_cast<std::uint16_t>(n>>16));
}
inline std::uint32_t crc32(std::vector<unsigned char> const& data) noexcept {
    std::uint32_t crc=0xffffffffu;
    for(const auto byte:data) {
        crc^=byte;
        for(unsigned bit=0;bit<8;++bit)
            crc=(crc>>1)^(0xedb88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
inline bool safeSource(std::wstring const& name,std::wstring& parent,
                       std::wstring& leaf,std::string& utf8) {
    if(name.size()<7||name.size()>240||
       name.find(L'\0')!=std::wstring::npos)return false;
    try {
        const std::filesystem::path path(name);
        const auto root=path.root_path().native();
        if(root.size()!=3||root[1]!=L':'||root[2]!=L'\\'||
           ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED||
           !path.is_absolute()||path.lexically_normal().native()!=name)
            return false;
        leaf=path.filename().native();
        bool directory=false;
        if(leaf.empty()||leaf.size()>180||
           !fxfile::zipinspect::detail::safeName(leaf,directory)||directory)
            return false;
        std::filesystem::path component=path.root_path();
        for(auto const& part:path.relative_path()) {
            component/=part;
            const DWORD attr=::GetFileAttributesW(component.c_str());
            if(attr==INVALID_FILE_ATTRIBUTES||
               (attr&FILE_ATTRIBUTE_REPARSE_POINT))return false;
        }
        parent=path.parent_path().native();
        const int length=::WideCharToMultiByte(
            CP_UTF8,WC_ERR_INVALID_CHARS,leaf.c_str(),
            static_cast<int>(leaf.size()),nullptr,0,nullptr,nullptr);
        if(length<=0||length>512)return false;
        utf8.resize(length);
        if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
           leaf.c_str(),static_cast<int>(leaf.size()),
           utf8.data(),length,nullptr,nullptr)!=length)return false;
        return true;
    }catch(...){return false;}
}
inline bool writeAll(HANDLE h,std::vector<unsigned char> const& bytes) noexcept {
    std::size_t pos=0;
    while(pos<bytes.size()) {
        const DWORD chunk=static_cast<DWORD>(
            (std::min)(bytes.size()-pos,std::size_t{65536}));
        DWORD written=0;
        if(!::WriteFile(h,bytes.data()+pos,chunk,&written,nullptr)||
           written==0||written>chunk)return false;
        pos+=written;
    }
    return ::FlushFileBuffers(h)!=FALSE;
}
} // namespace detail

inline Result createOne(std::wstring const& source) noexcept {
    Result result{};
    std::wstring parent,leaf;
    std::string encoded;
    if(!detail::safeSource(source,parent,leaf,encoded))
        return result;
    // The destination is deterministic and same-directory. Never choose a
    // different name silently or overwrite a pre-existing file.
    const std::wstring target=source+L".zip";
    if(target.size()>253u){result.status=Status::InvalidSource;return result;}
    try{
        fxfile::zipinspect::detail::Handle reader;
        reader.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
                   nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
        if(reader.h==INVALID_HANDLE_VALUE){
            result.status=Status::CannotRead;return result;
        }
        BY_HANDLE_FILE_INFORMATION info{};
        if(!::GetFileInformationByHandle(reader.h,&info)||
           (info.dwFileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|
                                   FILE_ATTRIBUTE_DIRECTORY))){
            result.status=Status::InvalidSource;return result;
        }
        LARGE_INTEGER length{};
        if(!::GetFileSizeEx(reader.h,&length)||length.QuadPart<0){
            result.status=Status::CannotRead;return result;
        }
        if(static_cast<std::uint64_t>(length.QuadPart)>kMaxInputBytes){
            result.status=Status::TooLarge;return result;
        }
        std::vector<unsigned char> content(
            static_cast<std::size_t>(length.QuadPart));
        std::size_t pos=0;
        while(pos<content.size()){
            DWORD read=0;
            const DWORD chunk=static_cast<DWORD>(
                (std::min)(content.size()-pos,std::size_t{65536}));
            if(!::ReadFile(reader.h,content.data()+pos,chunk,&read,nullptr)||
               read==0||read>chunk){
                result.status=Status::CannotRead;return result;
            }
            pos+=read;
        }
        LARGE_INTEGER end{};
        if(!::GetFileSizeEx(reader.h,&end)||end.QuadPart!=length.QuadPart){
            result.status=Status::CannotRead;return result;
        }
        if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            result.status=Status::AlreadyExists;return result;
        }

        const auto count=static_cast<std::uint32_t>(content.size());
        const auto nameSize=static_cast<std::uint16_t>(encoded.size());
        const auto crc=detail::crc32(content);
        std::vector<unsigned char> zip;
        zip.reserve(30u+nameSize+count+46u+nameSize+22u);
        const auto name=[&]{
            zip.insert(zip.end(),encoded.begin(),encoded.end());
        };
        // Local file header: UTF-8, method 0/Store, no data descriptor.
        detail::dword(zip,0x04034b50u);
        detail::word(zip,20);detail::word(zip,0x0800);detail::word(zip,0);
        detail::word(zip,0);detail::word(zip,0);
        detail::dword(zip,crc);detail::dword(zip,count);detail::dword(zip,count);
        detail::word(zip,nameSize);detail::word(zip,0);
        name();
        zip.insert(zip.end(),content.begin(),content.end());
        const auto directoryStart=static_cast<std::uint32_t>(zip.size());
        // Central directory with one DOS regular file.
        detail::dword(zip,0x02014b50u);
        detail::word(zip,20);detail::word(zip,20);
        detail::word(zip,0x0800);detail::word(zip,0);
        detail::word(zip,0);detail::word(zip,0);
        detail::dword(zip,crc);detail::dword(zip,count);detail::dword(zip,count);
        detail::word(zip,nameSize);detail::word(zip,0);detail::word(zip,0);
        detail::word(zip,0);detail::word(zip,0);
        detail::dword(zip,0);detail::dword(zip,0);
        name();
        // EOCD: exactly one entry, no optional comment, no ZIP64.
        detail::dword(zip,0x06054b50u);
        detail::word(zip,0);detail::word(zip,0);
        detail::word(zip,1);detail::word(zip,1);
        detail::dword(zip,46u+nameSize);
        detail::dword(zip,directoryStart);
        detail::word(zip,0);
        // A temporary file is created in the same directory and made
        // durable before atomic publication. Failure cleans only our temp.
        wchar_t temp[MAX_PATH]{};
        if(!::GetTempFileNameW(parent.c_str(),L"fxz",0,temp)){
            result.status=Status::CannotWrite;return result;
        }
        const std::wstring ownedTemp=temp;
        bool complete=false;
        {
            fxfile::zipinspect::detail::Handle writer;
            writer.h=::CreateFileW(temp,GENERIC_WRITE,0,nullptr,
                       OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(writer.h!=INVALID_HANDLE_VALUE){
                BY_HANDLE_FILE_INFORMATION attributes{};
                if(::GetFileInformationByHandle(writer.h,&attributes)&&
                   !(attributes.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&
                   detail::writeAll(writer.h,zip))
                    complete=true;
            }
        }
        if(complete){
            // MOVEFILE_REPLACE_EXISTING deliberately absent.
            if(::MoveFileExW(ownedTemp.c_str(),target.c_str(),
                             MOVEFILE_WRITE_THROUGH)){
                result.status=Status::Created;
                result.output=target;
                return result;
            }
        }
        const DWORD error=::GetLastError();
        ::DeleteFileW(ownedTemp.c_str()); // only our reserved staging file
        result.status=(error==ERROR_FILE_EXISTS||
                       error==ERROR_ALREADY_EXISTS)?
                      Status::AlreadyExists:Status::CannotWrite;
        return result;
    }catch(...){
        result.status=Status::CannotWrite;return result;
    }
}
} // namespace fxfile::zipstore
