//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "cfg_dlg.h"
#include "cfg_dlg_observer.h"

#include "../gui/ModernUI.h"

#include <vector>

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cfg
{
namespace
{
const UINT_PTR kModernGroupBoxSubclassId = 0x46474342; // 'FGCB'

const UINT_PTR kModernCfgComboSubclassId = 0x46474343; // 'FGCC'
const UINT_PTR kModernCfgToggleSubclassId = 0x46474354; // 'FGCT'
const UINT_PTR kModernCfgPushButtonSubclassId = 0x46474350; // 'FGCP'
const UINT_PTR kModernCfgEditSubclassId = 0x46474345; // 'FGCE'

void SnapshotChildWindows(HWND aParentHwnd, std::vector<HWND> &aChildHwnds)
{
    aChildHwnds.clear();

    if (XPR_IS_NULL(aParentHwnd) || ::IsWindow(aParentHwnd) == FALSE)
        return;

    HWND sChildHwnd = ::GetWindow(aParentHwnd, GW_CHILD);
    while (XPR_IS_NOT_NULL(sChildHwnd))
    {
        aChildHwnds.push_back(sChildHwnd);
        sChildHwnd = ::GetWindow(sChildHwnd, GW_HWNDNEXT);
    }
}

void DrawModernCfgCombo(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return;

    const LONG_PTR sStyle = ::GetWindowLongPtr(aHwnd, GWL_STYLE);
    if ((sStyle & CBS_DROPDOWNLIST) != CBS_DROPDOWNLIST)
        return;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast) || XPR_IS_FALSE(sPalette.mDark))
        return;

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
        XPR_TRUE : XPR_FALSE;

    POINT sCursor = {0};
    xpr_bool_t sHotButton = XPR_FALSE;
    if (::GetCursorPos(&sCursor) != FALSE &&
        ::ScreenToClient(aHwnd, &sCursor) != FALSE &&
        ::PtInRect(&sComboInfo.rcButton, sCursor) != FALSE)
    {
        sHotButton = XPR_TRUE;
    }

    COLORREF sFieldColor =
        XPR_IS_TRUE(sEnabled) ? sPalette.mElevated : sPalette.mCard;
    COLORREF sTextColor =
        XPR_IS_TRUE(sEnabled) ? sPalette.mText : sPalette.mSecondaryText;
    COLORREF sButtonColor = sFieldColor;
    if (XPR_IS_TRUE(sDropped))
        sButtonColor = sPalette.mPressed;
    else if (XPR_IS_TRUE(sHotButton) && XPR_IS_TRUE(sEnabled))
        sButtonColor = sPalette.mHover;

    ::SetDCBrushColor(sDC, sFieldColor);
    ::FillRect(
        sDC,
        &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    RECT sTextRect = sComboInfo.rcItem;
    const xpr_sint_t sTextMargin =
        ui::ModernUI::getAddressTextMargin(aHwnd);
    sTextRect.left += sTextMargin;
    sTextRect.right -= sTextMargin;

    xpr_tchar_t sText[256] = {0};
    ::GetWindowText(aHwnd, sText, XPR_COUNT_OF(sText));

    HFONT sFont = reinterpret_cast<HFONT>(
        ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = ::SelectObject(sDC, sFont);

    ::SetBkMode(sDC, TRANSPARENT);
    ::SetTextColor(sDC, sTextColor);
    ::DrawText(
        sDC,
        sText,
        -1,
        &sTextRect,
        DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::SetDCBrushColor(sDC, sButtonColor);
    ::FillRect(
        sDC,
        &sComboInfo.rcButton,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    RECT sSeparatorRect = sComboInfo.rcButton;
    sSeparatorRect.right =
        sSeparatorRect.left +
        max(1, ui::ModernUI::scaleForWindow(1, aHwnd));
    ::SetDCBrushColor(sDC, sPalette.mSeparator);
    ::FillRect(
        sDC,
        &sSeparatorRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    const xpr_sint_t sCenterX =
        (sComboInfo.rcButton.left + sComboInfo.rcButton.right) / 2;
    const xpr_sint_t sCenterY =
        (sComboInfo.rcButton.top + sComboInfo.rcButton.bottom) / 2;
    const xpr_sint_t sHalfWidth =
        max(2, ui::ModernUI::scaleForWindow(3, aHwnd));
    const xpr_sint_t sOffset =
        max(1, ui::ModernUI::scaleForWindow(2, aHwnd));

    HPEN sArrowPen = ::CreatePen(PS_SOLID, 1, sTextColor);
    if (XPR_IS_NOT_NULL(sArrowPen))
    {
        HGDIOBJ sOldPen = ::SelectObject(sDC, sArrowPen);
        ::MoveToEx(sDC, sCenterX - sHalfWidth, sCenterY - sOffset, XPR_NULL);
        ::LineTo(sDC, sCenterX, sCenterY + sOffset);
        ::LineTo(sDC, sCenterX + sHalfWidth, sCenterY - sOffset);
        ::SelectObject(sDC, sOldPen);
        ::DeleteObject(sArrowPen);
    }

    const COLORREF sBorderColor =
        XPR_IS_TRUE(sFocused) ? sPalette.mFocus : sPalette.mSeparator;
    ::SetDCBrushColor(sDC, sBorderColor);
    ::FrameRect(
        sDC,
        &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    ::ReleaseDC(aHwnd, sDC);
}

LRESULT CALLBACK ModernCfgComboSubclassProc(
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
            DrawModernCfgCombo(aHwnd);
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

        case CB_SHOWDROPDOWN:
        {
            const LRESULT sResult =
                ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);

            COMBOBOXINFO sComboInfo = {0};
            sComboInfo.cbSize = sizeof(COMBOBOXINFO);
            if (::GetComboBoxInfo(aHwnd, &sComboInfo) != FALSE &&
                XPR_IS_NOT_NULL(sComboInfo.hwndList))
            {
                const ui::ThemePalette sPalette =
                    ui::ModernUI::getPalette();
                if (XPR_IS_TRUE(sPalette.mDark) &&
                    XPR_IS_FALSE(sPalette.mHighContrast))
                {
                    ui::ModernUI::resetControlTheme(sComboInfo.hwndList);
                }
                else
                {
                    ui::ModernUI::applyExplorerControlTheme(
                        sComboInfo.hwndList);
                }

                ::InvalidateRect(sComboInfo.hwndList, XPR_NULL, TRUE);
            }

            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            return sResult;
        }

        case WM_MOUSELEAVE:
        case WM_LBUTTONDOWN:
        case WM_LBUTTONUP:
        case WM_ENABLE:
        case WM_SETFOCUS:
        case WM_KILLFOCUS:
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                ModernCfgComboSubclassProc,
                aSubclassId);
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}


xpr_bool_t IsModernCfgToggleType(DWORD aButtonType)
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

void DrawModernCfgToggle(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast) || XPR_IS_FALSE(sPalette.mDark))
        return;

    const DWORD sButtonType =
        static_cast<DWORD>(::GetWindowLongPtr(aHwnd, GWL_STYLE)) & BS_TYPEMASK;
    if (XPR_IS_FALSE(IsModernCfgToggleType(sButtonType)))
        return;

    PAINTSTRUCT sPaint = {0};
    HDC sDC = ::BeginPaint(aHwnd, &sPaint);
    if (XPR_IS_NULL(sDC))
        return;

    RECT sClientRect = {0};
    ::GetClientRect(aHwnd, &sClientRect);

    ::SetDCBrushColor(sDC, sPalette.mCard);
    ::FillRect(
        sDC,
        &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    const xpr_bool_t sEnabled =
        ::IsWindowEnabled(aHwnd) != FALSE ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sFocused =
        ::GetFocus() == aHwnd ? XPR_TRUE : XPR_FALSE;
    const LRESULT sState = ::SendMessage(aHwnd, BM_GETSTATE, 0, 0);
    const xpr_bool_t sHot =
        (sState & BST_HOT) != 0 ? XPR_TRUE : XPR_FALSE;
    const LRESULT sCheck = ::SendMessage(aHwnd, BM_GETCHECK, 0, 0);

    const xpr_sint_t sGlyphExtent =
        max(12, ui::ModernUI::scaleForWindow(14, aHwnd));
    const xpr_sint_t sGap =
        ui::ModernUI::scaleForWindow(8, aHwnd);
    const xpr_sint_t sTop =
        max(0, (sClientRect.bottom - sClientRect.top - sGlyphExtent) / 2);

    RECT sGlyphRect = {
        sClientRect.left,
        sClientRect.top + sTop,
        sClientRect.left + sGlyphExtent,
        sClientRect.top + sTop + sGlyphExtent
    };

    COLORREF sFill = sPalette.mElevated;
    COLORREF sBorder =
        XPR_IS_TRUE(sFocused) ? sPalette.mFocus : sPalette.mSeparator;
    COLORREF sGlyph = sPalette.mText;
    if (XPR_IS_FALSE(sEnabled))
    {
        sFill = sPalette.mCard;
        sBorder = sPalette.mSeparator;
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
        (sButtonType == BS_RADIOBUTTON || sButtonType == BS_AUTORADIOBUTTON) ?
        XPR_TRUE :
        XPR_FALSE;

    HBRUSH sFillBrush = ::CreateSolidBrush(sFill);
    HPEN sBorderPen = ::CreatePen(PS_SOLID, 1, sBorder);
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
            max(2, ui::ModernUI::scaleForWindow(3, aHwnd));
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
    ::DeleteObject(sBorderPen);
    ::DeleteObject(sFillBrush);

    if (sCheck == BST_CHECKED)
    {
        HPEN sGlyphPen = ::CreatePen(
            PS_SOLID,
            max(1, ui::ModernUI::scaleForWindow(2, aHwnd)),
            sGlyph);
        if (XPR_IS_NOT_NULL(sGlyphPen))
        {
            sOldPen = ::SelectObject(sDC, sGlyphPen);
            if (XPR_IS_TRUE(sRadio))
            {
                const xpr_sint_t sInset =
                    max(3, ui::ModernUI::scaleForWindow(4, aHwnd));
                HBRUSH sDotBrush = ::CreateSolidBrush(sGlyph);
                if (XPR_IS_NOT_NULL(sDotBrush))
                {
                    sOldBrush = ::SelectObject(sDC, sDotBrush);
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
                const xpr_sint_t sX1 = sGlyphRect.left + (sGlyphExtent * 3 / 10);
                const xpr_sint_t sY1 = sGlyphRect.top + (sGlyphExtent * 5 / 10);
                const xpr_sint_t sX2 = sGlyphRect.left + (sGlyphExtent * 45 / 100);
                const xpr_sint_t sY2 = sGlyphRect.top + (sGlyphExtent * 65 / 100);
                const xpr_sint_t sX3 = sGlyphRect.left + (sGlyphExtent * 75 / 100);
                const xpr_sint_t sY3 = sGlyphRect.top + (sGlyphExtent * 35 / 100);
                ::MoveToEx(sDC, sX1, sY1, XPR_NULL);
                ::LineTo(sDC, sX2, sY2);
                ::LineTo(sDC, sX3, sY3);
            }
            ::SelectObject(sDC, sOldPen);
            ::DeleteObject(sGlyphPen);
        }
    }
    else if (sCheck == BST_INDETERMINATE && XPR_IS_FALSE(sRadio))
    {
        RECT sMarkRect = sGlyphRect;
        const xpr_sint_t sInset =
            max(3, ui::ModernUI::scaleForWindow(4, aHwnd));
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
        const xpr_sint_t sFocusInset =
            max(1, ui::ModernUI::scaleForWindow(1, aHwnd));
        ::InflateRect(&sFocusRect, -sFocusInset, -sFocusInset);
        ::DrawFocusRect(sDC, &sFocusRect);
    }

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

LRESULT CALLBACK ModernCfgToggleSubclassProc(
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
            const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mDark) &&
                XPR_IS_FALSE(sPalette.mHighContrast))
            {
                DrawModernCfgToggle(aHwnd);
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
                ModernCfgToggleSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}


void DrawModernCfgEditFrame(HWND aHwnd)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast) || XPR_IS_FALSE(sPalette.mDark))
        return;

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

    // Cover the entire native non-client edge first. A one-pixel overlay is
    // not sufficient for classic/themed EDIT controls because WS_BORDER /
    // WS_EX_CLIENTEDGE can own more than one bright pixel at some DPIs.
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
        sPalette.mSeparator;
    HBRUSH sBorderBrush = ::CreateSolidBrush(sBorder);
    if (XPR_IS_NOT_NULL(sBorderBrush))
    {
        ::FrameRect(sDC, &sWindowRect, sBorderBrush);
        ::DeleteObject(sBorderBrush);
    }

    ::ReleaseDC(aHwnd, sDC);
}

LRESULT CALLBACK ModernCfgEditSubclassProc(
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
            DrawModernCfgEditFrame(aHwnd);
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
            ::RemoveWindowSubclass(
                aHwnd,
                ModernCfgEditSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

xpr_bool_t IsModernCfgPushButtonType(DWORD aButtonType)
{
    return
        aButtonType == BS_PUSHBUTTON ||
        aButtonType == BS_DEFPUSHBUTTON ?
        XPR_TRUE :
        XPR_FALSE;
}

void DrawModernCfgPushButton(HWND aHwnd)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast) || XPR_IS_FALSE(sPalette.mDark))
        return;

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
    HGDIOBJ sOldBrush = ::SelectObject(sDC, sBrush);
    HGDIOBJ sOldPen = ::SelectObject(sDC, sPen);
    const xpr_sint_t sRadius =
        ui::ModernUI::getControlCornerRadius(aHwnd);
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
    ::DeleteObject(sPen);
    ::DeleteObject(sBrush);

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
        &sRect,
        DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

    if (XPR_IS_NOT_NULL(sOldFont))
        ::SelectObject(sDC, sOldFont);

    ::EndPaint(aHwnd, &sPaint);
}

LRESULT CALLBACK ModernCfgPushButtonSubclassProc(
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
            const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mDark) &&
                XPR_IS_FALSE(sPalette.mHighContrast))
            {
                DrawModernCfgPushButton(aHwnd);
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
        case WM_LBUTTONDOWN:
        case WM_LBUTTONUP:
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
                ModernCfgPushButtonSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

LRESULT CALLBACK ModernGroupBoxSubclassProc(
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
            const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mHighContrast))
                break;

            PAINTSTRUCT sPaint = {0};
            HDC sDC = ::BeginPaint(aHwnd, &sPaint);
            if (XPR_IS_NULL(sDC))
                return 0;

            RECT sClientRect = {0};
            ::GetClientRect(aHwnd, &sClientRect);

            // Resource group boxes are section labels, not independent
            // opaque cards. The parent page owns the background. Keeping this
            // child transparent avoids covering sibling radio/check controls
            // whose legacy RC z-order places them inside the group rectangle.
            xpr_tchar_t sText[256] = {0};
            ::GetWindowText(aHwnd, sText, XPR_COUNT_OF(sText));

            HFONT sFont = reinterpret_cast<HFONT>(
                ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
            HGDIOBJ sOldFont = XPR_NULL;
            if (XPR_IS_NOT_NULL(sFont))
                sOldFont = ::SelectObject(sDC, sFont);

            ::SetBkMode(sDC, TRANSPARENT);
            ::SetTextColor(sDC, sPalette.mText);

            RECT sTextRect = sClientRect;
            const xpr_sint_t sInset =
                ui::ModernUI::scaleForWindow(2, aHwnd);
            sTextRect.left += sInset;
            ::DrawText(
                sDC,
                sText,
                -1,
                &sTextRect,
                DT_LEFT | DT_TOP | DT_SINGLELINE | DT_END_ELLIPSIS);

            RECT sMeasureRect = sTextRect;
            ::DrawText(
                sDC,
                sText,
                -1,
                &sMeasureRect,
                DT_LEFT | DT_TOP | DT_SINGLELINE | DT_CALCRECT);

            const xpr_sint_t sLineY =
                min(
                    sClientRect.bottom - 1,
                    max(
                        sClientRect.top,
                        sMeasureRect.bottom +
                            ui::ModernUI::scaleForWindow(4, aHwnd)));
            CPen sSeparatorPen(PS_SOLID, 1, sPalette.mSeparator);
            CPen *sOldPen = CDC::FromHandle(sDC)->SelectObject(&sSeparatorPen);
            ::MoveToEx(sDC, sClientRect.left, sLineY, XPR_NULL);
            ::LineTo(sDC, sClientRect.right, sLineY);
            CDC::FromHandle(sDC)->SelectObject(sOldPen);

            if (XPR_IS_NOT_NULL(sOldFont))
                ::SelectObject(sDC, sOldFont);

            ::EndPaint(aHwnd, &sPaint);
            return 0;
        }

        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                ModernGroupBoxSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

} // namespace

