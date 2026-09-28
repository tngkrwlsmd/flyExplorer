//
// Copyright (c) 2026 flyExplorer contributors.
//
// Windows 11 UI foundation: DPI, system typography and theme metrics.
//

#include "stdafx.h"
#include "ModernUI.h"
#include <oleacc.h> // Documented OBJID_* scrollbar constants
#include <vector>

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

const UINT_PTR kDialogButtonSubclassId = 0x46474442;   // 'FGDB'
const UINT_PTR kDialogTabSubclassId = 0x46474454;      // 'FGDT'
const UINT_PTR kDialogEditSubclassId = 0x46474445;     // 'FGDE'
const UINT_PTR kDialogComboSubclassId = 0x46474443;    // 'FGDC'
const UINT_PTR kDialogGroupSubclassId = 0x46474447;    // 'FGDG'
const wchar_t kDialogEmphasizedEditProperty[] =
    L"flyExplorer.ModernDialog.EmphasizedEdit";
const UINT_PTR kDialogScrollSubclassId = 0x46474453;   // 'FGDS'

LRESULT CALLBACK DialogScrollableSubclassProc(
    HWND aHwnd, UINT aMessage, WPARAM aWParam, LPARAM aLParam,
    UINT_PTR aSubclassId, DWORD_PTR)
{
    if (aMessage == WM_NCDESTROY)
    {
        ::RemoveWindowSubclass(
            aHwnd, DialogScrollableSubclassProc, aSubclassId);
        ModernUI::removeDarkScrollbarOverlay(aHwnd);
    }
    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

BOOL CALLBACK CloseOwnedDropdownProc(HWND aHwnd, LPARAM)
{
    xpr_tchar_t sClassName[64] = {0};
    ::GetClassName(aHwnd, sClassName, XPR_COUNT_OF(sClassName));
    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0 &&
        ::SendMessage(aHwnd, CB_GETDROPPEDSTATE, 0, 0) != FALSE)
    {
        ::SendMessage(aHwnd, CB_SHOWDROPDOWN, FALSE, 0);
    }
    return TRUE;
}

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


void drawDialogEditFrame(HWND aHwnd)
{
    const ThemePalette sPalette = ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) ||
        XPR_IS_TRUE(sPalette.mHighContrast))
    {
        return;
    }

    HDC sDC = ::GetWindowDC(aHwnd);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sWindowScreen = {0};
    ::GetWindowRect(aHwnd, &sWindowScreen);

    RECT sWindowRect =
    {
        0,
        0,
        sWindowScreen.right - sWindowScreen.left,
        sWindowScreen.bottom - sWindowScreen.top,
    };

    RECT sClientRect = {0};
    ::GetClientRect(aHwnd, &sClientRect);
    POINT sClientOrigin = {0, 0};
    ::ClientToScreen(aHwnd, &sClientOrigin);
    ::OffsetRect(
        &sClientRect,
        sClientOrigin.x - sWindowScreen.left,
        sClientOrigin.y - sWindowScreen.top);

    HBRUSH sSurfaceBrush = ::CreateSolidBrush(sPalette.mElevated);
    if (XPR_IS_NOT_NULL(sSurfaceBrush))
    {
        RECT sBand = sWindowRect;
        sBand.bottom = max(sWindowRect.top, sClientRect.top);
        ::FillRect(sDC, &sBand, sSurfaceBrush);

        sBand = sWindowRect;
        sBand.top = min(sWindowRect.bottom, sClientRect.bottom);
        ::FillRect(sDC, &sBand, sSurfaceBrush);

        sBand = sWindowRect;
        sBand.top = sClientRect.top;
        sBand.right = max(sWindowRect.left, sClientRect.left);
        sBand.bottom = sClientRect.bottom;
        ::FillRect(sDC, &sBand, sSurfaceBrush);

        sBand = sWindowRect;
        sBand.left = min(sWindowRect.right, sClientRect.right);
        sBand.top = sClientRect.top;
        sBand.bottom = sClientRect.bottom;
        ::FillRect(sDC, &sBand, sSurfaceBrush);

        ::DeleteObject(sSurfaceBrush);
    }

    const COLORREF sBorder =
        (::GetFocus() == aHwnd) ?
        sPalette.mFocus :
        (::GetPropW(aHwnd, kDialogEmphasizedEditProperty) != NULL ?
            sPalette.mSecondaryText : sPalette.mSeparator);
    HBRUSH sBorderBrush = ::CreateSolidBrush(sBorder);
    if (XPR_IS_NOT_NULL(sBorderBrush))
    {
        ::FrameRect(sDC, &sWindowRect, sBorderBrush);
        ::DeleteObject(sBorderBrush);
    }

    ::ReleaseDC(aHwnd, sDC);
}

