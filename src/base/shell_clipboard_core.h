// Windows file-drop / Preferred DropEffect and quoted-path text bridge.
// Actual OS clipboard reads/writes are ONLY invoked on an explicit user action.
// Owned native tests exercise encode/decode in memory (NEVER touch global clipboard).
#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile::shellclipboard {
struct Payload {
 std::vector<std::wstring> paths;
 bool move=false;
};
bool valid(Payload const&) noexcept;
bool encode(Payload const&,std::vector<unsigned char>&) noexcept;
bool decode(void const*,size_t,Payload&) noexcept;
DWORD write(HWND owner,Payload const&) noexcept;  // affects real OS clipboard
DWORD writePathsText(HWND owner,Payload const&) noexcept; // explicit quoted text copy
DWORD read(Payload&) noexcept;                      // reads real OS clipboard
}
