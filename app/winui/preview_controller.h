#pragma once
// F03 opt-in text-only pane bridge. UI events and presentation stay in MainWindow.
// File metadata, child IPC and cancellation occur strictly off the XAML thread.
#include "../../src/base/file_preview_request_gate.h"
#include "../../src/base/file_preview_supervisor.h"
#include <atomic>
#include <functional>
#include <memory>
#include <string>

namespace fxfile::previewctrl {
class PreviewController final {
public:
    struct Request final {
        int side=-1;
        previewgate::Key key{};
        std::wstring filePath;
        std::wstring siblingHelper;
    };
    struct Completion final {
        int side=-1;
        previewgate::Ticket ticket{};
        previewsupervisor::Result result{};
    };
    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using Done=std::function<void(Completion)>;

    PreviewController()=default;
    ~PreviewController(){prepareForClose();}
    PreviewController(PreviewController const&)=delete;
    PreviewController& operator=(PreviewController const&)=delete;
    bool start(Request request,Post post,Done done);
    bool accepts(previewgate::Ticket const& ticket) const noexcept {
        return gate_.current(ticket)&&!closing_.load();
    }
    void cancel() noexcept {gate_.clear();}
    void prepareForClose() noexcept {closing_.store(true);cancel();}
private:
    previewgate::Gate gate_{};
    std::atomic_bool closing_{false};
    std::shared_ptr<std::atomic_uint> inFlight_=
        std::make_shared<std::atomic_uint>(0);
};
} // namespace fxfile::previewctrl
