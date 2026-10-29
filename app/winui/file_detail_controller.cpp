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
       request.folderHints.size()!=request.paths.size()||
       request.shellParsingNames.size()!=request.paths.size()||
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
            static constexpr wchar_t const* knownFolderKeys[]{
                L"desktop",L"documents",L"downloads",
                L"pictures",L"music",L"videos"
            };
            std::vector<std::pair<std::wstring,std::wstring>> knownFolderPaths;
            knownFolderPaths.reserve(6);
            for(auto const* key:knownFolderKeys){
                auto path=fxfile::filetype::knownFolderPath(key);
                if(!path.empty())
                    knownFolderPaths.emplace_back(key,std::move(path));
            }
            std::vector<std::wstring> knownFolderKeyByIndex(
                request.paths.size());
            std::vector<std::wstring> requestedKnownFolderKeys;
            for(std::size_t i=0;i<request.paths.size();++i){
                auto const& candidate=request.paths[i];
                if(candidate.empty())continue;
                for(auto const& known:knownFolderPaths){
                    if(::CompareStringOrdinal(
                         candidate.c_str(),-1,known.second.c_str(),-1,TRUE)
                       !=CSTR_EQUAL)continue;
                    knownFolderKeyByIndex[i]=known.first;
                    if(std::find(requestedKnownFolderKeys.begin(),
                         requestedKnownFolderKeys.end(),known.first)
                       ==requestedKnownFolderKeys.end())
                        requestedKnownFolderKeys.push_back(known.first);
                    break;
                }
            }
            std::vector<std::wstring> extensions{L".flyfolder"};
            for(auto const& path:request.paths){
                // Match sortable metadata's filename-only extension rule:
                // .gitignore has no extension; .env.local has .local.
                auto ext=std::filesystem::path(path).extension().native();
                if(!fxfile::filetype::safeExtension(ext))continue;
                std::transform(ext.begin(),ext.end(),ext.begin(),
                   [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                if(std::find(extensions.begin(),extensions.end(),ext)==extensions.end()
                     &&extensions.size()<24)extensions.push_back(ext);
            }
            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::unordered_map<std::wstring,fxfile::filetype::Visual>
                knownFolderVisuals;
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
                    if(!requestedKnownFolderKeys.empty())
                        knownFolderVisuals=fxfile::filetype::queryKnownFolderVisuals(
                            visualHelper,requestedKnownFolderKeys,
                            2500,request.visualPixels);
                }
            }
            std::vector<std::uint8_t> shellThumbnailHints(
                request.paths.size(),0);
            if(request.shellProviderRoot&&
               (request.viewMode==FileViewMode::MediumIcons||
                request.viewMode==FileViewMode::LargeIcons)){
                std::size_t selected=0;
                auto select=[&](bool imageLike){
                    for(std::size_t i=0;
                        i<request.shellParsingNames.size()&&selected<4;++i){
                        if(shellThumbnailHints[i]||request.folderHints[i]||
                           request.shellParsingNames[i].empty())continue;
                        auto const& parsing=request.shellParsingNames[i];
                        const auto dot=parsing.find_last_of(L'.');
                        const auto slash=parsing.find_last_of(L"\\/");
                        std::wstring ext;
                        if(dot!=std::wstring::npos&&
                           (slash==std::wstring::npos||dot>slash)){
                            ext=parsing.substr(dot);
                            std::transform(ext.begin(),ext.end(),ext.begin(),
                              [](wchar_t c){
                               return static_cast<wchar_t>(::towlower(c));});
                        }
                        const bool supportedImage=
                            ext==L".png"||ext==L".jpg"||ext==L".jpeg"||
                            ext==L".bmp"||ext==L".webp";
                        if(supportedImage!=imageLike)continue;
                        shellThumbnailHints[i]=1;
                        ++selected;
                    }
                };
                select(true);
                select(false);
            }
            std::vector<fxfile::filetype::Visual> shellItemVisuals;
            if(!visualHelper.empty()&&
               std::any_of(request.shellParsingNames.begin(),
                           request.shellParsingNames.end(),
                           [](std::wstring const& value){return !value.empty();})){
                if(cancelToken->load())return;
                const bool wantsShellThumbnail=std::any_of(
                    shellThumbnailHints.begin(),shellThumbnailHints.end(),
                    [](std::uint8_t value){return value!=0;});
                shellItemVisuals=fxfile::filetype::queryShellItemVisuals(
                    visualHelper,request.shellParsingNames,shellThumbnailHints,
                    cancelToken.get(),4500,request.visualPixels,
                    wantsShellThumbnail?request.thumbnailPixels:0u);
                if(!shellItemVisuals.empty()&&
                   shellItemVisuals.size()!=request.paths.size())return;
            }
            std::vector<FileDetail> details(request.paths.size());
            std::size_t thumbnailBudget=0;
            for(std::size_t i=0;i<request.paths.size();++i){
                if(cancelToken->load())return; // prevent stale visual child launch
                auto const& path=request.paths[i];
                auto const& shellParsing=request.shellParsingNames[i];
                if((path.empty()&&shellParsing.empty())||
                   path.size()>32000||shellParsing.size()>4096)continue;
                WIN32_FILE_ATTRIBUTE_DATA data{};
                bool folder=request.folderHints[i]!=0;
                if(!path.empty()&&!request.isolatedPathAccess){
                    if(!::GetFileAttributesExW(
                         path.c_str(),GetFileExInfoStandard,&data))
                        continue;
                    if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)
                        continue;
                    folder=(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)!=0;
                }
                auto& entry=details[i];
                if(folder){
                    entry.typeLabel=L"폴더";
                    auto const& knownKey=knownFolderKeyByIndex[i];
                    auto known=knownKey.empty()?knownFolderVisuals.end():
                        knownFolderVisuals.find(knownKey);
                    if(known!=knownFolderVisuals.end()&&
                       !known->second.bgra.empty()){
                        entry.iconBgra=known->second.bgra;
                        entry.iconWidth=known->second.width;
                        entry.iconHeight=known->second.height;
                        entry.knownFolderVisual=true;
                    }else{
                        auto folder=windowsTypes.find(L".flyfolder");
                        if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                            entry.iconBgra=folder->second.bgra;
                            entry.iconWidth=folder->second.width;
                            entry.iconHeight=folder->second.height;
                        }
                    }
                }else{
                    auto ext=std::filesystem::path(path).extension().native();
                    entry.typeLabel=ext.size()>1&&ext.size()<=17?
                        ext.substr(1)+L" 파일":L"파일";
                    if(!ext.empty()){
                        std::transform(ext.begin(),ext.end(),ext.begin(),
                           [](wchar_t c){return static_cast<wchar_t>(::towlower(c));});
                        auto found=windowsTypes.find(ext);
                        if(found!=windowsTypes.end()){
                            // Keep the Details Type column concise:
                            // a registered Windows name replaces, rather
                            // than duplicates, the extension fallback.
                            if(!found->second.label.empty())
                                entry.typeLabel=found->second.label;
                            entry.iconBgra=found->second.bgra;
                            entry.iconWidth=found->second.width;
                            entry.iconHeight=found->second.height;
                        }
                    }
                }
                if(shellItemVisuals.size()==request.paths.size()){
                    auto const& shellVisual=shellItemVisuals[i];
                    if(!shellVisual.label.empty())
                        entry.typeLabel=shellVisual.label;
                    if(!shellVisual.bgra.empty()){
                        entry.iconBgra=shellVisual.bgra;
                        entry.iconWidth=shellVisual.width;
                        entry.iconHeight=shellVisual.height;
                        entry.knownFolderVisual=false;
                    }
                    if(!shellVisual.thumbnailBgra.empty()){
                        entry.thumbnailBgra=shellVisual.thumbnailBgra;
                        entry.thumbnailWidth=shellVisual.thumbnailWidth;
                        entry.thumbnailHeight=shellVisual.thumbnailHeight;
                    }
                }
                if(!folder&&!path.empty()&&!request.shellProviderRoot){
                    const bool thumbnailSizeEligible=request.isolatedPathAccess||
                        (data.nFileSizeHigh==0&&
                         data.nFileSizeLow<=32*1024*1024);
                    if((request.viewMode==FileViewMode::MediumIcons||
                        request.viewMode==FileViewMode::LargeIcons)&&
                       !visualHelper.empty()&&thumbnailBudget<4&&
                       thumbnailSizeEligible){
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