CfgDlg::CfgDlg(xpr_uint_t aResourceId, CWnd *aParentWnd)
    : super(aResourceId, aParentWnd)
    , mObserver(XPR_NULL)
    , mSurfaceColor(CLR_INVALID)
    , mWindowColor(CLR_INVALID)
    , mRefreshingModernAppearance(XPR_FALSE)
    , mResourceId(aResourceId), mCfgIndex(0)
{
}

CfgDlg::~CfgDlg(void)
{
    DELETE_OBJECT(mUIFont);
    DELETE_OBJECT(mSurfaceBrush);
    DELETE_OBJECT(mWindowBrush);
}

void CfgDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
}

CfgDlgObserver *CfgDlg::getObserver(void) const
{
    return mObserver;
}

void CfgDlg::setObserver(CfgDlgObserver *aObserver)
{
    mObserver = aObserver;
}

xpr_bool_t CfgDlg::Create(xpr_size_t aCfgIndex, CWnd *aParentWnd)
{
    mCfgIndex = aCfgIndex;

    return super::Create(mResourceId, aParentWnd);
}

BEGIN_MESSAGE_MAP(CfgDlg, super)
    ON_WM_ERASEBKGND()
    ON_WM_CTLCOLOR()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_DPICHANGED_AFTERPARENT, OnDpiChangedAfterParent)
