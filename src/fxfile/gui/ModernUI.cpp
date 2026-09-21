//
// Copyright (c) 2026 flyExplorer contributors.
//
// Windows 11 UI foundation: DPI, system typography and theme metrics.
//

#include "stdafx.h"
#include "ModernUI.h"

#include <roapi.h>
#include <winstring.h>
#include <windows.ui.viewmanagement.h>

#pragma comment(lib, "RuntimeObject.lib")

namespace fxfile
{
namespace ui
{
namespace
{
typedef UINT (WINAPI *GetDpiForWindowProc)(HWND);
typedef BOOL (WINAPI *SystemParametersInfoForDpiProc)(UINT, UINT, PVOID, UINT, UINT);
typedef HRESULT (WINAPI *DwmSetWindowAttributeProc)(HWND, DWORD, LPCVOID, DWORD);
typedef HRESULT (WINAPI *SetWindowThemeProc)(HWND, LPCWSTR, LPCWSTR);

class ThemeSettings
{
public:
    ThemeSettings(void)
        : mInitialized(XPR_FALSE)
        , mSettings(XPR_NULL)
    {
        const HRESULT sInitResult = ::RoInitialize(RO_INIT_SINGLETHREADED);
        if (FAILED(sInitResult))
            return;

        mInitialized = XPR_TRUE;

        HSTRING_HEADER sHeader = {0};
        HSTRING sClassId = XPR_NULL;
        const wchar_t *sRuntimeClass = RuntimeClass_Windows_UI_ViewManagement_UISettings;

        HRESULT sResult = ::WindowsCreateStringReference(
            sRuntimeClass,
            static_cast<UINT32>(::wcslen(sRuntimeClass)),
            &sHeader,
            &sClassId);
        if (FAILED(sResult))
            return;

        IInspectable *sInspectable = XPR_NULL;
        sResult = ::RoActivateInstance(sClassId, &sInspectable);
        if (SUCCEEDED(sResult) && XPR_IS_NOT_NULL(sInspectable))
        {
            sInspectable->QueryInterface(
                __uuidof(ABI::Windows::UI::ViewManagement::IUISettings3),
                reinterpret_cast<void **>(&mSettings));
        }

        if (XPR_IS_NOT_NULL(sInspectable))
            sInspectable->Release();
    }

    ~ThemeSettings(void)
    {
        if (XPR_IS_NOT_NULL(mSettings))
            mSettings->Release();

        if (XPR_IS_TRUE(mInitialized))
            ::RoUninitialize();
    }

