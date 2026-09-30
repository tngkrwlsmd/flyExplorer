// Explicit user-only Shell context popup in one exact owned child process.
#pragma once
#include <windows.h>
#include <string>
namespace fxfile::shellcontext {
DWORD show(std::wstring const& helper,
           std::wstring const& selectedLocalPath,
           POINT screenPoint,DWORD timeoutMs=45000) noexcept;
}
