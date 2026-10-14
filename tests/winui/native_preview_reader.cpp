// Focused Windows-native test for F03 readVerifiedHandle; test-owned files ONLY.
// This executable never creates a window and never touches user settings.
// Run with: native_preview_reader.exe C:\<precreated-owned-empty-directory>
#include "../../src/base/file_preview_reader.h"
#include "../../src/base/file_preview_safe_open.h"
#include <Windows.h>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <vector>
#include <utility>

bool runPreviewWorkerWireFixture(std::wstring const& path,
                                 std::vector<std::uint8_t> const& bytes);
using fxfile::previewread::Status;
using fxfile::previewpolicy::Kind;
using Clock=std::chrono::steady_clock;

static void check(bool value,char const* why)
{
    if(!value){std::fprintf(stderr,"F03_NATIVE_FAILED %s\n",why);std::exit(1);}
}
static std::wstring joined(std::wstring const& root,wchar_t const* name)
{
    return root+L"\\"+name;
}
static void writeOwned(std::wstring const& path,
                       std::vector<std::uint8_t> const& bytes)
{
    HANDLE file=::CreateFileW(path.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,
                              FILE_ATTRIBUTE_NORMAL,nullptr);
    check(file!=INVALID_HANDLE_VALUE,"create owned fixture");
    DWORD written=0;
    const auto done=bytes.empty() ||
        (!!::WriteFile(file,bytes.data(),static_cast<DWORD>(bytes.size()),
                      &written,nullptr)&&written==bytes.size());
    ::CloseHandle(file);
    check(done,"write owned fixture");
}
static HANDLE opened(std::wstring const& path)
{
    return ::CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,
                         OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
}
static fxfile::previewpolicy::Candidate ownedCandidate(
    std::wstring const& path,std::uint64_t bytes) noexcept
{
    return {path,bytes,true,true,true,false,true};
}
// Candidate stores a wstring_view; passing a temporary would dangle.
static fxfile::previewpolicy::Candidate ownedCandidate(
    std::wstring&&,std::uint64_t)=delete;
