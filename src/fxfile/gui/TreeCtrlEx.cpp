//
// Copyright (c) 2001-2012 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "TreeCtrlEx.h"
#include "ModernUI.h"
#include "DarkScrollbarLayer.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

TreeCtrlEx::TreeCtrlEx(void)
    : mVistaEnhanced(XPR_FALSE)
    , mDarkScrollbars(XPR_FALSE)
    , mScrollbarPaintQueued(XPR_FALSE)
    , mScrollbarPainting(XPR_FALSE)
{
}

TreeCtrlEx::~TreeCtrlEx(void)
{
}

BEGIN_MESSAGE_MAP(TreeCtrlEx, super)
END_MESSAGE_MAP()

xpr_bool_t TreeCtrlEx::hasChildItem(HTREEITEM aTreeItem) const
{
    TVITEM sTvItem = {0};
    sTvItem.hItem = aTreeItem;
    sTvItem.mask  = TVIF_CHILDREN;
    if (GetItem(&sTvItem) == XPR_FALSE)
        return XPR_FALSE;

    return (sTvItem.cChildren != 0) ? XPR_TRUE : XPR_FALSE;
}

HTREEITEM TreeCtrlEx::findChildItem(HTREEITEM aTreeItem, const xpr::string &aFindName, xpr_bool_t aCaseSensitivity) const
{
    XPR_ASSERT(aTreeItem != XPR_NULL);

    HTREEITEM sChildTreeItem = CTreeCtrl::GetChildItem(aTreeItem);
    if (XPR_IS_NOT_NULL(sChildTreeItem))
    {
        return findNextItem(sChildTreeItem, aFindName, aCaseSensitivity);
    }

    return XPR_NULL;
}

HTREEITEM TreeCtrlEx::findNextItem(HTREEITEM aTreeItem, const xpr::string &aFindName, xpr_bool_t aCaseSensitivity) const
{
    XPR_ASSERT(aTreeItem != XPR_NULL);

    HTREEITEM sTreeItem = aTreeItem;
    xpr::string sItemName;

    do
    {
        sItemName = CTreeCtrl::GetItemText(sTreeItem);

        if (XPR_IS_TRUE(aCaseSensitivity))
        {
            if (aFindName.compare(sItemName) == 0)
            {
                return sTreeItem;
            }
        }
        else
        {
            if (aFindName.compare_case(sItemName) == 0)
            {
                return sTreeItem;
            }
        }

        sTreeItem = CTreeCtrl::GetNextSiblingItem(sTreeItem);
    }
    while (XPR_IS_NOT_NULL(sTreeItem));

    return XPR_NULL;
}

xpr_bool_t TreeCtrlEx::isVistaEnhanced(void) const
{
    return mVistaEnhanced;
}

void TreeCtrlEx::enableVistaEnhanced(xpr_bool_t aEnable)
{
    DWORD sExStyleMask = TVS_EX_DOUBLEBUFFER | TVS_EX_FADEINOUTEXPANDOS | TVS_EX_AUTOHSCROLL;
    DWORD sExStyle     = TVS_EX_DOUBLEBUFFER;

    mVistaEnhanced = aEnable;
    refreshVistaEnhancedTheme();

    if (XPR_IS_TRUE(aEnable))
    {
        ModifyStyle(TVS_HASLINES, TVS_FULLROWSELECT | TVS_TRACKSELECT);

        sExStyle = sExStyleMask;
    }
    else
    {
        ModifyStyle(TVS_FULLROWSELECT | TVS_TRACKSELECT, TVS_HASLINES);
    }

    SetExtendedStyle(sExStyleMask, sExStyle);
}

