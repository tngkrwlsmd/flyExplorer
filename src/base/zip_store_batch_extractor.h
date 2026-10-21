// F08/EP10: strict bounded Store-only, 2-8 regular flat ZIP members.
// Validate every local/central record and CRC before any output. Publish a
// single owned staging directory by rename; never publish partial entries.
// No Deflate, ZIP64, extra/comment, symlinks, nested paths or overwrite.
// Untested on Windows: hostile concurrent directory replacement remains a risk.
#pragma once
#include "zip_store_batch_writer.h"
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
    Extracted, InvalidSource, CannotRead, TooLarge, UnsafeEntry,
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
    bool owned=false;
    ~StagedDirectory() noexcept {
        if(!owned)return;
        const DWORD root=::GetFileAttributesW(path.c_str());
        if(root==INVALID_FILE_ATTRIBUTES||
           !(root&FILE_ATTRIBUTE_DIRECTORY)||
           (root&FILE_ATTRIBUTE_REPARSE_POINT))return;
        for(auto const& name:files){
            const DWORD attr=::GetFileAttributesW(name.c_str());
            if(attr!=INVALID_FILE_ATTRIBUTES&&
               !(attr&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))
                ::DeleteFileW(name.c_str());
        }
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
} // namespace detail

inline Result extractMany(std::wstring const& source) noexcept {
    Result result{};
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
        for(std::size_t i=0;i<count;++i){
            // Local entries must be concatenated with no gaps or overlap.
            if(!span(localCursor,30u,central)||
               u32(bytes,localCursor)!=0x04034b50u||
               !span(directoryCursor,46u,eocd)||
               u32(bytes,directoryCursor)!=0x02014b50u){
                result.status=Status::Corrupt;return result;
            }
            const auto nameLength=std::size_t(u16(bytes,localCursor+26));
            const auto packed=std::size_t(u32(bytes,localCursor+18));
            const auto unpacked=std::size_t(u32(bytes,localCursor+22));
            const auto checksum=u32(bytes,localCursor+14);
            const auto nameLengthCentral=std::size_t(u16(bytes,directoryCursor+28));
            if(u16(bytes,localCursor+4)!=20||
               u16(bytes,localCursor+6)!=0x0800u||
               u16(bytes,localCursor+8)!=0||
               u16(bytes,localCursor+10)!=0||
               u16(bytes,localCursor+12)!=0||
               u16(bytes,localCursor+28)!=0||
               u16(bytes,directoryCursor+4)!=20||
               u16(bytes,directoryCursor+6)!=20||
               u16(bytes,directoryCursor+8)!=0x0800u||
               u16(bytes,directoryCursor+10)!=0||
               u16(bytes,directoryCursor+12)!=0||
               u16(bytes,directoryCursor+14)!=0||
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
               packed!=unpacked||
               packed>fxfile::zipstore::kMaxInputBytes||
               packed>fxfile::zipbatch::kMaxTotalBytes-uncompressedTotal){
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
            if(!decode(bytes,directoryCursor+46u,nameLength,true,name)){
                result.status=Status::Unsupported;return result;
            }
            if(!detail::flatName(name)){
                result.status=Status::UnsafeEntry;return result;
            }
            for(auto const& previous:members){
                if(fxfile::zipinspect::detail::same(previous.name,name)){
                    result.status=Status::UnsafeEntry;return result;
                }
            }
            detail::Member member{};
            member.name=std::move(name);
            member.content.assign(bytes.begin()+dataStart,
                                  bytes.begin()+dataStart+packed);
            if(fxfile::zipstore::detail::crc32(member.content)!=checksum){
                result.status=Status::Corrupt;return result;
            }
            members.push_back(std::move(member));
            uncompressedTotal+=packed;
            localCursor=dataStart+packed;
            directoryCursor+=46u+nameLength;
        }
        if(localCursor!=central||directoryCursor!=eocd){
            result.status=Status::Corrupt;return result;
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
        for(auto const& member:members){
            const auto staged=(std::filesystem::path(staging.path)/member.name).native();
            if(staged.size()>253u){
                result.status=Status::InvalidSource;return result;
            }
            staging.files.push_back(staged);
        }
        if(!::CreateDirectoryW(staging.path.c_str(),nullptr)){
            result.status=Status::CannotWrite;return result;
        }
        staging.owned=true;
        for(std::size_t i=0;i<members.size();++i){
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
               !fxfile::zipstore::detail::writeAll(output.h,members[i].content)){
                result.status=Status::CannotWrite;return result;
            }
        }
        // No per-file publish: the whole completed directory is renamed.
        result.output=target; // All allocations completed before rename.
        result.fileCount=members.size();
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
