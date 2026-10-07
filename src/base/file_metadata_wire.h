#pragma once
#include <cstddef>
#include <cstdint>

namespace fxfile::metadatawire {

inline constexpr std::uint32_t kMagic=0x31444D46u; // FMD1
inline constexpr std::uint32_t kVersion=1;
inline constexpr std::size_t kMaxItems=20000;
inline constexpr std::size_t kMaxPathUnits=1024*1024;
inline constexpr std::size_t kMaxBodyBytes=
    kMaxPathUnits*sizeof(wchar_t)+kMaxItems*sizeof(std::uint32_t);

#pragma pack(push,1)
struct RequestHeader final {
    std::uint32_t magic=0;
    std::uint32_t version=0;
    std::uint32_t count=0;
    std::uint32_t bodyBytes=0;
    std::uint32_t checksum=0;
    std::uint64_t cancelHandle=0;
};
struct Record final {
    std::uint32_t magic=0;
    std::uint32_t version=0;
    std::uint32_t index=0;
    std::uint32_t valid=0;
    std::uint32_t error=0;
    std::uint32_t attributes=0;
    std::uint64_t bytes=0;
    std::uint64_t modified=0;
};
#pragma pack(pop)

inline std::uint32_t checksum(void const* data,std::size_t size) noexcept
{
    auto const* bytes=static_cast<unsigned char const*>(data);
    std::uint32_t hash=2166136261u;
    for(std::size_t i=0;i<size;++i)hash=(hash^bytes[i])*16777619u;
    return hash;
}

} // namespace fxfile::metadatawire
