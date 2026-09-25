/////////////////////////////////////////////////////////////////////////////
// ToolBarEx.cpp: implementation of the CToolBarEx class.
//
/////////////////////////////////////////////////////////////////////////////
// Copyright (c) 2001-2002 by Nikolay Denisov. All rights reserved.
//
// This code is free for personal and commercial use, providing this 
// notice remains intact in the source files and all eventual changes are
// clearly marked with comments.
//
// You must obtain the author's consent before you can include this code
// in a software library.
//
// No warrantee of any kind, express or implied, is included with this
// software; use at your own risk, responsibility for damages (if any) to
// anyone resulting from the use of this software rests entirely with the
// user.
//
// Please email bug reports, bug fixes, enhancements, requests and
// comments to: acnick@mail.lanck.net
/////////////////////////////////////////////////////////////////////////////

#include "stdafx.h"
#include "Resource.h"
#include "CustomizeDialog.h"
#include "SizableReBar.h"
#include "ToolBarEx.h"
#include "WinAppEx.h"
#include "../ModernUI.h"
#include "../../ctrl_id.h"  // Bookmark band: scoped direct paint/print owner.

#include <afxpriv.h>    // ON_MESSAGE_VOID()

#ifdef _DEBUG
#undef THIS_FILE
static char THIS_FILE[]=__FILE__;
#define new DEBUG_NEW
#endif

/////////////////////////////////////////////////////////////////////////////
// CToolBarEx

LPCTSTR             CToolBarEx::m_lpszStateInfoEntry = _T("ToolbarStateInfo");
CToolBarEx*         CToolBarEx::m_pToolBar           = 0;
CCustomizeDialog*   CToolBarEx::m_pCustomizeDlg      = 0;
HHOOK               CToolBarEx::m_hCBTHook           = 0;

IMPLEMENT_DYNAMIC( CToolBarEx, CToolBar )

#ifndef TBCDRF_NOBACKGROUND
#define TBCDRF_NOBACKGROUND 0x00400000
#endif

#ifndef TBCDRF_USECDCOLORS
#define TBCDRF_USECDCOLORS 0x00800000
#endif

