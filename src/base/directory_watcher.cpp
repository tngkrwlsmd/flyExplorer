#include "directory_watcher.h"
#include "directory_change_bridge.h"
#include <windows.h>
#include <algorithm>
#include <map>
#include <mutex>
#include <thread>
#include <vector>
#include <utility>
namespace fxfile { namespace directorychange {
namespace {
constexpr size_t kMaxWatches=2;
struct Desired {std::uint64_t token=0;std::wstring path;};
struct Active {
    std::uint64_t route,token;std::wstring path;HANDLE handle;
};
}
struct DirectoryWatcher::State {
    std::mutex mutex;
    std::map<std::uint64_t,Desired> desired;
    Callback change;
    HANDLE wake=::CreateEventW(nullptr,FALSE,FALSE,nullptr);
    bool stopping=false,started=false;
    explicit State(Callback cb):change(std::move(cb)) {}
    ~State(){if(wake)::CloseHandle(wake);}
};
DirectoryWatcher::DirectoryWatcher(Callback cb):
    state_(std::make_shared<State>(std::move(cb))) {}
DirectoryWatcher::~DirectoryWatcher(){shutdown();}
bool DirectoryWatcher::start(){
    auto st=state_;
    if(!st||!st->wake)return false;
    {
        std::lock_guard<std::mutex> guard(st->mutex);
        if(st->stopping)return false;
        if(st->started)return true;
        st->started=true;
    }
    try{std::thread([st]{run(st);}).detach();return true;}
    catch(...){
        std::lock_guard<std::mutex> guard(st->mutex);
        st->started=false;
        return false;
    }
}
void DirectoryWatcher::watch(std::uint64_t route,std::uint64_t token,
                            std::wstring path){
    if(!route)return;
    auto st=state_;
    if(!st)return;
    try{
        std::lock_guard<std::mutex> guard(st->mutex);
        if(st->stopping)return;
        if(path.empty())st->desired.erase(route);
        else st->desired[route]={token,std::move(path)};
    }catch(...){return;}
    ::SetEvent(st->wake);
}
void DirectoryWatcher::unwatch(std::uint64_t route){watch(route,0,{});}
void DirectoryWatcher::shutdown() noexcept{
    auto st=std::move(state_);
    if(!st)return;
    {
        std::lock_guard<std::mutex> guard(st->mutex);
        st->stopping=true;
        st->change={};
        st->desired.clear();
    }
    if(st->wake)::SetEvent(st->wake);
}
void DirectoryWatcher::run(std::shared_ptr<State> st) noexcept{
    std::vector<Active> active;
    for(;;){
        std::map<std::uint64_t,Desired> desired;
        {
            std::lock_guard<std::mutex> guard(st->mutex);
            if(st->stopping)break;
            desired=st->desired;
        }
        for(auto it=active.begin();it!=active.end();){
            auto entry=desired.find(it->route);
            if(entry==desired.end()||entry->second.token!=it->token||
               entry->second.path!=it->path){
                close(it->handle);it=active.erase(it);
            }else ++it;
        }
        for(auto const& entry:desired){
            if(active.size()>=kMaxWatches)break;
            if(std::any_of(active.begin(),active.end(),[&](Active const& a){
                return a.route==entry.first;
            }))continue;
            HANDLE handle=open(entry.second.path.c_str(),false,kFilesAndFolders);
            if(handle!=INVALID_HANDLE_VALUE)
                active.push_back({entry.first,entry.second.token,
                                  entry.second.path,handle});
        }
        HANDLE handles[1+kMaxWatches]={st->wake,nullptr,nullptr};
        for(size_t i=0;i<active.size();++i)handles[i+1]=active[i].handle;
        const auto count=static_cast<DWORD>(active.size()+1);
        const DWORD event=::WaitForMultipleObjects(
            count,handles,FALSE,INFINITE);
        if(event==WAIT_OBJECT_0)continue;
        if(event>=WAIT_OBJECT_0+1&&event<WAIT_OBJECT_0+count){
            size_t index=event-WAIT_OBJECT_0-1;
            auto matched=active[index];
            if(!rearm(active[index].handle)){
                close(active[index].handle);
                active.erase(active.begin()+index);
            }
            Callback cb;
            {
                std::lock_guard<std::mutex> guard(st->mutex);
                auto live=st->desired.find(matched.route);
                if(!st->stopping&&live!=st->desired.end()&&
                   live->second.token==matched.token&&
                   live->second.path==matched.path)cb=st->change;
            }
            if(cb){try{cb(matched.route,matched.token);}catch(...){}}
        }else{
            // Broken watched handle: close and recreate only from next
            // desired refresh; never spin on WAIT_FAILED.
            for(auto& item:active)close(item.handle);
            active.clear();
            ::WaitForSingleObject(st->wake,500);
        }
    }
    for(auto& item:active)close(item.handle);
}
} }
