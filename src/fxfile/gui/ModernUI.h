//
// Copyright (c) 2026 flyExplorer contributors.
//
// Windows 11 UI foundation: DPI, system typography and theme metrics.
//

#ifndef __FXFILE_GUI_MODERN_UI_H__
#define __FXFILE_GUI_MODERN_UI_H__ 1
#pragma once

#ifndef WM_DPICHANGED
#define WM_DPICHANGED 0x02E0
#endif

#ifndef WM_DPICHANGED_AFTERPARENT
#define WM_DPICHANGED_AFTERPARENT 0x02E3
#endif

namespace fxfile
{
namespace ui
{
struct ThemePalette
{
    COLORREF mWindow;
    COLORREF mSurface;
    COLORREF mText;
    COLORREF mSecondaryText;
    COLORREF mBorder;
    COLORREF mSeparator;
    COLORREF mSelection;
    COLORREF mSelectionText;
    COLORREF mHover;
    xpr_bool_t mDark;
    xpr_bool_t mHighContrast;
};

class ModernUI
{
public:
    enum
    {
        kDefaultDpi = 96,
    };

    enum ThemeMode
    {
        ThemeModeSystem = 0,
        ThemeModeLight,
        ThemeModeDark,
    };

public:
    static xpr_uint_t getDpi(HWND aHwnd);
    static xpr_sint_t scale(xpr_sint_t aValue, xpr_uint_t aDpi);
    static xpr_sint_t scaleForWindow(xpr_sint_t aValue, HWND aHwnd);

    // Shared Windows 11 navigation/command metrics. Keep these centralized so
    // toolbar, rebar and address surfaces stay visually aligned at every DPI.
    static xpr_sint_t getCommandBarHeight(HWND aHwnd);
    static xpr_sint_t getCommandButtonExtent(HWND aHwnd);
    static xpr_sint_t getCommandHorizontalPadding(HWND aHwnd);
    static xpr_sint_t getCommandVerticalPadding(HWND aHwnd);
    static xpr_sint_t getAddressBarHeight(HWND aHwnd);
    static xpr_sint_t getAddressHorizontalInset(HWND aHwnd);
    static xpr_sint_t getAddressTextMargin(HWND aHwnd);
    static xpr_sint_t getPopupItemPadding(HWND aHwnd);

    static xpr_bool_t getUIFont(LOGFONT &aLogFont, HWND aHwnd);
    static HICON loadIconResource(HINSTANCE aInstance, xpr_uint_t aResourceId, HWND aHwnd, xpr_sint_t aLogicalSize);
    static void setThemeMode(xpr_sint_t aThemeMode);
    static xpr_sint_t getThemeMode(void);
    static ThemePalette getPalette(void);
    static xpr_bool_t isHighContrast(void);
    static xpr_bool_t applyWindowFrameTheme(HWND aHwnd);
    static xpr_bool_t applyExplorerControlTheme(HWND aHwnd);
    static xpr_bool_t resetControlTheme(HWND aHwnd);

private:
    ModernUI(void);
};
} // namespace ui
} // namespace fxfile

#endif // __FXFILE_GUI_MODERN_UI_H__
