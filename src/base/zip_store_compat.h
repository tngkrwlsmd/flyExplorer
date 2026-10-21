// F08/EP10 narrow Store ZIP interoperability policy.
// Do not interpret Windows MSZIP as ZIP raw Deflate (method 8).
// This helper never decompresses, writes, or permits zip paths by itself.
#pragma once
#include "zip_inspection.h"
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace fxfile::zipstorecompat {
inline constexpr std::uint16_t kUtf8NameFlag=0x0800u;

// Only legacy ASCII names (no UTF-8 flag) or strict UTF-8 names.
// Encryption, data descriptor, patching, strong encryption, etc. fail closed.
inline bool supportedFlags(std::uint16_t flags) noexcept {
    return flags==0u||flags==kUtf8NameFlag;
}
// The supported data and local headers use the historical DOS ZIP 1.0/2.0
// contract. Unix/NTFS creator attributes, symlinks, ZIP64 and later
// variants remain out of scope, even when their members are Store.
inline bool supportedDosVersion(std::uint16_t version) noexcept {
    return version==10u||version==20u;
}
inline bool sameDosTime(std::vector<unsigned char> const& bytes,
                        std::size_t local,std::size_t central) noexcept {
    // Caller has validated both 30/46-byte header spans.
    return fxfile::zipinspect::detail::u16(bytes,local+10u)==
           fxfile::zipinspect::detail::u16(bytes,central+12u)&&
           fxfile::zipinspect::detail::u16(bytes,local+12u)==
           fxfile::zipinspect::detail::u16(bytes,central+14u);
}
inline bool decodeName(std::vector<unsigned char> const& bytes,
                       std::size_t begin,std::size_t nameLength,
                       std::uint16_t flags,std::wstring& name) {
    if(!supportedFlags(flags))return false;
    // Without bit 11, accept ASCII only; never guess CP437/ACP/UTF-8.
    return fxfile::zipinspect::detail::decode(
        bytes,begin,nameLength,flags==kUtf8NameFlag,name);
}
} // namespace fxfile::zipstorecompat
