#include "file_preview_safe_open.h"
#include <algorithm>
#include <string>
#include <utility>

namespace fxfile::previewsafe {
namespace {
using Clock=std::chrono::steady_clock;

Status interrupted(std::atomic_bool const& cancelled,
                   Clock::time_point deadline) noexcept {
    if(cancelled.load(std::memory_order_acquire))return Status::Cancelled;
    if(Clock::now()>=deadline)return Status::Deadline;
    return Status::Accepted;
}

bool sameOpenedDosPath(HANDLE file,std::wstring_view expected) {
    const DWORD flags=FILE_NAME_NORMALIZED|VOLUME_NAME_DOS;
    const DWORD required=::GetFinalPathNameByHandleW(file,nullptr,0,flags);
    if(required<8||required>previewpolicy::kMaxPathUnits+5)return false;
    std::wstring buffer(static_cast<std::size_t>(required)+1,L'\0');
    const DWORD got=::GetFinalPathNameByHandleW(
        file,buffer.data(),static_cast<DWORD>(buffer.size()),flags);
    if(!got||got+1!=required||
       buffer.compare(0,4,L"\\\\?\\")!=0)return false;
    const std::wstring_view resolved(buffer.data()+4,got-4);
    if(resolved.size()!=expected.size())return false;
    return ::CompareStringOrdinal(resolved.data(),static_cast<int>(resolved.size()),
                                  expected.data(),static_cast<int>(expected.size()),
                                  TRUE)==CSTR_EQUAL;
}

bool safeAttributes(HANDLE h,bool directory,
                    FILE_ID_INFO& identity) noexcept {
    if(::GetFileType(h)!=FILE_TYPE_DISK)return false;
    FILE_ATTRIBUTE_TAG_INFO tag{};
    FILE_STANDARD_INFO standard{};
    if(!::GetFileInformationByHandleEx(
            h,FileAttributeTagInfo,&tag,sizeof(tag)) ||
       !::GetFileInformationByHandleEx(
            h,FileStandardInfo,&standard,sizeof(standard)) ||
       !::GetFileInformationByHandleEx(
            h,FileIdInfo,&identity,sizeof(identity)))return false;
    if((tag.FileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|
                            FILE_ATTRIBUTE_OFFLINE))!=0 ||
       standard.DeletePending)return false;
    if(directory){
        return standard.Directory &&
            (tag.FileAttributes&FILE_ATTRIBUTE_DIRECTORY)!=0;
    }
    return !standard.Directory &&
        (tag.FileAttributes&FILE_ATTRIBUTE_DIRECTORY)==0 &&
        standard.EndOfFile.QuadPart>=0;
}

UniqueHandle openPath(std::wstring const& path,bool directory) {
    // Canonical path is reviewed before entering this helper. The internal
    // \\?\ prefix allows long *local* paths without changing their meaning.
    const std::wstring extended=L"\\\\?\\"+path;
    DWORD access=FILE_READ_ATTRIBUTES;
    DWORD flags=FILE_FLAG_OPEN_REPARSE_POINT;
    if(directory){
        flags|=FILE_FLAG_BACKUP_SEMANTICS;
    }else{
        access|=FILE_READ_DATA;
        flags|=FILE_FLAG_SEQUENTIAL_SCAN;
    }
    return UniqueHandle(::CreateFileW(extended.c_str(),access,
        FILE_SHARE_READ,nullptr,OPEN_EXISTING,flags,nullptr));
}
} // namespace

Result openLocalRegular(
    previewpolicy::Candidate const& candidate,
    std::atomic_bool const& cancelled,
    Clock::time_point deadline) noexcept
{
    Result rejected{};
    try {
        // Own the request path before *any* policy decision so the policy
        // and the eventual opened path cannot observe different buffers.
        if(candidate.absolutePath.size()>previewpolicy::kMaxPathUnits)
            return rejected;
        const std::wstring path(candidate.absolutePath);
        auto stable=candidate;
        stable.absolutePath=path;
        const auto policy=previewpolicy::screen(stable);
        if(!policy.accepted())return rejected;
        const auto interrupt=interrupted(cancelled,deadline);
        if(interrupt!=Status::Accepted){
            rejected.status=interrupt;
            return rejected;
        }
        if(!previewpolicy::canonicalLocalPath(path)){
            rejected.status=Status::InvalidPath;
            return rejected;
        }
        const wchar_t rootText[]{path[0],L':',L'\\',L'\0'};
        if(::GetDriveTypeW(rootText)!=DRIVE_FIXED){
            rejected.status=Status::NonLocal;
            return rejected;
        }
        Result opened{};
        opened.kind=policy.kind;
        opened.knownBytes=candidate.knownBytes;
        opened.lockedAncestors.reserve(8);

        std::wstring current(rootText);
        auto dir=openPath(current,true);
        FILE_ID_INFO rootIdentity{};
        if(!dir||!sameOpenedDosPath(dir.get(),current)||
           !safeAttributes(dir.get(),true,rootIdentity)){
            rejected.status=Status::NonLocal;
            return rejected;
        }
        opened.lockedAncestors.push_back(std::move(dir));
        std::size_t cursor=3;
        while(cursor<path.size()){
            const auto stop=interrupted(cancelled,deadline);
            if(stop!=Status::Accepted){
                rejected.status=stop;
                return rejected;
            }
            const auto slash=path.find(L'\\',cursor);
            const bool last=slash==std::wstring::npos;
            const auto length=(last?path.size():slash)-cursor;
            if(length==0||length>255){
                rejected.status=Status::InvalidPath;
                return rejected;
            }
            if(current.back()!=L'\\')current.push_back(L'\\');
            current.append(path,cursor,length);
            if(!last&&opened.lockedAncestors.size()>=kMaxAncestors){
                rejected.status=Status::TooDeep;
                return rejected;
            }
            auto part=openPath(current,!last);
            FILE_ID_INFO id{};
            if(!part){
                rejected.status=Status::IoError;
                return rejected;
            }
            if(!sameOpenedDosPath(part.get(),current)||
               !safeAttributes(part.get(),!last,id)||
               id.VolumeSerialNumber!=rootIdentity.VolumeSerialNumber){
                rejected.status=Status::Reparse;
                return rejected;
            }
            if(last){
                FILE_STANDARD_INFO standard{};
                if(!::GetFileInformationByHandleEx(part.get(),FileStandardInfo,
                                                  &standard,sizeof(standard))){
                    rejected.status=Status::IoError;
                    return rejected;
                }
                if(static_cast<std::uint64_t>(standard.EndOfFile.QuadPart)!=
                   candidate.knownBytes){
                    rejected.status=Status::Changed;
                    return rejected;
                }
                opened.file=std::move(part);
                break;
            }
            opened.lockedAncestors.push_back(std::move(part));
            cursor=slash+1;
        }
        if(!opened.file){
            rejected.status=Status::InvalidPath;
            return rejected;
        }
        const auto stop=interrupted(cancelled,deadline);
        if(stop!=Status::Accepted){
            rejected.status=stop;
            return rejected;
        }
        opened.status=Status::Accepted;
        return opened;
    }catch(...){
        rejected.status=Status::IoError;
        return rejected;
    }
}

} // namespace fxfile::previewsafe
