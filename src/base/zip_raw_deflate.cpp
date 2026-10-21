// Native raw RFC1951 decoder adapter, miniz 3.1.2 pinned in third_party.
// No ZIP API or dynamic archive/file features from miniz are used.
#define MINIZ_NO_MALLOC
#define MINIZ_NO_STDIO
#define MINIZ_NO_TIME
#include "zip_raw_deflate.h"
#include "third_party/miniz_3_1_2/miniz_tinfl.h"
#include <utility>

// The pinned miniz low-level C implementation is built independently as C.
// The adapter calls its externally linked C symbols.

namespace fxfile::ziprawdeflate {
bool inflateExact(std::uint8_t const* input,std::size_t packed,
                  std::size_t expected,std::vector<unsigned char>& output,
                  std::atomic_bool const* cancellation) noexcept {
    output.clear();
    if((!input&&packed)||!packed||packed>kMaxPackedBytes||
       expected>kMaxOutputBytes||
       (expected>0&&static_cast<std::uint64_t>(expected)>
                      static_cast<std::uint64_t>(packed)*kMaxRatio)||
       (cancellation&&cancellation->load(std::memory_order_relaxed)))
        return false;
    try{
        // One bounded output allocation, never a dynamically expanding
        // heap decompressor. Supply one physical byte for the empty case.
        std::vector<unsigned char> decoded(expected?expected:1u);
        tinfl_decompressor decompressor{};
        tinfl_init(&decompressor);
        std::size_t consumed=packed;
        std::size_t produced=decoded.size();
        const auto status=tinfl_decompress(
            &decompressor,input,&consumed,decoded.data(),decoded.data(),
            &produced,TINFL_FLAG_USING_NON_WRAPPING_OUTPUT_BUF);
        if(status!=TINFL_STATUS_DONE||consumed!=packed||
           produced!=expected||
           (cancellation&&cancellation->load(std::memory_order_relaxed)))
            return false;
        decoded.resize(expected);
        output=std::move(decoded);
        return true;
    }catch(...){
        output.clear();return false;
    }
}
} // namespace fxfile::ziprawdeflate
