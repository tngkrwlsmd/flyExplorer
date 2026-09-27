#pragma once
#include <filesystem>
#include <system_error>
#include <vector>

// Independent filesystem navigation fixture. It is NOT ExplorerCtrl,
// Shell namespace navigation, or flyExplorer's production command adapter.
struct NavigationModel final {
    using Path = std::filesystem::path;
    Path current;
    std::vector<Path> previous;
    std::vector<Path> next;

    explicit NavigationModel(Path initial) {
        std::error_code ec;
        auto normalized = std::filesystem::weakly_canonical(initial, ec);
        current = (!ec && std::filesystem::is_directory(normalized)) ? normalized : std::filesystem::current_path();
    }
    bool Open(Path destination) {
        std::error_code ec;
        auto normalized = std::filesystem::weakly_canonical(destination, ec);
        if (ec || !std::filesystem::is_directory(normalized, ec) || normalized == current) return false;
        previous.push_back(current);
        current = normalized;
        next.clear();
        return true;
    }
    bool Back() {
        if (previous.empty()) return false;
        next.push_back(current);
        current = previous.back();
        previous.pop_back();
        return true;
    }
    bool Forward() {
        if (next.empty()) return false;
        previous.push_back(current);
        current = next.back();
        next.pop_back();
        return true;
    }
    bool Up() {
        auto parent = current.parent_path();
        return parent != current && Open(parent);
    }
};
