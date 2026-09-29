#include "shell_async_worker.h"
// Legacy native test include path contains a historical local stdint.h
// missing INTMAX_MAX. Supply the exact Windows intmax_t limit BEFORE
// standard <thread>/<mutex> import, without changing global toolchains.
#include <climits>
#ifndef INTMAX_MAX
#define INTMAX_MAX LLONG_MAX
#endif
#include "directory_change_bridge.h"
#include <windows.h>
#include <shlobj.h>
#include <algorithm>
#include <atomic>
#include <deque>
#include <map>
#include <mutex>
#include <thread>
#include <utility>
#include <vector>
namespace fxfile { namespace shellnav {
namespace {
constexpr DWORD kMaximumWatchedFolders=2; // one selected tab per pane
struct Work final {
    std::uint64_t route=0,request=0;
    NavigationAction action=NavigationAction::Open;
    Location absolute;
    std::wstring parsingName;
    std::shared_ptr<std::atomic_bool> cancel;
};
struct DesiredWatch final {
    std::uint64_t token=0;
    std::wstring path;
};
struct LiveWatch final {
    std::uint64_t route=0,token=0;
    std::wstring path;
    HANDLE handle=INVALID_HANDLE_VALUE;
};
}
struct AsyncShellWorker::State final {
    std::mutex lock;
    std::deque<Work> queued;
    std::map<std::uint64_t,std::uint64_t> latest;
    std::map<std::uint64_t,std::shared_ptr<std::atomic_bool>> cancellations;
    std::map<std::uint64_t,DesiredWatch> watches;
    ResultCallback results;
    ChangeCallback changes;
    HANDLE wake=nullptr;
    std::uint64_t nextRequest=1;
    bool stop=false;
    bool started=false;
    State(ResultCallback r,ChangeCallback c):
        results(std::move(r)),changes(std::move(c)) {
        wake=::CreateEventW(nullptr,FALSE,FALSE,nullptr);
    }
    ~State() {
        if(wake)::CloseHandle(wake);
    }
};

AsyncShellWorker::AsyncShellWorker(ResultCallback result,ChangeCallback changed)
    :state_(std::make_shared<State>(std::move(result),std::move(changed))) {}
AsyncShellWorker::~AsyncShellWorker() {shutdown();}
bool AsyncShellWorker::start() {
    const auto st=state_;
    if(!st || !st->wake)return false;
    {
        std::lock_guard<std::mutex> guard(st->lock);
        if(st->stop)return false;
        if(st->started)return true;
        st->started=true;
    }
    try {
        // Detached ONLY because a Shell extension can hang in COM and
        // must not block the WinUI STA while its window is closing.
        std::thread([st]{run(st);}).detach();
        return true;
    }catch(...) {
        std::lock_guard<std::mutex> guard(st->lock);
        st->started=false;
        return false;
    }
}
std::uint64_t AsyncShellWorker::submit(std::uint64_t route,
                                      Location target,
                                      NavigationAction action) {
    if(!target.valid() || !route)return 0;
    const auto st=state_;
    if(!st)return 0;
    std::uint64_t ticket=0;
    try {
        std::lock_guard<std::mutex> guard(st->lock);
        if(st->stop || !st->started)return 0;
        const auto existing=st->cancellations.find(route);
        if(existing!=st->cancellations.end())
            existing->second->store(true);
        Work work;
        work.route=route;
        work.request=ticket=st->nextRequest++;
        work.absolute=std::move(target);
        work.action=action;
        work.cancel=std::make_shared<std::atomic_bool>(false);
        st->latest[route]=ticket;
        st->cancellations[route]=work.cancel;
        for(auto it=st->queued.begin();it!=st->queued.end();) {
            if(it->route==route)it=st->queued.erase(it);
            else ++it;
        }
        st->queued.push_back(std::move(work));
    }catch(...) {return 0;}
    ::SetEvent(st->wake);
    return ticket;
}
std::uint64_t AsyncShellWorker::submitParsing(std::uint64_t route,
                                              std::wstring path) {
    if(path.empty() || !route)return 0;
    const auto st=state_;
    if(!st)return 0;
    std::uint64_t ticket=0;
    try {
        std::lock_guard<std::mutex> guard(st->lock);
        if(st->stop || !st->started)return 0;
        const auto existing=st->cancellations.find(route);
        if(existing!=st->cancellations.end())
            existing->second->store(true);
        Work work;
        work.route=route;
        work.request=ticket=st->nextRequest++;
        work.parsingName=std::move(path);
        work.cancel=std::make_shared<std::atomic_bool>(false);
        st->latest[route]=ticket;
        st->cancellations[route]=work.cancel;
        for(auto it=st->queued.begin();it!=st->queued.end();) {
            if(it->route==route)it=st->queued.erase(it);
            else ++it;
        }
        st->queued.push_back(std::move(work));
    }catch(...) {return 0;}
    ::SetEvent(st->wake);
    return ticket;
}
void AsyncShellWorker::watch(std::uint64_t route,std::uint64_t token,
                              std::wstring path) {
    if(!route)return;
    const auto st=state_;
    if(!st)return;
    try {
        std::lock_guard<std::mutex> guard(st->lock);
        if(st->stop)return;
        if(path.empty())st->watches.erase(route);
        else st->watches[route]={token,std::move(path)};
    }catch(...) {return;}
    ::SetEvent(st->wake);
}
void AsyncShellWorker::unwatch(std::uint64_t route) {
    watch(route,0,{});
}
void AsyncShellWorker::forget(std::uint64_t route) {
    const auto st=state_;
    if(!st)return;
    {
        std::lock_guard<std::mutex> guard(st->lock);
        const auto existing=st->cancellations.find(route);
        if(existing!=st->cancellations.end()) {
            existing->second->store(true);
            st->cancellations.erase(existing);
        }
        st->latest.erase(route);
        st->watches.erase(route);
        for(auto it=st->queued.begin();it!=st->queued.end();) {
            if(it->route==route)it=st->queued.erase(it);
            else ++it;
        }
    }
    ::SetEvent(st->wake);
}
void AsyncShellWorker::shutdown() noexcept {
    auto st=std::move(state_);
    if(!st)return;
    {
        std::lock_guard<std::mutex> guard(st->lock);
        st->stop=true;
        for(auto& x:st->cancellations)x.second->store(true);
        st->latest.clear();
        st->watches.clear();
        st->queued.clear();
        st->results={};
        st->changes={};
    }
    if(st->wake)::SetEvent(st->wake);
}

void AsyncShellWorker::run(std::shared_ptr<State> st) noexcept {
    // COM objects are CREATED, USED and RELEASED only on this STA.
    const HRESULT initialized=::CoInitializeEx(nullptr,
                           COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
    std::vector<LiveWatch> active;
    auto closeAll=[&] {
        for(auto& w:active)directorychange::close(w.handle);
        active.clear();
    };
    for(;;) {
        Work job;
        bool hasJob=false;
        std::map<std::uint64_t,DesiredWatch> desired;
        {
            std::lock_guard<std::mutex> guard(st->lock);
            if(st->stop)break;
            desired=st->watches;
            if(!st->queued.empty()) {
                job=std::move(st->queued.front());
                st->queued.pop_front();
                hasJob=true;
            }
        }
        // Watch handles are opened and closed ONLY by the owning STA.
        for(auto it=active.begin();it!=active.end();) {
            auto d=desired.find(it->route);
            if(d==desired.end() || d->second.token!=it->token ||
               d->second.path!=it->path) {
                directorychange::close(it->handle);
                it=active.erase(it);
            }else ++it;
        }
        for(auto const& d:desired) {
            if(active.size()>=kMaximumWatchedFolders)break;
            if(std::any_of(active.begin(),active.end(),[&](auto const& x){
                return x.route==d.first;
            }))continue;
            HANDLE h=directorychange::open(
                d.second.path.c_str(),false,directorychange::kFilesAndFolders);
            if(h!=INVALID_HANDLE_VALUE)
                active.push_back({d.first,d.second.token,d.second.path,h});
        }
        if(hasJob) {
            AsyncResult answer;
            answer.route=job.route;
            answer.request=job.request;
            answer.action=job.action;
            answer.hr=initialized;
            if(SUCCEEDED(initialized) && !job.cancel->load()) {
                if(!job.absolute.valid()) {
                    PIDLIST_ABSOLUTE id=nullptr;
                    answer.hr=::SHParseDisplayName(
                        job.parsingName.c_str(),nullptr,&id,0,nullptr);
                    if(SUCCEEDED(answer.hr))job.absolute.reset(id);
                }
                if(job.absolute.valid()) {
                    answer.hr=enumerate(job.absolute.get(),answer.snapshot,
                      SHCONTF_FOLDERS|SHCONTF_NONFOLDERS,1200,
                      job.cancel.get());
                }
            }
            // Never deliver obsolete, shutdown, or canceled requests.
            ResultCallback receiver;
            {
                std::lock_guard<std::mutex> guard(st->lock);
                const auto current=st->latest.find(job.route);
                if(!st->stop && current!=st->latest.end() &&
                   current->second==job.request && !job.cancel->load()) {
                    receiver=st->results;
                    st->cancellations.erase(job.route);
                }
            }
            if(receiver) {
                try {receiver(std::move(answer));}catch(...) {}
            }
            continue;
        }
        HANDLE waits[1+kMaximumWatchedFolders]={st->wake,nullptr,nullptr};
        for(size_t i=0;i<active.size();++i)waits[1+i]=active[i].handle;
        // A worker STA MUST pump its own messages to avoid COM reentrancy
        // starvation, but NEVER executes any application UI work.
        const DWORD count=static_cast<DWORD>(active.size()+1);
        const DWORD event=::MsgWaitForMultipleObjectsEx(
            count,waits,INFINITE,QS_ALLINPUT,MWMO_INPUTAVAILABLE);
        if(event==WAIT_OBJECT_0)continue;
        if(event==WAIT_OBJECT_0+count) {
            MSG message={};
            while(::PeekMessageW(&message,nullptr,0,0,PM_REMOVE)) {
                ::TranslateMessage(&message);
                ::DispatchMessageW(&message);
            }
            continue;
        }
        if(event>=WAIT_OBJECT_0+1 &&
           event<WAIT_OBJECT_0+count) {
            const size_t which=static_cast<size_t>(event-WAIT_OBJECT_0-1);
            const LiveWatch matched=active[which];
            if(!directorychange::rearm(active[which].handle)) {
                directorychange::close(active[which].handle);
                active.erase(active.begin()+which);
            }
            ChangeCallback change;
            {
                std::lock_guard<std::mutex> guard(st->lock);
                const auto want=st->watches.find(matched.route);
                if(!st->stop && want!=st->watches.end() &&
                   want->second.token==matched.token &&
                   want->second.path==matched.path)
                    change=st->changes;
            }
            if(change) {
                try {change(matched.route,matched.token);}catch(...) {}
            }
        }
    }
    closeAll();
    if(SUCCEEDED(initialized))::CoUninitialize();
}
} } // namespace fxfile::shellnav
