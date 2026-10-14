// F03 read-only preview candidate policy, host-independent native probe.
// Build with: c++ -std=c++17 -Wall -Wextra -pedantic -I. tests/winui/native_preview_policy.cpp -o preview-policy-test
#include "../../src/base/file_preview_policy.h"
#include <cassert>
using namespace fxfile::previewpolicy;

constexpr Candidate local(std::wstring_view path, std::uint64_t bytes) noexcept {
    return {path, bytes, true, true, true, false, true};
}
static_assert(canonicalLocalPath(L"C:\\test\\readme.txt"));
static_assert(!canonicalLocalPath(L"\\\\server\\share\\file.txt"));
static_assert(!canonicalLocalPath(L"\\\\?\\C:\\test\\file.txt"));
static_assert(!canonicalLocalPath(L"C:relative.txt"));
static_assert(!canonicalLocalPath(L"C:\\test\\..\\file.txt"));
static_assert(!canonicalLocalPath(L"C:\\test\\.\\file.txt"));
static_assert(!canonicalLocalPath(L"C:\\test\\\\file.txt"));
static_assert(!canonicalLocalPath(L"C:\\test\\file.txt\\"));
static_assert(!canonicalLocalPath(L"C:\\test\\bad:ads.txt"));
static_assert(!canonicalLocalPath(L"C:/test/file.txt"));
static_assert(screen(local(L"C:\\test\\README.TXT", 123)).kind == Kind::Text);
static_assert(screen(local(L"C:\\test\\한글.MD", 0)).kind == Kind::Text);
static_assert(screen(local(L"D:\\images\\IMG.PNG", 1024)).kind == Kind::Image);
static_assert(screen(local(L"C:\\test\\a.jpg", kMaxImageBytes)).accepted());
static_assert(screen(local(L"C:\\test\\a.jpeg", kMaxImageBytes + 1)).rejection
              == Rejection::TooLarge);
static_assert(screen(local(L"C:\\test\\data.txt", kMaxTextBytes)).accepted());
static_assert(screen(local(L"C:\\test\\data.txt", kMaxTextBytes + 1)).rejection
              == Rejection::TooLarge);
static_assert(screen(local(L"C:\\test\\a.svg", 2)).rejection
              == Rejection::UnsupportedType);
static_assert(screen(local(L"C:\\test\\a.pdf", 2)).rejection
              == Rejection::UnsupportedType);
static_assert(kMaxDecodedPixels == 16777216ull);

int main() {
    auto c = local(L"C:\\test\\hello.log", 25);
    assert(screen(c).kind == Kind::Text);
    c.hasKnownSize = false;
    assert(screen(c).rejection == Rejection::UnknownSize);
    c.hasKnownSize = true;
    c.isReparsePoint = true;
    assert(screen(c).rejection == Rejection::Reparse);
    c.isReparsePoint = false;
    c.isRegularFile = false;
    assert(screen(c).rejection == Rejection::NonRegular);
    c.isRegularFile = true;
    c.isLocalFixedDrive = false;
    assert(screen(c).rejection == Rejection::NonLocal);
    c.isLocalFixedDrive = true;
    c.isFilesystem = false;
    assert(screen(c).rejection == Rejection::NonLocal);
    c.isFilesystem = true;
    c.absolutePath = L"\\\\?\\C:\\test\\hello.log";
    assert(screen(c).rejection == Rejection::InvalidPath);
    return 0;
}
