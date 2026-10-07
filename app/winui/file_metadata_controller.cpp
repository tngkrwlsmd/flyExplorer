#include "pch.h"
#include "file_metadata_controller.h"
#include "../../src/base/file_metadata_wire.h"
#include "../../src/base/shell_isolation_wire.h"
#include <algorithm>
#include <array>
#include <cwchar>
#include <cwctype>
#include <cstring>
#include <filesystem>
#include <limits>
#include <thread>
#include <utility>
#include <vector>

namespace fxfile::previewmetadata {
namespace {

constexpr DWORD kNetworkMetadataInactivityMs=5000;
constexpr DWORD kNetworkMetadataCancelGraceMs=1200;
constexpr DWORD kNetworkMetadataExitGraceMs=1200;
constexpr DWORD kNetworkMetadataPollMs=20;

struct Handle final {
    HANDLE value=nullptr;
    Handle()=default;
    explicit Handle(HANDLE handle):value(handle){}
    ~Handle(){reset();}
    Handle(Handle const&)=delete;
    Handle& operator=(Handle const&)=delete;
    void reset(HANDLE handle=nullptr) noexcept {
        if(value&&value!=INVALID_HANDLE_VALUE)::CloseHandle(value);
        value=handle;
    }
    bool valid() const noexcept {
        return value&&value!=INVALID_HANDLE_VALUE;
    }
};

std::wstring typeKey(std::wstring const& path,bool folder)
{
    if(folder)return L"";
    auto ext=std::filesystem::path(path).extension().native();
    std::transform(ext.begin(),ext.end(),ext.begin(),[](wchar_t c){
        return static_cast<wchar_t>(::towlower(c));
    });
    return ext;
}

std::wstring sizeLabel(std::uint64_t bytes)
{
    return bytes<1024?
        std::to_wstring(bytes)+L" B":
        bytes<1048576?
        std::to_wstring(bytes/1024)+L" KB":
        std::to_wstring(bytes/1048576)+L" MB";
}

std::wstring dateLabel(FILETIME const& value)
{
    FILETIME local{};
    SYSTEMTIME stamp{};
    if(!::FileTimeToLocalFileTime(&value,&local)||
       !::FileTimeToSystemTime(&local,&stamp))return {};
    wchar_t text[32]{};
    if(std::swprintf(
         text,32,L"%04u-%02u-%02u %02u:%02u",
         static_cast<unsigned>(stamp.wYear),
         static_cast<unsigned>(stamp.wMonth),
         static_cast<unsigned>(stamp.wDay),
         static_cast<unsigned>(stamp.wHour),
         static_cast<unsigned>(stamp.wMinute))<=0)return {};
    return text;
}

void applyRaw(
    fxfile::previewlist::FileMetadata& entry,
    std::wstring const& path,DWORD attributes,
    std::uint64_t bytes,std::uint64_t modified)
{
    const bool folder=(attributes&FILE_ATTRIBUTE_DIRECTORY)!=0;
    entry.typeKey=typeKey(path,folder);
    if(!folder){
        entry.bytes=bytes;
        entry.bytesLabel=sizeLabel(bytes);
        entry.sizeKnown=true;
    }
    entry.modified=modified;
    entry.dateKnown=modified!=0;
    if(entry.dateKnown){
        ULARGE_INTEGER stamp{};
        stamp.QuadPart=modified;
        FILETIME value{};
        value.dwHighDateTime=stamp.HighPart;
        value.dwLowDateTime=stamp.LowPart;
        entry.dateLabel=dateLabel(value);
    }
}

bool writeAll(HANDLE handle,void const* data,std::size_t bytes) noexcept
{
    auto const* current=static_cast<unsigned char const*>(data);
    while(bytes){
        const auto chunk=static_cast<DWORD>((std::min)(
            bytes,std::size_t{64*1024}));
        DWORD written=0;
        if(!::WriteFile(handle,current,chunk,&written,nullptr)||!written)
            return false;
        current+=written;
        bytes-=written;
    }
    return true;
}

bool readAll(HANDLE handle,void* data,std::size_t bytes) noexcept
{
    auto* current=static_cast<unsigned char*>(data);
    while(bytes){
        const auto chunk=static_cast<DWORD>((std::min)(
            bytes,std::size_t{64*1024}));
        DWORD got=0;
        if(!::ReadFile(handle,current,chunk,&got,nullptr)||!got)
            return false;
        current+=got;
        bytes-=got;
    }
    return true;
}

bool appendBytes(
    std::vector<unsigned char>& body,void const* data,std::size_t bytes)
{
    if(bytes>fxfile::metadatawire::kMaxBodyBytes||
       body.size()>fxfile::metadatawire::kMaxBodyBytes-bytes)return false;
    auto const* first=static_cast<unsigned char const*>(data);
    body.insert(body.end(),first,first+bytes);
    return true;
}

bool appendU32(std::vector<unsigned char>& body,std::uint32_t value)
{
    return appendBytes(body,&value,sizeof(value));
}

bool serializeNetworkRequest(
    std::vector<std::wstring> const& paths,
    fxfile::metadatawire::RequestHeader& header,
    std::vector<unsigned char>& body) noexcept
{
    try{
        if(paths.empty()||
           paths.size()>fxfile::metadatawire::kMaxItems)return false;
        body.clear();
        std::size_t pathUnits=0;
        for(auto const& path:paths){
            if(path.size()>32000||
               path.size()>fxfile::metadatawire::kMaxPathUnits-pathUnits)
                return false;
            pathUnits+=path.size();
            if(!appendU32(body,static_cast<std::uint32_t>(path.size()))||
               (!path.empty()&&!appendBytes(
                    body,path.data(),path.size()*sizeof(wchar_t))))
                return false;
        }
        header.magic=fxfile::metadatawire::kMagic;
        header.version=fxfile::metadatawire::kVersion;
        header.count=static_cast<std::uint32_t>(paths.size());
        header.bodyBytes=static_cast<std::uint32_t>(body.size());
        header.checksum=fxfile::metadatawire::checksum(
            body.data(),body.size());
        return true;
    }catch(...){
        body.clear();
        return false;
    }
}

bool helperPath(std::wstring& result) noexcept
{
    result.clear();
    try{
        std::array<wchar_t,32768> module{};
        const auto length=::GetModuleFileNameW(
            nullptr,module.data(),static_cast<DWORD>(module.size()));
        if(!length||length>=module.size())return false;
        auto helper=std::filesystem::path(
            std::wstring(module.data(),length)).parent_path()/
            L"FlyShellIsolationHelper.exe";
        const auto attributes=::GetFileAttributesW(helper.c_str());
        if(attributes==INVALID_FILE_ATTRIBUTES||
           (attributes&FILE_ATTRIBUTE_DIRECTORY))return false;
        result=helper.native();
        return true;
    }catch(...){
        return false;
    }
}

std::uint32_t collectNetworkMetadata(
    std::vector<std::wstring> const& paths,
    std::shared_ptr<std::atomic_bool> const& cancelToken,
    std::vector<fxfile::previewlist::FileMetadata>& metadata) noexcept
{
    metadata.assign(paths.size(),{});
    if(cancelToken&&cancelToken->load())return ERROR_CANCELLED;
    if(paths.empty())return ERROR_SUCCESS;

    fxfile::metadatawire::RequestHeader request{};
    std::vector<unsigned char> body;
    if(!serializeNetworkRequest(paths,request,body))
        return ERROR_INVALID_PARAMETER;

    std::wstring helper;
    if(!helperPath(helper))return ERROR_FILE_NOT_FOUND;

    SECURITY_ATTRIBUTES inheritable{
        sizeof(SECURITY_ATTRIBUTES),nullptr,TRUE};
    HANDLE childInputRaw=nullptr,hostInputRaw=nullptr;
    HANDLE hostOutputRaw=nullptr,childOutputRaw=nullptr;
    if(!::CreatePipe(&childInputRaw,&hostInputRaw,&inheritable,131072))
        return ::GetLastError();
    Handle childInput(childInputRaw),hostInput(hostInputRaw);
    if(!::SetHandleInformation(hostInput.value,HANDLE_FLAG_INHERIT,0))
        return ::GetLastError();
    if(!::CreatePipe(&hostOutputRaw,&childOutputRaw,&inheritable,131072))
        return ::GetLastError();
    Handle hostOutput(hostOutputRaw),childOutput(childOutputRaw);
    if(!::SetHandleInformation(hostOutput.value,HANDLE_FLAG_INHERIT,0))
        return ::GetLastError();

    Handle childError(::CreateFileW(
        L"NUL",GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,
        &inheritable,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr));
    if(!childError.valid())return ::GetLastError();
    Handle cancelEvent(::CreateEventW(&inheritable,TRUE,FALSE,nullptr));
    if(!cancelEvent.valid())return ::GetLastError();
    request.cancelHandle=static_cast<std::uint64_t>(
        reinterpret_cast<std::uintptr_t>(cancelEvent.value));

    SIZE_T attributeBytes=0;
    ::InitializeProcThreadAttributeList(nullptr,1,0,&attributeBytes);
    if(!attributeBytes)return ERROR_INVALID_PARAMETER;
    std::vector<unsigned char> attributeStorage(attributeBytes);
    auto* attributes=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(
        attributeStorage.data());
    if(!::InitializeProcThreadAttributeList(
        attributes,1,0,&attributeBytes))return ::GetLastError();

    const HANDLE inherited[]={
        childInput.value,childOutput.value,childError.value,cancelEvent.value};
    if(!::UpdateProcThreadAttribute(
        attributes,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
        const_cast<HANDLE*>(inherited),sizeof(inherited),nullptr,nullptr)){
        const auto error=::GetLastError();
        ::DeleteProcThreadAttributeList(attributes);
        return error;
    }

    STARTUPINFOEXW startup{};
    startup.StartupInfo.cb=sizeof(startup);
    startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput=childInput.value;
    startup.StartupInfo.hStdOutput=childOutput.value;
    startup.StartupInfo.hStdError=childError.value;
    startup.lpAttributeList=attributes;
    std::wstring command=L"\""+helper+L"\" --file-metadata";
    std::vector<wchar_t> mutableCommand(command.begin(),command.end());
    mutableCommand.push_back(0);
    PROCESS_INFORMATION info{};
    const BOOL created=::CreateProcessW(
        helper.c_str(),mutableCommand.data(),nullptr,nullptr,TRUE,
        CREATE_NO_WINDOW|CREATE_SUSPENDED|EXTENDED_STARTUPINFO_PRESENT,
        nullptr,std::filesystem::path(helper).parent_path().c_str(),
        &startup.StartupInfo,&info);
    const auto createError=::GetLastError();
    ::DeleteProcThreadAttributeList(attributes);
    if(!created)return createError;

    Handle process(info.hProcess),thread(info.hThread);
    Handle job(::CreateJobObjectW(nullptr,nullptr));
    if(!job.valid()){
        const auto error=::GetLastError();
        ::TerminateProcess(process.value,error);
        ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
        return error;
    }
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags=
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|JOB_OBJECT_LIMIT_ACTIVE_PROCESS;
    limits.BasicLimitInformation.ActiveProcessLimit=1;
    if(!::SetInformationJobObject(
          job.value,JobObjectExtendedLimitInformation,&limits,sizeof(limits))||
       !::AssignProcessToJobObject(job.value,process.value)){
        const auto error=::GetLastError();
        ::TerminateProcess(process.value,error);
        ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
        return error;
    }
    if(::ResumeThread(thread.value)==DWORD(-1)){
        const auto error=::GetLastError();
        ::TerminateJobObject(job.value,error);
        ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
        return error;
    }
    thread.reset();
    childInput.reset();
    childOutput.reset();
    childError.reset();

    if(!writeAll(hostInput.value,&request,sizeof(request))||
       (!body.empty()&&!writeAll(hostInput.value,body.data(),body.size()))){
        ::TerminateJobObject(job.value,ERROR_WRITE_FAULT);
        ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
        return ERROR_WRITE_FAULT;
    }
    hostInput.reset();

    std::size_t received=0;
    auto lastProgress=::GetTickCount64();
    bool cancelSignaled=false;
    ULONGLONG cancelStarted=0;
    while(received<paths.size()){
        if(cancelToken&&cancelToken->load()&&!cancelSignaled){
            ::SetEvent(cancelEvent.value);
            cancelStarted=::GetTickCount64();
            cancelSignaled=true;
        }
        if(cancelSignaled&&
           ::GetTickCount64()-cancelStarted>=kNetworkMetadataCancelGraceMs&&
           ::WaitForSingleObject(process.value,0)!=WAIT_OBJECT_0){
            ::TerminateJobObject(job.value,ERROR_CANCELLED);
            ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
            return ERROR_CANCELLED;
        }

        DWORD available=0;
        if(!::PeekNamedPipe(
             hostOutput.value,nullptr,0,nullptr,&available,nullptr)){
            if(cancelSignaled)return ERROR_CANCELLED;
            return ::GetLastError();
        }
        if(available>=sizeof(fxfile::metadatawire::Record)){
            fxfile::metadatawire::Record record{};
            if(!readAll(hostOutput.value,&record,sizeof(record))||
               record.magic!=fxfile::metadatawire::kMagic||
               record.version!=fxfile::metadatawire::kVersion||
               record.index!=received){
                ::TerminateJobObject(job.value,ERROR_INVALID_DATA);
                ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
                return ERROR_INVALID_DATA;
            }
            if(record.valid){
                applyRaw(
                    metadata[received],paths[received],
                    record.attributes,record.bytes,record.modified);
            }
            ++received;
            lastProgress=::GetTickCount64();
            continue;
        }

        if(::WaitForSingleObject(process.value,0)==WAIT_OBJECT_0)break;
        if(::GetTickCount64()-lastProgress>=kNetworkMetadataInactivityMs){
            ::TerminateJobObject(job.value,ERROR_TIMEOUT);
            ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
            return ERROR_TIMEOUT;
        }
        ::Sleep(kNetworkMetadataPollMs);
    }

    if(received!=paths.size()){
        if(cancelSignaled)return ERROR_CANCELLED;
        return ERROR_GEN_FAILURE;
    }
    if(::WaitForSingleObject(
         process.value,kNetworkMetadataExitGraceMs)!=WAIT_OBJECT_0){
        ::TerminateJobObject(job.value,ERROR_TIMEOUT);
        ::WaitForSingleObject(process.value,kNetworkMetadataExitGraceMs);
        return ERROR_TIMEOUT;
    }
    DWORD exitCode=ERROR_GEN_FAILURE;
    if(!::GetExitCodeProcess(process.value,&exitCode))
        return ::GetLastError();
    return exitCode==0?ERROR_SUCCESS:ERROR_GEN_FAILURE;
}

void collectLocalMetadata(
    std::vector<std::wstring> const& paths,
    std::shared_ptr<std::atomic_bool> const& cancelToken,
    std::vector<fxfile::previewlist::FileMetadata>& metadata)
{
    metadata.assign(paths.size(),{});
    for(std::size_t i=0;i<paths.size();++i){
        if(cancelToken->load())return;
        auto const& path=paths[i];
        if(path.empty()||path.size()>32000)continue;
        WIN32_FILE_ATTRIBUTE_DATA data{};
        if(!::GetFileAttributesExW(
             path.c_str(),GetFileExInfoStandard,&data))continue;
        if(data.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)continue;
        const auto bytes=(static_cast<std::uint64_t>(
            data.nFileSizeHigh)<<32)|data.nFileSizeLow;
        ULARGE_INTEGER timestamp{};
        timestamp.HighPart=data.ftLastWriteTime.dwHighDateTime;
        timestamp.LowPart=data.ftLastWriteTime.dwLowDateTime;
        applyRaw(metadata[i],path,data.dwFileAttributes,
                 bytes,timestamp.QuadPart);
    }
}

} // namespace

FileMetadataController::~FileMetadataController(){prepareForClose();}

void FileMetadataController::cancel(int side) noexcept
{
    if(side<0||side>=static_cast<int>(cancel_.size()))return;
    auto& current=cancel_[static_cast<std::size_t>(side)];
    if(current)current->store(true);
    current.reset();
}

void FileMetadataController::prepareForClose() noexcept
{
    closing_.store(true);
    for(int side=0;side<static_cast<int>(cancel_.size());++side)cancel(side);
}

bool FileMetadataController::start(
    Request request,Post post,CompletionCallback completion)
{
    if(closing_.load()||request.side<0||
       request.side>=static_cast<int>(cancel_.size())||
       request.route==0||request.ticket==0||
       request.paths.size()>fxfile::isolation::kMaxCompleteModelEntries||
       !post||!completion)return false;
    const int side=request.side;
    cancel(side);
    auto cancelToken=std::make_shared<std::atomic_bool>(false);
    cancel_[static_cast<std::size_t>(side)]=cancelToken;
    try{
        std::thread([
            request=std::move(request),cancelToken,
            post=std::move(post),completion=std::move(completion)]() mutable {
            Completion result{};
            result.side=request.side;
            result.tab=request.tab;
            result.route=request.route;
            result.ticket=request.ticket;
            if(request.isolatedNetwork){
                result.error=collectNetworkMetadata(
                    request.paths,cancelToken,result.metadata);
                if(result.error==ERROR_CANCELLED)return;
            }else{
                collectLocalMetadata(
                    request.paths,cancelToken,result.metadata);
                if(cancelToken->load())return;
            }
            try{
                post([completion=std::move(completion),
                      result=std::move(result)]() mutable {
                    completion(std::move(result));
                });
            }catch(...){}
        }).detach();
    }catch(...){
        cancel_[static_cast<std::size_t>(side)].reset();
        return false;
    }
    return true;
}

} // namespace fxfile::previewmetadata
