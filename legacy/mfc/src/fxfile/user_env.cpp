//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "user_env.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
#define PACK_VERSION(major,minor) MAKELONG(minor,major)

static xpr_bool_t getWindowsFileVersion(DWORD &aMajor, DWORD &aMinor, DWORD &aBuild)
{
    xpr_tchar_t sKernelPath[XPR_MAX_PATH + 1] = {0};
    HMODULE sKernel = ::GetModuleHandle(XPR_STRING_LITERAL("kernel32.dll"));
    if (XPR_IS_NULL(sKernel) ||
        ::GetModuleFileName(sKernel, sKernelPath, XPR_COUNT_OF(sKernelPath)) == 0)
        return XPR_FALSE;

    DWORD sHandle = 0;
    DWORD sSize = ::GetFileVersionInfoSize(sKernelPath, &sHandle);
    if (sSize == 0)
        return XPR_FALSE;

    BYTE *sVersionData = new BYTE[sSize];
    xpr_bool_t sResult = XPR_FALSE;

    if (::GetFileVersionInfo(sKernelPath, 0, sSize, sVersionData) != XPR_FALSE)
    {
        VS_FIXEDFILEINFO *sFixedInfo = XPR_NULL;
        UINT sFixedInfoSize = 0;
        if (::VerQueryValue(sVersionData, XPR_STRING_LITERAL("\\"), (LPVOID *)&sFixedInfo, &sFixedInfoSize) != XPR_FALSE &&
            XPR_IS_NOT_NULL(sFixedInfo) &&
            sFixedInfoSize >= sizeof(VS_FIXEDFILEINFO) &&
            sFixedInfo->dwSignature == VS_FFI_SIGNATURE)
        {
            aMajor = HIWORD(sFixedInfo->dwFileVersionMS);
            aMinor = LOWORD(sFixedInfo->dwFileVersionMS);
            aBuild = HIWORD(sFixedInfo->dwFileVersionLS);
            sResult = XPR_TRUE;
        }
    }

    XPR_SAFE_DELETE_ARRAY(sVersionData);
    return sResult;
}

UserEnv::UserEnv(void)
{
    getUserEnvironment();
}

UserEnv::~UserEnv(void)
{
}

void UserEnv::getUserEnvironment(void)
{
    ::ZeroMemory(&mOSVerInfo, sizeof(mOSVerInfo));
    mOSVerInfo.dwOSVersionInfoSize = sizeof(mOSVerInfo);
    mOSVerInfo.dwPlatformId = VER_PLATFORM_WIN32_NT;

    DWORD sMajor = 10;
    DWORD sMinor = 0;
    DWORD sBuild = 0;
    getWindowsFileVersion(sMajor, sMinor, sBuild);
    mOSVerInfo.dwMajorVersion = sMajor;
    mOSVerInfo.dwMinorVersion = sMinor;
    mOSVerInfo.dwBuildNumber = sBuild;

    DWORD sComctl32DllVer = getDllVersion(XPR_STRING_LITERAL("Comctl32.dll"));
    DWORD sShlwapiDllVer  = getDllVersion(XPR_STRING_LITERAL("Shlwapi.dll"));
    DWORD sShell32DllVer  = getDllVersion(XPR_STRING_LITERAL("Shell32.dll"));

    if (sShell32DllVer > PACK_VERSION(6,1))
    {
        mShellVer = XPR_STRING_LITERAL("6.X");
        mInetExpVer = InetExp50More;
    }
    else if (sShell32DllVer == PACK_VERSION(6,1))
    {
        mShellVer = XPR_STRING_LITERAL("6.1");
        mInetExpVer = InetExp50More;
    }
    else if (sComctl32DllVer >= PACK_VERSION(6,0))
    {
        mShellVer = XPR_STRING_LITERAL("6.0");
        mInetExpVer = InetExp50More;
    }
    else if (sComctl32DllVer >= PACK_VERSION(5,81))
    {
        mShellVer = XPR_STRING_LITERAL("5.81");
        mInetExpVer = InetExp50More;
    }
    else if (sComctl32DllVer >= PACK_VERSION(5,8))
    {
        mShellVer = XPR_STRING_LITERAL("5.8");
        mInetExpVer = InetExp50More;
    }
    else if (sShlwapiDllVer >= PACK_VERSION(5,0))
    {
        mShellVer = XPR_STRING_LITERAL("5.0");
        mInetExpVer = InetExp50More;
    }
    else if (sShell32DllVer >= PACK_VERSION(4,72))
    {
        mShellVer = XPR_STRING_LITERAL("4.72");
        mInetExpVer = InetExp50Under;
    }
    else if (sShell32DllVer >= PACK_VERSION(4,71))
    {
        mShellVer = XPR_STRING_LITERAL("4.71");
        mInetExpVer = InetExp50Under;
    }
    else if (sShell32DllVer >= PACK_VERSION(4,7))
    {
        mShellVer = XPR_STRING_LITERAL("4.7");
        mInetExpVer = InetExp50Under;
    }
    else if (sShell32DllVer >= PACK_VERSION(4,0))
    {
        mShellVer = XPR_STRING_LITERAL("4.0");
        mInetExpVer = InetExp50Under;
    }
    else
    {
        mShellVer = XPR_STRING_LITERAL("Unknown");
        mInetExpVer = InetExp50Under;
    }
}

