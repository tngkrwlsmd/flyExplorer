//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "DrivePieCtrl.h"

#include "ModernUI.h"

#include <math.h>

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

const xpr_sint_t kMargin = 5;
const xpr_sint_t kLegendMarkerSize = 13;

DrivePieCtrl::DrivePieCtrl(void)
    : mTotalSize(0), mUsedSize(0), mFreeSize(0)
{
    mDrive[0] = XPR_STRING_LITERAL('\0');
}

DrivePieCtrl::~DrivePieCtrl(void)
{
}

BEGIN_MESSAGE_MAP(DrivePieCtrl, CStatic)
    ON_WM_PAINT()
    ON_WM_SETTINGCHANGE()
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_DPICHANGED_AFTERPARENT, OnDpiChangedAfterParent)
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
END_MESSAGE_MAP()

void DrivePieCtrl::OnPaint(void)
{
    CPaintDC sPaintDC(this);

    drawDrivePie(sPaintDC);
    drawLegends(sPaintDC);
}

void DrivePieCtrl::setString(const xpr_tchar_t *aTotalSizeText, const xpr_tchar_t *aUsedSizeText, const xpr_tchar_t *aFreeSizeText)
{
    mTotalSizeText.clear();
    mUsedSizeText.clear();
    mFreeSizeText.clear();

    if (XPR_IS_NOT_NULL(aTotalSizeText)) mTotalSizeText = aTotalSizeText;
    if (XPR_IS_NOT_NULL(aUsedSizeText )) mUsedSizeText  = aUsedSizeText;
    if (XPR_IS_NOT_NULL(aFreeSizeText )) mFreeSizeText  = aFreeSizeText;
}

void DrivePieCtrl::setDrive(const xpr_tchar_t *aDrive)
{
    _tcscpy(mDrive, aDrive);

    getDriveSpace();

    Invalidate();
}

xpr_sint_t DrivePieCtrl::scaleMetric(xpr_sint_t aValue) const
{
    return fxfile::ui::ModernUI::scaleForWindow(aValue, GetSafeHwnd());
}

void DrivePieCtrl::drawDrivePie(CDC &aDC)
{
    CRect sClientRect;
    GetClientRect(&sClientRect);

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    const COLORREF sBackgroundColor =
        XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mWindow : sPalette.mSurface;
    aDC.FillSolidRect(&sClientRect, sBackgroundColor);

    if (mDrive[0] == XPR_STRING_LITERAL('\0') || mTotalSize == 0)
        return;

    const xpr_sint_t sMargin = scaleMetric(kMargin);
    sClientRect.DeflateRect(sMargin, sMargin);

    CPen *sOldPen;
    CBrush *sOldBrush;
    const COLORREF sColors[2] =
    {
        sPalette.mSelection,
        XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mWindow : sPalette.mSurface,
    };

    // Draw the existing used/free pie with system-derived colors.
    xpr_sint_t sCenterX, sCenterY, sRadius, sNewX, sNewY, sLastX, sLastY;
    sCenterX = sClientRect.left + (xpr_sint_t)(sClientRect.Width() / 3.2);
    sCenterY = sClientRect.top + sClientRect.Height() / 2;

    sRadius = min(sClientRect.Height(), sClientRect.Width()) / 2;

    sLastX = sCenterX + sRadius;
    sLastY = sCenterY;

    CRect sPieRect;
    sPieRect.top    = sCenterY - sRadius;
    sPieRect.left   = sCenterX - sRadius;
    sPieRect.bottom = sCenterY + sRadius;
    sPieRect.right  = sCenterX + sRadius;

    xpr_double_t sSlice[2];
    sSlice[0] = (xpr_double_t)(mUsedSize * 1.0 / mTotalSize);
    sSlice[1] = (xpr_double_t)(mFreeSize * 1.0 / mTotalSize);

    xpr_sint_t i;
    xpr_double_t sDegree = 0, sDataSum = 0;
    for (i = 0; i < 2; ++i)
    {
        if (sSlice[i] == 0.f)
            continue;

        sDataSum += sSlice[i];
        sDegree = sDataSum * 2.0 * XPR_MATH_PI;

        sNewX = sCenterX + (xpr_sint_t)((xpr_double_t)sRadius * cos(sDegree));
        sNewY = sCenterY - (xpr_sint_t)((xpr_double_t)sRadius * sin(sDegree));

        CPoint sPoint1(sLastX, sLastY);
        CPoint sPoint2(sNewX, sNewY);

        CBrush sBrush(sColors[i]);
        CPen sPiePen(PS_SOLID, max(1, scaleMetric(1)), sPalette.mBorder);
        sOldPen = aDC.SelectObject(&sPiePen);
        sOldBrush = aDC.SelectObject(&sBrush);

        if (sSlice[i] >= 1.0)
            aDC.Ellipse(sPieRect);
        else
            aDC.Pie(sPieRect, sPoint1, sPoint2);

        aDC.SelectObject(sOldBrush);
        aDC.SelectObject(sOldPen);

        sLastX = sNewX;
        sLastY = sNewY;
    }
}

