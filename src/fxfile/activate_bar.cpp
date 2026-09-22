//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "activate_bar.h"
#include "option.h"

#include "gui/gdi.h"
#include "gui/MemDC.h"
#include "gui/ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace
{
const xpr_tchar_t kClassName[] = XPR_STRING_LITERAL("ActivateBar");
} // namespace anonymous

ActivateBar::ActivateBar(void)
    : mActivate(XPR_FALSE), mLastActivated(XPR_FALSE)
    , mBackColor(GetSysColor(COLOR_ACTIVECAPTION))
{
}

ActivateBar::~ActivateBar(void)
{
}

BEGIN_MESSAGE_MAP(ActivateBar, CWnd)
    ON_WM_CREATE()
    ON_WM_DESTROY()
    ON_WM_PAINT()
    ON_WM_ERASEBKGND()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
END_MESSAGE_MAP()

xpr_bool_t ActivateBar::Create(CWnd *aParentWnd, xpr_uint_t aId, const RECT &aRect)
{
    DWORD sStyle = 0;
    sStyle |= WS_VISIBLE;
    sStyle |= WS_CHILD;

    WNDCLASS sWndClass;
    HINSTANCE sInstance = AfxGetInstanceHandle();

    if (::GetClassInfo(sInstance, kClassName, &sWndClass) == XPR_FALSE)
    {
        sWndClass.style         = CS_DBLCLKS;
        sWndClass.lpfnWndProc   = ::DefWindowProc;
        sWndClass.cbClsExtra    = 0;
        sWndClass.cbWndExtra    = 0;
        sWndClass.hInstance     = sInstance;
        sWndClass.hIcon         = XPR_NULL;
        sWndClass.hCursor       = AfxGetApp()->LoadStandardCursor(IDC_ARROW);
        sWndClass.hbrBackground = ::GetSysColorBrush(COLOR_WINDOW);
        sWndClass.lpszMenuName  = XPR_NULL;
        sWndClass.lpszClassName = kClassName;

        if (AfxRegisterClass(&sWndClass) == XPR_FALSE)
        {
            AfxThrowResourceException();
            return XPR_FALSE;
        }
    }

    return CWnd::Create(kClassName, XPR_NULL, sStyle, aRect, aParentWnd, aId);
}

xpr_sint_t ActivateBar::OnCreate(LPCREATESTRUCT aCreateStruct)
{
    if (CWnd::OnCreate(aCreateStruct) == -1)
        return -1;

    applyModernAppearance();
    return 0;
}

void ActivateBar::OnDestroy(void)
{
    CWnd::OnDestroy();

}

void ActivateBar::activate(xpr_bool_t aActivate, xpr_bool_t aLastActivated)
{
    mActivate = aActivate;
    mLastActivated = aLastActivated;

    if (XPR_IS_TRUE(mActivate))
        mLastActivated = XPR_FALSE;

    applyModernAppearance();
}

xpr_bool_t ActivateBar::isActivated(void) const
{
    return mActivate;
}

void ActivateBar::setActivateBackColor(COLORREF aBackColor)
{
    if (XPR_IS_FALSE(mActivate))
        return;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    mBackColor = XPR_IS_TRUE(sPalette.mHighContrast) ?
        sPalette.mSelection :
        aBackColor;

    Invalidate(XPR_FALSE);
    UpdateWindow();
}

void ActivateBar::setBackColor(COLORREF aBackColor)
{
    mBackColor = aBackColor;
}

COLORREF ActivateBar::getBackColor(void) const
{
    return mBackColor;
}

void ActivateBar::applyModernAppearance(void)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();

    if (XPR_IS_TRUE(sPalette.mHighContrast))
    {
        if (XPR_IS_TRUE(mActivate))
            mBackColor = sPalette.mSelection;
        else if (XPR_IS_TRUE(mLastActivated))
            mBackColor = sPalette.mSurface;
        else
            mBackColor = sPalette.mWindow;
    }
    else if (XPR_IS_TRUE(mActivate))
    {
        // Preserve the user's configured active-pane color outside High Contrast.
        mBackColor = gOpt->mConfig.mActiveViewColor;
    }
    else if (XPR_IS_TRUE(mLastActivated))
    {
        mBackColor = CalculateColor(
            sPalette.mWindow,
            gOpt->mConfig.mActiveViewColor,
            150);
    }
    else
    {
        mBackColor = CalculateColor(
            sPalette.mWindow,
            sPalette.mSurface,
            50);
    }

    if (XPR_IS_NOT_NULL(m_hWnd))
    {
        Invalidate(XPR_FALSE);
        UpdateWindow();
    }
}

void ActivateBar::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    CWnd::OnSettingChange(aFlags, aSection);
    applyModernAppearance();
}

void ActivateBar::OnSysColorChange(void)
{
    CWnd::OnSysColorChange();
    applyModernAppearance();
}

LRESULT ActivateBar::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    applyModernAppearance();
    return 0;
}

void ActivateBar::OnPaint(void)
{
    CPaintDC sDC(this);
    MemDC sMemDC(&sDC);

    CRect sClientRect;
    GetClientRect(&sClientRect);

    sMemDC.FillSolidRect(sClientRect, mBackColor);
}

xpr_bool_t ActivateBar::OnEraseBkgnd(CDC *aDC)
{
    return XPR_TRUE;
    //return CWnd::OnEraseBkgnd(pDC);
}
} // namespace fxfile
