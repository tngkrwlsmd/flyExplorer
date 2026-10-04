// UI-independent Windows Shell navigation core shared by legacy ExplorerCtrl
// and the new WinUI 3 shell. GPLv3-or-later project source.
#pragma once
#ifndef FXFILE_BASE_SHELL_NAVIGATION_CORE_H
#define FXFILE_BASE_SHELL_NAVIGATION_CORE_H
#include <windows.h>
#include <shlobj.h>
#include <atomic>
#include <cstddef>
#include <string>
#include <vector>

namespace fxfile { namespace shellnav {

// Existing ExplorerCtrl/ShellEnumerator passes exactly the native EnumObjects
// flags and its owner HWND. The new WinUI session uses hwnd=nullptr.
// No MFC type, UI message pump, global settings, or private window lifetime.
HRESULT openEnumeration(IShellFolder* folder, HWND owner, DWORD flags,
                        IEnumIDList** enumeration) noexcept;

// Full absolute PIDL; own via ILCloneFull and CoTaskMemFree ONLY.
// COM objects themselves are never retained across threads or callbacks.
class Location final {
public:
    Location() noexcept = default;
    explicit Location(PCIDLIST_ABSOLUTE absolute);
    ~Location() noexcept;
    Location(Location const& other);
    Location& operator=(Location const& other);
    Location(Location&& other) noexcept;
    Location& operator=(Location&& other) noexcept;
    PCIDLIST_ABSOLUTE get() const noexcept {return pidl_;}
    bool valid() const noexcept {return pidl_!=nullptr;}
    void reset(PIDLIST_ABSOLUTE owned=nullptr) noexcept;
private:
    PIDLIST_ABSOLUTE pidl_=nullptr;
};

struct Item final {
    Location id;
    std::wstring label;
    std::wstring parsingName;
    SFGAOF attributes=0;
    bool isFolder() const noexcept {return (attributes&SFGAO_FOLDER)!=0;}
    bool isFileSystem() const noexcept {return (attributes&SFGAO_FILESYSTEM)!=0;}
};
struct Snapshot final {
    Location folder;
    std::wstring displayName;
    std::wstring parsingName;
    std::vector<Item> children;
    // Logical enumeration coordinates are independent from resident children.
    // Today baseOffset remains zero because all accepted pages stay resident;
    // keeping these coordinates explicit allows a later bounded resident window
    // without reusing children.size() as the Shell continuation cursor.
    std::size_t baseOffset=0;
    std::size_t nextOffset=0;
    bool truncated=false;
    std::uint64_t logicalIndex(std::size_t resident) const noexcept {
        return static_cast<std::uint64_t>(baseOffset)+resident;
    }
    bool residentIndex(std::uint64_t logical,std::size_t& resident) const noexcept {
        const auto base=static_cast<std::uint64_t>(baseOffset);
        if(logical<base)return false;
        const auto delta=logical-base;
        if(delta>=children.size())return false;
        resident=static_cast<std::size_t>(delta);
        return true;
    }
};

// Call on a COM-initialized STA/UI thread only. Shell extensions may display
// UI or block in EnumObjects, so arbitrary slow/remote folders still require
// a separately designed cancellable STA worker in a later migration phase.
// Atomic cancellation here is a cooperative boundary between Next() calls,
// NOT a guarantee to interrupt a Shell extension already blocked inside COM.
HRESULT enumeratePage(PCIDLIST_ABSOLUTE folder, Snapshot& result,
                      DWORD flags,std::size_t offset,std::size_t itemLimit,
                      std::atomic_bool const* cancel=nullptr) noexcept;
HRESULT enumerate(PCIDLIST_ABSOLUTE folder, Snapshot& result,
                  DWORD flags=SHCONTF_FOLDERS|SHCONTF_NONFOLDERS,
                  size_t itemLimit=1200,
                  std::atomic_bool const* cancel=nullptr) noexcept;

enum class HistoryAction { Open, Back, Forward, Up, Refresh };
struct HistoryPaths final {
    std::vector<std::wstring> back,forward;
};
struct HistoryLocations final {
    std::vector<Location> back,forward;
};
bool historyPathsFromLocations(HistoryLocations const&,HistoryPaths&) noexcept;

class Session final {
public:
    // Commit ONLY a complete owned value snapshot prepared by a separate
    // COM worker; no Shell API call is made on the receiving UI thread.
    HRESULT accept(Snapshot&& prepared,HistoryAction action) noexcept;
    HRESULT appendPage(Snapshot&& page,std::size_t expectedOffset) noexcept;
    // Clone only a PIDL; never transfer the worker's COM interface.
    Location target(HistoryAction action) const;
    HRESULT open(std::wstring const& parsingName) noexcept;
    HRESULT open(PCIDLIST_ABSOLUTE absolute) noexcept;
    HRESULT openDesktop() noexcept;
    HRESULT refresh() noexcept;
    HRESULT back() noexcept;
    HRESULT forward() noexcept;
    HRESULT up() noexcept;
    Snapshot const& snapshot() const noexcept {return current_;}
    bool canBack() const noexcept {return !back_.empty();}
    bool canForward() const noexcept {return !forward_.empty();}
    bool historyLocations(HistoryLocations&) const noexcept;
    bool restoreHistoryPaths(HistoryPaths const&) noexcept;
private:
    HRESULT commit(Location next,bool record) noexcept;
    Snapshot current_;
    std::vector<Location> back_;
    std::vector<Location> forward_;
};

} } // namespace fxfile::shellnav
#endif
