// WinUI-preview file-list cache state; no UI objects or Shell COM interfaces.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace fxfile::previewlist {
struct FileDetail final {
    std::uint64_t bytes=0;
    std::uint64_t modified=0;
    std::wstring bytesLabel;
    std::wstring typeLabel;
    std::wstring dateLabel;
    bool sizeKnown=false;
    bool dateKnown=false;
};
struct PaneState final {
    int sortMode=0;
    std::vector<FileDetail> details;
    std::vector<std::wstring> renderedPaths;
    std::uint64_t route=0,epoch=0;
    std::size_t tab=0;
    void invalidate() noexcept {
        ++epoch;
        details.clear();
        route=0;
    }
    std::uint64_t begin(std::uint64_t nextRoute,std::size_t nextTab) {
        ++epoch;
        route=nextRoute;
        tab=nextTab;
        details.clear();
        return epoch;
    }
    bool isCurrent(std::uint64_t expectedRoute,std::size_t expectedTab,
                   std::size_t expectedItems) const noexcept {
        return route!=0 && route==expectedRoute && tab==expectedTab &&
               details.size()==expectedItems;
    }
    bool accepts(std::uint64_t ticket,std::uint64_t expectedRoute,
                 std::size_t expectedTab) const noexcept {
        return epoch==ticket && route!=0 && route==expectedRoute &&
               tab==expectedTab;
    }
};
} // namespace fxfile::previewlist