static fxfile::previewread::Result read(
    HANDLE h,std::wstring const& path,Kind kind,std::size_t expected,
    std::atomic_bool const& cancel,Clock::time_point deadline)
{
    return fxfile::previewread::readVerifiedHandle(
        h,path,kind,expected,cancel,deadline);
}
int wmain(int argc,wchar_t** argv)
{
    check(argc==2,"requires a pre-created test-owned directory");
    std::wstring root=argv[1];
    check(fxfile::previewpolicy::canonicalLocalPath(root),
          "owned directory path must be canonical");
    const std::wstring text=joined(root,L"owned-text.txt");
    const std::wstring image=joined(root,L"owned-image.png");
    const std::wstring invalid=joined(root,L"invalid-text.txt");
    const std::wstring longtext=joined(root,L"too-large.txt");
    const std::vector<std::uint8_t> data{'f','l','y','\n',0xed,0x95,0x9c};
    writeOwned(text,data);
    writeOwned(image,{0x89,0x50,0x4e,0x47,0x0d,0x0a});
    writeOwned(invalid,{0xc0,0xaf,0x00});
    check(runPreviewWorkerWireFixture(text,data),
          "one-shot worker pipe wire and safe file reads");
    // Create a sparse, bounded fixture at 256 KiB + 1 without allocating
    // a large buffer; never read it into memory.
    {
        HANDLE h=::CreateFileW(longtext.c_str(),GENERIC_WRITE,0,nullptr,
                               CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        check(h!=INVALID_HANDLE_VALUE,"create oversized fixture");
        LARGE_INTEGER bytes{};
        bytes.QuadPart=fxfile::previewpolicy::kMaxTextBytes+1;
        check(!!::SetFilePointerEx(h,bytes,nullptr,FILE_BEGIN)&&
              !!::SetEndOfFile(h),"set owned oversized fixture size");
        ::CloseHandle(h);
    }
    std::atomic_bool cancel{false};
    auto end=Clock::now()+std::chrono::seconds(8);
    HANDLE file=opened(text);
    check(file!=INVALID_HANDLE_VALUE,"open own text");
    auto out=read(file,text,Kind::Text,data.size(),cancel,end);
    check(out.ok()&&out.bytes==data&&out.kind==Kind::Text,"read exact text bytes");
    check(read(file,text+L".wrong",Kind::Text,data.size(),cancel,end).status
          ==Status::UnsafeHandle,"reject mismatched opened path");
    check(read(file,text,Kind::Text,data.size()+1,cancel,end).status
          ==Status::ChangedFile,"reject incorrect metadata size");
    cancel.store(true);
    check(read(file,text,Kind::Text,data.size(),cancel,end).status
          ==Status::Cancelled,"reject cancelled work");
    cancel.store(false);
    check(read(file,text,Kind::Text,data.size(),cancel,
          Clock::now()-std::chrono::seconds(1)).status==Status::Deadline,
          "reject expired work");
    check(read(file,text,Kind::None,data.size(),cancel,end).status
          ==Status::InvalidRequest,"reject unknown format");
    ::CloseHandle(file);

    file=opened(image);
    check(file!=INVALID_HANDLE_VALUE,"open own image");
    out=read(file,image,Kind::Image,6,cancel,end);
    check(out.ok()&&out.bytes.size()==6&&out.bytes[0]==0x89,
          "return bounded opaque image bytes without decoding");
    ::CloseHandle(file);

    file=opened(invalid);
    check(file!=INVALID_HANDLE_VALUE,"open own invalid text");
    check(read(file,invalid,Kind::Text,3,cancel,end).status
          ==Status::InvalidText,"reject invalid UTF8/control bytes");
    ::CloseHandle(file);

    file=opened(longtext);
    check(file!=INVALID_HANDLE_VALUE,"open owned oversized file");
    check(read(file,longtext,Kind::Text,
          fxfile::previewpolicy::kMaxTextBytes+1,cancel,end).status
          ==Status::TooLarge,"refuse oversized request before allocation");
    ::CloseHandle(file);
    check(read(INVALID_HANDLE_VALUE,text,Kind::Text,0,cancel,end).status
          ==Status::InvalidHandle,"reject invalid file handle");
    // A directory handle cannot be previewed even when named on C:.
    HANDLE directory=::CreateFileW(root.c_str(),FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS,nullptr);
    check(directory!=INVALID_HANDLE_VALUE,"open owned directory as directory");
    check(read(directory,root,Kind::Text,0,cancel,end).status
          ==Status::UnsafeHandle,"reject directory handles");
    ::CloseHandle(directory);

    // Safety gate: forged candidate flags must never grant a raw path open.
    const auto nested=joined(root,L"nested");
    const auto nestedFile=joined(nested,L"open-me.txt");
    check(!!::CreateDirectoryW(nested.c_str(),nullptr),"create owned nested dir");
    writeOwned(nestedFile,data);
    {
        auto c=ownedCandidate(nestedFile,data.size());
        auto guarded=fxfile::previewsafe::openLocalRegular(c,cancel,end);
        check(guarded.accepted()&&guarded.lockedAncestors.size()>=2,
              "lock real ancestors and opened local regular handle");
        auto result=read(guarded.file.get(),nestedFile,guarded.kind,
                         guarded.knownBytes,cancel,end);
        check(result.ok()&&result.bytes==data,"consume guarded handle");
        auto changed=ownedCandidate(nestedFile,data.size()+1);
        check(fxfile::previewsafe::openLocalRegular(changed,cancel,end).status
              ==fxfile::previewsafe::Status::Changed,
              "reject forged metadata size at opened handle");
        const auto missingPath=joined(nested,L"missing.txt");
        auto wrong=ownedCandidate(missingPath,1);
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject missing file");
        const std::wstring uncPath=L"\\\\server\\share\\test.txt";
        wrong=ownedCandidate(uncPath,1);
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject UNC");
        const auto adsPath=nestedFile+L":ads";
        wrong=ownedCandidate(adsPath,1);
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject alternate stream");
        const auto traversalPath=nestedFile+L"\\..\\test.txt";
        wrong=ownedCandidate(traversalPath,1);
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject dot-dot path");
        wrong=ownedCandidate(nestedFile, data.size());
        wrong.isLocalFixedDrive=false;
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject forged nonlocal flag");
        wrong=ownedCandidate(nestedFile,data.size());
        wrong.isReparsePoint=true;
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject advertised reparse");
        const auto svgPath=joined(nested,L"payload.svg");
        wrong=ownedCandidate(svgPath,0);
        check(!fxfile::previewsafe::openLocalRegular(wrong,cancel,end).accepted(),
              "reject active file type");
        cancel.store(true);
        check(fxfile::previewsafe::openLocalRegular(c,cancel,end).status
              ==fxfile::previewsafe::Status::Cancelled,
              "reject stale cancelled open");
        cancel.store(false);
        check(fxfile::previewsafe::openLocalRegular(
                  c,cancel,Clock::now()-std::chrono::seconds(1)).status
              ==fxfile::previewsafe::Status::Deadline,
              "reject expired safe-open");
    }
    // Symlinks are optional on locked-down VMs: report NOT_TESTED, never
    // silently mark reparse traversal coverage passed when creation failed.
    {
        const auto symlink=joined(root,L"symlink.txt");
        if(::CreateSymbolicLinkW(symlink.c_str(),nestedFile.c_str(),0x2)){
            auto c=ownedCandidate(symlink,data.size());
            check(!fxfile::previewsafe::openLocalRegular(c,cancel,end).accepted(),
                  "reject leaf symlink");
            check(!!::DeleteFileW(symlink.c_str()),"delete own leaf symlink");
            std::printf("F03_NATIVE_LEAF_SYMLINK_REJECT=PASS\n");
        }else std::printf("F03_NATIVE_LEAF_SYMLINK_REJECT=NOT_TESTED\n");
        const auto linkdir=joined(root,L"linked-dir");
        if(::CreateSymbolicLinkW(linkdir.c_str(),nested.c_str(),0x3)){
            const auto linkedFile=joined(linkdir,L"open-me.txt");
            auto c=ownedCandidate(linkedFile,data.size());
            check(!fxfile::previewsafe::openLocalRegular(c,cancel,end).accepted(),
                  "reject ancestor directory symlink");
            check(!!::RemoveDirectoryW(linkdir.c_str()),
                  "delete own directory symlink");
            std::printf("F03_NATIVE_ANCESTOR_SYMLINK_REJECT=PASS\n");
        }else std::printf("F03_NATIVE_ANCESTOR_SYMLINK_REJECT=NOT_TESTED\n");
    }
    check(!!::DeleteFileW(nestedFile.c_str()),"delete nested owned file");
    check(!!::RemoveDirectoryW(nested.c_str()),"remove nested owned dir");
    std::printf("F03_NATIVE_SAFE_OPEN_AND_GUARDED_READ=PASS\n");
    for(auto const& p:{text,image,invalid,longtext}){
        check(!!::DeleteFileW(p.c_str()),"delete owned fixture");
    }
    std::printf("F03_NATIVE_HANDLE_READ_AND_FAILURE_CONTRACT=PASS\n");
    return 0;
}