namespace
{
void DrawRoundedToolbarState(
    LPNMTBCUSTOMDRAW aCustomDraw,
    COLORREF aFillColor)
{
    RECT sRect = aCustomDraw->nmcd.rc;
    const HWND sHwnd = aCustomDraw->nmcd.hdr.hwndFrom;
    const xpr_sint_t sInset =
        max(1, fxfile::ui::ModernUI::scaleForWindow(3, sHwnd));
    const xpr_sint_t sRadius =
        fxfile::ui::ModernUI::getControlCornerRadius(sHwnd);

    ::InflateRect(&sRect, -sInset, -sInset);
    if (sRect.right <= sRect.left || sRect.bottom <= sRect.top)
        return;

    HBRUSH sBrush = ::CreateSolidBrush(aFillColor);
    if (XPR_IS_NULL(sBrush))
        return;

    HGDIOBJ sOldBrush = ::SelectObject(aCustomDraw->nmcd.hdc, sBrush);
    HGDIOBJ sOldPen =
        ::SelectObject(aCustomDraw->nmcd.hdc, ::GetStockObject(NULL_PEN));
    ::RoundRect(
        aCustomDraw->nmcd.hdc,
        sRect.left,
        sRect.top,
        sRect.right,
        sRect.bottom,
        sRadius * 2,
        sRadius * 2);
    ::SelectObject(aCustomDraw->nmcd.hdc, sOldPen);
    ::SelectObject(aCustomDraw->nmcd.hdc, sOldBrush);
    ::DeleteObject(sBrush);
}

void DrawFinalDarkToolbarItem(
    LPNMTBCUSTOMDRAW aCustomDraw,
    COLORREF aBackground)
{
    if (XPR_IS_NULL(aCustomDraw))
        return;

    const HWND sHwnd = aCustomDraw->nmcd.hdr.hwndFrom;
    if (XPR_IS_NULL(sHwnd))
        return;

    const xpr_uint_t sCommandId =
        static_cast<xpr_uint_t>(aCustomDraw->nmcd.dwItemSpec);

    TBBUTTONINFO sButtonInfo = {0};
    sButtonInfo.cbSize = sizeof(sButtonInfo);
    sButtonInfo.dwMask = TBIF_IMAGE | TBIF_STATE | TBIF_STYLE;
    if (::SendMessage(
            sHwnd,
            TB_GETBUTTONINFO,
            static_cast<WPARAM>(sCommandId),
            reinterpret_cast<LPARAM>(&sButtonInfo)) < 0)
    {
        return;
    }

    const fxfile::ui::ThemePalette sPalette =
        fxfile::ui::ModernUI::getPalette();
    const UINT sItemState = aCustomDraw->nmcd.uItemState;
    const xpr_bool_t sDisabled =
        ((sItemState & CDIS_DISABLED) != 0 ||
         (sButtonInfo.fsState & TBSTATE_ENABLED) == 0) ?
        XPR_TRUE :
        XPR_FALSE;
    const xpr_bool_t sPressed =
        (sItemState & (CDIS_SELECTED | CDIS_CHECKED)) != 0 ?
        XPR_TRUE :
        XPR_FALSE;
    const xpr_bool_t sHot =
        (sItemState & CDIS_HOT) != 0 ?
        XPR_TRUE :
        XPR_FALSE;

    COLORREF sItemBackground = aBackground;
    if (XPR_IS_FALSE(sDisabled))
    {
        if (XPR_IS_TRUE(sPressed))
            sItemBackground = sPalette.mPressed;
        else if (XPR_IS_TRUE(sHot))
            sItemBackground = sPalette.mHover;
    }

    const COLORREF sForeground =
        XPR_IS_TRUE(sDisabled) ?
        sPalette.mSecondaryText :
        sPalette.mText;

    RECT sItemRect = aCustomDraw->nmcd.rc;
    const xpr_bool_t sDropDown =
        (sButtonInfo.fsStyle &
         (TBSTYLE_DROPDOWN | BTNS_WHOLEDROPDOWN)) != 0 ?
        XPR_TRUE :
        XPR_FALSE;

    const xpr_sint_t sDropWidth =
        fxfile::ui::ModernUI::scaleForWindow(14, sHwnd);

    if (XPR_IS_TRUE(sDropDown))
    {
        RECT sDropRect = sItemRect;
        sDropRect.left = max(
            sDropRect.left,
            sDropRect.right - sDropWidth);

        ::SetDCBrushColor(
            aCustomDraw->nmcd.hdc,
            sItemBackground);
        ::FillRect(
            aCustomDraw->nmcd.hdc,
            &sDropRect,
            static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

        if ((sButtonInfo.fsStyle & BTNS_WHOLEDROPDOWN) == 0)
        {
            RECT sSeparatorRect = sDropRect;
            sSeparatorRect.right =
                min(
                    sSeparatorRect.right,
                    sSeparatorRect.left +
                        max(
                            1,
                            fxfile::ui::ModernUI::scaleForWindow(
                                1,
                                sHwnd)));
            ::SetDCBrushColor(
                aCustomDraw->nmcd.hdc,
                sPalette.mSeparator);
            ::FillRect(
                aCustomDraw->nmcd.hdc,
                &sSeparatorRect,
                static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
        }

        const xpr_sint_t sCenterX =
            (sDropRect.left + sDropRect.right) / 2;
        const xpr_sint_t sCenterY =
            (sDropRect.top + sDropRect.bottom) / 2;
        const xpr_sint_t sHalfWidth =
            max(
                2,
                fxfile::ui::ModernUI::scaleForWindow(
                    3,
                    sHwnd));
        const xpr_sint_t sOffset =
            max(
                1,
                fxfile::ui::ModernUI::scaleForWindow(
                    2,
                    sHwnd));

        HPEN sArrowPen =
            ::CreatePen(
                PS_SOLID,
                max(
                    1,
                    fxfile::ui::ModernUI::scaleForWindow(
                        1,
                        sHwnd)),
                sForeground);
        if (XPR_IS_NOT_NULL(sArrowPen))
        {
            HGDIOBJ sOldPen =
                ::SelectObject(
                    aCustomDraw->nmcd.hdc,
                    sArrowPen);
            ::MoveToEx(
                aCustomDraw->nmcd.hdc,
                sCenterX - sHalfWidth,
                sCenterY - sOffset,
                XPR_NULL);
            ::LineTo(
                aCustomDraw->nmcd.hdc,
                sCenterX,
                sCenterY + sOffset);
            ::LineTo(
                aCustomDraw->nmcd.hdc,
                sCenterX + sHalfWidth,
                sCenterY - sOffset);
            ::SelectObject(
                aCustomDraw->nmcd.hdc,
                sOldPen);
            ::DeleteObject(sArrowPen);
        }
    }

    if ((sButtonInfo.fsStyle & BTNS_SHOWTEXT) == 0)
        return;

    xpr_tchar_t sText[512] = {0};
    const LRESULT sTextLength =
        ::SendMessage(
            sHwnd,
            TB_GETBUTTONTEXT,
            static_cast<WPARAM>(sCommandId),
            reinterpret_cast<LPARAM>(sText));
    if (sTextLength <= 0)
        return;

    RECT sTextRect = sItemRect;
    const xpr_sint_t sPadding =
        max(
            2,
            fxfile::ui::ModernUI::scaleForWindow(
                4,
                sHwnd));
    const DWORD sToolbarStyle =
        static_cast<DWORD>(
            ::GetWindowLongPtr(
                sHwnd,
                GWL_STYLE));
    xpr_sint_t sBitmapWidth = 0;
    xpr_sint_t sBitmapHeight = 0;
    HIMAGELIST sImageList =
        reinterpret_cast<HIMAGELIST>(
            ::SendMessage(
                sHwnd,
                TB_GETIMAGELIST,
                0,
                0));
    if (XPR_IS_NOT_NULL(sImageList))
    {
        xpr_sint_t sImageWidth = 0;
        xpr_sint_t sImageHeight = 0;
        if (::ImageList_GetIconSize(
                sImageList,
                &sImageWidth,
                &sImageHeight) != FALSE)
        {
            sBitmapWidth = sImageWidth;
            sBitmapHeight = sImageHeight;
        }
    }

    if ((sToolbarStyle & TBSTYLE_LIST) != 0)
    {
        if (sButtonInfo.iImage >= 0)
            sTextRect.left += sBitmapWidth + sPadding;
        else
            sTextRect.left += sPadding;

        sTextRect.right -=
            sPadding +
            (XPR_IS_TRUE(sDropDown) ?
                sDropWidth :
                0);
    }
    else
    {
        sTextRect.left += sPadding;
        sTextRect.right -=
            sPadding +
            (XPR_IS_TRUE(sDropDown) ?
                sDropWidth :
                0);

        if (sButtonInfo.iImage >= 0)
        {
            sTextRect.top =
                min(
                    sTextRect.bottom,
                    sTextRect.top +
                        sBitmapHeight +
                        max(
                            1,
                            fxfile::ui::ModernUI::scaleForWindow(
                                2,
                                sHwnd)));
        }
    }

    if (sTextRect.right <= sTextRect.left ||
        sTextRect.bottom <= sTextRect.top)
    {
        return;
    }

    // ToolbarWindow32 can still draw native black text even after custom-draw
    // colors are supplied.  Erase only the text region after native painting
    // and redraw it using the same UI font/palette as the rest of the app.
    ::SetDCBrushColor(
        aCustomDraw->nmcd.hdc,
        sItemBackground);
    ::FillRect(
        aCustomDraw->nmcd.hdc,
        &sTextRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    HFONT sFont =
        reinterpret_cast<HFONT>(
            ::SendMessage(
                sHwnd,
                WM_GETFONT,
                0,
                0));
    HGDIOBJ sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
    {
        sOldFont =
            ::SelectObject(
                aCustomDraw->nmcd.hdc,
                sFont);
    }

    const int sOldMode =
        ::SetBkMode(
            aCustomDraw->nmcd.hdc,
            TRANSPARENT);
    const COLORREF sOldTextColor =
        ::SetTextColor(
            aCustomDraw->nmcd.hdc,
            sForeground);

    UINT sTextFlags =
        DT_SINGLELINE |
        DT_VCENTER |
        DT_END_ELLIPSIS |
        DT_NOPREFIX;
    sTextFlags |=
        (sToolbarStyle & TBSTYLE_LIST) != 0 ?
        DT_LEFT :
        DT_CENTER;

    ::DrawText(
        aCustomDraw->nmcd.hdc,
        sText,
        -1,
        &sTextRect,
        sTextFlags);

    ::SetTextColor(
        aCustomDraw->nmcd.hdc,
        sOldTextColor);
    ::SetBkMode(
        aCustomDraw->nmcd.hdc,
        sOldMode);

    if (XPR_IS_NOT_NULL(sOldFont))
    {
        ::SelectObject(
            aCustomDraw->nmcd.hdc,
            sOldFont);
    }
}


// Own the *complete* final button in both Light and Dark. Previously Light
// repainted only the label, leaving a second clipped native icon/text baseline
// beneath the app-owned one (visible as colored and black short underlines
// in the bookmark toolbar). Native ToolbarWindow32 still owns commands,
// hit-testing, keyboard handling and accessibility, not the final pixels.
void DrawOwnedToolbarItem(
    LPNMTBCUSTOMDRAW aCustomDraw,
    COLORREF aBackground)
{
    if (XPR_IS_NULL(aCustomDraw))
        return;

    const HWND sToolbar = aCustomDraw->nmcd.hdr.hwndFrom;
    if (XPR_IS_NULL(sToolbar))
        return;

    TBBUTTONINFO sButton = {0};
    sButton.cbSize = sizeof(sButton);
    sButton.dwMask = TBIF_IMAGE | TBIF_STATE | TBIF_STYLE;
    if (::SendMessage(
            sToolbar,
            TB_GETBUTTONINFO,
            static_cast<WPARAM>(aCustomDraw->nmcd.dwItemSpec),
            reinterpret_cast<LPARAM>(&sButton)) < 0)
    {
        DrawFinalDarkToolbarItem(aCustomDraw, aBackground);
        return;
    }

    HIMAGELIST sImages = reinterpret_cast<HIMAGELIST>(
        ::SendMessage(sToolbar, TB_GETIMAGELIST, 0, 0));
    const xpr_bool_t sHasIcon =
        sButton.iImage >= 0 ? XPR_TRUE : XPR_FALSE;
    xpr_sint_t sIconWidth = 0;
    xpr_sint_t sIconHeight = 0;
    if (XPR_IS_TRUE(sHasIcon) &&
        (XPR_IS_NULL(sImages) ||
         sButton.iImage >= ::ImageList_GetImageCount(sImages) ||
         ::ImageList_GetIconSize(
             sImages, &sIconWidth, &sIconHeight) == FALSE))
    {
        // Preserve an unusual caller-owned icon rather than erase it.
        DrawFinalDarkToolbarItem(aCustomDraw, aBackground);
        return;
    }

    const fxfile::ui::ThemePalette sPalette =
        fxfile::ui::ModernUI::getPalette();
    const UINT sState = aCustomDraw->nmcd.uItemState;
    const xpr_bool_t sDisabled =
        ((sState & CDIS_DISABLED) != 0 ||
         (sButton.fsState & TBSTATE_ENABLED) == 0) ?
        XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sPressed =
        (sState & (CDIS_SELECTED | CDIS_CHECKED)) != 0 ?
        XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sHot =
        (sState & CDIS_HOT) != 0 ? XPR_TRUE : XPR_FALSE;
    const RECT sItemRect = aCustomDraw->nmcd.rc;

    // Native ToolbarWindow32 leaves its accent-blue/light tile under the
    // bitmap even though custom-draw foreground colors are correct.
    // Own the entire final item and redraw image, label and dropdown.
    ::SetDCBrushColor(aCustomDraw->nmcd.hdc, aBackground);
    ::FillRect(
        aCustomDraw->nmcd.hdc,
        &sItemRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
    if (XPR_IS_FALSE(sDisabled) &&
        (XPR_IS_TRUE(sPressed) || XPR_IS_TRUE(sHot)))
    {
        DrawRoundedToolbarState(
            aCustomDraw,
            XPR_IS_TRUE(sPressed) ?
                sPalette.mPressed : sPalette.mHover);
    }

    if (XPR_IS_TRUE(sHasIcon))
    {
        if (XPR_IS_TRUE(sDisabled))
        {
            HIMAGELIST sDisabledImages = reinterpret_cast<HIMAGELIST>(
                ::SendMessage(sToolbar, TB_GETDISABLEDIMAGELIST, 0, 0));
            if (XPR_IS_NOT_NULL(sDisabledImages) &&
                sButton.iImage < ::ImageList_GetImageCount(sDisabledImages))
                sImages = sDisabledImages;
        }

        const xpr_bool_t sDropDown =
            (sButton.fsStyle &
             (TBSTYLE_DROPDOWN | BTNS_WHOLEDROPDOWN)) != 0 ?
            XPR_TRUE : XPR_FALSE;
        const xpr_sint_t sDropWidth =
            XPR_IS_TRUE(sDropDown) ?
            fxfile::ui::ModernUI::scaleForWindow(14, sToolbar) : 0;
        const xpr_sint_t sPadding =
            max(2, fxfile::ui::ModernUI::scaleForWindow(4, sToolbar));
        const DWORD sStyle =
            static_cast<DWORD>(::GetWindowLongPtr(sToolbar, GWL_STYLE));
        const xpr_bool_t sHasText =
            (sButton.fsStyle & BTNS_SHOWTEXT) != 0 ?
            XPR_TRUE : XPR_FALSE;
        xpr_sint_t sImageX = sItemRect.left + sPadding;
        xpr_sint_t sImageY = sItemRect.top +
            (sItemRect.bottom - sItemRect.top - sIconHeight) / 2;
        if (XPR_IS_FALSE(sHasText) ||
            (sStyle & TBSTYLE_LIST) == 0)
        {
            sImageX = sItemRect.left +
                (sItemRect.right - sItemRect.left -
                 sDropWidth - sIconWidth) / 2;
            if (XPR_IS_TRUE(sHasText))
                sImageY = sItemRect.top + sPadding;
        }

        ::ImageList_DrawEx(
            sImages,
            sButton.iImage,
            aCustomDraw->nmcd.hdc,
            sImageX,
            sImageY,
            sIconWidth,
            sIconHeight,
            CLR_NONE,
            CLR_NONE,
            ILD_TRANSPARENT);
    }

    DrawFinalDarkToolbarItem(aCustomDraw, aBackground);
}

// The parent rebar may composite its children using WM_PRINT, bypassing the
// reflected NM_CUSTOMDRAW postpaint path entirely. A postpaint-only fix cannot
// remove a second native icon/text baseline in that composition path.
//
// The reported repeat occurs in the bookmark band. Keep the correction
// scoped to that band: it has one existing normal image list and native
// toolbar commands, but its final client pixels are app-owned. Other bands
// retain their current renderer until independently reproduced/tested.
bool CanPaintOwnedBookmarkToolbar(HWND aToolbar)
{
    if (::IsWindow(aToolbar) == FALSE ||
        ::GetDlgCtrlID(aToolbar) != AFX_IDW_BOOKMARK_BAR)
    {
        return false;
    }

    // Asynchronous icon loading must not switch the whole bookmark band
    // between native and app-owned full-surface paint. A transient missing
    // image is handled by the existing per-item renderer instead.
    return true;
}

void PaintOwnedBookmarkToolbar(HWND aToolbar, HDC aHdc)
{
    if (XPR_IS_NULL(aHdc))
        return;

    RECT sClientRect = {0};
    ::GetClientRect(aToolbar, &sClientRect);
    const int sDcState = ::SaveDC(aHdc);
    if (sDcState == 0)
        return;

    ::IntersectClipRect(
        aHdc,
        sClientRect.left, sClientRect.top,
        sClientRect.right, sClientRect.bottom);

    const fxfile::ui::ThemePalette sPalette =
        fxfile::ui::ModernUI::getPalette();
    ::SetDCBrushColor(aHdc, sPalette.mChrome);
    ::FillRect(
        aHdc, &sClientRect,
        static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

    const xpr_sint_t sHotItem = static_cast<xpr_sint_t>(
        ::SendMessage(aToolbar, TB_GETHOTITEM, 0, 0));
    const xpr_sint_t sCount = static_cast<xpr_sint_t>(
        ::SendMessage(aToolbar, TB_BUTTONCOUNT, 0, 0));
    const LRESULT sUiState =
        ::SendMessage(aToolbar, WM_QUERYUISTATE, 0, 0);

    // In nonwrapping mode, restrict both item eligibility and DC clipping
    // to the first native row. A clip alone can admit fragments from a
    // partially overlapping second-row item during layout transitions.
    const xpr_bool_t sSingleRow =
        (::GetWindowLongPtr(aToolbar, GWL_STYLE) & TBSTYLE_WRAPABLE) == 0 ?
        XPR_TRUE : XPR_FALSE;
    xpr_bool_t sHaveFirstRow = XPR_FALSE;
    xpr_sint_t sFirstRowTop = 0;
    if (XPR_IS_TRUE(sSingleRow))
    {
        for (xpr_sint_t i = 0; i < sCount; ++i)
        {
            TBBUTTON sButton = {0};
            RECT sFirstItem = {0};
            if (::SendMessage(
                    aToolbar, TB_GETBUTTON, i,
                    reinterpret_cast<LPARAM>(&sButton)) != FALSE &&
                (sButton.fsState & TBSTATE_HIDDEN) == 0 &&
                (sButton.fsStyle & BTNS_SEP) == 0 &&
                ::SendMessage(
                    aToolbar, TB_GETITEMRECT, i,
                    reinterpret_cast<LPARAM>(&sFirstItem)) != FALSE &&
                sFirstItem.bottom > sFirstItem.top)
            {
                sFirstRowTop = sFirstItem.top;
                sHaveFirstRow = XPR_TRUE;
                ::IntersectClipRect(
                    aHdc,
                    sClientRect.left,
                    sClientRect.top,
                    sClientRect.right,
                    min(sClientRect.bottom, sFirstItem.bottom));
                break;
            }
        }
    }

    for (xpr_sint_t i = 0; i < sCount; ++i)
    {
        TBBUTTON sButton = {0};
        RECT sItemRect = {0};
        if (::SendMessage(
                aToolbar, TB_GETBUTTON, i,
                reinterpret_cast<LPARAM>(&sButton)) == FALSE ||
            (sButton.fsState & TBSTATE_HIDDEN) != 0 ||
            ::SendMessage(
                aToolbar, TB_GETITEMRECT, i,
                reinterpret_cast<LPARAM>(&sItemRect)) == FALSE)
        {
            continue;
        }

        // Ignore every other native row, even if its rectangle overlaps
        // the clipping boundary by a few pixels.
        if (XPR_IS_TRUE(sSingleRow) &&
            (XPR_IS_FALSE(sHaveFirstRow) ||
             sItemRect.top != sFirstRowTop))
        {
            continue;
        }

        if ((sButton.fsStyle & BTNS_SEP) != 0)
        {
            const xpr_sint_t sMiddleX =
                (sItemRect.left + sItemRect.right) / 2;
            RECT sSeparator = {
                sMiddleX,
                sItemRect.top + fxfile::ui::ModernUI::scaleForWindow(8, aToolbar),
                sMiddleX + max(1, fxfile::ui::ModernUI::scaleForWindow(1, aToolbar)),
                sItemRect.bottom - fxfile::ui::ModernUI::scaleForWindow(8, aToolbar)
            };
            if (sSeparator.bottom > sSeparator.top)
            {
                ::SetDCBrushColor(aHdc, sPalette.mSeparator);
                ::FillRect(
                    aHdc, &sSeparator,
                    static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
            }
            continue;
        }

        NMTBCUSTOMDRAW sDraw = {0};
        sDraw.nmcd.hdr.hwndFrom = aToolbar;
        sDraw.nmcd.hdc = aHdc;
        sDraw.nmcd.dwItemSpec = sButton.idCommand;
        sDraw.nmcd.rc = sItemRect;
        if ((sButton.fsState & TBSTATE_ENABLED) == 0)
            sDraw.nmcd.uItemState |= CDIS_DISABLED;
        if ((sButton.fsState & TBSTATE_PRESSED) != 0)
            sDraw.nmcd.uItemState |= CDIS_SELECTED;
        if ((sButton.fsState & TBSTATE_CHECKED) != 0)
            sDraw.nmcd.uItemState |= CDIS_CHECKED;
        if (sHotItem == i)
            sDraw.nmcd.uItemState |= CDIS_HOT;

        DrawOwnedToolbarItem(&sDraw, sPalette.mChrome);

        // Native toolbar remains responsible for keyboard input/focus;
        // mirror its visible focus cue in this app-owned pixel route.
        if (::GetFocus() == aToolbar && sHotItem == i &&
            (sUiState & UISF_HIDEFOCUS) == 0)
        {
            ::DrawFocusRect(aHdc, &sItemRect);
        }
    }

    ::RestoreDC(aHdc, sDcState);
}

LRESULT ApplyDarkToolBarCustomDraw(
    LPNMTBCUSTOMDRAW aCustomDraw,
    xpr_bool_t aElevatedSurface = XPR_FALSE)
{
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast) || WinAppEx::GetInstance()->IsWinXP())
        return CDRF_DODEFAULT;

    const COLORREF sBackground =
        XPR_IS_TRUE(aElevatedSurface) ?
        sPalette.mElevated :
        sPalette.mChrome;

    switch (aCustomDraw->nmcd.dwDrawStage)
    {
        case CDDS_PREPAINT:
        {
            // ToolbarWindow32 is transparent in the rebar. Paint the complete
            // command surface ourselves so Light/Dark modes cannot leak the
            // legacy COLOR_BTNFACE/white rebar background around buttons.
            ::SetDCBrushColor(aCustomDraw->nmcd.hdc, sBackground);
            ::FillRect(
                aCustomDraw->nmcd.hdc,
                &aCustomDraw->nmcd.rc,
                static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));
            return CDRF_NOTIFYITEMDRAW;
        }

        case CDDS_ITEMPREPAINT:
        {
            const UINT sItemState = aCustomDraw->nmcd.uItemState;
            LRESULT sResult =
                CDRF_DODEFAULT |
                TBCDRF_NOEDGES |
                TBCDRF_NOOFFSET |
                TBCDRF_NOBACKGROUND |
                TBCDRF_USECDCOLORS;

            aCustomDraw->clrBtnFace = sBackground;
            aCustomDraw->clrText =
                (sItemState & CDIS_DISABLED) ?
                sPalette.mSecondaryText :
                sPalette.mText;
            aCustomDraw->clrTextHighlight = aCustomDraw->clrText;
            aCustomDraw->nStringBkMode = TRANSPARENT;
            aCustomDraw->nHLStringBkMode = TRANSPARENT;

            if (!(sItemState & CDIS_DISABLED) &&
                (sItemState & (CDIS_HOT | CDIS_SELECTED | CDIS_CHECKED)))
            {
                const xpr_bool_t sSelected =
                    (sItemState & (CDIS_SELECTED | CDIS_CHECKED)) != 0 ?
                    XPR_TRUE :
                    XPR_FALSE;

                const COLORREF sStateColor =
                    XPR_IS_TRUE(sSelected) ?
                    sPalette.mPressed :
                    sPalette.mHover;
                DrawRoundedToolbarState(aCustomDraw, sStateColor);
                aCustomDraw->clrHighlightHotTrack = sStateColor;
                aCustomDraw->clrText = sPalette.mText;
                aCustomDraw->clrTextHighlight = sPalette.mText;
            }

            // Native toolbar rendering is retained for image placement and
            // accessibility, but text/drop-down glyph pixels are finalized
            // after it paints so no black native text/arrow can leak onto a
            // dark command surface.
            return sResult | CDRF_NOTIFYPOSTPAINT;
        }

        case CDDS_ITEMPOSTPAINT:
        {
            // Light and Dark require identical final pixel ownership.
            // A text-only Light overlay leaves the native icon/text tail
            // un-erased when system toolbar metrics differ from our font.
            // High Contrast and legacy XP still take the native path above.
            DrawOwnedToolbarItem(aCustomDraw, sBackground);
            return CDRF_DODEFAULT;
        }

        default:
            return CDRF_DODEFAULT;
    }
}
} // namespace

CToolBarEx::CToolBarEx()
{
    m_pObserver = NULL;

    m_szLargeIcon = CSize(22,22);
    m_szSmallIcon = CSize(16,16);
    m_clrMask = RGB(255,0,255);

    m_nTextType = TBT_RIGHT;
    m_nIconType = TBI_SMALL;
    m_nTextTypeDefault = TBT_RIGHT;
    m_nIconTypeDefault = TBI_SMALL;

    m_nIDSmallCold = (UINT)-1;
    m_nIDSmallHot = (UINT)-1;
    m_nIDSmallDisabled = (UINT)-1;
    m_nIDLargeCold = (UINT)-1;
    m_nIDLargeHot = (UINT)-1;
    m_nIDLargeDisabled = (UINT)-1;
}

CToolBarEx::~CToolBarEx()
{
    if (m_uiFont.m_hObject != NULL)
        m_uiFont.DeleteObject();

    m_dqButtons.clear();
    m_mpButtons.clear();
}

void CToolBarEx::SetObserver(Observer *pObserver)
{
    m_pObserver = pObserver;
}

BOOL CToolBarEx::Create( CWnd* pParentWnd,
                         DWORD dwStyle,
                         UINT nID /*=AFX_IDW_TOOLBAR*/,
                         DWORD dwExtendedStyle /*= TBSTYLE_EX_DRAWDDARROWS | TBSTYLE_EX_HIDECLIPPEDBUTTONS*/ )
{
    dwStyle &= ~CBRS_TOOLTIPS;
    DWORD dwCtrlStyle = TBSTYLE_FLAT | TBSTYLE_TRANSPARENT | TBSTYLE_TOOLTIPS;
    if (!CreateEx(pParentWnd, dwCtrlStyle, dwStyle, CRect(0,0,0,0), nID))
        return FALSE;

    GetToolBarCtrl().SetExtendedStyle(dwExtendedStyle | TBSTYLE_EX_DOUBLEBUFFER);
    ApplyModernMetrics();
    ApplyModernAppearance();

    return TRUE;
}

/////////////////////////////////////////////////////////////////////////////
// Attributes

void CToolBarEx::SetTextType( int nTextType, bool bUpdate /*=true*/ )
{
    ASSERT( ::IsWindow( m_hWnd ) );
    ASSERT( GetStyle() & TBSTYLE_TOOLTIPS );
    ASSERT( !( GetBarStyle() & CBRS_TOOLTIPS ) );
    ASSERT( IsTextTypeAvailable( nTextType ) );

    m_nTextType = nTextType;

    // Modify toolbar style according to new text options
    ModifyStyle(
        ( nTextType == TBT_RIGHT ) ? 0 : TBSTYLE_LIST,
        ( nTextType == TBT_RIGHT ) ? TBSTYLE_LIST : 0 );

    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    DWORD dwStyleEx = tbCtrl.GetExtendedStyle();
    tbCtrl.SetExtendedStyle(
        ( nTextType == TBT_RIGHT ) ?
            ( dwStyleEx |  TBSTYLE_EX_MIXEDBUTTONS ) :
            ( dwStyleEx & ~TBSTYLE_EX_MIXEDBUTTONS ) );
    VERIFY( tbCtrl.SetMaxTextRows(
        ( nTextType == TBT_NONE ) ? 0 : 1 ) );

    if ( nTextType == TBT_TEXT )
    {
        VERIFY( tbCtrl.SetButtonWidth( 0, 76 ) );
    }

    // Modify all (even currently hidden ones) buttons in internal cache
	TBBUTTONEX *sTbButtonEx;
	ButtonDeque::iterator sIterator;

	sIterator = m_dqButtons.begin();
	for (; sIterator != m_dqButtons.end(); ++sIterator)
	{
		sTbButtonEx = *sIterator;

        if ( !( sTbButtonEx->tbinfo.fsStyle & TBSTYLE_SEP ) )
        {
            CString strButtonText;
            GetButtonTextByCommand( sTbButtonEx->tbinfo.idCommand, strButtonText );
            CString strToAdd( strButtonText, strButtonText.GetLength() + 1 );
            sTbButtonEx->tbinfo.iString = tbCtrl.AddStrings( strToAdd );

            switch ( nTextType )
            {
                case TBT_TEXT:
                    sTbButtonEx->tbinfo.fsStyle &= ~( TBSTYLE_AUTOSIZE | BTNS_SHOWTEXT );
                    break;

                case TBT_RIGHT:
                    sTbButtonEx->tbinfo.fsStyle |= ( TBSTYLE_AUTOSIZE |
                        ( HasButtonText( sTbButtonEx->tbinfo.idCommand ) ? BTNS_SHOWTEXT : 0 ) );
                    break;

                case TBT_NONE:
                    sTbButtonEx->tbinfo.fsStyle &= ~BTNS_SHOWTEXT;
                    sTbButtonEx->tbinfo.fsStyle |= TBSTYLE_AUTOSIZE;
                    break;
            }
        }
    }

    // If requested, reflect changes immediately
    if ( bUpdate )
    {
        ReloadButtons();
        UpdateToolbarSize();
    }
}

int CToolBarEx::GetTextType() const
{
    return m_nTextType;
}

void CToolBarEx::SetIconType( int nIconType, bool bUpdate /*=true*/ )
{
    ASSERT( ::IsWindow( m_hWnd ) );
    ASSERT( IsIconTypeAvailable( nIconType ) );

    m_nIconType = nIconType;

    // Set image list(s) and icon size for selected icon options
    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    tbCtrl.SetImageList( 0 );
    tbCtrl.SetHotImageList( 0 );
    tbCtrl.SetDisabledImageList( 0 );

    CSize szIcon = ( nIconType == TBI_SMALL ) ? m_szSmallIcon : m_szLargeIcon;
    VERIFY( tbCtrl.SetBitmapSize( szIcon ) );

    UINT nIDCold     = ( nIconType == TBI_SMALL ) ? m_nIDSmallCold     : m_nIDLargeCold;
    UINT nIDHot      = ( nIconType == TBI_SMALL ) ? m_nIDSmallHot      : m_nIDLargeHot;
    UINT nIDDisabled = ( nIconType == TBI_SMALL ) ? m_nIDSmallDisabled : m_nIDLargeDisabled;
    ASSERT( nIDCold != ( UINT )-1 );    // at least there must be "cold" imagelist

    LPCTSTR lpResName = MAKEINTRESOURCE( nIDCold );
    HINSTANCE hInst = AfxFindResourceHandle( lpResName, RT_BITMAP );

    m_imageListCold.DeleteImageList();
    VERIFY( m_imageListCold.Attach( ImageList_LoadImage( hInst, lpResName,
        szIcon.cx, 0, m_clrMask, IMAGE_BITMAP, LR_CREATEDIBSECTION ) ) );
    m_imageListCold.SetBkColor(CLR_NONE);
    tbCtrl.SetImageList( &m_imageListCold );

    if ( nIDHot != ( UINT )-1 ) // "hot" imagelist is optional
    {
        m_imageListHot.DeleteImageList();

        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        const xpr_bool_t sUseDarkHotCopy =
            XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast) &&
            XPR_IS_NOT_NULL(m_imageListCold.m_hImageList) ?
            XPR_TRUE :
            XPR_FALSE;

        if (XPR_IS_TRUE(sUseDarkHotCopy))
        {
            // Legacy HOT bitmap strips contain bright hover artwork intended
            // for classic/light toolbars.  On a Dark command bar this becomes
            // the white block seen behind icons.  Keep the icon source stable
            // and let ThemePalette custom draw provide the subtle hot surface.
            HIMAGELIST sHotImageList =
                ::ImageList_Duplicate(
                    m_imageListCold.m_hImageList);
            if (XPR_IS_NOT_NULL(sHotImageList))
                m_imageListHot.Attach(sHotImageList);
        }
        else
        {
            lpResName = MAKEINTRESOURCE( nIDHot );
            hInst = AfxFindResourceHandle( lpResName, RT_BITMAP );

            m_imageListHot.Attach(
                ImageList_LoadImage(
                    hInst,
                    lpResName,
                    szIcon.cx,
                    0,
                    m_clrMask,
                    IMAGE_BITMAP,
                    LR_CREATEDIBSECTION));
        }

        if (XPR_IS_NOT_NULL(m_imageListHot.m_hImageList))
        {
            m_imageListHot.SetBkColor(CLR_NONE);
            tbCtrl.SetHotImageList( &m_imageListHot );
        }
    }

    m_imageListDisabled.DeleteImageList();
    if ( nIDDisabled != ( UINT )-1 ) // "disabled" imagelist is optional
    {
        lpResName = MAKEINTRESOURCE( nIDDisabled );
        hInst = AfxFindResourceHandle( lpResName, RT_BITMAP );

        VERIFY( m_imageListDisabled.Attach( ImageList_LoadImage( hInst, lpResName,
            szIcon.cx, 0, m_clrMask, IMAGE_BITMAP, LR_CREATEDIBSECTION ) ) );
        m_imageListDisabled.SetBkColor(CLR_NONE);
        tbCtrl.SetDisabledImageList( &m_imageListDisabled );
    }
    else
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast) &&
            XPR_IS_NOT_NULL(m_imageListCold.m_hImageList))
        {
            HIMAGELIST sDisabledImageList =
                ::ImageList_Duplicate(m_imageListCold.m_hImageList);
            if (XPR_IS_NOT_NULL(sDisabledImageList))
            {
                m_imageListDisabled.Attach(sDisabledImageList);
                m_imageListDisabled.SetBkColor(CLR_NONE);
                tbCtrl.SetDisabledImageList(&m_imageListDisabled);
            }
        }
    }

    OnImageListsReloaded();

    // If requested, reflect changes immediately
    if ( bUpdate )
    {
        ReloadButtons();
        UpdateToolbarSize();
    }
}

