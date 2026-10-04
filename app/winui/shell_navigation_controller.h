#pragma once
#include "../../src/base/explorer_ui_state.h"
#include "../../src/base/shell_isolated_supervisor.h"
#include "../../src/base/directory_watcher.h"
#include "../../src/base/shell_namespace_watcher.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace fxfile::previewnav {

class ShellNavigationController final {
public:
    enum class StartFailure {
        None,
        Supervisor,
        DirectoryWatcher,
        ShellNamespaceWatcher
    };
    enum class CompletionKind {
        Ignored,
        Failed,
        Applied,
        Extended,
        Rejected,
        NoChange
    };
    enum class PageDirection {
        None,
        Forward,
        Backward
    };
    struct Completion final {
        CompletionKind kind=CompletionKind::Ignored;
        int side=-1;
        std::size_t tab=0;
        std::uint64_t request=0;
        bool active=false;
        PageDirection pageDirection=PageDirection::None;
        fxfile::shellnav::NavigationAction action=
            fxfile::shellnav::NavigationAction::Open;
        HRESULT hr=S_OK;
        bool recovered=false;
        bool timedOut=false;
        bool networkRequest=false;
    };
    enum class ChangeDisposition {
        Ignored,
        Queued,
        InvalidTarget,
        SubmitFailed
    };

    ShellNavigationController(
        fxfile::shellnav::IsolatedCallback result,
        fxfile::directorychange::Callback change);
    ~ShellNavigationController();

    StartFailure start(std::wstring absoluteHelperExe);
    void shutdown() noexcept;

    std::uint64_t submitParsing(
        fxfile::explorerui::Model& model,int side,std::size_t tab,
        std::wstring path,bool supersedeOthers);
    std::uint64_t submitActive(
        fxfile::explorerui::Model& model,int side,
        fxfile::shellnav::Location target,
        fxfile::shellnav::NavigationAction action);
    std::uint64_t submitNextPage(
        fxfile::explorerui::Model& model,int side,std::size_t ceiling);
    std::uint64_t submitPreviousPage(
        fxfile::explorerui::Model& model,int side);

    Completion accept(
        fxfile::explorerui::Model& model,
        fxfile::shellnav::IsolatedResult result);
    void updateWatch(
        fxfile::explorerui::Model const& model,int side,bool force=false,
        bool forceShellNamespace=false);
    ChangeDisposition handleChange(
        fxfile::explorerui::Model& model,
        std::uint64_t route,std::uint64_t token);

    void forget(std::uint64_t route);
    void suspend(fxfile::explorerui::Model& model);
    void release(fxfile::explorerui::Model& model);

#if defined(_DEBUG)
    std::uint64_t submitOwnedTestDelay(
        fxfile::explorerui::Model& model,int side,std::size_t tab,
        std::wstring recoveryFolder,bool supersedeOthers);
    std::uint64_t submitOwnedComDelay(
        fxfile::explorerui::Model& model,int side,std::size_t tab,
        std::wstring recoveryFolder,bool exhaust,bool supersedeOthers);
#endif

private:
    bool validTab(
        fxfile::explorerui::Model const& model,int side,
        std::size_t tab) const noexcept;
    void clearWatchForRoute(std::uint64_t route) noexcept;
    void clearWatch(int side) noexcept;

    std::unique_ptr<fxfile::shellnav::IsolatedShellSupervisor> supervisor_;
    std::unique_ptr<fxfile::directorychange::DirectoryWatcher> watcher_;
    std::unique_ptr<fxfile::directorychange::ShellNamespaceWatcher> shellWatcher_;
    std::uint64_t nextWatchToken_=1;
    std::array<std::uint64_t,2> watchedRoutes_{};
    std::array<std::uint64_t,2> watchTokens_{};
    std::array<std::wstring,2> watchedPaths_{};
};

} // namespace fxfile::previewnav
