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
const xpr_tchar_t kThemeAssociationProp[] =
    XPR_STRING_LITERAL("fxfile.ModernUI.ThemeAssociation");

enum ControlThemeAssociation
{
    ControlThemeAssociationExplorer = 1,
    ControlThemeAssociationDefault  = 2,
    ControlThemeAssociationDisabled = 3,
};

xpr_bool_t hasControlThemeAssociation(
    HWND aHwnd,
    ControlThemeAssociation aAssociation)
{
    return
        ::GetProp(aHwnd, kThemeAssociationProp) ==
        reinterpret_cast<HANDLE>(static_cast<INT_PTR>(aAssociation)) ?
        XPR_TRUE :
        XPR_FALSE;
}

void rememberControlThemeAssociation(
    HWND aHwnd,
    ControlThemeAssociation aAssociation)
{
    if (XPR_IS_NULL(aHwnd))
        return;

    ::SetProp(
        aHwnd,
        kThemeAssociationProp,
        reinterpret_cast<HANDLE>(static_cast<INT_PTR>(aAssociation)));
}

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

const UINT_PTR kDialogButtonSubclassId = 0x46474442; // 'FGDB'
const UINT_PTR kDialogTabSubclassId = 0x46474454;    // 'FGDT'

HBRUSH getDialogParentBrush(HWND aHwnd, HDC aDC, UINT aCtlColorMessage)
{
    HWND sParent = ::GetParent(aHwnd);
    if (XPR_IS_NULL(sParent))
        return XPR_NULL;

    return reinterpret_cast<HBRUSH>(
        ::SendMessage(
            sParent,
            aCtlColorMessage,
            reinterpret_cast<WPARAM>(aDC),
            reinterpret_cast<LPARAM>(aHwnd)));
}