int CToolBarEx::GetIconType() const
{
    return m_nIconType;
}

/////////////////////////////////////////////////////////////////////////////
// Operations

void CToolBarEx::SetIconSize(CSize szLargeIcon, CSize szSmallIcon)
{
    m_szLargeIcon = szLargeIcon;
    m_szSmallIcon = szSmallIcon;
}

void CToolBarEx::SetImageList(UINT nIDSmallDisabled, UINT nIDSmallCold, UINT nIDSmallHot,
                              UINT nIDLargeDisabled, UINT nIDLargeCold, UINT nIDLargeHot,
                              int nIconTypeDefault, COLORREF clrMask /*= RGB(255,0,255)*/)
{
    m_nIDSmallCold     = nIDSmallCold;
    m_nIDSmallHot      = nIDSmallHot;
    m_nIDSmallDisabled = nIDSmallDisabled;
    m_nIDLargeCold     = nIDLargeCold;
    m_nIDLargeHot      = nIDLargeHot;
    m_nIDLargeDisabled = nIDLargeDisabled;
    m_clrMask          = clrMask;

    m_nIconTypeDefault = nIconTypeDefault;    // to be used on reset
    SetIconType( m_nIconTypeDefault );        // apply new options
}

void CToolBarEx::GetImageList(CImageList *pImgList, BOOL bSmall/* = TRUE*/, int nImageType/* = TBG_HOT*/)
{
    UINT nID = bSmall ? m_nIDSmallHot : m_nIDLargeHot;
    CSize szIcon = bSmall ? m_szSmallIcon : m_szLargeIcon;

    HIMAGELIST hImageList;
    hImageList = ImageList_LoadImage(AfxGetResourceHandle(), MAKEINTRESOURCE(nID),
        szIcon.cx, 0, m_clrMask, IMAGE_BITMAP, LR_CREATEDIBSECTION);

    if (hImageList)
    {
        if (pImgList->m_hImageList)
            pImgList->DeleteImageList();

        pImgList->Attach(hImageList);
        pImgList->SetBkColor(CLR_NONE);
    }
}

