#include "shell_navigation_core.h"
#include <shlwapi.h>
#include <new>
#include <utility>
#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "shlwapi.lib")

namespace fxfile { namespace shellnav {
namespace {
struct FolderRef {
    IShellFolder* p=nullptr;
    FolderRef()=default;
    ~FolderRef() {if(p)p->Release();}
    FolderRef(FolderRef const&)=delete;
    FolderRef& operator=(FolderRef const&)=delete;
};
struct EnumRef {
    IEnumIDList* p=nullptr;
    ~EnumRef() {if(p)p->Release();}
};
std::wstring nameOf(PCIDLIST_ABSOLUTE id,SIGDN kind) {
    PWSTR raw=nullptr;
    const HRESULT hr=::SHGetNameFromIDList(id,kind,&raw);
    if(FAILED(hr)) {
        ::CoTaskMemFree(raw);
        return {};
    }
    std::wstring out=raw?raw:L"";
    ::CoTaskMemFree(raw);
    return out;
}
HRESULT bindFolder(PCIDLIST_ABSOLUTE id,IShellFolder** result) noexcept {
    if(!result)return E_POINTER;
    *result=nullptr;
    if(!id)return E_INVALIDARG;
    if(ILIsEmpty(id)) return ::SHGetDesktopFolder(result);
    return ::SHBindToObject(nullptr,id,nullptr,IID_IShellFolder,
                            reinterpret_cast<void**>(result));
}
} // namespace

Location::Location(PCIDLIST_ABSOLUTE id)
    :pidl_(id?::ILCloneFull(id):nullptr) {}
Location::~Location() noexcept {reset();}
Location::Location(Location const& other):Location(other.pidl_) {}
Location& Location::operator=(Location const& other) {
    if(this!=&other) {
        Location replacement(other);
        *this=std::move(replacement);
    }
    return *this;
}
Location::Location(Location&& other) noexcept:pidl_(other.pidl_) {
    other.pidl_=nullptr;
}
Location& Location::operator=(Location&& other) noexcept {
    if(this!=&other) {
        reset();
        pidl_=other.pidl_;
        other.pidl_=nullptr;
    }
    return *this;
}
void Location::reset(PIDLIST_ABSOLUTE owned) noexcept {
    ::CoTaskMemFree(pidl_);
    pidl_=owned;
}

HRESULT enumeratePage(PCIDLIST_ABSOLUTE folder,Snapshot& result,
                      DWORD flags,std::size_t offset,std::size_t limit,
                      std::atomic_bool const* cancel) noexcept {
    if(!folder || !limit)return E_INVALIDARG;
    try {
        if(cancel && cancel->load())return HRESULT_FROM_WIN32(ERROR_CANCELLED);
        FolderRef parent;
        HRESULT hr=bindFolder(folder,&parent.p);
        if(FAILED(hr))return hr;
        EnumRef iterator;
        hr=openEnumeration(parent.p,nullptr,flags,&iterator.p);
        if(FAILED(hr))return hr;

        for(std::size_t skipped=0;skipped<offset;++skipped){
            if(cancel && cancel->load())return HRESULT_FROM_WIN32(ERROR_CANCELLED);
            PIDLIST_RELATIVE raw=nullptr;
            ULONG fetched=0;
            hr=iterator.p->Next(1,&raw,&fetched);
            if(hr==S_FALSE){
                ::CoTaskMemFree(raw);
                break;
            }
            if(FAILED(hr)){
                ::CoTaskMemFree(raw);
                return hr;
            }
            if(fetched!=1||!raw){
                ::CoTaskMemFree(raw);
                return E_FAIL;
            }
            ::CoTaskMemFree(raw);
        }

        Snapshot fresh;
        fresh.folder=Location(folder);
        if(!fresh.folder.valid())return E_OUTOFMEMORY;
        fresh.parsingName=nameOf(folder,SIGDN_DESKTOPABSOLUTEPARSING);
        fresh.displayName=nameOf(folder,SIGDN_NORMALDISPLAY);
        while(iterator.p) {
            if(cancel && cancel->load())return HRESULT_FROM_WIN32(ERROR_CANCELLED);
            PIDLIST_RELATIVE raw=nullptr;
            ULONG fetched=0;
            hr=iterator.p->Next(1,&raw,&fetched);
            if(hr==S_FALSE)break;
            if(FAILED(hr)) {
                ::CoTaskMemFree(raw);
                return hr;
            }
            if(fetched!=1 || !raw) {
                ::CoTaskMemFree(raw);
                return E_FAIL;
            }
            PIDLIST_ABSOLUTE full=::ILCombine(folder,raw);
            SFGAOF attributes=SFGAO_FOLDER|SFGAO_FILESYSTEM|SFGAO_HIDDEN;
            PCUITEMID_CHILD child=raw;
            const HRESULT attrHr=parent.p->GetAttributesOf(1,&child,&attributes);
            if(FAILED(attrHr))attributes=0;
            ::CoTaskMemFree(raw);
            if(!full)return E_OUTOFMEMORY;
            Item item;
            item.id.reset(full);
            item.attributes=attributes;
            item.label=nameOf(item.id.get(),SIGDN_NORMALDISPLAY);
            item.parsingName=nameOf(item.id.get(),SIGDN_DESKTOPABSOLUTEPARSING);
            fresh.children.push_back(std::move(item));
            if(fresh.children.size()==limit) {
                fresh.truncated=true;
                break;
            }
        }
        fresh.baseOffset=offset;
        fresh.nextOffset=offset+fresh.children.size();
        result=std::move(fresh);
        return S_OK;
    } catch(std::bad_alloc const&) {
        return E_OUTOFMEMORY;
    } catch(...) {
        return E_FAIL;
    }
}

HRESULT enumerate(PCIDLIST_ABSOLUTE folder,Snapshot& result,
                  DWORD flags,size_t limit,
                  std::atomic_bool const* cancel) noexcept {
    return enumeratePage(folder,result,flags,0,limit,cancel);
}

bool Session::historyLocations(HistoryLocations& out) const noexcept {
    out={};
    try {
        if(back_.size()>16||forward_.size()>16)return false;
        auto clone=[](std::vector<Location> const& source,
                      std::vector<Location>& target)->bool {
            target.reserve(source.size());
            for(auto const& loc:source){
                if(!loc.valid())return false;
                target.emplace_back(loc);
                if(!target.back().valid())return false;
            }
            return true;
        };
        return clone(back_,out.back)&&clone(forward_,out.forward);
    }catch(...){out={};return false;}
}
bool historyPathsFromLocations(HistoryLocations const& source,
                               HistoryPaths& out) noexcept {
    out={};
    try {
        if(source.back.size()>16||source.forward.size()>16)return false;
        auto append=[](std::vector<Location> const& locations,
                       std::vector<std::wstring>& target)->bool {
            target.reserve(locations.size());
            for(auto const& loc:locations){
                if(!loc.valid())return false;
                PWSTR raw=nullptr;
                const HRESULT hr=::SHGetNameFromIDList(loc.get(),SIGDN_FILESYSPATH,&raw);
                // The private session persists fixed-local filesystem history
                // only. A supported local current folder may legitimately have
                // virtual Shell entries (for example This PC) in its Back stack;
                // omit those entries rather than failing the entire save.
                if(FAILED(hr)||!raw){::CoTaskMemFree(raw);continue;}
                std::wstring path(raw);::CoTaskMemFree(raw);
                if(path.empty())continue;
                target.push_back(std::move(path));
            }
            return true;
        };
        return append(source.back,out.back)&&append(source.forward,out.forward);
    }catch(...){out={};return false;}
}
bool Session::restoreHistoryPaths(HistoryPaths const& paths) noexcept {
    if(paths.back.size()>16||paths.forward.size()>16)return false;
    try {
        auto build=[](std::vector<std::wstring> const& source,
                      std::vector<Location>& target)->bool {
            for(auto const& path:source){
                if(path.empty())return false;
                PIDLIST_ABSOLUTE raw=::ILCreateFromPathW(path.c_str());
                if(!raw)return false;
                Location item;item.reset(raw);target.push_back(std::move(item));
            }
            return true;
        };
        std::vector<Location> back,forward;
        if(!build(paths.back,back)||!build(paths.forward,forward))return false;
        back_=std::move(back);forward_=std::move(forward);return true;
    }catch(...){return false;}
}

Location Session::target(HistoryAction action) const {
    if(action==HistoryAction::Back)
        return back_.empty()?Location():Location(back_.back());
    if(action==HistoryAction::Forward)
        return forward_.empty()?Location():Location(forward_.back());
    if(!current_.folder.valid())return {};
    Location chosen(current_.folder);
    if(action==HistoryAction::Up && chosen.valid()) {
        if(ILIsEmpty(chosen.get()) ||
           !::ILRemoveLastID(
               const_cast<PIDLIST_ABSOLUTE>(chosen.get())))
            return {};
    }
    return chosen;
}
HRESULT Session::accept(Snapshot&& prepared,HistoryAction action) noexcept {
    if(!prepared.folder.valid())return E_INVALIDARG;
    if(action==HistoryAction::Refresh) {
        if(!current_.folder.valid() ||
           !::ILIsEqual(current_.folder.get(),prepared.folder.get()))
            return E_INVALIDARG;
        current_=std::move(prepared);
        return S_OK;
    }
    if(action==HistoryAction::Back) {
        if(back_.empty() ||
           !::ILIsEqual(back_.back().get(),prepared.folder.get()))
            return E_INVALIDARG;
        try {
            Location previous(current_.folder);
            if(!previous.valid())return E_OUTOFMEMORY;
            forward_.push_back(std::move(previous));
            current_=std::move(prepared);
            back_.pop_back();
            return S_OK;
        }catch(...) {return E_OUTOFMEMORY;}
    }
    if(action==HistoryAction::Forward) {
        if(forward_.empty() ||
           !::ILIsEqual(forward_.back().get(),prepared.folder.get()))
            return E_INVALIDARG;
        try {
            Location previous(current_.folder);
            if(!previous.valid())return E_OUTOFMEMORY;
            back_.push_back(std::move(previous));
            current_=std::move(prepared);
            forward_.pop_back();
            return S_OK;
        }catch(...) {return E_OUTOFMEMORY;}
    }
    if(current_.folder.valid() &&
       ::ILIsEqual(current_.folder.get(),prepared.folder.get()))
        return S_FALSE;
    try {
        if(current_.folder.valid()) {
            Location previous(current_.folder);
            if(!previous.valid())return E_OUTOFMEMORY;
            back_.push_back(std::move(previous));
        }
        current_=std::move(prepared);
        forward_.clear();
        return S_OK;
    }catch(...) {return E_OUTOFMEMORY;}
}

HRESULT Session::appendPage(
    Snapshot&& page,std::size_t expectedOffset) noexcept
{
    if(!current_.folder.valid()||!page.folder.valid()||
       !::ILIsEqual(current_.folder.get(),page.folder.get())||
       current_.nextOffset!=expectedOffset||
       page.baseOffset!=expectedOffset||
       page.nextOffset!=expectedOffset+page.children.size()||
       current_.parsingName!=page.parsingName)
        return HRESULT_FROM_WIN32(ERROR_INVALID_STATE);
    try{
        current_.children.reserve(
            current_.children.size()+page.children.size());
        for(auto& child:page.children)
            current_.children.push_back(std::move(child));
        current_.nextOffset=page.nextOffset;
        current_.truncated=page.truncated;
        return S_OK;
    }catch(std::bad_alloc const&){
        return E_OUTOFMEMORY;
    }catch(...){
        return E_FAIL;
    }
}

HRESULT Session::commit(Location next,bool record) noexcept {
    if(!next.valid())return E_INVALIDARG;
    if(current_.folder.valid() &&
       ::ILIsEqual(next.get(),current_.folder.get()))
        return S_FALSE;
    Snapshot fresh;
    const HRESULT hr=enumerate(next.get(),fresh);
    if(FAILED(hr))return hr;
    try {
        if(record && current_.folder.valid()) {
            back_.push_back(current_.folder);
            forward_.clear();
        }
        current_=std::move(fresh);
        return S_OK;
    } catch(...) {return E_OUTOFMEMORY;}
}
HRESULT Session::open(std::wstring const& parsingName) noexcept {
    if(parsingName.empty())return E_INVALIDARG;
    PIDLIST_ABSOLUTE raw=nullptr;
    const HRESULT hr=::SHParseDisplayName(parsingName.c_str(),nullptr,&raw,0,nullptr);
    if(FAILED(hr))return hr;
    Location incoming;
    incoming.reset(raw);
    return commit(std::move(incoming),true);
}
HRESULT Session::open(PCIDLIST_ABSOLUTE full) noexcept {
    if(!full)return E_INVALIDARG;
    try {
        Location next(full);
        if(!next.valid())return E_OUTOFMEMORY;
        return commit(std::move(next),true);
    }catch(...) {return E_OUTOFMEMORY;}
}
HRESULT Session::openDesktop() noexcept {
    PIDLIST_ABSOLUTE id=nullptr;
    const HRESULT hr=::SHGetKnownFolderIDList(FOLDERID_Desktop,0,nullptr,&id);
    if(FAILED(hr))return hr;
    Location next;next.reset(id);
    return commit(std::move(next),true);
}
HRESULT Session::refresh() noexcept {
    if(!current_.folder.valid())return E_UNEXPECTED;
    Snapshot fresh;
    const HRESULT hr=enumerate(current_.folder.get(),fresh);
    if(SUCCEEDED(hr))current_=std::move(fresh);
    return hr;
}
HRESULT Session::back() noexcept {
    if(back_.empty())return S_FALSE;
    Snapshot fresh;
    const HRESULT hr=enumerate(back_.back().get(),fresh);
    if(FAILED(hr))return hr;
    try {
        forward_.push_back(current_.folder);
        current_=std::move(fresh);
        back_.pop_back();
        return S_OK;
    }catch(...) {return E_OUTOFMEMORY;}
}
HRESULT Session::forward() noexcept {
    if(forward_.empty())return S_FALSE;
    Snapshot fresh;
    const HRESULT hr=enumerate(forward_.back().get(),fresh);
    if(FAILED(hr))return hr;
    try {
        back_.push_back(current_.folder);
        current_=std::move(fresh);
        forward_.pop_back();
        return S_OK;
    }catch(...) {return E_OUTOFMEMORY;}
}
HRESULT Session::up() noexcept {
    if(!current_.folder.valid() || ILIsEmpty(current_.folder.get()))
        return S_FALSE;
    Location parent(current_.folder);
    // The desktop is the Shell namespace root. RemoveLastID on a
    // cloned PIDL, never an item borrowed from an old snapshot.
    if(!parent.valid())return E_OUTOFMEMORY;
    if(!::ILRemoveLastID(const_cast<PIDLIST_ABSOLUTE>(parent.get())))
        return S_FALSE;
    return commit(std::move(parent),true);
}
} } // namespace fxfile::shellnav