DWORD UserEnv::getDllVersion(const xpr_tchar_t *aDllName)
{
    HINSTANCE sInstance;
    DWORD sVersion = 0;

    sInstance = ::LoadLibrary(aDllName);
    if (XPR_IS_NOT_NULL(sInstance))
    {
        DLLGETVERSIONPROC sDllGetVersionFunc = (DLLGETVERSIONPROC)::GetProcAddress(sInstance, "DllGetVersion");
        if (XPR_IS_NOT_NULL(sDllGetVersionFunc))
        {
            DLLVERSIONINFO sDllVersionInfo = {0};
            sDllVersionInfo.cbSize = sizeof(sDllVersionInfo);

            HRESULT sHResult = (*sDllGetVersionFunc)(&sDllVersionInfo);

            if (SUCCEEDED(sHResult))
                sVersion = PACK_VERSION(sDllVersionInfo.dwMajorVersion, sDllVersionInfo.dwMinorVersion);
        }

        ::FreeLibrary(sInstance);
    }

    return sVersion;
}

void UserEnv::getDllVersion(const xpr_tchar_t *aDllName, LPDWORD aMajorVersion, LPDWORD aMinorVersion, LPDWORD aBuildNumber)
{
    HINSTANCE sInstance;
    DWORD sVersion = 0;

    sInstance = ::LoadLibrary(aDllName);
    if (XPR_IS_NOT_NULL(sInstance))
    {
        DLLGETVERSIONPROC sDllGetVersionFunc = (DLLGETVERSIONPROC)::GetProcAddress(sInstance, "DllGetVersion");
        if (XPR_IS_NOT_NULL(sDllGetVersionFunc))
        {
            DLLVERSIONINFO sDllVersionInfo = {0};
            sDllVersionInfo.cbSize = sizeof(sDllVersionInfo);

            HRESULT sHResult = (*sDllGetVersionFunc)(&sDllVersionInfo);

            if (SUCCEEDED(sHResult))
            {
                if (XPR_IS_NOT_NULL(aMajorVersion))
                    *aMajorVersion = sDllVersionInfo.dwMajorVersion;

                if (XPR_IS_NOT_NULL(aMinorVersion))
                    *aMinorVersion = sDllVersionInfo.dwMinorVersion;

                if (XPR_IS_NOT_NULL(aBuildNumber))
                    *aBuildNumber = sDllVersionInfo.dwBuildNumber;
            }
        }

        ::FreeLibrary(sInstance);
    }
}
} // namespace fxfile
