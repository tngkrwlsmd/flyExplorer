//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "tip_dlg.h"
#include "../gui/ModernUI.h"

#include "option.h"
#include "resource.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cmd
{
#define MAX_TIP 100

TipDlg::TipDlg(void)
    : super(IDD_TIP, XPR_NULL)
    , mIndex(-1)
{
}

void TipDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(TipDlg, super)
    ON_WM_PAINT()
    ON_WM_DESTROY()
    ON_BN_CLICKED(IDC_TIP_NEXT, OnNext)
    ON_BN_CLICKED(IDC_TIP_SHOW_AT_STARTUP, OnTipStartup)
END_MESSAGE_MAP()

xpr_bool_t TipDlg::OnInitDialog(void) 
{
    super::OnInitDialog();

    xpr_bool_t sStartupTip = gOpt->mMain.mTipOfTheToday;
    ((CButton *)GetDlgItem(IDC_TIP_SHOW_AT_STARTUP))->SetCheck(sStartupTip);

    xpr_sint_t i;
    xpr_tchar_t sStringId[0xff] = {0};
    const xpr_tchar_t *sString = XPR_NULL;

    for (i = 1; i <= MAX_TIP ; ++i)
    {
        _stprintf(sStringId, XPR_STRING_LITERAL("popup.tip_of_today.tip%d"), i);

        sString = gApp.loadString(sStringId, XPR_TRUE);
        if (sString != XPR_NULL)
        {
            mTipDeque.push_back(sString);
        }
        else
        {
            break;
        }
    }

    srand((xpr_uint_t)time(XPR_NULL));

    if (mTipDeque.empty() == false)
        mIndex = rand() % mTipDeque.size();

    SetWindowText(gApp.loadString(XPR_STRING_LITERAL("popup.tip_of_today.title")));
    SetDlgItemText(IDC_TIP_SHOW_AT_STARTUP, gApp.loadString(XPR_STRING_LITERAL("popup.tip_of_today.check.show_at_startup")));
    SetDlgItemText(IDC_TIP_NEXT,            gApp.loadString(XPR_STRING_LITERAL("popup.tip_of_today.button.next_tip")));
    SetDlgItemText(IDOK,                    gApp.loadString(XPR_STRING_LITERAL("popup.common.button.ok")));

    return XPR_TRUE;
}

void TipDlg::OnPaint(void) 
{
    CPaintDC sPaintDc(this);

    const xpr_uint_t sDpi = ui::ModernUI::getDpi(GetSafeHwnd());
    const xpr_sint_t sIconSize = ui::ModernUI::scale(32, sDpi);
    const CRect sOffsetRect(
        ui::ModernUI::scale(7, sDpi),
        ui::ModernUI::scale(10, sDpi),
        ui::ModernUI::scale(7, sDpi),
        ui::ModernUI::scale(10, sDpi));
    const CPoint sTextOffset(
        ui::ModernUI::scale(15, sDpi),
        ui::ModernUI::scale(10, sDpi));
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();

    CRect sRect;
    GetClientRect(&sRect);

    CRect sOkButtonRect;
    GetDlgItem(IDOK)->GetWindowRect(&sOkButtonRect);
    ScreenToClient(&sOkButtonRect);
    sRect.bottom = sOkButtonRect.top - sOffsetRect.bottom;

    sPaintDc.FillSolidRect(sRect, sPalette.mSurface);

    HICON sIcon = ui::ModernUI::loadIconResource(
        AfxGetResourceHandle(),
        IDI_TIP,
        GetSafeHwnd(),
        32);
    if (sIcon != XPR_NULL)
    {
        CPoint sIconPoint(sOffsetRect.left, sOffsetRect.top);
        ::DrawIconEx(
            sPaintDc.m_hDC,
            sIconPoint.x,
            sIconPoint.y,
            sIcon,
            sIconSize,
            sIconSize,
            0,
            XPR_NULL,
            DI_NORMAL);
        DESTROY_ICON(sIcon);
    }

    CPen sPen(PS_SOLID, 1, sPalette.mSeparator);
    CPen *sOldPen = sPaintDc.SelectObject(&sPen);
    sPaintDc.MoveTo(sRect.left,  sRect.bottom);
    sPaintDc.LineTo(sRect.right, sRect.bottom);
    sPaintDc.SelectObject(sOldPen);

    CRect sTitleRect(sRect);
    sTitleRect.left   = sOffsetRect.left + sIconSize + sTextOffset.x;
    sTitleRect.top    = sOffsetRect.top;
    sTitleRect.bottom = sTitleRect.top + sIconSize;

    LOGFONT sLogFont = {0};
    GetFont()->GetLogFont(&sLogFont);

    CFont sTextFont;
    sTextFont.CreateFontIndirect(&sLogFont);

    CFont sTitleFont;
    sLogFont.lfHeight = -MulDiv(13, GetDeviceCaps(sPaintDc.m_hDC, LOGPIXELSY), 72);
    sTitleFont.CreateFontIndirect(&sLogFont);

    sPaintDc.SetTextColor(sPalette.mSelection);

    CFont *sOldFont = sPaintDc.SelectObject(&sTitleFont);
    const xpr_tchar_t sTipOfTodayText[] = XPR_STRING_LITERAL("Did you know...");
    sPaintDc.DrawText(sTipOfTodayText, (xpr_sint_t)_tcslen(sTipOfTodayText), sTitleRect, DT_SINGLELINE | DT_LEFT | DT_VCENTER);
    sPaintDc.SelectObject(sOldFont);

    sPaintDc.SetTextColor(sPalette.mText);

    CRect sTextRect;
    sTextRect.left   = sTitleRect.left;
    sTextRect.top    = sTitleRect.bottom + sTextOffset.y;
    sTextRect.right  = sRect.right  - sOffsetRect.right;
    sTextRect.bottom = sRect.bottom - sOffsetRect.bottom;

    const xpr_tchar_t *sText = XPR_NULL;
    if (FXFILE_STL_IS_INDEXABLE(mIndex, mTipDeque))
    {
        sText = mTipDeque[mIndex].c_str();
    }

    if (sText != XPR_NULL)
    {
        sOldFont = sPaintDc.SelectObject(&sTextFont);
        sPaintDc.DrawText(sText, (xpr_sint_t)_tcslen(sText), sTextRect, DT_LEFT | DT_WORDBREAK);
        sPaintDc.SelectObject(sOldFont);
    }
}

void TipDlg::OnNext(void)
{
    if (mTipDeque.empty() == false)
    {
        mIndex = ++mIndex % mTipDeque.size();
        Invalidate(XPR_FALSE);
    }
}

void TipDlg::OnDestroy(void) 
{
    super::OnDestroy();

}

void TipDlg::OnTipStartup(void) 
{
    gOpt->mMain.mTipOfTheToday = ((CButton *)GetDlgItem(IDC_TIP_SHOW_AT_STARTUP))->GetCheck();
}
} // namespace cmd
} // namespace fxfile
