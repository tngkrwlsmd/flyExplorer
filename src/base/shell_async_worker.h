// MFC-free, nonblocking lifetime, private COM STA Shell requests and
// directory invalidation. All COM interfaces stay on the worker STA.
// The caller/UI receives only value snapshots and owned absolute PIDLs.
#pragma once
#ifndef FXFILE_BASE_SHELL_ASYNC_WORKER_H
#define FXFILE_BASE_SHELL_ASYNC_WORKER_H
#include "shell_navigation_core.h"
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
namespace fxfile { namespace shellnav {
enum class NavigationAction { Open, Back, Forward, Up, Refresh };
struct AsyncResult final {
    std::uint64_t route=0;
    std::uint64_t request=0;
    NavigationAction action=NavigationAction::Open;
    HRESULT hr=E_UNEXPECTED;
    Snapshot snapshot;
};
using ResultCallback=std::function<void(AsyncResult)>;
using ChangeCallback=std::function<void(std::uint64_t route,
                                        std::uint64_t watchToken)>;

// Single serialized STA worker. Newer requests for the SAME route supersede
// old results. Other pane/tab routes retain their own queued requests.
// shutdown() NEVER synchronously joins a third-party Shell extension:
// the detached thread keeps only shared internal state (not a UI pointer).
class AsyncShellWorker final {
public:
    AsyncShellWorker(ResultCallback result,ChangeCallback changed);
    ~AsyncShellWorker();
    AsyncShellWorker(AsyncShellWorker const&)=delete;
    AsyncShellWorker& operator=(AsyncShellWorker const&)=delete;
    bool start();
    std::uint64_t submit(std::uint64_t route,Location target,
                         NavigationAction action);
    std::uint64_t submitParsing(std::uint64_t route,std::wstring path);
    void watch(std::uint64_t route,std::uint64_t watchToken,
               std::wstring filesystemDirectory);
    void unwatch(std::uint64_t route);
    void forget(std::uint64_t route);
    void shutdown() noexcept;
private:
    struct State;
    std::shared_ptr<State> state_;
    static void run(std::shared_ptr<State> state) noexcept;
};
} }
#endif
