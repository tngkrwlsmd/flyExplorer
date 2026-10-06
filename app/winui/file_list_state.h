// WinUI-preview file-list cache state; no UI objects or Shell COM interfaces.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace fxfile::previewlist {
enum class FileViewMode : int { Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4 };
struct FileMetadata final {
    std::uint64_t bytes=0;
    std::uint64_t modified=0;
    std::wstring bytesLabel;
    std::wstring dateLabel;
    std::wstring typeKey;
    bool sizeKnown=false;
    bool dateKnown=false;
};
struct FileDetail final {
    std::wstring typeLabel;
    std::vector<unsigned char> iconBgra; // optional isolated system item icon
    std::uint32_t iconWidth=0,iconHeight=0;
    bool knownFolderVisual=false;
    std::vector<unsigned char> thumbnailBgra;
    std::uint32_t thumbnailWidth=0,thumbnailHeight=0;
};
struct PaneState final {
    int sortMode=0;
    FileViewMode viewMode=FileViewMode::Details;
    int appliedItemsPanel=0; // 0=vertical XAML default, 1=small wrap, 2=medium wrap, 3=large wrap
    std::uint32_t visualPixels=0; // DPI-scaled system visual size for current details
    double nameColumnWidth=168.0;
    double typeColumnWidth=180.0;
    double sizeColumnWidth=80.0;
    // Render a bounded first view page. Large Shell folders keep only the
    // currently streamed native pages; route/tab identity resets both view
    // paging and continuation intent on navigation without stale UI rows.
    std::wstring filenameFilter;
    std::size_t filteredCount=0;
    std::size_t visibleCount=160;
    std::uint64_t visibleRoute=0;
    std::size_t visibleTab=0;
    bool streamToComplete=false;
    bool indexToComplete=false;
    bool indexedNameSort=false;
    bool indexedNameProjection=false;
    bool fullModelLimitReached=false;
    std::vector<FileMetadata> metadata;
    std::vector<FileDetail> details;
    std::size_t renderedBaseOffset=0;
    std::vector<std::uint64_t> renderedLogical;
    std::vector<std::wstring> renderedPaths;
    std::uint64_t metadataRoute=0,metadataEpoch=0;
    std::size_t metadataTab=0;
    std::uint64_t route=0,epoch=0;
    std::size_t tab=0;
    void invalidateMetadata() noexcept {
        ++metadataEpoch;
        metadata.clear();
        metadataRoute=0;
    }
    void invalidateDetails() noexcept {
        ++epoch;
        details.clear();
        visualPixels=0;
        route=0;
    }
    void invalidate() noexcept {
        invalidateMetadata();
        invalidateDetails();
    }
    std::uint64_t beginMetadata(
        std::uint64_t nextRoute,std::size_t nextTab) {
        ++metadataEpoch;
        metadataRoute=nextRoute;
        metadataTab=nextTab;
        metadata.clear();
        return metadataEpoch;
    }
    bool metadataCurrent(
        std::uint64_t expectedRoute,std::size_t expectedTab,
        std::size_t expectedItems) const noexcept {
        return metadataRoute!=0 && metadataRoute==expectedRoute &&
               metadataTab==expectedTab && metadata.size()==expectedItems;
    }
    bool acceptsMetadata(
        std::uint64_t ticket,std::uint64_t expectedRoute,
        std::size_t expectedTab) const noexcept {
        return metadataEpoch==ticket && metadataRoute!=0 &&
               metadataRoute==expectedRoute && metadataTab==expectedTab;
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