void CToolBarEx::SetDefaultButtons()
{
    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    while (tbCtrl.DeleteButton(0));

    TBBUTTONEX *sTbButtonEx;
    ButtonDeque::iterator sIterator;

    sIterator = m_dqButtons.begin();
    for (; sIterator!=m_dqButtons.end(); ++sIterator)
    {
        sTbButtonEx = *sIterator;

        if (sTbButtonEx->bInitiallyVisible)
            tbCtrl.AddButtons(1, &sTbButtonEx->tbinfo);
    }

    SetTextType(TBT_RIGHT);
}

void CToolBarEx::SetButtons(int nCount, TBBUTTONEX* lpButtons)
{
    m_dqButtons.clear();
    m_mpButtons.clear();

    int i;
    for (i = 0; i < nCount; ++i)
    {
        m_dqButtons.push_back(&lpButtons[i]);
        m_mpButtons[lpButtons[i].tbinfo.idCommand] = &lpButtons[i];
    }
}

void CToolBarEx::LoadState( LPCTSTR lpszProfileName )
{
    CString strSubKey;
    strSubKey.Format( _T("Software\\%s\\%s\\%s"),
        AfxGetApp()->m_pszRegistryKey,
        AfxGetApp()->m_pszProfileName,
        lpszProfileName );

    GetToolBarCtrl().RestoreState( HKEY_CURRENT_USER,
        strSubKey, m_lpszStateInfoEntry );

// It was found out that TB_SAVERESTORE causes TBN_BEGINADJUST
// and TBN_ENDADJUST to be sent correspondingly at the beggining
// and the end of save/restore process.  So, the following
// call is redundant and therefore was commented out.

//    UpdateToolbarSize();
}

void CToolBarEx::SaveState( LPCTSTR lpszProfileName )
{
    CString strSubKey;
    strSubKey.Format( _T("Software\\%s\\%s\\%s"),
        AfxGetApp()->m_pszRegistryKey,
        AfxGetApp()->m_pszProfileName,
        lpszProfileName );

    m_hToolbarData = 0;
    GetToolBarCtrl().SaveState( HKEY_CURRENT_USER,
        strSubKey, m_lpszStateInfoEntry );
    if ( m_hToolbarData != 0 )
    {
        ::GlobalFree( m_hToolbarData );
    }
}

/////////////////////////////////////////////////////////////////////////////
// Overrides

LRESULT CToolBarEx::WindowProc( UINT message, WPARAM wParam, LPARAM lParam )
{
    // Keep non-paint messages on the original route. Bookmark renderer
    // eligibility is HWND-only, independent of asynchronous image state.
    const xpr_bool_t sPaintMessage =
        message == WM_PAINT ? XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sPrintClient =
        message == WM_PRINTCLIENT ||
        (message == WM_PRINT && (lParam & PRF_CLIENT) != 0) ?
        XPR_TRUE : XPR_FALSE;
    const xpr_bool_t sCandidate =
        XPR_IS_TRUE(sPaintMessage) || XPR_IS_TRUE(sPrintClient) ?
        XPR_TRUE : XPR_FALSE;

    xpr_bool_t sOwnBookmarkPixels = XPR_FALSE;
    if (XPR_IS_TRUE(sCandidate))
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_FALSE(sPalette.mHighContrast) &&
            !WinAppEx::GetInstance()->IsWinXP() &&
            CanPaintOwnedBookmarkToolbar(m_hWnd))
        {
            sOwnBookmarkPixels = XPR_TRUE;
        }
    }

    // WM_PRINT* is a separate rebar composition route, not a custom-draw
    // item notification. WM_PAINT also must not call native ToolbarWindow32
    // before the app renderer: the previous postpaint fix left two baselines.
    if (XPR_IS_TRUE(sOwnBookmarkPixels))
    {
        if (message == WM_PAINT)
        {
            if (wParam != 0)
            {
                PaintOwnedBookmarkToolbar(
                    m_hWnd, reinterpret_cast<HDC>(wParam));
            }
            else
            {
                CPaintDC sPaintDC(this);
                PaintOwnedBookmarkToolbar(
                    m_hWnd, sPaintDC.GetSafeHdc());
            }
            return 0;
        }

        if (XPR_IS_TRUE(sPrintClient) && wParam != 0)
        {
            if (message == WM_PRINT &&
                (lParam & PRF_CHECKVISIBLE) != 0 &&
                ::IsWindowVisible(m_hWnd) == FALSE)
            {
                return 0;
            }
            PaintOwnedBookmarkToolbar(
                m_hWnd, reinterpret_cast<HDC>(wParam));
            return 0;
        }
    }

    // Special handling for certain messages (forwarding to owner/parent)
    switch ( message )
    {
        case WM_WINDOWPOSCHANGING:
        case WM_WINDOWPOSCHANGED:
            {
                UpdateToolbarSize();
                break;
            }

        case WM_DPICHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
        case WM_THEMECHANGED:
            {
                ApplyModernMetrics();
                ApplyModernAppearance();

                const UINT sColdImageListId =
                    (m_nIconType == TBI_SMALL) ?
                    m_nIDSmallCold :
                    m_nIDLargeCold;
                if (sColdImageListId != (UINT)-1)
                    SetIconType(m_nIconType, false);

                UpdateToolbarSize();
                break;
            }
    }

    return CToolBar::WindowProc( message, wParam, lParam );
}

