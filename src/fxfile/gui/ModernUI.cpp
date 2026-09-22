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

xpr_sint_t gThemeMode = ModernUI::ThemeModeSystem;

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

#ifndef DWMWA_WINDOW_CORNER_PREFERENCE
#define DWMWA_WINDOW_CORNER_PREFERENCE 33
#endif

#ifndef DWMWCP_DEFAULT
#define DWMWCP_DEFAULT 0
#define DWMWCP_ROUND   2
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

const xpr_tchar_t kThemeApplyGuardProp[] =
    XPR_STRING_LITERAL("fxfile.ModernUI.ThemeApplyGuard");

xpr_bool_t beginControlThemeChange(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return XPR_FALSE;

    // SetWindowTheme synchronously sends WM_THEMECHANGED to some common and
    // custom controls. A WM_THEMECHANGED handler that reapplies the same
    // association would otherwise recurse until the process terminates.
    if (XPR_IS_NOT_NULL(::GetProp(aHwnd, kThemeApplyGuardProp)))
        return XPR_FALSE;

    return ::SetProp(
        aHwnd,
        kThemeApplyGuardProp,
        reinterpret_cast<HANDLE>(1)) != FALSE ? XPR_TRUE : XPR_FALSE;
}

void endControlThemeChange(HWND aHwnd)
{
    if (XPR_IS_NOT_NULL(aHwnd))
        ::RemoveProp(aHwnd, kThemeApplyGuardProp);
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

xpr_sint_t ModernUI::getCommandBarHeight(HWND aHwnd)
{
    return scaleForWindow(40, aHwnd);
}

xpr_sint_t ModernUI::getCommandButtonExtent(HWND aHwnd)
{
    return scaleForWindow(36, aHwnd);
}

xpr_sint_t ModernUI::getCommandHorizontalPadding(HWND aHwnd)
{
    return scaleForWindow(10, aHwnd);
}

xpr_sint_t ModernUI::getCommandVerticalPadding(HWND aHwnd)
{
    return scaleForWindow(7, aHwnd);
}

xpr_sint_t ModernUI::getAddressBarHeight(HWND aHwnd)
{
    return scaleForWindow(36, aHwnd);
}

xpr_sint_t ModernUI::getAddressHorizontalInset(HWND aHwnd)
{
    return scaleForWindow(6, aHwnd);
}

xpr_sint_t ModernUI::getAddressVerticalInset(HWND aHwnd)
{
    return scaleForWindow(4, aHwnd);
}

xpr_sint_t ModernUI::getAddressTextMargin(HWND aHwnd)
{
    return scaleForWindow(10, aHwnd);
}

xpr_sint_t ModernUI::getPopupItemPadding(HWND aHwnd)
{
    return scaleForWindow(6, aHwnd);
}

xpr_sint_t ModernUI::getPopupItemHeight(HWND aHwnd)
{
    return scaleForWindow(30, aHwnd);
}

xpr_sint_t ModernUI::getPopupIconGutter(HWND aHwnd)
{
    return scaleForWindow(32, aHwnd);
}

xpr_sint_t ModernUI::getPopupSeparatorHeight(HWND aHwnd)
{
    return scaleForWindow(8, aHwnd);
}

xpr_sint_t ModernUI::getPopupSeparatorInset(HWND aHwnd)
{
    return scaleForWindow(12, aHwnd);
}

xpr_sint_t ModernUI::getPopupShortcutGap(HWND aHwnd)
{
    return scaleForWindow(14, aHwnd);
}

xpr_sint_t ModernUI::getPopupBorderThickness(HWND aHwnd)
{
    return max(1, scaleForWindow(1, aHwnd));
}

xpr_sint_t ModernUI::getContentRowHeight(HWND aHwnd)
{
    return scaleForWindow(24, aHwnd);
}

xpr_sint_t ModernUI::getTreeRowHeight(HWND aHwnd)
{
    return getContentRowHeight(aHwnd);
}

xpr_sint_t ModernUI::getTreeIndent(HWND aHwnd)
{
    return scaleForWindow(20, aHwnd);
}

xpr_sint_t ModernUI::getListHeaderTextPadding(HWND aHwnd)
{
    return scaleForWindow(8, aHwnd);
}

xpr_sint_t ModernUI::getTabHeight(HWND aHwnd)
{
    return scaleForWindow(32, aHwnd);
}

xpr_sint_t ModernUI::getTabHorizontalPadding(HWND aHwnd)
{
    return scaleForWindow(10, aHwnd);
}

xpr_sint_t ModernUI::getPaneSeparatorThickness(HWND aHwnd)
{
    return max(1, scaleForWindow(2, aHwnd));
}

xpr_sint_t ModernUI::getActivePaneIndicatorThickness(HWND aHwnd)
{
    return max(2, scaleForWindow(3, aHwnd));
}

xpr_sint_t ModernUI::getControlCornerRadius(HWND aHwnd)
{
    return scaleForWindow(6, aHwnd);
}

xpr_sint_t ModernUI::getCardCornerRadius(HWND aHwnd)
{
    return scaleForWindow(8, aHwnd);
}

xpr_sint_t ModernUI::getPopupCornerRadius(HWND aHwnd)
{
    return scaleForWindow(8, aHwnd);
}

xpr_sint_t ModernUI::getMenuBarItemHeight(HWND aHwnd)
{
    return scaleForWindow(32, aHwnd);
}

xpr_sint_t ModernUI::getSettingsNavRowHeight(HWND aHwnd)
{
    return scaleForWindow(34, aHwnd);
}

xpr_sint_t ModernUI::getSettingsPanelPadding(HWND aHwnd)
{
    return scaleForWindow(14, aHwnd);
}

xpr_sint_t ModernUI::getDialogControlHeight(HWND aHwnd)
{
    return scaleForWindow(30, aHwnd);
}

xpr_sint_t ModernUI::getDialogSectionSpacing(HWND aHwnd)
{
    return scaleForWindow(12, aHwnd);
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

HICON ModernUI::loadIconResource(
    HINSTANCE aInstance,
    xpr_uint_t aResourceId,
    HWND aHwnd,
    xpr_sint_t aLogicalSize)
{
    if (XPR_IS_NULL(aInstance) || aResourceId == 0 || aLogicalSize <= 0)
        return XPR_NULL;

    const xpr_sint_t sPixelSize = scale(aLogicalSize, getDpi(aHwnd));
    return static_cast<HICON>(::LoadImage(
        aInstance,
        MAKEINTRESOURCE(aResourceId),
        IMAGE_ICON,
        sPixelSize,
        sPixelSize,
        LR_DEFAULTCOLOR));
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

void ModernUI::setThemeMode(xpr_sint_t aThemeMode)
{
    if (aThemeMode < ThemeModeSystem || aThemeMode > ThemeModeDark)
        aThemeMode = ThemeModeSystem;

    gThemeMode = aThemeMode;
}

xpr_sint_t ModernUI::getThemeMode(void)
{
    return gThemeMode;
}

ThemePalette ModernUI::getPalette(void)
{
    ThemePalette sPalette;

    const COLORREF sSystemWindow = ::GetSysColor(COLOR_WINDOW);
    const COLORREF sSystemFace = ::GetSysColor(COLOR_3DFACE);
    const COLORREF sSystemText = ::GetSysColor(COLOR_WINDOWTEXT);

    sPalette.mWindow        = sSystemWindow;
    sPalette.mSurface       = blendColor(sSystemWindow, sSystemFace, 35);
    sPalette.mText          = sSystemText;
    sPalette.mSecondaryText = ::GetSysColor(COLOR_GRAYTEXT);
    sPalette.mBorder        = ::GetSysColor(COLOR_3DSHADOW);
    sPalette.mSeparator     = ::GetSysColor(COLOR_3DLIGHT);
    sPalette.mSelection     = ::GetSysColor(COLOR_HIGHLIGHT);
    sPalette.mSelectionText = ::GetSysColor(COLOR_HIGHLIGHTTEXT);
    sPalette.mHighContrast  = isHighContrast();
    sPalette.mDark          = isDarkColor(sPalette.mWindow);

    // High Contrast always owns the final colors. Outside High Contrast,
    // ThemeModeSystem follows the documented UISettings app-color signal.
    // Explicit Light keeps the Win32 system-color baseline, while explicit
    // Dark reuses the native dark palette when Windows is dark and otherwise
    // derives a dark palette from the user's system window/text colors.
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        const xpr_sint_t sThemeMode = getThemeMode();

        ThemeSettings &sThemeSettings = getThemeSettings();
        COLORREF sBackground = 0;
        COLORREF sForeground = 0;
        const xpr_bool_t sHasSystemTheme =
            XPR_IS_TRUE(sThemeSettings.getColor(
                ABI::Windows::UI::ViewManagement::UIColorType_Background,
                sBackground)) &&
            XPR_IS_TRUE(sThemeSettings.getColor(
                ABI::Windows::UI::ViewManagement::UIColorType_Foreground,
                sForeground)) ?
            XPR_TRUE :
            XPR_FALSE;

        xpr_bool_t sSystemDark = XPR_FALSE;
        if (XPR_IS_TRUE(sHasSystemTheme))
            sSystemDark = XPR_IS_FALSE(isDarkColor(sForeground));

        if ((sThemeMode == ThemeModeSystem && XPR_IS_TRUE(sSystemDark)) ||
            (sThemeMode == ThemeModeDark && XPR_IS_TRUE(sSystemDark)))
        {
            sPalette.mDark          = XPR_TRUE;
            // Windows UISettings may report an almost-black app background.
            // Lift it slightly toward the foreground so the frame/content
            // surfaces match Windows 11 Explorer's neutral dark hierarchy
            // instead of collapsing into a flat pure-black canvas.
            sPalette.mWindow        = blendColor(sBackground, sForeground, 10);
            sPalette.mSurface       = blendColor(sBackground, sForeground, 14);
            sPalette.mText          = sForeground;
            sPalette.mSecondaryText = blendColor(sPalette.mWindow, sForeground, 65);
            sPalette.mBorder        = blendColor(sPalette.mWindow, sForeground, 24);
            sPalette.mSeparator     = blendColor(sPalette.mWindow, sForeground, 16);
        }
        else if (sThemeMode == ThemeModeDark)
        {
            sPalette.mDark          = XPR_TRUE;
            sPalette.mWindow        = blendColor(sSystemWindow, sSystemText, 90);
            sPalette.mSurface       = blendColor(sPalette.mWindow, sSystemWindow, 8);
            sPalette.mText          = sSystemWindow;
            sPalette.mSecondaryText = blendColor(sPalette.mWindow, sPalette.mText, 65);
            sPalette.mBorder        = blendColor(sPalette.mWindow, sPalette.mText, 24);
            sPalette.mSeparator     = blendColor(sPalette.mWindow, sPalette.mText, 16);
        }
        else if (sThemeMode == ThemeModeLight)
        {
            sPalette.mDark = XPR_FALSE;
        }
    }

    if (XPR_IS_TRUE(sPalette.mHighContrast))
    {
        sPalette.mChrome            = sPalette.mSurface;
        sPalette.mElevated          = sPalette.mSurface;
        sPalette.mCard              = sPalette.mSurface;
        sPalette.mHover             = sPalette.mSelection;
        sPalette.mPressed           = sPalette.mSelection;
        sPalette.mInactiveSelection = sPalette.mSurface;
        sPalette.mFocus             = sPalette.mSelection;
    }
    else
    {
        const xpr_uint_t sChromeLift = XPR_IS_TRUE(sPalette.mDark) ? 4 : 2;
        const xpr_uint_t sElevatedLift = XPR_IS_TRUE(sPalette.mDark) ? 7 : 4;
        const xpr_uint_t sCardLift = XPR_IS_TRUE(sPalette.mDark) ? 5 : 2;

        sPalette.mChrome = blendColor(
            sPalette.mSurface,
            sPalette.mText,
            sChromeLift);
        sPalette.mElevated = blendColor(
            sPalette.mSurface,
            sPalette.mText,
            sElevatedLift);
        sPalette.mCard = blendColor(
            sPalette.mWindow,
            sPalette.mText,
            sCardLift);
        sPalette.mHover = blendColor(
            sPalette.mElevated,
            sPalette.mSelection,
            10);
        sPalette.mPressed = blendColor(
            sPalette.mElevated,
            sPalette.mSelection,
            18);
        sPalette.mInactiveSelection = blendColor(
            sPalette.mSurface,
            sPalette.mSelection,
            6);
        sPalette.mFocus = blendColor(
            sPalette.mSelection,
            sPalette.mText,
            XPR_IS_TRUE(sPalette.mDark) ? 8 : 4);
    }

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
        const ThemePalette sPalette = getPalette();
        const BOOL sUseDarkFrame =
            (XPR_IS_TRUE(sPalette.mDark) && XPR_IS_FALSE(sPalette.mHighContrast)) ?
            TRUE :
            FALSE;
        const HRESULT sResult = sDwmSetWindowAttribute(
            aHwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            &sUseDarkFrame,
            sizeof(sUseDarkFrame));

        sApplied = SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;

        // Windows 11 dialogs and Explorer use rounded top-level corners. The
        // documented DWM attribute is ignored on older Windows, so it is safe
        // to request here while retaining the existing fallback behavior.
        const DWORD sCornerPreference =
            XPR_IS_TRUE(sPalette.mHighContrast) ?
            DWMWCP_DEFAULT :
            DWMWCP_ROUND;
        const HRESULT sCornerResult = sDwmSetWindowAttribute(
            aHwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            &sCornerPreference,
            sizeof(sCornerPreference));
        if (SUCCEEDED(sCornerResult))
            sApplied = XPR_TRUE;
    }

    ::FreeLibrary(sDwmApi);
    return sApplied;
}

xpr_bool_t ModernUI::applyRoundedWindowRegion(
    HWND aHwnd,
    xpr_sint_t aRadius)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return XPR_FALSE;

    if (XPR_IS_TRUE(isHighContrast()) || aRadius <= 0)
    {
        ::SetWindowRgn(aHwnd, XPR_NULL, TRUE);
        return XPR_TRUE;
    }

    RECT sClientRect = {0};
    if (::GetClientRect(aHwnd, &sClientRect) == FALSE)
        return XPR_FALSE;

    const xpr_sint_t sRadius = max(1, aRadius);
    HRGN sRegion = ::CreateRoundRectRgn(
        sClientRect.left,
        sClientRect.top,
        sClientRect.right + 1,
        sClientRect.bottom + 1,
        sRadius * 2,
        sRadius * 2);
    if (XPR_IS_NULL(sRegion))
        return XPR_FALSE;

    if (::SetWindowRgn(aHwnd, sRegion, TRUE) == 0)
    {
        ::DeleteObject(sRegion);
        return XPR_FALSE;
    }

    // The system owns sRegion after successful SetWindowRgn.
    return XPR_TRUE;
}

