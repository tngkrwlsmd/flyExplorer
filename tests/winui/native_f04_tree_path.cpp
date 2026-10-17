#include "../../app/winui/folder_tree_path.h"
#include <cassert>
#include <iostream>
#include <string>

using namespace fxfile::foldertree;
int main() {
    assert(normalizedDrivePath(L"C:\\"));
    assert(normalizedDrivePath(L"d:\\한글\\테스트 폴더"));
    assert(!normalizedDrivePath(L"C:"));
    assert(!normalizedDrivePath(L"C:relative"));
    assert(!normalizedDrivePath(L"\\\\server\\share"));
    assert(!normalizedDrivePath(L"\\\\?\\C:\\Windows"));
    assert(!normalizedDrivePath(L"C:\\folder\\..\\other"));
    assert(!normalizedDrivePath(L"C:\\folder\\.\\other"));
    assert(!normalizedDrivePath(L"C:\\folder\\\\other"));
    assert(!normalizedDrivePath(L"C:\\folder\\"));
    assert(!normalizedDrivePath(L"C:\\NUL.txt"));
    assert(!safeLeaf(L"COM1"));
    assert(!safeLeaf(L"lPt9.txt"));
    assert(!safeLeaf(L"name. "));
    assert(!safeLeaf(L"bad:file"));
    assert(!safeLeaf(L"folder/name"));
    assert(safeLeaf(L"한글 폴더"));
    std::wstring combined = L"previous";
    assert(childPath(L"D:\\", L"한글 폴더", combined));
    assert(combined == L"D:\\한글 폴더");
    assert(childPath(combined, L"child", combined));
    assert(combined == L"D:\\한글 폴더\\child");
    assert(!childPath(L"C:\\", L"..", combined));
    assert(combined == L"D:\\한글 폴더\\child");
    std::wstring deep = L"C:\\";
    for (std::size_t i = 0; i < kMaxTreeDepth; ++i) {
        assert(childPath(deep, L"part", deep));
    }
    assert(!childPath(deep, L"overflow", combined));
    assert(!normalizedDrivePath(std::wstring(L"C:\\") + std::wstring(kMaxPathUnits, L'x')));
    RequestIdentity current{0, 3, 42, 9};
    assert(accepts(current, current));
    assert(!accepts(current, RequestIdentity{1,3,42,9}));
    assert(!accepts(current, RequestIdentity{0,4,42,9}));
    assert(!accepts(current, RequestIdentity{0,3,43,9}));
    assert(!accepts(current, RequestIdentity{0,3,42,10}));
    assert(!accepts(RequestIdentity{0,3,0,9}, RequestIdentity{0,3,0,9}));
    std::cout << "F04_TREE_PATH_NATIVE_PASS\n";
}