BOOL CToolBarEx::OnNotify( WPARAM wParam, LPARAM lParam, LRESULT* pResult )
{
    NMHDR* pNMHDR = ( NMHDR* )lParam;
    if ( ( pNMHDR->code == TTN_NEEDTEXTA ) ||
         ( pNMHDR->code == TTN_NEEDTEXTW ) )
    {
        // If button doesn't have a tip, ignore notification
        *pResult = HasButtonTip( (UINT)pNMHDR->idFrom ) ? Default() : 0;
        return TRUE;
    }

    return CToolBar::OnNotify( wParam, lParam, pResult );
}

//LRESULT CToolBarEx::DoCustomDraw( NMHDR* pNMHDR, CWnd* /*pToolBar*/ )
//{
//    LPNMTBCUSTOMDRAW lpNMCustomDraw = ( LPNMTBCUSTOMDRAW )pNMHDR;
//
//    switch ( lpNMCustomDraw->nmcd.dwDrawStage )
//    {
//        case CDDS_PREPAINT:
//            return CDRF_NOTIFYITEMDRAW;
//
//        case CDDS_ITEMPREPAINT:
//        {
//            UINT uItemState = lpNMCustomDraw->nmcd.uItemState;
//            if ( ( uItemState & CDIS_CHECKED ) && ( uItemState & CDIS_HOT ) )
//            {
//                // I personally don't like when background of checked item
//                // which is currently hot is drawn using dither brush
//                //lpNMCustomDraw->hbrMonoDither = 0;
//            }
//            // fall through...
//        }
//        default:
//            return CDRF_DODEFAULT;
//    }
//}

BOOL CToolBarEx::HasButtonText( UINT /*nID*/ )
{
    return TRUE;
}

BOOL CToolBarEx::HasButtonTip( UINT nID )
{
    switch ( m_nTextType )
    {
        case TBT_TEXT:
            return FALSE;
        case TBT_RIGHT:
            return !HasButtonText( nID );
        case TBT_NONE:
            return TRUE;
        default:
            ASSERT( FALSE );
            return FALSE;
    }
}

void CToolBarEx::GetButtonTextByCommand( UINT nID, CString& strText )
{
    CString strFull;
    VERIFY( strFull.LoadString( nID ) );
    VERIFY( AfxExtractSubString( strText, strFull, 1, _T('\n') ) );
}

void CToolBarEx::GetButtonTip( UINT nID, CString& strTip )
{
    GetButtonTextByCommand( nID, strTip );
}

void CToolBarEx::Init()
{
    ASSERT( false );    // must be overridden
}

bool CToolBarEx::IsTextTypeAvailable( int /*nTextType*/ ) const
{
    return true;
}

bool CToolBarEx::IsIconTypeAvailable( int /*nIconType*/ ) const
{
    return true;
}

/////////////////////////////////////////////////////////////////////////////
// Implementation

void CToolBarEx::OnImageListsReloaded()
{
}

void CToolBarEx::ReloadButtons()
{
    // Reload buttons from internal cache
    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    for ( int nIndex = 0, nButtons = tbCtrl.GetButtonCount(); nIndex < nButtons; nIndex++ )
    {
        TBBUTTON tbinfo;
        VERIFY( tbCtrl.GetButton( 0, &tbinfo ) );
        VERIFY( GetButtonInfo( tbinfo.idCommand, tbinfo ) );
        VERIFY( tbCtrl.DeleteButton( 0 ) );
        VERIFY( tbCtrl.AddButtons( 1, &tbinfo ) );
    }
}

void CToolBarEx::ApplyModernMetrics()
{
    if (!::IsWindow(m_hWnd))
        return;

    // Keep the bitmap strip and command mapping intact, but let every toolbar
    // share the same Windows 11 command metrics. Text/list buttons still use
    // their native autosize width; the default button extent only establishes
    // a comfortable minimum hit target.
    const int sHorizontalPadding =
        fxfile::ui::ModernUI::getCommandHorizontalPadding(m_hWnd);
    const int sVerticalPadding =
        fxfile::ui::ModernUI::getCommandVerticalPadding(m_hWnd);
    const int sButtonExtent =
        fxfile::ui::ModernUI::getCommandButtonExtent(m_hWnd);

    CToolBarCtrl &sToolBarCtrl = GetToolBarCtrl();
    sToolBarCtrl.SendMessage(
        TB_SETPADDING,
        0,
        MAKELPARAM(sHorizontalPadding, sVerticalPadding));

    const DWORD sCurrentButtonSize =
        static_cast<DWORD>(sToolBarCtrl.SendMessage(TB_GETBUTTONSIZE, 0, 0));
    const int sCurrentButtonWidth = LOWORD(sCurrentButtonSize);
    sToolBarCtrl.SendMessage(
        TB_SETBUTTONSIZE,
        0,
        MAKELPARAM(max(sCurrentButtonWidth, sButtonExtent), sButtonExtent));

    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(
            fxfile::ui::ModernUI::getUIFont(
                sLogFont,
                m_hWnd)) &&
        XPR_IS_FALSE(
            fxfile::ui::ModernUI::isSameFont(
                reinterpret_cast<HFONT>(
                    m_uiFont.GetSafeHandle()),
                sLogFont)))
    {
        if (m_uiFont.m_hObject != NULL)
            m_uiFont.DeleteObject();

        if (m_uiFont.CreateFontIndirect(&sLogFont))
            SetFont(&m_uiFont, FALSE);
    }
}

void CToolBarEx::ApplyModernAppearance()
{
    if (!::IsWindow(m_hWnd))
        return;

    if (!WinAppEx::GetInstance()->IsWinXP())
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast))
        {
            fxfile::ui::ModernUI::resetControlTheme(m_hWnd);
        }
        else
        {
            fxfile::ui::ModernUI::applyExplorerControlTheme(m_hWnd);
        }
    }

    CToolTipCtrl* sToolTip = GetToolBarCtrl().GetToolTips();
    if (sToolTip != NULL && ::IsWindow(sToolTip->m_hWnd))
        fxfile::ui::ModernUI::applyExplorerControlTheme(sToolTip->m_hWnd);

    Invalidate(FALSE);
}

void CToolBarEx::UpdateToolbarSize()
{
    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    tbCtrl.AutoSize();

    if (m_pObserver != NULL)
        m_pObserver->onUpdatedToolbarSize(*this);

    Invalidate();   // visual feedback
}

BOOL CToolBarEx::GetButtonInfo( UINT nID, TBBUTTON& tbinfo )
{
    if ( tbinfo.fsStyle & TBSTYLE_SEP )
    {
        return TRUE;
    }

    ButtonMap::iterator sIterator = m_mpButtons.find(nID);
    if (sIterator == m_mpButtons.end())
        return FALSE;

    tbinfo = sIterator->second->tbinfo;

    return TRUE;
}

/////////////////////////////////////////////////////////////////////////
// CToolBarEx message handlers

BEGIN_MESSAGE_MAP(CToolBarEx, CToolBar)
    //{{AFX_MSG_MAP(CToolBarEx)
    //}}AFX_MSG_MAP

    ON_MESSAGE( WM_REBAR_CHEVRONPUSHED, OnReBarChevronPushed )

    ON_NOTIFY_REFLECT( NM_CUSTOMDRAW, OnCustomDraw )
    ON_NOTIFY_REFLECT( TBN_GETINFOTIP, OnGetInfoTip )

    // Toolbar customization
    ON_NOTIFY_REFLECT( TBN_BEGINADJUST, OnBeginAdjust )
    ON_NOTIFY_REFLECT( TBN_ENDADJUST, OnEndAdjust )
    ON_NOTIFY_REFLECT( TBN_QUERYINSERT, OnQueryInsert )
    ON_NOTIFY_REFLECT( TBN_QUERYDELETE, OnQueryDelete )
    ON_NOTIFY_REFLECT( TBN_INITCUSTOMIZE, OnInitCustomize )
    ON_NOTIFY_REFLECT( TBN_GETBUTTONINFO, OnGetButtonInfo )
    ON_NOTIFY_REFLECT( TBN_RESET, OnReset )
    ON_NOTIFY_REFLECT( TBN_TOOLBARCHANGE, OnToolBarChange )

    // Saving and restoring toolbar
    ON_NOTIFY_REFLECT( TBN_SAVE, OnSave )
    ON_NOTIFY_REFLECT( TBN_RESTORE, OnRestore )
END_MESSAGE_MAP()

void CToolBarEx::Customize()
{
    GetToolBarCtrl().Customize();
}

LRESULT CToolBarEx::OnReBarChevronPushed( WPARAM wParam, LPARAM /*lParam*/ )
{
    CRect rcChevron( ( LPCRECT )wParam );

    CToolBarPopup menu( this );
    menu.ShowPopup( TPM_LEFTALIGN | TPM_VERTICAL |
            (WinAppEx::GetInstance()->IsWin50() ? TPM_VERPOSANIMATION : 0 ),
        CPoint( rcChevron.left, rcChevron.bottom ), rcChevron );

    return 0L;
}

void CToolBarEx::OnCustomDraw( NMHDR* pNMHDR, LRESULT* pResult )
{
    LPNMTBCUSTOMDRAW sCustomDraw = reinterpret_cast<LPNMTBCUSTOMDRAW>(pNMHDR);
    *pResult = ApplyDarkToolBarCustomDraw(sCustomDraw);
}

void CToolBarEx::OnGetInfoTip( NMHDR* pNMHDR, LRESULT* pResult )
{
    NMTBGETINFOTIP* lptbgit = ( NMTBGETINFOTIP* )pNMHDR;
    CString strTip;
    GetButtonTip( lptbgit->iItem, strTip );
    _tcsncpy( lptbgit->pszText, strTip, lptbgit->cchTextMax );

    *pResult = 0;
}

LRESULT CALLBACK CToolBarEx::CBTProc( int nCode, WPARAM wParam, LPARAM lParam )
{
    ASSERT( m_pToolBar != 0 );
    HWND hWnd = ( HWND )wParam;

    switch ( nCode )
    {
        case HCBT_CREATEWND:
            if ( m_pCustomizeDlg == 0 )
            {
                // This is where we have a good chance to subclass standard
                // "Customize toolbar" dialog in order to add to it some of
                // our new features (ie. text and icon options selectors)
                TCHAR szClassName[ 7 ];
                ::GetClassName( hWnd, szClassName, sizeof( szClassName ) / sizeof( szClassName[ 0 ] ) );
                if ( !lstrcmp( _T("#32770"), szClassName ) )
                {
                    m_pCustomizeDlg = new CCustomizeDialog( m_pToolBar );
                    VERIFY( m_pCustomizeDlg->SubclassWindow( hWnd ) );
                    return 0;
                }
            }
            break;

        case HCBT_DESTROYWND:
            if ( ( m_pCustomizeDlg != 0 ) && ( m_pCustomizeDlg->m_hWnd == hWnd ) )
            {
                m_pCustomizeDlg = 0;
                return 0;
            }
            break;
    }

    return ::CallNextHookEx( m_hCBTHook, nCode, wParam, lParam );
}

void CToolBarEx::OnBeginAdjust( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    m_pToolBar = this;
    m_hCBTHook = ::SetWindowsHookEx( WH_CBT, CBTProc, 0, ::GetCurrentThreadId() );
    ASSERT( m_hCBTHook != 0 );

    *pResult = 0;
}

