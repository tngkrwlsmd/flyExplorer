// Read-only Windows Shell change registration on an independent message-pump thread.
// Never invokes EnumObjects, parses user input, or runs on the WinUI STA.
#pragma once
#ifndef FXFILE_BASE_SHELL_NAMESPACE_WATCHER_H
#define FXFILE_BASE_SHELL_NAMESPACE_WATCHER_H
#include <windows.h>
#include <shlobj.h>
#include <cstdint>
#include <functional>
#include <memory>
namespace fxfile { namespace directorychange {
class ShellNamespaceWatcher final {
public:
    using Callback=std::function<void(std::uint64_t,std::uint64_t)>;
    explicit ShellNamespaceWatcher(Callback);
    ~ShellNamespaceWatcher();
    ShellNamespaceWatcher(ShellNamespaceWatcher const&)=delete;
    ShellNamespaceWatcher& operator=(ShellNamespaceWatcher const&)=delete;
    bool start();
    void watch(std::uint64_t route,std::uint64_t token,
               PCIDLIST_ABSOLUTE folder);
    void unwatch(std::uint64_t route);
    void shutdown() noexcept;
private:
    struct State;
    std::shared_ptr<State> state_;
    static void run(std::shared_ptr<State>) noexcept;
};
} }
#endif
