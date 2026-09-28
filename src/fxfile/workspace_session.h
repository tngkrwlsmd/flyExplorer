// Isolated named-workspace sessions: only exact files in marked,
// non-reparse temporary directories. Never recursively remove paths.
#ifndef FXFILE_WORKSPACE_SESSION_H
#define FXFILE_WORKSPACE_SESSION_H
#include <windows.h>
#include <tchar.h>
namespace fxfile { namespace workspace_session {
inline const TCHAR *marker() { return _T("fxfile-workspace-owned.marker"); }
inline const char *magic() { return "flyExplorer-ephemeral-workspace-v1\n"; }
inline CString path(LPCTSTR dir, LPCTSTR file) {
    CString result(dir); result += _T("\\"); result += file; return result;
}
inline bool ownedDir(LPCTSTR dir) {
    if (!dir || !*dir) return false;
    TCHAR temp[MAX_PATH] = {0};
    DWORD n = ::GetTempPath(_countof(temp), temp);
    if (!n || n >= _countof(temp)) return false;
    size_t root = _tcslen(temp);
    if (_tcsnicmp(dir, temp, root)) return false;
    LPCTSTR leaf = dir + root;
    if (_tcslen(leaf) != 11 || _tcsnicmp(leaf,_T("fxw"),3) ||
        _tcsicmp(leaf+7,_T(".tmp"))) return false;
    for (int i=3; i<7; ++i) {
        TCHAR c=leaf[i];
        if (!((c>=_T('0') && c<=_T('9')) ||
              (c>=_T('a') && c<=_T('f')) ||
              (c>=_T('A') && c<=_T('F')))) return false;
    }
    DWORD attrs=::GetFileAttributes(dir);
    return attrs!=INVALID_FILE_ATTRIBUTES &&
           (attrs & FILE_ATTRIBUTE_DIRECTORY) &&
           !(attrs & FILE_ATTRIBUTE_REPARSE_POINT);
}
inline bool allowedFile(LPCTSTR name) {
    static const TCHAR *allowed[] = {
       _T("fxfile.conf"), _T("fxfile-main.conf"),
       _T("fxfile-bookmark.conf"), _T("fxfile-file_scrap.conf"),
       _T("fxfile-search_dir.conf"), _T("fxfile-folder_layout.conf"),
       _T("fxfile-dlg_state.conf"), _T("fxfile-accel.dat"),
       _T("fxfile-coolbar.dat"), _T("fxfile-toolbar.dat"),
       _T("fxfile-workspace-owned.marker")
    };
    for (int i=0; i<static_cast<int>(_countof(allowed)); ++i)
        if (_tcsicmp(name,allowed[i])==0) return true;
    return false;
}
inline HANDLE lockMarker(LPCTSTR dir) {
    if (!ownedDir(dir)) return INVALID_HANDLE_VALUE;
    CString file=path(dir,marker());
    DWORD attrs=::GetFileAttributes(file);
    if (attrs==INVALID_FILE_ATTRIBUTES ||
        (attrs & (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)))
        return INVALID_HANDLE_VALUE;
    // Exclusive open fails while a different live owned child holds it.
    HANDLE h=::CreateFile(file,GENERIC_READ,0,NULL,OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    if (h==INVALID_HANDLE_VALUE) return h;
    char data[80]={0};
    DWORD n=0;
    const size_t size=strlen(magic());
    if (!::ReadFile(h,data,sizeof(data),&n,NULL) ||
        n!=size || memcmp(data,magic(),size)!=0) {
        ::CloseHandle(h);
        return INVALID_HANDLE_VALUE;
    }
    return h;
}
inline bool writeMarker(LPCTSTR dir) {
    if (!ownedDir(dir)) return false;
    CString file=path(dir,marker());
    HANDLE h=::CreateFile(file,GENERIC_WRITE,0,NULL,CREATE_NEW,
                         FILE_ATTRIBUTE_NORMAL,NULL);
    if (h==INVALID_HANDLE_VALUE) return false;
    DWORD n=0;
    size_t size=strlen(magic());
    bool ok=::WriteFile(h,magic(),static_cast<DWORD>(size),&n,NULL)!=0
            && n==size && ::FlushFileBuffers(h)!=0;
    ::CloseHandle(h);
    if (!ok) ::DeleteFile(file);
    return ok;
}
inline bool cleanup(LPCTSTR dir) {
    if (!ownedDir(dir)) return false;
    HANDLE markerHandle=lockMarker(dir);
    if (markerHandle==INVALID_HANDLE_VALUE) return false;
    // Validate the entire direct directory BEFORE deleting anything.
    // No recursion, unknown files, subdirectories or reparse entries.
    CString pattern=path(dir,_T("*"));
    WIN32_FIND_DATA data={0};
    HANDLE finder=::FindFirstFile(pattern,&data);
    bool safe=finder!=INVALID_HANDLE_VALUE;
    if (safe) {
        do {
            if (!_tcscmp(data.cFileName,_T(".")) ||
                !_tcscmp(data.cFileName,_T(".."))) continue;
            if (!allowedFile(data.cFileName) ||
                (data.dwFileAttributes &
                   (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY))) {
                safe=false; break;
            }
        } while (::FindNextFile(finder,&data));
        ::FindClose(finder);
    }
    ::CloseHandle(markerHandle);
    if (!safe) return false;
    static const TCHAR *others[] = {
       _T("fxfile.conf"), _T("fxfile-main.conf"),
       _T("fxfile-bookmark.conf"), _T("fxfile-file_scrap.conf"),
       _T("fxfile-search_dir.conf"), _T("fxfile-folder_layout.conf"),
       _T("fxfile-dlg_state.conf"), _T("fxfile-accel.dat"),
       _T("fxfile-coolbar.dat"), _T("fxfile-toolbar.dat")
    };
    bool ok=true;
    for (int i=0; i<static_cast<int>(_countof(others)); ++i) {
        CString f=path(dir,others[i]);
        DWORD a=::GetFileAttributes(f);
        if (a==INVALID_FILE_ATTRIBUTES) continue;
        if (a & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DIRECTORY) ||
            ::DeleteFile(f)==FALSE) ok=false;
    }
    if (!ok) return false; // retain marker for a later retry
    if (!::DeleteFile(path(dir,marker()))) return false;
    return ::RemoveDirectory(dir)!=FALSE;
}
inline void reapStale() {
    TCHAR temp[MAX_PATH]={0};
    DWORD n=::GetTempPath(_countof(temp),temp);
    if (!n || n>=_countof(temp)) return;
    CString pattern(temp);pattern+=_T("fxw????.tmp");
    WIN32_FIND_DATA data={0};
    HANDLE finder=::FindFirstFile(pattern,&data);
    if (finder==INVALID_HANDLE_VALUE) return;
    FILETIME current={0};
    ::GetSystemTimeAsFileTime(&current);
    ULARGE_INTEGER now={0};
    now.LowPart=current.dwLowDateTime;
    now.HighPart=current.dwHighDateTime;
    unsigned scanned=0;
    do {
        if (++scanned>64) break; // bounded per launch, never aggressive
        if (!(data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
             (data.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) continue;
        CString dir(temp);dir+=data.cFileName;
        if (!ownedDir(dir)) continue;
        WIN32_FILE_ATTRIBUTE_DATA info={0};
        if (!::GetFileAttributesEx(path(dir,marker()),
               GetFileExInfoStandard,&info) ||
            (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT)) continue;
        ULARGE_INTEGER modified={0};
        modified.LowPart=info.ftLastWriteTime.dwLowDateTime;
        modified.HighPart=info.ftLastWriteTime.dwHighDateTime;
        // A still-running child has its marker locked; never remove
        // recent failed launches. Retry only after at least 24 hours.
        if (now.QuadPart>modified.QuadPart &&
            now.QuadPart-modified.QuadPart>864000000000ULL)
            cleanup(dir);
    } while (::FindNextFile(finder,&data));
    ::FindClose(finder);
}
}} // namespace fxfile::workspace_session
#endif
