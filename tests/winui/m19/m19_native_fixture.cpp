// Test-owned native M1.9 workspace/search bridge contract, no MFC profile.
#include "m19_workspace.h"
#include "m19_search.h"
#include "../../../src/base/search_preset_store.h"
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
std::vector<unsigned char> codepage(
    UINT page,std::wstring const& text)
{
    BOOL usedDefault=FALSE;
    const int needed=::WideCharToMultiByte(
        page,WC_NO_BEST_FIT_CHARS,text.data(),
        static_cast<int>(text.size()),nullptr,0,nullptr,&usedDefault);
    if(needed<=0||usedDefault)return {};
    std::vector<unsigned char> out(static_cast<std::size_t>(needed));
    usedDefault=FALSE;
    const int written=::WideCharToMultiByte(
        page,WC_NO_BEST_FIT_CHARS,text.data(),
        static_cast<int>(text.size()),
        reinterpret_cast<char*>(out.data()),needed,nullptr,&usedDefault);
    if(written!=needed||usedDefault)return {};
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
    auto touch=[&](std::wstring const& path){
        HANDLE file=::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,
            CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(file==INVALID_HANDLE_VALUE)return false;
        ::CloseHandle(file);
        return true;
    };
    auto sizeAndDate=[&](std::wstring const& path,
                         std::uint64_t bytes,
                         WORD year,WORD month,WORD day){
        HANDLE file=::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,
            OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
        if(file==INVALID_HANDLE_VALUE)return false;
        LARGE_INTEGER size{};size.QuadPart=static_cast<LONGLONG>(bytes);
        bool ok=::SetFilePointerEx(file,size,nullptr,FILE_BEGIN)!=FALSE&&
                ::SetEndOfFile(file)!=FALSE;
        SYSTEMTIME local{};
        local.wYear=year;local.wMonth=month;local.wDay=day;local.wHour=12;
        FILETIME localFt{},utcFt{};
        ok=ok&&::SystemTimeToFileTime(&local,&localFt)!=FALSE&&
              ::LocalFileTimeToFileTime(&localFt,&utcFt)!=FALSE&&
              ::SetFileTime(file,nullptr,nullptr,&utcFt)!=FALSE;
        ::CloseHandle(file);
        return ok;
    };
    const auto reportUpper=left+L"\\Report-2026.TXT";
    const auto reportLower=left+L"\\report-2025.txt";
    const auto notes=left+L"\\notes.md";
    const auto reportFolder=left+L"\\Report-Archive";
    const auto nestedReport=reportFolder+L"\\nested-report.txt";
    const auto korean=left+L"\\한글-보고서.TXT";
    if(!touch(reportUpper)||!touch(reportLower)||!touch(notes)||
       !::CreateDirectoryW(reportFolder.c_str(),nullptr)||
       !touch(nestedReport)||!touch(korean))return 95;

    if(!sizeAndDate(reportUpper,4096,2026,1,15)||
       !sizeAndDate(reportLower,16384,2025,6,10)||
       !sizeAndDate(notes,2048,2024,3,20)||
       !sizeAndDate(nestedReport,8192,2026,2,5)||
       !sizeAndDate(korean,12288,2026,4,1))return 94;

    auto cancel=std::make_shared<std::atomic_bool>(false);
    auto result=fxfile::preview::scanFiles(left,L"owned-needle",cancel);
    expect(result.valid&&!result.truncated&&result.count==1&&
           result.matches.size()==1&&result.matches[0]==match,
           "NATIVE_READ_ONLY_BOUNDED_SEARCH");

    const auto scaleRoot=root+L"\\Search Scale";
    if(!::CreateDirectoryW(scaleRoot.c_str(),nullptr))return 90;
    bool scaleFiles=true;
    for(int i=0;i<2600;++i){
        const auto prefix=i<1100?L"\\scale-bulk-hit-":L"\\scale-filler-";
        if(!touch(scaleRoot+prefix+std::to_wstring(i)+L".txt")){
            scaleFiles=false;break;
        }
    }
    auto deep=scaleRoot;
    bool deepTree=true;
    for(int depth=0;depth<7;++depth){
        deep+=L"\\level-"+std::to_wstring(depth);
        if(!::CreateDirectoryW(deep.c_str(),nullptr)){
            deepTree=false;break;
        }
    }
    const auto deepTarget=deep+L"\\scale-deep-target.txt";
    if(deepTree)deepTree=touch(deepTarget);

    fxfile::preview::SearchQuery scaleBulk{};
    scaleBulk.term=L"scale-bulk-hit";
    auto scaleBulkResult=fxfile::preview::scanFiles(
        scaleRoot,scaleBulk,cancel);
    expect(scaleFiles&&deepTree&&scaleBulkResult.valid&&
           scaleBulkResult.truncated&&scaleBulkResult.resultLimited&&
           !scaleBulkResult.traversalLimited&&
           scaleBulkResult.visited>2500&&scaleBulkResult.count==1100&&
           scaleBulkResult.matches.size()==1000,
           "SEARCH_SCALE_BEYOND_2500_WALK_AND_100_RESULTS");

    fxfile::preview::SearchQuery scaleDeep{};
    scaleDeep.term=L"scale-deep-target";
    auto scaleDeepResult=fxfile::preview::scanFiles(
        scaleRoot,scaleDeep,cancel);
    expect(scaleDeepResult.valid&&!scaleDeepResult.truncated&&
           !scaleDeepResult.traversalLimited&&
           scaleDeepResult.count==1&&scaleDeepResult.matches.size()==1&&
           scaleDeepResult.matches[0]==deepTarget,
           "SEARCH_SCALE_DEPTH_BEYOND_FIVE");

    fxfile::preview::SearchQuery regexCase{};
    regexCase.term=L"^Report-[0-9]{4}\\.TXT$";
    regexCase.regex=true;
    regexCase.caseSensitive=true;
    auto regexCaseResult=fxfile::preview::scanFiles(left,regexCase,cancel);
    expect(regexCaseResult.valid&&regexCaseResult.count==1&&
           regexCaseResult.matches.size()==1&&
           regexCaseResult.matches[0]==reportUpper,
           "REGEX_CASE_SENSITIVE_FILE_MATCH");

    regexCase.caseSensitive=false;
    auto regexIgnoreCase=fxfile::preview::scanFiles(left,regexCase,cancel);
    expect(regexIgnoreCase.valid&&regexIgnoreCase.count==2,
           "REGEX_CASE_INSENSITIVE_FILE_MATCH");

    fxfile::preview::SearchQuery indexedExtension{};
    indexedExtension.mode=fxfile::preview::SearchMode::WindowsIndex;
    indexedExtension.term=L"report";
    indexedExtension.extension=L".TXT";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_EXTENSION_UPPERCASE_AND_LEADING_DOT_ACCEPTED");
    indexedExtension.extension=L"txt";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_EXTENSION_WITHOUT_DOT_ACCEPTED");
    indexedExtension.extension=L".t/x";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidExtension,
           "INDEXED_INVALID_EXTENSION_REJECTED");
    indexedExtension.extension=L"txt";
    indexedExtension.minSizeKb=L"0";
    indexedExtension.maxSizeKb=L"32";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_SIZE_RANGE_ACCEPTED");
    indexedExtension.maxSizeKb=L"0";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_ZERO_BYTE_BOUND_ACCEPTED");
    indexedExtension.minSizeKb=L"20";
    indexedExtension.maxSizeKb=L"10";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidSizeRange,
           "INDEXED_REVERSED_SIZE_RANGE_REJECTED");
    indexedExtension.minSizeKb=L"1x";
    indexedExtension.maxSizeKb=L"";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidSizeRange,
           "INDEXED_NONDECIMAL_SIZE_REJECTED");
    indexedExtension.minSizeKb=L"9007199254740992";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidSizeRange,
           "INDEXED_SIZE_SQL_BIGINT_OVERFLOW_REJECTED");
    indexedExtension.minSizeKb=L"";
    indexedExtension.maxSizeKb=L"9007199254740991";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_SIZE_SQL_BIGINT_CEILING_ACCEPTED");
    indexedExtension.maxSizeKb=L"";
    indexedExtension.modifiedAfter=L"2026-02-01";
    indexedExtension.modifiedBefore=L"2026-02-28";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_INCLUSIVE_DATE_RANGE_ACCEPTED");
    indexedExtension.modifiedAfter=L"";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_BEFORE_ONLY_ACCEPTED");
    indexedExtension.modifiedBefore=L"";
    indexedExtension.modifiedAfter=L"2024-02-29";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_LEAP_DAY_ACCEPTED");
    indexedExtension.modifiedAfter=L"2025-02-29";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INDEXED_NONLEAP_DAY_REJECTED");
    indexedExtension.modifiedAfter=L"2026-02-30";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INDEXED_INVALID_DAY_REJECTED");
    indexedExtension.modifiedAfter=L"2026/02/01";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INDEXED_DATE_FORMAT_REJECTED");
    indexedExtension.modifiedAfter=L"2026-04-01";
    indexedExtension.modifiedBefore=L"2026-03-31";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INDEXED_REVERSED_DATE_RANGE_REJECTED");
    indexedExtension.modifiedAfter=L"1600-12-31";
    indexedExtension.modifiedBefore=L"";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INDEXED_OUT_OF_RANGE_YEAR_REJECTED");
    indexedExtension.modifiedAfter=L"2026-02-01";
    indexedExtension.modifiedBefore=L"2026-02-28";
    indexedExtension.minSizeKb=L"1";
    indexedExtension.maxSizeKb=L"8";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::Valid,
           "INDEXED_EXTENSION_SIZE_DATE_AND_ACCEPTED");
    indexedExtension.contentTerm=L"unrelated content";
    expect(fxfile::preview::validateSearchQuery(indexedExtension)==
           fxfile::preview::SearchQueryValidation::InvalidIndexedCriteria,
           "INDEXED_CONTENT_STILL_REJECTED");
    indexedExtension.contentTerm=L"";
    indexedExtension.minSizeKb=L"";
    indexedExtension.maxSizeKb=L"";
    indexedExtension.modifiedAfter=L"";
    indexedExtension.modifiedBefore=L"";

    fxfile::preview::SearchQuery extensionQuery{};
    extensionQuery.term=L"report";
    extensionQuery.extension=L".txt";
    auto extensionResult=fxfile::preview::scanFiles(
        left,extensionQuery,cancel);
    expect(extensionResult.valid&&extensionResult.count==3,
           "LITERAL_EXTENSION_FILTER");

    fxfile::preview::SearchQuery folders{};
    folders.term=L"Report";
    folders.kind=fxfile::preview::SearchEntryKind::Folders;
    auto folderResult=fxfile::preview::scanFiles(left,folders,cancel);
    expect(folderResult.valid&&folderResult.count==1&&
           folderResult.matches[0]==reportFolder,
           "FOLDER_ONLY_SEARCH");

    fxfile::preview::SearchQuery both{};
    both.term=L"report";
    both.kind=fxfile::preview::SearchEntryKind::FilesAndFolders;
    auto bothResult=fxfile::preview::scanFiles(left,both,cancel);
    expect(bothResult.valid&&bothResult.count==4,
           "FILES_AND_FOLDERS_SEARCH");

    fxfile::preview::SearchQuery invalidRegex{};
    invalidRegex.term=L"[";
    invalidRegex.regex=true;
    auto invalidRegexResult=fxfile::preview::scanFiles(
        left,invalidRegex,cancel);
    expect(!invalidRegexResult.valid&&invalidRegexResult.invalidPattern&&
           fxfile::preview::validateSearchQuery(invalidRegex)==
             fxfile::preview::SearchQueryValidation::InvalidRegex,
           "INVALID_REGEX_REJECTED_BEFORE_SEARCH");

    fxfile::preview::SearchQuery unicodeQuery{};
    unicodeQuery.term=L"보고서";
    unicodeQuery.extension=L"txt";
    auto unicodeResult=fxfile::preview::scanFiles(left,unicodeQuery,cancel);
    expect(unicodeResult.valid&&unicodeResult.count==1&&
           unicodeResult.matches[0]==korean,
           "UNICODE_LITERAL_EXTENSION_MATCH");

    fxfile::preview::SearchQuery sizeOnly{};
    sizeOnly.minSizeKb=L"10";
    sizeOnly.maxSizeKb=L"13";
    auto sizeResult=fxfile::preview::scanFiles(left,sizeOnly,cancel);
    expect(sizeResult.valid&&sizeResult.count==1&&
           sizeResult.matches[0]==korean,
           "SIZE_ONLY_QUERY_WITH_EMPTY_TERM");

    fxfile::preview::SearchQuery dateOnly{};
    dateOnly.modifiedAfter=L"2026-02-01";
    dateOnly.modifiedBefore=L"2026-02-28";
    auto dateResult=fxfile::preview::scanFiles(left,dateOnly,cancel);
    expect(dateResult.valid&&dateResult.count==1&&
           dateResult.matches[0]==nestedReport,
           "LOCAL_MODIFIED_DATE_RANGE");

    fxfile::preview::SearchQuery compound{};
    compound.term=L"report";
    compound.extension=L"txt";
    compound.minSizeKb=L"7";
    compound.maxSizeKb=L"9";
    compound.modifiedAfter=L"2026-02-01";
    compound.modifiedBefore=L"2026-02-28";
    auto compoundResult=fxfile::preview::scanFiles(left,compound,cancel);
    expect(compoundResult.valid&&compoundResult.count==1&&
           compoundResult.matches[0]==nestedReport,
           "NAME_EXTENSION_SIZE_DATE_AND_QUERY");

    fxfile::preview::SearchQuery invalidSize{};
    invalidSize.term=L"report";invalidSize.minSizeKb=L"20";
    invalidSize.maxSizeKb=L"10";
    expect(fxfile::preview::validateSearchQuery(invalidSize)==
           fxfile::preview::SearchQueryValidation::InvalidSizeRange,
           "INVALID_SIZE_RANGE_REJECTED");

    fxfile::preview::SearchQuery invalidDate{};
    invalidDate.term=L"report";invalidDate.modifiedAfter=L"2026-02-30";
    expect(fxfile::preview::validateSearchQuery(invalidDate)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "INVALID_DATE_SYNTAX_REJECTED");

    fxfile::preview::SearchQuery reversedDate{};
    reversedDate.term=L"report";reversedDate.modifiedAfter=L"2026-04-01";
    reversedDate.modifiedBefore=L"2026-02-01";
    expect(fxfile::preview::validateSearchQuery(reversedDate)==
           fxfile::preview::SearchQueryValidation::InvalidDateRange,
           "REVERSED_DATE_RANGE_REJECTED");

    fxfile::preview::SearchQuery folderSize{};
    folderSize.term=L"Report";
    folderSize.kind=fxfile::preview::SearchEntryKind::Folders;
    folderSize.minSizeKb=L"1";
    auto folderSizeResult=fxfile::preview::scanFiles(left,folderSize,cancel);
    expect(folderSizeResult.valid&&folderSizeResult.count==0,
           "SIZE_CRITERIA_EXCLUDES_FOLDERS");

    const auto contentUtf8=left+L"\\content-utf8.txt";
    const auto contentUtf16Le=left+L"\\content-utf16le.txt";
    const auto contentUtf16Be=left+L"\\content-utf16be.txt";
    const auto contentBinary=left+L"\\content-binary.bin";
    const auto contentOversize=left+L"\\content-oversize.txt";
    const auto contentCp949=left+L"\\content-cp949.txt";
    const auto content1252=left+L"\\content-1252.txt";
    const std::string utf8Body="Alpha UtfEightOnly omega";
    if(!put(contentUtf8,std::vector<unsigned char>(
             utf8Body.begin(),utf8Body.end()))||
       !put(contentUtf16Le,utf16(L"prefix 한글바늘 suffix")))
        return 93;

    std::vector<unsigned char> utf16be{0xfe,0xff};
    for(const auto ch:std::wstring(L"prefix BigEndianNeedle suffix")){
        utf16be.push_back(static_cast<unsigned char>((ch>>8)&255));
        utf16be.push_back(static_cast<unsigned char>(ch&255));
    }
    const auto cp949=codepage(949,L"prefix 레거시한글 suffix");
    const auto cp1252=codepage(1252,L"prefix café western suffix");
    if(cp949.empty()||cp1252.empty()||
       !put(contentUtf16Be,utf16be)||
       !put(contentBinary,std::vector<unsigned char>{
           'A',0,'N','e','e','d','l','e'})||
       !put(contentOversize,
            std::vector<unsigned char>(1024*1024+1,'x'))||
       !put(contentCp949,cp949)||
       !put(content1252,cp1252))
        return 92;

    fxfile::preview::SearchQuery contentUtf8Query{};
    contentUtf8Query.contentTerm=L"utfEightOnly";
    auto contentUtf8Result=fxfile::preview::scanFiles(
        left,contentUtf8Query,cancel);
    expect(contentUtf8Result.valid&&contentUtf8Result.count==1&&
           contentUtf8Result.matches[0]==contentUtf8&&
           contentUtf8Result.contentFilesScanned>0,
           "UTF8_CONTENT_CASE_INSENSITIVE_MATCH");

    contentUtf8Query.caseSensitive=true;
    contentUtf8Query.contentTerm=L"UtfEightOnly";
    auto contentCaseResult=fxfile::preview::scanFiles(
        left,contentUtf8Query,cancel);
    expect(contentCaseResult.valid&&contentCaseResult.count==1&&
           contentCaseResult.matches[0]==contentUtf8,
           "CONTENT_CASE_SENSITIVE_MATCH");

    fxfile::preview::SearchQuery contentRegexQuery{};
    contentRegexQuery.term=L"content-utf8";
    contentRegexQuery.contentTerm=
        L"^Alpha\\s+Utf(Eight|Never)Only\\s+omega$";
    contentRegexQuery.contentRegex=true;
    auto contentRegexResult=fxfile::preview::scanFiles(
        left,contentRegexQuery,cancel);
    expect(contentRegexResult.valid&&contentRegexResult.count==1&&
           contentRegexResult.matches.size()==1&&
           contentRegexResult.matches[0]==contentUtf8,
           "CONTENT_REGEX_GROUP_ALTERNATION_MATCH");

    fxfile::preview::SearchQuery unsupportedContentRegex{};
    unsupportedContentRegex.contentTerm=L"(?=Alpha)Alpha";
    unsupportedContentRegex.contentRegex=true;
    expect(fxfile::preview::validateSearchQuery(unsupportedContentRegex)==
           fxfile::preview::SearchQueryValidation::InvalidContentRegex,
           "CONTENT_REGEX_UNSUPPORTED_LOOKAROUND_REJECTED");

    fxfile::preview::SearchQuery contentLeQuery{};
    contentLeQuery.contentTerm=L"한글바늘";
    auto contentLeResult=fxfile::preview::scanFiles(
        left,contentLeQuery,cancel);
    expect(contentLeResult.valid&&contentLeResult.count==1&&
           contentLeResult.matches[0]==contentUtf16Le,
           "UTF16LE_BOM_CONTENT_MATCH");

    fxfile::preview::SearchQuery contentBeQuery{};
    contentBeQuery.contentTerm=L"BigEndianNeedle";
    contentBeQuery.caseSensitive=true;
    auto contentBeResult=fxfile::preview::scanFiles(
        left,contentBeQuery,cancel);
    expect(contentBeResult.valid&&contentBeResult.count==1&&
           contentBeResult.matches[0]==contentUtf16Be,
           "UTF16BE_BOM_CONTENT_MATCH");

    fxfile::preview::SearchQuery cp949Auto{};
    cp949Auto.term=L"content-cp949";
    cp949Auto.contentTerm=L"레거시한글";
    auto cp949AutoResult=fxfile::preview::scanFiles(
        left,cp949Auto,cancel);
    expect(cp949AutoResult.valid&&cp949AutoResult.count==0&&
           cp949AutoResult.contentFilesSkipped==1,
           "AUTO_UTF_REJECTS_CP949");

    auto cp949Query=cp949Auto;
    cp949Query.contentEncoding=
        fxfile::preview::SearchContentEncoding::Korean949;
    auto cp949Result=fxfile::preview::scanFiles(left,cp949Query,cancel);
    expect(cp949Result.valid&&cp949Result.count==1&&
           cp949Result.matches[0]==contentCp949,
           "EXPLICIT_CP949_CONTENT_MATCH");

    fxfile::preview::SearchQuery cp1252Auto{};
    cp1252Auto.term=L"content-1252";
    cp1252Auto.contentTerm=L"café";
    auto cp1252AutoResult=fxfile::preview::scanFiles(
        left,cp1252Auto,cancel);
    expect(cp1252AutoResult.valid&&cp1252AutoResult.count==0&&
           cp1252AutoResult.contentFilesSkipped==1,
           "AUTO_UTF_REJECTS_WINDOWS1252");

    auto cp1252Query=cp1252Auto;
    cp1252Query.contentEncoding=
        fxfile::preview::SearchContentEncoding::Windows1252;
    auto cp1252Result=fxfile::preview::scanFiles(
        left,cp1252Query,cancel);
    expect(cp1252Result.valid&&cp1252Result.count==1&&
           cp1252Result.matches[0]==content1252,
           "EXPLICIT_WINDOWS1252_CONTENT_MATCH");

    auto bomFallback=contentLeQuery;
    bomFallback.contentEncoding=
        fxfile::preview::SearchContentEncoding::Korean949;
    auto bomFallbackResult=fxfile::preview::scanFiles(
        left,bomFallback,cancel);
    expect(bomFallbackResult.valid&&bomFallbackResult.count==1&&
           bomFallbackResult.matches[0]==contentUtf16Le,
           "BOM_OVERRIDES_EXPLICIT_FALLBACK_ENCODING");

    fxfile::preview::SearchQuery invalidEncoding{};
    invalidEncoding.contentTerm=L"needle";
    invalidEncoding.contentEncoding=
        static_cast<fxfile::preview::SearchContentEncoding>(99);
    expect(fxfile::preview::validateSearchQuery(invalidEncoding)==
           fxfile::preview::SearchQueryValidation::InvalidContentEncoding,
           "INVALID_CONTENT_ENCODING_REJECTED");

    fxfile::preview::SearchQuery binaryQuery{};
    binaryQuery.term=L"content-binary";
    binaryQuery.contentTerm=L"Needle";
    auto binaryResult=fxfile::preview::scanFiles(left,binaryQuery,cancel);
    expect(binaryResult.valid&&binaryResult.count==0&&
           binaryResult.contentFilesSkipped==1,
           "BINARY_NUL_CONTENT_SKIPPED");

    fxfile::preview::SearchQuery oversizeQuery{};
    oversizeQuery.term=L"content-oversize";
    oversizeQuery.contentTerm=L"x";
    auto oversizeResult=fxfile::preview::scanFiles(
        left,oversizeQuery,cancel);
    expect(oversizeResult.valid&&oversizeResult.count==0&&
           oversizeResult.contentFilesSkipped==1&&
           oversizeResult.contentBytesRead==0,
           "CONTENT_FILE_OVER_1MIB_SKIPPED");

    fxfile::preview::SearchQuery contentAnd{};
    contentAnd.term=L"content-utf8";
    contentAnd.extension=L".txt";
    contentAnd.contentTerm=L"utfEightOnly";
    auto contentAndResult=fxfile::preview::scanFiles(
        left,contentAnd,cancel);
    expect(contentAndResult.valid&&contentAndResult.count==1&&
           contentAndResult.matches[0]==contentUtf8,
           "NAME_EXTENSION_CONTENT_AND_QUERY");

    fxfile::preview::SearchQuery contentFolderOnly{};
    contentFolderOnly.contentTerm=L"needle";
    contentFolderOnly.kind=fxfile::preview::SearchEntryKind::Folders;
    expect(fxfile::preview::validateSearchQuery(contentFolderOnly)==
           fxfile::preview::SearchQueryValidation::InvalidContentTerm,
           "CONTENT_FOLDER_ONLY_REJECTED_BEFORE_SEARCH");

    const auto budgetDir=left+L"\\ContentBudget";
    if(!::CreateDirectoryW(budgetDir.c_str(),nullptr))return 91;
    const std::vector<unsigned char> oneMiB(1024*1024,'a');
    bool budgetFiles=true;
    for(int i=0;i<17;++i){
        const auto path=budgetDir+L"\\budget-"+
            (i<10?L"0":L"")+std::to_wstring(i)+L".txt";
        if(!put(path,oneMiB)){budgetFiles=false;break;}
    }
    fxfile::preview::SearchQuery budgetQuery{};
    budgetQuery.term=L"budget-";
    budgetQuery.contentTerm=L"needle-never";
    auto budgetResult=fxfile::preview::scanFiles(
        left,budgetQuery,cancel);
    expect(budgetFiles&&budgetResult.valid&&budgetResult.truncated&&
           budgetResult.contentLimited&&budgetResult.count==0&&
           budgetResult.contentFilesScanned==16&&
           budgetResult.contentBytesRead==16ull*1024ull*1024ull,
           "CONTENT_TOTAL_IO_BUDGET_16MIB");

    fxfile::preview::SearchQuery adversarialRegex{};
    adversarialRegex.term=L"budget-00";
    adversarialRegex.contentTerm=
        L"(?:a|aa|aaa|aaaa|aaaaa|aaaaaa)+b";
    adversarialRegex.contentRegex=true;
    auto adversarialRegexResult=fxfile::preview::scanFiles(
        left,adversarialRegex,cancel);
    expect(adversarialRegexResult.valid&&
           adversarialRegexResult.count==0&&
           adversarialRegexResult.contentRegexLimited&&
           adversarialRegexResult.contentFilesSkipped==1&&
           adversarialRegexResult.contentBytesRead==1024ull*1024ull,
           "CONTENT_REGEX_ADVERSARIAL_STEP_BUDGET");

    using PresetStore=fxfile::searchpresets::Store;
    using PresetResult=fxfile::searchpresets::MutationResult;
    PresetStore presets;
    fxfile::searchpresets::Preset preset{};
    preset.name=L"이번 달 보고서";
    preset.term=L"report";preset.extension=L"txt";
    preset.contentTerm=L"needle.*";
    preset.contentEncoding=1;
    preset.contentRegex=true;
    preset.minSizeKb=L"7";preset.maxSizeKb=L"9";
    preset.modifiedAfter=L"2026-02-01";
    preset.modifiedBefore=L"2026-02-28";
    expect(presets.add(preset)==PresetResult::Applied&&
           presets.add(preset)==PresetResult::Duplicate,
           "SEARCH_PRESET_ADD_DUPLICATE_BOUNDARY");
    const auto presetFile=root+L"\\search-presets.txt";
    PresetStore reloaded;
    expect(presets.saveTo(presetFile)&&reloaded.loadFrom(presetFile)&&
           reloaded.items().size()==1&&
           reloaded.items()[0].modifiedAfter==L"2026-02-01"&&
           reloaded.items()[0].minSizeKb==L"7",
           "SEARCH_PRESET_ATOMIC_RESTART_PERSISTENCE");
    const auto presetRaw=bytes(presetFile);
    const std::string presetText(presetRaw.begin(),presetRaw.end());
    expect(reloaded.items()[0].contentTerm==L"needle.*"&&
           reloaded.items()[0].contentEncoding==1&&
           reloaded.items()[0].contentRegex&&
           presetRaw.size()>8&&
           presetText.find("schema=4")!=std::string::npos,
           "SEARCH_PRESET_CONTENT_REGEX_SCHEMA4_RESTART");

    const auto schema3PresetFile=root+L"\\search-presets-v3.txt";
    const std::string schema3Preset=
        "schema=3\r\nLegacy3\treport\tneedle\t1\ttxt\t0\t0\t0\t7\t9\t"
        "2026-02-01\t2026-02-28\r\n";
    PresetStore schema3Presets;
    expect(put(schema3PresetFile,std::vector<unsigned char>(
               schema3Preset.begin(),schema3Preset.end()))&&
           schema3Presets.loadFrom(schema3PresetFile)&&
           schema3Presets.items().size()==1&&
           schema3Presets.items()[0].contentTerm==L"needle"&&
           schema3Presets.items()[0].contentEncoding==1&&
           !schema3Presets.items()[0].contentRegex,
           "SEARCH_PRESET_SCHEMA3_BACKWARD_COMPAT");

    const auto schema2PresetFile=root+L"\\search-presets-v2.txt";
    const std::string schema2Preset=
        "schema=2\r\nLegacy2\treport\tneedle\ttxt\t0\t0\t0\t7\t9\t"
        "2026-02-01\t2026-02-28\r\n";
    PresetStore schema2Presets;
    expect(put(schema2PresetFile,std::vector<unsigned char>(
               schema2Preset.begin(),schema2Preset.end()))&&
           schema2Presets.loadFrom(schema2PresetFile)&&
           schema2Presets.items().size()==1&&
           schema2Presets.items()[0].contentTerm==L"needle"&&
           schema2Presets.items()[0].contentEncoding==0,
           "SEARCH_PRESET_SCHEMA2_BACKWARD_COMPAT");

    const auto legacyPresetFile=root+L"\\search-presets-v1.txt";
    const std::string legacyPreset=
        "schema=1\r\nLegacy\treport\ttxt\t0\t0\t0\t7\t9\t"
        "2026-02-01\t2026-02-28\r\n";
    PresetStore legacyPresets;
    expect(put(legacyPresetFile,std::vector<unsigned char>(
               legacyPreset.begin(),legacyPreset.end()))&&
           legacyPresets.loadFrom(legacyPresetFile)&&
           legacyPresets.items().size()==1&&
           legacyPresets.items()[0].name==L"Legacy"&&
           legacyPresets.items()[0].contentTerm.empty(),
           "SEARCH_PRESET_SCHEMA1_BACKWARD_COMPAT");

    expect(reloaded.erase(0)&&reloaded.items().empty(),
           "SEARCH_PRESET_DELETE");
    ::DeleteFileW(presetFile.c_str());
    ::DeleteFileW(schema3PresetFile.c_str());
    ::DeleteFileW(schema2PresetFile.c_str());
    ::DeleteFileW(legacyPresetFile.c_str());

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
