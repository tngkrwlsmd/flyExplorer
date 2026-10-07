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

namespace fxfile::previewdetail {

class FileDetailController final {
public:
    struct Request final {
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::uint64_t ticket=0;
        fxfile::previewlist::FileViewMode viewMode=
            fxfile::previewlist::FileViewMode::Details;
        std::uint32_t visualPixels=16;
        std::uint32_t thumbnailPixels=48;
        bool isolatedPathAccess=false;
        bool shellProviderRoot=false;
        std::vector<std::wstring> paths{};
        std::vector<std::wstring> shellParsingNames{};
        std::vector<std::uint8_t> folderHints{};
    };
    struct Completion final {
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::uint64_t ticket=0;
        std::vector<fxfile::previewlist::FileDetail> details{};
    };
    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using CompletionCallback=std::function<void(Completion)>;

    FileDetailController()=default;
    ~FileDetailController();
    bool start(Request request,Post post,CompletionCallback completion);
    void cancel(int side) noexcept;
    void prepareForClose() noexcept;

private:
    std::array<std::shared_ptr<std::atomic_bool>,2> cancel_{};
    std::atomic_bool closing_{false};
};

} // namespace fxfile::previewdetail