void TreeCtrlEx::refreshVistaEnhancedTheme(void)
{
    if (XPR_IS_NULL(m_hWnd))
        return;

    const fxfile::ui::ThemePalette sPalette =
        fxfile::ui::ModernUI::getPalette();
    const xpr_bool_t sOwnDarkSurface =
        (XPR_IS_TRUE(sPalette.mDark) &&
         XPR_IS_FALSE(sPalette.mHighContrast)) ?
        XPR_TRUE :
        XPR_FALSE;
    mDarkScrollbars = sOwnDarkSurface;
    if (XPR_IS_FALSE(mDarkScrollbars))
        mScrollbarPaintQueued = XPR_FALSE;

    if (XPR_IS_TRUE(mVistaEnhanced) &&
        XPR_IS_FALSE(sOwnDarkSurface))
    {
        // Light/System and High Contrast keep the documented Explorer/system
        // visual-style path.
        fxfile::ui::ModernUI::applyExplorerControlTheme(m_hWnd);
    }
    else
    {
        // Dark mode is palette-owned. Do not reintroduce a light Explorer
        // association just because enhanced tree behavior is enabled.
        fxfile::ui::ModernUI::resetControlTheme(m_hWnd);
    }
    ::RedrawWindow(m_hWnd, NULL, NULL, RDW_INVALIDATE | RDW_FRAME);

    if (XPR_IS_TRUE(mDarkScrollbars))
        fxfile::ui::DarkScrollbarLayer::enable(m_hWnd, sPalette);
    else
        fxfile::ui::DarkScrollbarLayer::disable(m_hWnd);
}

LRESULT TreeCtrlEx::WindowProc(UINT aMessage, WPARAM aWParam, LPARAM aLParam)
{
    if (aMessage == WM_DESTROY)
        fxfile::ui::DarkScrollbarLayer::disable(m_hWnd);

    const UINT sPaintMessage =
        fxfile::ui::ModernUI::getDeferredDarkScrollbarMessage();
    if (sPaintMessage != 0 && aMessage == sPaintMessage)
    {
        mScrollbarPaintQueued = XPR_FALSE;
        if (XPR_IS_TRUE(mDarkScrollbars) &&
            XPR_IS_FALSE(mScrollbarPainting) && ::IsWindow(m_hWnd))
        {
            mScrollbarPainting = XPR_TRUE;
            fxfile::ui::ModernUI::paintDarkNativeScrollbars(m_hWnd);
            mScrollbarPainting = XPR_FALSE;
        }
        return 0;
    }

    const LRESULT sResult = super::WindowProc(
        aMessage, aWParam, aLParam);

    // Refresh the cached draw owner only on theme/setting transitions.
    // Do not query the WinRT palette from WM_NCPAINT or native scroll input.
    if ((aMessage == WM_THEMECHANGED ||
         aMessage == WM_SYSCOLORCHANGE ||
         aMessage == WM_SETTINGCHANGE) && ::IsWindow(m_hWnd))
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        mDarkScrollbars =
            XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast) ?
            XPR_TRUE : XPR_FALSE;
        if (XPR_IS_FALSE(mDarkScrollbars))
            mScrollbarPaintQueued = XPR_FALSE;
        ::RedrawWindow(m_hWnd, NULL, NULL, RDW_INVALIDATE | RDW_FRAME);
        if (XPR_IS_TRUE(mDarkScrollbars))
            fxfile::ui::DarkScrollbarLayer::enable(m_hWnd, sPalette);
        else
            fxfile::ui::DarkScrollbarLayer::disable(m_hWnd);
    }

    if (sPaintMessage != 0 && ::IsWindow(m_hWnd) &&
        XPR_IS_TRUE(mDarkScrollbars) &&
        XPR_IS_FALSE(mScrollbarPaintQueued) &&
        XPR_IS_FALSE(mScrollbarPainting) &&
        ((::GetWindowLongPtr(m_hWnd, GWL_STYLE) &
            (WS_VSCROLL | WS_HSCROLL)) != 0) &&
        (aMessage == WM_NCPAINT || aMessage == WM_VSCROLL ||
         aMessage == WM_HSCROLL || aMessage == WM_NCLBUTTONUP ||
         aMessage == WM_NCMOUSEMOVE || aMessage == WM_SIZE))
    {
        if (PostMessage(sPaintMessage))
            mScrollbarPaintQueued = XPR_TRUE;
    }
    return sResult;
}

DWORD TreeCtrlEx::GetExtendedStyle() const
{
    ASSERT(::IsWindow(m_hWnd));
    return (DWORD)::SendMessage(m_hWnd, TVM_GETEXTENDEDSTYLE, (WPARAM)0, 0);
}

DWORD TreeCtrlEx::SetExtendedStyle(DWORD dwExMask, DWORD dwExStyles)
{
    ASSERT(::IsWindow(m_hWnd));
    return (DWORD)::SendMessage(m_hWnd, TVM_SETEXTENDEDSTYLE, (WPARAM)dwExMask, (LPARAM)dwExStyles);
}
