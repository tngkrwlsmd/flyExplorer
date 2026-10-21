// F14: explicit per-folder view overrides. Pure in-memory value owner,
// not another source of PaneTab/session state and never writes user settings.
#pragma once
#include <algorithm>
#include <cstddef>
#include <cwctype>
#include <filesystem>
#include <string>
#include <vector>

namespace fxfile::previewfolderview {
class FolderViewController final {
public:
    static constexpr std::size_t kMaxOverrides=64;
    struct Entry final {
        std::wstring folder;
        int mode=0;
    };

    bool remember(std::wstring const& folder,int mode) {
        if(!validFolder(folder)||mode<0||mode>4)return false;
        auto it=std::find_if(items_.begin(),items_.end(),
            [&folder](Entry const& item){return same(item.folder,folder);});
        if(it!=items_.end())items_.erase(it);
        else if(items_.size()==kMaxOverrides)items_.pop_back();
        items_.insert(items_.begin(),{folder,mode});
        return true;
    }
    bool lookup(std::wstring const& folder,int& mode) const {
        if(!validFolder(folder))return false;
        const auto it=std::find_if(items_.begin(),items_.end(),
            [&folder](Entry const& item){return same(item.folder,folder);});
        if(it==items_.end())return false;
        mode=it->mode;
        return true;
    }
    bool forget(std::wstring const& folder) {
        if(!validFolder(folder))return false;
        const auto it=std::find_if(items_.begin(),items_.end(),
            [&folder](Entry const& item){return same(item.folder,folder);});
        if(it==items_.end())return false;
        items_.erase(it);
        return true;
    }
    void clear() noexcept {items_.clear();}
    std::size_t size() const noexcept {return items_.size();}

    static bool validFolder(std::wstring const& folder) {
        if(folder.size()<3||folder.size()>1024||
           folder.find(L'\0')!=std::wstring::npos||
           !((folder[0]>=L'A'&&folder[0]<=L'Z')||
             (folder[0]>=L'a'&&folder[0]<=L'z'))||
           folder[1]!=L':'||folder[2]!=L'\\')return false;
        try{
            const std::filesystem::path path(folder);
            const auto root=path.root_path().native();
            return root.size()==3&&root[1]==L':'&&root[2]==L'\\'&&
                   path.is_absolute()&&path.lexically_normal().native()==folder;
        }catch(...){return false;}
    }
private:
    static bool same(std::wstring const& left,std::wstring const& right) {
        if(left.size()!=right.size())return false;
        for(std::size_t i=0;i<left.size();++i)
            if(std::towlower(left[i])!=std::towlower(right[i]))return false;
        return true;
    }
    std::vector<Entry> items_{};
};
} // namespace fxfile::previewfolderview
