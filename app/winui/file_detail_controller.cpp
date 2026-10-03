#include "pch.h"
#include "file_detail_controller.h"
#include "../../src/base/shell_assoc_type_core.h"
#include "../../src/base/shell_thumbnail_core.h"
#include <algorithm>
#include <cwctype>
#include <filesystem>
#include <thread>
#include <unordered_map>
#include <utility>

namespace fxfile::previewdetail {

FileDetailController::~FileDetailController(){prepareForClose();}

void FileDetailController::cancel(int side) noexcept
{
    if(side<0||side>=static_cast<int>(cancel_.size()))return;
    auto& current=cancel_[static_cast<std::size_t>(side)];
    if(current)current->store(true);
    current.reset();
}

void FileDetailController::prepareForClose() noexcept
{
    closing_.store(true);
    for(int side=0;side<static_cast<int>(cancel_.size());++side)cancel(side);
}

bool FileDetailController::start(
    Request request,Post post,CompletionCallback completion)
{
    if(closing_.load()||request.side<0||
       request.side>=static_cast<int>(cancel_.size())||
       request.route==0||request.ticket==0||request.paths.size()>1200||
       !post||!completion)return false;
    const int side=request.side;
    cancel(side);
    auto cancelToken=std::make_shared<std::atomic_bool>(false);
    cancel_[static_cast<std::size_t>(side)]=cancelToken;
    try{
        std::thread([
            request=std::move(request),cancelToken,
            post=std::move(post),completion=std::move(completion)]() mutable {
            using FileDetail=fxfile::previewlist::FileDetail;
            using FileViewMode=fxfile::previewlist::FileViewMode;
            std::vector<std::wstring> extensions{L".flyfolder"};
            for(auto const& path:request.paths){
                const auto dot=path.find_last_of(L'.');
                const auto slash=path.find_last_of(L"\\/");
                if(dot==std::wstring::npos||
                   (slash!=std::wstring::npos&&dot<slash))continue;
                auto ext=path.substr(dot);
                if(!fxfile::filetype::safeExtension(ext))continue;
                std::transform(ext.begin(),ext.end(),ext.begin(),
                   [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                if(std::find(extensions.begin(),extensions.end(),ext)==extensions.end()
                     &&extensions.size()<24)extensions.push_back(ext);
            }
            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::wstring visualHelper;
            if(!extensions.empty()){
                wchar_t exe[32768]{};
                const auto count=::GetModuleFileNameW(nullptr,exe,32768);
                if(count&&count<32768){
                    visualHelper=(std::filesystem::path(exe).parent_path()/
                        L"FlyShellIsolationHelper.exe").native();
                    windowsTypes=fxfile::filetype::queryVisuals(
                        visualHelper,extensions,2500,request.visualPixels);
                    std::vector<std::wstring> recover;
                    if(windowsTypes.empty()){
                        auto text=std::find(extensions.begin(),extensions.end(),L".txt");
                        if(text!=extensions.end())recover.push_back(*text);
                        for(auto const& ext:extensions){
                            if(recover.size()>=2)break;
                            if(std::find(recover.begin(),recover.end(),ext)
                               ==recover.end())recover.push_back(ext);
                        }
                    }else{
                        auto text=std::find(extensions.begin(),extensions.end(),L".txt");
                        if(text!=extensions.end()&&
                           (windowsTypes.find(*text)==windowsTypes.end()||
                            windowsTypes[*text].label.empty()))
                            recover.push_back(*text);
                    }
                    for(auto const& ext:recover){
                        auto one=fxfile::filetype::queryVisuals(
                            visualHelper,{ext},1350,request.visualPixels);
                        auto found=one.find(ext);
                        if(found!=one.end())windowsTypes[ext]=std::move(found->second);
                    }
                }
            }
            std::vector<FileDetail> details(request.paths.size());
            std::size_t thumbnailBudget=0;
            for(std::size_t i=0;i<request.paths.size();++i){
                if(cancelToken->load())return; // prevent stale metadata child launch
                auto const& path=request.paths[i];
                if(path.empty()||path.size()>32000)continue;
                WIN32_FILE_ATTRIBUTE_DATA data{};
                if(!::GetFileAttributesExW(path.c_str(),GetFileExInfoStandard,&data))
                    continue;
                if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)continue;
                auto& entry=details[i];
                if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                    entry.typeLabel=L"폴더";
                    auto folder=windowsTypes.find(L".flyfolder");
                    if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                        entry.iconBgra=folder->second.bgra;
                        entry.iconWidth=folder->second.width;
                        entry.iconHeight=folder->second.height;
                    }
                }else{
                    const auto dot=path.find_last_of(L'.');
                    const auto slash=path.find_last_of(L"\\/");
                    entry.typeLabel=dot!=std::wstring::npos&&
                         (slash==std::wstring::npos||dot>slash)&&
                         dot+1<path.size()&&path.size()-dot<=17?
                         path.substr(dot+1)+L" 파일":L"파일";
                    if(dot!=std::wstring::npos&&
                       (slash==std::wstring::npos||dot>slash)){
                        auto ext=path.substr(dot);
                        std::transform(ext.begin(),ext.end(),ext.begin(),
                           [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                        auto found=windowsTypes.find(ext);
                        if(found!=windowsTypes.end()){
                            if(!found->second.label.empty())
                                entry.typeLabel+=L" (Windows 유형: "+
                                    found->second.label+L")";
                            entry.iconBgra=found->second.bgra;
                            entry.iconWidth=found->second.width;
                            entry.iconHeight=found->second.height;
                        }
                    }
                }
                if(!(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)){
                    if(request.viewMode==FileViewMode::MediumIcons&&
                       !visualHelper.empty()&&thumbnailBudget<4&&
                       data.nFileSizeHigh==0&&
                       data.nFileSizeLow<=32*1024*1024){
                        auto ext=std::filesystem::path(path).extension().native();
                        std::transform(ext.begin(),ext.end(),ext.begin(),
                          [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                        if(ext==L".png"||ext==L".jpg"||ext==L".jpeg"||
                           ext==L".bmp"||ext==L".webp"){
                            ++thumbnailBudget;
                            if(cancelToken->load())return;
                            auto result=fxfile::thumbnail::query(
                                visualHelper,path,1800,request.thumbnailPixels);
                            if(result.valid()){
                                entry.thumbnailBgra=std::move(result.bgra);
                                entry.thumbnailWidth=result.width;
                                entry.thumbnailHeight=result.height;
                            }
                        }
                    }
                    entry.bytes=(static_cast<std::uint64_t>(
                        data.nFileSizeHigh)<<32)|data.nFileSizeLow;
                    entry.sizeKnown=true;
                    entry.bytesLabel=entry.bytes<1024?
                      std::to_wstring(entry.bytes)+L" B":
                      entry.bytes<1048576?
                      std::to_wstring(entry.bytes/1024)+L" KB":
                      std::to_wstring(entry.bytes/1048576)+L" MB";
                }
                ULARGE_INTEGER timestamp{};
                timestamp.HighPart=data.ftLastWriteTime.dwHighDateTime;
                timestamp.LowPart=data.ftLastWriteTime.dwLowDateTime;
                entry.modified=timestamp.QuadPart;
                FILETIME local{};
                SYSTEMTIME stamp{};
                if(::FileTimeToLocalFileTime(&data.ftLastWriteTime,&local)&&
                   ::FileTimeToSystemTime(&local,&stamp)){
                    wchar_t date[32]{},time[24]{};
                    if(::GetDateFormatEx(L"ko-KR",0,&stamp,L"yyyy-MM-dd",date,32,nullptr)&&
                       ::GetTimeFormatEx(L"ko-KR",0,&stamp,L"HH:mm",time,24)){
                        entry.dateLabel=std::wstring(date)+L" "+time;
                        entry.dateKnown=true;
                    }
                }
            }
            if(cancelToken->load())return;
            Completion result{};
            result.side=request.side;
            result.tab=request.tab;
            result.route=request.route;
            result.ticket=request.ticket;
            result.details=std::move(details);
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

} // namespace fxfile::previewdetail