    xpr_bool_t getColor(
        ABI::Windows::UI::ViewManagement::UIColorType aColorType,
        COLORREF &aColor) const
    {
        if (XPR_IS_NULL(mSettings))
            return XPR_FALSE;

        ABI::Windows::UI::Color sColor = {0};
        const HRESULT sResult = mSettings->GetColorValue(aColorType, &sColor);
        if (FAILED(sResult))
            return XPR_FALSE;

        aColor = RGB(sColor.R, sColor.G, sColor.B);
        return XPR_TRUE;
    }

private:
    xpr_bool_t mInitialized;
    ABI::Windows::UI::ViewManagement::IUISettings3 *mSettings;
};

ThemeSettings &getThemeSettings(void)
{
    static thread_local ThemeSettings sThemeSettings;
    return sThemeSettings;
}

#ifndef DWMWA_USE_IMMERSIVE_DARK_MODE
#define DWMWA_USE_IMMERSIVE_DARK_MODE 20
#endif

COLORREF blendColor(COLORREF aBase, COLORREF aOverlay, xpr_uint_t aOverlayPercent)
{
    if (aOverlayPercent > 100)
        aOverlayPercent = 100;

    const xpr_uint_t sBasePercent = 100 - aOverlayPercent;

    const xpr_uint_t sRed =
        (GetRValue(aBase) * sBasePercent + GetRValue(aOverlay) * aOverlayPercent) / 100;
    const xpr_uint_t sGreen =
        (GetGValue(aBase) * sBasePercent + GetGValue(aOverlay) * aOverlayPercent) / 100;
    const xpr_uint_t sBlue =
        (GetBValue(aBase) * sBasePercent + GetBValue(aOverlay) * aOverlayPercent) / 100;

    return RGB(sRed, sGreen, sBlue);
}

xpr_bool_t isDarkColor(COLORREF aColor)
{
    // ITU-R BT.601 luma approximation. This is intentionally based on the
    // effective system palette instead of undocumented dark-mode APIs.
    const xpr_uint_t sLuma =
        (GetRValue(aColor) * 299 +
         GetGValue(aColor) * 587 +
         GetBValue(aColor) * 114) / 1000;

    return sLuma < 128 ? XPR_TRUE : XPR_FALSE;
}
} // namespace anonymous

xpr_uint_t ModernUI::getDpi(HWND aHwnd)
{
    HMODULE sUser32 = ::GetModuleHandle(XPR_STRING_LITERAL("user32.dll"));
    if (XPR_IS_NOT_NULL(sUser32))
    {
        GetDpiForWindowProc sGetDpiForWindow =
            reinterpret_cast<GetDpiForWindowProc>(::GetProcAddress(sUser32, "GetDpiForWindow"));

        if (XPR_IS_NOT_NULL(sGetDpiForWindow) && XPR_IS_NOT_NULL(aHwnd))
        {
            const UINT sDpi = sGetDpiForWindow(aHwnd);
            if (sDpi != 0)
                return static_cast<xpr_uint_t>(sDpi);
        }
    }

    HDC sDC = ::GetDC(aHwnd);
    if (XPR_IS_NOT_NULL(sDC))
    {
        const xpr_sint_t sDpi = ::GetDeviceCaps(sDC, LOGPIXELSX);
        ::ReleaseDC(aHwnd, sDC);

        if (sDpi > 0)
            return static_cast<xpr_uint_t>(sDpi);
    }

    return kDefaultDpi;
}

xpr_sint_t ModernUI::scale(xpr_sint_t aValue, xpr_uint_t aDpi)
{
    if (aDpi == 0)
        aDpi = kDefaultDpi;

    return ::MulDiv(aValue, static_cast<xpr_sint_t>(aDpi), kDefaultDpi);
}

xpr_sint_t ModernUI::scaleForWindow(xpr_sint_t aValue, HWND aHwnd)
{
    return scale(aValue, getDpi(aHwnd));
}

xpr_bool_t ModernUI::getUIFont(LOGFONT &aLogFont, HWND aHwnd)
{
    ::ZeroMemory(&aLogFont, sizeof(aLogFont));

    NONCLIENTMETRICS sMetrics = {0};
    sMetrics.cbSize = sizeof(sMetrics);

    xpr_bool_t sLoaded = XPR_FALSE;
    const xpr_uint_t sDpi = getDpi(aHwnd);

    HMODULE sUser32 = ::GetModuleHandle(XPR_STRING_LITERAL("user32.dll"));
    if (XPR_IS_NOT_NULL(sUser32))
    {
        SystemParametersInfoForDpiProc sSystemParametersInfoForDpi =
            reinterpret_cast<SystemParametersInfoForDpiProc>(
                ::GetProcAddress(sUser32, "SystemParametersInfoForDpi"));

        if (XPR_IS_NOT_NULL(sSystemParametersInfoForDpi))
        {
            sLoaded = sSystemParametersInfoForDpi(
                SPI_GETNONCLIENTMETRICS,
                sizeof(sMetrics),
                &sMetrics,
                0,
                sDpi) ? XPR_TRUE : XPR_FALSE;
        }
    }

    if (XPR_IS_FALSE(sLoaded))
    {
        sLoaded = ::SystemParametersInfo(
            SPI_GETNONCLIENTMETRICS,
            sizeof(sMetrics),
            &sMetrics,
            0) ? XPR_TRUE : XPR_FALSE;
    }

    if (XPR_IS_TRUE(sLoaded))
    {
        aLogFont = sMetrics.lfMessageFont;
        if (aLogFont.lfFaceName[0] == XPR_STRING_LITERAL('\0'))
            aLogFont = sMetrics.lfMenuFont;

        return XPR_TRUE;
    }

    HFONT sFont = static_cast<HFONT>(::GetStockObject(DEFAULT_GUI_FONT));
    if (XPR_IS_NOT_NULL(sFont) && ::GetObject(sFont, sizeof(aLogFont), &aLogFont) != 0)
        return XPR_TRUE;

    return XPR_FALSE;
}

xpr_bool_t ModernUI::isHighContrast(void)
{
    HIGHCONTRAST sHighContrast = {0};
    sHighContrast.cbSize = sizeof(sHighContrast);

    if (::SystemParametersInfo(
            SPI_GETHIGHCONTRAST,
            sizeof(sHighContrast),
            &sHighContrast,
            0) == XPR_FALSE)
    {
        return XPR_FALSE;
    }

    return (sHighContrast.dwFlags & HCF_HIGHCONTRASTON) != 0 ? XPR_TRUE : XPR_FALSE;
}

ThemePalette ModernUI::getPalette(void)
{
    ThemePalette sPalette;

    sPalette.mWindow        = ::GetSysColor(COLOR_WINDOW);
    sPalette.mSurface       = blendColor(
        ::GetSysColor(COLOR_WINDOW),
        ::GetSysColor(COLOR_3DFACE),
        35);
    sPalette.mText          = ::GetSysColor(COLOR_WINDOWTEXT);
    sPalette.mSecondaryText = ::GetSysColor(COLOR_GRAYTEXT);
    sPalette.mBorder        = ::GetSysColor(COLOR_3DSHADOW);
    sPalette.mSeparator     = ::GetSysColor(COLOR_3DLIGHT);
    sPalette.mSelection     = ::GetSysColor(COLOR_HIGHLIGHT);
    sPalette.mSelectionText = ::GetSysColor(COLOR_HIGHLIGHTTEXT);
    sPalette.mHighContrast  = isHighContrast();
    sPalette.mDark          = isDarkColor(sPalette.mWindow);

    // Microsoft documents UISettings foreground/background colors as the
    // Win32 signal for the user's app light/dark preference. Keep High
    // Contrast on the system-color path and retain the legacy system-color
    // palette if Windows Runtime activation is unavailable for any reason.
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        ThemeSettings &sThemeSettings = getThemeSettings();
        COLORREF sBackground = 0;
        COLORREF sForeground = 0;

        if (XPR_IS_TRUE(sThemeSettings.getColor(
                ABI::Windows::UI::ViewManagement::UIColorType_Background,
                sBackground)) &&
            XPR_IS_TRUE(sThemeSettings.getColor(
                ABI::Windows::UI::ViewManagement::UIColorType_Foreground,
                sForeground)))
        {
            // A light foreground is the documented indicator that the app
            // color mode is dark.
            sPalette.mDark = XPR_IS_FALSE(isDarkColor(sForeground));

            if (XPR_IS_TRUE(sPalette.mDark))
            {
                sPalette.mWindow        = sBackground;
                sPalette.mSurface       = blendColor(sBackground, sForeground, 8);
                sPalette.mText          = sForeground;
                sPalette.mSecondaryText = blendColor(sBackground, sForeground, 65);
                sPalette.mBorder        = blendColor(sBackground, sForeground, 24);
                sPalette.mSeparator     = blendColor(sBackground, sForeground, 16);
            }
        }
    }

