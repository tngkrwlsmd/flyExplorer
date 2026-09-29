// Windows registered file-type names: bounded disposable helper process.
// Never invoke association or Shell extension code on the WinUI UI thread.
#pragma once
#include <windows.h>
#include <string>
#include <unordered_map>
#include <vector>

namespace fxfile::filetype {
// Extensions are limited to one period followed by 1..16 ASCII alpha/numeric
// characters; no path or command-line metacharacters reach the helper.
bool safeExtension(std::wstring const& ext) noexcept;
// On failures or timeout returns an empty mapping. The caller's original
// generic extension-based classification remains a valid safe fallback.
std::unordered_map<std::wstring,std::wstring> query(
    std::wstring const& ownedHelper,
    std::vector<std::wstring> const& extensions,
    DWORD timeoutMs=2500) noexcept;
}
