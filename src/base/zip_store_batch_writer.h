// F08 / EP10. Explicitly selected 2-8 flat local files into a ZIP Store
// archive named flyExplorer-selection.zip in their source directory.
// This neither compresses nor extracts data; NO existing file is overwritten.
// Windows runtime/GUI acceptance is not established by this source.
#pragma once
#include "zip_store_writer.h"
#include <windows.h>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::zipbatch {
inline constexpr std::size_t kMinFiles=2;
inline constexpr std::size_t kMaxFiles=8;
inline constexpr std::uint64_t kMaxTotalBytes=8ull*1024ull*1024ull;
inline constexpr wchar_t kArchiveName[]=L"flyExplorer-selection.zip";

enum class Status {
    Created, Cancelled, InvalidSource, DuplicateName, TooLarge,
    CannotRead, AlreadyExists, CannotWrite
};
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
    std::size_t fileCount=0;
};
namespace detail {
struct Member final {
    std::string name;
    std::wstring leaf;
    std::vector<unsigned char> data;
    std::uint32_t crc=0;
    std::uint32_t localOffset=0;
};
inline bool unchanged(BY_HANDLE_FILE_INFORMATION const& before,
                      BY_HANDLE_FILE_INFORMATION const& after) noexcept {
    return before.nFileSizeHigh==after.nFileSizeHigh&&
           before.nFileSizeLow==after.nFileSizeLow&&
           before.ftLastWriteTime.dwHighDateTime==
               after.ftLastWriteTime.dwHighDateTime&&
           before.ftLastWriteTime.dwLowDateTime==
               after.ftLastWriteTime.dwLowDateTime;
}
} // namespace detail

