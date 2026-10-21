// F08 / EP10. Strict 2-8-file ZIP creation: default Store-only or optional
// per-member Deflate with Store fallback. One root and up to 3 child dirs.
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
inline constexpr std::size_t kMaxChildFolders=3;
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
    std::wstring child; // empty or shared immediate subfolder of folderRoot
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
        std::wstring directory=folderRoot;
        std::vector<std::wstring> allowedChildren;
        allowedChildren.reserve(kMaxChildFolders);
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
            std::wstring child;
            if(folderRoot.empty()){
                if(directory.empty())directory=parent;
                else if(!fxfile::zipinspect::detail::same(directory,parent)){
                    result.status=Status::InvalidSource;return result;
                }
            }else if(!fxfile::zipinspect::detail::same(folderRoot,parent)){
                if(!fxfile::zipinspect::detail::same(
                        std::filesystem::path(parent).parent_path().native(),
                        folderRoot)){
                    result.status=Status::InvalidSource;return result;
                }
                child=std::filesystem::path(parent).filename().native();
                bool isDirectoryEntry=false;
                if(child.empty()||child.size()>180u||
                   !fxfile::zipinspect::detail::safeName(
                        child,isDirectoryEntry)||isDirectoryEntry){
                    result.status=Status::InvalidSource;return result;
                }
                const bool known=std::any_of(
                    allowedChildren.begin(),allowedChildren.end(),
                    [&](std::wstring const& x){
                        return fxfile::zipinspect::detail::same(x,child);
                    });
                if(!known){
                    if(allowedChildren.size()>=kMaxChildFolders){
                        result.status=Status::InvalidSource;return result;
                    }
                    allowedChildren.push_back(child);
                }
            }
            for(auto const& prior:members){
                if(fxfile::zipinspect::detail::same(prior.leaf,leaf)&&
                   fxfile::zipinspect::detail::same(prior.child,child)){
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
            member.child=std::move(child);
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
        // Explicit folder mode permits direct files and files under one
        // child directory. Never normalize ZIP names or follow other roots.
        // Output is one sibling ZIP containing root/[child/]leaf entries.
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
                std::string entryPrefix=prefix;
                if(!member.child.empty()){
                    const int childBytes=::WideCharToMultiByte(
                        CP_UTF8,WC_ERR_INVALID_CHARS,
                        member.child.c_str(),
                        static_cast<int>(member.child.size()),
                        nullptr,0,nullptr,nullptr);
                    if(childBytes<=0||childBytes>512u){
                        result.status=Status::InvalidSource;return result;
                    }
                    const auto start=entryPrefix.size();
                    entryPrefix.resize(start+childBytes);
                    if(::WideCharToMultiByte(
                            CP_UTF8,WC_ERR_INVALID_CHARS,
                            member.child.c_str(),
                            static_cast<int>(member.child.size()),
                            entryPrefix.data()+start,childBytes,
                            nullptr,nullptr)!=childBytes){
                        result.status=Status::InvalidSource;return result;
                    }
                    entryPrefix.push_back('/');
                }
                const auto innerUnits=member.child.empty()?0u:
                    member.child.size()+1u;
                if(entryPrefix.size()+member.name.size()>512u||
                   rootLeaf.size()+1u+innerUnits+
                     member.leaf.size()>260u||
                   destinationParent.size()+64u+
                     rootLeaf.size()+innerUnits+member.leaf.size()>253u){
                    result.status=Status::InvalidSource;return result;
                }
                member.name.insert(0,entryPrefix);
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
// One enumerated root and up to 3 immediate child directories.
// Never recurse. Any deeper directory, fourth child directory or reparse
// item rejects the entire operation; no existing file is altered.
// createMany revalidates every path/CRC and owns the atomic ZIP publish.
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
        std::vector<std::wstring> childFolders;
        childFolders.reserve(kMaxChildFolders);
        do{
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            const std::wstring name(data.cFileName);
            if(name==L"."||name==L"..")continue;
            if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT){
                result.status=Status::InvalidSource;return result;
            }
            if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                bool folderMarker=false;
                if(childFolders.size()>=kMaxChildFolders||name.size()>180u||
                   !fxfile::zipinspect::detail::safeName(
                        name,folderMarker)||folderMarker){
                    result.status=Status::InvalidSource;return result;
                }
                childFolders.push_back((p/name).native());
            }else{
                if(files.size()>=kMaxFiles){
                    result.status=Status::TooLarge;return result;
                }
                files.push_back((p/name).native());
            }
        }while(::FindNextFileW(found,&data));
        if(::GetLastError()!=ERROR_NO_MORE_FILES){
            result.status=Status::CannotRead;return result;
        }
        std::sort(childFolders.begin(),childFolders.end());
        for(auto const& childFolder:childFolders){
            const DWORD childAttr=::GetFileAttributesW(childFolder.c_str());
            if(childAttr==INVALID_FILE_ATTRIBUTES||
               !(childAttr&FILE_ATTRIBUTE_DIRECTORY)||
               (childAttr&FILE_ATTRIBUTE_REPARSE_POINT)){
                result.status=Status::InvalidSource;return result;
            }
            WIN32_FIND_DATAW nested{};
            const auto searchChild=(std::filesystem::path(childFolder)/L"*").native();
            const HANDLE nestedHandle=::FindFirstFileW(searchChild.c_str(),&nested);
            if(nestedHandle==INVALID_HANDLE_VALUE){
                result.status=Status::CannotRead;return result;
            }
            FindGuard nestedFinder{nestedHandle};
            std::size_t childCount=0;
            do{
                if(fxfile::zipstore::detail::cancelled(cancellation)){
                    result.status=Status::Cancelled;return result;
                }
                const std::wstring name(nested.cFileName);
                if(name==L"."||name==L"..")continue;
                if(nested.dwFileAttributes&
                   (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)){
                    result.status=Status::InvalidSource;return result;
                }
                if(files.size()>=kMaxFiles){
                    result.status=Status::TooLarge;return result;
                }
                files.push_back(
                    (std::filesystem::path(childFolder)/name).native());
                ++childCount;
            }while(::FindNextFileW(nestedHandle,&nested));
            if(::GetLastError()!=ERROR_NO_MORE_FILES){
                result.status=Status::CannotRead;return result;
            }
            if(!childCount){
                result.status=Status::InvalidSource;return result;
            }
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
