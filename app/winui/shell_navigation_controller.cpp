#include "pch.h"
#include "shell_navigation_controller.h"
#include <utility>

namespace fxfile::previewnav {
namespace {
fxfile::shellnav::HistoryAction historyAction(
    fxfile::shellnav::NavigationAction action) noexcept
{
    using Action=fxfile::shellnav::NavigationAction;
    using History=fxfile::shellnav::HistoryAction;
    if(action==Action::Back)return History::Back;
    if(action==Action::Forward)return History::Forward;
    if(action==Action::Up)return History::Up;
    if(action==Action::Refresh)return History::Refresh;
    return History::Open;
}
}

ShellNavigationController::ShellNavigationController(
    fxfile::shellnav::IsolatedCallback result,
    fxfile::directorychange::Callback change)
{
    supervisor_=std::make_unique<fxfile::shellnav::IsolatedShellSupervisor>(
        std::move(result));
    watcher_=std::make_unique<fxfile::directorychange::DirectoryWatcher>(change);
    shellWatcher_=std::make_unique<fxfile::directorychange::ShellNamespaceWatcher>(
        std::move(change));
}

ShellNavigationController::~ShellNavigationController()
{
    shutdown();
}

ShellNavigationController::StartFailure ShellNavigationController::start(
    std::wstring absoluteHelperExe)
{
    if(!supervisor_->start(std::move(absoluteHelperExe)))
        return StartFailure::Supervisor;
    if(!watcher_->start()){
        supervisor_->shutdown();
        return StartFailure::DirectoryWatcher;
    }
    if(!shellWatcher_->start()){
        watcher_->shutdown();
        supervisor_->shutdown();
        return StartFailure::ShellNamespaceWatcher;
    }
    return StartFailure::None;
}

void ShellNavigationController::shutdown() noexcept
{
    if(supervisor_)supervisor_->shutdown();
    if(watcher_)watcher_->shutdown();
    if(shellWatcher_)shellWatcher_->shutdown();
    for(int side=0;side<2;++side)clearWatch(side);
}

bool ShellNavigationController::validTab(
    fxfile::explorerui::Model const& model,int side,std::size_t tab) const noexcept
{
    if(side<0||side>1)return false;
    auto const& pane=model.panes[static_cast<std::size_t>(side)];
    return tab<pane.tabs.size()&&tab<pane.routeIds.size()&&
        tab<pane.pending.size()&&tab<pane.filesystemPaths.size();
}

std::uint64_t ShellNavigationController::submitParsing(
    fxfile::explorerui::Model& model,int side,std::size_t tab,
    std::wstring path,bool supersedeOthers)
{
    if(!validTab(model,side,tab))return 0;
    auto& pane=model.panes[static_cast<std::size_t>(side)];
    const auto id=supervisor_->submitParsing(
        side,pane.routeIds[tab],std::move(path));
    if(id)model.markPending(side,tab,id,supersedeOthers);
    return id;
}

std::uint64_t ShellNavigationController::submitActive(
    fxfile::explorerui::Model& model,int side,
    fxfile::shellnav::Location target,
    fxfile::shellnav::NavigationAction action)
{
    if(side<0||side>1||!target.valid())return 0;
    auto& pane=model.panes[static_cast<std::size_t>(side)];
    if(!validTab(model,side,pane.active))return 0;
    const auto id=supervisor_->submit(
        side,pane.routeIds[pane.active],std::move(target),action);
    if(id)model.markPending(side,pane.active,id,true);
    return id;
}

ShellNavigationController::Completion ShellNavigationController::accept(
    fxfile::explorerui::Model& model,
    fxfile::shellnav::IsolatedResult result)
{
    Completion completed{};
    completed.action=result.action;
    completed.recovered=result.recovered;
    completed.timedOut=result.timedOut;
    completed.networkRequest=result.networkRequest;
    completed.hr=result.hr;
    completed.request=result.request;

    for(int side=0;side<2;++side){
        auto& pane=model.panes[static_cast<std::size_t>(side)];
        for(std::size_t tab=0;tab<pane.routeIds.size();++tab){
            if(pane.routeIds[tab]!=result.route ||
               pane.pending[tab]!=result.request)continue;
            completed.side=side;
            completed.tab=tab;
            completed.active=tab==pane.active;
            if(!model.completeRequest(
                side,tab,result.route,result.request))return completed;
            if(FAILED(result.hr)){
                completed.kind=CompletionKind::Failed;
                return completed;
            }
            const auto applied=pane.tabs[tab].accept(
                std::move(result.snapshot),historyAction(result.action));
            completed.hr=applied;
            if(applied==S_OK){
                pane.filesystemPaths[tab]=std::move(result.filesystemPath);
                completed.kind=CompletionKind::Applied;
            }else if(FAILED(applied)){
                completed.kind=CompletionKind::Rejected;
            }else{
                completed.kind=CompletionKind::NoChange;
            }
            return completed;
        }
    }
    return completed;
}

void ShellNavigationController::clearWatch(int side) noexcept
{
    if(side<0||side>1)return;
    watchedRoutes_[side]=0;
    watchTokens_[side]=0;
    watchedPaths_[side].clear();
}

void ShellNavigationController::clearWatchForRoute(std::uint64_t route) noexcept
{
    for(int side=0;side<2;++side)
        if(watchedRoutes_[side]==route)clearWatch(side);
}

void ShellNavigationController::updateWatch(
    fxfile::explorerui::Model const& model,int side,bool force,
    bool forceShellNamespace)
{
    if(side<0||side>1)return;
    auto const& pane=model.panes[static_cast<std::size_t>(side)];
    if(!validTab(model,side,pane.active))return;
    const auto route=pane.routeIds[pane.active];
    const std::wstring path=(side==0||model.split)?
        pane.filesystemPaths[pane.active]:std::wstring{};
    if(!force&&route==watchedRoutes_[side]&&path==watchedPaths_[side])return;

    if(watchedRoutes_[side]){
        watcher_->unwatch(watchedRoutes_[side]);
        shellWatcher_->unwatch(watchedRoutes_[side]);
    }
    clearWatch(side);

    auto const& location=pane.tabs[pane.active].snapshot().folder;
    if(path.empty()&&!location.valid())return;

    const auto token=nextWatchToken_++;
    if(!path.empty()&&!(forceShellNamespace&&side==0))
        watcher_->watch(route,token,path);
    else if(location.valid())
        shellWatcher_->watch(route,token,location.get());
    else
        return;

    watchedRoutes_[side]=route;
    watchTokens_[side]=token;
    watchedPaths_[side]=path;
}

ShellNavigationController::ChangeDisposition
ShellNavigationController::handleChange(
    fxfile::explorerui::Model& model,
    std::uint64_t route,std::uint64_t token)
{
    for(int side=0;side<2;++side){
        if(route!=watchedRoutes_[side]||token!=watchTokens_[side])continue;
        auto& pane=model.panes[static_cast<std::size_t>(side)];
        if(!validTab(model,side,pane.active)||
           pane.routeIds[pane.active]!=route||
           pane.pending[pane.active])
            return ChangeDisposition::Ignored;
        auto target=pane.tabs[pane.active].target(
            fxfile::shellnav::HistoryAction::Refresh);
        if(!target.valid())return ChangeDisposition::InvalidTarget;
        return submitActive(
            model,side,std::move(target),
            fxfile::shellnav::NavigationAction::Refresh)?
            ChangeDisposition::Queued:ChangeDisposition::SubmitFailed;
    }
    return ChangeDisposition::Ignored;
}

void ShellNavigationController::forget(std::uint64_t route)
{
    if(!route)return;
    supervisor_->forget(route);
    watcher_->unwatch(route);
    shellWatcher_->unwatch(route);
    clearWatchForRoute(route);
}

void ShellNavigationController::suspend(fxfile::explorerui::Model& model)
{
    for(int side=0;side<2;++side){
        auto& pane=model.panes[static_cast<std::size_t>(side)];
        for(auto route:pane.routeIds){
            watcher_->unwatch(route);
            shellWatcher_->unwatch(route);
        }
        for(auto& pending:pane.pending)pending=0;
        clearWatch(side);
    }
}

void ShellNavigationController::release(fxfile::explorerui::Model& model)
{
    for(int side=0;side<2;++side){
        auto& pane=model.panes[static_cast<std::size_t>(side)];
        for(auto route:pane.routeIds)forget(route);
        for(auto& pending:pane.pending)pending=0;
    }
}

#if defined(_DEBUG)
std::uint64_t ShellNavigationController::submitOwnedTestDelay(
    fxfile::explorerui::Model& model,int side,std::size_t tab,
    std::wstring recoveryFolder,bool supersedeOthers)
{
    if(!validTab(model,side,tab))return 0;
    auto& pane=model.panes[static_cast<std::size_t>(side)];
    const auto id=supervisor_->submitOwnedTestDelay(
        side,pane.routeIds[tab],std::move(recoveryFolder));
    if(id)model.markPending(side,tab,id,supersedeOthers);
    return id;
}

std::uint64_t ShellNavigationController::submitOwnedComDelay(
    fxfile::explorerui::Model& model,int side,std::size_t tab,
    std::wstring recoveryFolder,bool exhaust,bool supersedeOthers)
{
    if(!validTab(model,side,tab))return 0;
    auto& pane=model.panes[static_cast<std::size_t>(side)];
    const auto id=supervisor_->submitOwnedComDelay(
        side,pane.routeIds[tab],std::move(recoveryFolder),exhaust);
    if(id)model.markPending(side,tab,id,supersedeOthers);
    return id;
}
#endif

} // namespace fxfile::previewnav
