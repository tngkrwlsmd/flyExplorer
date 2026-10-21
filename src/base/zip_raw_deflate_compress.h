// F08: raw RFC1951 compression without file or ZIP header authority.
#pragma once
#include <cstddef>
#include <vector>
namespace fxfile::ziprawdeflate {
inline constexpr std::size_t kMaxCompressionInput=8u*1024u*1024u;
// Only raw DEFLATE bytes, not a zlib or gzip wrapper. No cancellation
// mid-call; the single-file ZIP action is not currently cancellable.
bool compressBounded(std::vector<unsigned char> const& source,
                     std::vector<unsigned char>& output) noexcept;
}
