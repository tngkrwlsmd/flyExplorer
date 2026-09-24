// Pure transfer-budget contract shared by the updater and native regression.
#ifndef FXFILE_BASE_UPDATE_DOWNLOAD_LIMITS_H_
#define FXFILE_BASE_UPDATE_DOWNLOAD_LIMITS_H_

#include <cstddef>

namespace fxfile {
namespace base {

static const std::size_t kMaxUpdateMetadataBytes = 256u * 1024u;

inline bool canAcceptUpdateMetadataChunk(
    std::size_t aCompletedBytes,
    std::size_t aElementSize,
    std::size_t aElementCount)
{
    if (aCompletedBytes > kMaxUpdateMetadataBytes)
        return false;
    if (aElementSize == 0 || aElementCount == 0)
        return true;
    return aElementSize <=
        (kMaxUpdateMetadataBytes - aCompletedBytes) / aElementCount;
}

} // namespace base
} // namespace fxfile

#endif // FXFILE_BASE_UPDATE_DOWNLOAD_LIMITS_H_
