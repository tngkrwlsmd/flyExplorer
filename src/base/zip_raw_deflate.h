// F08/EP10: raw RFC1951 DEFLATE only. This is NOT a ZIP parser.
// Both ZIP extractors own strict metadata and path/CRC validation.
// Decoder must consume exactly the declared compressed range.
#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace fxfile::ziprawdeflate {
inline constexpr std::size_t kMaxPackedBytes=16u*1024u*1024u;
inline constexpr std::size_t kMaxOutputBytes=8u*1024u*1024u;
inline constexpr std::uint64_t kMaxRatio=100u;

// On false, caller MUST NOT publish output. Zero bytes is a valid
// decompressed length. This function is independently build-linked in the
// native WinUI project and does not access any filesystem.
bool inflateExact(std::uint8_t const* input,std::size_t packed,
                  std::size_t expected,std::vector<unsigned char>& output,
                  std::atomic_bool const* cancellation=nullptr) noexcept;
}