void DrivePieCtrl::getDriveSpace(void)
{
    ULARGE_INTEGER sUsedSize  = {0};
    ULARGE_INTEGER sTotalSize = {0};
    ULARGE_INTEGER sFreeSize  = {0};
    ULARGE_INTEGER sTempSize  = {0};

    TRY
    {
        ::GetDiskFreeSpaceEx(mDrive, &sTempSize, &sTotalSize, &sFreeSize);
        sUsedSize.QuadPart = sTotalSize.QuadPart - sFreeSize.QuadPart;
    }
    END_TRY

    mTotalSize = sTotalSize.QuadPart;
    mFreeSize  = sFreeSize.QuadPart;
    mUsedSize  = sUsedSize.QuadPart;
}

void DrivePieCtrl::drawLegends(CDC &aDC)
{
    if (mDrive[0] == XPR_STRING_LITERAL('\0') || mTotalSize == 0)
        return;

    const xpr_sint_t sMargin = scaleMetric(kMargin);
    const xpr_sint_t sMarkerSize = scaleMetric(kLegendMarkerSize);
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();

    CRect sClientRect;
    GetClientRect(&sClientRect);
    sClientRect.top    += sMargin;
    sClientRect.right  -= sMargin;
    sClientRect.left   += (xpr_sint_t)(sClientRect.Width() / 1.8) + sMargin;
    sClientRect.bottom -= sClientRect.Height() * 3 / 5 + sMargin;

    CRect sLine1Rect, sLine2Rect, sLine3Rect;
    sLine1Rect = sLine2Rect = sLine3Rect = sClientRect;
    sLine1Rect.bottom = sClientRect.top + sClientRect.Height() / 3;
    sLine2Rect.top = sLine1Rect.bottom + sMargin;
    sLine2Rect.bottom = sClientRect.bottom - sClientRect.Height() / 3 + sMargin / 2;
    sLine3Rect.top = sLine2Rect.bottom + sMargin;

    xpr::string sTitle;
    CFont *sFont = GetFont();
    if (XPR_IS_NULL(sFont))
        sFont = GetParent()->GetFont();

    CFont *sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(sFont))
        sOldFont = aDC.SelectObject(sFont);

    aDC.SetBkMode(TRANSPARENT);
    aDC.SetTextColor(sPalette.mText);

    if (mTotalSize > 1024.0*1024.0*1024)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f GB"), mTotalSizeText.c_str(), mTotalSize/1024.0/1024.0/1024.0);
    else if (mTotalSize > 1024.0*1024.0)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f MB"), mTotalSizeText.c_str(), mTotalSize/1024.0/1024.0);
    else
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f KB"), mTotalSizeText.c_str(), mTotalSize/1024.0);
    aDC.TextOut(sLine1Rect.left + sMargin, sLine1Rect.top + sMargin, sTitle.c_str());

    if (mUsedSize > 1024.0*1024.0*1024)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f GB"), mUsedSizeText.c_str(), mUsedSize/1024.0/1024.0/1024.0);
    else if (mUsedSize > 1024.0*1024.0)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f MB"), mUsedSizeText.c_str(), mUsedSize/1024.0/1024.0);
    else
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f KB"), mUsedSizeText.c_str(), mUsedSize/1024.0);
    aDC.TextOut(sLine2Rect.left + sMargin + sLine2Rect.Width()/5, sLine2Rect.top, sTitle.c_str());

    if (mFreeSize > 1024.0*1024.0*1024)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f GB"), mFreeSizeText.c_str(), mFreeSize/1024.0/1024.0/1024.0);
    else if (mFreeSize > 1024.0*1024.0)
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f MB"), mFreeSizeText.c_str(), mFreeSize/1024.0/1024.0);
    else
        sTitle.format(XPR_STRING_LITERAL("%s: %2.2f KB"), mFreeSizeText.c_str(), mFreeSize/1024.0);
    aDC.TextOut(sLine3Rect.left + sMargin + sLine3Rect.Width()/5, sLine3Rect.top - sMargin, sTitle.c_str());

    if (XPR_IS_NOT_NULL(sOldFont))
        aDC.SelectObject(sOldFont);

    const COLORREF sFreeColor =
        XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mWindow : sPalette.mSurface;

    CRect sUsedRect(
        sLine2Rect.left + sMargin * 2,
        sLine2Rect.top,
        sLine2Rect.left + sMargin * 2 + sMarkerSize,
        sLine2Rect.top + sMarkerSize);
    CRect sFreeRect(
        sLine3Rect.left + sMargin * 2,
        sLine3Rect.top - sMargin,
        sLine3Rect.left + sMargin * 2 + sMarkerSize,
        sLine3Rect.top - sMargin + sMarkerSize);

    CBrush sUsedBrush(sPalette.mSelection);
    CBrush sFreeBrush(sFreeColor);
    aDC.FillRect(&sUsedRect, &sUsedBrush);
    aDC.FillRect(&sFreeRect, &sFreeBrush);

    aDC.Draw3dRect(&sUsedRect, sPalette.mBorder, sPalette.mBorder);
    aDC.Draw3dRect(&sFreeRect, sPalette.mBorder, sPalette.mBorder);
}

void DrivePieCtrl::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    Invalidate(XPR_FALSE);
    CStatic::OnSettingChange(aFlags, aSection);
}

LRESULT DrivePieCtrl::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    Invalidate(XPR_FALSE);
    return 0;
}

LRESULT DrivePieCtrl::OnDpiChangedAfterParent(WPARAM aWParam, LPARAM aLParam)
{
    Invalidate(XPR_FALSE);
    return 0;
}

LRESULT DrivePieCtrl::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    Invalidate(XPR_FALSE);
    return 0;
}
