//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "FlatHeaderCtrl.h"

#include "MemDC.h"
#include "ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

#define ARROW_HEIGHT 6

FlatHeaderCtrl::FlatHeaderCtrl(void)
    : mCallDrawItem(XPR_FALSE)
    , mSortColumn(-1)
    , mBoldFont(XPR_FALSE)
    , mOffset(6)
    , mParentWnd(XPR_NULL)
    , mDragging(XPR_FALSE)
    , mTracking(XPR_FALSE)
    , mMouseHover(XPR_FALSE)
    , mMouseHoverColumn(-1)
{
}

FlatHeaderCtrl::~FlatHeaderCtrl(void)
{
}

BEGIN_MESSAGE_MAP(FlatHeaderCtrl, CHeaderCtrl)
    ON_WM_PAINT()
    ON_WM_CREATE()
    ON_WM_WINDOWPOSCHANGED()
    ON_WM_MOUSEMOVE()
    ON_WM_SETTINGCHANGE()
    ON_MESSAGE(WM_DPICHANGED,   OnDpiChanged)
    ON_MESSAGE(WM_MOUSEHOVER,   OnMouseHover)
    ON_MESSAGE(WM_MOUSELEAVE,   OnMouseLeave)
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_NOTIFY_REFLECT(HDN_BEGINDRAG, OnHdnBegindrag)
    ON_NOTIFY_REFLECT(HDN_ENDDRAG,   OnHdnEnddrag)
END_MESSAGE_MAP()

void FlatHeaderCtrl::initHeader(xpr_bool_t aBoldFont)
{
    if (XPR_IS_NOT_NULL(mFont.m_hObject))
        mFont.DeleteObject();

    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(fxfile::ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())))
    {
        if (XPR_IS_TRUE(aBoldFont))
            sLogFont.lfWeight = FW_SEMIBOLD;

        mFont.CreateFontIndirect(&sLogFont);
        if (XPR_IS_NOT_NULL(mFont.m_hObject))
            SetFont(&mFont);
    }

    mOffset =
        fxfile::ui::ModernUI::getListHeaderTextPadding(GetSafeHwnd());
    mBoldFont = aBoldFont;
}

xpr_sint_t FlatHeaderCtrl::OnCreate(LPCREATESTRUCT aCreateStruct)
{
    if (CHeaderCtrl::OnCreate(aCreateStruct) == -1)
        return -1;

    mParentWnd = CWnd::FromHandle(aCreateStruct->hwndParent);
    ASSERT(mParentWnd);

    resizeWindow();

    return 0;
}

void FlatHeaderCtrl::PreSubclassWindow(void)
{
    CHeaderCtrl::PreSubclassWindow();

    mParentWnd = GetParent();
    ASSERT(mParentWnd);

    resizeWindow();
}

xpr_sint_t FlatHeaderCtrl::setSortImage(xpr_sint_t aColumn, xpr_bool_t aAscending)
{
    xpr_sint_t aOldSortColumn = mSortColumn;

    mSortColumn = aColumn;
    mSortAscending = aAscending;

    HD_ITEM sHdItem = {0};
    sHdItem.mask = HDI_BITMAP | HDI_FORMAT;

    xpr_sint_t i;
    xpr_sint_t sCount = GetItemCount();

    for (i = 0; i < sCount; ++i)
    {
        GetItem(i, &sHdItem);

        sHdItem.fmt |= HDF_OWNERDRAW;
        SetItem(i, &sHdItem);
    }

    Invalidate();

    return aOldSortColumn;
}