    sPalette.mHover = blendColor(
        sPalette.mSurface,
        sPalette.mSelection,
        12);

    return sPalette;
}

xpr_bool_t ModernUI::applyWindowFrameTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd))
        return XPR_FALSE;

    // DWMWA_USE_IMMERSIVE_DARK_MODE is documented for Windows 11 build 22000+.
    // Resolve DWM dynamically so older Windows versions keep the existing
    // light frame instead of gaining a new load-time dependency.
    HMODULE sDwmApi = ::LoadLibrary(XPR_STRING_LITERAL("dwmapi.dll"));
    if (XPR_IS_NULL(sDwmApi))
        return XPR_FALSE;

    DwmSetWindowAttributeProc sDwmSetWindowAttribute =
        reinterpret_cast<DwmSetWindowAttributeProc>(
            ::GetProcAddress(sDwmApi, "DwmSetWindowAttribute"));

    xpr_bool_t sApplied = XPR_FALSE;
    if (XPR_IS_NOT_NULL(sDwmSetWindowAttribute))
    {
        const BOOL sUseDarkFrame = XPR_IS_TRUE(isHighContrast()) ? FALSE : TRUE;
        const HRESULT sResult = sDwmSetWindowAttribute(
            aHwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            &sUseDarkFrame,
            sizeof(sUseDarkFrame));

        sApplied = SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
    }

    ::FreeLibrary(sDwmApi);
    return sApplied;
}

xpr_bool_t ModernUI::applyExplorerControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd))
        return XPR_FALSE;

    // SetWindowTheme is documented, but resolving it dynamically keeps the
    // ModernUI foundation safe on systems where uxtheme is unavailable.
    HMODULE sUxTheme = ::LoadLibrary(XPR_STRING_LITERAL("uxtheme.dll"));
    if (XPR_IS_NULL(sUxTheme))
        return XPR_FALSE;

    SetWindowThemeProc sSetWindowTheme =
        reinterpret_cast<SetWindowThemeProc>(
            ::GetProcAddress(sUxTheme, "SetWindowTheme"));

    xpr_bool_t sApplied = XPR_FALSE;
    if (XPR_IS_NOT_NULL(sSetWindowTheme))
    {
        // High Contrast should retain the system's default control rendering.
        // The Explorer theme is a documented/common Win32 visual-style opt-in
        // already used by flyExplorer list/tree controls.
        const LPCWSTR sSubAppName =
            XPR_IS_TRUE(isHighContrast()) ? XPR_NULL : L"Explorer";
        const HRESULT sResult = sSetWindowTheme(aHwnd, sSubAppName, XPR_NULL);
        sApplied = SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
    }

    ::FreeLibrary(sUxTheme);
    return sApplied;
}
xpr_bool_t ModernUI::resetControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd))
        return XPR_FALSE;

    HMODULE sUxTheme = ::LoadLibrary(XPR_STRING_LITERAL("uxtheme.dll"));
    if (XPR_IS_NULL(sUxTheme))
        return XPR_FALSE;

    SetWindowThemeProc sSetWindowTheme =
        reinterpret_cast<SetWindowThemeProc>(
            ::GetProcAddress(sUxTheme, "SetWindowTheme"));

    xpr_bool_t sApplied = XPR_FALSE;
    if (XPR_IS_NOT_NULL(sSetWindowTheme))
    {
        const HRESULT sResult = sSetWindowTheme(aHwnd, XPR_NULL, XPR_NULL);
        sApplied = SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
    }

    ::FreeLibrary(sUxTheme);
    return sApplied;
}
} // namespace ui
} // namespace fxfile
