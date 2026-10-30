// Explicit user-only Shell context popup in one exact owned child process.
#pragma once
#include <windows.h>
#include <string>
#include <vector>
namespace fxfile::shellcontext {
inline constexpr std::size_t kMaxContextSelection=32;
inline constexpr std::size_t kMaxContextPathUnits=16*1024;
DWORD show(std::wstring const& helper,
           std::vector<std::wstring> const& selectedLocalPaths,
           POINT screenPoint,DWORD timeoutMs=45000,
           bool propertiesOnly=false) noexcept;
}
