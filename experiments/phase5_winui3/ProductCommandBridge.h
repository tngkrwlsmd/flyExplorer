#pragma once
#include <windows.h>
#include "../../src/fxfile/resource.h"
#include <string>
#include <cwchar>
#include <cstdint>

// Experiment-only transport: UI sends scalar, timeout-protected WM_COMMAND to
// an explicitly supplied test-owned flyExplorer MainFrame. Existing product
// routes commands through its real CommandContext and ExplorerCtrl. No user
// product process is discovered automatically and no pointers cross processes.
struct ProductCommandBridge {
    HWND mainWindow{};
    DWORD testProcessId{};

    bool Attach(DWORD pid, HWND hwnd) {
        if (!pid || !hwnd || !::IsWindow(hwnd) ||
            ::GetAncestor(hwnd, GA_ROOT) != hwnd) return false;
        DWORD actualPid{};
        ::GetWindowThreadProcessId(hwnd, &actualPid);
        if (pid != actualPid) return false;
        wchar_t path[32768]{};
        DWORD length = static_cast<DWORD>(_countof(path));
        HANDLE process = ::OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
        if (!process) return false;
        const BOOL queried = ::QueryFullProcessImageNameW(process, 0, path, &length);
        ::CloseHandle(process);
        if (!queried) return false;
        const wchar_t* basename = ::wcsrchr(path, L'\\');
        basename = basename ? basename + 1 : path;
        if (_wcsicmp(basename, L"fxfile.exe") != 0) return false;
        wchar_t title[512]{};
        if (!::GetWindowTextW(hwnd, title, _countof(title))) return false;
        const std::wstring name{title};
        if (name.size() < 9 || name.substr(name.size() - 9) != L" - fxfile") return false;
        mainWindow = hwnd;
        testProcessId = pid;
        return true;
    }

    bool Connected() const {
        if (!mainWindow || !::IsWindow(mainWindow)) return false;
        DWORD pid{};
        ::GetWindowThreadProcessId(mainWindow, &pid);
        return pid == testProcessId;
    }

    std::wstring ProductTitle() const {
        if (!Connected()) return L"[isolated product unavailable]";
        wchar_t title[1024]{};
        ::GetWindowTextW(mainWindow, title, _countof(title));
        return title;
    }

    bool SendNavCommand(std::uint32_t id) const {
        // Command IDs taken from actual src/fxfile/resource.h.
        if ((id != ID_GO_UP && id != ID_GO_BACK && id != ID_GO_FORWARD) || !Connected()) return false;
        DWORD_PTR result{};
        const LRESULT sent = ::SendMessageTimeoutW(mainWindow, WM_COMMAND,
                 MAKEWPARAM(id, 0), 0, SMTO_ABORTIFHUNG | SMTO_BLOCK,
                 2200, &result);
        return sent != 0 && result != 0;
    }
};
