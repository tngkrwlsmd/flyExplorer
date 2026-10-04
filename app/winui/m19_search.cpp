#include "m19_search.h"
#include <windows.h>
#include <algorithm>
#include <cwchar>
#include <cwctype>
#include <regex>
#include <utility>

namespace fxfile { namespace preview {
namespace {

constexpr size_t kMaxWalk=2500,kMaxDepth=5,kMaxResults=100,kRecentMax=8;
constexpr size_t kMaxExtension=32;
constexpr DWORD kMaxRecentBytes=65536;

std::wstring lower(std::wstring value){
    for(auto& c:value)c=static_cast<wchar_t>(std::towlower(c));
    return value;
}

std::wstring normalizeExtension(std::wstring value){
    if(!value.empty()&&value.front()==L'.')value.erase(value.begin());
    return value;
}

std::wstring extensionOf(std::wstring const& name){
    const auto dot=name.find_last_of(L'.');
    if(dot==std::wstring::npos||dot+1>=name.size())return {};
    return name.substr(dot+1);
}

bool extensionMatches(
    std::wstring const& name,std::wstring const& requested,bool caseSensitive)
{
    if(requested.empty())return true;
    auto actual=extensionOf(name);
    if(caseSensitive)return actual==requested;
    return lower(std::move(actual))==lower(requested);
}

bool kindMatches(bool folder,SearchEntryKind kind){
    if(kind==SearchEntryKind::Files)return !folder;
    if(kind==SearchEntryKind::Folders)return folder;
    return true;
}

bool literalMatches(
    std::wstring const& name,std::wstring const& term,bool caseSensitive)
{
    if(caseSensitive)return name.find(term)!=std::wstring::npos;
    return lower(name).find(lower(term))!=std::wstring::npos;
}


bool parseOptionalSizeKb(
    std::wstring const& text,bool& has,std::uint64_t& bytes)
{
    has=!text.empty();bytes=0;
    if(!has)return true;
    if(text.size()>20)return false;
    std::uint64_t value=0;
    for(const auto ch:text){
        if(ch<L'0'||ch>L'9')return false;
        const auto digit=static_cast<std::uint64_t>(ch-L'0');
        if(value>(UINT64_MAX-digit)/10)return false;
        value=value*10+digit;
    }
    if(value>UINT64_MAX/1024)return false;
    bytes=value*1024;
    return true;
}

bool leap(int year){
    return (year%4==0&&year%100!=0)||year%400==0;
}

bool parseDate(std::wstring const& text,std::uint32_t& key)
{
    key=0;
    if(text.empty())return true;
    if(text.size()!=10||text[4]!=L'-'||text[7]!=L'-')return false;
    for(std::size_t i=0;i<text.size();++i)
        if(i!=4&&i!=7&&(text[i]<L'0'||text[i]>L'9'))return false;
    const int year=std::stoi(text.substr(0,4));
    const int month=std::stoi(text.substr(5,2));
    const int day=std::stoi(text.substr(8,2));
    if(year<1601||year>9999||month<1||month>12)return false;
    static constexpr int days[]=
        {31,28,31,30,31,30,31,31,30,31,30,31};
    const int maxDay=month==2&&leap(year)?29:days[month-1];
    if(day<1||day>maxDay)return false;
    key=static_cast<std::uint32_t>(year*10000+month*100+day);
    return true;
}

std::uint32_t localDateKey(FILETIME const& value)
{
    FILETIME local{};
    SYSTEMTIME time{};
    if(!::FileTimeToLocalFileTime(&value,&local)||
       !::FileTimeToSystemTime(&local,&time))return 0;
    return static_cast<std::uint32_t>(
        time.wYear*10000+time.wMonth*100+time.wDay);
}

bool criteriaMatch(
    WIN32_FIND_DATAW const& fd,bool folderEntry,
    SearchQuery const& query,
    std::uint64_t minBytes,bool hasMin,
    std::uint64_t maxBytes,bool hasMax,
    std::uint32_t afterDate,std::uint32_t beforeDate)
{
    if((hasMin||hasMax)&&folderEntry)return false;
    if(!folderEntry&&(hasMin||hasMax)){
        ULARGE_INTEGER size{};
        size.LowPart=fd.nFileSizeLow;
        size.HighPart=fd.nFileSizeHigh;
        if(hasMin&&size.QuadPart<minBytes)return false;
        if(hasMax&&size.QuadPart>maxBytes)return false;
    }
    if(afterDate||beforeDate){
        const auto key=localDateKey(fd.ftLastWriteTime);
        if(!key)return false;
        if(afterDate&&key<afterDate)return false;
        if(beforeDate&&key>beforeDate)return false;
    }
    return true;
}

std::wstring recentFile(){
    wchar_t base[32768]{};
    const DWORD size=::GetEnvironmentVariableW(
        L"LOCALAPPDATA",base,static_cast<DWORD>(_countof(base)));
    if(!size||size>=_countof(base))return {};
    return std::wstring(base)+L"\\flyExplorer\\recent-scopes-v1.txt";
}

bool regularFolder(std::wstring const& path){
    if(path.empty()||path.size()>32700||
       path.find_first_of(L"\r\n")!=std::wstring::npos||
       path.find(L'\0')!=std::wstring::npos)return false;
    const DWORD attrs=::GetFileAttributesW(path.c_str());
    return attrs!=INVALID_FILE_ATTRIBUTES &&
           (attrs&FILE_ATTRIBUTE_DIRECTORY)!=0;
}

bool exactWrite(HANDLE h,unsigned char const* p,size_t bytes){
    while(bytes){
        DWORD n=0;
        auto next=static_cast<DWORD>(std::min<size_t>(bytes,65536));
        if(!::WriteFile(h,p,next,&n,nullptr)||!n)return false;
        p+=n;bytes-=n;
    }
    return true;
}

} // namespace

SearchQueryValidation validateSearchQuery(SearchQuery const& query) noexcept
{
    try{
        if(query.term.size()>256||
           query.term.find_first_of(L"\r\n")!=std::wstring::npos)
            return SearchQueryValidation::InvalidTerm;

        const bool hasCriterion=
            !query.term.empty()||!query.extension.empty()||
            !query.minSizeKb.empty()||!query.maxSizeKb.empty()||
            !query.modifiedAfter.empty()||!query.modifiedBefore.empty();
        if(!hasCriterion||(query.regex&&query.term.empty()))
            return SearchQueryValidation::InvalidTerm;

        auto extension=normalizeExtension(query.extension);
        if(query.extension.size()>kMaxExtension||
           (!query.extension.empty()&&extension.empty())||
           query.extension.find_first_of(L"\\/:*?\"<>|\r\n")!=
               std::wstring::npos)
            return SearchQueryValidation::InvalidExtension;

        bool hasMin=false,hasMax=false;
        std::uint64_t minBytes=0,maxBytes=0;
        if(!parseOptionalSizeKb(query.minSizeKb,hasMin,minBytes)||
           !parseOptionalSizeKb(query.maxSizeKb,hasMax,maxBytes)||
           (hasMin&&hasMax&&minBytes>maxBytes))
            return SearchQueryValidation::InvalidSizeRange;

        std::uint32_t afterDate=0,beforeDate=0;
        if(!parseDate(query.modifiedAfter,afterDate)||
           !parseDate(query.modifiedBefore,beforeDate)||
           (afterDate&&beforeDate&&afterDate>beforeDate))
            return SearchQueryValidation::InvalidDateRange;

        if(query.regex){
            auto flags=std::regex_constants::ECMAScript;
            if(!query.caseSensitive)flags|=std::regex_constants::icase;
            std::wregex compiled(query.term,flags);
            (void)compiled;
        }
        return SearchQueryValidation::Valid;
    }catch(std::regex_error const&){
        return SearchQueryValidation::InvalidRegex;
    }catch(...){
        return SearchQueryValidation::InvalidRegex;
    }
}

bool sameSearchQuery(SearchQuery const& a,SearchQuery const& b) noexcept
{
    return a.term==b.term&&a.extension==b.extension&&
           a.minSizeKb==b.minSizeKb&&a.maxSizeKb==b.maxSizeKb&&
           a.modifiedAfter==b.modifiedAfter&&
           a.modifiedBefore==b.modifiedBefore&&
           a.regex==b.regex&&a.caseSensitive==b.caseSensitive&&
           a.kind==b.kind;
}

SearchResults scanFiles(
    std::wstring const& folder,SearchQuery const& query,
    std::shared_ptr<std::atomic_bool> cancel)
{
    SearchResults out;
    out.scope=folder;
    out.term=query.term;
    const auto validation=validateSearchQuery(query);
    if(validation!=SearchQueryValidation::Valid||!regularFolder(folder)){
        out.invalidPattern=validation==SearchQueryValidation::InvalidRegex;
        return out;
    }

    out.valid=true;
    std::vector<std::pair<std::wstring,size_t>> pending{{folder,0}};
    size_t walked=0;
    const auto requestedExtension=normalizeExtension(query.extension);
    bool hasMin=false,hasMax=false;
    std::uint64_t minBytes=0,maxBytes=0;
    (void)parseOptionalSizeKb(query.minSizeKb,hasMin,minBytes);
    (void)parseOptionalSizeKb(query.maxSizeKb,hasMax,maxBytes);
    std::uint32_t afterDate=0,beforeDate=0;
    (void)parseDate(query.modifiedAfter,afterDate);
    (void)parseDate(query.modifiedBefore,beforeDate);
    std::wregex pattern;
    if(query.regex){
        auto flags=std::regex_constants::ECMAScript;
        if(!query.caseSensitive)flags|=std::regex_constants::icase;
        pattern.assign(query.term,flags);
    }

    while(!pending.empty()&&walked<kMaxWalk){
        if(cancel&&cancel->load()){out.canceled=true;return out;}
        auto top=std::move(pending.back());
        pending.pop_back();
        const auto patternPath=top.first+
            ((top.first.back()==L'\\'||top.first.back()==L'/')?
              L"*":L"\\*");
        WIN32_FIND_DATAW fd{};
        HANDLE find=::FindFirstFileExW(
            patternPath.c_str(),FindExInfoBasic,&fd,
            FindExSearchNameMatch,nullptr,0);
        if(find==INVALID_HANDLE_VALUE)continue;
        do{
            if(cancel&&cancel->load()){out.canceled=true;break;}
            if(!wcscmp(fd.cFileName,L".")||!wcscmp(fd.cFileName,L".."))
                continue;

            ++walked;
            const auto candidate=top.first+
                ((top.first.back()==L'\\'||top.first.back()==L'/')?
                  L"":L"\\")+fd.cFileName;
            const bool folderEntry=
                (fd.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY)!=0;

            bool nameMatch=query.term.empty();
            if(!query.term.empty()){
                if(query.regex)
                    nameMatch=std::regex_search(fd.cFileName,pattern);
                else
                    nameMatch=literalMatches(
                        fd.cFileName,query.term,query.caseSensitive);
            }

            const bool extensionMatch=
                folderEntry?requestedExtension.empty():
                extensionMatches(
                    fd.cFileName,requestedExtension,query.caseSensitive);

            if(kindMatches(folderEntry,query.kind)&&
               nameMatch&&extensionMatch&&
               criteriaMatch(fd,folderEntry,query,
                             minBytes,hasMin,maxBytes,hasMax,
                             afterDate,beforeDate)){
                ++out.count;
                if(out.matches.size()<kMaxResults)
                    out.matches.push_back(candidate);
                else out.truncated=true;
            }

            if(folderEntry&&top.second<kMaxDepth &&
               (fd.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)==0)
                pending.emplace_back(candidate,top.second+1);

            if(walked>=kMaxWalk){
                out.truncated=true;
                break;
            }
        }while(::FindNextFileW(find,&fd));
        ::FindClose(find);
        if(out.canceled)return out;
    }
    if(!pending.empty())out.truncated=true;
    return out;
}

SearchResults scanFiles(
    std::wstring const& folder,std::wstring const& term,
    std::shared_ptr<std::atomic_bool> cancel)
{
    SearchQuery query{};
    query.term=term;
    return scanFiles(folder,query,std::move(cancel));
}

void rememberScope(std::vector<std::wstring>& items,
                   std::wstring const& folder){
    if(!regularFolder(folder))return;
    auto value=lower(folder);
    items.erase(std::remove_if(items.begin(),items.end(),
        [&](std::wstring const& v){return lower(v)==value;}),items.end());
    items.insert(items.begin(),folder);
    if(items.size()>kRecentMax)items.resize(kRecentMax);
}

bool readRecentScopes(std::vector<std::wstring>& out){
    out.clear();
    const auto file=recentFile();
    if(file.empty())return false;
    const auto attrs=::GetFileAttributesW(file.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES)return true;
    if(attrs&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))
        return false;