xpr_bool_t ModernUI::applyExplorerControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return XPR_FALSE;

    // SetWindowTheme is documented, but resolving it dynamically keeps the
    // ModernUI foundation safe on systems where uxtheme is unavailable.
    HMODULE sUxTheme = ::LoadLibrary(XPR_STRING_LITERAL("uxtheme.dll"));
    if (XPR_IS_NULL(sUxTheme))
        return XPR_FALSE;

    SetWindowThemeProc sSetWindowTheme =
        reinterpret_cast<SetWindowThemeProc>(
            ::GetProcAddress(sUxTheme, "SetWindowTheme"));

    if (XPR_IS_NULL(sSetWindowTheme))
    {
        ::FreeLibrary(sUxTheme);
        return XPR_FALSE;
    }

    if (XPR_IS_FALSE(beginControlThemeChange(aHwnd)))
    {
        // The only expected false result for a valid control during theme
        // application is a synchronous WM_THEMECHANGED re-entry. Treat that
        // nested request as already satisfied by the outer operation.
        const xpr_bool_t sNested =
            XPR_IS_NOT_NULL(::GetProp(aHwnd, kThemeApplyGuardProp)) ?
            XPR_TRUE : XPR_FALSE;
        ::FreeLibrary(sUxTheme);
        return sNested;
    }

    // High Contrast should retain the system's default control rendering.
    // The Explorer theme is a documented/common Win32 visual-style opt-in
    // already used by flyExplorer list/tree controls.
    const LPCWSTR sSubAppName =
        XPR_IS_TRUE(isHighContrast()) ? XPR_NULL : L"Explorer";
    const HRESULT sResult = sSetWindowTheme(aHwnd, sSubAppName, XPR_NULL);

    endControlThemeChange(aHwnd);
    ::FreeLibrary(sUxTheme);
    return SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
}

