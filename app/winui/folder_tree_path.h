#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>

namespace fxfile::foldertree {

// F04-A: lexical-only guards for a future bounded, opt-in, fixed-drive tree.
// Never treat these guards as proof that a drive is fixed or that ancestors
// are not reparse points. Those checks belong in a detached OS worker.
inline constexpr std::size_t kMaxPathUnits = 1024;
inline constexpr std::size_t kMaxTreeDepth = 12;
inline constexpr std::size_t kMaxChildrenPerNode = 128;

inline bool asciiLetter(wchar_t c) noexcept {
    return (c >= L'A' && c <= L'Z') || (c >= L'a' && c <= L'z');
}

inline wchar_t asciiUpper(wchar_t c) noexcept {
    if (c >= L'a' && c <= L'z') return c - L'a' + L'A';
    return c;
}

inline bool safeLeaf(std::wstring_view name) noexcept {
    if (name.empty() || name == L"." || name == L".." || name.size() > 255 ||
        name.back() == L'.' || name.back() == L' ') return false;
    for (wchar_t c : name) {
        if (c < 32 || c == 127 || c == L'\\' || c == L'/' || c == L':' ||
            c == L'*' || c == L'?' || c == L'"' || c == L'<' ||
            c == L'>' || c == L'|') return false;
    }
    // Win32 device names are reserved even when a filename extension follows.
    const auto end = name.find(L'.');
    const auto base = name.substr(0, end);
    wchar_t upper[4]{};
    if (base.size() != 3 && base.size() != 4) return true;
    for (std::size_t i = 0; i < base.size(); ++i) upper[i] = asciiUpper(base[i]);
    if (base.size() == 3) {
        if ((upper[0] == L'C' && upper[1] == L'O' && upper[2] == L'N') ||
            (upper[0] == L'P' && upper[1] == L'R' && upper[2] == L'N') ||
            (upper[0] == L'A' && upper[1] == L'U' && upper[2] == L'X') ||
            (upper[0] == L'N' && upper[1] == L'U' && upper[2] == L'L')) return false;
    } else if (upper[3] >= L'1' && upper[3] <= L'9') {
        if ((upper[0] == L'C' && upper[1] == L'O' && upper[2] == L'M') ||
            (upper[0] == L'L' && upper[1] == L'P' && upper[2] == L'T')) return false;
    }
    return true;
}

inline bool normalizedDrivePath(std::wstring_view path) noexcept {
    if (path.size() < 3 || path.size() > kMaxPathUnits ||
        !asciiLetter(path[0]) || path[1] != L':' || path[2] != L'\\') return false;
    if (path.size() == 3) return true;
    if (path.back() == L'\\') return false;
    std::size_t start = 3;
    std::size_t depth = 0;
    for (std::size_t i = 3; i <= path.size(); ++i) {
        if (i == path.size() || path[i] == L'\\') {
            if (++depth > kMaxTreeDepth || !safeLeaf(path.substr(start, i - start)))
                return false;
            start = i + 1;
        }
    }
    return true;
}

inline bool childPath(std::wstring_view parent, std::wstring_view leaf,
                      std::wstring& result) {
    if (!normalizedDrivePath(parent) || !safeLeaf(leaf) ||
        parent.size() + leaf.size() + (parent.size() == 3 ? 0 : 1) >
            kMaxPathUnits) return false;
    std::wstring combined(parent);
    if (combined.back() != L'\\') combined += L'\\';
    combined.append(leaf);
    if (!normalizedDrivePath(combined)) return false;
    result = std::move(combined);
    return true;
}

struct RequestIdentity final {
    int side = -1;
    std::size_t tab = 0;
    std::uint64_t route = 0;
    std::uint64_t generation = 0;
};

inline bool accepts(RequestIdentity const& current,
                    RequestIdentity const& received) noexcept {
    return current.side >= 0 && current.side <= 1 &&
        current.route != 0 && current.generation != 0 &&
        current.side == received.side && current.tab == received.tab &&
        current.route == received.route &&
        current.generation == received.generation;
}

} // namespace fxfile::foldertree
