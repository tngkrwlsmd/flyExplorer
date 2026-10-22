// MFC-free Win32 directory invalidation bridge.
#pragma once
#ifndef FXFILE_BASE_DIRECTORY_CHANGE_BRIDGE_H
#define FXFILE_BASE_DIRECTORY_CHANGE_BRIDGE_H
#include <windows.h>
namespace fxfile { namespace directorychange {
HANDLE open(wchar_t const* directory, bool subtree, DWORD mask) noexcept;
// Preserve the original legacy x86 Multibyte watcher build contract.
HANDLE open(char const* directory, bool subtree, DWORD mask) noexcept;
bool rearm(HANDLE watch) noexcept;
void close(HANDLE watch) noexcept;
constexpr DWORD kFilesAndFolders =
    FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_DIR_NAME |
    FILE_NOTIFY_CHANGE_ATTRIBUTES | FILE_NOTIFY_CHANGE_SIZE |
    FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_SECURITY;
} }
#endif
