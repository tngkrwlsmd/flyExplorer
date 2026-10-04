#pragma once
#include <cstddef>
#include <string>
#include <vector>

namespace fxfile::searchpresets {

struct Preset final {
    std::wstring name;
    std::wstring term;
    std::wstring extension;
    std::wstring minSizeKb;
    std::wstring maxSizeKb;
    std::wstring modifiedAfter;
    std::wstring modifiedBefore;
    bool regex=false;
    bool caseSensitive=false;
    int kind=0;
};

enum class MutationResult { Applied, Invalid, Duplicate, Full, NotFound };

class Store final {
public:
    static constexpr std::size_t kMaxItems=20;
    static constexpr std::size_t kMaxName=56;
    static constexpr std::size_t kMaxField=256;

    std::vector<Preset> const& items() const noexcept { return mItems; }
    bool load() noexcept;
    bool save() const noexcept;
    bool loadFrom(std::wstring const& path) noexcept;
    bool saveTo(std::wstring const& path) const noexcept;
    MutationResult add(Preset value) noexcept;
    MutationResult update(std::size_t index,Preset value) noexcept;
    bool erase(std::size_t index) noexcept;
    static std::wstring privatePath();

private:
    std::vector<Preset> mItems;
};

} // namespace fxfile::searchpresets
