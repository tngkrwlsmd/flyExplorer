// M1.9/M2 search core: Win32-only, read-only, bounded name search and
// opt-in per-preview recent filesystem scopes. No legacy fxfile profile.
#pragma once
#ifndef FLYEXPLORER_WINUI_PREVIEW_M19_SEARCH_H
#define FLYEXPLORER_WINUI_PREVIEW_M19_SEARCH_H
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace fxfile { namespace preview {

enum class SearchEntryKind {
    Files,
    Folders,
    FilesAndFolders,
};

struct SearchQuery {
    std::wstring term;
    std::wstring extension;
    std::wstring minSizeKb;
    std::wstring maxSizeKb;
    std::wstring modifiedAfter;
    std::wstring modifiedBefore;
    bool regex=false;
    bool caseSensitive=false;
    SearchEntryKind kind=SearchEntryKind::Files;
};

enum class SearchQueryValidation {
    Valid,
    InvalidTerm,
    InvalidExtension,
    InvalidSizeRange,
    InvalidDateRange,
    InvalidRegex,
};

struct SearchResults {
    std::wstring scope;
    std::wstring term;
    bool valid=false,truncated=false,canceled=false,invalidPattern=false;
    size_t count=0;
    std::vector<std::wstring> matches;
};

SearchQueryValidation validateSearchQuery(SearchQuery const&) noexcept;
bool sameSearchQuery(SearchQuery const&,SearchQuery const&) noexcept;

SearchResults scanFiles(
    std::wstring const& folder,SearchQuery const& query,
    std::shared_ptr<std::atomic_bool> cancel);

SearchResults scanFiles(
    std::wstring const& folder,std::wstring const& term,
    std::shared_ptr<std::atomic_bool> cancel);

bool readRecentScopes(std::vector<std::wstring>& result);
bool writeRecentScopes(std::vector<std::wstring> const& recent);
void rememberScope(std::vector<std::wstring>& recent,
                   std::wstring const& folder);

} }
#endif