END_MESSAGE_MAP()

xpr_bool_t CfgDlg::OnInitDialog(void)
{
    super::OnInitDialog();
    refreshModernAppearance();
    return XPR_TRUE;
}

void CfgDlg::applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont)
{
    if (XPR_IS_NULL(aWnd) || ::IsWindow(aWnd->GetSafeHwnd()) == FALSE)
        return;

    xpr_tchar_t sClassName[64] = {0};
    ::GetClassName(aWnd->GetSafeHwnd(), sClassName, XPR_COUNT_OF(sClassName));

    const xpr_bool_t sStandardFontControl =
        (_tcsicmp(sClassName, XPR_STRING_LITERAL("Static")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("Button")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBoxEx32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysListView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTabControl32")) == 0) ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_TRUE(sStandardFontControl) && XPR_IS_NOT_NULL(mUIFont.m_hObject))
    {
        HFONT sCurrentFont = reinterpret_cast<HFONT>(
            aWnd->SendMessage(WM_GETFONT, 0, 0));
        if (XPR_IS_NULL(sCurrentFont) || sCurrentFont == aPreviousFont)
            aWnd->SetFont(&mUIFont, XPR_FALSE);
    }

    const xpr_bool_t sExplorerThemeControl =
        (_tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBoxEx32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysListView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTabControl32")) == 0) ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_TRUE(sExplorerThemeControl))
    {
        const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
        if (XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast))
        {
            ui::ModernUI::resetControlTheme(aWnd->GetSafeHwnd());
        }
        else
        {
            ui::ModernUI::applyExplorerControlTheme(aWnd->GetSafeHwnd());
        }
    }

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("SysListView32")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTabControl32")) == 0)
    {
        // Refresh final palette-owned common-control colors as well as the
        // visual-style association. This keeps blank list/tree/tab surfaces
        // from retaining the previous theme after an in-place theme switch.
        ui::ModernUI::applyDialogControlTheme(aWnd->GetSafeHwnd());
    }

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0)
    {
        ::SetWindowSubclass(
            aWnd->GetSafeHwnd(),
            ModernCfgEditSubclassProc,
            kModernCfgEditSubclassId,
            0);
    }

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0)
    {
        const LONG_PTR sStyle =
            ::GetWindowLongPtr(aWnd->GetSafeHwnd(), GWL_STYLE);
        if ((sStyle & CBS_DROPDOWNLIST) == CBS_DROPDOWNLIST)
        {
            ::SetWindowSubclass(
                aWnd->GetSafeHwnd(),
                ModernCfgComboSubclassProc,
                kModernCfgComboSubclassId,
                0);
        }
    }

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("Button")) == 0)
    {
        const DWORD sButtonType =
            static_cast<DWORD>(aWnd->GetStyle()) & BS_TYPEMASK;
        if (sButtonType == BS_GROUPBOX)
        {
            ::SetWindowSubclass(
                aWnd->GetSafeHwnd(),
                ModernGroupBoxSubclassProc,
                kModernGroupBoxSubclassId,
                0);

            // Legacy RC files often declare GROUPBOX after the controls that
            // visually live inside it. Native group boxes do not obscure
            // those siblings, but an opaque owner-draw child can. Keep the
            // layout container at the bottom of the sibling z-order so radio
            // buttons/check boxes remain visible (notably Layout > Style).
            const LONG_PTR sExStyle =
                ::GetWindowLongPtr(aWnd->GetSafeHwnd(), GWL_EXSTYLE);
            if ((sExStyle & WS_EX_TRANSPARENT) == 0)
            {
                ::SetWindowLongPtr(
                    aWnd->GetSafeHwnd(),
                    GWL_EXSTYLE,
                    sExStyle | WS_EX_TRANSPARENT);
            }

            ::SetWindowPos(
                aWnd->GetSafeHwnd(),
                HWND_BOTTOM,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        }
        else if (XPR_IS_TRUE(IsModernCfgToggleType(sButtonType)))
        {
            ::SetWindowSubclass(
                aWnd->GetSafeHwnd(),
                ModernCfgToggleSubclassProc,
                kModernCfgToggleSubclassId,
                0);
        }
        else if (XPR_IS_TRUE(IsModernCfgPushButtonType(sButtonType)))
        {
            ::SetWindowSubclass(
                aWnd->GetSafeHwnd(),
                ModernCfgPushButtonSubclassProc,
                kModernCfgPushButtonSubclassId,
                0);
        }
    }

    // GROUPBOX modernization can move a child to HWND_BOTTOM. Walking the
    // live sibling chain while changing z-order can revisit the same pair of
    // group boxes forever. Snapshot child HWNDs before processing them.
    std::vector<HWND> sChildHwnds;
    SnapshotChildWindows(aWnd->GetSafeHwnd(), sChildHwnds);
    for (std::vector<HWND>::const_iterator sIterator = sChildHwnds.begin();
         sIterator != sChildHwnds.end();
         ++sIterator)
    {
        if (::IsWindow(*sIterator) == FALSE)
            continue;

        CWnd *sChild = CWnd::FromHandle(*sIterator);
        if (XPR_IS_NOT_NULL(sChild))
            applyModernAppearanceToChild(sChild, aPreviousFont);
    }
}

