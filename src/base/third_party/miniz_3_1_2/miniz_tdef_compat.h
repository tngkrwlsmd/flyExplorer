#pragma once
// F08 miniz 3.1.2 tdefl-only shim: the upstream monolithic miniz.h also
// defines these constants and checksums. All functions here are LOCAL to the
// separately compiled vendor C translation unit; no external dependencies.
#if defined(_MSC_VER)
#define MZ_FORCEINLINE __forceinline
#else
#define MZ_FORCEINLINE inline
#endif
#define MZ_DEFAULT_LEVEL 6
#define MZ_FILTERED 1
#define MZ_HUFFMAN_ONLY 2
#define MZ_RLE 3
#define MZ_FIXED 4
#define MZ_CRC32_INIT 0u
static mz_uint32 fx_miniz_local_adler32(mz_uint32 state,
                                        const mz_uint8* bytes,size_t count) {
    mz_uint32 s1=state&65535u,s2=state>>16;
    for(size_t i=0;i<count;++i){
        s1=(s1+bytes[i])%65521u;
        s2=(s2+s1)%65521u;
    }
    return (s2<<16)|s1;
}
static mz_uint32 fx_miniz_local_crc32(mz_uint32 prior,
                                      const mz_uint8* bytes,size_t count) {
    mz_uint32 crc=~prior;
    for(size_t i=0;i<count;++i){
        crc^=bytes[i];
        for(unsigned bit=0;bit<8;++bit)
            crc=(crc>>1)^(0xedb88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
#define mz_adler32 fx_miniz_local_adler32
#define mz_crc32 fx_miniz_local_crc32
