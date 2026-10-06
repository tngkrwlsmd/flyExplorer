#pragma once
#include <atomic>
#include <memory>
#include <string>

namespace fxfile::boundedregex {

enum class CompileResult {
    Valid,
    InvalidSyntax,
    Unsupported,
    TooComplex,
};

enum class MatchResult {
    Match,
    NoMatch,
    Canceled,
    BudgetExceeded,
};

class Pattern final {
public:
    Pattern();
    Pattern(Pattern&&) noexcept;
    Pattern& operator=(Pattern&&) noexcept;
    ~Pattern();

    Pattern(Pattern const&)=delete;
    Pattern& operator=(Pattern const&)=delete;

    CompileResult compile(
        std::wstring const& pattern,bool caseSensitive) noexcept;
    MatchResult search(
        std::wstring const& text,
        std::shared_ptr<std::atomic_bool> const& cancel) const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace fxfile::boundedregex
