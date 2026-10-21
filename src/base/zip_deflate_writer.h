// F08: single ordinary local file -> ZIP Deflate (method 8) or Store
// fallback when packed output grows or breaks our 100:1 extraction limit.
// Bounded in-memory processing, actual CRC check, exclusive staged publish,
// NO overwrite and NO original-file modification. NOT TESTED on Windows.
#pragma once
#include "zip_store_writer.h"
#include "zip_raw_deflate.h"
#include "zip_raw_deflate_compress.h"
#include <windows.h>
#include <algorithm>
#include <filesystem>
#include <string>
#include <vector>
namespace fxfile::zipdeflate {
enum class Status { Created, InvalidSource, CannotRead, TooLarge,
                    CompressionFailed, AlreadyExists, CannotWrite };
struct Result final {
    Status status=Status::InvalidSource;
    std::wstring output{};
    bool usedDeflate=false;
};
inline Result createOne(std::wstring const& source) noexcept {
    Result result{};
    std::wstring parent,leaf;
    std::string encoded;
    if(!fxfile::zipstore::detail::safeSource(source,parent,leaf,encoded))
        return result;
    try{
        const std::wstring target=source+L".deflate.zip";
        if(target.size()>253u)return result;
        fxfile::zipinspect::detail::Handle reader;
        reader.h=::CreateFileW(source.c_str(),GENERIC_READ,FILE_SHARE_READ,
                               nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,
                               nullptr);
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
        if(static_cast<std::uint64_t>(length.QuadPart)>
           fxfile::ziprawdeflate::kMaxCompressionInput){
            result.status=Status::TooLarge;return result;
        }
        std::vector<unsigned char> content(static_cast<std::size_t>(length.QuadPart));
        std::size_t offset=0;
        while(offset<content.size()){
            DWORD read=0;
            const DWORD desired=static_cast<DWORD>(
                (std::min)(content.size()-offset,std::size_t{65536}));
            if(!::ReadFile(reader.h,content.data()+offset,desired,&read,nullptr)||
               !read||read>desired){
                result.status=Status::CannotRead;return result;
            }
            offset+=read;
        }
        LARGE_INTEGER finalLength{};
        BY_HANDLE_FILE_INFORMATION after{};
        if(!::GetFileSizeEx(reader.h,&finalLength)||
           finalLength.QuadPart!=length.QuadPart||
           !::GetFileInformationByHandle(reader.h,&after)||
           info.nFileSizeHigh!=after.nFileSizeHigh||
           info.nFileSizeLow!=after.nFileSizeLow||
           info.ftLastWriteTime.dwHighDateTime!=after.ftLastWriteTime.dwHighDateTime||
           info.ftLastWriteTime.dwLowDateTime!=after.ftLastWriteTime.dwLowDateTime){
            result.status=Status::CannotRead;return result;
        }
        if(::GetFileAttributesW(target.c_str())!=INVALID_FILE_ATTRIBUTES){
            result.status=Status::AlreadyExists;return result;
        }
        std::vector<unsigned char> compressed;
        if(!fxfile::ziprawdeflate::compressBounded(content,compressed)){
            result.status=Status::CompressionFailed;return result;
        }
        bool useDeflate=compressed.size()<content.size()&&
            std::uint64_t(content.size())<=
            std::uint64_t(compressed.size())*fxfile::ziprawdeflate::kMaxRatio;
        if(useDeflate){
            // Verify the compressor's raw stream using the *separate*
            // bounded decoder before writing even the first staged byte.
            std::vector<unsigned char> verified;
            if(!fxfile::ziprawdeflate::inflateExact(
                 compressed.data(),compressed.size(),content.size(),verified)||
               verified!=content){
                result.status=Status::CompressionFailed;return result;
            }
        }else{
            // Store fallback also covers highly compressible (>100:1)
            // data, which our own safety-gated extractor would reject.
            compressed=std::move(content);
        }
        const auto unpacked=static_cast<std::uint32_t>(
            useDeflate?length.QuadPart:compressed.size());
        const auto packed=static_cast<std::uint32_t>(compressed.size());
        // CRC is always computed from uncompressed bytes.
        const auto crc=useDeflate?
            fxfile::zipstore::detail::crc32(content):
            fxfile::zipstore::detail::crc32(compressed);
        const auto nameLength=static_cast<std::uint16_t>(encoded.size());
        const auto method=static_cast<std::uint16_t>(useDeflate?8u:0u);
        const std::size_t archiveSize=30u+nameLength+packed+
                                      46u+nameLength+22u;
        if(archiveSize>fxfile::zipinspect::kMaxZipBytes){
            result.status=Status::TooLarge;return result;
        }
        std::vector<unsigned char> zip;
        zip.reserve(archiveSize);
        const auto addName=[&]{
            zip.insert(zip.end(),encoded.begin(),encoded.end());
        };
        fxfile::zipstore::detail::dword(zip,0x04034b50u);
        fxfile::zipstore::detail::word(zip,20);
        fxfile::zipstore::detail::word(zip,0x0800);
        fxfile::zipstore::detail::word(zip,method);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::dword(zip,crc);
        fxfile::zipstore::detail::dword(zip,packed);
        fxfile::zipstore::detail::dword(zip,unpacked);
        fxfile::zipstore::detail::word(zip,nameLength);
        fxfile::zipstore::detail::word(zip,0);
        addName();
        zip.insert(zip.end(),compressed.begin(),compressed.end());
        const auto directoryStart=static_cast<std::uint32_t>(zip.size());
        fxfile::zipstore::detail::dword(zip,0x02014b50u);
        fxfile::zipstore::detail::word(zip,20);
        fxfile::zipstore::detail::word(zip,20);
        fxfile::zipstore::detail::word(zip,0x0800);
        fxfile::zipstore::detail::word(zip,method);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::dword(zip,crc);
        fxfile::zipstore::detail::dword(zip,packed);
        fxfile::zipstore::detail::dword(zip,unpacked);
        fxfile::zipstore::detail::word(zip,nameLength);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::dword(zip,0);
        fxfile::zipstore::detail::dword(zip,0);
        addName();
        fxfile::zipstore::detail::dword(zip,0x06054b50u);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,0);
        fxfile::zipstore::detail::word(zip,1);
        fxfile::zipstore::detail::word(zip,1);
        fxfile::zipstore::detail::dword(zip,46u+nameLength);
        fxfile::zipstore::detail::dword(zip,directoryStart);
        fxfile::zipstore::detail::word(zip,0);
        if(zip.size()!=archiveSize){
            result.status=Status::CannotWrite;return result;
        }
        if(!fxfile::zipstore::detail::safeSource(source,parent,leaf,encoded)){
            result.status=Status::InvalidSource;return result;
        }
        fxfile::zipstore::detail::Staging staging;
        if(!::GetTempFileNameW(parent.c_str(),L"fxd",0,staging.path)){
            result.status=Status::CannotWrite;return result;
        }
        staging.owned=true;
        bool flushed=false;
        {
            fxfile::zipinspect::detail::Handle output;
            output.h=::CreateFileW(staging.path,GENERIC_WRITE,0,nullptr,
                 OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
            if(output.h!=INVALID_HANDLE_VALUE){
                BY_HANDLE_FILE_INFORMATION state{};
                if(::GetFileInformationByHandle(output.h,&state)&&
                   state.nNumberOfLinks==1&&
                   !(state.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&
                   fxfile::zipstore::detail::writeAll(output.h,zip))
                    flushed=true;
            }
        }
        if(!flushed){
            result.status=Status::CannotWrite;return result;
        }
        result.output=target;
        if(::MoveFileExW(staging.path,target.c_str(),MOVEFILE_WRITE_THROUGH)){
            staging.owned=false;
            result.usedDeflate=useDeflate;
            result.status=Status::Created;
            return result;
        }
        const DWORD error=::GetLastError();
        result.output.clear();
        result.status=(error==ERROR_ALREADY_EXISTS||error==ERROR_FILE_EXISTS)?
            Status::AlreadyExists:Status::CannotWrite;
        return result;
    }catch(...){result.status=Status::CannotWrite;return result;}
}
}