inline Result createMany(std::vector<std::wstring> const& paths,
                         std::atomic_bool const* cancellation=nullptr) noexcept {
    Result result{};
    if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
    if(paths.size()<kMinFiles||paths.size()>kMaxFiles)return result;
    try{
        std::vector<detail::Member> members;
        members.reserve(paths.size());
        std::wstring directory;
        std::uint64_t totalBytes=0;
        // Finish all source reads and validation before creating any output.
        for(auto const& source:paths){
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            std::wstring parent,leaf;
            std::string encoded;
            if(!fxfile::zipstore::detail::safeSource(source,parent,leaf,encoded)){
                result.status=Status::InvalidSource;return result;
            }
            if(directory.empty())directory=parent;
            else if(!fxfile::zipinspect::detail::same(directory,parent)){
                result.status=Status::InvalidSource;return result;
            }
            for(auto const& prior:members){
                if(fxfile::zipinspect::detail::same(prior.leaf,leaf)){
                    result.status=Status::DuplicateName;return result;
                }
            }
            fxfile::zipinspect::detail::Handle handle;
            handle.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
                 nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(handle.h==INVALID_HANDLE_VALUE){
                result.status=Status::CannotRead;return result;
            }
            BY_HANDLE_FILE_INFORMATION before{};
            if(!::GetFileInformationByHandle(handle.h,&before)||
               (before.dwFileAttributes&
                (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))){
                result.status=Status::InvalidSource;return result;
            }
            LARGE_INTEGER size{};
            if(!::GetFileSizeEx(handle.h,&size)||size.QuadPart<0){
                result.status=Status::CannotRead;return result;
            }
            const auto length=static_cast<std::uint64_t>(size.QuadPart);
            if(length>kMaxTotalBytes-totalBytes){
                result.status=Status::TooLarge;return result;
            }
            detail::Member member{};
            member.name=std::move(encoded);
            member.leaf=std::move(leaf);
            member.data.resize(static_cast<std::size_t>(length));
            std::size_t offset=0;
            while(offset<member.data.size()){
                if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
                DWORD read=0;
                const DWORD desired=static_cast<DWORD>(
                    (std::min)(member.data.size()-offset,std::size_t{65536}));
                if(!::ReadFile(handle.h,member.data.data()+offset,
                               desired,&read,nullptr)||!read||read>desired){
                    result.status=Status::CannotRead;return result;
                }
                offset+=read;
            }
            LARGE_INTEGER afterSize{};
            BY_HANDLE_FILE_INFORMATION after{};
            if(!::GetFileSizeEx(handle.h,&afterSize)||
               afterSize.QuadPart!=size.QuadPart||
               !::GetFileInformationByHandle(handle.h,&after)||
               !detail::unchanged(before,after)){
                result.status=Status::CannotRead;return result;
            }
            member.crc=fxfile::zipstore::detail::crc32(member.data);
            totalBytes+=length;
            members.push_back(std::move(member));
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        // A deterministic file name is deliberate: never silently find an
        // unused name that the user did not request.
        const auto destination=(std::filesystem::path(directory)/kArchiveName);
        const std::wstring target=destination.native();
        if(target.size()>253||
           ::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            result.status=target.size()>253?
                Status::InvalidSource:Status::AlreadyExists;
            return result;
        }
        std::size_t archiveCapacity=static_cast<std::size_t>(totalBytes)+22;
        for(auto const& member:members){
            archiveCapacity+=76u+member.name.size()*2u;
        }
        if(archiveCapacity>fxfile::zipinspect::kMaxZipBytes){
            result.status=Status::TooLarge;return result;
        }
        std::vector<unsigned char> zip;
        zip.reserve(archiveCapacity);
        for(auto& member:members){
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            const auto length=static_cast<std::uint32_t>(member.data.size());
            const auto nameLength=static_cast<std::uint16_t>(member.name.size());
            member.localOffset=static_cast<std::uint32_t>(zip.size());
            fxfile::zipstore::detail::dword(zip,0x04034b50u);
            fxfile::zipstore::detail::word(zip,20);
            fxfile::zipstore::detail::word(zip,0x0800);
            fxfile::zipstore::detail::word(zip,0); // Store
            fxfile::zipstore::detail::word(zip,0); // DOS time
            fxfile::zipstore::detail::word(zip,0); // DOS date
            fxfile::zipstore::detail::dword(zip,member.crc);
            fxfile::zipstore::detail::dword(zip,length);
            fxfile::zipstore::detail::dword(zip,length);
            fxfile::zipstore::detail::word(zip,nameLength);
            fxfile::zipstore::detail::word(zip,0);
            zip.insert(zip.end(),member.name.begin(),member.name.end());
            zip.insert(zip.end(),member.data.begin(),member.data.end());
        }
        const auto directoryOffset=static_cast<std::uint32_t>(zip.size());
        for(auto const& member:members){
            const auto length=static_cast<std::uint32_t>(member.data.size());
            const auto nameLength=static_cast<std::uint16_t>(member.name.size());
            fxfile::zipstore::detail::dword(zip,0x02014b50u);
            fxfile::zipstore::detail::word(zip,20); // DOS creator
            fxfile::zipstore::detail::word(zip,20);
            fxfile::zipstore::detail::word(zip,0x0800);
            fxfile::zipstore::detail::word(zip,0); // Store
            fxfile::zipstore::detail::word(zip,0);
            fxfile::zipstore::detail::word(zip,0);
            fxfile::zipstore::detail::dword(zip,member.crc);
            fxfile::zipstore::detail::dword(zip,length);
            fxfile::zipstore::detail::dword(zip,length);
            fxfile::zipstore::detail::word(zip,nameLength);
            fxfile::zipstore::detail::word(zip,0); // extra
            fxfile::zipstore::detail::word(zip,0); // comment
            fxfile::zipstore::detail::word(zip,0); // disk
            fxfile::zipstore::detail::word(zip,0); // internal attrs
            fxfile::zipstore::detail::dword(zip,0); // external attrs
            fxfile::zipstore::detail::dword(zip,member.localOffset);
            zip.insert(zip.end(),member.name.begin(),member.name.end());
        }
        const auto directorySize=
            static_cast<std::uint32_t>(zip.size()-directoryOffset);
        const auto fileCount=static_cast<std::uint16_t>(members.size());
        fxfile::zipstore::detail::dword(zip,0x06054b50u);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,fileCount);
        fxfile::zipstore::detail::word(zip,fileCount);
        fxfile::zipstore::detail::dword(zip,directorySize);
        fxfile::zipstore::detail::dword(zip,directoryOffset);
        fxfile::zipstore::detail::word(zip,0);
        if(zip.size()!=archiveCapacity){
            result.status=Status::CannotWrite;return result;
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        fxfile::zipstore::detail::Staging staging;
        if(!::GetTempFileNameW(directory.c_str(),L"fxm",0,staging.path)){
            result.status=Status::CannotWrite;return result;
        }
        staging.owned=true;
        bool flushed=false;
        {
            fxfile::zipinspect::detail::Handle writer;
            writer.h=::CreateFileW(staging.path,GENERIC_WRITE,0,nullptr,
                         OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(writer.h!=INVALID_HANDLE_VALUE){
                BY_HANDLE_FILE_INFORMATION info{};
                if(::GetFileInformationByHandle(writer.h,&info)&&
                   info.nNumberOfLinks==1&&
                   !(info.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&
                   fxfile::zipstore::detail::writeAll(writer.h,zip,cancellation))
                    flushed=true;
            }
        }
        if(!flushed){
            result.status=fxfile::zipstore::detail::cancelled(cancellation)?
                Status::Cancelled:Status::CannotWrite;
            return result;
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        // Prepare all user-visible result allocations before publication.
        result.output=target;
        result.fileCount=members.size();
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.output.clear();result.fileCount=0;
            result.status=Status::Cancelled;return result;
        }
        // No rollback if the final rename has already committed.
        if(::MoveFileExW(staging.path,target.c_str(),
                         MOVEFILE_WRITE_THROUGH)){
            staging.owned=false;
            result.status=Status::Created;
            return result;
        }
        const DWORD error=::GetLastError();
        result.output.clear();
        result.fileCount=0;
        result.status=(error==ERROR_ALREADY_EXISTS||error==ERROR_FILE_EXISTS)?
            Status::AlreadyExists:Status::CannotWrite;
        return result;
    }catch(...){
        result.status=Status::CannotWrite;return result;
    }
}
} // namespace fxfile::zipbatch