    HANDLE handle=::CreateFileW(
        file.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if(handle==INVALID_HANDLE_VALUE)return false;

    const DWORD size=::GetFileSize(handle,nullptr);
    if(size==INVALID_FILE_SIZE||size<2||size>kMaxRecentBytes||size%2){
        ::CloseHandle(handle);
        return false;
    }

    std::vector<unsigned char> bytes(size);
    DWORD used=0;
    bool valid=::ReadFile(handle,bytes.data(),size,&used,nullptr)!=FALSE &&
               used==size&&bytes[0]==0xff&&bytes[1]==0xfe;
    ::CloseHandle(handle);
    if(!valid)return false;

    std::wstring text;
    for(size_t i=2;i<size;i+=2)
        text.push_back(static_cast<wchar_t>(bytes[i]|(bytes[i+1]<<8)));

    size_t pos=0;
    while(pos<text.size()){
        auto end=text.find(L'\n',pos);
        auto line=text.substr(
            pos,end==std::wstring::npos?std::wstring::npos:end-pos);
        if(!line.empty()&&line.back()==L'\r')line.pop_back();
        if(line.find(L'\0')!=std::wstring::npos||line.size()>32700)
            return false;
        if(!line.empty()&&regularFolder(line)){
            const auto key=lower(line);
            const bool exists=std::any_of(
                out.begin(),out.end(),
                [&](std::wstring const& item){return lower(item)==key;});
            if(!exists)out.push_back(std::move(line));
        }
        if(out.size()>kRecentMax)return false;
        if(end==std::wstring::npos)break;
        pos=end+1;
    }
    return true;
}

bool writeRecentScopes(std::vector<std::wstring> const& items){
    if(items.size()>kRecentMax)return false;
    const auto path=recentFile();
    if(path.empty())return false;
    const auto split=path.find_last_of(L'\\');
    if(split==std::wstring::npos)return false;
    const auto dir=path.substr(0,split);
    if(!::CreateDirectoryW(dir.c_str(),nullptr)&&
       ::GetLastError()!=ERROR_ALREADY_EXISTS)return false;
    const auto attrs=::GetFileAttributesW(dir.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES||
       (attrs&FILE_ATTRIBUTE_DIRECTORY)==0||
       (attrs&FILE_ATTRIBUTE_REPARSE_POINT)!=0)return false;

    std::wstring text;
    for(auto const& folder:items){
        if(!regularFolder(folder))return false;
        text+=folder+L"\r\n";
    }
    if((text.size()+1)*2>kMaxRecentBytes)return false;

    const auto tmp=path+L".tmp."+std::to_wstring(::GetCurrentProcessId())+
                   L"."+std::to_wstring(::GetTickCount64());
    HANDLE handle=::CreateFileW(
        tmp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,
        FILE_ATTRIBUTE_NORMAL,nullptr);
    if(handle==INVALID_HANDLE_VALUE)return false;

    const unsigned char bom[]={0xff,0xfe};
    bool ok=exactWrite(handle,bom,2)&&
      exactWrite(handle,reinterpret_cast<unsigned char const*>(text.data()),
                 text.size()*sizeof(wchar_t))&&
      ::FlushFileBuffers(handle)!=FALSE;
    ::CloseHandle(handle);
    if(ok)ok=::MoveFileExW(
        tmp.c_str(),path.c_str(),
        MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=FALSE;
    if(!ok)::DeleteFileW(tmp.c_str());
    return ok;
}

} }
