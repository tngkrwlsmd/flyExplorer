#pragma once
#ifndef FXFILE_SHELL_VISUAL_WIRE_H
#define FXFILE_SHELL_VISUAL_WIRE_H
#include <cstddef>
#include <cstdint>

namespace fxfile::visualwire {
constexpr std::uint32_t kMagic=0x31565346; // FSV1 little endian
constexpr std::uint32_t kVersion=2;
constexpr std::uint32_t kMaxItems=1200;
constexpr std::uint32_t kMaxNameUnits=4096;
constexpr std::uint32_t kMaxBodyBytes=8u*1024u*1024u;
constexpr std::uint32_t kMaxLabelUnits=80;
constexpr std::uint32_t kMinPixels=16;
constexpr std::uint32_t kMaxPixels=64;
constexpr std::uint32_t kMinThumbnailPixels=32;
constexpr std::uint32_t kMaxThumbnailPixels=128;
constexpr std::uint32_t kMaxThumbnailItems=4;
constexpr std::uint32_t kWantThumbnail=1u;

#pragma pack(push,1)
struct RequestHeader {
    std::uint32_t magic,version,count,pixels,thumbnailPixels,bodyBytes,checksum;
};
struct ItemHeader {
    std::uint32_t units,flags;
};
struct ResultHeader {
    std::uint32_t magic,version,index,labelUnits,pixelBytes;
    std::uint32_t thumbnailWidth,thumbnailHeight,thumbnailPixelBytes;
};
#pragma pack(pop)

static_assert(sizeof(RequestHeader)==28,"Shell visual request ABI");
static_assert(sizeof(ItemHeader)==8,"Shell visual item ABI");
static_assert(sizeof(ResultHeader)==32,"Shell visual result ABI");

inline std::uint32_t checksum(void const* data,std::size_t length) noexcept {
    auto const* ptr=static_cast<unsigned char const*>(data);
    std::uint32_t hash=2166136261u;
    for(std::size_t i=0;i<length;++i)hash=(hash^ptr[i])*16777619u;
    return hash;
}
} // namespace fxfile::visualwire
#endif
