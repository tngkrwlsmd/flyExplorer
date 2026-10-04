#pragma once
#include <cstddef>
#include <string>
#include <vector>

namespace fxfile::filterrules {

struct Rule final {
    std::wstring name;
    std::wstring masks;
};

enum class MutationResult {
    Applied,
    Invalid,
    Duplicate,
    Full,
    NotFound,
};

class Store final {
public:
    static constexpr std::size_t kMaxItems = 20;
    static constexpr std::size_t kMaxName = 56;
    static constexpr std::size_t kMaxMasks = 260;

    std::vector<Rule> const& items() const noexcept { return mItems; }

    bool load() noexcept;
    bool save() const noexcept;
    bool loadFrom(std::wstring const& path) noexcept;
    bool saveTo(std::wstring const& path) const noexcept;

    MutationResult add(std::wstring name, std::wstring masks) noexcept;
    MutationResult update(
        std::size_t index, std::wstring name, std::wstring masks) noexcept;
    bool erase(std::size_t index) noexcept;

    static std::wstring privatePath();
    static bool validExpression(std::wstring const& expression) noexcept;
    static bool matches(
        std::wstring const& filename,
        std::wstring const& expression) noexcept;

private:
    std::vector<Rule> mItems;
};

} // namespace fxfile::filterrules
