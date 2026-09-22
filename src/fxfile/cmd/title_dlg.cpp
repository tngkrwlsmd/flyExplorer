//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "title_dlg.h"

#include "gui/ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cmd
{
#define TITLE_MARGIN 13

TitleDlg::TitleDlg(const xpr_uint_t aResourceId)
    : CDialog(aResourceId, XPR_NULL)
    , mDescIcon(XPR_NULL)
    , mDescIconResourceId(0)
    , mSurfaceColor(CLR_INVALID)
    , mWindowColor(CLR_INVALID)
    , mBold(XPR_FALSE)
    , mOffset(0)
{
}

BEGIN_MESSAGE_MAP(TitleDlg, CDialog)
    ON_WM_PAINT()
    ON_WM_ERASEBKGND()
    ON_WM_CTLCOLOR()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_WM_DESTROY()
END_MESSAGE_MAP()

void TitleDlg::setCtrlOffset(xpr_sint_t aOffset)
{
    mOffset = aOffset;
}

xpr_bool_t TitleDlg::OnInitDialog(void)
{
    CDialog::OnInitDialog();

    refreshModernAppearance();
    refreshDescResourceIcon();

    if (mOffset > 0)
    {
        CRect sRect;
        CWnd *sWnd = GetWindow(GW_CHILD);
        while (sWnd != XPR_NULL)
        {
            sWnd->GetWindowRect(&sRect);
            ScreenToClient(&sRect);

            sRect.InflateRect(0, -mOffset, 0, mOffset);
            sWnd->MoveWindow(sRect, XPR_FALSE);

            sWnd = sWnd->GetWindow(GW_HWNDNEXT);
        }

        GetWindowRect(&sRect);
        SetWindowPos(XPR_NULL, sRect.left, sRect.top, sRect.Width(), sRect.Height()+mOffset, SWP_NOZORDER);
        CenterWindow();
    }

    LOGFONT sLogFont = {0};
    GetFont()->GetLogFont(&sLogFont);
    if (mBold == XPR_TRUE)
        sLogFont.lfWeight = FW_BOLD;

    if (XPR_IS_NOT_NULL(mTitleFont.m_hObject))
        mTitleFont.DeleteObject();
    mTitleFont.CreateFontIndirect(&sLogFont);

    if (mTitle.empty() == XPR_FALSE)
        SetWindowText(mTitle.c_str());

    SetDlgItemText(IDOK,     gApp.loadString(XPR_STRING_LITERAL("popup.common.button.ok")));
    SetDlgItemText(IDCANCEL, gApp.loadString(XPR_STRING_LITERAL("popup.common.button.cancel")));

    return XPR_TRUE;
}

void TitleDlg::setTitle(const xpr_tchar_t *aTitle)
{
    if (aTitle == XPR_NULL)
        return;

    mTitle = aTitle;

    if (m_hWnd != XPR_NULL)
        SetWindowText(mTitle.c_str());
}

void TitleDlg::setDesc(const xpr_tchar_t *aDesc)
{
    if (aDesc == XPR_NULL)
        return;

    mDesc = aDesc;
}

void TitleDlg::setDescIcon(xpr_uint_t aIconId, xpr_bool_t aIconLeft)
{
    DESTROY_ICON(mDescIcon);

    mDescIconResourceId = aIconId;
    mIconLeft = aIconLeft;

    refreshDescResourceIcon();
}

void TitleDlg::setDescIcon(HICON aIcon, xpr_bool_t aIconLeft, xpr_bool_t aBold)
{
    DESTROY_ICON(mDescIcon);

    mDescIcon = aIcon;
    mDescIconResourceId = 0;
    mIconLeft = aIconLeft;
    mBold     = aBold;
}

void TitleDlg::OnPaint(void)
{
    CPaintDC sPaintDc(this);

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    const xpr_sint_t sDefaultHeaderHeight = ui::ModernUI::scaleForWindow(50, GetSafeHwnd());
    const xpr_sint_t sHeight =
        (mOffset > 0) ?
        (mOffset - ui::ModernUI::scaleForWindow(2, GetSafeHwnd())) :
        sDefaultHeaderHeight;
    const xpr_sint_t sMargin = ui::ModernUI::scaleForWindow(TITLE_MARGIN, GetSafeHwnd());
    const xpr_sint_t sIconSize = ui::ModernUI::scaleForWindow(32, GetSafeHwnd());
    const xpr_sint_t sIconSlot = ui::ModernUI::scaleForWindow(60, GetSafeHwnd());

    CRect sRect;
    GetClientRect(&sRect);
    sRect.bottom = sHeight;

    sPaintDc.FillSolidRect(sRect, sPalette.mWindow);

    CPen sSeparatorPen(PS_SOLID, 1, sPalette.mSeparator);
    CPen *sOldPen = sPaintDc.SelectObject(&sSeparatorPen);
    sPaintDc.MoveTo(sRect.left, sRect.bottom - 1);
    sPaintDc.LineTo(sRect.right, sRect.bottom - 1);
    sPaintDc.SelectObject(sOldPen);

    sPaintDc.SetBkMode(TRANSPARENT);
    sPaintDc.SetTextColor(sPalette.mText);

    CRect sTextRect(
        sMargin + ui::ModernUI::scaleForWindow(2, GetSafeHwnd()),
        0,
        sRect.right - (sMargin + ui::ModernUI::scaleForWindow(2, GetSafeHwnd())),
        sRect.bottom);
    CPoint sIconPoint(0,0);
    if (mDescIcon != XPR_NULL)
    {
        if (mIconLeft)
        {
            sTextRect.left = sIconSlot;
            sIconPoint = CPoint(
                sMargin,
                (sRect.Height() - sIconSize) / 2);
        }
        else
        {
            sTextRect.right = sRect.right - sIconSlot;
            sIconPoint = CPoint(
                sRect.right - sMargin - sIconSize,
                (sRect.Height() - sIconSize) / 2);
        }
    }

    CFont *sOldFont = sPaintDc.SelectObject(&mTitleFont);

    CRect sCalcRect(sTextRect);
    sPaintDc.DrawText(mDesc.c_str(), sCalcRect, DT_LEFT | DT_VCENTER | DT_WORDBREAK | DT_CALCRECT);

    sTextRect.top    = sTextRect.top + (sTextRect.Height() - sCalcRect.Height()) / 2;
    sTextRect.bottom = sTextRect.top + sCalcRect.Height();
    sPaintDc.DrawText(mDesc.c_str(), sTextRect, DT_LEFT | DT_VCENTER | DT_WORDBREAK);

    sPaintDc.SelectObject(sOldFont);

    if (mDescIcon != XPR_NULL)
    {
        ::DrawIconEx(
            sPaintDc.m_hDC,
            sIconPoint.x,
            sIconPoint.y,
            mDescIcon,
            sIconSize,
            sIconSize,
            0,
            XPR_NULL,
            DI_NORMAL);
    }
}

void TitleDlg::applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont)
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
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0) ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_TRUE(sStandardFontControl) &&
        XPR_IS_NOT_NULL(mUIFont.m_hObject))
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
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0) ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_TRUE(sExplorerThemeControl))
        ui::ModernUI::applyExplorerControlTheme(aWnd->GetSafeHwnd());

    CWnd *sChild = aWnd->GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void TitleDlg::applyModernAppearanceToChildren(HFONT aPreviousFont)
{
    CWnd *sChild = GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void TitleDlg::refreshDescResourceIcon(void)
{
    if (mDescIconResourceId == 0 || XPR_IS_NULL(m_hWnd))
        return;

    DESTROY_ICON(mDescIcon);
    mDescIcon = ui::ModernUI::loadIconResource(
        AfxGetResourceHandle(),
        mDescIconResourceId,
        GetSafeHwnd(),
        32);
}

void TitleDlg::refreshModernAppearance(void)
{
    if (XPR_IS_NULL(m_hWnd))
        return;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    const HFONT sPreviousFont = reinterpret_cast<HFONT>(
        SendMessage(WM_GETFONT, 0, 0));

    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())))
    {
        if (XPR_IS_NOT_NULL(mUIFont.m_hObject))
            mUIFont.DeleteObject();

        if (mUIFont.CreateFontIndirect(&sLogFont) == XPR_TRUE)
            SetFont(&mUIFont, XPR_FALSE);
    }

    if (mSurfaceColor != sPalette.mSurface)
    {
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            mSurfaceBrush.DeleteObject();

        if (mSurfaceBrush.CreateSolidBrush(sPalette.mSurface) == XPR_TRUE)
            mSurfaceColor = sPalette.mSurface;
        else
            mSurfaceColor = CLR_INVALID;
    }

    if (mWindowColor != sPalette.mWindow)
    {
        if (XPR_IS_NOT_NULL(mWindowBrush.m_hObject))
            mWindowBrush.DeleteObject();

        if (mWindowBrush.CreateSolidBrush(sPalette.mWindow) == XPR_TRUE)
            mWindowColor = sPalette.mWindow;
        else
            mWindowColor = CLR_INVALID;
    }

    ui::ModernUI::applyWindowFrameTheme(GetSafeHwnd());
    applyModernAppearanceToChildren(sPreviousFont);

    Invalidate(XPR_FALSE);
}

