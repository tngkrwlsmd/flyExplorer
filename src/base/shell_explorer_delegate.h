// Native Windows Explorer handoff: use the OS's own commands/archivers
// instead of extending the app's experimental F08 ZIP implementation.
// Opens an Explorer window with explicitly selected sibling items.
// No archive parser, mutation, persistent setting or child process command.
#pragma once
#include <windows.h>
#include <shlobj.h>
#include <objbase.h>
#include <algorithm>
#include <filesystem>
#include <string>
#include <vector>
namespace fxfile::shellexplorer {
inline constexpr std::size_t kMaxSelected=128;
inline constexpr std::size_t kMaxPathUnits=16u*1024u;
namespace detail {
struct Apartment final {
    bool initialized=false;
    ~Apartment() noexcept {if(initialized)::CoUninitialize();}
};
struct Pidls final {
    PIDLIST_ABSOLUTE folder=nullptr;
    std::vector<PIDLIST_ABSOLUTE> items{};
    ~Pidls() noexcept {
        for(auto p:items)if(p)::CoTaskMemFree(p);
        if(folder)::CoTaskMemFree(folder);
    }
};
inline bool equal(std::wstring const& a,std::wstring const& b) noexcept {
    return ::CompareStringOrdinal(a.c_str(),-1,b.c_str(),-1,TRUE)==CSTR_EQUAL;
}
}
// Only filesystem siblings can be represented by child PIDLs of one parent.
// Validation is read-only; Explorer owns the actual operation, conflicts,
// progress, archive compatibility and OS version-specific UI.
inline HRESULT reveal(std::vector<std::wstring> const& paths) noexcept {
    if(paths.empty()||paths.size()>kMaxSelected)return E_INVALIDARG;
    try {
        std::wstring parent;
        std::size_t units=0;
        for(auto const& path:paths){
            if(path.size()<4||path.size()>1024||
               path.size()>kMaxPathUnits-units||
               path.find(L'\0')!=std::wstring::npos)return E_INVALIDARG;
            const auto p=std::filesystem::path(path);
            if(!p.is_absolute()||p.lexically_normal().native()!=path||
               p.filename().empty())return E_INVALIDARG;
            const auto owner=p.parent_path().native();
            if(owner.empty()||(!parent.empty()&&!detail::equal(owner,parent)))
                return E_INVALIDARG;
            for(auto const& previous:paths){
                if(&previous==&path)break;
                if(detail::equal(previous,path))return E_INVALIDARG;
            }
            if(parent.empty())parent=owner;
            units+=path.size();
        }
        const HRESULT apartment=::CoInitializeEx(
            nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
        if(FAILED(apartment))return apartment;
        detail::Apartment lifetime{true};
        detail::Pidls pidls;
        HRESULT result=::SHParseDisplayName(
            parent.c_str(),nullptr,&pidls.folder,0,nullptr);
        if(FAILED(result)||!pidls.folder)return FAILED(result)?result:E_FAIL;
        pidls.items.reserve(paths.size());
        std::vector<PCUITEMID_CHILD> children;
        children.reserve(paths.size());
        for(auto const& path:paths){
            PIDLIST_ABSOLUTE absolute=nullptr;
            result=::SHParseDisplayName(
                path.c_str(),nullptr,&absolute,0,nullptr);
            if(FAILED(result)||!absolute){
                if(absolute)::CoTaskMemFree(absolute);
                return FAILED(result)?result:E_FAIL;
            }
            pidls.items.push_back(absolute);
            // The absolute item is owned until SHOpenFolderAndSelectItems
            // returns, so its final child ID stays alive throughout.
            children.push_back(::ILFindLastID(absolute));
        }
        return ::SHOpenFolderAndSelectItems(
            pidls.folder,static_cast<UINT>(children.size()),
            children.data(),0);
    }catch(...){return E_FAIL;}
}
} // namespace fxfile::shellexplorer
