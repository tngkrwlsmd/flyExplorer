#include "directory_change_bridge.h"
namespace fxfile { namespace directorychange {
HANDLE open(wchar_t const* directory,bool subtree,DWORD mask) noexcept {
    if(!directory || !*directory) {
        ::SetLastError(ERROR_INVALID_PARAMETER);
        return INVALID_HANDLE_VALUE;
    }
    return ::FindFirstChangeNotificationW(directory,subtree?TRUE:FALSE,mask);
}
HANDLE open(char const* directory,bool subtree,DWORD mask) noexcept {
    if(!directory || !*directory) {
        ::SetLastError(ERROR_INVALID_PARAMETER);
        return INVALID_HANDLE_VALUE;
    }
    return ::FindFirstChangeNotificationA(directory,subtree?TRUE:FALSE,mask);
}
bool rearm(HANDLE watch) noexcept {
    return watch && watch!=INVALID_HANDLE_VALUE &&
           ::FindNextChangeNotification(watch)!=FALSE;
}
void close(HANDLE watch) noexcept {
    if(watch && watch!=INVALID_HANDLE_VALUE)
        ::FindCloseChangeNotification(watch);
}
} }
