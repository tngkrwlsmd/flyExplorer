// F08/EP10: bounded one-file, flat-path ZIP Store extraction.
// This is intentionally NOT a general ZIP extractor: no Deflate, ZIP64,
// encryption, data descriptors, directories, symlinks or multi-entry archives.
// One held source handle, CRC verified before any output, staged no-overwrite
// publication, and cleanup of only our temporary file.
#pragma once
#include "zip_store_writer.h"
#include "zip_store_compat.h"
#include <windows.h>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace fxfile::zipextract {
enum class Status {
    Extracted, InvalidSource, CannotRead, TooLarge, UnsafeEntry,
    Unsupported, Corrupt, AlreadyExists, CannotWrite
};
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
};
namespace detail {
inline bool safeLeaf(std::wstring const& leaf) {
    bool directory=false;
    return !leaf.empty()&&leaf.size()<=180&&
           leaf.find(L'/')==std::wstring::npos&&
           fxfile::zipinspect::detail::safeName(leaf,directory)&&!directory;
}
} // namespace detail

inline Result extractOne(std::wstring const& source) noexcept {
    Result answer{};
    using namespace fxfile::zipinspect::detail;
    try{
        if(!fxfile::zipinspect::detail::source(source))return answer;
        const std::filesystem::path archive(source);
        const std::wstring parent=archive.parent_path().native();
        Handle reader;
        reader.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
                nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
        if(reader.h==INVALID_HANDLE_VALUE){
            answer.status=Status::CannotRead;return answer;
        }
        BY_HANDLE_FILE_INFORMATION sourceInfo{};
        if(!::GetFileInformationByHandle(reader.h,&sourceInfo)||
           (sourceInfo.dwFileAttributes&
            (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))){
            answer.status=Status::InvalidSource;return answer;
        }
        LARGE_INTEGER length{};
        if(!::GetFileSizeEx(reader.h,&length)||length.QuadPart<0){
            answer.status=Status::CannotRead;return answer;
        }
        if(static_cast<std::uint64_t>(length.QuadPart)>
           fxfile::zipinspect::kMaxZipBytes){
            answer.status=Status::TooLarge;return answer;
        }
        const std::size_t total=static_cast<std::size_t>(length.QuadPart);
        if(total<30u+46u+22u){
            answer.status=Status::Corrupt;return answer;
        }
        std::vector<unsigned char> archiveBytes(total);
        std::size_t readPos=0;
        while(readPos<total){
            const DWORD amount=static_cast<DWORD>(
                (std::min)(total-readPos,std::size_t{65536}));
            DWORD read=0;
            if(!::ReadFile(reader.h,archiveBytes.data()+readPos,amount,
                           &read,nullptr)||!read||read>amount){
                answer.status=Status::CannotRead;return answer;
            }
            readPos+=read;
        }
        LARGE_INTEGER after{};
        if(!::GetFileSizeEx(reader.h,&after)||
           after.QuadPart!=length.QuadPart){
            answer.status=Status::CannotRead;return answer;
        }
        // Strict single Store member. Reject archive prefixes, trailing
        // data, all extra fields/comments, and non-exact central placement.
        const std::size_t eocd=total-22;
        if(u32(archiveBytes,eocd)!=0x06054b50u){
            answer.status=Status::Corrupt;return answer;
        }
        if(u16(archiveBytes,eocd+4)!=0||
           u16(archiveBytes,eocd+6)!=0||
           u16(archiveBytes,eocd+8)!=1||
           u16(archiveBytes,eocd+10)!=1||
           u16(archiveBytes,eocd+20)!=0){
            answer.status=Status::Unsupported;return answer;
        }
        const auto centralBytes=std::size_t(u32(archiveBytes,eocd+12));
        const auto central=std::size_t(u32(archiveBytes,eocd+16));
        if(centralBytes<46u||!span(central,centralBytes,eocd)||
           central+centralBytes!=eocd||
           !span(central,46u,eocd)||
           u32(archiveBytes,central)!=0x02014b50u){
            answer.status=Status::Corrupt;return answer;
        }
        const std::uint16_t versionMade=u16(archiveBytes,central+4);
        const std::uint16_t versionNeeded=u16(archiveBytes,central+6);
        const std::uint16_t flags=u16(archiveBytes,central+8);
        const std::uint16_t method=u16(archiveBytes,central+10);
        const std::uint32_t checksum=u32(archiveBytes,central+16);
        const std::uint32_t packed=u32(archiveBytes,central+20);
        const std::uint32_t expanded=u32(archiveBytes,central+24);
        const auto nameLength=std::size_t(u16(archiveBytes,central+28));
        if(!fxfile::zipstorecompat::supportedDosVersion(versionMade)||
           !fxfile::zipstorecompat::supportedDosVersion(versionNeeded)||
           !fxfile::zipstorecompat::supportedFlags(flags)||method!=0||
           u16(archiveBytes,central+30)!=0||
           u16(archiveBytes,central+32)!=0||
           u16(archiveBytes,central+34)!=0||
           u16(archiveBytes,central+36)!=0||
           u32(archiveBytes,central+38)!=0||
           u32(archiveBytes,central+42)!=0){
            answer.status=Status::Unsupported;return answer;
        }
        if(packed!=expanded||packed>fxfile::zipstore::kMaxInputBytes||
           packed>fxfile::zipinspect::kMaxSingleBytes){
            answer.status=Status::TooLarge;return answer;
        }
        if(!nameLength||nameLength>512u||
           centralBytes!=46u+nameLength||
           !span(central+46u,nameLength,eocd)){
            answer.status=Status::Corrupt;return answer;
        }
        // Validate the local header against the same immutable read buffer.
        if(u32(archiveBytes,0)!=0x04034b50u||
           u16(archiveBytes,4)!=versionNeeded||
           u16(archiveBytes,6)!=flags||
           !fxfile::zipstorecompat::sameDosTime(archiveBytes,0,central)||
           u16(archiveBytes,8)!=method||
           u32(archiveBytes,14)!=checksum||
           u32(archiveBytes,18)!=packed||
           u32(archiveBytes,22)!=expanded||
           u16(archiveBytes,26)!=nameLength||
           u16(archiveBytes,28)!=0){
            answer.status=Status::Corrupt;return answer;
        }
        const auto dataBegin=30u+nameLength;
        if(!span(dataBegin,packed,central)||dataBegin+packed!=central||
           !std::equal(archiveBytes.begin()+30u,
                       archiveBytes.begin()+30u+nameLength,
                       archiveBytes.begin()+central+46u)){
            answer.status=Status::Corrupt;return answer;
        }
        std::wstring member;
        if(!fxfile::zipstorecompat::decodeName(
               archiveBytes,central+46u,nameLength,flags,member)){
            answer.status=Status::Unsupported;return answer;
        }
        if(!detail::safeLeaf(member)){
            answer.status=Status::UnsafeEntry;return answer;
        }
        const std::filesystem::path outputPath=
            std::filesystem::path(parent)/member;
        const std::wstring target=outputPath.native();
        if(target.size()>253u||
           outputPath.parent_path().native()!=parent){
            answer.status=Status::UnsafeEntry;return answer;
        }
        // CRC check is over the actual member bytes, NOT declared metadata.
        const std::vector<unsigned char> payload(
            archiveBytes.begin()+dataBegin,
            archiveBytes.begin()+dataBegin+packed);
        if(fxfile::zipstore::detail::crc32(payload)!=checksum){
            answer.status=Status::Corrupt;return answer;
        }
        if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            answer.status=Status::AlreadyExists;return answer;
        }
        // Rerun the fixed-drive/reparse-path guard before publishing to
        // reduce parent replacement risk. No preexisting file is deleted.
        if(!fxfile::zipinspect::detail::source(source)){
            answer.status=Status::InvalidSource;return answer;
        }
        fxfile::zipstore::detail::Staging staging;
        if(!::GetTempFileNameW(parent.c_str(),L"fxe",0,staging.path)){
            answer.status=Status::CannotWrite;return answer;
        }
        staging.owned=true;
        bool written=false;
        {
            Handle writer;
            writer.h=::CreateFileW(staging.path,GENERIC_WRITE,0,nullptr,
                         OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(writer.h!=INVALID_HANDLE_VALUE){
                BY_HANDLE_FILE_INFORMATION information{};
                if(::GetFileInformationByHandle(writer.h,&information)&&
                   information.nNumberOfLinks==1&&
                   !(information.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&
                   fxfile::zipstore::detail::writeAll(writer.h,payload))
                    written=true;
            }
        }
        if(!written){
            answer.status=Status::CannotWrite;return answer;
        }
        answer.output=target; // Finish allocation before publishing.
        // MOVEFILE_REPLACE_EXISTING is forbidden.
        if(::MoveFileExW(staging.path,target.c_str(),
                         MOVEFILE_WRITE_THROUGH)){
            staging.owned=false;
            answer.status=Status::Extracted;
            return answer;
        }
        const DWORD error=::GetLastError();
        answer.output.clear();
        answer.status=(error==ERROR_ALREADY_EXISTS||error==ERROR_FILE_EXISTS)?
            Status::AlreadyExists:Status::CannotWrite;
        return answer;
    }catch(...){
        answer.status=Status::CannotWrite;
        return answer;
    }
}
} // namespace fxfile::zipextract
