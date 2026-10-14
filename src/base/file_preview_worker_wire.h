#pragma once
// F03 private one-shot preview worker wire. This format is NOT shell_isolation_wire.
// The parent must supervise each exact-owned child process in a kill-on-close
// Job Object, bound stdin/stdout, and discard stale PaneTab completions.
// All header fields are little-endian Windows ABI; no pointers cross the wire.
#ifndef FXFILE_PREVIEW_WORKER_WIRE_H
#define FXFILE_PREVIEW_WORKER_WIRE_H
#include "file_preview_policy.h"
#include <cstddef>
#include <cstdint>

namespace fxfile::previewwire {
inline constexpr std::uint32_t kRequestMagic=0x31515046; // FPQ1
inline constexpr std::uint32_t kReplyMagic=0x31525046;   // FPR1
inline constexpr std::uint32_t kVersion=1;
inline constexpr std::uint32_t kMaxPathUnits=previewpolicy::kMaxPathUnits;
inline constexpr std::uint32_t kMaxReplyBytes=
    static_cast<std::uint32_t>(previewpolicy::kMaxImageBytes);
inline constexpr std::uint32_t kDeadlineMs=3000;

#pragma pack(push,1)
struct Request final {
    std::uint32_t magic=kRequestMagic;
    std::uint32_t version=kVersion;
    std::uint32_t kind=0;      // previewpolicy::Kind, Text=1, Image=2
    std::uint32_t pathUnits=0; // following UTF-16 code units, no NUL
    std::uint64_t knownBytes=0;
    std::uint32_t pathChecksum=0;
};
struct Reply final {
    std::uint32_t magic=kReplyMagic;
    std::uint32_t version=kVersion;
    std::uint32_t status=0;    // previewworker::Status
    std::uint32_t kind=0;
    std::uint32_t byteCount=0; // following opaque bytes; zero on failure
    std::uint32_t checksum=0;
};
#pragma pack(pop)
static_assert(sizeof(Request)==28,"preview request wire size");
static_assert(sizeof(Reply)==24,"preview reply wire size");

inline std::uint32_t checksum(void const* bytes,std::size_t n) noexcept {
    auto const* data=static_cast<std::uint8_t const*>(bytes);
    std::uint32_t hash=2166136261u;
    for(std::size_t i=0;i<n;++i)hash=(hash^data[i])*16777619u;
    return hash;
}
inline constexpr bool validHeader(Request const& r) noexcept {
    return r.magic==kRequestMagic && r.version==kVersion &&
        (r.kind==1u||r.kind==2u) &&
        r.pathUnits>=4u && r.pathUnits<=kMaxPathUnits &&
        r.knownBytes<=((r.kind==1u)?
            previewpolicy::kMaxTextBytes:previewpolicy::kMaxImageBytes);
}
inline constexpr bool validReply(Reply const& r) noexcept {
    return r.magic==kReplyMagic && r.version==kVersion &&
        r.status<=10u &&
        (r.kind==0u||r.kind==1u||r.kind==2u) &&
        r.byteCount<=kMaxReplyBytes &&
        (r.status==0u || (!r.byteCount&&!r.checksum&&r.kind==0u));
}
} // namespace fxfile::previewwire
#endif
