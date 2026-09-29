// M1.9: Win32-only, read-only bounded filename search and isolated
// opt-in per-preview recent filesystem scopes. No legacy fxfile profile.
#pragma once
#ifndef FLYEXPLORER_WINUI_PREVIEW_M19_SEARCH_H
#define FLYEXPLORER_WINUI_PREVIEW_M19_SEARCH_H
#include <atomic>
#include <cstddef>
#include <memory>
#include <string>
#include <vector>
namespace fxfile { namespace preview {
struct SearchResults {
    std::wstring scope;
    std::wstring term;
    bool valid=false,truncated=false,canceled=false;
    size_t count=0;
    std::vector<std::wstring> matches;
};
SearchResults scanFiles(std::wstring const& folder,std::wstring const& term,
                        std::shared_ptr<std::atomic_bool> cancel);
bool readRecentScopes(std::vector<std::wstring>& result);
bool writeRecentScopes(std::vector<std::wstring> const& recent);
void rememberScope(std::vector<std::wstring>& recent,
                   std::wstring const& folder);
} }
#endif
