//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "ListCtrlEx.h"

#include "FlatHeaderCtrl.h"
#include "ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

ListCtrlEx::ListCtrlEx(void)
    : mVistaEnhanced(XPR_FALSE)
    , mHeaderCtrl(XPR_NULL)
{
}

BEGIN_MESSAGE_MAP(ListCtrlEx, super)
    ON_WM_CREATE()
    ON_WM_DESTROY()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
END_MESSAGE_MAP()

xpr_sint_t ListCtrlEx::OnCreate(LPCREATESTRUCT aCreateStruct)
{
    if (super::OnCreate(aCreateStruct) == -1)
        return -1;

    // header control subclassing
    if (subclassHeader(XPR_FALSE) == XPR_FALSE)
        return -1;

    return 0;
}

void ListCtrlEx::OnDestroy(void)
{
    super::OnDestroy();

    XPR_SAFE_DELETE(mHeaderCtrl);
}

xpr_bool_t ListCtrlEx::isVistaEnhanced(void) const
{
    return mVistaEnhanced;
}

void ListCtrlEx::enableVistaEnhanced(xpr_bool_t aEnable)
{
    mVistaEnhanced = aEnable;

    DWORD sExStyle = GetExtendedStyle();
    sExStyle |= LVS_EX_DOUBLEBUFFER; // support from WinXP
    SetExtendedStyle(sExStyle);

    refreshModernAppearance();
}

void ListCtrlEx::refreshModernAppearance(xpr_bool_t aRethemeControl)
{
    if (XPR_IS_NULL(m_hWnd))
        return;

    if (XPR_IS_TRUE(aRethemeControl))
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        const xpr_bool_t sOwnDarkSurface =
            (XPR_IS_TRUE(sPalette.mDark) &&
             XPR_IS_FALSE(sPalette.mHighContrast)) ?
            XPR_TRUE :
            XPR_FALSE;

        if (XPR_IS_TRUE(mVistaEnhanced) &&
            XPR_IS_FALSE(sOwnDarkSurface))
        {
            fxfile::ui::ModernUI::applyExplorerControlTheme(m_hWnd);
        }
        else
        {
            fxfile::ui::ModernUI::resetControlTheme(m_hWnd);
        }
    }

    if (XPR_IS_NOT_NULL(mHeaderCtrl) &&
        XPR_IS_NOT_NULL(mHeaderCtrl->m_hWnd))
    {
        mHeaderCtrl->initHeader(XPR_FALSE);
        mHeaderCtrl->Invalidate(XPR_FALSE);
    }

    // Non-client scrollbars are painted by Windows, not the client palette.
    // Force their frame to be refreshed when the app changes theme.
    RedrawWindow(XPR_NULL, XPR_NULL, RDW_INVALIDATE | RDW_FRAME);
}

xpr_bool_t ListCtrlEx::subclassHeader(xpr_bool_t aBoldFont)
{
    if (XPR_IS_NOT_NULL(mHeaderCtrl))
        return XPR_TRUE;

    mHeaderCtrl = new FlatHeaderCtrl;
    ASSERT(mHeaderCtrl);

    HWND sHwnd = GetDlgItem(0)->GetSafeHwnd();
    if (XPR_IS_NULL(sHwnd))
        return XPR_FALSE;

    if (mHeaderCtrl->SubclassWindow(sHwnd) == XPR_FALSE)
        return XPR_FALSE;

    mHeaderCtrl->initHeader(aBoldFont);

    return XPR_TRUE;
}

xpr_sint_t ListCtrlEx::setSortImage(xpr_sint_t aColumn, xpr_bool_t aAscending)
{
    if (XPR_IS_NULL(mHeaderCtrl))
        return -1;

    return mHeaderCtrl->setSortImage(aColumn, aAscending);
}

void ListCtrlEx::OnSettingChange(
    xpr_uint_t aFlags,
    const xpr_tchar_t *aSection)
{
    super::OnSettingChange(aFlags, aSection);
    refreshModernAppearance();
}

void ListCtrlEx::OnSysColorChange(void)
{
    super::OnSysColorChange();
    refreshModernAppearance();
}

LRESULT ListCtrlEx::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    return 0;
}

LRESULT ListCtrlEx::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    // SetWindowTheme can emit WM_THEMECHANGED. Repaint dependent surfaces,
    // but do not issue another association change from inside the notification.
    refreshModernAppearance(XPR_FALSE);
    return 0;
}

LRESULT ListCtrlEx::WindowProc(xpr_uint_t msg, WPARAM wParam, LPARAM lParam) 
{
    LRESULT lResult = super::WindowProc(msg, wParam, lParam);

    // UI-02: let the native list do layout/hit testing and then match only
    // its exposed scrollbar pixels in Dark (never in High Contrast).
    if (msg == WM_NCPAINT || msg == WM_VSCROLL ||
        msg == WM_HSCROLL || msg == WM_MOUSEWHEEL ||
        msg == WM_NCLBUTTONUP || msg == WM_NCMOUSEMOVE)
        fxfile::ui::ModernUI::paintDarkNativeScrollbars(m_hWnd);

    if (msg == WM_SETREDRAW)
    {
        xpr_bool_t sRedraw = (xpr_bool_t)wParam;
        if (XPR_IS_TRUE(sRedraw))
        {
            if (XPR_IS_NOT_NULL(mHeaderCtrl))
                mHeaderCtrl->Invalidate(XPR_FALSE);
        }
    }

    return lResult;
}