void CfgDlg::applyModernAppearanceToChildren(HFONT aPreviousFont)
{
    // The direct child list must also be stable before GROUPBOX controls are
    // sent to HWND_BOTTOM by applyModernAppearanceToChild().
    std::vector<HWND> sChildHwnds;
    SnapshotChildWindows(GetSafeHwnd(), sChildHwnds);
    for (std::vector<HWND>::const_iterator sIterator = sChildHwnds.begin();
         sIterator != sChildHwnds.end();
         ++sIterator)
    {
        if (::IsWindow(*sIterator) == FALSE)
            continue;

        CWnd *sChild = CWnd::FromHandle(*sIterator);
        if (XPR_IS_NOT_NULL(sChild))
            applyModernAppearanceToChild(sChild, aPreviousFont);
    }
}

void CfgDlg::refreshModernAppearance(xpr_bool_t aRethemeControls)
{
    if (XPR_IS_NULL(m_hWnd) || XPR_IS_TRUE(mRefreshingModernAppearance))
        return;

    // Child SetWindowTheme calls can synchronously emit WM_THEMECHANGED.
    // Keep one refresh traversal active per settings page.
    mRefreshingModernAppearance = XPR_TRUE;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    const HFONT sPreviousFont = reinterpret_cast<HFONT>(
        SendMessage(WM_GETFONT, 0, 0));

    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())) &&
        XPR_IS_FALSE(
            ui::ModernUI::isSameFont(
                reinterpret_cast<HFONT>(mUIFont.GetSafeHandle()),
                sLogFont)))
    {
        if (XPR_IS_NOT_NULL(mUIFont.m_hObject))
            mUIFont.DeleteObject();

        if (mUIFont.CreateFontIndirect(&sLogFont) == XPR_TRUE)
            SetFont(&mUIFont, XPR_FALSE);
    }

    if (mSurfaceColor != sPalette.mCard)
    {
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            mSurfaceBrush.DeleteObject();
        if (mSurfaceBrush.CreateSolidBrush(sPalette.mCard) == XPR_TRUE)
            mSurfaceColor = sPalette.mCard;
        else
            mSurfaceColor = CLR_INVALID;
    }

    if (mWindowColor != sPalette.mElevated)
    {
        if (XPR_IS_NOT_NULL(mWindowBrush.m_hObject))
            mWindowBrush.DeleteObject();
        if (mWindowBrush.CreateSolidBrush(sPalette.mElevated) == XPR_TRUE)
            mWindowColor = sPalette.mElevated;
        else
            mWindowColor = CLR_INVALID;
    }

    // Config pages contain controls at x/y == 0 in the canonical RC.
    // Rounding the child-window region clips those controls at the corners.
    // Keep the page rectangular and let individual controls/surfaces own
    // their rounded geometry.
    ::SetWindowRgn(GetSafeHwnd(), XPR_NULL, TRUE);
    if (XPR_IS_TRUE(aRethemeControls))
        applyModernAppearanceToChildren(sPreviousFont);
    RedrawWindow(
        XPR_NULL,
        XPR_NULL,
        RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);

    mRefreshingModernAppearance = XPR_FALSE;
}

