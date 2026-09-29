// M1.7 EXPERIMENT: private, versioned, strictly bounded Shell-helper wire.
#pragma once
#ifndef FXFILE_SHELL_ISOLATION_WIRE_H
#define FXFILE_SHELL_ISOLATION_WIRE_H
#include <cstdint>
#include <cstring>
namespace fxfile { namespace isolation {
constexpr std::uint32_t kMagic=0x314c5346; // FSL1 little endian
constexpr std::uint32_t kVersion=2;
constexpr std::uint32_t kPath=1,kAbsolutePidl=2;
constexpr std::uint32_t kMaxPathUnits=16384;
constexpr std::uint32_t kMaxItemUnits=4096;
constexpr std::uint32_t kMaxPidl=65536;
constexpr std::uint32_t kMaxBody=4u*1024u*1024u;
constexpr std::uint32_t kMaxEntries=1200;
#pragma pack(push,1)
struct Request {
    std::uint32_t magic,version,type,length;
};
struct Reply {
    std::uint32_t magic,version;
    std::int32_t hr;
    std::uint32_t count,bodyBytes,checksum,flags;
};
#pragma pack(pop)
static_assert(sizeof(Request)==16,"Shell request ABI");
static_assert(sizeof(Reply)==28,"Shell response ABI");
inline std::uint32_t checksum(void const* data,size_t length) noexcept {
    const auto* ptr=static_cast<unsigned char const*>(data);
    std::uint32_t hash=2166136261u;
    for(size_t i=0;i<length;++i)hash=(hash^ptr[i])*16777619u;
    return hash;
}
inline bool validPidl(void const* data,size_t length) noexcept {
    if(!data||length<2||length>kMaxPidl)return false;
    const auto* bytes=static_cast<unsigned char const*>(data);
    size_t offset=0;
    for(;;){
        if(offset+2>length)return false;
        const unsigned size=static_cast<unsigned>(bytes[offset]) |
                            (static_cast<unsigned>(bytes[offset+1])<<8);
        if(size==0)return offset+2==length;
        if(size<2 || size>length-offset)return false;
        offset+=size;
    }
}
} }
#endif
