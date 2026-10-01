// M2.1: private, opt-in WinUI preview settings. Never touches MFC fxfile/conf.
#pragma once
#include <string>
namespace fxfile::uisettings {
enum class Theme { System, Light, Dark };
struct Preferences { Theme theme=Theme::System; std::wstring language=L"ko-KR"; };
std::wstring privatePath();
bool load(Preferences& out) noexcept; // missing/malformed -> ko-KR/System
bool save(Preferences const& value) noexcept; // new same-dir temp + atomic replace
}
