#include "m19_search.h"
#include "../../src/base/bounded_regex.h"
#include "../../src/base/indexed_search_wire.h"
#include <filesystem>
#include <windows.h>
#include <algorithm>
#include <array>
#include <cwchar>
#include <cwctype>
#include <regex>
#include <cstring>
#include <new>
#include <utility>

namespace fxfile { namespace preview {
namespace {

constexpr size_t kMaxWalk=20000,kMaxDepth=32,kMaxResults=1000,kRecentMax=8;
constexpr size_t kMaxExtension=32;
constexpr std::uint64_t kMaxContentFileBytes=1024ull*1024ull;
constexpr std::uint64_t kMaxContentSearchBytes=16ull*1024ull*1024ull;
constexpr DWORD kContentChunkBytes=64*1024;
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


enum class ContentMatch {
    Match,
    NoMatch,
    Skipped,
    Canceled,
    BudgetExceeded,
};

bool decodeUtf8(
    unsigned char const* data,std::size_t size,std::wstring& out)
{
    out.clear();
    if(!size)return true;
    const int needed=::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,
        reinterpret_cast<char const*>(data),
        static_cast<int>(size),nullptr,0);
    if(needed<=0)return false;
    out.resize(static_cast<std::size_t>(needed));
    return ::MultiByteToWideChar(
        CP_UTF8,MB_ERR_INVALID_CHARS,
        reinterpret_cast<char const*>(data),
        static_cast<int>(size),out.data(),needed)==needed;
}

bool decodeCodePage(
    UINT codePage,unsigned char const* data,std::size_t size,
    std::wstring& out)
{
    out.clear();
    if(!size)return true;
    const int needed=::MultiByteToWideChar(
        codePage,MB_ERR_INVALID_CHARS,
        reinterpret_cast<char const*>(data),
        static_cast<int>(size),nullptr,0);
    if(needed<=0)return false;
    out.resize(static_cast<std::size_t>(needed));
    return ::MultiByteToWideChar(
        codePage,MB_ERR_INVALID_CHARS,
        reinterpret_cast<char const*>(data),
        static_cast<int>(size),out.data(),needed)==needed;
}

bool decodeText(
    std::vector<unsigned char> const& bytes,
    SearchContentEncoding encoding,std::wstring& out)
{
    out.clear();
    if(bytes.empty())return true;
    if(bytes.size()>=2&&bytes[0]==0xff&&bytes[1]==0xfe){
        const auto remaining=bytes.size()-2;
        if(remaining%2)return false;
        out.reserve(remaining/2);
        for(std::size_t i=2;i<bytes.size();i+=2)
            out.push_back(static_cast<wchar_t>(
                bytes[i]|(static_cast<unsigned>(bytes[i+1])<<8)));
        return true;
    }
    if(bytes.size()>=2&&bytes[0]==0xfe&&bytes[1]==0xff){
        const auto remaining=bytes.size()-2;
        if(remaining%2)return false;
        out.reserve(remaining/2);
        for(std::size_t i=2;i<bytes.size();i+=2)
            out.push_back(static_cast<wchar_t>(
                (static_cast<unsigned>(bytes[i])<<8)|bytes[i+1]));
        return true;
    }
    std::size_t start=0;
    if(bytes.size()>=3&&bytes[0]==0xef&&bytes[1]==0xbb&&bytes[2]==0xbf)
        start=3;
    if(std::find(bytes.begin()+static_cast<std::ptrdiff_t>(start),
                 bytes.end(),static_cast<unsigned char>(0))!=bytes.end())
        return false;
    const auto* data=bytes.data()+start;
    const auto size=bytes.size()-start;
    switch(encoding){
    case SearchContentEncoding::AutoUtf:
        return decodeUtf8(data,size,out);
    case SearchContentEncoding::Korean949:
        return decodeCodePage(949,data,size,out);
    case SearchContentEncoding::Windows1252:
        return decodeCodePage(1252,data,size,out);
    default:
        return false;
    }
}

ContentMatch contentMatches(
    std::wstring const& path,std::uint64_t fileBytes,
    std::wstring const& term,bool caseSensitive,
    bool contentRegex,
    SearchContentEncoding encoding,
    fxfile::boundedregex::Pattern const* contentPattern,
    std::shared_ptr<std::atomic_bool> const& cancel,
    std::uint64_t& remainingBudget,
    SearchResults& out)
{
    if(fileBytes>kMaxContentFileBytes){
        ++out.contentFilesSkipped;
        return ContentMatch::Skipped;
    }
    if(fileBytes>remainingBudget){
        out.contentLimited=true;
        return ContentMatch::BudgetExceeded;
    }

    HANDLE file=::CreateFileW(
        path.c_str(),GENERIC_READ,
        FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
        nullptr,OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL|FILE_FLAG_SEQUENTIAL_SCAN|FILE_FLAG_OPEN_REPARSE_POINT,
        nullptr);
    if(file==INVALID_HANDLE_VALUE){
        ++out.contentFilesSkipped;
        return ContentMatch::Skipped;
    }
    const DWORD attrs=::GetFileAttributesW(path.c_str());
    if(attrs==INVALID_FILE_ATTRIBUTES||
       (attrs&FILE_ATTRIBUTE_REPARSE_POINT)!=0){
        ::CloseHandle(file);
        ++out.contentFilesSkipped;
        return ContentMatch::Skipped;
    }

    std::vector<unsigned char> bytes;
    bytes.reserve(static_cast<std::size_t>(fileBytes));
    std::array<unsigned char,kContentChunkBytes> chunk{};
    std::uint64_t readTotal=0;
    bool good=true;
    while(readTotal<fileBytes){
        if(cancel&&cancel->load()){
            ::CloseHandle(file);
            return ContentMatch::Canceled;
        }
        const DWORD wanted=static_cast<DWORD>(
            (std::min<std::uint64_t>)(kContentChunkBytes,fileBytes-readTotal));
        DWORD used=0;
        if(!::ReadFile(file,chunk.data(),wanted,&used,nullptr)){
            good=false;break;
        }
        if(!used)break;
        bytes.insert(bytes.end(),chunk.begin(),chunk.begin()+used);
        readTotal+=used;
    }
    ::CloseHandle(file);
    remainingBudget-=readTotal;
    out.contentBytesRead+=readTotal;
    if(!good||readTotal!=fileBytes){
        ++out.contentFilesSkipped;
        return ContentMatch::Skipped;
    }

    std::wstring text;
    if(!decodeText(bytes,encoding,text)){
        ++out.contentFilesSkipped;
        return ContentMatch::Skipped;
    }
    ++out.contentFilesScanned;
    if(contentRegex){
        if(!contentPattern){
            ++out.contentFilesSkipped;
            return ContentMatch::Skipped;
        }
        const auto matched=contentPattern->search(text,cancel);
        if(matched==fxfile::boundedregex::MatchResult::Canceled)
            return ContentMatch::Canceled;
        if(matched==fxfile::boundedregex::MatchResult::BudgetExceeded){
            out.contentRegexLimited=true;
            ++out.contentFilesSkipped;
            return ContentMatch::Skipped;
        }
        return matched==fxfile::boundedregex::MatchResult::Match?
            ContentMatch::Match:ContentMatch::NoMatch;
    }
    return literalMatches(text,term,caseSensitive)?
        ContentMatch::Match:ContentMatch::NoMatch;
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
        if(query.mode!=SearchMode::Traversal&&
           query.mode!=SearchMode::WindowsIndex)
            return SearchQueryValidation::InvalidIndexedCriteria;
        if(query.mode==SearchMode::WindowsIndex&&
           (!fxfile::indexwire::validTerm(query.term)||
            query.regex||query.caseSensitive||
            query.kind!=SearchEntryKind::Files||
             !query.contentTerm.empty()||query.contentRegex))
            return SearchQueryValidation::InvalidIndexedCriteria;
        if(query.term.size()>256||
           query.term.find_first_of(L"\r\n")!=std::wstring::npos)
            return SearchQueryValidation::InvalidTerm;

        const bool hasCriterion=
            !query.term.empty()||!query.extension.empty()||
            !query.minSizeKb.empty()||!query.maxSizeKb.empty()||
            !query.modifiedAfter.empty()||!query.modifiedBefore.empty()||
            !query.contentTerm.empty();
        if(!hasCriterion||(query.regex&&query.term.empty()))
            return SearchQueryValidation::InvalidTerm;
        if(query.contentTerm.size()>256||
           query.contentTerm.find_first_of(L"\r\n")!=std::wstring::npos||
           (!query.contentTerm.empty()&&
            query.kind==SearchEntryKind::Folders))
            return SearchQueryValidation::InvalidContentTerm;
        if(query.contentEncoding!=SearchContentEncoding::AutoUtf&&
           query.contentEncoding!=SearchContentEncoding::Korean949&&
           query.contentEncoding!=SearchContentEncoding::Windows1252)
            return SearchQueryValidation::InvalidContentEncoding;
        if(query.contentRegex){
            if(query.contentTerm.empty())
                return SearchQueryValidation::InvalidContentTerm;
            fxfile::boundedregex::Pattern contentPattern;
            if(contentPattern.compile(query.contentTerm,query.caseSensitive)!=
               fxfile::boundedregex::CompileResult::Valid)
                return SearchQueryValidation::InvalidContentRegex;
        }

        auto extension=normalizeExtension(query.extension);
        if(query.extension.size()>kMaxExtension||
           (!query.extension.empty()&&extension.empty())||
           query.extension.find_first_of(L"\\/:*?\"<>|\r\n")!=
               std::wstring::npos)
            return SearchQueryValidation::InvalidExtension;
        if(query.mode==SearchMode::WindowsIndex&&
           !query.extension.empty()&&
           !fxfile::indexwire::validExtension(extension))
            return SearchQueryValidation::InvalidExtension;

        bool hasMin=false,hasMax=false;
        std::uint64_t minBytes=0,maxBytes=0;
        if(!parseOptionalSizeKb(query.minSizeKb,hasMin,minBytes)||
           !parseOptionalSizeKb(query.maxSizeKb,hasMax,maxBytes)||
           (hasMin&&hasMax&&minBytes>maxBytes))
            return SearchQueryValidation::InvalidSizeRange;
        if(query.mode==SearchMode::WindowsIndex&&
           (minBytes>fxfile::indexwire::kMaxIndexedSizeBytes||
            maxBytes>fxfile::indexwire::kMaxIndexedSizeBytes))
            return SearchQueryValidation::InvalidSizeRange;

        std::uint32_t afterDate=0,beforeDate=0;
        if(!parseDate(query.modifiedAfter,afterDate)||
           !parseDate(query.modifiedBefore,beforeDate)||
           (afterDate&&beforeDate&&afterDate>beforeDate))
            return SearchQueryValidation::InvalidDateRange;
        if(query.mode==SearchMode::WindowsIndex&&
           (!fxfile::indexwire::parseIndexedDate(query.modifiedAfter,afterDate)||
            !fxfile::indexwire::parseIndexedDate(query.modifiedBefore,beforeDate)))
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
    return a.mode==b.mode&&a.term==b.term&&a.extension==b.extension&&
           a.minSizeKb==b.minSizeKb&&a.maxSizeKb==b.maxSizeKb&&
           a.modifiedAfter==b.modifiedAfter&&
           a.modifiedBefore==b.modifiedBefore&&
           a.contentTerm==b.contentTerm&&
           a.contentEncoding==b.contentEncoding&&
           a.regex==b.regex&&a.contentRegex==b.contentRegex&&
           a.caseSensitive==b.caseSensitive&&
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
        out.invalidPattern=
            validation==SearchQueryValidation::InvalidRegex||
            validation==SearchQueryValidation::InvalidContentRegex;
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
    std::uint64_t contentBudget=kMaxContentSearchBytes;
    fxfile::boundedregex::Pattern contentPattern;
    if(query.contentRegex&&
       contentPattern.compile(query.contentTerm,query.caseSensitive)!=
           fxfile::boundedregex::CompileResult::Valid){
        out.valid=false;
        out.invalidPattern=true;
        return out;
    }
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
            out.visited=walked;
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

            bool matched=kindMatches(folderEntry,query.kind)&&
               nameMatch&&extensionMatch&&
               criteriaMatch(fd,folderEntry,
                             minBytes,hasMin,maxBytes,hasMax,
                             afterDate,beforeDate);
            if(matched&&!query.contentTerm.empty()){
                if(folderEntry){
                    matched=false;
                }else{
                    ULARGE_INTEGER size{};
                    size.LowPart=fd.nFileSizeLow;
                    size.HighPart=fd.nFileSizeHigh;
                    const auto content=contentMatches(
                        candidate,size.QuadPart,query.contentTerm,
                        query.caseSensitive,query.contentRegex,
                        query.contentEncoding,
                        query.contentRegex?&contentPattern:nullptr,
                        cancel,contentBudget,out);
                    if(content==ContentMatch::Canceled){
                        out.canceled=true;
                        ::FindClose(find);
                        return out;
                    }
                    if(content==ContentMatch::BudgetExceeded){
                        out.truncated=true;
                        ::FindClose(find);
                        return out;
                    }
                    matched=content==ContentMatch::Match;
                }
            }
            if(matched){
                ++out.count;
                if(out.matches.size()<kMaxResults)
                    out.matches.push_back(candidate);
                else{
                    out.resultLimited=true;
                    out.truncated=true;
                }
            }

            if(folderEntry&&
               (fd.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)==0){
                if(top.second<kMaxDepth)
                    pending.emplace_back(candidate,top.second+1);
                else{
                    out.traversalLimited=true;
                    out.truncated=true;
                }
            }

            if(walked>=kMaxWalk){
                out.traversalLimited=true;
                out.truncated=true;
                break;
            }
        }while(::FindNextFileW(find,&fd));
        ::FindClose(find);
        if(out.canceled)return out;
    }
    if(!pending.empty()){
        out.traversalLimited=true;
        out.truncated=true;
    }
    return out;
}


