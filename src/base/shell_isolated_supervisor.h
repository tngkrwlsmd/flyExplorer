// Native, MFC-free, bounded read-only Shell child supervisor for WinUI 3.
// Two independent lanes, one exact-owned helper per active pane, never a
// product/user process. Child failures do not share Shell COM apartments.
#pragma once
#ifndef FXFILE_BASE_SHELL_ISOLATED_SUPERVISOR_H
#define FXFILE_BASE_SHELL_ISOLATED_SUPERVISOR_H
#include "shell_async_worker.h" // shared NavigationAction type (no worker used)
#include <functional>
#include <memory>
#include <string>
#include <cstdint>
namespace fxfile { namespace shellnav {
struct IsolatedResult {
    std::uint64_t route=0,request=0;
    NavigationAction action=NavigationAction::Open;
    HRESULT hr=E_UNEXPECTED;
    Snapshot snapshot;
    std::wstring filesystemPath; // computed inside the isolated child
    bool recovered=false;
    bool timedOut=false;
    bool networkRequest=false;
    std::uint32_t attempts=0;
};
using IsolatedCallback=std::function<void(IsolatedResult)>;
class IsolatedShellSupervisor final {
public:
    explicit IsolatedShellSupervisor(IsolatedCallback);
    ~IsolatedShellSupervisor();
    IsolatedShellSupervisor(IsolatedShellSupervisor const&)=delete;
    IsolatedShellSupervisor& operator=(IsolatedShellSupervisor const&)=delete;
    bool start(std::wstring absoluteHelperExe);
    std::uint64_t submit(int pane,std::uint64_t route,Location target,
                         NavigationAction action);
    std::uint64_t submitParsing(int pane,std::uint64_t route,std::wstring path);
    void forget(std::uint64_t route);
    void shutdown() noexcept;
#if defined(_DEBUG)
    // Opt-in, test-owned synthetic timeout; not reachable by typing a path.
    std::uint64_t submitOwnedTestDelay(int pane,std::uint64_t route,
                                      std::wstring recoveryFolder);
    // Test-only self-contained COM object, never a registered Shell extension.
    std::uint64_t submitOwnedComDelay(int pane,std::uint64_t route,
                                     std::wstring recoveryFolder,bool exhaust=false);
#endif
private:
    struct State;
    std::shared_ptr<State> state_;
    static void runLane(std::shared_ptr<State>,int pane) noexcept;
};
} }
#endif
