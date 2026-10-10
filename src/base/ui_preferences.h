// M2.1: private, opt-in WinUI preview settings. Never touches MFC fxfile/conf.
#pragma once
#include <string>
namespace fxfile::uisettings {
enum class Theme { System, Light, Dark };
// Focus-only Ctrl shortcuts use the closed key set [L, E, F, K].
inline constexpr bool validFocusShortcuts(int address,int search) noexcept {
    return address>=0&&address<4&&search>=0&&search<4&&address!=search;
}
struct Preferences {
    Theme theme=Theme::System;
    std::wstring language=L"ko-KR";
    int defaultViewMode=0;
    int addressShortcut=0;
    int searchShortcut=2;
};
std::wstring privatePath();
bool load(Preferences& out) noexcept; // missing/malformed -> ko-KR/System
bool save(Preferences const& value) noexcept; // new same-dir temp + atomic replace
}