void CToolBarEx::OnEndAdjust( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    VERIFY( ::UnhookWindowsHookEx( m_hCBTHook ) );
    m_hCBTHook = 0;
    m_pToolBar = 0;

    ReloadButtons();
    UpdateToolbarSize();

    *pResult = 0;
}

void CToolBarEx::OnQueryInsert( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    *pResult = TRUE;    // otherwise Customize dialog will not be shown
}

void CToolBarEx::OnQueryDelete( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    *pResult = TRUE;    // why not? :)
}

void CToolBarEx::OnInitCustomize( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    *pResult = TBNRF_HIDEHELP;      // no help available yet
}

void CToolBarEx::OnGetButtonInfo( NMHDR* pNMHDR, LRESULT* pResult )
{
    NMTOOLBAR* lpnmtb = ( NMTOOLBAR* )pNMHDR;
    *pResult = FALSE;

    int nItem = lpnmtb->iItem;
    if (!FXFILE_STL_IS_INDEXABLE(nItem, m_dqButtons))
        return;

    lpnmtb->tbButton = m_dqButtons[nItem]->tbinfo;
    if (!XPR_TEST_BITS(lpnmtb->tbButton.fsStyle, TBSTYLE_SEP))
    {
        CString strText;
        ButtonMap::iterator sIterator;

        sIterator = m_mpButtons.find(lpnmtb->tbButton.idCommand);
        if (sIterator != m_mpButtons.end())
            strText.LoadString((UINT)sIterator->second->tbinfo.iString);

        _tcscpy(lpnmtb->pszText, strText);
    }

    *pResult = TRUE;
}

void CToolBarEx::OnReset( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    // Delete all buttons
    CToolBarCtrl& tbCtrl = GetToolBarCtrl();
    while ( tbCtrl.DeleteButton( 0 ) );

    // Load buttons from internal cache
    TBBUTTONEX *sTbButtonEx;
    ButtonDeque::iterator sIterator;

    sIterator = m_dqButtons.begin();
    for (; sIterator != m_dqButtons.end(); ++sIterator)
    {
        sTbButtonEx = *sIterator;

        if (XPR_IS_TRUE(sTbButtonEx->bInitiallyVisible))
            tbCtrl.AddButtons(1, &sTbButtonEx->tbinfo);
    }

    // Set default text & icon options
    SetIconType( m_nIconTypeDefault, false );
    SetTextType( m_nTextTypeDefault, false );
    ReloadButtons();
    UpdateToolbarSize();

    // Synchronize with Customize dialog
    ASSERT( m_pCustomizeDlg != 0 );
    m_pCustomizeDlg->SetTextType( m_nIconTypeDefault, true );
    m_pCustomizeDlg->SetIconType( m_nTextTypeDefault, true );

    *pResult = 0;
}

void CToolBarEx::OnToolBarChange( NMHDR* /*pNMHDR*/, LRESULT* pResult )
{
    UpdateToolbarSize();

    *pResult = 0;
}

void CToolBarEx::OnSave( NMHDR* pNMHDR, LRESULT* pResult )
{
    NMTBSAVE* lpnmtb = ( NMTBSAVE* )pNMHDR;
    if ( lpnmtb->iItem == -1 )
    {
        lpnmtb->cbData += sizeof( DWORD ) * 2;

        m_hToolbarData = ::GlobalAlloc( GMEM_FIXED, lpnmtb->cbData );
        ASSERT( m_hToolbarData != 0 );

        lpnmtb->pData    = ( LPDWORD )m_hToolbarData;
        lpnmtb->pCurrent = lpnmtb->pData;

        *lpnmtb->pCurrent++ = ( DWORD )m_nTextType;
        *lpnmtb->pCurrent++ = ( DWORD )m_nIconType;
    }

    *pResult = 0;
}

void CToolBarEx::OnRestore( NMHDR* pNMHDR, LRESULT* pResult )
{
    NMTBRESTORE* lpnmtb = ( NMTBRESTORE* )pNMHDR;
    if ( lpnmtb->iItem == -1 )
    {
        lpnmtb->cButtons = ( lpnmtb->cbData - sizeof( DWORD ) * 2 ) / lpnmtb->cbBytesPerRecord;
        lpnmtb->pCurrent = lpnmtb->pData;

        SetTextType( ( int )*lpnmtb->pCurrent++, false );
        SetIconType( ( int )*lpnmtb->pCurrent++, false );

        if ( lpnmtb->cButtons == 0 )
        {
            ReloadButtons();
            UpdateToolbarSize();

            *pResult = 1;
            return;
        }
    }
    else
    {
        VERIFY( GetButtonInfo( lpnmtb->tbButton.idCommand, lpnmtb->tbButton ) );
    }

    *pResult = 0;
}

/////////////////////////////////////////////////////////////////////////////
// CToolBarPopup

HHOOK           CToolBarPopup::m_hKeyboardHook  = 0;
CToolBarPopup*  CToolBarPopup::m_pPopup         = 0;

IMPLEMENT_DYNAMIC( CToolBarPopup, CWnd )

CToolBarPopup::CToolBarPopup( CToolBarEx* pToolBar )
{
    ASSERT_VALID( pToolBar );

    m_pToolBar    = pToolBar;
    m_bOverTbCtrl = false;
    m_bTextLabels = false;

    WinAppEx* pApp = WinAppEx::GetInstance();
    // Keep the exact XP behavior, but use the flat palette-owned shell on
    // current Windows where a WS_DLGFRAME popup reads as legacy chrome.
    m_bFlatMenu = pApp->IsWinXP() ? pApp->GetFlatMenu() : true;
}

CToolBarPopup::~CToolBarPopup()
{
}

/////////////////////////////////////////////////////////////////////////////
// Operations

bool CToolBarPopup::ShowPopup( UINT nFlags, CPoint pt, CRect& rcExclude )
{
    WinAppEx* pApp = WinAppEx::GetInstance();
    const bool sLegacyPopup = pApp->IsWinXP();
    const HBRUSH sClassBrush =
        sLegacyPopup ?
        (HBRUSH)(COLOR_MENU + 1) :
        (HBRUSH)::GetStockObject(NULL_BRUSH);
    CString strWndClass = AfxRegisterWndClass(
        CS_SAVEBITS | (sLegacyPopup ? CS_DROPSHADOW : 0),
        ::LoadCursor(0, IDC_ARROW),
        sClassBrush,
        0);

    const DWORD sExStyle =
        sLegacyPopup ?
        (m_bFlatMenu ?
            (WS_EX_TOOLWINDOW | WS_EX_TOPMOST) :
            WS_EX_PALETTEWINDOW) :
        (WS_EX_TOOLWINDOW | WS_EX_TOPMOST);
    const DWORD sPopupFrameStyle =
        sLegacyPopup ?
        (m_bFlatMenu ?
            WS_BORDER :
            (WS_DLGFRAME | WS_CLIPCHILDREN)) :
        WS_CLIPCHILDREN;

    if ( !CreateEx(
            sExStyle,
            strWndClass,
            0,
            WS_POPUP | WS_CLIPSIBLINGS | WS_OVERLAPPED | sPopupFrameStyle,
            CRect( 0, 0, 0, 0 ), 0, 0 ) )
    {
        return false;
    }

    SetPosition( nFlags, pt, rcExclude );

    if (!sLegacyPopup)
    {
        fxfile::ui::ModernUI::applyRoundedWindowRegion(
            m_hWnd,
            fxfile::ui::ModernUI::getPopupCornerRadius(m_hWnd));
    }

    SetCapture();
    SendMessage( WM_SETCURSOR, ( WPARAM )m_hWnd, MAKELPARAM( HTCLIENT, 0 ) );

    m_pPopup = this;
    m_hKeyboardHook = ::SetWindowsHookEx( WH_KEYBOARD, KeyboardProc, 0, ::GetCurrentThreadId() );
    ASSERT( m_hKeyboardHook != 0 );

    // Emulate menu loop
    RunModalLoop( MLF_NOKICKIDLE );

    VERIFY( ::UnhookWindowsHookEx( m_hKeyboardHook ) );
    m_hKeyboardHook = 0;
    m_pPopup = 0;

    DestroyWindow();

    return true;
}

/////////////////////////////////////////////////////////////////////////////
// Implementation

void CToolBarPopup::SetPosition( UINT nFlags, CPoint pt, CRect& rcExclude )
{
    // The main purpose of this functions is to find proper position of
    // the popup window, so that we neither exceed screen dimensions nor
    // intersect rcExclude rectangle.  The function also takes into account
    // control flags specified by the user.

    // Calc initial position
    CRect rc;
    m_tbCtrl.GetWindowRect( rc );

    CalcWindowRect( rc, CWnd::adjustBorder );

    const fxfile::ui::ThemePalette sPalette =
        fxfile::ui::ModernUI::getPalette();
    if (!WinAppEx::GetInstance()->IsWinXP() &&
        XPR_IS_FALSE(sPalette.mHighContrast))
    {
        const int sBorderThickness =
            fxfile::ui::ModernUI::getPopupBorderThickness(m_hWnd);
        rc.InflateRect(sBorderThickness, sBorderThickness);
    }

    rc.OffsetRect( -rc.TopLeft() );
    rc.OffsetRect(
        ( nFlags & TPM_CENTERALIGN ) ? ( pt.x - rc.Width() / 2 ) :
        ( nFlags & TPM_RIGHTALIGN  ) ? ( pt.x - rc.Width() ) : pt.x, 0 );
    rc.OffsetRect( 0,
        ( nFlags & TPM_VCENTERALIGN ) ? ( pt.y - rc.Height() / 2 ) :
        ( nFlags & TPM_BOTTOMALIGN  ) ? ( pt.y - rc.Height() ) : pt.y );

    // Keep the app-owned chevron popup inside the *anchor monitor's work
    // area*, not the virtual desktop (which includes taskbars and other
    // monitors). The legacy desktop bounds remain a safe fallback.
    CRect rcDesktop;
    GetDesktopWindow()->GetWindowRect(rcDesktop);

    MONITORINFO sMonitorInfo = {0};
    sMonitorInfo.cbSize = sizeof(sMonitorInfo);
    HMONITOR sMonitor = ::MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
    if (sMonitor != NULL &&
        ::GetMonitorInfo(sMonitor, &sMonitorInfo) != FALSE)
    {
        rcDesktop.SetRect(
            sMonitorInfo.rcWork.left,
            sMonitorInfo.rcWork.top,
            sMonitorInfo.rcWork.right,
            sMonitorInfo.rcWork.bottom);
    }

    rc.OffsetRect(
        min( rcDesktop.right  - rc.right,  0 ),
        min( rcDesktop.bottom - rc.bottom, 0 ) );
    rc.OffsetRect(
        max( rcDesktop.left   - rc.left,   0 ),
        max( rcDesktop.top    - rc.top,    0 ) );

    // Make sure we don't intersect rcExclude rectangle
    CRect rcTemp;
    if ( !rcExclude.IsRectEmpty() && rcTemp.IntersectRect( rc, rcExclude ) )
    {
        if ( nFlags & TPM_VERTICAL )
        {
            CRect rcUp( rc );
            int nUp = rc.bottom - rcExclude.top;
            rcUp.OffsetRect( 0, -nUp );

            CRect rcDown( rc );
            int nDown = rcExclude.bottom - rc.top;
            rcDown.OffsetRect( 0, nDown );

            bool bUp = false;
            if ( ( rcUp.top >= rcDesktop.top ) && ( rcDown.bottom <= rcDesktop.bottom ) )
            {
                bUp = ( nUp < nDown );
            }
            else if ( rcUp.top >= rcDesktop.top )
            {
                bUp = true;
            }
            else if ( rcDown.bottom <= rcDesktop.bottom )
            {
                bUp = false;
            }
            else
            {
                ASSERT( false );    // this case is not supported yet
            }

            rc = bUp ? rcUp : rcDown;
            nFlags &= ~( TPM_HORPOSANIMATION | TPM_HORNEGANIMATION | TPM_VERPOSANIMATION | TPM_VERNEGANIMATION );
            nFlags |=  ( bUp ? TPM_VERNEGANIMATION : TPM_VERPOSANIMATION );
        }
        else
        {
            CRect rcLeft( rc );
            int nLeft = rc.right - rcExclude.left;
            rcLeft.OffsetRect( -nLeft, 0 );

            CRect rcRight( rc );
            int nRight = rcExclude.right - rc.left;
            rcRight.OffsetRect( nRight, 0 );

            bool bLeft = false;
            if ( ( rcLeft.left >= rcDesktop.left ) && ( rcRight.right <= rcDesktop.right ) )
            {
                bLeft = ( nLeft < nRight );
            }
            else if ( rcLeft.left >= rcDesktop.left )
            {
                bLeft = true;
            }
            else if ( rcRight.right <= rcDesktop.right )
            {
                bLeft = false;
            }
            else
            {
                ASSERT( false );    // this case is not supported yet
            }

            rc = bLeft ? rcLeft : rcRight;
            nFlags &= ~( TPM_HORPOSANIMATION | TPM_HORNEGANIMATION | TPM_VERPOSANIMATION | TPM_VERNEGANIMATION );
            nFlags |=  ( bLeft ? TPM_HORNEGANIMATION : TPM_HORPOSANIMATION );
        }
    }

    Show( nFlags, rc );
}

