// Windows registered file-type names and fixed Known Folder visuals:
// bounded disposable helper process, never on the WinUI UI thread.
#pragma once
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace fxfile::filetype {
// Extensions are limited to one period followed by 1..16 ASCII alpha/numeric
// characters; no path or command-line metacharacters reach the helper.
bool safeExtension(std::wstring const& ext) noexcept;
// Known Folder helper keys are a fixed product-owned allowlist. No arbitrary
// path is passed on the helper command line.
bool safeKnownFolderKey(std::wstring const& key) noexcept;
std::wstring knownFolderPath(std::wstring const& key) noexcept;

// On failures or timeout returns an empty mapping. The caller's original
// generic extension/folder classification remains a valid safe fallback.
struct Visual {
    std::wstring label;
    // Square BGRA from a disposable OS Shell helper, or empty.
    std::vector<unsigned char> bgra;
    std::uint32_t width=0,height=0;
};
std::unordered_map<std::wstring,Visual> queryVisuals(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& extensions,
    DWORD timeoutMs=2500,std::uint32_t requestedPixels=16) noexcept;
std::unordered_map<std::wstring,Visual> queryKnownFolderVisuals(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& keys,
    DWORD timeoutMs=2500,std::uint32_t requestedPixels=16) noexcept;
std::vector<Visual> queryShellItemVisuals(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& parsingNames,
    std::atomic_bool const* cancel=nullptr,
    DWORD inactivityMs=4500,std::uint32_t requestedPixels=16) noexcept;
std::unordered_map<std::wstring,std::wstring> query(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& extensions,
    DWORD timeoutMs=2500) noexcept;
}