SearchResults scanIndexedFiles(
    std::wstring const& folder,SearchQuery const& query,
    std::shared_ptr<std::atomic_bool> cancel)
{
 using namespace fxfile::indexwire;
 SearchResults result{};
 result.scope=folder;
 result.term=query.term;
 result.indexOnly=true;
 if(query.mode!=SearchMode::WindowsIndex||
    validateSearchQuery(query)!=SearchQueryValidation::Valid||
    !validScope(folder))return result;
 if(cancel&&cancel->load()){result.canceled=true;return result;}
 namespace fs=std::filesystem;
 struct Handle {
  HANDLE value=nullptr;
  Handle()=default;
  explicit Handle(HANDLE h):value(h){}
  ~Handle(){reset();}
  void reset(HANDLE next=nullptr){
   if(value&&value!=INVALID_HANDLE_VALUE)::CloseHandle(value);
   value=next;
  }
  Handle(Handle const&)=delete;
  Handle& operator=(Handle const&)=delete;
  bool valid()const{return value&&value!=INVALID_HANDLE_VALUE;}
 };
 try {
  wchar_t module[32768]{};
  DWORD size=::GetModuleFileNameW(
      nullptr,module,static_cast<DWORD>(_countof(module)));
  if(!size||size>=_countof(module))return result;
  const auto helper=(fs::path(module).parent_path()/
      L"FlyShellIsolationHelper.exe").native();
  if(!fs::is_regular_file(fs::path(helper))) {
   result.valid=true;result.indexUnavailable=true;return result;
  }
  SECURITY_ATTRIBUTES sa{sizeof(sa),nullptr,TRUE};
  HANDLE childWriteRaw=nullptr,parentReadRaw=nullptr;
  if(!::CreatePipe(&parentReadRaw,&childWriteRaw,&sa,65536)){
   result.valid=true;result.indexUnavailable=true;return result;
  }
  Handle parentRead(parentReadRaw),childWrite(childWriteRaw);
  ::SetHandleInformation(parentRead.value,HANDLE_FLAG_INHERIT,0);
  Handle childIn(::CreateFileW(L"NUL",GENERIC_READ,
      FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,nullptr));
  Handle childError(::CreateFileW(L"NUL",GENERIC_WRITE,
      FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,nullptr));
  if(!childIn.valid()||!childError.valid())return result;

  SIZE_T bytes=0;
  ::InitializeProcThreadAttributeList(nullptr,1,0,&bytes);
  if(!bytes)return result;
  std::vector<unsigned char> storage(bytes);
  auto* attrs=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(storage.data());
  if(!::InitializeProcThreadAttributeList(attrs,1,0,&bytes))return result;
  HANDLE allowed[]{childIn.value,childWrite.value,childError.value};
  if(!::UpdateProcThreadAttribute(attrs,0,
      PROC_THREAD_ATTRIBUTE_HANDLE_LIST,allowed,sizeof(allowed),nullptr,nullptr)){
   ::DeleteProcThreadAttributeList(attrs);return result;
  }
  STARTUPINFOEXW startup{};
  startup.StartupInfo.cb=sizeof(startup);
  startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
  startup.StartupInfo.hStdInput=childIn.value;
  startup.StartupInfo.hStdOutput=childWrite.value;
  startup.StartupInfo.hStdError=childError.value;
  startup.lpAttributeList=attrs;
  // CreateProcessW does not quote argv for us. Preserve a trailing
  // backslash before the closing quote instead of swallowing that quote.
  auto quoteArg=[](std::wstring const& arg){
   std::wstring quoted=L"\"";
   std::size_t slashes=0;
   for(const wchar_t ch:arg){
    if(ch==L'\\'){++slashes;continue;}
    if(ch==L'"')quoted.append(slashes*2+1,L'\\');
    else quoted.append(slashes,L'\\');
    quoted.push_back(ch);
    slashes=0;
   }
   quoted.append(slashes*2,L'\\');
   quoted.push_back(L'"');
   return quoted;
  };
  std::wstring command=quoteArg(helper)+
      L" --indexed-filename-search "+quoteArg(folder)+
      L" "+quoteArg(query.term);
  // Send explicit empty fields; the child independently validates sizes.
  command+=L" "+quoteArg(
      query.extension.empty()?L"":normalizeExtension(query.extension))+
      L" "+quoteArg(query.minSizeKb)+
      L" "+quoteArg(query.maxSizeKb)+
      L" "+quoteArg(query.modifiedAfter)+
      L" "+quoteArg(query.modifiedBefore);
  std::vector<wchar_t> mutableCommand(command.begin(),command.end());
  mutableCommand.push_back(0);
  PROCESS_INFORMATION created{};
  const BOOL launched=::CreateProcessW(
      helper.c_str(),mutableCommand.data(),nullptr,nullptr,TRUE,
      CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT,
      nullptr,fs::path(helper).parent_path().c_str(),
      &startup.StartupInfo,&created);
  ::DeleteProcThreadAttributeList(attrs);
  if(!launched){
   result.valid=true;result.indexUnavailable=true;return result;
  }
  Handle process(created.hProcess),thread(created.hThread);
  Handle job(::CreateJobObjectW(nullptr,nullptr));
  JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
  limits.BasicLimitInformation.LimitFlags=
      JOB_OBJECT_LIMIT_ACTIVE_PROCESS|JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
  limits.BasicLimitInformation.ActiveProcessLimit=1;
  if(!job.valid()||
     !::SetInformationJobObject(job.value,
         JobObjectExtendedLimitInformation,&limits,sizeof(limits))||
     !::AssignProcessToJobObject(job.value,process.value)){
   ::TerminateProcess(process.value,ERROR_ACCESS_DENIED);
   ::WaitForSingleObject(process.value,250);
   return result;
  }
  if(::ResumeThread(thread.value)==DWORD(-1)){
   ::TerminateJobObject(job.value,ERROR_GEN_FAILURE);
   ::WaitForSingleObject(process.value,250);
   return result;
  }
  childWrite.reset();
  thread.reset();
  childIn.reset();
  childError.reset();

  const auto start=::GetTickCount64();
  auto stop=[&](DWORD why){
   ::TerminateJobObject(job.value,why);
   ::WaitForSingleObject(process.value,250);
  };
  auto readMonitored=[&](void* destination,std::size_t wanted)->bool {
   auto* p=static_cast<unsigned char*>(destination);
   while(wanted){
    if(cancel&&cancel->load()){stop(ERROR_CANCELLED);return false;}
    DWORD available=0;
    if(!::PeekNamedPipe(parentRead.value,nullptr,0,nullptr,&available,nullptr)){
     stop(ERROR_READ_FAULT);return false;
    }
    if(available){
     DWORD count=0;
     const DWORD chunk=static_cast<DWORD>(
         (std::min<std::size_t>)(wanted,available));
     if(!::ReadFile(parentRead.value,p,chunk,&count,nullptr)||!count){
      stop(ERROR_READ_FAULT);return false;
     }
     p+=count;wanted-=count;
     continue;
    }
    if(::GetTickCount64()-start>=12000){
     result.indexTimedOut=true;
     stop(ERROR_TIMEOUT);return false;
    }
    if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0)return false;
    ::Sleep(20);
   }
   return true;
  };
  Header wire{};
  if(!readMonitored(&wire,sizeof(wire))){
   if(cancel&&cancel->load())result.canceled=true;
   else {result.valid=true;result.indexUnavailable=!result.indexTimedOut;}
   return result;
  }
  if(wire.magic!=kMagic||wire.version!=kVersion||
     wire.count>kMaxResults||wire.bytes>kMaxBodyBytes){
   stop(ERROR_INVALID_DATA);return result;
  }
  std::vector<unsigned char> body(wire.bytes);
  if(wire.bytes&&!readMonitored(body.data(),body.size())){
   if(cancel&&cancel->load())result.canceled=true;
   else {result.valid=true;result.indexUnavailable=!result.indexTimedOut;}
   return result;
  }
  if(checksum(body.data(),body.size())!=wire.checksum){
   stop(ERROR_INVALID_DATA);return result;
  }
  if(::WaitForSingleObject(process.value,250)!=WAIT_OBJECT_0){
   stop(ERROR_TIMEOUT);return result;
  }
  DWORD code=1;
  if(!::GetExitCodeProcess(process.value,&code)||code!=0)return result;
  if(wire.status!=ERROR_SUCCESS&&wire.status!=ERROR_MORE_DATA){
   result.valid=true;result.indexUnavailable=true;return result;
  }
  std::size_t position=0;
  for(std::uint32_t i=0;i<wire.count;++i){
   if(position+4>body.size())return result;
   std::uint32_t units=0;
   std::memcpy(&units,body.data()+position,4);
   position+=4;
   if(!units||units>kMaxPathUnits||
      units>(body.size()-position)/sizeof(wchar_t))return result;
   std::wstring path(units,L'\0');
   std::memcpy(path.data(),body.data()+position,
               units*sizeof(wchar_t));
   position+=units*sizeof(wchar_t);
   if(!validScope(path))return result;
   result.matches.push_back(std::move(path));
  }
  if(position!=body.size())return result;
  result.count=result.matches.size();
  result.resultLimited=wire.status==ERROR_MORE_DATA;
  result.truncated=result.resultLimited;
  result.valid=true;
  return result;
 }catch(...){return result;}
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
