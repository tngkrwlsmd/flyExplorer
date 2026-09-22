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

LRESULT CALLBACK ModernGroupBoxSubclassProc(
    HWND aHwnd,
    UINT aMessage,
    WPARAM,
    LPARAM,
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

            ::SetDCBrushColor(sDC, sPalette.mCard);
            ::FillRect(
                sDC,
                &sClientRect,
                static_cast<HBRUSH>(::GetStockObject(DC_BRUSH)));

            RECT sCardRect = sClientRect;
            const xpr_sint_t sTitleOffset =
                ui::ModernUI::scaleForWindow(6, aHwnd);
            sCardRect.top += sTitleOffset;

            const xpr_sint_t sRadius =
                ui::ModernUI::getCardCornerRadius(aHwnd);
            HBRUSH sCardBrush = ::CreateSolidBrush(sPalette.mElevated);
            HPEN sBorderPen = ::CreatePen(PS_SOLID, 1, sPalette.mSeparator);
            HGDIOBJ sOldBrush = ::SelectObject(sDC, sCardBrush);
            HGDIOBJ sOldPen = ::SelectObject(sDC, sBorderPen);
            ::RoundRect(
                sDC,
                sCardRect.left,
                sCardRect.top,
                sCardRect.right,
                sCardRect.bottom,
                sRadius * 2,
                sRadius * 2);
            ::SelectObject(sDC, sOldPen);
            ::SelectObject(sDC, sOldBrush);
            ::DeleteObject(sBorderPen);
            ::DeleteObject(sCardBrush);

            xpr_tchar_t sText[256] = {0};
            ::GetWindowText(aHwnd, sText, XPR_COUNT_OF(sText));
            if (sText[0] != XPR_STRING_LITERAL('\0'))
            {
                HFONT sFont = reinterpret_cast<HFONT>(
                    ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
                HGDIOBJ sOldFont = XPR_NULL;
                if (XPR_IS_NOT_NULL(sFont))
                    sOldFont = ::SelectObject(sDC, sFont);

                ::SetBkMode(sDC, TRANSPARENT);
                ::SetTextColor(sDC, sPalette.mText);

                RECT sTextRect = sClientRect;
                const xpr_sint_t sPadding =
                    ui::ModernUI::getSettingsPanelPadding(aHwnd);
                sTextRect.left += sPadding;
                sTextRect.right -= sPadding;
                ::DrawText(
                    sDC,
                    sText,
                    -1,
                    &sTextRect,
                    DT_LEFT | DT_TOP | DT_SINGLELINE | DT_END_ELLIPSIS);

                if (XPR_IS_NOT_NULL(sOldFont))
                    ::SelectObject(sDC, sOldFont);
            }

            ::EndPaint(aHwnd, &sPaint);
            return 0;
        }

        case WM_THEMECHANGED:
        case WM_SETTINGCHANGE:
        case WM_SYSCOLORCHANGE:
            ::InvalidateRect(aHwnd, XPR_NULL, TRUE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(aHwnd, ModernGroupBoxSubclassProc, aSubclassId);
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
        ui::ModernUI::applyExplorerControlTheme(aWnd->GetSafeHwnd());

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
        }
    }

    CWnd *sChild = aWnd->GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CfgDlg::applyModernAppearanceToChildren(HFONT aPreviousFont)
{
    CWnd *sChild = GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CfgDlg::refreshModernAppearance(void)
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

    ui::ModernUI::applyRoundedWindowRegion(
        GetSafeHwnd(),
        ui::ModernUI::getCardCornerRadius(GetSafeHwnd()));
    applyModernAppearanceToChildren(sPreviousFont);
    RedrawWindow(
        XPR_NULL,
        XPR_NULL,
        RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);
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
    refreshModernAppearance();
    return Default();
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