LRESULT CALLBACK DialogEditSubclassProc(
    HWND aHwnd,
    UINT aMessage,
    WPARAM aWParam,
    LPARAM aLParam,
    UINT_PTR aSubclassId,
    DWORD_PTR)
{
    switch (aMessage)
    {
        case WM_NCPAINT:
        {
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
            drawDialogEditFrame(aHwnd);
            return sResult;
        }

        case WM_SETFOCUS:
        case WM_KILLFOCUS:
        case WM_ENABLE:
        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::RedrawWindow(
                aHwnd,
                XPR_NULL,
                XPR_NULL,
                RDW_INVALIDATE | RDW_FRAME);
            break;

        case WM_NCDESTROY:
            ::RemovePropW(aHwnd, kDialogEmphasizedEditProperty);
            ::RemoveWindowSubclass(
                aHwnd,
                DialogEditSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

void drawDialogCombo(HWND aHwnd)
{
    const LONG_PTR sStyle = ::GetWindowLongPtr(aHwnd, GWL_STYLE);
    if ((sStyle & CBS_DROPDOWNLIST) != CBS_DROPDOWNLIST)
        return;

    const ThemePalette sPalette = ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) ||
        XPR_IS_TRUE(sPalette.mHighContrast))
    {
        return;
    }

    COMBOBOXINFO sComboInfo = {0};
    sComboInfo.cbSize = sizeof(COMBOBOXINFO);
    if (::GetComboBoxInfo(aHwnd, &sComboInfo) == FALSE)
        return;

    HDC sDC = ::GetDC(aHwnd);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sClientRect = {0};
    ::GetClientRect(aHwnd, &sClientRect);

    const xpr_bool_t sEnabled =
        ::IsWindowEnabled(aHwnd) != FALSE ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sFocused =
        ::GetFocus() == aHwnd ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sDropped =
        ::SendMessage(aHwnd, CB_GETDROPPEDSTATE, 0, 0) != FALSE ?
        XPR_TRUE :
        XPR_FALSE;

    POINT sCursor = {0};
    xpr_bool_t sHotButton = XPR_FALSE;
    if (::GetCursorPos(&sCursor) != FALSE &&
        ::ScreenToClient(aHwnd, &sCursor) != FALSE &&
        ::PtInRect(&sComboInfo.rcButton, sCursor) != FALSE)
    {
        sHotButton = XPR_TRUE;
    }

    COLORREF sField =
        XPR_IS_TRUE(sEnabled) ? sPalette.mElevated : sPalette.mCard;
    COLORREF sText =
        XPR_IS_TRUE(sEnabled) ? sPalette.mText : sPalette.mSecondaryText;
    COLORREF sButton = sField;
    if (XPR_IS_TRUE(sDropped))
        sButton = sPalette.mPressed;
    else if (XPR_IS_TRUE(sHotButton) && XPR_IS_TRUE(sEnabled))
        sButton = sPalette.mHover;

    ::SetDCBrushColor(sDC, sField);
    ::FillRect(
        sDC,
        &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    RECT sTextRect = sComboInfo.rcItem;
    const xpr_sint_t sMargin =
        ModernUI::getAddressTextMargin(aHwnd);
    sTextRect.left += sMargin;
    sTextRect.right -= sMargin;

    xpr_tchar_t sLabel[256] = {0};
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
        &sTextRect,
        DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

    ::SetDCBrushColor(sDC, sButton);
    ::FillRect(
        sDC,
        &sComboInfo.rcButton,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    RECT sSeparator = sComboInfo.rcButton;
    sSeparator.right =
        sSeparator.left +
        max(1, ModernUI::scaleForWindow(1, aHwnd));
    ::SetDCBrushColor(sDC, sPalette.mSeparator);
    ::FillRect(
        sDC,
        &sSeparator,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    const xpr_sint_t sCenterX =
        (sComboInfo.rcButton.left + sComboInfo.rcButton.right) / 2;
    const xpr_sint_t sCenterY =
        (sComboInfo.rcButton.top + sComboInfo.rcButton.bottom) / 2;
    const xpr_sint_t sHalfWidth =
        max(2, ModernUI::scaleForWindow(3, aHwnd));
    const xpr_sint_t sOffset =
        max(1, ModernUI::scaleForWindow(2, aHwnd));

    HPEN sArrowPen = ::CreatePen(PS_SOLID, 1, sText);
    if (XPR_IS_NOT_NULL(sArrowPen))
    {
        HGDIOBJ sOldPen = ::SelectObject(sDC, sArrowPen);
        ::MoveToEx(
            sDC,
            sCenterX - sHalfWidth,
            sCenterY - sOffset,
            XPR_NULL);
        ::LineTo(sDC, sCenterX, sCenterY + sOffset);
        ::LineTo(
            sDC,
            sCenterX + sHalfWidth,
            sCenterY - sOffset);
        ::SelectObject(sDC, sOldPen);
        ::DeleteObject(sArrowPen);
    }

    const COLORREF sBorder =
        XPR_IS_TRUE(sFocused) ? sPalette.mFocus : sPalette.mSeparator;
    ::SetDCBrushColor(sDC, sBorder);
    ::FrameRect(
        sDC,
        &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::ReleaseDC(aHwnd, sDC);
}

LRESULT CALLBACK DialogComboSubclassProc(
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
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
            drawDialogCombo(aHwnd);
            return sResult;
        }

        case CB_SHOWDROPDOWN:
        {
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);

            COMBOBOXINFO sComboInfo = {0};
            sComboInfo.cbSize = sizeof(COMBOBOXINFO);
            if (::GetComboBoxInfo(aHwnd, &sComboInfo) != FALSE &&
                XPR_IS_NOT_NULL(sComboInfo.hwndList))
            {
                const ThemePalette sPalette = ModernUI::getPalette();
                if (XPR_IS_TRUE(sPalette.mDark) &&
                    XPR_IS_FALSE(sPalette.mHighContrast))
                {
                    ModernUI::resetControlTheme(sComboInfo.hwndList);
                }
                else
                {
                    ModernUI::applyExplorerControlTheme(
                        sComboInfo.hwndList);
                }
                ::InvalidateRect(sComboInfo.hwndList, XPR_NULL, TRUE);
            }

            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
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
        case WM_ENABLE:
        case WM_SETFOCUS:
        case WM_KILLFOCUS:
        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                DialogComboSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

void drawDialogGroupBox(HWND aHwnd)
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
    fillDialogControlBackground(
        aHwnd,
        sDC,
        sRect,
        sPalette.mSurface);

    xpr_tchar_t sText[256] = {0};
    ::GetWindowText(aHwnd, sText, XPR_COUNT_OF(sText));

    HFONT sFont = reinterpret_cast<HFONT>(
        ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = ::SelectObject(sDC, sFont);

    SIZE sTextSize = {0};
    if (sText[0] != XPR_STRING_LITERAL('\0'))
        ::GetTextExtentPoint32(sDC, sText, (int)_tcslen(sText), &sTextSize);

    const xpr_sint_t sTextGap =
        ModernUI::scaleForWindow(8, aHwnd);
    const xpr_sint_t sTextInset =
        ModernUI::scaleForWindow(8, aHwnd);
    const xpr_sint_t sLineY =
        max(1, (xpr_sint_t)(sTextSize.cy / 2));

    HPEN sPen = ::CreatePen(PS_SOLID, 1, sPalette.mSeparator);
    if (XPR_IS_NOT_NULL(sPen))
    {
        HGDIOBJ sOldPen = ::SelectObject(sDC, sPen);

        ::MoveToEx(sDC, sRect.left, sLineY, XPR_NULL);
        ::LineTo(sDC, sRect.left + sTextInset, sLineY);

        const xpr_sint_t sTextRight =
            sRect.left + sTextInset + sTextSize.cx + sTextGap;
        ::MoveToEx(sDC, sTextRight, sLineY, XPR_NULL);
        ::LineTo(sDC, sRect.right - 1, sLineY);
        ::LineTo(sDC, sRect.right - 1, sRect.bottom - 1);
        ::LineTo(sDC, sRect.left, sRect.bottom - 1);
        ::LineTo(sDC, sRect.left, sLineY);

        ::SelectObject(sDC, sOldPen);
        ::DeleteObject(sPen);
    }

    RECT sTextRect = sRect;
    sTextRect.left += sTextInset;
    sTextRect.right = min(
        sRect.right,
        sTextRect.left + sTextSize.cx + sTextGap);
    sTextRect.bottom = max(sTextSize.cy, sLineY * 2);

    ::SetBkMode(sDC, TRANSPARENT);
    ::SetTextColor(
        sDC,
        ::IsWindowEnabled(aHwnd) != FALSE ?
        sPalette.mText :
        sPalette.mSecondaryText);
    ::DrawText(
        sDC,
        sText,
        -1,
        &sTextRect,
        DT_LEFT | DT_TOP | DT_SINGLELINE | DT_END_ELLIPSIS);

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

LRESULT CALLBACK DialogGroupSubclassProc(
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
                drawDialogGroupBox(aHwnd);
                return 0;
            }
            break;
        }

        case WM_ENABLE:
        case WM_SETTEXT:
        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                DialogGroupSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
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
        // The native tab control already sizes items for its labels.  The
        // former 8-DPI-pixel inset on both sides consumed too much of that
        // native width and truncated short labels such as "License" and
        // "Credits".  Keep only a small text inset; image-bearing tabs add
        // their own image/text gap below.
        const xpr_sint_t sPadding =
            ModernUI::scaleForWindow(3, aHwnd);
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
    // Match the standard navigation touch target without changing tree
    // hierarchy, scrolling, image-list indices or keyboard focus.
    return scaleForWindow(38, aHwnd);
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
    // Separate the preference-page breadcrumb/description from its controls.
    // Do not resize fixed-layout checkboxes within their legacy resources.
    return scaleForWindow(16, aHwnd);
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

void ModernUI::dismissOwnedDropdowns(HWND aDialogHwnd)
{
    if (!::IsWindow(aDialogHwnd))
        return;
    HWND sOwner = ::GetWindow(aDialogHwnd, GW_OWNER);
    if (!::IsWindow(sOwner))
        return;
    // EnumChildWindows includes the native ComboBox inside each ComboBoxEx.
    ::EnumChildWindows(sOwner, CloseOwnedDropdownProc, 0);
}

void ModernUI::emphasizeDialogEdit(HWND aHwnd)
{
    if (!::IsWindow(aHwnd))
        return;
    ::SetPropW(aHwnd, kDialogEmphasizedEditProperty,
        reinterpret_cast<HANDLE>(1));
    ::RedrawWindow(aHwnd, NULL, NULL, RDW_INVALIDATE | RDW_FRAME);
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
        else if (sButtonType == BS_GROUPBOX)
        {
            ::SetWindowSubclass(
                aHwnd,
                DialogGroupSubclassProc,
                kDialogGroupSubclassId,
                0);
        }
    }
    else if (_tcsicmp(
                 sClassName,
                 XPR_STRING_LITERAL("Edit")) == 0)
    {
        ::SetWindowSubclass(
            aHwnd,
            DialogEditSubclassProc,
            kDialogEditSubclassId,
            0);
    }
    else if (_tcsicmp(
                 sClassName,
                 XPR_STRING_LITERAL("ComboBox")) == 0)
    {
        const LONG_PTR sStyle =
            ::GetWindowLongPtr(aHwnd, GWL_STYLE);
        if ((sStyle & CBS_DROPDOWNLIST) == CBS_DROPDOWNLIST)
        {
            ::SetWindowSubclass(
                aHwnd,
                DialogComboSubclassProc,
                kDialogComboSubclassId,
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

    const bool sListOrTree =
        _tcsicmp(sClassName, XPR_STRING_LITERAL("SysListView32")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0;
    const bool sScrollableEdit =
        _tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0 &&
        (::GetWindowLongPtr(aHwnd, GWL_STYLE) &
            (WS_VSCROLL | WS_HSCROLL)) != 0;
    if (sListOrTree || sScrollableEdit)
    {
        const bool sDark = XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast);
        if (sDark)
            ::SetWindowSubclass(aHwnd, DialogScrollableSubclassProc,
                kDialogScrollSubclassId, 0);
        ModernUI::configureDarkScrollbarOverlay(
            aHwnd, sDark ? &sPalette : NULL);
        if (!sDark)
            ::RemoveWindowSubclass(aHwnd,
                DialogScrollableSubclassProc, kDialogScrollSubclassId);
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
        // Hover/pressed are transient command/control states, not content
        // selection. Keep them neutral like current Windows 11 command
        // surfaces; mSelection/mFocus remain the accent-bearing semantics.
        const xpr_uint_t sHoverTextLift =
            XPR_IS_TRUE(sPalette.mDark) ? 6 : 4;
        const xpr_uint_t sPressedTextLift =
            XPR_IS_TRUE(sPalette.mDark) ? 11 : 7;
        sPalette.mHover = blendColor(
            sPalette.mElevated,
            sPalette.mText,
            sHoverTextLift);
        sPalette.mPressed = blendColor(
            sPalette.mElevated,
            sPalette.mText,
            sPressedTextLift);
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

namespace
{
// UI-02: mirror the OS scrollbar's measured rectangles, never replace its
// HWND, hit testing, keyboard behavior, focus, scroll range or thumb tracking.
// Invoked only from a coalesced posted owner-window message after native processing.
// Never call synchronously from WM_NCPAINT or a scroll notification.
void PaintDarkScrollBarPart(
    HDC aDC, const SCROLLBARINFO &aInfo, const RECT &aWindowRect,
    const ThemePalette &aPalette, bool aVertical)
{
    if ((aInfo.rgstate[0] &
         (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) != 0)
        return;

    RECT sBar = aInfo.rcScrollBar;
    ::OffsetRect(&sBar, -aWindowRect.left, -aWindowRect.top);
    if (sBar.right <= sBar.left || sBar.bottom <= sBar.top)
        return;

    ::SetDCBrushColor(aDC, aPalette.mSurface);
    ::FillRect(aDC, &sBar, static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    const int sLength =
        aVertical ? sBar.bottom - sBar.top : sBar.right - sBar.left;
    const int sButtonExtent =
        min(max(0, aInfo.dxyLineButton), sLength / 2);

    // The native SCROLLBARINFO child states distinguish disabled arrows.
    if (sButtonExtent > 0)
    {
        HPEN sPen = ::CreatePen(PS_SOLID, 1, aPalette.mSecondaryText);
        HGDIOBJ sOldPen = sPen != NULL ?
            ::SelectObject(aDC, sPen) : NULL;
        for (int sIndex = 0; sIndex < 2; ++sIndex)
        {
            RECT sButton = sBar;
            if (aVertical)
            {
                if (sIndex == 0) sButton.bottom = sBar.top + sButtonExtent;
                else sButton.top = sBar.bottom - sButtonExtent;
            }
            else
            {
                if (sIndex == 0) sButton.right = sBar.left + sButtonExtent;
                else sButton.left = sBar.right - sButtonExtent;
            }
            // SCROLLBARINFO index 1 is top/right; index 5 is bottom/left.
            // The native horizontal bar's left/right arrow states are
            // reversed relative to the vertical bar's top/bottom arrows.
            const DWORD sState = aInfo.rgstate[
                aVertical ? (sIndex == 0 ? 1 : 5) :
                            (sIndex == 0 ? 5 : 1)];
            ::SetDCBrushColor(
                aDC, (sState & STATE_SYSTEM_PRESSED) != 0 ?
                    aPalette.mPressed : aPalette.mChrome);
            ::FillRect(
                aDC, &sButton,
                static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
            if (sOldPen == NULL ||
                (sState & STATE_SYSTEM_UNAVAILABLE) != 0)
                continue;

            const int sCenterX = (sButton.left + sButton.right) / 2;
            const int sCenterY = (sButton.top + sButton.bottom) / 2;
            const int sRadius = max(1, min(
                sButton.right - sButton.left,
                sButton.bottom - sButton.top) / 6);
            if (aVertical)
            {
                const int sDirection = sIndex == 0 ? -1 : 1;
                ::MoveToEx(aDC, sCenterX - sRadius,
                    sCenterY - sDirection, NULL);
                ::LineTo(aDC, sCenterX, sCenterY + sDirection * sRadius);
                ::LineTo(aDC, sCenterX + sRadius,
                    sCenterY - sDirection);
            }
            else
            {
                const int sDirection = sIndex == 0 ? -1 : 1;
                ::MoveToEx(aDC, sCenterX - sDirection,
                    sCenterY - sRadius, NULL);
                ::LineTo(aDC, sCenterX + sDirection * sRadius, sCenterY);
                ::LineTo(aDC, sCenterX - sDirection,
                    sCenterY + sRadius);
            }
        }
        if (sOldPen != NULL)
            ::SelectObject(aDC, sOldPen);
        if (sPen != NULL)
            ::DeleteObject(sPen);
    }

    if ((aInfo.rgstate[3] &
         (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) == 0 &&
        aInfo.xyThumbBottom > aInfo.xyThumbTop)
    {
        RECT sThumb = sBar;
        const int sTrackStart = aVertical ? sBar.top : sBar.left;
        if (aVertical)
        {
            sThumb.top = sTrackStart + aInfo.xyThumbTop;
            sThumb.bottom = sTrackStart + aInfo.xyThumbBottom;
            sThumb.left += 3;
            sThumb.right -= 3;
        }
        else
        {
            sThumb.left = sTrackStart + aInfo.xyThumbTop;
            sThumb.right = sTrackStart + aInfo.xyThumbBottom;
            sThumb.top += 3;
            sThumb.bottom -= 3;
        }
        sThumb.left = max(sThumb.left, sBar.left + 1);
        sThumb.top = max(sThumb.top, sBar.top + 1);
        sThumb.right = min(sThumb.right, sBar.right - 1);
        sThumb.bottom = min(sThumb.bottom, sBar.bottom - 1);
        if (sThumb.right > sThumb.left && sThumb.bottom > sThumb.top)
        {
            const COLORREF sThumbColor =
                (aInfo.rgstate[3] & STATE_SYSTEM_PRESSED) != 0 ?
                aPalette.mText : blendColor(
                    aPalette.mSurface, aPalette.mText, 48);
            HBRUSH sBrush = ::CreateSolidBrush(sThumbColor);
            if (sBrush != NULL)
            {
                HGDIOBJ sOldBrush = ::SelectObject(aDC, sBrush);
                HGDIOBJ sOldPen =
                    ::SelectObject(aDC, ::GetStockObject(NULL_PEN));
                ::RoundRect(aDC, sThumb.left, sThumb.top,
                    sThumb.right, sThumb.bottom, 6, 6);
                ::SelectObject(aDC, sOldPen);
                ::SelectObject(aDC, sOldBrush);
                ::DeleteObject(sBrush);
            }
        }
    }
}
// UI-02: separate owner-attached layered windows own the final Dark
// scrollbar pixels. Their hit testing is transparent, so USER32 still owns
// the native WS_*SCROLL input, range, focus, accessibility and thumb tracking.
// In contrast, painting the target's nonclient DC loses to native modal draws.
const wchar_t kDarkScrollbarOverlayClass[] =
    L"flyExplorer.DarkScrollbarOverlay.v1";

struct DarkScrollbarEntry
{
    HWND mTarget;
    HWND mVerticalPopup;
    HWND mHorizontalPopup;
    HWND mCornerPopup;
    ThemePalette mPalette;
    SCROLLBARINFO mLastVertical;
    SCROLLBARINFO mLastHorizontal;
    RECT mLastCorner;
    bool mVerticalValid;
    bool mHorizontalValid;
    bool mCornerValid;
    bool mForce;
    bool mPopupTopMost;
    HWND mPopupHostRoot;
};

static thread_local std::vector<DarkScrollbarEntry> sDarkScrollbarEntries;
static thread_local HHOOK sDarkScrollbarCallRetHook = NULL;
static thread_local HHOOK sDarkScrollbarFilterHook = NULL;
static thread_local bool sDarkScrollbarUpdating = false;

LRESULT CALLBACK DarkScrollbarPopupProc(
    HWND aHwnd, UINT aMessage, WPARAM aWParam, LPARAM aLParam)
{
    // Same-thread HTTRANSPARENT and layered WS_EX_TRANSPARENT were verified
    // together while real native thumbs moved under a pinned opaque popup.
    if (aMessage == WM_NCHITTEST)
        return HTTRANSPARENT;
    if (aMessage == WM_MOUSEACTIVATE)
        return MA_NOACTIVATE;
    return ::DefWindowProcW(aHwnd, aMessage, aWParam, aLParam);
}

bool EnsureDarkScrollbarPopupClass()
{
    static bool sRegistered = false;
    if (sRegistered)
        return true;

    WNDCLASSW sClass = {0};
    sClass.hInstance = ::GetModuleHandleW(NULL);
    sClass.lpfnWndProc = DarkScrollbarPopupProc;
    sClass.lpszClassName = kDarkScrollbarOverlayClass;
    if (::RegisterClassW(&sClass) == 0 &&
        ::GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
        return false;
    sRegistered = true;
    return true;
}

void HideDarkScrollbarPopup(HWND aPopup)
{
    if (::IsWindow(aPopup))
        ::ShowWindow(aPopup, SW_HIDE);
}

HWND EnsureDarkScrollbarPopup(HWND aTarget, HWND &aPopup)
{
    if (::IsWindow(aPopup))
        return aPopup;
    if (!EnsureDarkScrollbarPopupClass())
        return NULL;
    HWND sRoot = ::GetAncestor(aTarget, GA_ROOT);
    if (sRoot == NULL)
        return NULL;
    aPopup = ::CreateWindowExW(
        WS_EX_LAYERED | WS_EX_TRANSPARENT |
            WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
        kDarkScrollbarOverlayClass, L"", WS_POPUP,
        0, 0, 1, 1, sRoot, NULL, ::GetModuleHandleW(NULL), NULL);
    return aPopup;
}

// Create one premultiplied-alpha opaque surface in the overlay's own HWND.
// USER32 can repaint the native scrollbar without overwriting these pixels.
bool ComposeDarkScrollbarPopup(
    HWND aPopup, const RECT &aScreenRect,
    const SCROLLBARINFO *aScrollbar,
    const ThemePalette &aPalette, bool aVertical, bool aPopupTopMost)
{
    const int sWidth = aScreenRect.right - aScreenRect.left;
    const int sHeight = aScreenRect.bottom - aScreenRect.top;
    if (sWidth <= 0 || sHeight <= 0 ||
        sWidth > 8192 || sHeight > 8192)
        return false;
    HDC sScreen = ::GetDC(NULL);
    HDC sMemory = sScreen ? ::CreateCompatibleDC(sScreen) : NULL;
    BITMAPINFO sBitmapInfo = {0};
    sBitmapInfo.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    sBitmapInfo.bmiHeader.biWidth = sWidth;
    sBitmapInfo.bmiHeader.biHeight = -sHeight;
    sBitmapInfo.bmiHeader.biPlanes = 1;
    sBitmapInfo.bmiHeader.biBitCount = 32;
    void *sPixels = NULL;
    HBITMAP sBitmap = sMemory ?
        ::CreateDIBSection(sScreen, &sBitmapInfo, DIB_RGB_COLORS,
            &sPixels, NULL, 0) : NULL;

    bool sComposed = false;
    if (sBitmap != NULL && sPixels != NULL)
    {
        HGDIOBJ sOldBitmap = ::SelectObject(sMemory, sBitmap);
        if (aScrollbar != NULL)
        {
            PaintDarkScrollBarPart(
                sMemory, *aScrollbar, aScrollbar->rcScrollBar,
                aPalette, aVertical);
        }
        else
        {
            RECT sFill = {0, 0, sWidth, sHeight};
            ::SetDCBrushColor(sMemory, aPalette.mSurface);
            ::FillRect(sMemory, &sFill,
                static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
        }

        // GDI's RGB renderer leaves DIB alpha unset. This popup is entirely
        // opaque, so set all alpha bytes after drawing its native geometry.
        DWORD *sPixels32 = static_cast<DWORD *>(sPixels);
        const size_t sPixelCount =
            static_cast<size_t>(sWidth) * static_cast<size_t>(sHeight);
        for (size_t i = 0; i < sPixelCount; ++i)
            sPixels32[i] |= 0xFF000000u;

        POINT sDestination = {aScreenRect.left, aScreenRect.top};
        POINT sOrigin = {0, 0};
        SIZE sSize = {sWidth, sHeight};
        BLENDFUNCTION sBlend = {AC_SRC_OVER, 0, 255, AC_SRC_ALPHA};
        sComposed =
            ::UpdateLayeredWindow(
                aPopup, sScreen, &sDestination, &sSize, sMemory,
                &sOrigin, 0, &sBlend, ULW_ALPHA) != FALSE;
        ::SelectObject(sMemory, sOldBitmap);
        ::DeleteObject(sBitmap);
    }

    if (sMemory != NULL)
        ::DeleteDC(sMemory);
    if (sScreen != NULL)
        ::ReleaseDC(NULL, sScreen);
    if (sComposed)
        ::SetWindowPos(
            aPopup, aPopupTopMost ? HWND_TOPMOST : HWND_TOP,
            aScreenRect.left, aScreenRect.top,
            sWidth, sHeight, SWP_NOACTIVATE | SWP_SHOWWINDOW);
    else
        HideDarkScrollbarPopup(aPopup);
    return sComposed;
}

bool SameScrollbarSnapshot(
    const SCROLLBARINFO &aLeft, const SCROLLBARINFO &aRight)
{
    return ::EqualRect(
        &aLeft.rcScrollBar, &aRight.rcScrollBar) != FALSE &&
        aLeft.dxyLineButton == aRight.dxyLineButton &&
        aLeft.xyThumbTop == aRight.xyThumbTop &&
        aLeft.xyThumbBottom == aRight.xyThumbBottom &&
        aLeft.rgstate[0] == aRight.rgstate[0] &&
        aLeft.rgstate[1] == aRight.rgstate[1] &&
        aLeft.rgstate[3] == aRight.rgstate[3] &&
        aLeft.rgstate[5] == aRight.rgstate[5];
}

bool SyncDarkScrollbarPart(
    DarkScrollbarEntry &aEntry, bool aVertical)
{
    SCROLLBARINFO sInfo = {0};
    sInfo.cbSize = sizeof(sInfo);
    const LONG sObject = aVertical ? OBJID_VSCROLL : OBJID_HSCROLL;
    HWND &sPopup =
        aVertical ? aEntry.mVerticalPopup : aEntry.mHorizontalPopup;
    SCROLLBARINFO &sPrevious =
        aVertical ? aEntry.mLastVertical : aEntry.mLastHorizontal;
    bool &sValid =
        aVertical ? aEntry.mVerticalValid : aEntry.mHorizontalValid;
    const DWORD sStyle = static_cast<DWORD>(
        ::GetWindowLongPtr(aEntry.mTarget, GWL_STYLE));
    const bool sVisible =
        (sStyle & (aVertical ? WS_VSCROLL : WS_HSCROLL)) != 0 &&
        ::GetScrollBarInfo(aEntry.mTarget, sObject, &sInfo) != FALSE &&
        (sInfo.rgstate[0] &
            (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) == 0;

    if (!sVisible)
    {
        HideDarkScrollbarPopup(sPopup);
        sValid = false;
        return false;
    }

    if (sValid && !aEntry.mForce &&
        ::IsWindowVisible(sPopup) &&
        SameScrollbarSnapshot(sInfo, sPrevious))
        return true;
    if (EnsureDarkScrollbarPopup(aEntry.mTarget, sPopup) == NULL)
        return false;
    if (!ComposeDarkScrollbarPopup(
            sPopup, sInfo.rcScrollBar, &sInfo, aEntry.mPalette,
            aVertical, aEntry.mPopupTopMost))
    {
        sValid = false;
        return false;
    }
    sPrevious = sInfo;
    sValid = true;
    return true;
}

void SyncDarkScrollbarEntry(DarkScrollbarEntry &aEntry)
{
    // ComboLBox is a desktop-owned popup: GA_ROOTOWNER does NOT identify
    // the containing MFC window. The address control passes its real host.
    const HWND sRootOwner =
        ::IsWindow(aEntry.mPopupHostRoot) ?
            aEntry.mPopupHostRoot :
            ::GetAncestor(aEntry.mTarget, GA_ROOTOWNER);
    const HWND sForeground = ::GetForegroundWindow();
    const HWND sTargetRoot =
        ::GetAncestor(aEntry.mTarget, GA_ROOT);
    const bool sPopupOccluded =
        aEntry.mPopupTopMost &&
        ((::IsWindow(sRootOwner) &&
          !::IsWindowEnabled(sRootOwner)) ||
         (sForeground != NULL && sForeground != sRootOwner &&
          sForeground != sTargetRoot));
    if (!::IsWindow(aEntry.mTarget) ||
        !::IsWindowVisible(aEntry.mTarget) || sPopupOccluded)
    {
        HideDarkScrollbarPopup(aEntry.mVerticalPopup);
        HideDarkScrollbarPopup(aEntry.mHorizontalPopup);
        HideDarkScrollbarPopup(aEntry.mCornerPopup);
        aEntry.mVerticalValid = false;
        aEntry.mHorizontalValid = false;
        aEntry.mCornerValid = false;
        return;
    }

    const bool sVertical = SyncDarkScrollbarPart(aEntry, true);
    const bool sHorizontal = SyncDarkScrollbarPart(aEntry, false);
    if (sVertical && sHorizontal)
    {
        RECT sCorner = {
            aEntry.mLastVertical.rcScrollBar.left,
            aEntry.mLastHorizontal.rcScrollBar.top,
            aEntry.mLastVertical.rcScrollBar.right,
            aEntry.mLastHorizontal.rcScrollBar.bottom
        };
        if (sCorner.right > sCorner.left &&
            sCorner.bottom > sCorner.top)
        {
            if (!aEntry.mCornerValid || aEntry.mForce ||
                ::IsWindowVisible(aEntry.mCornerPopup) == FALSE ||
                ::EqualRect(&aEntry.mLastCorner, &sCorner) == FALSE)
            {
                if (EnsureDarkScrollbarPopup(
                        aEntry.mTarget, aEntry.mCornerPopup) != NULL &&
                    ComposeDarkScrollbarPopup(
                        aEntry.mCornerPopup, sCorner, NULL,
                        aEntry.mPalette, true, aEntry.mPopupTopMost))
                {
                    aEntry.mLastCorner = sCorner;
                    aEntry.mCornerValid = true;
                }
                else
                    aEntry.mCornerValid = false;
            }
        }
        else
        {
            HideDarkScrollbarPopup(aEntry.mCornerPopup);
            aEntry.mCornerValid = false;
        }
    }
    else
    {
        HideDarkScrollbarPopup(aEntry.mCornerPopup);
        aEntry.mCornerValid = false;
    }
    aEntry.mForce = false;
}

void SyncDarkScrollbarEntries(void)
{
    if (sDarkScrollbarUpdating)
        return;
    sDarkScrollbarUpdating = true;
    for (size_t i = 0; i < sDarkScrollbarEntries.size(); ++i)
        SyncDarkScrollbarEntry(sDarkScrollbarEntries[i]);
    sDarkScrollbarUpdating = false;
}

LRESULT CALLBACK DarkScrollbarCallRet(
    int aCode, WPARAM aWParam, LPARAM aLParam)
{
    if (aCode >= 0 && aLParam != 0 && !sDarkScrollbarUpdating)
    {
        const CWPRETSTRUCT *sEvent =
            reinterpret_cast<const CWPRETSTRUCT *>(aLParam);
        const UINT sMsg = sEvent->message;
        const bool sVisibilityOrPosition =
            sMsg == WM_WINDOWPOSCHANGED ||
            sMsg == WM_MOVE || sMsg == WM_SHOWWINDOW;
        const bool sNativeScroll =
            sMsg == WM_VSCROLL || sMsg == WM_HSCROLL ||
            sMsg == WM_NCPAINT || sMsg == WM_NCLBUTTONUP;
        const bool sOwnerState =
            sMsg == WM_ENABLE || sMsg == WM_ACTIVATE ||
            sMsg == WM_ACTIVATEAPP;
        bool sRelevant = false;
        for (size_t i = 0; i < sDarkScrollbarEntries.size(); ++i)
        {
            const HWND sTarget = sDarkScrollbarEntries[i].mTarget;
            if ((sEvent->hwnd == sTarget &&
                 (sVisibilityOrPosition || sNativeScroll)) ||
                (sVisibilityOrPosition &&
                 ::IsChild(sEvent->hwnd, sTarget)) ||
                (sOwnerState &&
                 sDarkScrollbarEntries[i].mPopupTopMost &&
                 sEvent->hwnd ==
                    (::IsWindow(sDarkScrollbarEntries[i].mPopupHostRoot) ?
                        sDarkScrollbarEntries[i].mPopupHostRoot :
                        ::GetAncestor(sTarget, GA_ROOTOWNER))))
            {
                sRelevant = true;
                break;
            }
        }
        if (sRelevant)
            SyncDarkScrollbarEntries();
    }
    return ::CallNextHookEx(
        sDarkScrollbarCallRetHook, aCode, aWParam, aLParam);
}

LRESULT CALLBACK DarkScrollbarModalFilter(
    int aCode, WPARAM aWParam, LPARAM aLParam)
{
    // Native thumb tracking has its own modal message loop. Unlike a
    // deferred PostMessage, this documented thread hook still sees input.
    if (aCode == MSGF_SCROLLBAR && aLParam != 0 &&
        !sDarkScrollbarUpdating)
    {
        const MSG *sMsg = reinterpret_cast<const MSG *>(aLParam);
        if (sMsg->message == WM_MOUSEMOVE ||
            sMsg->message == WM_LBUTTONUP ||
            sMsg->message == WM_NCMOUSEMOVE)
            SyncDarkScrollbarEntries();
    }
    return ::CallNextHookEx(
        sDarkScrollbarFilterHook, aCode, aWParam, aLParam);
}

void StartDarkScrollbarHooks(void)
{
    if (sDarkScrollbarCallRetHook == NULL)
        sDarkScrollbarCallRetHook = ::SetWindowsHookExW(
            WH_CALLWNDPROCRET, DarkScrollbarCallRet,
            NULL, ::GetCurrentThreadId());
    if (sDarkScrollbarFilterHook == NULL)
        sDarkScrollbarFilterHook = ::SetWindowsHookExW(
            WH_MSGFILTER, DarkScrollbarModalFilter,
            NULL, ::GetCurrentThreadId());
}

void StopDarkScrollbarHooks(void)
{
    if (sDarkScrollbarCallRetHook != NULL)
        ::UnhookWindowsHookEx(sDarkScrollbarCallRetHook);
    if (sDarkScrollbarFilterHook != NULL)
        ::UnhookWindowsHookEx(sDarkScrollbarFilterHook);
    sDarkScrollbarCallRetHook = NULL;
    sDarkScrollbarFilterHook = NULL;
}

DarkScrollbarEntry *FindDarkScrollbarEntry(HWND aTarget)
{
    for (size_t i = 0; i < sDarkScrollbarEntries.size(); ++i)
        if (sDarkScrollbarEntries[i].mTarget == aTarget)
            return &sDarkScrollbarEntries[i];
    return NULL;
}

void RemoveDarkScrollbarEntry(HWND aTarget)
{
    if (sDarkScrollbarUpdating)
        return;
    sDarkScrollbarUpdating = true;
    for (std::vector<DarkScrollbarEntry>::iterator it =
            sDarkScrollbarEntries.begin();
         it != sDarkScrollbarEntries.end(); ++it)
    {
        if (it->mTarget == aTarget)
        {
            if (::IsWindow(it->mVerticalPopup))
                ::DestroyWindow(it->mVerticalPopup);
            if (::IsWindow(it->mHorizontalPopup))
                ::DestroyWindow(it->mHorizontalPopup);
            if (::IsWindow(it->mCornerPopup))
                ::DestroyWindow(it->mCornerPopup);
            sDarkScrollbarEntries.erase(it);
            break;
        }
    }
    if (sDarkScrollbarEntries.empty())
        StopDarkScrollbarHooks();
    sDarkScrollbarUpdating = false;
}


} // namespace

void ModernUI::configureDarkScrollbarOverlay(
    HWND aHwnd, const ThemePalette *aPalette,
    xpr_bool_t aPopupTopMost, HWND aPopupHost)
{
    if (!::IsWindow(aHwnd))
        return;

    if (aPalette == NULL ||
        XPR_IS_FALSE(aPalette->mDark) ||
        XPR_IS_TRUE(aPalette->mHighContrast))
    {
        RemoveDarkScrollbarEntry(aHwnd);
        return;
    }

    DarkScrollbarEntry *sEntry = FindDarkScrollbarEntry(aHwnd);
    if (sEntry == NULL)
    {
        DarkScrollbarEntry sNew = {0};
        sNew.mTarget = aHwnd;
        sNew.mPalette = *aPalette;
        sNew.mPopupTopMost = XPR_IS_TRUE(aPopupTopMost);
        sNew.mPopupHostRoot =
            ::IsWindow(aPopupHost) ?
                ::GetAncestor(aPopupHost, GA_ROOT) : NULL;
        sNew.mForce = true;
        sDarkScrollbarEntries.push_back(sNew);
        StartDarkScrollbarHooks();
    }
    else
    {
        sEntry->mPalette = *aPalette;
        sEntry->mPopupTopMost = XPR_IS_TRUE(aPopupTopMost);
        sEntry->mPopupHostRoot =
            ::IsWindow(aPopupHost) ?
                ::GetAncestor(aPopupHost, GA_ROOT) : NULL;
        sEntry->mForce = true;
    }
    SyncDarkScrollbarEntries();
}

void ModernUI::removeDarkScrollbarOverlay(HWND aHwnd)
{
    RemoveDarkScrollbarEntry(aHwnd);
}

void ModernUI::paintDarkNativeScrollbars(HWND aHwnd)
{
    // The existing native-first coalesced message now refreshes separately
    // composited Dark pixels rather than painting the native nonclient DC.
    if (::IsWindow(aHwnd) && FindDarkScrollbarEntry(aHwnd) != NULL)
        SyncDarkScrollbarEntries();
}

UINT ModernUI::getDeferredDarkScrollbarMessage(void)
{
    // Registered messages cannot collide with existing MFC/plugin WM_APP IDs.
    static const UINT sMessage =
        ::RegisterWindowMessage(XPR_STRING_LITERAL(
            "flyExplorer.DeferredDarkScrollbarPaint.v2"));
    return sMessage;
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
