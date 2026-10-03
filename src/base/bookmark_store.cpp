#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlobj.h>
#include "bookmark_store.h"
#include <algorithm>
#include <array>
#include <cwctype>
#include <map>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#pragma comment(lib, "shell32.lib")
#pragma comment(lib, "ole32.lib")

namespace fxfile::bookmarks {
namespace {

std::wstring directory()
{
    std::array<wchar_t, 32768> buffer{};
    const auto count = ::GetEnvironmentVariableW(
        L"LOCALAPPDATA", buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!count || count >= buffer.size()) return {};
    return std::wstring(buffer.data(), count) + L"\\flyExplorer";
}

bool hasForbidden(std::wstring const& value)
{
    return value.find_first_of(L"\r\n\t") != std::wstring::npos ||
           value.find(L'\0') != std::wstring::npos;
}

bool validName(std::wstring const& name)
{
    if (name.empty() || name.size() > Store::kMaxName || hasForbidden(name))
        return false;
    return std::any_of(name.begin(), name.end(),
        [](wchar_t ch) { return !std::iswspace(ch); });
}

std::wstring normalizePath(std::wstring path)
{
    std::replace(path.begin(), path.end(), L'/', L'\\');
    while (path.size() > 3 && path.back() == L'\\') path.pop_back();
    return path;
}

bool validPath(std::wstring const& path)
{
    if (path.size() < 3 || path.size() > Store::kMaxPath || hasForbidden(path) ||
        path.find(L'"') != std::wstring::npos)
        return false;
    const bool drive = std::iswalpha(path[0]) && path[1] == L':' &&
                       path[2] == L'\\';
    const bool unc = path.size() > 4 && path[0] == L'\\' &&
                     path[1] == L'\\' && path[2] != L'\\';
    return drive || unc;
}

bool samePath(std::wstring const& a, std::wstring const& b)
{
    return ::CompareStringOrdinal(
        a.c_str(), static_cast<int>(a.size()),
        b.c_str(), static_cast<int>(b.size()), TRUE) == CSTR_EQUAL;
}

bool readBytes(std::wstring const& path, std::size_t maximum,
               std::vector<unsigned char>& bytes)
{
    HANDLE handle = ::CreateFileW(path.c_str(), GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (handle == INVALID_HANDLE_VALUE) return false;

    LARGE_INTEGER length{};
    const bool sized = ::GetFileSizeEx(handle, &length) != FALSE &&
        length.QuadPart >= 0 &&
        static_cast<unsigned long long>(length.QuadPart) <= maximum;
    if (!sized) {
        ::CloseHandle(handle);
        return false;
    }

    bytes.assign(static_cast<std::size_t>(length.QuadPart), 0);
    DWORD read = 0;
    const bool good = bytes.empty() ||
        (::ReadFile(handle, bytes.data(), static_cast<DWORD>(bytes.size()),
                    &read, nullptr) != FALSE &&
         read == bytes.size());
    ::CloseHandle(handle);
    return good;
}

bool utf8ToWide(std::string const& input, std::wstring& output)
{
    output.clear();
    if (input.empty()) return true;
    const int needed = ::MultiByteToWideChar(
        CP_UTF8, MB_ERR_INVALID_CHARS, input.data(),
        static_cast<int>(input.size()), nullptr, 0);
    if (needed <= 0) return false;
    output.resize(static_cast<std::size_t>(needed));
    return ::MultiByteToWideChar(
        CP_UTF8, MB_ERR_INVALID_CHARS, input.data(),
        static_cast<int>(input.size()), output.data(), needed) == needed;
}

bool wideToUtf8(std::wstring const& input, std::string& output)
{
    output.clear();
    if (input.empty()) return true;
    const int needed = ::WideCharToMultiByte(
        CP_UTF8, WC_ERR_INVALID_CHARS, input.data(),
        static_cast<int>(input.size()), nullptr, 0, nullptr, nullptr);
    if (needed <= 0) return false;
    output.resize(static_cast<std::size_t>(needed));
    return ::WideCharToMultiByte(
        CP_UTF8, WC_ERR_INVALID_CHARS, input.data(),
        static_cast<int>(input.size()), output.data(), needed,
        nullptr, nullptr) == needed;
}

bool writeAtomic(std::wstring const& path, std::string const& body)
{
    const auto slash = path.find_last_of(L"\\/");
    if (slash == std::wstring::npos) return false;
    const auto parent = path.substr(0, slash);
    if (parent.empty() || parent.size() > MAX_PATH - 35) return false;

    wchar_t temporary[MAX_PATH]{};
    if (!::GetTempFileNameW(parent.c_str(), L"fbm", 0, temporary))
        return false;

    HANDLE handle = ::CreateFileW(temporary, GENERIC_WRITE, 0, nullptr,
        TRUNCATE_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (handle == INVALID_HANDLE_VALUE) {
        ::DeleteFileW(temporary);
        return false;
    }

    DWORD written = 0;
    bool good = body.empty() ||
        (::WriteFile(handle, body.data(), static_cast<DWORD>(body.size()),
                     &written, nullptr) != FALSE &&
         written == body.size());
    if (good) good = ::FlushFileBuffers(handle) != FALSE;
    if (!::CloseHandle(handle)) good = false;
    if (good) {
        good = ::MoveFileExW(temporary, path.c_str(),
            MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != FALSE;
    }
    if (!good) ::DeleteFileW(temporary);
    return good;
}

bool decodeLegacy(std::vector<unsigned char> const& bytes, std::wstring& text)
{
    text.clear();
    if (bytes.size() >= 2 && bytes[0] == 0xff && bytes[1] == 0xfe) {
        if ((bytes.size() - 2) % 2 != 0) return false;
        text.reserve((bytes.size() - 2) / 2);
        for (std::size_t i = 2; i + 1 < bytes.size(); i += 2) {
            text.push_back(static_cast<wchar_t>(
                static_cast<unsigned int>(bytes[i]) |
                (static_cast<unsigned int>(bytes[i + 1]) << 8)));
        }
        return true;
    }

    std::size_t offset = 0;
    if (bytes.size() >= 3 && bytes[0] == 0xef &&
        bytes[1] == 0xbb && bytes[2] == 0xbf)
        offset = 3;
    const std::string utf8(
        reinterpret_cast<char const*>(bytes.data() + offset),
        bytes.size() - offset);
    return utf8ToWide(utf8, text);
}

std::wstring trim(std::wstring value)
{
    const auto first = std::find_if_not(value.begin(), value.end(),
        [](wchar_t ch) { return std::iswspace(ch); });
    const auto last = std::find_if_not(value.rbegin(), value.rend(),
        [](wchar_t ch) { return std::iswspace(ch); }).base();
    if (first >= last) return {};
    return std::wstring(first, last);
}

bool equalNoCase(std::wstring const& a, std::wstring const& b)
{
    return ::CompareStringOrdinal(a.c_str(), static_cast<int>(a.size()),
        b.c_str(), static_cast<int>(b.size()), TRUE) == CSTR_EQUAL;
}

std::wstring knownFolder(REFKNOWNFOLDERID id)
{
    PWSTR raw = nullptr;
    if (FAILED(::SHGetKnownFolderPath(id, KF_FLAG_DEFAULT, nullptr, &raw)) ||
        !raw)
        return {};
    std::wstring value(raw);
    ::CoTaskMemFree(raw);
    return value;
}

std::wstring resolveLegacyPath(std::wstring value)
{
    value = trim(std::move(value));
    const std::pair<wchar_t const*, KNOWNFOLDERID const*> known[] = {
        {L"%Desktop%", &FOLDERID_Desktop},
        {L"%Personal%", &FOLDERID_Documents},
        {L"%MyDocuments%", &FOLDERID_Documents},
        {L"%MyMusic%", &FOLDERID_Music},
        {L"%MyPictures%", &FOLDERID_Pictures},
        {L"%MyVideo%", &FOLDERID_Videos},
        {L"%Downloads%", &FOLDERID_Downloads},
    };
    for (auto const& entry : known) {
        if (equalNoCase(value, entry.first))
            return normalizePath(knownFolder(*entry.second));
    }

    if (value.find(L'%') != std::wstring::npos) {
        std::array<wchar_t, 32768> buffer{};
        const auto count = ::ExpandEnvironmentStringsW(
            value.c_str(), buffer.data(), static_cast<DWORD>(buffer.size()));
        if (count && count < buffer.size())
            value.assign(buffer.data(), count - 1);
    }
    return normalizePath(std::move(value));
}

} // namespace

std::wstring Store::privatePath()
{
    const auto dir = directory();
    return dir.empty() ? L"" : dir + L"\\bookmarks-v1.txt";
}

MutationResult Store::add(std::wstring name, std::wstring path) noexcept
{
    try {
        path = normalizePath(std::move(path));
        if (!validName(name) || !validPath(path)) return MutationResult::Invalid;
        if (mItems.size() >= kMaxItems) return MutationResult::Full;
        if (std::any_of(mItems.begin(), mItems.end(),
            [&](Item const& item) { return samePath(item.path, path); }))
            return MutationResult::Duplicate;
        mItems.push_back({std::move(name), std::move(path)});
        return MutationResult::Applied;
    } catch (...) {
        return MutationResult::Invalid;
    }
}

MutationResult Store::rename(std::size_t index, std::wstring name) noexcept
{
    try {
        if (index >= mItems.size()) return MutationResult::NotFound;
        if (!validName(name)) return MutationResult::Invalid;
        mItems[index].name = std::move(name);
        return MutationResult::Applied;
    } catch (...) {
        return MutationResult::Invalid;
    }
}

bool Store::erase(std::size_t index) noexcept
{
    try {
        if (index >= mItems.size()) return false;
        mItems.erase(mItems.begin() + static_cast<std::ptrdiff_t>(index));
        return true;
    } catch (...) {
        return false;
    }
}

bool Store::loadFrom(std::wstring const& path) noexcept
{
    try {
        std::vector<unsigned char> bytes;
        if (!readBytes(path, 256 * 1024, bytes)) return false;
        std::wstring text;
        const std::string utf8(
            reinterpret_cast<char const*>(bytes.data()), bytes.size());
        if (!utf8ToWide(utf8, text)) return false;

        std::wistringstream lines(text);
        std::wstring line;
        if (!std::getline(lines, line)) return false;
        if (!line.empty() && line.back() == L'\r') line.pop_back();
        if (line != L"schema=1") return false;

        Store candidate;
        while (std::getline(lines, line)) {
            if (!line.empty() && line.back() == L'\r') line.pop_back();
            if (line.empty()) continue;
            const auto tab = line.find(L'\t');
            if (tab == std::wstring::npos ||
                line.find(L'\t', tab + 1) != std::wstring::npos)
                return false;
            if (candidate.add(line.substr(0, tab), line.substr(tab + 1)) !=
                MutationResult::Applied)
                return false;
        }
        mItems = std::move(candidate.mItems);
        return true;
    } catch (...) {
        return false;
    }
}

bool Store::saveTo(std::wstring const& path) const noexcept
{
    try {
        Store validated;
        for (auto const& item : mItems) {
            if (validated.add(item.name, item.path) != MutationResult::Applied)
                return false;
        }

        std::wstring text = L"schema=1\r\n";
        for (auto const& item : mItems) {
            text += item.name;
            text += L'\t';
            text += item.path;
            text += L"\r\n";
        }
        std::string utf8;
        if (!wideToUtf8(text, utf8)) return false;
        return writeAtomic(path, utf8);
    } catch (...) {
        return false;
    }
}

bool Store::load() noexcept
{
    mItems.clear();
    const auto path = privatePath();
    if (path.empty()) return false;
    const DWORD attrs = ::GetFileAttributesW(path.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES) {
        const auto error = ::GetLastError();
        return error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND;
    }
    if (attrs & FILE_ATTRIBUTE_DIRECTORY) return false;
    return loadFrom(path);
}

bool Store::save() const noexcept
{
    const auto dir = directory();
    if (dir.empty()) return false;
    if (!::CreateDirectoryW(dir.c_str(), nullptr) &&
        ::GetLastError() != ERROR_ALREADY_EXISTS)
        return false;
    const DWORD attrs = ::GetFileAttributesW(dir.c_str());
    if (attrs == INVALID_FILE_ATTRIBUTES ||
        !(attrs & FILE_ATTRIBUTE_DIRECTORY) ||
        (attrs & FILE_ATTRIBUTE_REPARSE_POINT))
        return false;
    return saveTo(privatePath());
}

ImportResult Store::importLegacy(std::wstring const& path) noexcept
{
    ImportResult result{};
    try {
        std::vector<unsigned char> bytes;
        if (!readBytes(path, 512 * 1024, bytes)) return result;
        std::wstring text;
        if (!decodeLegacy(bytes, text)) return result;

        std::wistringstream lines(text);
        std::wstring line;
        bool inBookmark = false;
        bool foundBookmark = false;
        std::map<std::wstring, std::wstring> values;
        while (std::getline(lines, line)) {
            if (!line.empty() && line.back() == L'\r') line.pop_back();
            const auto stripped = trim(line);
            if (stripped.empty() || stripped[0] == L';' ||
                stripped[0] == L'#')
                continue;
            if (stripped.front() == L'[' && stripped.back() == L']') {
                const auto section = stripped.substr(1, stripped.size() - 2);
                inBookmark = equalNoCase(section, L"bookmark");
                if (inBookmark) foundBookmark = true;
                else if (foundBookmark) break;
                continue;
            }
            if (!inBookmark) continue;
            const auto equals = line.find(L'=');
            if (equals == std::wstring::npos) continue;
            values[trim(line.substr(0, equals))] = line.substr(equals + 1);
        }
        if (!foundBookmark) return result;
        result.loaded = true;

        for (std::size_t i = 1; i <= kMaxItems; ++i) {
            const auto stem = L"bookmark.item" + std::to_wstring(i);
            const auto nameIt = values.find(stem + L".name");
            const auto pathIt = values.find(stem + L".path");
            if (nameIt == values.end() && pathIt == values.end()) continue;
            if (nameIt == values.end() || pathIt == values.end()) {
                ++result.skipped;
                continue;
            }
            const auto mutation = add(
                nameIt->second, resolveLegacyPath(pathIt->second));
            if (mutation == MutationResult::Applied) ++result.added;
            else ++result.skipped;
        }
        return result;
    } catch (...) {
        return result;
    }
}

} // namespace fxfile::bookmarks