void CToolBarPopup::Show( UINT nFlags, const CRect& rc )
{
    // On W98/W2K systems the menu animation feature is supported.
    // This function tries to mimic this feature conformably to
    // toolbar popup window.

    // Position window on the screen
    SetWindowPos( &wndTopMost, rc.left, rc.top, rc.Width(), rc.Height(),
        SWP_NOACTIVATE );

    WinAppEx* pApp = WinAppEx::GetInstance();
    if ( pApp->IsWin50() && !( nFlags & TPM_NOANIMATION ) ) // W98/W2K specific (menu animation)
    {
        if ( pApp->GetMenuAnimation() )
        {
            DWORD dwAnimationFlags = AW_SLIDE |
                ( ( nFlags & TPM_HORPOSANIMATION ) ? AW_HOR_POSITIVE : 0 ) |
                ( ( nFlags & TPM_HORNEGANIMATION ) ? AW_HOR_NEGATIVE : 0 ) |
                ( ( nFlags & TPM_VERPOSANIMATION ) ? AW_VER_POSITIVE : 0 ) |
                ( ( nFlags & TPM_VERNEGANIMATION ) ? AW_VER_NEGATIVE : 0 );
            if ( dwAnimationFlags == AW_SLIDE )
            {
                // If none of TPM_*ANIMATION flags is set, set default animation
                dwAnimationFlags |= AW_HOR_POSITIVE | AW_VER_POSITIVE;
            }

            if ( pApp->IsWin2K() && pApp->GetMenuFade() )   // W2K specific (fade effect)
            {
                dwAnimationFlags = AW_BLEND;
            }

            VERIFY( ::AnimateWindowWin50( m_hWnd, 200, dwAnimationFlags ) );
            return;
        }
    }

    // The animation feature is whether turned off or unsupported
    // on this system.  Therefore, just show window without activation.
    ShowWindow( SW_SHOWNOACTIVATE );
}

void CToolBarPopup::OnKeyDown( UINT nChar )
{
    switch ( nChar )
    {
        case VK_ESCAPE: // dismiss menu
        case VK_MENU:
            SendMessage( WM_TB_ENDMODALLOOP );
            break;

        case VK_UP:     // select next/prev button
        case VK_DOWN:
        {
            int nLastItem = m_tbCtrl.GetButtonCount() - 1;
            int nHotItem  = m_tbCtrl.GetHotItem();

            for ( int nIndex = 0; nIndex <= nLastItem; nIndex++ )
            {
                if ( nHotItem >= 0 )
                {
                    nHotItem = ( nChar == VK_UP ) ?
                        ( nHotItem ? nHotItem - 1 : nLastItem ) :
                        ( nHotItem == nLastItem ? 0 : nHotItem + 1 );
                }
                else
                {
                    nHotItem = ( nChar == VK_UP ) ?
                        nLastItem : 0;
                }

                m_tbCtrl.SetHotItem( nHotItem );
                if ( m_tbCtrl.GetHotItem() == nHotItem )
                {
                    break;
                }
            }
            break;
        }
        case VK_RETURN: // issue command associated with selected button
        {
            int nHotItem = m_tbCtrl.GetHotItem();
            if ( nHotItem >= 0 )
            {
                TBBUTTON tbinfo;
                VERIFY( m_tbCtrl.GetButton( nHotItem, &tbinfo ) );
                if ( tbinfo.idCommand != 0 )
                {
                    SendMessage( WM_COMMAND, tbinfo.idCommand );
                    break;
                }
            }

            SendMessage( WM_TB_ENDMODALLOOP );
            break;
        }
        default:
            break;
    }
}

LRESULT CALLBACK CToolBarPopup::KeyboardProc( int code, WPARAM wParam, LPARAM lParam )
{
    ASSERT( m_pPopup != 0 );

    if ( code == HC_ACTION )
    {
        CWnd* pCapture = GetCapture();
        if ( ( pCapture == m_pPopup ) ||
             ( pCapture == &m_pPopup->m_tbCtrl ) )
        {
            if ( !( HIWORD( lParam ) & KF_UP ) )
            {
                m_pPopup->OnKeyDown( (UINT)wParam );
            }

            return 1;
        }
    }

    return ::CallNextHookEx( m_hKeyboardHook, code, wParam, lParam );
}

void CToolBarPopup::DrawBorder( CDC* pDC )
{
    CRect rcWindow;
    GetWindowRect( rcWindow );
    CRect rcClient;
    GetClientRect( rcClient );
    ClientToScreen( rcClient );
    rcClient.OffsetRect( -rcWindow.TopLeft() );
    rcWindow.OffsetRect( -rcWindow.TopLeft() );
    pDC->ExcludeClipRect( rcClient );
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    pDC->FillSolidRect(
        rcWindow,
        XPR_IS_TRUE(sPalette.mHighContrast) ?
            ::GetSysColor(COLOR_3DSHADOW) :
            sPalette.mBorder );
}

/////////////////////////////////////////////////////////////////////////////
// Overrides

BOOL CToolBarPopup::OnCommand( WPARAM wParam, LPARAM /*lParam*/ )
{
    // Dismiss menu
    SendMessage( WM_TB_ENDMODALLOOP );

    // Forward command to the original toolbar window
    m_pToolBar->PostMessage( WM_COMMAND, LOWORD( wParam ), 0 );

    return TRUE;    // command was processed
}

BOOL CToolBarPopup::OnNotify( WPARAM wParam, LPARAM lParam, LRESULT* pResult )
{
    NMHDR* pNMHDR = ( NMHDR* )lParam;
    if ( pNMHDR->hwndFrom == m_tbCtrl.m_hWnd )
    {
        // Handle certain notifications from embedded toolbar control
        switch ( pNMHDR->code )
        {
            case NM_RELEASEDCAPTURE:
                SetCapture();
                *pResult = 0;
                break;

            case NM_CUSTOMDRAW:
            {
                LPNMTBCUSTOMDRAW lpNMCustomDraw = ( LPNMTBCUSTOMDRAW )pNMHDR;
                const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();

                WinAppEx* pApp = WinAppEx::GetInstance();
                if ( XPR_IS_FALSE(sPalette.mHighContrast) && !pApp->IsWinXP() )
                {
                    *pResult = ApplyDarkToolBarCustomDraw(lpNMCustomDraw, XPR_TRUE);
                }
                else
                {
                    if ( pApp->IsWinXP() )
                    {
                        *pResult = CDRF_DODEFAULT;  // by default

                        switch ( lpNMCustomDraw->nmcd.dwDrawStage )
                        {
                            case CDDS_PREPAINT:
                                *pResult = CDRF_NOTIFYITEMDRAW;
                                break;

                            case CDDS_ITEMPREPAINT:
                            {
                                *pResult |= TBCDRF_NOEDGES | TBCDRF_NOOFFSET;
                                UINT uItemState = lpNMCustomDraw->nmcd.uItemState;
                                if ( !( uItemState & CDIS_DISABLED ) && ( uItemState & ( CDIS_HOT | CDIS_SELECTED ) ) )
                                {
                                    lpNMCustomDraw->clrHighlightHotTrack = ::GetSysColor( pApp->GetFlatMenu() ? COLOR_MENUHILIGHT : COLOR_HIGHLIGHT );
                                    lpNMCustomDraw->clrText = ::GetSysColor( COLOR_HIGHLIGHTTEXT );
                                    *pResult |= TBCDRF_HILITEHOTTRACK;
                                }
                                else
                                {
                                    if ( uItemState & CDIS_DISABLED )
                                    {
                                        lpNMCustomDraw->clrText = ::GetSysColor( COLOR_GRAYTEXT );
                                    }
                                    else if ( uItemState & CDIS_CHECKED )
                                    {
                                        lpNMCustomDraw->clrText = ::GetSysColor( COLOR_HIGHLIGHTTEXT );
                                        lpNMCustomDraw->clrBtnFace = ::GetSysColor( pApp->GetFlatMenu() ? COLOR_MENUHILIGHT : COLOR_HIGHLIGHT );
                                    }
                                    else
                                    {
                                        lpNMCustomDraw->clrText = ::GetSysColor( COLOR_MENUTEXT );
                                    }
                                }
                                break;
                            }
                        }
                    }
                }
                break;
            }
            case TBN_GETINFOTIP:
                if ( !m_bTextLabels )
                {
                    NMTBGETINFOTIP* lptbgit = ( NMTBGETINFOTIP* )pNMHDR;
                    CString strTip;
                    m_pToolBar->GetButtonTip( lptbgit->iItem, strTip );
                    _tcsncpy( lptbgit->pszText, strTip, lptbgit->cchTextMax );
                }
                *pResult = 0;
                break;

            default:    // forward message to the parent of the original toolbar
                *pResult = m_pToolBar->GetParent()->SendMessage( WM_NOTIFY, wParam, lParam );
                break;
        }

        return TRUE;
    }

    return CWnd::OnNotify( wParam, lParam, pResult );
}

