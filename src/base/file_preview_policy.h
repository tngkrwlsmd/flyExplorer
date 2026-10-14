#pragma once
// F03 phase 1: PURE candidate screening, not authorization to open a file.
// An eventual isolated worker MUST verify local fixed-disk identity, every
// reparse boundary, regular-file type, final file size and decoded pixel
// dimensions on the actual opened handle before returning bounded bytes.
// Never call blocking filesystem/COM/provider APIs on the WinUI thread.
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace fxfile::previewpolicy {

inline constexpr std::size_t kMaxPathUnits = 32767;
inline constexpr std::uint64_t kMaxTextBytes = 256ull * 1024;
inline constexpr std::uint64_t kMaxImageBytes = 12ull * 1024 * 1024;
inline constexpr std::uint64_t kMaxDecodedPixels = 16ull * 1024 * 1024;

enum class Kind : std::uint8_t { None, Text, Image };
enum class Rejection : std::uint8_t {
    None, NonLocal, NonRegular, Reparse, UnknownSize, InvalidPath,
    UnsupportedType, TooLarge
};

struct Candidate final {
    std::wstring_view absolutePath{};
    std::uint64_t knownBytes = 0;
    bool isFilesystem = false;
    bool isLocalFixedDrive = false;
    bool isRegularFile = false;
    bool isReparsePoint = false;
    bool hasKnownSize = false;
};

struct Decision final {
    Kind kind = Kind::None;
    Rejection rejection = Rejection::UnsupportedType;
    std::uint64_t maxEncodedBytes = 0;
    // "accepted" is ONLY a candidate, not file-open authorization.
    constexpr bool accepted() const noexcept { return rejection == Rejection::None; }
};

constexpr bool asciiDriveLetter(wchar_t c) noexcept
{
    return (c >= L'A' && c <= L'Z') || (c >= L'a' && c <= L'z');
}

constexpr wchar_t asciiLower(wchar_t c) noexcept
{
    return c >= L'A' && c <= L'Z' ? static_cast<wchar_t>(c + 32) : c;
}

constexpr bool endsWithAsciiNoCase(std::wstring_view path,
                                   std::wstring_view suffix) noexcept
{
    if (suffix.size() > path.size()) return false;
    const auto start = path.size() - suffix.size();
    for (std::size_t i = 0; i < suffix.size(); ++i)
        if (asciiLower(path[start + i]) != asciiLower(suffix[i])) return false;
    return true;
}

constexpr bool canonicalLocalPath(std::wstring_view path) noexcept
{
    // Reject UNC, device/extended prefixes and drive-relative paths.
    if (path.size() < 4 || path.size() > kMaxPathUnits ||
        !asciiDriveLetter(path[0]) || path[1] != L':' ||
        path[2] != L'\\') return false;
    std::size_t segment = 3;
    for (std::size_t i = 3; i <= path.size(); ++i) {
        if (i < path.size() &&
            (path[i] == L'/' || path[i] == L'\0' || path[i] == L':')) return false;
        if (i == path.size() || path[i] == L'\\') {
            const auto size = i - segment;
            if (size == 1 && path[segment] == L'.') return false;
            if (size == 2 && path[segment] == L'.' &&
                path[segment + 1] == L'.') return false;
            if (size == 0 && i != path.size()) return false;
            segment = i + 1;
        }
    }
    return segment == path.size() + 1 && path.back() != L'\\';
}

constexpr Decision screen(Candidate const& item) noexcept
{
    if (!item.isFilesystem || !item.isLocalFixedDrive)
        return {Kind::None, Rejection::NonLocal, 0};
    if (!item.isRegularFile)
        return {Kind::None, Rejection::NonRegular, 0};
    if (item.isReparsePoint)
        return {Kind::None, Rejection::Reparse, 0};
    if (!item.hasKnownSize)
        return {Kind::None, Rejection::UnknownSize, 0};
    if (!canonicalLocalPath(item.absolutePath))
        return {Kind::None, Rejection::InvalidPath, 0};

    Kind kind = Kind::None;
    std::uint64_t bound = 0;
    if (endsWithAsciiNoCase(item.absolutePath, L".txt") ||
        endsWithAsciiNoCase(item.absolutePath, L".md") ||
        endsWithAsciiNoCase(item.absolutePath, L".log")) {
        kind = Kind::Text;
        bound = kMaxTextBytes;
    } else if (endsWithAsciiNoCase(item.absolutePath, L".png") ||
               endsWithAsciiNoCase(item.absolutePath, L".jpg") ||
               endsWithAsciiNoCase(item.absolutePath, L".jpeg") ||
               endsWithAsciiNoCase(item.absolutePath, L".bmp")) {
        kind = Kind::Image;
        bound = kMaxImageBytes;
    } else {
        return {Kind::None, Rejection::UnsupportedType, 0};
    }
    if (item.knownBytes > bound)
        return {Kind::None, Rejection::TooLarge, bound};
    return {kind, Rejection::None, bound};
}

} // namespace fxfile::previewpolicy
