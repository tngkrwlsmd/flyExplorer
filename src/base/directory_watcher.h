// Win32-only filesystem invalidation. No Shell/COM/UI dependency.
// Separate from the two potentially untrusted Shell helper processes.
#pragma once
#ifndef FXFILE_BASE_DIRECTORY_WATCHER_H
#define FXFILE_BASE_DIRECTORY_WATCHER_H
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
namespace fxfile { namespace directorychange {
using Callback=std::function<void(std::uint64_t,std::uint64_t)>;
class DirectoryWatcher final {
public:
    explicit DirectoryWatcher(Callback change);
    ~DirectoryWatcher();
    DirectoryWatcher(DirectoryWatcher const&)=delete;
    DirectoryWatcher& operator=(DirectoryWatcher const&)=delete;
    bool start();
    void watch(std::uint64_t route,std::uint64_t token,std::wstring path);
    void unwatch(std::uint64_t route);
    void shutdown() noexcept;
private:
    struct State;
    std::shared_ptr<State> state_;
    static void run(std::shared_ptr<State>) noexcept;
};
} }
#endif
