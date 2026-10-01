// Test-owned native M1.9 workspace/search bridge contract, no MFC profile.
#include "../m19_workspace.h"
#include "../m19_search.h"
#include <windows.h>
#include <atomic>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <memory>
#include <string>
#include <vector>
namespace {
int passed=0,failed=0;
void expect(bool ok,char const* label){
    if(ok){++passed;std::printf("M19_NATIVE_%s PASS\n",label);}
    else{++failed;std::printf("M19_NATIVE_%s FAIL\n",label);}
}
std::vector<unsigned char> bytes(std::wstring const& file){
    std::ifstream stream(file,std::ios::binary);
    return {std::istreambuf_iterator<char>(stream),
            std::istreambuf_iterator<char>()};
}
bool put(std::wstring const& file,std::vector<unsigned char> const& blob){
    std::ofstream stream(file,std::ios::binary);
    stream.write(reinterpret_cast<char const*>(blob.data()),
                 static_cast<std::streamsize>(blob.size()));
    return stream.good();
}
std::vector<unsigned char> utf16(std::wstring const& text){
    std::vector<unsigned char> out{0xff,0xfe};
    for(auto c:text){
        out.push_back(static_cast<unsigned char>(c&255));
        out.push_back(static_cast<unsigned char>((c>>8)&255));
    }
    return out;
}
}
int wmain(int argc,wchar_t** argv){
    wchar_t yes[8]{},local[32768]{};
    if(argc!=2 ||
       ::GetEnvironmentVariableW(
          L"FLY_M19_OWNED_NATIVE_ONLY",yes,8)!=3||
       wcscmp(yes,L"YES"))return 99;
    const std::wstring root=argv[1];
    const auto count=::GetEnvironmentVariableW(
        L"LOCALAPPDATA",local,static_cast<DWORD>(_countof(local)));
    if(root.empty()||!count||count>=_countof(local)||
       std::wstring(local).find(root)!=0)return 98;
    const auto left=root+L"\\Native Left";
    const auto right=root+L"\\Native Right";
    const auto second=left+L"\\Native Subfolder";
    if(!::CreateDirectoryW(left.c_str(),nullptr) ||
       !::CreateDirectoryW(right.c_str(),nullptr) ||
       !::CreateDirectoryW(second.c_str(),nullptr))return 97;
    auto file=root+L"\\named.fxworkspace";
    fxfile::preview::Workspace work;
    work.split=true;work.paths[0]={left,second};
    work.paths[1]={right};work.selected[0]=1;
    std::wstring reason;
    expect(fxfile::preview::saveWorkspaceNew(file,work,reason),
        "WRITES_LEGACY_UTF16_V1_TWO_PANES_THREE_TABS");
    auto raw=bytes(file);
    expect(raw.size()>100&&raw[0]==255&&raw[1]==254,
        "BOUND_UTF16_LEGACY_BOM");
    fxfile::preview::Workspace incoming;
    expect(fxfile::preview::loadWorkspace(file,incoming,reason)&&
        incoming.split&&incoming.selected[0]==1&&
        incoming.paths[0]==work.paths[0]&&
        incoming.paths[1]==work.paths[1],
        "LEGACY_WORKSPACE_SELECTED_TABS_ROUNDTRIP");
    expect(!fxfile::preview::saveWorkspaceNew(file,work,reason)&&
        bytes(file)==raw,"CREATE_NEW_NEVER_OVERWRITES");
    std::wstring legacy=L"[main]\r\nversion = 1\r\n"
        L"main.view.row_count = 1\r\n"
        L"main.view.column_count = 2\r\n"
        L"main.view1.current_tab = 1\r\n"
        L"main.view1.tab1.path = "+left+L"\r\n"
        L"main.view1.tab2.path = "+second+L"\r\n"
        L"main.view2.current_tab = 0\r\n"
        L"main.view2.tab1.path = "+right+L"\r\n"
        L"main.view1.tab1.backward1 = "+left+
        L"\r\n[workspace]\r\nschema = 1\r\n";
    auto extended=root+L"\\legacy-extra.fxworkspace";
    expect(put(extended,utf16(legacy))&&
           fxfile::preview::loadWorkspace(extended,incoming,reason)&&
           incoming.paths[0]==work.paths[0],
           "IMPORT_EXTENDED_LEGACY_MAIN_FIELDS");
    unsigned rejected=0;
    auto reject=[&](wchar_t const* name,std::vector<unsigned char> body,
                    bool wrongExt=false){
        const auto target=root+L"\\"+name+
            (wrongExt?L".txt":L".fxworkspace");
        fxfile::preview::Workspace unchanged=incoming;
        if(put(target,body)&&
           !fxfile::preview::loadWorkspace(target,unchanged,reason)&&
           unchanged.paths[0]==incoming.paths[0]&&!reason.empty())
            ++rejected;
    };
    auto mutate=[&](std::wstring search,size_t size,std::wstring value){
        auto changed=legacy;
        auto i=changed.find(search);
        if(i==std::wstring::npos)return std::vector<unsigned char>{};
        changed.replace(i,size,value);
        return utf16(changed);
    };
    reject(L"empty",{});
    reject(L"bad-schema",mutate(L"schema = 1",10,L"schema = 2"));
    reject(L"bad-pane",mutate(L"row_count = 1",13,L"row_count = 0"));
    reject(L"missing-tab",mutate(L"tab1.path = ",12+left.size(),L"tab1.path = "));
    reject(L"missing-folder",mutate(left,left.size(),root+L"\\absent"));
    reject(L"duplicate",utf16(legacy+
           L"[main]\r\nmain.view1.current_tab = 0\r\n"));
    reject(L"oversize",std::vector<unsigned char>(1048577,0x61));
    auto partial=raw;partial.resize(23);
    reject(L"odd-length",partial);
    reject(L"wrong-extension",raw,true);
    expect(rejected==9,"NINE_MALFORMED_LEGACY_WORKSPACES_REJECTED");
    std::vector<std::wstring> recent;
    const auto privateFile=std::wstring(local)+
            L"\\flyExplorer\\recent-scopes-v1.txt";
    expect(::GetFileAttributesW(privateFile.c_str())==
           INVALID_FILE_ATTRIBUTES,
           "OPT_OUT_DOES_NOT_CREATE_PRIVATE_HISTORY");
    auto match=left+L"\\m19-unit-owned-needle.txt";
    HANDLE h=::CreateFileW(match.c_str(),GENERIC_WRITE,0,nullptr,
       CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(h==INVALID_HANDLE_VALUE)return 96;
    ::CloseHandle(h);
    auto cancel=std::make_shared<std::atomic_bool>(false);
    auto result=fxfile::preview::scanFiles(left,L"owned-needle",cancel);
    expect(result.valid&&!result.truncated&&result.count==1&&
           result.matches.size()==1&&result.matches[0]==match,
           "NATIVE_READ_ONLY_BOUNDED_SEARCH");
    cancel->store(true);
    expect(fxfile::preview::scanFiles(
           left,L"owned-needle",cancel).canceled,
           "SEARCH_CANCELLATION");
    fxfile::preview::rememberScope(recent,left);
    fxfile::preview::rememberScope(recent,right);
    fxfile::preview::rememberScope(recent,left);
    expect(recent.size()==2&&recent[0]==left,
           "RECENT_CASE_INSENSITIVE_DEDUP");
    expect(fxfile::preview::writeRecentScopes(recent)&&
           fxfile::preview::readRecentScopes(recent)&&
           recent.size()==2&&recent[0]==left,
           "OPT_IN_PRIVATE_HISTORY_RESTART");
    recent.clear();
    expect(fxfile::preview::writeRecentScopes(recent)&&
           fxfile::preview::readRecentScopes(recent)&&recent.empty(),
           "CLEAR_HISTORY_PERSISTS");
    std::printf("M19_NATIVE_SUMMARY %d passed, %d failed.\n",passed,failed);
    return failed?1:0;
}