xpr_bool_t CfgDlg::OnEraseBkgnd(CDC *aDC)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        CRect sClientRect;
        GetClientRect(&sClientRect);
        aDC->FillSolidRect(&sClientRect, sPalette.mCard);
        return XPR_TRUE;
    }

    return super::OnEraseBkgnd(aDC);
}

HBRUSH CfgDlg::OnCtlColor(CDC *aDC, CWnd *aWnd, xpr_uint_t aCtlColor)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast))
        return super::OnCtlColor(aDC, aWnd, aCtlColor);

    aDC->SetTextColor(
        XPR_IS_NOT_NULL(aWnd) && XPR_IS_FALSE(aWnd->IsWindowEnabled()) ?
        sPalette.mSecondaryText :
        sPalette.mText);

    if (aCtlColor == CTLCOLOR_EDIT || aCtlColor == CTLCOLOR_LISTBOX)
    {
        aDC->SetBkMode(OPAQUE);
        aDC->SetBkColor(sPalette.mElevated);
        if (XPR_IS_NOT_NULL(mWindowBrush.m_hObject))
            return (HBRUSH)mWindowBrush.GetSafeHandle();
    }
    else if (aCtlColor == CTLCOLOR_STATIC ||
             aCtlColor == CTLCOLOR_BTN ||
             aCtlColor == CTLCOLOR_DLG)
    {
        aDC->SetBkMode(TRANSPARENT);
        aDC->SetBkColor(sPalette.mCard);
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            return (HBRUSH)mSurfaceBrush.GetSafeHandle();
    }

    return super::OnCtlColor(aDC, aWnd, aCtlColor);
}

