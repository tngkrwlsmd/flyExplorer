// Pinned miniz 3.1.2 low-level tdefl. Never uses ZIP archive APIs.
#define MINIZ_NO_MALLOC
#define MINIZ_NO_STDIO
#define MINIZ_NO_TIME
#include "zip_raw_deflate_compress.h"
#include "third_party/miniz_3_1_2/miniz_tdef.h"
#include <memory>
#include <utility>
namespace fxfile::ziprawdeflate {
bool compressBounded(std::vector<unsigned char> const& source,
                     std::vector<unsigned char>& output) noexcept {
    output.clear();
    if(source.size()>kMaxCompressionInput)return false;
    try{
        // Raw Deflate expands by a bounded overhead on incompressible input.
        // Reject rather than grow the buffer beyond the fixed allocation.
        const std::size_t capacity=source.size()+
                                   source.size()/16u+65536u;
        std::vector<unsigned char> bytes(capacity);
        auto state=std::make_unique<tdefl_compressor>();
        if(tdefl_init(state.get(),nullptr,nullptr,TDEFL_DEFAULT_MAX_PROBES)!=
           TDEFL_STATUS_OKAY)return false;
        std::size_t consumed=source.size();
        std::size_t produced=bytes.size();
        // No TDEFL_WRITE_ZLIB_HEADER: ZIP method 8 stores a raw stream.
        const auto status=tdefl_compress(
            state.get(),source.data(),&consumed,
            bytes.data(),&produced,TDEFL_FINISH);
        if(status!=TDEFL_STATUS_DONE||consumed!=source.size()||
           produced==0||produced>capacity)return false;
        bytes.resize(produced);
        output=std::move(bytes);
        return true;
    }catch(...){output.clear();return false;}
}
}
