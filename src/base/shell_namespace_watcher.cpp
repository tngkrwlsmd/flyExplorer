#include "shell_namespace_watcher.h"
#include "shell_isolation_wire.h"
#include <windows.h>
#include <shlobj.h>
#include <array>
#include <map>
#include <mutex>
#include <thread>
#include <vector>
#include <functional>
#include <cstring>
#include <algorithm>
#include <utility>
namespace fxfile { namespace directorychange {
namespace {
constexpr UINT kNotifyBase=WM_APP+0x270;
constexpr wchar_t kWindowClass[]=L"flyExplorerPrivateNamespaceChangeWatcher";
struct Spec {std::uint64_t token=0;std::vector<unsigned char> pidl;};
struct Active {
    std::uint64_t route=0,token=0;
    std::vector<unsigned char> pidl;
    ULONG registration=0;
};
struct Runtime {
    std::function<void(size_t)> delivered;
};
LRESULT CALLBACK WindowProc(HWND window,UINT message,WPARAM w,LPARAM l) {
    if(message>=kNotifyBase&&message<kNotifyBase+2) {
        PIDLIST_ABSOLUTE* list=nullptr;
        LONG event=0;
        const auto handle=::SHChangeNotification_Lock(
            reinterpret_cast<HANDLE>(w),static_cast<DWORD>(l),&list,&event);
        if(handle) {
            ::SHChangeNotification_Unlock(handle);
            auto* runtime=reinterpret_cast<Runtime*>(
                ::GetWindowLongPtrW(window,GWLP_USERDATA));
            if(runtime && runtime->delivered)
                runtime->delivered(message-kNotifyBase);
        }
        return 0;
    }
    return ::DefWindowProcW(window,message,w,l);
}
}
struct ShellNamespaceWatcher::State {
    std::mutex mutex;
    std::map<std::uint64_t,Spec> desired;
    Callback callback;
    HANDLE wake=::CreateEventW(nullptr,FALSE,FALSE,nullptr);
    bool stopping=false,started=false;
    explicit State(Callback cb):callback(std::move(cb)){}
    ~State(){if(wake)::CloseHandle(wake);}
};
ShellNamespaceWatcher::ShellNamespaceWatcher(Callback cb):
    state_(std::make_shared<State>(std::move(cb))){}
ShellNamespaceWatcher::~ShellNamespaceWatcher(){shutdown();}
bool ShellNamespaceWatcher::start(){
    auto st=state_;
    if(!st||!st->wake)return false;
    {
        std::lock_guard<std::mutex> lock(st->mutex);
        if(st->stopping)return false;
        if(st->started)return true;
        st->started=true;
    }
    try{std::thread([st]{run(st);}).detach();return true;}
    catch(...){
        std::lock_guard<std::mutex> lock(st->mutex);
        st->started=false;
        return false;
    }
}
void ShellNamespaceWatcher::watch(
    std::uint64_t route,std::uint64_t token,PCIDLIST_ABSOLUTE folder){
    if(!route||!folder)return;
    const auto size=::ILGetSize(folder);
    if(!fxfile::isolation::validPidl(folder,size))return;
    auto st=state_;
    if(!st)return;
    try {
        std::vector<unsigned char> bytes(size);
        std::memcpy(bytes.data(),folder,size);
        {
            std::lock_guard<std::mutex> lock(st->mutex);
            if(st->stopping)return;
            st->desired[route]={token,std::move(bytes)};
        }
        ::SetEvent(st->wake);
    }catch(...){}
}
void ShellNamespaceWatcher::unwatch(std::uint64_t route){
    auto st=state_;
    if(!st)return;
    {
        std::lock_guard<std::mutex> lock(st->mutex);
        st->desired.erase(route);
    }
    ::SetEvent(st->wake);
}
void ShellNamespaceWatcher::shutdown() noexcept{
    auto st=std::move(state_);
    if(!st)return;
    {
        std::lock_guard<std::mutex> lock(st->mutex);
        st->stopping=true;
        st->desired.clear();
        st->callback={};
    }
    if(st->wake)::SetEvent(st->wake);
}
void ShellNamespaceWatcher::run(std::shared_ptr<State> st) noexcept{
    WNDCLASSW klass{};
    klass.lpfnWndProc=WindowProc;
    klass.hInstance=::GetModuleHandleW(nullptr);
    klass.lpszClassName=kWindowClass;
    if(!::RegisterClassW(&klass)&&::GetLastError()!=ERROR_CLASS_ALREADY_EXISTS)
        return;
    HWND window=::CreateWindowExW(0,kWindowClass,L"",0,0,0,0,0,
                                 HWND_MESSAGE,nullptr,klass.hInstance,nullptr);
    if(!window)return;
    std::array<Active,2> active{};
    Runtime runtime;
    runtime.delivered=[&](size_t slot){
        if(slot>=active.size()||!active[slot].registration)return;
        const auto route=active[slot].route;
        const auto token=active[slot].token;
        Callback cb;
        {
            std::lock_guard<std::mutex> guard(st->mutex);
            const auto found=st->desired.find(route);
            if(!st->stopping&&found!=st->desired.end()&&
               found->second.token==token&&
               found->second.pidl==active[slot].pidl)
                cb=st->callback;
        }
        if(cb){try{cb(route,token);}catch(...){}}
    };
    ::SetWindowLongPtrW(window,GWLP_USERDATA,
                        reinterpret_cast<LONG_PTR>(&runtime));
    for(;;){
        std::map<std::uint64_t,Spec> desired;
        {
            std::lock_guard<std::mutex> guard(st->mutex);
            if(st->stopping)break;
            desired=st->desired;
        }
        for(auto& current:active){
            if(!current.registration)continue;
            auto found=desired.find(current.route);
            if(found==desired.end()||found->second.token!=current.token||
               found->second.pidl!=current.pidl){
                ::SHChangeNotifyDeregister(current.registration);
                current=Active{};
            }
        }
        for(auto const& item:desired){
            const bool exists=std::any_of(active.begin(),active.end(),
                [&](Active const& a){return a.registration&&a.route==item.first;});
            if(exists)continue;
            auto slot=std::find_if(active.begin(),active.end(),
                [](Active const& a){return a.registration==0;});
            if(slot==active.end())break;
            const size_t index=static_cast<size_t>(slot-active.begin());
            SHChangeNotifyEntry entry{};
            entry.pidl=reinterpret_cast<PCIDLIST_ABSOLUTE>(
                item.second.pidl.data());
            entry.fRecursive=TRUE;
            const auto id=::SHChangeNotifyRegister(window,
                SHCNRF_ShellLevel|SHCNRF_InterruptLevel|SHCNRF_NewDelivery,
                SHCNE_UPDATEDIR|SHCNE_UPDATEITEM|SHCNE_CREATE|
                SHCNE_DELETE|SHCNE_RENAMEFOLDER|SHCNE_DRIVEADD|
                SHCNE_DRIVEREMOVED|SHCNE_MEDIAINSERTED|SHCNE_MEDIAREMOVED,
                kNotifyBase+static_cast<UINT>(index),1,&entry);
            if(id)
                *slot={item.first,item.second.token,item.second.pidl,id};
        }
        const DWORD wait=::MsgWaitForMultipleObjectsEx(
            1,&st->wake,INFINITE,QS_ALLINPUT,MWMO_INPUTAVAILABLE);
        if(wait==WAIT_OBJECT_0)continue;
        if(wait==WAIT_OBJECT_0+1){
            MSG msg{};
            while(::PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){
                ::TranslateMessage(&msg);
                ::DispatchMessageW(&msg);
            }
        }else ::WaitForSingleObject(st->wake,200);
    }
    ::SetWindowLongPtrW(window,GWLP_USERDATA,0);
    for(auto& entry:active)
        if(entry.registration)::SHChangeNotifyDeregister(entry.registration);
    ::DestroyWindow(window);
}
} }
