#pragma once
#include "window_workspace_controller.h"
#include "../../src/base/ui_session.h"
#include "../../src/base/shell_navigation_core.h"
#include <array>
#include <cstdint>
#include <functional>
#include <memory>
#include <vector>

namespace fxfile::sessioncoord {

class SessionCoordinator final {
public:
    enum class CaptureError {
        None,
        HistoryUnavailable,
        InvalidSession
    };

    using CapturedHistory =
        std::array<std::vector<fxfile::shellnav::HistoryLocations>,2>;

    struct Capture final {
        fxfile::uisession::Session session{};
        std::vector<CapturedHistory> histories{};
    };

    struct CaptureResult final {
        Capture value{};
        CaptureError error=CaptureError::InvalidSession;
        explicit operator bool() const noexcept {
            return error==CaptureError::None;
        }
    };

    struct RestorePayload final {
        fxfile::uisession::Session session{};
        std::vector<fxfile::previewtabs::WindowTabState> states{};
    };

    using UiTask=std::function<void()>;
    using Post=std::function<void(UiTask)>;
    using Completion=std::function<void(bool)>;
    using RestoreCompletion=
        std::function<void(std::shared_ptr<RestorePayload>)>;

    SessionCoordinator();

    bool autoRestoreAllowed() const noexcept;
    CaptureResult capture(
        fxfile::previewtabs::WindowWorkspaceController const& workspace,
        std::uint32_t width,std::uint32_t height) const noexcept;

    bool save(Capture&& capture,Post post,Completion completion);
    bool load(Post post,RestoreCompletion completion);
    bool clear(Post post,Completion completion);

    bool applyRestore(
        RestorePayload& payload,
        fxfile::previewtabs::WindowWorkspaceController& workspace);

    void prepareForClose() noexcept;

private:
    struct SharedState;
    std::shared_ptr<SharedState> state_;
};

} // namespace fxfile::sessioncoord