xpr_bool_t TitleDlg::OnEraseBkgnd(CDC *aDC)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mDark) && XPR_IS_FALSE(sPalette.mHighContrast))
    {
        CRect sClientRect;
        GetClientRect(&sClientRect);
        aDC->FillSolidRect(&sClientRect, sPalette.mSurface);
        return XPR_TRUE;
    }

    return CDialog::OnEraseBkgnd(aDC);
}

HBRUSH TitleDlg::OnCtlColor(CDC *aDC, CWnd *aWnd, xpr_uint_t aCtlColor)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mDark) || XPR_IS_TRUE(sPalette.mHighContrast))
        return CDialog::OnCtlColor(aDC, aWnd, aCtlColor);

    aDC->SetTextColor(
        XPR_IS_NOT_NULL(aWnd) && XPR_IS_FALSE(aWnd->IsWindowEnabled()) ?
        sPalette.mSecondaryText :
        sPalette.mText);

    if (aCtlColor == CTLCOLOR_EDIT || aCtlColor == CTLCOLOR_LISTBOX)
    {
        aDC->SetBkMode(OPAQUE);
        aDC->SetBkColor(sPalette.mWindow);
        if (XPR_IS_NOT_NULL(mWindowBrush.m_hObject))
            return (HBRUSH)mWindowBrush.GetSafeHandle();
    }
    else if (aCtlColor == CTLCOLOR_STATIC ||
             aCtlColor == CTLCOLOR_BTN ||
             aCtlColor == CTLCOLOR_DLG)
    {
        aDC->SetBkMode(TRANSPARENT);
        aDC->SetBkColor(sPalette.mSurface);
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            return (HBRUSH)mSurfaceBrush.GetSafeHandle();
    }

    return CDialog::OnCtlColor(aDC, aWnd, aCtlColor);
}

