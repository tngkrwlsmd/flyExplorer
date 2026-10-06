#include "pch.h"
#include "file_metadata_controller.h"
#include "../../src/base/shell_isolation_wire.h"
#include <algorithm>
#include <cwctype>
#include <filesystem>
#include <thread>
#include <utility>

namespace fxfile::previewmetadata {
namespace {

std::wstring typeKey(std::wstring const& path,bool folder)
{
    if(folder)return L"";
    auto ext=std::filesystem::path(path).extension().native();
    std::transform(ext.begin(),ext.end(),ext.begin(),[](wchar_t c){
        return static_cast<wchar_t>(::towlower(c));
    });
    return ext;
}

std::wstring sizeLabel(std::uint64_t bytes)
{
    return bytes<1024?
        std::to_wstring(bytes)+L" B":
        bytes<1048576?
        std::to_wstring(bytes/1024)+L" KB":
        std::to_wstring(bytes/1048576)+L" MB";
}

std::wstring dateLabel(FILETIME const& value)
{
    FILETIME local{};
    SYSTEMTIME stamp{};
    if(!::FileTimeToLocalFileTime(&value,&local)||
       !::FileTimeToSystemTime(&local,&stamp))return {};
    wchar_t date[32]{},time[24]{};
    if(!::GetDateFormatEx(L"ko-KR",0,&stamp,L"yyyy-MM-dd",date,32,nullptr)||
       !::GetTimeFormatEx(L"ko-KR",0,&stamp,L"HH:mm",time,24))return {};
    return std::wstring(date)+L" "+time;
}

}

FileMetadataController::~FileMetadataController(){prepareForClose();}

void FileMetadataController::cancel(int side) noexcept
{
    if(side<0||side>=static_cast<int>(cancel_.size()))return;
    auto& current=cancel_[static_cast<std::size_t>(side)];
    if(current)current->store(true);
    current.reset();
}

void FileMetadataController::prepareForClose() noexcept
{
    closing_.store(true);
    for(int side=0;side<static_cast<int>(cancel_.size());++side)cancel(side);
}

bool FileMetadataController::start(
    Request request,Post post,CompletionCallback completion)
{
    if(closing_.load()||request.side<0||
       request.side>=static_cast<int>(cancel_.size())||
       request.route==0||request.ticket==0||
       request.paths.size()>fxfile::isolation::kMaxCompleteModelEntries||
       !post||!completion)return false;
    const int side=request.side;
    cancel(side);
    auto cancelToken=std::make_shared<std::atomic_bool>(false);
    cancel_[static_cast<std::size_t>(side)]=cancelToken;
    try{
        std::thread([
            request=std::move(request),cancelToken,
            post=std::move(post),completion=std::move(completion)]() mutable {
            using FileMetadata=fxfile::previewlist::FileMetadata;
            std::vector<FileMetadata> metadata(request.paths.size());
            for(std::size_t i=0;i<request.paths.size();++i){
                if(cancelToken->load())return;
                auto const& path=request.paths[i];
                if(path.empty()||path.size()>32000)continue;
                WIN32_FILE_ATTRIBUTE_DATA data{};
                if(!::GetFileAttributesExW(
                     path.c_str(),GetFileExInfoStandard,&data))continue;
                if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)continue;
                auto& entry=metadata[i];
                const bool folder=
                    (data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)!=0;
                entry.typeKey=typeKey(path,folder);
                if(!folder){
                    entry.bytes=(static_cast<std::uint64_t>(
                        data.nFileSizeHigh)<<32)|data.nFileSizeLow;
                    entry.bytesLabel=sizeLabel(entry.bytes);
                    entry.sizeKnown=true;
                }
                ULARGE_INTEGER timestamp{};
                timestamp.HighPart=data.ftLastWriteTime.dwHighDateTime;
                timestamp.LowPart=data.ftLastWriteTime.dwLowDateTime;
                entry.modified=timestamp.QuadPart;
                entry.dateLabel=dateLabel(data.ftLastWriteTime);
                entry.dateKnown=!entry.dateLabel.empty();
            }
            if(cancelToken->load())return;
            Completion result{};
            result.side=request.side;
            result.tab=request.tab;
            result.route=request.route;
            result.ticket=request.ticket;
            result.metadata=std::move(metadata);
            try{
                post([completion=std::move(completion),
                      result=std::move(result)]() mutable {
                    completion(std::move(result));
                });
            }catch(...){}
        }).detach();
    }catch(...){
        cancel_[static_cast<std::size_t>(side)].reset();
        return false;
    }
    return true;
}

} // namespace fxfile::previewmetadata
