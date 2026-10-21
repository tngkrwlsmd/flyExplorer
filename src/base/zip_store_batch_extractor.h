// F08/EP10: strict bounded Store/Deflate, 2-8 flat or single-root members.
// Validate every local/central record and CRC before any output. Publish a
// single owned staging directory by rename; never publish partial entries.
// No ZIP64, extra/comment, symlinks, multiple roots, deep paths or overwrite.
// Untested on Windows: hostile concurrent directory replacement remains a risk.
#pragma once
#include "zip_store_batch_writer.h"
#include "zip_store_compat.h"
#include "zip_raw_deflate.h"
#include <windows.h>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace fxfile::zipbatchextract {
inline constexpr wchar_t kExtractedDirectory[]=L"flyExplorer-selection-unpacked";
enum class Status {
    Extracted, Cancelled, InvalidSource, CannotRead, TooLarge, UnsafeEntry,
    Unsupported, Corrupt, AlreadyExists, CannotWrite
};
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
    std::size_t fileCount=0;
};
namespace detail {
struct Member final {
    std::wstring name;
    std::vector<unsigned char> content;
};
// Only remove known staged, ordinary files from the uniquely created
// directory. Never recurse or delete an existing destination directory.
// If an external process changed the folder, fail closed: cleanup can leave
// owned remnants instead of following a reparse point or deleting strangers.
struct StagedDirectory final {
    std::wstring path;
    std::vector<std::wstring> files;
    std::wstring nestedRoot;
    bool owned=false;
    bool nestedOwned=false;
    ~StagedDirectory() noexcept {
        if(!owned)return;
        const DWORD root=::GetFileAttributesW(path.c_str());
        if(root==INVALID_FILE_ATTRIBUTES||
           !(root&FILE_ATTRIBUTE_DIRECTORY)||
           (root&FILE_ATTRIBUTE_REPARSE_POINT))return;
        // Never descend into an externally replaced junction/reparse root.
        if(!nestedRoot.empty()){
            // A child we did not exclusively create must not be traversed.
            if(!nestedOwned)return;
            const DWORD child=::GetFileAttributesW(nestedRoot.c_str());
            if(child==INVALID_FILE_ATTRIBUTES||
               !(child&FILE_ATTRIBUTE_DIRECTORY)||
               (child&FILE_ATTRIBUTE_REPARSE_POINT))return;
        }
        for(auto const& name:files){
            const DWORD attr=::GetFileAttributesW(name.c_str());
            if(attr!=INVALID_FILE_ATTRIBUTES&&
               !(attr&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
                ::DeleteFileW(name.c_str());
        }
        if(!nestedRoot.empty())::RemoveDirectoryW(nestedRoot.c_str());
        ::RemoveDirectoryW(path.c_str());
    }
    StagedDirectory()=default;
    StagedDirectory(StagedDirectory const&)=delete;
    StagedDirectory& operator=(StagedDirectory const&)=delete;
};
inline bool flatName(std::wstring const& name) {
    bool isFolder=false;
    return name.size()<=180&&!name.empty()&&
           name.find(L'/')==std::wstring::npos&&
           fxfile::zipinspect::detail::safeName(name,isFolder)&&!isFolder;
}
// Reject all path shapes except "leaf" or "singleRoot/leaf".
// No drive, dot components, empty segment, second slash, or directory-only
// ZIP entries can pass the shared safeName validation.
inline bool memberPath(std::wstring const& value,
                       std::wstring& root,std::wstring& leaf) {
    const auto slash=value.find(L'/');
    if(slash==std::wstring::npos){
        root.clear();leaf=value;
        return flatName(leaf);
    }
    if(value.find(L'/',slash+1)!=std::wstring::npos)return false;
    root=value.substr(0,slash);
    leaf=value.substr(slash+1);
    return flatName(root)&&flatName(leaf);
}
} // namespace detail

inline Result extractMany(std::wstring const& source,
                          std::atomic_bool const* cancellation=nullptr) noexcept {
    Result result{};
    if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
    using namespace fxfile::zipinspect::detail;
    try{
        if(!fxfile::zipinspect::detail::source(source))return result;
        const std::wstring parent=std::filesystem::path(source).parent_path().native();
        const std::wstring target=
            (std::filesystem::path(parent)/kExtractedDirectory).native();
        if(target.size()>240||parent.size()>195){
            result.status=Status::InvalidSource;return result;
        }
        Handle input;
        input.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
                       nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
        if(input.h==INVALID_HANDLE_VALUE){
            result.status=Status::CannotRead;return result;
        }
        BY_HANDLE_FILE_INFORMATION inputInfo{};
        if(!::GetFileInformationByHandle(input.h,&inputInfo)||
           (inputInfo.dwFileAttributes&
            (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))){
            result.status=Status::InvalidSource;return result;
        }
        LARGE_INTEGER length{};
        if(!::GetFileSizeEx(input.h,&length)||length.QuadPart<0){
            result.status=Status::CannotRead;return result;
        }
        if(static_cast<std::uint64_t>(length.QuadPart)>
           fxfile::zipinspect::kMaxZipBytes){
            result.status=Status::TooLarge;return result;
        }
        const std::size_t total=static_cast<std::size_t>(length.QuadPart);
        if(total<22u+2u*(30u+46u+1u)){
            result.status=Status::Corrupt;return result;
        }
        std::vector<unsigned char> bytes(total);
        std::size_t progress=0;
        while(progress<bytes.size()){
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            DWORD read=0;
            const DWORD chunk=static_cast<DWORD>(
                (std::min)(bytes.size()-progress,std::size_t{65536}));
            if(!::ReadFile(input.h,bytes.data()+progress,chunk,&read,nullptr)||
               read==0||read>chunk){
                result.status=Status::CannotRead;return result;
            }
            progress+=read;
        }
        LARGE_INTEGER afterSize{};
        if(!::GetFileSizeEx(input.h,&afterSize)||
           afterSize.QuadPart!=length.QuadPart){
            result.status=Status::CannotRead;return result;
        }

        // EOCD is exactly the final 22 bytes, no spanning disks or comment.
        const std::size_t eocd=total-22;
        if(u32(bytes,eocd)!=0x06054b50u){
            result.status=Status::Corrupt;return result;
        }
        const auto count=std::size_t(u16(bytes,eocd+10));
        if(u16(bytes,eocd+4)!=0||u16(bytes,eocd+6)!=0||
           u16(bytes,eocd+8)!=count||u16(bytes,eocd+20)!=0||
           count<fxfile::zipbatch::kMinFiles||
           count>fxfile::zipbatch::kMaxFiles){
            result.status=Status::Unsupported;return result;
        }
        const auto central=std::size_t(u32(bytes,eocd+16));
        const auto centralBytes=std::size_t(u32(bytes,eocd+12));
        if(!span(central,centralBytes,eocd)||
           central+centralBytes!=eocd||central==0){
            result.status=Status::Corrupt;return result;
        }
        std::size_t localCursor=0;
        std::size_t directoryCursor=central;
        std::uint64_t uncompressedTotal=0;
        std::vector<detail::Member> members;
        members.reserve(count);
        std::wstring archiveRoot;
        bool rootMode=false;
        for(std::size_t i=0;i<count;++i){
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            // Local entries must be concatenated with no gaps or overlap.
            if(!span(localCursor,30u,central)||
               u32(bytes,localCursor)!=0x04034b50u||
               !span(directoryCursor,46u,eocd)||
               u32(bytes,directoryCursor)!=0x02014b50u){
                result.status=Status::Corrupt;return result;
            }
            const auto nameLength=std::size_t(u16(bytes,localCursor+26));
            const auto versionNeeded=u16(bytes,directoryCursor+6);
            const auto flags=u16(bytes,directoryCursor+8);
            const auto method=u16(bytes,directoryCursor+10);
            const auto packed=std::size_t(u32(bytes,localCursor+18));
            const auto unpacked=std::size_t(u32(bytes,localCursor+22));
            const auto checksum=u32(bytes,localCursor+14);
            const auto nameLengthCentral=std::size_t(u16(bytes,directoryCursor+28));
            if(!fxfile::zipstorecompat::supportedDosVersion(versionNeeded)||
               !fxfile::zipstorecompat::supportedDosVersion(
                    u16(bytes,directoryCursor+4))||
               !fxfile::zipstorecompat::supportedFlags(flags)||
               (method!=0&&method!=8)||
               (method==8&&versionNeeded!=20)||
               u16(bytes,localCursor+4)!=versionNeeded||
               u16(bytes,localCursor+6)!=flags||
               u16(bytes,localCursor+8)!=method||
               !fxfile::zipstorecompat::sameDosTime(
                    bytes,localCursor,directoryCursor)||
               u16(bytes,localCursor+28)!=0||
               u16(bytes,directoryCursor+30)!=0||
               u16(bytes,directoryCursor+32)!=0||
               u16(bytes,directoryCursor+34)!=0||
               u16(bytes,directoryCursor+36)!=0||
               u32(bytes,directoryCursor+38)!=0||
               u32(bytes,directoryCursor+42)!=localCursor){
                result.status=Status::Unsupported;return result;
            }
            if(!nameLength||nameLength>512u||
               nameLengthCentral!=nameLength||
               !span(localCursor+30u,nameLength,central)||
               !span(directoryCursor+46u,nameLength,eocd)||
               unpacked>fxfile::zipbatch::kMaxTotalBytes-uncompressedTotal||
               unpacked>fxfile::ziprawdeflate::kMaxOutputBytes||
               packed>fxfile::ziprawdeflate::kMaxPackedBytes||
               (method==0&&packed!=unpacked)||
               (method==8&&(!packed||
                             (unpacked>0&&
                              std::uint64_t(unpacked)>
                              std::uint64_t(packed)*
                              fxfile::ziprawdeflate::kMaxRatio)))){
                result.status=Status::TooLarge;return result;
            }
            const auto dataStart=localCursor+30u+nameLength;
            if(!span(dataStart,packed,central)||
               u32(bytes,directoryCursor+16)!=checksum||
               u32(bytes,directoryCursor+20)!=packed||
               u32(bytes,directoryCursor+24)!=unpacked||
               !std::equal(bytes.begin()+localCursor+30u,
                           bytes.begin()+localCursor+30u+nameLength,
                           bytes.begin()+directoryCursor+46u)){
                result.status=Status::Corrupt;return result;
            }
            std::wstring name;
            if(!fxfile::zipstorecompat::decodeName(
                   bytes,directoryCursor+46u,nameLength,flags,name)){
                result.status=Status::Unsupported;return result;
            }
            std::wstring entryRoot,entryLeaf;
            if(!detail::memberPath(name,entryRoot,entryLeaf)){
                result.status=Status::UnsafeEntry;return result;
            }
            if(i==0){
                rootMode=!entryRoot.empty();
                archiveRoot=entryRoot;
            }else if(rootMode!=!entryRoot.empty()||
                     (rootMode&&!fxfile::zipinspect::detail::same(
                         archiveRoot,entryRoot))){
                result.status=Status::UnsafeEntry;return result;
            }
            for(auto const& previous:members){
                if(fxfile::zipinspect::detail::same(previous.name,entryLeaf)){
                    result.status=Status::UnsafeEntry;return result;
                }
            }
            // Validate the entire member before staging any output.
            detail::Member member{};
            member.name=std::move(entryLeaf);
            if(method==0){
                member.content.assign(bytes.begin()+dataStart,
                                      bytes.begin()+dataStart+packed);
            }else{
                if(fxfile::zipstore::detail::cancelled(cancellation)){
                    result.status=Status::Cancelled;return result;
                }
                if(!fxfile::ziprawdeflate::inflateExact(
                       bytes.data()+dataStart,packed,unpacked,
                       member.content,cancellation)){
                    result.status=fxfile::zipstore::detail::cancelled(cancellation)?
                        Status::Cancelled:Status::Corrupt;
                    return result;
                }
            }
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            if(member.content.size()!=unpacked||
               fxfile::zipstore::detail::crc32(member.content)!=checksum){
                result.status=Status::Corrupt;return result;
            }
            members.push_back(std::move(member));
            uncompressedTotal+=unpacked;
            localCursor=dataStart+packed;
            directoryCursor+=46u+nameLength;
        }
        if(localCursor!=central||directoryCursor!=eocd){
            result.status=Status::Corrupt;return result;
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            result.status=Status::AlreadyExists;return result;
        }
        // Check the parent's fixed-drive/reparse chain again after parsing.
        if(!fxfile::zipinspect::detail::source(source)){
            result.status=Status::InvalidSource;return result;
        }
        // GetTempFileNameW reserves a random same-directory *file*.
        // Convert only a distinct ".dir" sibling into a directory with
        // CreateDirectoryW (fail-if-present). Never delete the final target.
        fxfile::zipstore::detail::Staging reservation;
        if(!::GetTempFileNameW(parent.c_str(),L"fxu",0,reservation.path)){
            result.status=Status::CannotWrite;return result;
        }
        reservation.owned=true;
        detail::StagedDirectory staging;
        staging.path=std::wstring(reservation.path)+L".dir";
        staging.files.reserve(members.size());
        if(rootMode){
            staging.nestedRoot=(std::filesystem::path(staging.path)/archiveRoot).native();
            if(staging.nestedRoot.size()>240u){
                result.status=Status::InvalidSource;return result;
            }
        }
        for(auto const& member:members){
            const auto base=rootMode?
                std::filesystem::path(staging.nestedRoot):
                std::filesystem::path(staging.path);
            const auto staged=(base/member.name).native();
            if(staged.size()>253u){
                result.status=Status::InvalidSource;return result;
            }
            staging.files.push_back(staged);
        }
        if(!::CreateDirectoryW(staging.path.c_str(),nullptr)){
            result.status=Status::CannotWrite;return result;
        }
        staging.owned=true;
        if(rootMode){
            if(!::CreateDirectoryW(staging.nestedRoot.c_str(),nullptr)){
                result.status=Status::CannotWrite;return result;
            }
            staging.nestedOwned=true;
        }
        for(std::size_t i=0;i<members.size();++i){
            if(fxfile::zipstore::detail::cancelled(cancellation)){
                result.status=Status::Cancelled;return result;
            }
            const auto& filePath=staging.files[i];
            Handle output;
            output.h=::CreateFileW(filePath.c_str(),GENERIC_WRITE,0,nullptr,
                CREATE_NEW,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,
                nullptr);
            if(output.h==INVALID_HANDLE_VALUE){
                result.status=Status::CannotWrite;return result;
            }
            BY_HANDLE_FILE_INFORMATION details{};
            if(!::GetFileInformationByHandle(output.h,&details)||
               (details.dwFileAttributes&
                (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))||
               details.nNumberOfLinks!=1||
               !fxfile::zipstore::detail::writeAll(
                   output.h,members[i].content,cancellation)){
                result.status=fxfile::zipstore::detail::cancelled(cancellation)?
                    Status::Cancelled:Status::CannotWrite;return result;
            }
        }
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.status=Status::Cancelled;return result;
        }
        // No per-file publish: the whole completed directory is renamed.
        result.output=target; // All allocations completed before rename.
        result.fileCount=members.size();
        if(fxfile::zipstore::detail::cancelled(cancellation)){
            result.output.clear();result.fileCount=0;
            result.status=Status::Cancelled;return result;
        }
        // No rollback if the final directory rename has committed.
        if(::MoveFileExW(staging.path.c_str(),target.c_str(),
                         MOVEFILE_WRITE_THROUGH)){
            staging.owned=false;
            result.status=Status::Extracted;
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
} // namespace fxfile::zipbatchextract