void CfgDlg::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    super::OnSettingChange(aFlags, aSection);
    refreshModernAppearance();
}

void CfgDlg::OnSysColorChange(void)
{
    super::OnSysColorChange();
    refreshModernAppearance();
}

LRESULT CfgDlg::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    // A page already owns its child theme associations after creation.
    // Repainting on WM_THEMECHANGED is sufficient and avoids SetWindowTheme
    // feeding another theme notification back into the settings hierarchy.
    refreshModernAppearance(XPR_FALSE);
    return 0;
}

LRESULT CfgDlg::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    return Default();
}

LRESULT CfgDlg::OnDpiChangedAfterParent(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    return Default();
}

void CfgDlg::addIgnoreApply(xpr_uint_t aId)
{
    mIgnoreApplySet.insert(aId);
}

xpr_size_t CfgDlg::getCfgIndex(void) const
{
    return mCfgIndex;
}

xpr_bool_t CfgDlg::isModified(void)
{
    if (XPR_IS_NULL(mObserver))
        return XPR_FALSE;

    return mObserver->onIsModified(*this);
}

void CfgDlg::setModified(xpr_bool_t aModified)
{
    mObserver->onSetModified(*this, aModified);
}

xpr_bool_t CfgDlg::OnCommand(WPARAM wParam, LPARAM lParam) 
{
    xpr_uint_t sNotifyMsg = HIWORD(wParam);
    xpr_uint_t sId = LOWORD(wParam);

    if (sNotifyMsg == BN_CLICKED ||
        sNotifyMsg == EN_UPDATE  ||
        sNotifyMsg == CBN_SELCHANGE)
    {
        if (mIgnoreApplySet.find(sId) == mIgnoreApplySet.end())
        {
            setModified();
        }
    }

    return super::OnCommand(wParam, lParam);
}

xpr_bool_t CfgDlg::PreTranslateMessage(MSG *aMsg) 
{
    return super::PreTranslateMessage(aMsg);
}
} // namespace cfg
} // namespace fxfile
