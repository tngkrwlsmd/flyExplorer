#pragma once
#include "../../src/base/ui_preferences.h"
#include <atomic>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>

namespace fxfile::previewprefs {

class PreferencesCoordinator final {
public:
    using Preferences=fxfile::uisettings::Preferences;
    using UiTask=std::function<void()>;
    using Post=std::function<bool(UiTask)>;
    using FailureCallback=std::function<void()>;

    bool load() noexcept;
    Preferences const& current() const noexcept { return preferences_; }
    void setTheme(fxfile::uisettings::Theme theme) noexcept {
        preferences_.theme=theme;
    }
    void setDefaultViewMode(int view) noexcept {
        preferences_.defaultViewMode=view;
    }
    bool setFocusShortcuts(int address,int search) noexcept {
        if(!fxfile::uisettings::validFocusShortcuts(address,search))return false;
        preferences_.addressShortcut=address;
        preferences_.searchShortcut=search;
        return true;
    }
    bool persist(Post post,FailureCallback failure);

private:
    Preferences preferences_{};
    std::shared_ptr<std::mutex> writeMutex_=std::make_shared<std::mutex>();
    std::shared_ptr<std::atomic_uint64_t> revision_=
        std::make_shared<std::atomic_uint64_t>(0);
};

} // namespace fxfile::previewprefs
