#include "pch.h"
#include "session_coordinator.h"
#include <shellapi.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cwchar>
#include <mutex>
#include <thread>
#include <utility>

namespace fxfile::sessioncoord {

struct SessionCoordinator::SharedState final {
    std::mutex mutation;
    std::atomic_uint64_t epoch{0};
    std::atomic_uint64_t revision{0};
};

SessionCoordinator::SessionCoordinator()
    : state_(std::make_shared<SharedState>())
{
}

bool SessionCoordinator::autoRestoreAllowed() const noexcept
{
    try{
        int argc=0;
        auto argv=::CommandLineToArgvW(::GetCommandLineW(),&argc);
        if(!argv)return false;
        const bool explicitPath=argc>1&&argv[1][0]!=L'-';
        bool testOverride=false;
        wchar_t guard[8]{};
        const bool owned=
            ::GetEnvironmentVariableW(L"FLY_M23_OWNED_SESSION",guard,8)==3&&
            !wcscmp(guard,L"YES");
        if(owned){
            for(int i=1;i<argc;++i){
                if(!wcscmp(argv[i],L"--m23-owned-auto-restore")){
                    testOverride=true;
                    break;
                }
            }
        }
        const bool allowed=argc==1||testOverride||(!explicitPath&&argc==1);
        ::LocalFree(argv);
        return allowed;
    }catch(...){
        return false;
    }
}

SessionCoordinator::CaptureResult SessionCoordinator::capture(
    fxfile::previewtabs::WindowWorkspaceController const& workspace,
    std::uint32_t width,std::uint32_t height) const noexcept
{
    CaptureResult result{};
    try{
        auto& data=result.value.session;
        data.activeWindow=static_cast<std::uint32_t>(workspace.activeIndex());
        data.width=width;
        data.height=height;
        data.windowTabs.reserve(workspace.count());
        result.value.histories.reserve(workspace.count());

        for(auto const& state:workspace.states()){
            CapturedHistory captured{};
            fxfile::uisession::WindowTab saved{};
            saved.split=state.model.split;
            saved.splitPermille=state.splitPermille;
            saved.activeSide=
                static_cast<std::uint32_t>(state.model.activePane);
            for(int side=0;side<2;++side){
                auto const& pane=state.model.panes[side];
                auto& target=saved.panes[side];
                target.selected=static_cast<std::uint32_t>(pane.active);
                if(state.tabSortModes[side].size()!=pane.tabs.size()){
                    result.error=CaptureError::InvalidSession;
                    return result;
                }
                target.sort=static_cast<std::uint32_t>(
                    state.fileLists[side].sortMode);
                target.view=static_cast<std::uint32_t>(
                    state.fileLists[side].viewMode);
                target.nameColumnWidth=static_cast<std::uint32_t>(
                    (std::clamp)(
                        std::lround(state.fileLists[side].nameColumnWidth),
                        80l,600l));
                target.showSelectionCheckboxes=state.fileLists[side].showSelectionCheckboxes;
                target.compactRows=state.fileLists[side].compactRows;
                target.showFileExtensions=state.fileLists[side].showFileExtensions;
                target.showHiddenItems=state.fileLists[side].showHiddenItems;
                target.tabs.reserve(pane.tabs.size());
                captured[side].reserve(pane.tabs.size());
                for(std::size_t i=0;i<pane.tabs.size();++i){
                    fxfile::uisession::PaneTab tab{};
                    tab.sort=static_cast<std::uint32_t>(
                        i==pane.active?state.fileLists[side].sortMode:
                        state.tabSortModes[side][i]);
                    tab.path=i<pane.filesystemPaths.size()?
                        pane.filesystemPaths[i]:L"";
                    if(tab.path.empty())
                        tab.path=pane.tabs[i].snapshot().parsingName;
                    fxfile::shellnav::HistoryLocations history{};
                    if(!pane.tabs[i].historyLocations(history)){
                        result.error=CaptureError::HistoryUnavailable;
                        return result;
                    }
                    captured[side].push_back(std::move(history));
                    target.tabs.push_back(std::move(tab));
                }
            }
            data.windowTabs.push_back(std::move(saved));
            result.value.histories.push_back(std::move(captured));
        }
        if(!fxfile::uisession::valid(data)){
            result.error=CaptureError::InvalidSession;
            return result;
        }
        result.error=CaptureError::None;
        return result;
    }catch(...){
        result.error=CaptureError::InvalidSession;
        return result;
    }
}

bool SessionCoordinator::save(
    Capture&& capture,Post post,Completion completion)
{
    if(!post||!completion)return false;
    const auto shared=state_;
    shared->epoch.fetch_add(1);
    const auto ticket=shared->revision.fetch_add(1)+1;
    try{
        std::thread([
            shared,capture=std::move(capture),ticket,
            post=std::move(post),completion=std::move(completion)
        ]() mutable {
            std::lock_guard<std::mutex> guarded(shared->mutation);
            if(ticket!=shared->revision.load())return;

            bool ok=capture.histories.size()==capture.session.windowTabs.size();
            for(std::size_t w=0;ok&&w<capture.histories.size();++w){
                for(int side=0;ok&&side<2;++side){
                    auto& tabs=capture.session.windowTabs[w].panes[side].tabs;
                    if(capture.histories[w][side].size()!=tabs.size()){
                        ok=false;
                        break;
                    }
                    for(std::size_t i=0;ok&&i<tabs.size();++i){
                        fxfile::shellnav::HistoryPaths paths{};
                        ok=fxfile::shellnav::historyPathsFromLocations(
                            capture.histories[w][side][i],paths);
                        if(ok){
                            tabs[i].back=std::move(paths.back);
                            tabs[i].forward=std::move(paths.forward);
                        }
                    }
                }
            }
            if(ok)ok=fxfile::uisession::save(capture.session);
            if(ticket!=shared->revision.load())return;
            try{
                post([
                    shared,ticket,ok,
                    completion=std::move(completion)
                ]() mutable {
                    if(ticket!=shared->revision.load())return;
                    completion(ok);
                });
            }catch(...){}
        }).detach();
        return true;
    }catch(...){
        return false;
    }
}

bool SessionCoordinator::load(Post post,RestoreCompletion completion)
{
    if(!post||!completion)return false;
    const auto shared=state_;
    const auto ticket=shared->epoch.fetch_add(1)+1;
    const auto revisionTicket=shared->revision.load();
    try{
        std::thread([
            shared,ticket,revisionTicket,
            post=std::move(post),completion=std::move(completion)
        ]() mutable {
            auto payload=std::make_shared<RestorePayload>();
            bool ok=fxfile::uisession::load(payload->session);
            std::vector<fxfile::uisession::WindowTab> windows{};
            if(ok){
                windows=payload->session.windowTabs;
                if(windows.empty()){
                    fxfile::uisession::WindowTab legacy{};
                    legacy.split=payload->session.split;
                    legacy.splitPermille=payload->session.splitPermille;
                    legacy.activeSide=payload->session.activeSide;
                    for(int side=0;side<2;++side){
                        auto paths=payload->session.paths[side];
                        if(side==1&&!legacy.split){
                            paths={payload->session.paths[0][
                                payload->session.selected[0]]};
                        }
                        legacy.panes[side].selected=
                            side==1&&!legacy.split?
                                0:payload->session.selected[side];
                        legacy.panes[side].sort=payload->session.sort[side];
                        for(auto const& path:paths){
                            fxfile::uisession::PaneTab tab{};
                            tab.path=path;
                            tab.sort=legacy.panes[side].sort;
                            legacy.panes[side].tabs.push_back(std::move(tab));
                        }
                    }
                    windows.push_back(std::move(legacy));
                    payload->session.activeWindow=0;
                }

                const HRESULT co=
                    ::CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
                const bool uninit=SUCCEEDED(co);
                if(FAILED(co)&&co!=RPC_E_CHANGED_MODE)ok=false;

                for(std::size_t w=0;ok&&w<windows.size();++w){
                    auto const& source=windows[w];
                    fxfile::previewtabs::WindowTabState state(
                        static_cast<std::uint64_t>(w+1));
                    std::array<std::size_t,2> counts{{
                        source.panes[0].tabs.size(),
                        source.panes[1].tabs.size()}};
                    std::array<std::size_t,2> selected{{
                        source.panes[0].selected,
                        source.panes[1].selected}};
                    ok=state.model.reset(source.split,counts,selected);
                    state.splitPermille=source.splitPermille;
                    if(ok&&source.activeSide){
                        ok=state.model.dispatch(
                            fxfile::explorerui::Command::ActivatePane,
                            static_cast<int>(source.activeSide)).accepted;
                    }
                    for(int side=0;ok&&side<2;++side){
                        state.tabSortModes[side].clear();
                        for(auto const& savedTab:source.panes[side].tabs)
                            state.tabSortModes[side].push_back(static_cast<int>(savedTab.sort));
                        state.fileLists[side].sortMode=
                            state.tabSortModes[side][source.panes[side].selected];
                        state.fileLists[side].viewMode=
                            static_cast<fxfile::previewlist::FileViewMode>(
                                source.panes[side].view);
                        state.fileLists[side].nameColumnWidth=
                            source.panes[side].nameColumnWidth;
                        state.fileLists[side].showSelectionCheckboxes=
                            source.panes[side].showSelectionCheckboxes;
                        state.fileLists[side].compactRows=
                            source.panes[side].compactRows;
                        state.fileLists[side].showFileExtensions=
                            source.panes[side].showFileExtensions;
                        state.fileLists[side].showHiddenItems=
                            source.panes[side].showHiddenItems;
                        auto& pane=state.model.panes[side];
                        for(std::size_t i=0;
                            ok&&i<source.panes[side].tabs.size();++i){
                            auto const& saved=source.panes[side].tabs[i];
                            pane.filesystemPaths[i]=saved.path;
                            ok=SUCCEEDED(pane.tabs[i].open(saved.path));
                            if(ok){
                                ok=pane.tabs[i].restoreHistoryPaths(
                                    {saved.back,saved.forward});
                            }
                        }
                    }
                    if(ok)payload->states.push_back(std::move(state));
                }
                if(uninit)::CoUninitialize();
            }

            if(
                !ok||payload->states.empty()||
                revisionTicket!=shared->revision.load())
                return;

            try{
                post([
                    shared,ticket,revisionTicket,payload,
                    completion=std::move(completion)
                ]() mutable {
                    if(
                        ticket!=shared->epoch.load()||
                        revisionTicket!=shared->revision.load())
                        return;
                    completion(std::move(payload));
                });
            }catch(...){}
        }).detach();
        return true;
    }catch(...){
        return false;
    }
}

bool SessionCoordinator::clear(Post post,Completion completion)
{
    if(!post||!completion)return false;
    const auto shared=state_;
    shared->epoch.fetch_add(1);
    const auto ticket=shared->revision.fetch_add(1)+1;
    try{
        std::thread([
            shared,ticket,post=std::move(post),
            completion=std::move(completion)
        ]() mutable {
            std::lock_guard<std::mutex> guarded(shared->mutation);
            if(ticket!=shared->revision.load())return;
            const bool ok=fxfile::uisession::clear();
            if(ticket!=shared->revision.load())return;
            try{
                post([
                    shared,ticket,ok,
                    completion=std::move(completion)
                ]() mutable {
                    if(ticket!=shared->revision.load())return;
                    completion(ok);
                });
            }catch(...){}
        }).detach();
        return true;
    }catch(...){
        return false;
    }
}

bool SessionCoordinator::applyRestore(
    RestorePayload& payload,
    fxfile::previewtabs::WindowWorkspaceController& workspace)
{
    if(payload.states.empty())return false;
    return workspace.replace(
        std::move(payload.states),
        static_cast<std::size_t>(payload.session.activeWindow));
}

void SessionCoordinator::prepareForClose() noexcept
{
    state_->epoch.fetch_add(1);
    state_->revision.fetch_add(1);
}

} // namespace fxfile::sessioncoord
