// Bounded private helper query: four visible images per local folder at most.
#pragma once
#include <windows.h>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile::thumbnail {
struct Result {
 std::uint32_t width=0,height=0;
 std::vector<unsigned char> bgra;
 bool valid() const noexcept {
  return width>0&&height>0&&
         bgra.size()==static_cast<size_t>(width)*height*4;
 }
};
Result query(std::wstring const& helper,
             std::wstring const& localImagePath,
             DWORD timeoutMs=1800,std::uint32_t requestedPixels=64) noexcept;
}
