#pragma once
#ifndef FLY_INDEXED_SEARCH_WIRE_H
#define FLY_INDEXED_SEARCH_WIRE_H
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile::indexwire {
constexpr std::uint32_t kMagic=0x33585346; // FSX3
constexpr std::uint32_t kVersion=1;
constexpr std::uint32_t kMaxResults=1000;
constexpr std::uint32_t kMaxBodyBytes=1024u*1024u;
constexpr std::uint32_t kMaxPathUnits=2048;
constexpr std::uint32_t kMaxTermUnits=128;
#pragma pack(push,1)
struct Header {
 std::uint32_t magic,version,status,count,bytes,checksum;
};
#pragma pack(pop)
static_assert(sizeof(Header)==24,"indexed search response ABI");
inline std::uint32_t checksum(void const* raw,std::size_t size) noexcept {
 auto const* p=static_cast<unsigned char const*>(raw);
 std::uint32_t value=2166136261u;
 for(std::size_t i=0;i<size;++i)value=(value^p[i])*16777619u;
 return value;
}
inline bool validTerm(std::wstring const& value) noexcept {
 return !value.empty()&&value.size()<=kMaxTermUnits&&
    value.find_first_of(L"%_[]\r\n\"\0")==std::wstring::npos;
}
inline bool validScope(std::wstring const& value) noexcept {
 if(value.size()<3||value.size()>kMaxPathUnits||
    value.find_first_of(L"\r\n\"\0")!=std::wstring::npos)return false;
 if(value.rfind(L"\\\\?\\",0)==0||value.rfind(L"\\\\.\\",0)==0)return false;
 return value[1]==L':'&&(value[2]==L'\\'||value[2]==L'/');
}
} // namespace fxfile::indexwire
#endif