void fillDialogControlBackground(
    HWND aHwnd,
    HDC aDC,
    const RECT &aRect,
    COLORREF aFallback)
{
    HBRUSH sBrush =
        getDialogParentBrush(aHwnd, aDC, WM_CTLCOLORBTN);
    if (XPR_IS_NOT_NULL(sBrush) &&
        sBrush != reinterpret_cast<HBRUSH>(::GetStockObject(NULL_BRUSH)))
    {
        ::FillRect(aDC, &aRect, sBrush);
        return;
    }

    ::SetDCBrushColor(aDC, aFallback);
    ::FillRect(
        aDC,
        &aRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
}

xpr_bool_t isDialogToggleButton(DWORD aButtonType)
{
    return
        aButtonType == BS_CHECKBOX ||
        aButtonType == BS_AUTOCHECKBOX ||
        aButtonType == BS_3STATE ||
        aButtonType == BS_AUTO3STATE ||
        aButtonType == BS_RADIOBUTTON ||
        aButtonType == BS_AUTORADIOBUTTON ?
        XPR_TRUE :
        XPR_FALSE;
}

xpr_bool_t isDialogPushButton(DWORD aButtonType)
{
    return
        aButtonType == BS_PUSHBUTTON ||
        aButtonType == BS_DEFPUSHBUTTON ?
        XPR_TRUE :
        XPR_FALSE;
}

void drawDialogPushButton(HWND aHwnd)
{
    const ThemePalette sPalette = ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) ||
        XPR_IS_TRUE(sPalette.mHighContrast))
    {
        return;
    }

    PAINTSTRUCT sPaint = {0};
    HDC sDC = ::BeginPaint(aHwnd, &sPaint);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sRect = {0};
    ::GetClientRect(aHwnd, &sRect);

    const xpr_bool_t sEnabled =
        ::IsWindowEnabled(aHwnd) != FALSE ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sFocused =
        ::GetFocus() == aHwnd ? XPR_TRUE : XPR_FALSE;
    const LRESULT sState = ::SendMessage(aHwnd, BM_GETSTATE, 0, 0);
    const xpr_bool_t sPressed =
        (sState & BST_PUSHED) != 0 ? XPR_TRUE : XPR_FALSE;

    POINT sCursor = {0};
    RECT sWindowRect = {0};
    ::GetCursorPos(&sCursor);
    ::GetWindowRect(aHwnd, &sWindowRect);
    const xpr_bool_t sHot =
        ::PtInRect(&sWindowRect, sCursor) != FALSE ?
        XPR_TRUE :
        XPR_FALSE;

    COLORREF sFill =
        XPR_IS_TRUE(sEnabled) ? sPalette.mElevated : sPalette.mCard;
    COLORREF sText =
        XPR_IS_TRUE(sEnabled) ? sPalette.mText : sPalette.mSecondaryText;
    COLORREF sBorder =
        XPR_IS_TRUE(sFocused) ? sPalette.mFocus : sPalette.mSeparator;

    if (XPR_IS_TRUE(sEnabled))
    {
        if (XPR_IS_TRUE(sPressed))
            sFill = sPalette.mPressed;
        else if (XPR_IS_TRUE(sHot))
            sFill = sPalette.mHover;
    }

    HBRUSH sBrush = ::CreateSolidBrush(sFill);
    HPEN sPen = ::CreatePen(PS_SOLID, 1, sBorder);
    if (XPR_IS_NOT_NULL(sBrush) && XPR_IS_NOT_NULL(sPen))
    {
        HGDIOBJ sOldBrush = ::SelectObject(sDC, sBrush);
        HGDIOBJ sOldPen = ::SelectObject(sDC, sPen);
        const xpr_sint_t sRadius =
            ModernUI::getControlCornerRadius(aHwnd);
        ::RoundRect(
            sDC,
            sRect.left,
            sRect.top,
            sRect.right,
            sRect.bottom,
            sRadius * 2,
            sRadius * 2);
        ::SelectObject(sDC, sOldPen);
        ::SelectObject(sDC, sOldBrush);
    }
    if (XPR_IS_NOT_NULL(sPen))
        ::DeleteObject(sPen);
    if (XPR_IS_NOT_NULL(sBrush))
        ::DeleteObject(sBrush);

    xpr_tchar_t sLabel[512] = {0};
    ::GetWindowText(aHwnd, sLabel, XPR_COUNT_OF(sLabel));
    HFONT sFont = reinterpret_cast<HFONT>(
        ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = ::SelectObject(sDC, sFont);

    ::SetBkMode(sDC, TRANSPARENT);
    ::SetTextColor(sDC, sText);
    ::DrawText(
        sDC,
        sLabel,
        -1,
        &sRect,
        DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

void drawDialogToggle(HWND aHwnd)
{
    const ThemePalette sPalette = ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) ||
        XPR_IS_TRUE(sPalette.mHighContrast))
    {
        return;
    }

    const DWORD sButtonType =
        static_cast<DWORD>(::GetWindowLongPtr(aHwnd, GWL_STYLE)) &
        BS_TYPEMASK;
    if (XPR_IS_FALSE(isDialogToggleButton(sButtonType)))
        return;

    PAINTSTRUCT sPaint = {0};
    HDC sDC = ::BeginPaint(aHwnd, &sPaint);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sClientRect = {0};
    ::GetClientRect(aHwnd, &sClientRect);
    fillDialogControlBackground(
        aHwnd,
        sDC,
        sClientRect,
        sPalette.mSurface);

    const xpr_bool_t sEnabled =
        ::IsWindowEnabled(aHwnd) != FALSE ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sFocused =
        ::GetFocus() == aHwnd ? XPR_TRUE : XPR_FALSE;
    const LRESULT sState = ::SendMessage(aHwnd, BM_GETSTATE, 0, 0);
    const xpr_bool_t sHot =
        (sState & BST_HOT) != 0 ? XPR_TRUE : XPR_FALSE;
    const LRESULT sCheck = ::SendMessage(aHwnd, BM_GETCHECK, 0, 0);

    const xpr_sint_t sGlyphExtent =
        max(12, ModernUI::scaleForWindow(14, aHwnd));
    const xpr_sint_t sGap =
        ModernUI::scaleForWindow(8, aHwnd);
    const xpr_sint_t sTop =
        max(0, (sClientRect.bottom - sClientRect.top - sGlyphExtent) / 2);

    RECT sGlyphRect =
    {
        sClientRect.left,
        sClientRect.top + sTop,
        sClientRect.left + sGlyphExtent,
        sClientRect.top + sTop + sGlyphExtent,
    };

    COLORREF sFill = sPalette.mElevated;
    COLORREF sBorder =
        XPR_IS_TRUE(sFocused) ? sPalette.mFocus : sPalette.mSeparator;
    COLORREF sGlyph = sPalette.mText;
    if (XPR_IS_FALSE(sEnabled))
    {
        sFill = sPalette.mCard;
        sGlyph = sPalette.mSecondaryText;
    }
    else if (XPR_IS_TRUE(sHot))
    {
        sFill = sPalette.mHover;
    }

    if (sCheck == BST_CHECKED || sCheck == BST_INDETERMINATE)
    {
        sFill = sPalette.mSelection;
        sBorder = sPalette.mSelection;
        sGlyph = sPalette.mSelectionText;
    }

    const xpr_bool_t sRadio =
        (sButtonType == BS_RADIOBUTTON ||
         sButtonType == BS_AUTORADIOBUTTON) ?
        XPR_TRUE :
        XPR_FALSE;

    HBRUSH sFillBrush = ::CreateSolidBrush(sFill);
    HPEN sBorderPen = ::CreatePen(PS_SOLID, 1, sBorder);
    if (XPR_IS_NOT_NULL(sFillBrush) && XPR_IS_NOT_NULL(sBorderPen))
    {
        HGDIOBJ sOldBrush = ::SelectObject(sDC, sFillBrush);
        HGDIOBJ sOldPen = ::SelectObject(sDC, sBorderPen);
        if (XPR_IS_TRUE(sRadio))
        {
            ::Ellipse(
                sDC,
                sGlyphRect.left,
                sGlyphRect.top,
                sGlyphRect.right,
                sGlyphRect.bottom);
        }
        else
        {
            const xpr_sint_t sRadius =
                max(2, ModernUI::scaleForWindow(3, aHwnd));
            ::RoundRect(
                sDC,
                sGlyphRect.left,
                sGlyphRect.top,
                sGlyphRect.right,
                sGlyphRect.bottom,
                sRadius * 2,
                sRadius * 2);
        }
        ::SelectObject(sDC, sOldPen);
        ::SelectObject(sDC, sOldBrush);
    }
    if (XPR_IS_NOT_NULL(sBorderPen))
        ::DeleteObject(sBorderPen);
    if (XPR_IS_NOT_NULL(sFillBrush))
        ::DeleteObject(sFillBrush);

    if (sCheck == BST_CHECKED)
    {
        HPEN sGlyphPen = ::CreatePen(
            PS_SOLID,
            max(1, ModernUI::scaleForWindow(2, aHwnd)),
            sGlyph);
        if (XPR_IS_NOT_NULL(sGlyphPen))
        {
            HGDIOBJ sOldPen = ::SelectObject(sDC, sGlyphPen);
            if (XPR_IS_TRUE(sRadio))
            {
                const xpr_sint_t sInset =
                    max(3, ModernUI::scaleForWindow(4, aHwnd));
                HBRUSH sDotBrush = ::CreateSolidBrush(sGlyph);
                if (XPR_IS_NOT_NULL(sDotBrush))
                {
                    HGDIOBJ sOldBrush = ::SelectObject(sDC, sDotBrush);
                    ::Ellipse(
                        sDC,
                        sGlyphRect.left + sInset,
                        sGlyphRect.top + sInset,
                        sGlyphRect.right - sInset,
                        sGlyphRect.bottom - sInset);
                    ::SelectObject(sDC, sOldBrush);
                    ::DeleteObject(sDotBrush);
                }
            }
            else
            {
                ::MoveToEx(
                    sDC,
                    sGlyphRect.left + (sGlyphExtent * 3 / 10),
                    sGlyphRect.top + (sGlyphExtent * 5 / 10),
                    XPR_NULL);
                ::LineTo(
                    sDC,
                    sGlyphRect.left + (sGlyphExtent * 45 / 100),
                    sGlyphRect.top + (sGlyphExtent * 65 / 100));
                ::LineTo(
                    sDC,
                    sGlyphRect.left + (sGlyphExtent * 75 / 100),
                    sGlyphRect.top + (sGlyphExtent * 35 / 100));
            }
            ::SelectObject(sDC, sOldPen);
            ::DeleteObject(sGlyphPen);
        }
    }
    else if (sCheck == BST_INDETERMINATE && XPR_IS_FALSE(sRadio))
    {
        RECT sMarkRect = sGlyphRect;
        const xpr_sint_t sInset =
            max(3, ModernUI::scaleForWindow(4, aHwnd));
        ::InflateRect(&sMarkRect, -sInset, -sInset);
        ::SetDCBrushColor(sDC, sGlyph);
        ::FillRect(
            sDC,
            &sMarkRect,
            static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
    }

    xpr_tchar_t sText[512] = {0};
    ::GetWindowText(aHwnd, sText, XPR_COUNT_OF(sText));
    RECT sTextRect = sClientRect;
    sTextRect.left = sGlyphRect.right + sGap;

    HFONT sFont = reinterpret_cast<HFONT>(
        ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = ::SelectObject(sDC, sFont);

    ::SetBkMode(sDC, TRANSPARENT);
    ::SetTextColor(
        sDC,
        XPR_IS_TRUE(sEnabled) ?
        sPalette.mText :
        sPalette.mSecondaryText);
    ::DrawText(
        sDC,
        sText,
        -1,
        &sTextRect,
        DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

    if (XPR_IS_TRUE(sFocused))
    {
        RECT sFocusRect = sTextRect;
        ::InflateRect(
            &sFocusRect,
            -max(1, ModernUI::scaleForWindow(1, aHwnd)),
            -max(1, ModernUI::scaleForWindow(1, aHwnd)));
        ::DrawFocusRect(sDC, &sFocusRect);
    }

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

LRESULT CALLBACK DialogButtonSubclassProc(
    HWND aHwnd,
    UINT aMessage,
    WPARAM aWParam,
    LPARAM aLParam,
    UINT_PTR aSubclassId,
    DWORD_PTR)
{
    const DWORD sButtonType =
        static_cast<DWORD>(::GetWindowLongPtr(aHwnd, GWL_STYLE)) &
        BS_TYPEMASK;

    switch (aMessage)
    {
        case WM_PAINT:
        {
            const ThemePalette sPalette = ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mDark) &&
                XPR_IS_FALSE(sPalette.mHighContrast))
            {
                if (XPR_IS_TRUE(isDialogPushButton(sButtonType)))
                    drawDialogPushButton(aHwnd);
                else if (XPR_IS_TRUE(isDialogToggleButton(sButtonType)))
                    drawDialogToggle(aHwnd);
                else
                    break;
                return 0;
            }
            break;
        }

        case BM_SETCHECK:
        case WM_SETTEXT:
        {
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            return sResult;
        }

        case WM_MOUSEMOVE:
        {
            TRACKMOUSEEVENT sTrack = {0};
            sTrack.cbSize = sizeof(sTrack);
            sTrack.dwFlags = TME_LEAVE;
            sTrack.hwndTrack = aHwnd;
            ::TrackMouseEvent(&sTrack);
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;
        }

        case WM_MOUSELEAVE:
        case WM_LBUTTONDOWN:
        case WM_LBUTTONUP:
        case WM_ENABLE:
        case WM_SETFOCUS:
        case WM_KILLFOCUS:
        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                DialogButtonSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

void drawDialogTab(HWND aHwnd)
{
    const ThemePalette sPalette = ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) ||
        XPR_IS_TRUE(sPalette.mHighContrast))
    {
        return;
    }

    PAINTSTRUCT sPaint = {0};
    HDC sDC = ::BeginPaint(aHwnd, &sPaint);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sClientRect = {0};
    ::GetClientRect(aHwnd, &sClientRect);

    HBRUSH sParentBrush =
        getDialogParentBrush(aHwnd, sDC, WM_CTLCOLORSTATIC);
    if (XPR_IS_NOT_NULL(sParentBrush) &&
        sParentBrush != reinterpret_cast<HBRUSH>(::GetStockObject(NULL_BRUSH)))
    {
        ::FillRect(sDC, &sClientRect, sParentBrush);
    }
    else
    {
        ::SetDCBrushColor(sDC, sPalette.mSurface);
        ::FillRect(
            sDC,
            &sClientRect,
            static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
    }

    HFONT sFont = reinterpret_cast<HFONT>(
        ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = ::SelectObject(sDC, sFont);

    POINT sCursor = {0};
    ::GetCursorPos(&sCursor);
    ::ScreenToClient(aHwnd, &sCursor);

    const xpr_sint_t sCount = TabCtrl_GetItemCount(aHwnd);
    const xpr_sint_t sSelected = TabCtrl_GetCurSel(aHwnd);
    HIMAGELIST sImageList = TabCtrl_GetImageList(aHwnd);

    for (xpr_sint_t i = 0; i < sCount; ++i)
    {
        RECT sItemRect = {0};
        if (TabCtrl_GetItemRect(aHwnd, i, &sItemRect) == FALSE)
            continue;

        const xpr_bool_t sCurrent =
            i == sSelected ? XPR_TRUE : XPR_FALSE;
        const xpr_bool_t sHot =
            ::PtInRect(&sItemRect, sCursor) != FALSE ?
            XPR_TRUE :
            XPR_FALSE;

        COLORREF sFill = sPalette.mSurface;
        if (XPR_IS_TRUE(sCurrent))
            sFill = sPalette.mElevated;
        else if (XPR_IS_TRUE(sHot))
            sFill = sPalette.mHover;

        HBRUSH sBrush = ::CreateSolidBrush(sFill);
        if (XPR_IS_NOT_NULL(sBrush))
        {
            const xpr_sint_t sRadius =
                ModernUI::getControlCornerRadius(aHwnd);
            HPEN sPen = ::CreatePen(
                PS_SOLID,
                1,
                XPR_IS_TRUE(sCurrent) ?
                sPalette.mSelection :
                sPalette.mSeparator);
            HGDIOBJ sOldBrush = ::SelectObject(sDC, sBrush);
            HGDIOBJ sOldPen =
                XPR_IS_NOT_NULL(sPen) ?
                ::SelectObject(sDC, sPen) :
                XPR_NULL;
            ::RoundRect(
                sDC,
                sItemRect.left,
                sItemRect.top,
                sItemRect.right,
                sItemRect.bottom,
                sRadius * 2,
                sRadius * 2);
            if (XPR_IS_NOT_NULL(sOldPen))
                ::SelectObject(sDC, sOldPen);
            ::SelectObject(sDC, sOldBrush);
            if (XPR_IS_NOT_NULL(sPen))
                ::DeleteObject(sPen);
            ::DeleteObject(sBrush);
        }

        xpr_tchar_t sText[256] = {0};
        TCITEM sItem = {0};
        sItem.mask = TCIF_TEXT | TCIF_IMAGE;
        sItem.pszText = sText;
        sItem.cchTextMax = XPR_COUNT_OF(sText);
        sItem.iImage = -1;
        TabCtrl_GetItem(aHwnd, i, &sItem);

        RECT sTextRect = sItemRect;
        const xpr_sint_t sPadding =
            ModernUI::scaleForWindow(8, aHwnd);
        sTextRect.left += sPadding;
        sTextRect.right -= sPadding;

        if (XPR_IS_NOT_NULL(sImageList) && sItem.iImage >= 0)
        {
            xpr_sint_t sCx = 0;
            xpr_sint_t sCy = 0;
            if (::ImageList_GetIconSize(sImageList, &sCx, &sCy) != FALSE)
            {
                const xpr_sint_t sY =
                    sItemRect.top +
                    ((sItemRect.bottom - sItemRect.top - sCy) / 2);
                ::ImageList_Draw(
                    sImageList,
                    sItem.iImage,
                    sDC,
                    sTextRect.left,
                    sY,
                    ILD_TRANSPARENT);
                sTextRect.left += sCx + sPadding;
            }
        }

        ::SetBkMode(sDC, TRANSPARENT);
        ::SetTextColor(sDC, sPalette.mText);
        ::DrawText(
            sDC,
            sText,
            -1,
            &sTextRect,
            DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);
    }

    const xpr_sint_t sLineHeight =
        max(1, ModernUI::scaleForWindow(1, aHwnd));
    RECT sSeparator = sClientRect;
    sSeparator.top = sSeparator.bottom - sLineHeight;
    ::SetDCBrushColor(sDC, sPalette.mSeparator);
    ::FillRect(
        sDC,
        &sSeparator,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

LRESULT CALLBACK DialogTabSubclassProc(
    HWND aHwnd,
    UINT aMessage,
    WPARAM aWParam,
    LPARAM aLParam,
    UINT_PTR aSubclassId,
    DWORD_PTR)
{
    switch (aMessage)
    {
        case WM_PAINT:
        {
            const ThemePalette sPalette = ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mDark) &&
                XPR_IS_FALSE(sPalette.mHighContrast))
            {
                drawDialogTab(aHwnd);
                return 0;
            }
            break;
        }

        case WM_MOUSEMOVE:
        {
            TRACKMOUSEEVENT sTrack = {0};
            sTrack.cbSize = sizeof(sTrack);
            sTrack.dwFlags = TME_LEAVE;
            sTrack.hwndTrack = aHwnd;
            ::TrackMouseEvent(&sTrack);
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;
        }

        case WM_MOUSELEAVE:
        case WM_SETFOCUS:
        case WM_KILLFOCUS:
        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
        case TCM_SETCURSEL:
        case TCM_INSERTITEM:
        case TCM_DELETEITEM:
        {
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            return sResult;
        }

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                DialogTabSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
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
    // A 22 px Fluent command glyph plus 7 px on either side fills the
    // 36-DIP Windows 11-style command hit target without the oversized gaps
    // produced by the legacy 16 px bitmap assumptions.
    return scaleForWindow(7, aHwnd);
}

xpr_sint_t ModernUI::getCommandVerticalPadding(HWND aHwnd)
{
    return scaleForWindow(6, aHwnd);
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

xpr_bool_t ModernUI::isSameFont(
    HFONT aFont,
    const LOGFONT &aLogFont)
{
    if (XPR_IS_NULL(aFont))
        return XPR_FALSE;

    LOGFONT sCurrent = {0};
    if (::GetObject(aFont, sizeof(sCurrent), &sCurrent) == 0)
        return XPR_FALSE;

    return ::memcmp(&sCurrent, &aLogFont, sizeof(LOGFONT)) == 0 ?
        XPR_TRUE :
        XPR_FALSE;
}

void ModernUI::applyDialogControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return;

    xpr_tchar_t sClassName[64] = {0};
    ::GetClassName(aHwnd, sClassName, XPR_COUNT_OF(sClassName));

    const ThemePalette sPalette = getPalette();

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("Button")) == 0)
    {
        const DWORD sButtonType =
            static_cast<DWORD>(::GetWindowLongPtr(aHwnd, GWL_STYLE)) &
            BS_TYPEMASK;
        if (XPR_IS_TRUE(isDialogPushButton(sButtonType)) ||
            XPR_IS_TRUE(isDialogToggleButton(sButtonType)))
        {
            ::SetWindowSubclass(
                aHwnd,
                DialogButtonSubclassProc,
                kDialogButtonSubclassId,
                0);
        }
    }
    else if (_tcsicmp(
                 sClassName,
                 XPR_STRING_LITERAL("SysTabControl32")) == 0)
    {
        ::SetWindowSubclass(
            aHwnd,
            DialogTabSubclassProc,
            kDialogTabSubclassId,
            0);
    }
    else if (_tcsicmp(
                 sClassName,
                 XPR_STRING_LITERAL("SysListView32")) == 0)
    {
        const COLORREF sBackground =
            XPR_IS_TRUE(sPalette.mHighContrast) ?
            sPalette.mWindow :
            sPalette.mElevated;
        ListView_SetBkColor(aHwnd, sBackground);
        ListView_SetTextBkColor(aHwnd, sBackground);
        ListView_SetTextColor(aHwnd, sPalette.mText);
    }
    else if (_tcsicmp(
                 sClassName,
                 XPR_STRING_LITERAL("SysTreeView32")) == 0)
    {
        const COLORREF sBackground =
            XPR_IS_TRUE(sPalette.mHighContrast) ?
            sPalette.mWindow :
            sPalette.mCard;
        TreeView_SetBkColor(aHwnd, sBackground);
        TreeView_SetTextColor(aHwnd, sPalette.mText);
        TreeView_SetLineColor(aHwnd, sPalette.mSeparator);
    }

    ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
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

    // A visual-style association remains attached to the HWND across normal
    // WM_THEMECHANGED notifications. Repeating SetWindowTheme with the same
    // association can generate another WM_THEMECHANGED and keep the UI thread
    // in a self-sustaining message loop. Skip identical requests entirely.
    const xpr_bool_t sHighContrast = isHighContrast();
    const ControlThemeAssociation sDesiredAssociation =
        XPR_IS_TRUE(sHighContrast) ?
        ControlThemeAssociationDefault :
        ControlThemeAssociationExplorer;
    if (XPR_IS_TRUE(
            hasControlThemeAssociation(aHwnd, sDesiredAssociation)))
    {
        return XPR_TRUE;
    }

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
        XPR_IS_TRUE(sHighContrast) ? XPR_NULL : L"Explorer";
    const HRESULT sResult = sSetWindowTheme(aHwnd, sSubAppName, XPR_NULL);
    if (SUCCEEDED(sResult))
        rememberControlThemeAssociation(aHwnd, sDesiredAssociation);

    endControlThemeChange(aHwnd);
    ::FreeLibrary(sUxTheme);
    return SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
}

xpr_bool_t ModernUI::resetControlTheme(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return XPR_FALSE;

    if (XPR_IS_TRUE(
            hasControlThemeAssociation(
                aHwnd,
                ControlThemeAssociationDisabled)))
    {
        return XPR_TRUE;
    }

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

    // The empty sub-app/sub-id contract disables themed painting for controls
    // whose complete Dark surface is owned by flyExplorer.
    const HRESULT sResult = sSetWindowTheme(aHwnd, L"", L"");
    if (SUCCEEDED(sResult))
    {
        rememberControlThemeAssociation(
            aHwnd,
            ControlThemeAssociationDisabled);
    }

    endControlThemeChange(aHwnd);
    ::FreeLibrary(sUxTheme);
    return SUCCEEDED(sResult) ? XPR_TRUE : XPR_FALSE;
}
} // namespace ui
} // namespace fxfile