void TitleDlg::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    CDialog::OnSettingChange(aFlags, aSection);
    refreshModernAppearance();
    refreshDescResourceIcon();
}

void TitleDlg::OnSysColorChange(void)
{
    CDialog::OnSysColorChange();
    refreshModernAppearance();
    refreshDescResourceIcon();
}

LRESULT TitleDlg::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    refreshDescResourceIcon();
    return Default();
}

LRESULT TitleDlg::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    refreshDescResourceIcon();

    if (XPR_IS_NOT_NULL(mTitleFont.m_hObject))
        mTitleFont.DeleteObject();

    LOGFONT sLogFont = {0};
    if (XPR_IS_NOT_NULL(GetFont()))
    {
        GetFont()->GetLogFont(&sLogFont);
        if (mBold == XPR_TRUE)
            sLogFont.lfWeight = FW_BOLD;
        mTitleFont.CreateFontIndirect(&sLogFont);
    }

    return Default();
}

void TitleDlg::OnDestroy(void) 
{
    CDialog::OnDestroy();

    DELETE_OBJECT(mTitleFont);
    DELETE_OBJECT(mUIFont);
    DELETE_OBJECT(mSurfaceBrush);
    DELETE_OBJECT(mWindowBrush);
    DESTROY_ICON(mDescIcon);
}
} // namespace cmd
} // namespace fxfile