void FlatHeaderCtrl::DrawItem(LPDRAWITEMSTRUCT aDrawItemStruct)
{
    mCallDrawItem = XPR_TRUE;

    ASSERT(aDrawItemStruct != XPR_NULL);

    CDC        *sDC       = CDC::FromHandle(aDrawItemStruct->hDC);
    CRect       sItemRect = aDrawItemStruct->rcItem;
    xpr_uint_t  sState    = aDrawItemStruct->itemState;
    xpr_sint_t  sIndex    = aDrawItemStruct->itemID;

    if (XPR_IS_TRUE(mMouseHover))
    {
        if (sIndex == mMouseHoverColumn)
            sState |= ODS_HOTLIGHT;
    }

    drawItem(sDC, sItemRect, sState, sIndex);
}

void FlatHeaderCtrl::drawItem(CDC *aDC, CRect aItemRect, xpr_uint_t aState, xpr_sint_t aIndex)
{
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    const xpr_uint_t sDpi = fxfile::ui::ModernUI::getDpi(GetSafeHwnd());
    const xpr_sint_t sArrowHeight = max(4, fxfile::ui::ModernUI::scale(ARROW_HEIGHT, sDpi));
    const xpr_sint_t sSeparatorWidth = max(1, fxfile::ui::ModernUI::scale(1, sDpi));

    const xpr_sint_t sSavedDC = aDC->SaveDC();

    HD_ITEM sHdItem = {0};
    xpr_tchar_t sText[XPR_MAX_PATH + 1] = {0};

    sHdItem.mask       = HDI_TEXT | HDI_FORMAT;
    sHdItem.pszText    = sText;
    sHdItem.cchTextMax = XPR_MAX_PATH;
    GetItem(aIndex, &sHdItem);

    COLORREF sBackColor = sPalette.mSurface;
    if (XPR_TEST_BITS(aState, ODS_HOTLIGHT))
        sBackColor = sPalette.mHover;
    if (XPR_TEST_BITS(aState, ODS_SELECTED))
        sBackColor = XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mSelection : sPalette.mHover;

    aDC->FillSolidRect(aItemRect, sBackColor);
    aDC->SetBkMode(TRANSPARENT);
    aDC->SetTextColor(
        XPR_IS_TRUE(sPalette.mHighContrast) && XPR_TEST_BITS(aState, ODS_SELECTED) ?
            sPalette.mSelectionText : sPalette.mText);

    CRect sSeparatorRect(aItemRect);
    sSeparatorRect.left = max(sSeparatorRect.left, sSeparatorRect.right - sSeparatorWidth);
    aDC->FillSolidRect(sSeparatorRect, sPalette.mSeparator);

    CRect sTextArea(aItemRect);
    if (aIndex == mSortColumn)
        sTextArea.right -= 3 * mOffset;

    sTextArea.left  += mOffset;
    sTextArea.right -= mOffset;

    xpr_uint_t sFormat = DT_SINGLELINE | DT_NOPREFIX | DT_VCENTER | DT_END_ELLIPSIS;
    if (sHdItem.fmt & HDF_CENTER)     sFormat |= DT_CENTER;
    else if (sHdItem.fmt & HDF_RIGHT) sFormat |= DT_RIGHT;
    else                              sFormat |= DT_LEFT;

    CFont *sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(mFont.m_hObject))
        sOldFont = aDC->SelectObject(&mFont);

    CRect sTextRect(0,0,0,0);
    if (sTextArea.left < sTextArea.right)
    {
        aDC->DrawText(sText, -1, &sTextRect, DT_SINGLELINE | DT_CALCRECT);
        aDC->DrawText(sText, -1, sTextArea, sFormat);
    }

    if (aIndex == mSortColumn)
    {
        const xpr_sint_t sCenterX = aItemRect.right - (mOffset * 2);
        const xpr_sint_t sCenterY = aItemRect.top + aItemRect.Height() / 2;
        const xpr_sint_t sHalfWidth = max(3, sArrowHeight / 2);

        POINT sPoints[3];
        if (XPR_IS_TRUE(mSortAscending))
        {
            sPoints[0].x = sCenterX;              sPoints[0].y = sCenterY - sArrowHeight / 2;
            sPoints[1].x = sCenterX - sHalfWidth; sPoints[1].y = sCenterY + sArrowHeight / 2;
            sPoints[2].x = sCenterX + sHalfWidth; sPoints[2].y = sCenterY + sArrowHeight / 2;
        }
        else
        {
            sPoints[0].x = sCenterX - sHalfWidth; sPoints[0].y = sCenterY - sArrowHeight / 2;
            sPoints[1].x = sCenterX + sHalfWidth; sPoints[1].y = sCenterY - sArrowHeight / 2;
            sPoints[2].x = sCenterX;              sPoints[2].y = sCenterY + sArrowHeight / 2;
        }

        CBrush sArrowBrush(sPalette.mSecondaryText);
        CRgn sArrowRgn;
        sArrowRgn.CreatePolygonRgn(sPoints, 3, ALTERNATE);
        aDC->FillRgn(&sArrowRgn, &sArrowBrush);
    }

    if (XPR_IS_NOT_NULL(sOldFont))
        aDC->SelectObject(sOldFont);

    aDC->RestoreDC(sSavedDC);
}

