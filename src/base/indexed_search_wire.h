#pragma once
#ifndef FLY_INDEXED_SEARCH_WIRE_H
#define FLY_INDEXED_SEARCH_WIRE_H
#include <cstddef>
#include <cstdint>
#include <limits>
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
    value.find_first_of(L"%_[]\r\n\"/\\*?")==std::wstring::npos&&
    value.find(L'\0')==std::wstring::npos;
}
// A normalized extension is one filename suffix without its leading dot.
inline bool validExtension(std::wstring const& value) noexcept {
 return !value.empty()&&value.size()<=32&&
    value.find_first_of(L"\\/:*?\"<>|\r\n\t")==std::wstring::npos&&
    value.find(L'\0')==std::wstring::npos;
}
// Indexed System.Size is a signed BIGINT. Fail closed above that ceiling.
constexpr std::uint64_t kMaxIndexedSizeBytes=
    static_cast<std::uint64_t>((std::numeric_limits<std::int64_t>::max)());
inline bool parseIndexedSizeKb(std::wstring const& text,
                               bool& present,std::uint64_t& bytes) noexcept {
 present=!text.empty();bytes=0;
 if(!present)return true;
 if(text.size()>20)return false;
 std::uint64_t kb=0;
 const auto limit=kMaxIndexedSizeBytes/1024;
 for(wchar_t ch:text){
  if(ch<L'0'||ch>L'9')return false;
  const auto digit=static_cast<std::uint64_t>(ch-L'0');
  if(kb>(limit-digit)/10)return false;
  kb=kb*10+digit;
 }
 bytes=kb*1024;
 return true;
}
inline bool validScope(std::wstring const& value) noexcept {
 if(value.size()<3||value.size()>kMaxPathUnits||
    value.find_first_of(L"\r\n\"")!=std::wstring::npos||
    value.find(L'\0')!=std::wstring::npos)return false;
 if(value.rfind(L"\\\\?\\",0)==0||value.rfind(L"\\\\.\\",0)==0)return false;
 return value[1]==L':'&&(value[2]==L'\\'||value[2]==L'/');
}
} // namespace fxfile::indexwire
#endif
