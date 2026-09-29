// M2.3 private, opt-in saved WinUI session. No legacy MFC config read/write.
#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile::previewsession {
struct Session {
 bool split=true;
 std::array<std::vector<std::wstring>,2> paths;
 std::array<std::uint32_t,2> selected{{0,0}},sort{{0,0}};
 std::uint32_t width=1160,height=760,splitPermille=500,activeSide=0;
};
std::wstring privatePath();
bool valid(Session const&) noexcept; // only existing local, non-reparse dirs
bool save(Session const&) noexcept;  // atomic same-directory private write
bool load(Session&) noexcept;        // strict bounded versioned read
bool clear() noexcept;               // explicit private-session deletion only
}