xpr_bool_t ModernUI::resetControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return XPR_FALSE;

    HMODULE sUxTheme = ::LoadLibrary(XPR_STRING_LITERAL("uxtheme.dll"));
    if (XPR_IS_NULL(sUxTheme))
        return XPR_FALSE;

    SetWindowThemeProc sSetWindowTheme =
        reinterpret_cast<SetWindowThemeProc>(
            ::GetProcAddress(sUxTheme, "SetWindowTheme"));

    if (XPR_IS_NULL(sSetWindowTheme))
    {
        ::FreeLibrary(sUxTheme);
        return XPR_FALSE;
    }

    if (XPR_IS_FALSE(beginControlThemeChange(aHwnd)))
    {
        const xpr_bool_t sNested =
            XPR_IS_NOT_NULL(::GetProp(aHwnd, kThemeApplyGuardProp)) ?
            XPR_TRUE : XPR_FALSE;
        ::FreeLibrary(sUxTheme);
        return sNested;
    }

    // SetWindowTheme(hwnd, NULL, NULL) restores the default visual-style
    // association; it does not disable themed painting. Dark surfaces that
    // are fully owned by flyExplorer need the documented empty sub-app/sub-id
    // contract so native light borders/backgrounds do not leak through custom
    // palette rendering.
    const HRESULT sResult = sSetWindowTheme(aHwnd, L"", L"");

    endControlThemeChange(aHwnd);
    ::FreeLibrary(sUxTheme);
    return SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
}
} // namespace ui
} // namespace fxfile