void FlatHeaderCtrl::OnPaint(void)
{
    CPaintDC sPaintDC(this);
    MemDC sMemDC(&sPaintDC);

    CRect sClientRect;
    GetClientRect(&sClientRect);

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    sMemDC.FillSolidRect(sClientRect, sPalette.mSurface);

    mCallDrawItem = XPR_FALSE;
    CWnd::DefWindowProc(WM_PAINT, (WPARAM)sMemDC.m_hDC, 0);
    drawFlatBorder(&sMemDC);
}

void FlatHeaderCtrl::drawFlatBorder(CDC *aDC)
{
    CRect sClientRect;
    GetClientRect(&sClientRect);

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    const xpr_sint_t sSeparatorHeight =
        max(1, fxfile::ui::ModernUI::scaleForWindow(1, GetSafeHwnd()));

    xpr_sint_t sTotalWidth = 0;
    const xpr_sint_t sCount = GetItemCount();

    if (XPR_IS_FALSE(mCallDrawItem))
    {
        CFont *sOldFont = XPR_NULL;
        if (XPR_IS_NOT_NULL(mFont.m_hObject))
            sOldFont = aDC->SelectObject(&mFont);

        for (xpr_sint_t i = 0; i < sCount; ++i)
        {
            CRect sItemRect;
            if (GetItemRect(i, &sItemRect) == XPR_TRUE)
            {
                drawItem(aDC, sItemRect, 0, i);
                sTotalWidth = max(sTotalWidth, sItemRect.right);
            }
        }

        if (XPR_IS_NOT_NULL(sOldFont))
            aDC->SelectObject(sOldFont);
    }
    else
    {
        for (xpr_sint_t i = 0; i < sCount; ++i)
        {
            CRect sItemRect;
            if (GetItemRect(i, &sItemRect) == XPR_TRUE)
                sTotalWidth = max(sTotalWidth, sItemRect.right);
        }
    }

    if (sTotalWidth < sClientRect.right)
    {
        CRect sFillRect(sClientRect);
        sFillRect.left = max(sClientRect.left, sTotalWidth);
        aDC->FillSolidRect(sFillRect, sPalette.mSurface);
    }

    CRect sBottomRect(sClientRect);
    sBottomRect.top = max(sBottomRect.top, sBottomRect.bottom - sSeparatorHeight);
    aDC->FillSolidRect(sBottomRect, sPalette.mSeparator);
}

void FlatHeaderCtrl::OnWindowPosChanged(WINDOWPOS FAR *aWindowPos)
{
    CHeaderCtrl::OnWindowPosChanged(aWindowPos);

    Invalidate(XPR_FALSE);
}

