#include "file_preview_reader.h"
#include <algorithm>
#include <limits>
#include <string>
#include <utility>

namespace fxfile::previewread {
namespace {
using Clock=std::chrono::steady_clock;
constexpr std::size_t kChunk=64u*1024u;

bool stopped(std::atomic_bool const& cancelled,Clock::time_point end) noexcept
{
    return cancelled.load(std::memory_order_acquire)||Clock::now()>=end;
}

Status stoppedStatus(std::atomic_bool const& cancelled) noexcept
{
    return cancelled.load(std::memory_order_acquire)?
        Status::Cancelled:Status::Deadline;
}

// Reject binary controls and malformed/overlong UTF-8 before any bytes are
// returned to a text view. No HTML/Markdown active interpretation is allowed.
bool inertUtf8(std::vector<std::uint8_t> const& bytes) noexcept
{
    std::size_t i=0;
    if(bytes.size()>=3 && bytes[0]==0xef && bytes[1]==0xbb &&
       bytes[2]==0xbf)i=3;
    while(i<bytes.size()){
        const std::uint32_t first=bytes[i++];
        std::uint32_t code=0;
        unsigned continuation=0;
        std::uint32_t minimum=0;
        if(first<0x80){code=first;}
        else if(first>=0xc2&&first<=0xdf){
            code=first&0x1f;continuation=1;minimum=0x80;
        }else if(first>=0xe0&&first<=0xef){
            code=first&0x0f;continuation=2;minimum=0x800;
        }else if(first>=0xf0&&first<=0xf4){
            code=first&0x07;continuation=3;minimum=0x10000;
        }else return false;
        if(continuation>bytes.size()-i)return false;
        for(unsigned n=0;n<continuation;++n){
            const std::uint8_t next=bytes[i++];
            if((next&0xc0)!=0x80)return false;
            code=(code<<6)|(next&0x3f);
        }
        if(code<minimum||code>0x10ffff||
           (code>=0xd800&&code<=0xdfff))return false;
        if(code==0||code<0x20 && code!=9 && code!=10 && code!=13 ||
           code==0x7f)return false;
    }
    return true;
}

bool statHandle(HANDLE handle,FILE_STANDARD_INFO& standard,
                FILE_BASIC_INFO& basic) noexcept
{
    return !!::GetFileInformationByHandleEx(
        handle,FileStandardInfo,&standard,sizeof(standard)) &&
        !!::GetFileInformationByHandleEx(
        handle,FileBasicInfo,&basic,sizeof(basic));
}

bool matchesExpectedLocalHandle(HANDLE handle,
                                std::wstring_view expected) noexcept
{
    if(!previewpolicy::canonicalLocalPath(expected) ||
       expected.size()>previewpolicy::kMaxPathUnits ||
       ::GetFileType(handle)!=FILE_TYPE_DISK)return false;

    // Resolve the final *opened handle*, not a path string supplied by a row.
    // Windows supplies \\?\C:\... for a DOS drive or a different prefix
    // (UNC, volume GUID, device) which this conservative reader rejects.
    DWORD required=::GetFinalPathNameByHandleW(
        handle,nullptr,0,FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);
    if(required<8||required>previewpolicy::kMaxPathUnits+4)return false;
    std::wstring actual(required+1,L'\0');
    DWORD got=::GetFinalPathNameByHandleW(
        handle,actual.data(),static_cast<DWORD>(actual.size()),
        FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);
    if(got!=required||actual.compare(0,4,L"\\\\?\\")!=0)return false;
    actual.resize(got);
    std::wstring_view resolved(actual.data()+4,actual.size()-4);
    if(!previewpolicy::canonicalLocalPath(resolved) ||
       resolved.size()!=expected.size() ||
       ::CompareStringOrdinal(resolved.data(),static_cast<int>(resolved.size()),
              expected.data(),static_cast<int>(expected.size()),TRUE)
                  !=CSTR_EQUAL)return false;
    wchar_t volume[4]{resolved[0],L':',L'\\',L'\0'};
    return ::GetDriveTypeW(volume)==DRIVE_FIXED;
}
} // namespace

Result readVerifiedHandle(
    HANDLE file,std::wstring_view expectedAbsolutePath,
    previewpolicy::Kind kind,std::uint64_t expectedBytes,
    std::atomic_bool const& cancelled,Clock::time_point deadline) noexcept
{
    Result failure{};
    auto reject=[&](Status status) noexcept -> Result {
        failure.status=status;
        return std::move(failure);
    };
    try {
        if(kind!=previewpolicy::Kind::Text &&
           kind!=previewpolicy::Kind::Image)
            return reject(Status::InvalidRequest);
        const std::uint64_t bound=kind==previewpolicy::Kind::Text?
            previewpolicy::kMaxTextBytes:previewpolicy::kMaxImageBytes;
        if(expectedBytes>bound)return reject(Status::TooLarge);
        if(file==nullptr||file==INVALID_HANDLE_VALUE)
            return reject(Status::InvalidHandle);
        if(stopped(cancelled,deadline))return reject(stoppedStatus(cancelled));

        FILE_STANDARD_INFO before{};
        FILE_BASIC_INFO beforeBasic{};
        FILE_ATTRIBUTE_TAG_INFO tag{};
        if(!statHandle(file,before,beforeBasic)||
           !::GetFileInformationByHandleEx(file,FileAttributeTagInfo,
                                          &tag,sizeof(tag)))
            return reject(Status::UnsafeHandle);
        if(before.Directory || before.DeletePending ||
           before.EndOfFile.QuadPart<0 ||
           (tag.FileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|
                                FILE_ATTRIBUTE_DIRECTORY|
                                FILE_ATTRIBUTE_OFFLINE))!=0 ||
           !matchesExpectedLocalHandle(file,expectedAbsolutePath))
            return reject(Status::UnsafeHandle);
        if(static_cast<std::uint64_t>(before.EndOfFile.QuadPart)!=expectedBytes)
            return reject(Status::ChangedFile);
        if(!::SetFilePointerEx(file,LARGE_INTEGER{},nullptr,FILE_BEGIN))
            return reject(Status::IoError);
        std::vector<std::uint8_t> payload;
        payload.resize(static_cast<std::size_t>(expectedBytes));
        std::size_t offset=0;
        while(offset<payload.size()){
            if(stopped(cancelled,deadline))return reject(stoppedStatus(cancelled));
            const DWORD count=static_cast<DWORD>((std::min)(
                kChunk,payload.size()-offset));
            DWORD got=0;
            if(!::ReadFile(file,payload.data()+offset,count,&got,nullptr))
                return reject(Status::IoError);
            if(got==0)return reject(Status::ShortRead);
            if(got>count)return reject(Status::IoError);
            offset+=got;
        }
        if(stopped(cancelled,deadline))return reject(stoppedStatus(cancelled));
        FILE_STANDARD_INFO after{};
        FILE_BASIC_INFO afterBasic{};
        if(!statHandle(file,after,afterBasic))
            return reject(Status::IoError);
        if(after.EndOfFile.QuadPart!=before.EndOfFile.QuadPart ||
           afterBasic.LastWriteTime.QuadPart!=beforeBasic.LastWriteTime.QuadPart)
            return reject(Status::ChangedFile);
        if(kind==previewpolicy::Kind::Text && !inertUtf8(payload))
            return reject(Status::InvalidText);
        Result success{};
        success.status=Status::Success;
        success.kind=kind;
        success.bytes=std::move(payload);
        return success;
    }catch(...){
        return reject(Status::IoError);
    }
}
} // namespace fxfile::previewread
