#pragma once
#include <cstddef>
#include <string>
#include <vector>

namespace fxfile::bookmarks {

struct Item {
    std::wstring name;
    std::wstring path;
};

enum class MutationResult {
    Applied,
    Invalid,
    Duplicate,
    Full,
    NotFound,
};

struct ImportResult {
    bool loaded = false;
    std::size_t added = 0;
    std::size_t skipped = 0;
};

class Store final {
public:
    static constexpr std::size_t kMaxItems = 100;
    static constexpr std::size_t kMaxName = 256;
    static constexpr std::size_t kMaxPath = 32760;

    std::vector<Item> const& items() const noexcept { return mItems; }

    bool load() noexcept;
    bool save() const noexcept;
    bool loadFrom(std::wstring const& path) noexcept;
    bool saveTo(std::wstring const& path) const noexcept;

    MutationResult add(std::wstring name, std::wstring path) noexcept;
    MutationResult rename(std::size_t index, std::wstring name) noexcept;
    bool erase(std::size_t index) noexcept;
    ImportResult importLegacy(std::wstring const& path) noexcept;

    static std::wstring privatePath();

private:
    std::vector<Item> mItems;
};

} // namespace fxfile::bookmarks
