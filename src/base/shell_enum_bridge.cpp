// Shared original ExplorerCtrl/WinUI native Shell enum entry point.
// This low-level compilation unit intentionally uses pre-Vista COM APIs
// so the original MFC application's forced legacy PCH still compiles.
#include "shell_navigation_core.h"

namespace fxfile { namespace shellnav {
HRESULT openEnumeration(IShellFolder* folder,HWND owner,DWORD flags,
                        IEnumIDList** result) noexcept {
    if(!result)return E_POINTER;
    *result=nullptr;
    if(!folder)return E_INVALIDARG;
    return folder->EnumObjects(owner,flags,result);
}
} }
