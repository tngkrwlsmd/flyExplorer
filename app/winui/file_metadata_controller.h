#pragma once
#include "file_list_state.h"
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace fxfile::previewmetadata {

// Separate metadata-index budget; ordinary complete-model and network
// transport limits remain unchanged. Only local fixed-drive paths qualify.
inline constexpr std::size_t kMaxIndexedMetadataEntries=25000;
inline constexpr std::size_t kMaxIndexedMetadataPathUnits=12*1024*1024;

class FileMetadataController final {
public:
    struct Request final {
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::uint64_t ticket=0;
        bool isolatedNetwork=false;
        bool requireCompleteIndex=false;
        std::vector<std::wstring> paths{};
    };
    struct Completion final {
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::uint64_t ticket=0;
        std::uint32_t error=0;
        std::vector<fxfile::previewlist::FileMetadata> metadata{};
    };
    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using CompletionCallback=std::function<void(Completion)>;

    FileMetadataController()=default;
    ~FileMetadataController();
    bool start(Request request,Post post,CompletionCallback completion);
    void cancel(int side) noexcept;
    void prepareForClose() noexcept;

private:
    std::array<std::shared_ptr<std::atomic_bool>,2> cancel_{};
    std::atomic_bool closing_{false};
};

} // namespace fxfile::previewmetadata
