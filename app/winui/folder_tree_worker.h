#pragma once
#include "folder_tree_path.h"
#include <windows.h>
#include <atomic>
#include <string>
#include <vector>

namespace fxfile::foldertree {

struct ChildListing final {
    bool complete=false;
    bool limited=false;
    std::vector<std::wstring> names;
};

// Runs ONLY on an opt-in background thread. Do not call from XAML/UI.
// No Shell providers, UNC, removable roots, junction traversal or writes.
// A drive/path substitution race cannot be made atomic using Win32 paths;
// this intentionally read-only feature does not claim adversarial durability.
inline ChildListing enumerateFixedChildren(
    std::wstring const& parent,std::atomic_bool const& cancel) noexcept {
    ChildListing out;
    if(cancel.load()||!normalizedDrivePath(parent))return out;
    wchar_t root[]{L"C:\\"};
    root[0]=asciiUpper(parent[0]);
    if(::GetDriveTypeW(root)!=DRIVE_FIXED)return out;
    // Reject reparse components before asking Windows to enumerate children.
    std::wstring prefix(root);
    auto check=[](std::wstring const& path){
        const DWORD attributes=::GetFileAttributesW(path.c_str());
        return attributes!=INVALID_FILE_ATTRIBUTES &&
            (attributes&FILE_ATTRIBUTE_DIRECTORY)!=0 &&
            (attributes&FILE_ATTRIBUTE_REPARSE_POINT)==0;
    };
    if(!check(prefix))return out;
    std::size_t start=3;
    while(start<parent.size()){
        if(cancel.load())return out;
        const auto end=parent.find(L'\\',start);
        if(prefix.back()!=L'\\')prefix+=L'\\';
        prefix.append(parent,start,end==std::wstring::npos?
                             std::wstring::npos:end-start);
        if(!check(prefix))return out;
        if(end==std::wstring::npos)break;
        start=end+1;
    }
    std::wstring mask=parent;
    if(mask.back()!=L'\\')mask+=L'\\';
    mask+=L'*';
    WIN32_FIND_DATAW data{};
    HANDLE find=::FindFirstFileW(mask.c_str(),&data);
    if(find==INVALID_HANDLE_VALUE){
        if(::GetLastError()==ERROR_FILE_NOT_FOUND){
            out.complete=true;
        }
        return out;
    }
    constexpr std::size_t kMaxVisited=4096;
    std::size_t visited=0;
    const auto startTick=::GetTickCount64();
    do {
        if(cancel.load()){::FindClose(find);return ChildListing{};}
        if(++visited>kMaxVisited||::GetTickCount64()-startTick>2500){
            out.limited=true;
            break;
        }
        const auto attributes=data.dwFileAttributes;
        if((attributes&FILE_ATTRIBUTE_DIRECTORY)!=0 &&
           (attributes&FILE_ATTRIBUTE_REPARSE_POINT)==0 &&
           (attributes&FILE_ATTRIBUTE_HIDDEN)==0 &&
           safeLeaf(data.cFileName)){
            if(out.names.size()==kMaxChildrenPerNode){
                out.limited=true;
                break;
            }
            out.names.emplace_back(data.cFileName);
        }
    }while(::FindNextFileW(find,&data));
    const DWORD err=::GetLastError();
    ::FindClose(find);
    if(!out.limited && err!=ERROR_NO_MORE_FILES)return ChildListing{};
    out.complete=true;
    return out;
}
} // namespace fxfile::foldertree