void FlatHeaderCtrl::resizeWindow(void)
{
    ASSERT_VALID(this);
    ASSERT_VALID(mParentWnd);

    CRect sParentRect;
    mParentWnd->GetClientRect(&sParentRect);

    CRect sWindowRect;
    GetWindowRect(&sWindowRect);

    SetWindowPos(XPR_NULL, 0, 0, sParentRect.Width(), sWindowRect.Height(), SWP_NOMOVE|SWP_FRAMECHANGED);
}

xpr_bool_t FlatHeaderCtrl::OnEraseBkgnd(CDC *aDC)
{
    return CHeaderCtrl::OnEraseBkgnd(aDC);
}

void FlatHeaderCtrl::OnMouseMove(xpr_uint_t aFlags, CPoint aPoint)
{
    if (XPR_IS_FALSE(mDragging))
    {
        if (aFlags == MK_LBUTTON)
            Invalidate(XPR_FALSE);

        if (XPR_IS_FALSE(mTracking))
        {
            TRACKMOUSEEVENT sTrackMouseEvent = {0};
            sTrackMouseEvent.cbSize      = sizeof(sTrackMouseEvent);
            sTrackMouseEvent.hwndTrack   = m_hWnd;
            sTrackMouseEvent.dwFlags     = TME_HOVER | TME_LEAVE;
            sTrackMouseEvent.dwHoverTime = 1;

            mTracking = _TrackMouseEvent(&sTrackMouseEvent) != XPR_FALSE;
        }

        if (XPR_IS_TRUE(mTracking))
        {
            xpr_sint_t sOldMouseHoverColumn = mMouseHoverColumn;
            mMouseHoverColumn = -1;

            xpr_sint_t i, sCount;
            CRect sItemRect;

            sCount = GetItemCount();
            for (i = 0; i < sCount; ++i)
            {
                GetItemRect(i, &sItemRect);
                if (sItemRect.PtInRect(aPoint) == XPR_TRUE)
                {
                    mMouseHoverColumn = i;
                    break;
                }
            }

            if (sOldMouseHoverColumn != mMouseHoverColumn)
                Invalidate(XPR_FALSE);
        }
    }

    CHeaderCtrl::OnMouseMove(aFlags, aPoint);
}

LRESULT FlatHeaderCtrl::OnMouseHover(WPARAM wParam, LPARAM lParam)
{
    CPoint sPoint(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));

    mMouseHover = XPR_TRUE;
    Invalidate();

    return 1;
}

LRESULT FlatHeaderCtrl::OnMouseLeave(WPARAM wParam, LPARAM lParam)
{
    CPoint sPoint(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));

    mTracking         = XPR_FALSE;
    mMouseHover       = XPR_FALSE;
    mMouseHoverColumn = -1;
    Invalidate(XPR_FALSE);

    return 0;
}

void FlatHeaderCtrl::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    CHeaderCtrl::OnSettingChange(aFlags, aSection);
    initHeader(mBoldFont);
    resizeWindow();
    Invalidate(XPR_FALSE);
}

LRESULT FlatHeaderCtrl::OnDpiChanged(WPARAM wParam, LPARAM lParam)
{
    initHeader(mBoldFont);
    resizeWindow();
    Invalidate(XPR_FALSE);
    return 0;
}

LRESULT FlatHeaderCtrl::OnThemeChanged(WPARAM wParam, LPARAM lParam)
{
    initHeader(mBoldFont);
    Invalidate(XPR_FALSE);
    return 0;
}

void FlatHeaderCtrl::OnHdnBegindrag(NMHDR *aNmHdr, LRESULT *aResult)
{
    LPNMHEADER sNmHeader = reinterpret_cast<LPNMHEADER>(aNmHdr);
    *aResult = 1;

    mDragging = XPR_FALSE;
}

void FlatHeaderCtrl::OnHdnEnddrag(NMHDR *aNmHdr, LRESULT *aResult)
{
    LPNMHEADER sNmHeader = reinterpret_cast<LPNMHEADER>(aNmHdr);
    *aResult = 0;

    mDragging = XPR_FALSE;
}
