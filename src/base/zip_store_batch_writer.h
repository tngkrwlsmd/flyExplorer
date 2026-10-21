// F08 / EP10. Strict 2-8-file ZIP creation: default Store-only or optional
// per-member Deflate with Store fallback. No original/existing output overwrite.
// Windows runtime/GUI acceptance is not established by this source.
#pragma once
#include "zip_store_writer.h"
#include "zip_raw_deflate.h"
#include "zip_raw_deflate_compress.h"
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
inline constexpr wchar_t kDeflateArchiveName[]=L"flyExplorer-selection-deflate.zip";
enum class Compression { StoreOnly, DeflatePreferred };

enum class Status {
    Created, Cancelled, InvalidSource, DuplicateName, TooLarge,
    CannotRead, CompressionFailed, AlreadyExists, CannotWrite
};
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
    std::size_t fileCount=0;
    std::size_t deflatedFiles=0;
};
namespace detail {
struct Member final {
    std::string name;
    std::wstring leaf;
    std::vector<unsigned char> data;
    std::uint32_t crc=0;
    std::uint32_t originalSize=0;
    std::uint32_t localOffset=0;
    std::uint16_t method=0;
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
                         std::atomic_bool const* cancellation=nullptr,
                         Compression compression=Compression::StoreOnly,
                         std::wstring const& folderRoot={}) noexcept {
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
            member.originalSize=static_cast<std::uint32_t>(length);
            totalBytes+=length;
            members.push_back(std::move(member));
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        // Explicit folder mode: every selected file must be a direct child
        // of exactly the same normalized, non-reparse local folder.
        // The archive records "root/leaf", and lives beside that folder.
        std::string prefix;
        if(!folderRoot.empty()){
            if(!fxfile::zipinspect::detail::same(directory,folderRoot)){
                result.status=Status::InvalidSource;return result;
            }
            const std::wstring rootLeaf=
                std::filesystem::path(directory).filename().native();
            bool directoryEntry=false;
            if(rootLeaf.empty()||rootLeaf.size()>180u||
               !fxfile::zipinspect::detail::safeName(rootLeaf,directoryEntry)||
               directoryEntry){
                result.status=Status::InvalidSource;return result;
            }
            const int n=::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                rootLeaf.c_str(),static_cast<int>(rootLeaf.size()),
                nullptr,0,nullptr,nullptr);
            if(n<=0||n>256){
                result.status=Status::InvalidSource;return result;
            }
            prefix.resize(n);
            if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                rootLeaf.c_str(),static_cast<int>(rootLeaf.size()),
                prefix.data(),n,nullptr,nullptr)!=n){
                result.status=Status::InvalidSource;return result;
            }
            prefix.push_back('/');
            // Our strict extractor decodes at most 260 UTF-16 units
            // for the full name and stages within a classic MAX_PATH
            // directory; reject a ZIP we could not unpack ourselves.
            const std::wstring destinationParent=
                std::filesystem::path(directory).parent_path().native();
            for(auto& member:members){
                if(prefix.size()+member.name.size()>512u||
                   rootLeaf.size()+1u+member.leaf.size()>260u||
                   destinationParent.size()+64u+
                      rootLeaf.size()+member.leaf.size()>253u){
                    result.status=Status::InvalidSource;return result;
                }
                member.name.insert(0,prefix);
            }
        }
        // Both modes use deterministic filenames, never silent replacement.
        const wchar_t* archiveName=compression==Compression::DeflatePreferred?
            kDeflateArchiveName:kArchiveName;
        const std::wstring targetFolder=
            folderRoot.empty()?directory:
            std::filesystem::path(directory).parent_path().native();
        const auto destination=folderRoot.empty()?
            (std::filesystem::path(targetFolder)/archiveName):
            std::filesystem::path(directory+L".flyExplorer-folder.zip");
        const std::wstring target=destination.native();
        if(target.size()>253||
           ::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            result.status=target.size()>253?
                Status::InvalidSource:Status::AlreadyExists;
            return result;
        }
        // Read/check all originals first. Never stage a partial archive
        // until all Deflate candidates are self-verified with raw inflate.
        std::size_t deflatedFiles=0;
        if(compression==Compression::DeflatePreferred){
            for(auto& member:members){
                if(fxfile::zipstore::detail::cancelled(cancellation)){
                    result.status=Status::Cancelled;return result;
                }
                std::vector<unsigned char> compressed;
                if(!fxfile::ziprawdeflate::compressBounded(member.data,compressed)){
                    result.status=Status::CompressionFailed;return result;
                }
                const bool useDeflate=compressed.size()<member.data.size()&&
                    std::uint64_t(member.originalSize)<=
                    std::uint64_t(compressed.size())*
                    fxfile::ziprawdeflate::kMaxRatio;
                if(useDeflate){
                    std::vector<unsigned char> verified;
                    if(!fxfile::ziprawdeflate::inflateExact(
                           compressed.data(),compressed.size(),
                           member.originalSize,verified,cancellation)){
                        result.status=fxfile::zipstore::detail::cancelled(cancellation)?
                            Status::Cancelled:Status::CompressionFailed;
                        return result;
                    }
                    if(verified!=member.data){
                        result.status=Status::CompressionFailed;return result;
                    }
                    member.data=std::move(compressed);
                    member.method=8;
                    ++deflatedFiles;
                }
            }
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        std::size_t archiveCapacity=22;
        for(auto const& member:members){
            archiveCapacity+=member.data.size()+76u+member.name.size()*2u;
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
            const auto packed=static_cast<std::uint32_t>(member.data.size());
            const auto nameLength=static_cast<std::uint16_t>(member.name.size());
            member.localOffset=static_cast<std::uint32_t>(zip.size());
            fxfile::zipstore::detail::dword(zip,0x04034b50u);
            fxfile::zipstore::detail::word(zip,20);
            fxfile::zipstore::detail::word(zip,0x0800);
            fxfile::zipstore::detail::word(zip,member.method); // Store/Deflate
            fxfile::zipstore::detail::word(zip,0); // DOS time
            fxfile::zipstore::detail::word(zip,0); // DOS date
            fxfile::zipstore::detail::dword(zip,member.crc);
            fxfile::zipstore::detail::dword(zip,packed);
            fxfile::zipstore::detail::dword(zip,member.originalSize);
            fxfile::zipstore::detail::word(zip,nameLength);
            fxfile::zipstore::detail::word(zip,0);
            zip.insert(zip.end(),member.name.begin(),member.name.end());
            zip.insert(zip.end(),member.data.begin(),member.data.end());
        }
        const auto directoryOffset=static_cast<std::uint32_t>(zip.size());
        for(auto const& member:members){
            const auto packed=static_cast<std::uint32_t>(member.data.size());
            const auto nameLength=static_cast<std::uint16_t>(member.name.size());
            fxfile::zipstore::detail::dword(zip,0x02014b50u);
            fxfile::zipstore::detail::word(zip,20); // DOS creator
            fxfile::zipstore::detail::word(zip,20);
            fxfile::zipstore::detail::word(zip,0x0800);
            fxfile::zipstore::detail::word(zip,member.method); // Store/Deflate
            fxfile::zipstore::detail::word(zip,0);
            fxfile::zipstore::detail::word(zip,0);
            fxfile::zipstore::detail::dword(zip,member.crc);
            fxfile::zipstore::detail::dword(zip,packed);
            fxfile::zipstore::detail::dword(zip,member.originalSize);
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
        if(!::GetTempFileNameW(targetFolder.c_str(),L"fxm",0,staging.path)){
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
        result.deflatedFiles=deflatedFiles;
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.output.clear();result.fileCount=0;
            result.deflatedFiles=0;
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
        result.deflatedFiles=0;
        result.status=(error==ERROR_ALREADY_EXISTS||error==ERROR_FILE_EXISTS)?
            Status::AlreadyExists:Status::CannotWrite;
        return result;
    }catch(...){
        result.status=Status::CannotWrite;return result;
    }
}
// Direct children only. No nested directories, reparse points, implicit
// traversal, hidden recursion or existing-file modifications. The creator
// calls createMany with the same safety, CRC, Store/Deflate and cancel gates.
inline Result createFolder(std::wstring const& folder,
                           std::atomic_bool const* cancellation=nullptr,
                           Compression mode=Compression::DeflatePreferred) noexcept {
    Result result{};
    if(fxfile::zipstore::detail::cancelled(cancellation)){
        result.status=Status::Cancelled;return result;
    }
    try{
        const std::filesystem::path p(folder);
        const auto root=p.root_path().native();
        const auto leaf=p.filename().native();
        bool directoryEntry=false;
        if(folder.size()<7||folder.size()>195||root.size()!=3||
           root[1]!=L':'||root[2]!=L'\\'||
           ::GetDriveTypeW(root.c_str())!=DRIVE_FIXED||
           !p.is_absolute()||p.lexically_normal().native()!=folder||
           leaf.empty()||leaf.size()>180||
           !fxfile::zipinspect::detail::safeName(leaf,directoryEntry)||
           directoryEntry)return result;
        std::filesystem::path prefix=p.root_path();
        for(auto const& component:p.relative_path()){
            prefix/=component;
            const DWORD attributes=::GetFileAttributesW(prefix.c_str());
            if(attributes==INVALID_FILE_ATTRIBUTES||
               (attributes&FILE_ATTRIBUTE_REPARSE_POINT))return result;
        }
        const DWORD attr=::GetFileAttributesW(folder.c_str());
        if(attr==INVALID_FILE_ATTRIBUTES||
           !(attr&FILE_ATTRIBUTE_DIRECTORY)||
           (attr&FILE_ATTRIBUTE_REPARSE_POINT))return result;
        const std::wstring search=(p/L"*").native();
        WIN32_FIND_DATAW data{};
        const HANDLE found=::FindFirstFileW(search.c_str(),&data);
        if(found==INVALID_HANDLE_VALUE){
            result.status=Status::CannotRead;return result;
        }
        struct FindGuard final {
            HANDLE handle;
            ~FindGuard(){::FindClose(handle);}
        } finder{found};
        std::vector<std::wstring> files;
        do{
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            const std::wstring name(data.cFileName);
            if(name==L"."||name==L"..")continue;
            if(data.dwFileAttributes&
               (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)){
                result.status=Status::InvalidSource;return result;
            }
            if(files.size()>=kMaxFiles){
                result.status=Status::TooLarge;return result;
            }
            files.push_back((p/name).native());
        }while(::FindNextFileW(found,&data));
        if(::GetLastError()!=ERROR_NO_MORE_FILES){
            result.status=Status::CannotRead;return result;
        }
        if(files.size()<kMinFiles)return result;
        // Ordinal sort only; Windows case-insensitive name collision
        // rejection is performed explicitly in createMany().
        std::sort(files.begin(),files.end());
        return createMany(files,cancellation,mode,folder);
    }catch(...){
        result.status=Status::CannotWrite;return result;
    }
}
} // namespace fxfile::zipbatch
