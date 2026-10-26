// UI-independent guard for the exact file-name edit opened by the user.
// This header has no Windows, filesystem-mutation or WinRT dependencies.
#pragma once
#include <string>

namespace fxfile::nameedit {

template<class Context>
bool sameScope(Context const& opened,Context const& live) noexcept {
 return opened.windowTabIdentity==live.windowTabIdentity&&
        opened.side==live.side&&opened.tab==live.tab&&
        opened.route==live.route&&
        opened.visibleFolder==live.visibleFolder&&
        opened.visibleShellFolder==live.visibleShellFolder;
}

inline bool sameRenameSource(std::wstring const& opened,
                             std::wstring const& selected) noexcept {
 // A blank edit source never authorizes renaming any selected item.
 return !opened.empty()&&!selected.empty()&&opened==selected;
}

} // namespace fxfile::nameedit
