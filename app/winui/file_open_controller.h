#pragma once
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.Storage.h>
#include <winrt/Windows.System.h>
#include <winrt/Microsoft.UI.Dispatching.h>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <utility>

namespace fxfile::previewops {
// UI-apartment owner for one explicit file activation. Windows brokers the
// asynchronous lookup/launch; no Shell extension runs synchronously in XAML.
class FileOpenController final {
public:
    enum class Result { Opened, NoAssociation, AppUnavailable, Failed, TimedOut };
    enum class Start { Started, Busy, Invalid };
    FileOpenController() : state_(std::make_shared<State>()) {}
    ~FileOpenController() { prepareForClose(); }
    FileOpenController(FileOpenController const&)=delete;
    FileOpenController& operator=(FileOpenController const&)=delete;

    Start request(std::wstring path,
                  winrt::Microsoft::UI::Dispatching::DispatcherQueue const& queue,
                  std::function<bool()> current,
                  std::function<void(Result)> completed) {
        auto s=state_;
        if(s->closing||path.empty()||path.size()>32767||
           path.find(L'\0')!=std::wstring::npos||
           !std::filesystem::path(path).is_absolute())return Start::Invalid;
        if(s->busy)return Start::Busy;
        s->busy=true;
        const auto ticket=++s->ticket;
        s->current=std::move(current);
        s->completed=std::move(completed);
        try {
            s->timer=queue.CreateTimer();
            s->timer.IsRepeating(false);
            s->timer.Interval(std::chrono::seconds(15));
            s->timer.Tick([weak=std::weak_ptr<State>(s),ticket](auto const&,auto const&) {
                if(auto live=weak.lock())finish(live,ticket,Result::TimedOut);
            });
            s->timer.Start();
            run(s,ticket,winrt::hstring(path));
        } catch(...) { finish(s,ticket,Result::Failed); }
        return Start::Started;
    }

    void prepareForClose() noexcept {
        auto s=state_;
        s->closing=true;
        ++s->ticket;
        s->busy=false;
        s->current={};
        s->completed={};
        try { if(s->timer)s->timer.Stop(); } catch(...) {}
        try { if(s->pending)s->pending.Cancel(); } catch(...) {}
        s->pending=nullptr;
    }

private:
    struct State {
        bool closing=false,busy=false;
        std::uint64_t ticket=0;
        winrt::Windows::Foundation::IAsyncInfo pending{nullptr};
        winrt::Microsoft::UI::Dispatching::DispatcherQueueTimer timer{nullptr};
        std::function<bool()> current;
        std::function<void(Result)> completed;
    };
    std::shared_ptr<State> state_;

    static bool live(std::shared_ptr<State> const& s,std::uint64_t ticket) {
        return !s->closing&&s->busy&&s->ticket==ticket&&s->current&&s->current();
    }
    static void finish(std::shared_ptr<State> const& s,std::uint64_t ticket,
                       Result result) noexcept {
        if(s->ticket!=ticket||!s->busy)return;
        try {
            const bool notify=live(s,ticket);
            s->busy=false;
            ++s->ticket;
            if(s->timer)s->timer.Stop();
            auto pending=std::exchange(s->pending,nullptr);
            auto completed=std::move(s->completed);
            s->current={};
            try { if(pending&&result==Result::TimedOut)pending.Cancel(); } catch(...) {}
            if(notify&&completed)completed(result);
        } catch(...) {}
    }
    static winrt::fire_and_forget run(std::shared_ptr<State> s,
                                     std::uint64_t ticket,winrt::hstring path) {
        try {
            auto lookup=winrt::Windows::Storage::StorageFile::GetFileFromPathAsync(path);
            s->pending=lookup;
            auto file=co_await lookup;
            // A tab switch/close during resolution must not open a stale file.
            if(!live(s,ticket)) {
                finish(s,ticket,Result::Failed);
                co_return;
            }
            // Query only the Windows association broker; no Shell extension
            // or external command is run while resolving the handler.
            // Unknown/query failures keep the existing default launch path.
            try {
                auto query=winrt::Windows::System::Launcher::QueryFileSupportAsync(file);
                s->pending=query;
                const auto support=co_await query;
                if(!live(s,ticket)){
                    finish(s,ticket,Result::Failed);
                    co_return;
                }
                using Support=winrt::Windows::System::LaunchQuerySupportStatus;
                if(support==Support::AppNotInstalled||
                   support==Support::NotSupported){
                    finish(s,ticket,Result::NoAssociation);
                    co_return;
                }
                if(support==Support::AppUnavailable){
                    finish(s,ticket,Result::AppUnavailable);
                    co_return;
                }
            }catch(...){
                if(!live(s,ticket)){
                    finish(s,ticket,Result::Failed);
                    co_return;
                }
                // On transient association-query errors let LaunchFileAsync
                // return its original reliable success/failure result.
            }
            if(!live(s,ticket)){
                finish(s,ticket,Result::Failed);
                co_return;
            }
            auto launch=winrt::Windows::System::Launcher::LaunchFileAsync(file);
            s->pending=launch;
            const bool opened=co_await launch;
            finish(s,ticket,opened?Result::Opened:Result::Failed);
        } catch(...) { finish(s,ticket,Result::Failed); }
    }
};
}