LRESULT CToolBarPopup::WindowProc( UINT message, WPARAM wParam, LPARAM lParam )
{
    if ( WM_MOUSEFIRST <= message && message <= WM_MOUSELAST )
    {
        DWORD dwPos = ::GetMessagePos();
        CPoint ptScreen( LOWORD( dwPos ), HIWORD( dwPos ) );
        CWnd* pWnd = WindowFromPoint( ptScreen );
        if ( pWnd != 0 )
        {
            CPoint ptClient( ptScreen );
            pWnd->ScreenToClient( &ptClient );

            switch ( message )
            {
                case WM_MOUSEMOVE:
                {
                    // Check if hot item should be changed
                    bool bOverTbCtrl = ( pWnd == &m_tbCtrl );
                    if ( bOverTbCtrl )
                    {
                        int nHit = m_tbCtrl.HitTest( &ptClient );
                        m_tbCtrl.SetHotItem( nHit );

                        // Let tooltip control process mouse event
                        CToolTipCtrl* pTtCtrl = m_tbCtrl.GetToolTips();
                        if ( pTtCtrl != 0 )
                        {
                            MSG msg;
                            msg.hwnd    = m_tbCtrl.m_hWnd;
                            msg.message = WM_MOUSEMOVE;
                            msg.wParam  = wParam;
                            msg.lParam  = MAKELPARAM( ptClient.x, ptClient.y );
                            msg.pt      = ptScreen;
                            msg.time    = ::GetMessageTime();
                            pTtCtrl->RelayEvent( &msg );
                        }
                    }
                    else if ( m_bOverTbCtrl )
                    {
                        m_tbCtrl.SetHotItem( -1 );
                    }

                    m_bOverTbCtrl = bOverTbCtrl;
                    return 0L;
                }
                case WM_LBUTTONDOWN:
                    if ( pWnd != this )
                    {
                        // Dismiss menu if user has clicked outside the window
                        if ( pWnd != &m_tbCtrl )
                        {
                            SendMessage( WM_TB_ENDMODALLOOP );
                        }

                        // Forward this mouse event to the window that was clicked
                        LPARAM nPosition = MAKELPARAM( ptScreen.x, ptScreen.y );
                        WPARAM nHitTest  = pWnd->SendMessage( WM_NCHITTEST, 0, nPosition );
                        if ( nHitTest == HTCLIENT )
                        {
                            nPosition = MAKELPARAM( ptClient.x, ptClient.y );
                            pWnd->PostMessage( WM_LBUTTONDOWN, wParam, nPosition );
                        }
                        else
                        {
                            pWnd->PostMessage( WM_NCLBUTTONDOWN, nHitTest, nPosition );
                        }
                    }
                    return 0L;

                default:
                    break;
            }
        }
    }

    return CWnd::WindowProc( message, wParam, lParam );
}

/////////////////////////////////////////////////////////////////////////
// CToolBarPopup message handlers

BEGIN_MESSAGE_MAP(CToolBarPopup, CWnd)
    //{{AFX_MSG_MAP(CToolBarPopup)
    ON_WM_CAPTURECHANGED()
    ON_WM_CREATE()
    ON_WM_ERASEBKGND()
    ON_WM_MOUSEACTIVATE()
    ON_WM_NCPAINT()
    //}}AFX_MSG_MAP
    ON_MESSAGE( WM_PRINT, OnPrint )
    ON_MESSAGE_VOID( WM_TB_ENDMODALLOOP, OnEndModalLoop )
END_MESSAGE_MAP()

void CToolBarPopup::OnCaptureChanged( CWnd* pWnd )
{
    if ( ( pWnd != this ) && ( pWnd != &m_tbCtrl ) && ContinueModal() )
    {
        PostMessage( WM_TB_ENDMODALLOOP );  // dismiss menu
    }

    CWnd::OnCaptureChanged( pWnd );
}

int CToolBarPopup::OnCreate( LPCREATESTRUCT lpCreateStruct )
{
    if ( CWnd::OnCreate( lpCreateStruct ) == -1 )
    {
        return -1;
    }

    // Create embedded toolbar control
    if ( !m_tbCtrl.Create(
            TBSTYLE_FLAT | TBSTYLE_WRAPABLE | TBSTYLE_LIST | TBSTYLE_TOOLTIPS |
            CCS_NODIVIDER | CCS_NOPARENTALIGN | CCS_NORESIZE |
            WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN,
            CRect( 0, 0, 0, 0 ), this, m_pToolBar->GetDlgCtrlID() ) )
    {
        return -1;
    }

    m_tbCtrl.SetExtendedStyle( TBSTYLE_EX_DRAWDDARROWS | TBSTYLE_EX_MIXEDBUTTONS );
    VERIFY( m_tbCtrl.GetToolTips()->ModifyStyle( 0, TTS_ALWAYSTIP ) );

    if (WinAppEx::GetInstance()->IsWinXP() )
    {
        HRESULT hr = ::SetWindowThemeXP( m_tbCtrl.m_hWnd, L"", L"" );
        ASSERT( SUCCEEDED( hr ) );
    }
    else
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast))
        {
            fxfile::ui::ModernUI::resetControlTheme(
                m_tbCtrl.m_hWnd);
        }
        else
        {
            fxfile::ui::ModernUI::applyExplorerControlTheme(
                m_tbCtrl.m_hWnd);
        }

        CToolTipCtrl* sToolTip = m_tbCtrl.GetToolTips();
        if (sToolTip != NULL && ::IsWindow(sToolTip->m_hWnd))
            fxfile::ui::ModernUI::applyExplorerControlTheme(sToolTip->m_hWnd);

        const int sPopupPadding =
            fxfile::ui::ModernUI::getPopupItemPadding(m_hWnd);
        const int sPopupItemHeight =
            fxfile::ui::ModernUI::getPopupItemHeight(m_hWnd);

        m_tbCtrl.SendMessage(
            TB_SETPADDING,
            0,
            MAKELPARAM(sPopupPadding, max(1, sPopupPadding / 2)));

        const DWORD sCurrentButtonSize =
            static_cast<DWORD>(m_tbCtrl.SendMessage(TB_GETBUTTONSIZE, 0, 0));
        m_tbCtrl.SendMessage(
            TB_SETBUTTONSIZE,
            0,
            MAKELPARAM(
                LOWORD(sCurrentButtonSize),
                max((int)HIWORD(sCurrentButtonSize), sPopupItemHeight)));

        CFont *sSourceFont = m_pToolBar->GetFont();
        if (sSourceFont != NULL && sSourceFont->m_hObject != NULL)
            m_tbCtrl.SetFont(sSourceFont, FALSE);
    }

    // There could be only two modes, depending on text options
    // of the original toolbar: with or without text labels.
    int nTextType = m_pToolBar->GetTextType();
    m_bTextLabels =
        ( nTextType == TBT_TEXT ) ||
        ( nTextType == TBT_RIGHT );

    // Copy all required information from the original toolbar
    CToolBarCtrl& tbCtrl = m_pToolBar->GetToolBarCtrl();
    m_tbCtrl.SetImageList( tbCtrl.GetImageList() );
    m_tbCtrl.SetHotImageList( tbCtrl.GetHotImageList() );
    m_tbCtrl.SetDisabledImageList( tbCtrl.GetDisabledImageList() );

    CRect rcItem, rcClient;
    tbCtrl.GetClientRect( rcClient );

    TBBUTTON tbinfo;
    int nMaxWidth = 0;
    int nButtons = tbCtrl.GetButtonCount();
    int nIndex;
    for ( nIndex = 0; nIndex < nButtons; nIndex++ )
    {
        tbCtrl.GetItemRect( nIndex, rcItem );
        if ( rcItem.right > rcClient.right )
        {
            VERIFY( tbCtrl.GetButton( nIndex, &tbinfo ) );
            if ( !( tbinfo.fsStyle & TBSTYLE_SEP ) && !( tbinfo.fsState & TBSTATE_HIDDEN ) )
            {
                CString strButtonText;
                m_pToolBar->GetButtonTextByCommand( tbinfo.idCommand, strButtonText );
                CString strToAdd( strButtonText, strButtonText.GetLength() + 1 );
                tbinfo.iString  = m_tbCtrl.AddStrings( strToAdd );
                tbinfo.fsStyle |= TBSTYLE_AUTOSIZE | ( m_bTextLabels ? BTNS_SHOWTEXT : 0 );
                VERIFY( m_tbCtrl.AddButtons( 1, &tbinfo ) );
                VERIFY( m_tbCtrl.GetItemRect( m_tbCtrl.CommandToIndex( tbinfo.idCommand ), rcItem ) );
                nMaxWidth = max( nMaxWidth, rcItem.Width() );
            }
        }
    }

    nButtons = m_tbCtrl.GetButtonCount();
    if ( nButtons == 0 )
    {
        ASSERT( false );    // this should never happen
        return -1;
    }

    if ( m_bTextLabels )
    {
        TBBUTTONINFO tbbi;
        tbbi.cbSize = sizeof( tbbi );
        tbbi.dwMask = TBIF_SIZE | TBIF_STYLE;
        for ( nIndex = 0; nIndex < nButtons; nIndex++ )
        {
            VERIFY( m_tbCtrl.GetButton( nIndex, &tbinfo ) );
            tbbi.cx      = ( WORD )nMaxWidth;
            tbbi.fsStyle = ( BYTE )( tbinfo.fsStyle & ~TBSTYLE_AUTOSIZE );
            VERIFY( m_tbCtrl.SetButtonInfo( tbinfo.idCommand, &tbbi ) );
        }
    }

    m_tbCtrl.AutoSize();

    // Calc toolbar size
    if ( nButtons > 1 )
    {
        m_tbCtrl.SetRows( nButtons, m_bTextLabels, rcClient );
    }
    else
    {
        VERIFY( m_tbCtrl.GetItemRect( 0, rcClient ) );
    }

    if (!WinAppEx::GetInstance()->IsWinXP())
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_FALSE(sPalette.mHighContrast))
        {
            const int sBorderThickness =
                fxfile::ui::ModernUI::getPopupBorderThickness(m_hWnd);
            rcClient.OffsetRect(sBorderThickness, sBorderThickness);
        }
    }

    m_tbCtrl.MoveWindow( rcClient );

    return 0;
}

BOOL CToolBarPopup::OnEraseBkgnd(CDC *pDC)
{
    if (pDC == NULL)
        return CWnd::OnEraseBkgnd(pDC);

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast))
        return CWnd::OnEraseBkgnd(pDC);

    CRect sClientRect;
    GetClientRect(&sClientRect);
    pDC->FillSolidRect(&sClientRect, sPalette.mElevated);

    const int sBorderThickness =
        fxfile::ui::ModernUI::getPopupBorderThickness(m_hWnd);
    CBrush sBorderBrush(sPalette.mBorder);
    for (int i = 0; i < sBorderThickness && !sClientRect.IsRectEmpty(); ++i)
    {
        pDC->FrameRect(&sClientRect, &sBorderBrush);
        sClientRect.DeflateRect(1, 1);
    }

    return TRUE;
}

int CToolBarPopup::OnMouseActivate( CWnd* /*pDesktopWnd*/, UINT /*nHitTest*/, UINT /*message*/ )
{
    return MA_NOACTIVATEANDEAT; // just in case
}

void CToolBarPopup::OnNcPaint()
{
    if ( m_bFlatMenu )
    {
        CWindowDC dc(this);
        DrawBorder(&dc);
        // CWindowDC owns this HDC and releases it at scope exit.
    }
    else
    {
        CWnd::OnNcPaint();
    }
}

LRESULT CToolBarPopup::OnPrint( WPARAM wParam, LPARAM lParam )
{
    LRESULT lResult = DefWindowProc( WM_PRINT, wParam, lParam );

    if ( m_bFlatMenu && ( lParam & PRF_NONCLIENT ) )
    {
        CDC* pDC = CDC::FromHandle( ( HDC )wParam );
        int nSavedDC = pDC->SaveDC();
        DrawBorder( pDC );
        pDC->RestoreDC( nSavedDC );
    }

    return lResult;
}

void CToolBarPopup::OnEndModalLoop()
{
    EndModalLoop( 0 );
}
