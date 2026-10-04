#pragma once
#include "m19_search.h"
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace fxfile::previewsearch {

class SearchController final {
public:
    struct Context final {
        std::uint64_t windowIdentity=0;
        int side=-1;
        std::size_t tab=0;
        std::uint64_t route=0;
        std::wstring paneFolder;
        std::wstring scope;
        fxfile::preview::SearchQuery query{};
    };

    struct Request final {
        std::wstring scope;
        fxfile::preview::SearchQuery query{};
        bool remember=false;
    };

    enum class StartStatus {
        Started,
        InvalidRequest,
        InvalidExtension,
        InvalidSizeRange,
        InvalidDateRange,
        InvalidContentTerm,
        InvalidContentEncoding,
        InvalidPattern,
        Closing,
        ThreadStartFailed
    };

    enum class Disposition {
        Ignored,
        StaleContext,
        Canceled,
        Invalid,
        Applied
    };

    struct Completion final {
        std::uint64_t ticket=0;
        Context context{};
        Request request{};
        fxfile::preview::SearchResults result{};
    };

    struct Acceptance final {
        Disposition disposition=Disposition::Ignored;
        bool recentChanged=false;
        bool recentSaved=true;
    };

    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using CompletionCallback=std::function<void(Completion)>;
    using RecentCallback=std::function<void(bool)>;

    SearchController();
    ~SearchController();

    StartStatus start(
        Request request,Context context,Post post,
        CompletionCallback completion);
    Acceptance accept(
        Completion const& completion,Context const& liveContext);

    void invalidate() noexcept;
    void prepareForClose() noexcept;

    bool loadRecents(Post post,RecentCallback completion);
    std::vector<std::wstring> recentScopes() const;
    bool clearRecent();

private:
    struct SharedState;
    std::shared_ptr<SharedState> state_;

    static StartStatus validateRequest(Request const&) noexcept;
    static bool sameContext(
        Context const&,Context const&) noexcept;
};

} // namespace fxfile::previewsearch
