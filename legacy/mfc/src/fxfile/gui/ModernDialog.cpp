//
// Copyright (c) 2026 flyExplorer contributors.
//
// Shared ModernUI foundation for non-resizing MFC dialogs.
//

#include "stdafx.h"
#include "ModernDialog.h"
#include "ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

CModernDialog::CModernDialog(void)
    : super()
    , mModernSurfaceColor(CLR_INVALID)
    , mModernWindowColor(CLR_INVALID)
{
}

CModernDialog::CModernDialog(UINT aResourceId, CWnd *aParentWnd)
    : super(aResourceId, aParentWnd)
    , mModernSurfaceColor(CLR_INVALID)
    , mModernWindowColor(CLR_INVALID)
{
}

CModernDialog::~CModernDialog(void)
{
    if (XPR_IS_NOT_NULL(mModernUIFont.m_hObject))
        mModernUIFont.DeleteObject();
    if (XPR_IS_NOT_NULL(mModernSurfaceBrush.m_hObject))
        mModernSurfaceBrush.DeleteObject();
    if (XPR_IS_NOT_NULL(mModernWindowBrush.m_hObject))
        mModernWindowBrush.DeleteObject();
}

BEGIN_MESSAGE_MAP(CModernDialog, super)
    ON_WM_ERASEBKGND()
    ON_WM_CTLCOLOR()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_DPICHANGED_AFTERPARENT, OnDpiChangedAfterParent)
END_MESSAGE_MAP()

BOOL CModernDialog::OnInitDialog(void)
{
    super::OnInitDialog();
    // Close ComboBoxEx address/history popups when an owned modal opens.
    fxfile::ui::ModernUI::dismissOwnedDropdowns(m_hWnd);
    refreshModernAppearance();
    return TRUE;
}

void CModernDialog::applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont)
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
        XPR_TRUE : XPR_FALSE;

    if (XPR_IS_TRUE(sStandardFontControl) && XPR_IS_NOT_NULL(mModernUIFont.m_hObject))
    {
        HFONT sCurrentFont = reinterpret_cast<HFONT>(aWnd->SendMessage(WM_GETFONT, 0, 0));
        if (XPR_IS_NULL(sCurrentFont) || sCurrentFont == aPreviousFont)
            aWnd->SetFont(&mModernUIFont, XPR_FALSE);
    }

    const xpr_bool_t sExplorerThemeControl =
        (_tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBoxEx32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysListView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0 ||
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTabControl32")) == 0) ?
        XPR_TRUE : XPR_FALSE;

    if (XPR_IS_TRUE(sExplorerThemeControl))
    {
        const fxfile::ui::ThemePalette sPalette =
            fxfile::ui::ModernUI::getPalette();
        if (XPR_IS_TRUE(sPalette.mDark) &&
            XPR_IS_FALSE(sPalette.mHighContrast))
        {
            fxfile::ui::ModernUI::resetControlTheme(aWnd->GetSafeHwnd());
        }
        else
        {
            fxfile::ui::ModernUI::applyExplorerControlTheme(
                aWnd->GetSafeHwnd());
        }
    }

    fxfile::ui::ModernUI::applyDialogControlTheme(aWnd->GetSafeHwnd());

    CWnd *sChild = aWnd->GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CModernDialog::applyModernAppearanceToChildren(HFONT aPreviousFont)
{
    CWnd *sChild = GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CModernDialog::refreshModernAppearance(void)
{
    if (XPR_IS_NULL(m_hWnd))
        return;

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    const HFONT sPreviousFont = reinterpret_cast<HFONT>(SendMessage(WM_GETFONT, 0, 0));

    fxfile::ui::ModernUI::applyWindowFrameTheme(m_hWnd);

    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(fxfile::ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())) &&
        XPR_IS_FALSE(
            fxfile::ui::ModernUI::isSameFont(
                reinterpret_cast<HFONT>(mModernUIFont.GetSafeHandle()),
                sLogFont)))
    {
        if (XPR_IS_NOT_NULL(mModernUIFont.m_hObject))
            mModernUIFont.DeleteObject();
        if (mModernUIFont.CreateFontIndirect(&sLogFont) == TRUE)
            SetFont(&mModernUIFont, XPR_FALSE);
    }

    if (mModernSurfaceColor != sPalette.mCard)
    {
        if (XPR_IS_NOT_NULL(mModernSurfaceBrush.m_hObject))
            mModernSurfaceBrush.DeleteObject();
        mModernSurfaceColor =
            (mModernSurfaceBrush.CreateSolidBrush(sPalette.mCard) == TRUE) ?
            sPalette.mCard : CLR_INVALID;
    }

    if (mModernWindowColor != sPalette.mElevated)
    {
        if (XPR_IS_NOT_NULL(mModernWindowBrush.m_hObject))
            mModernWindowBrush.DeleteObject();
        mModernWindowColor =
            (mModernWindowBrush.CreateSolidBrush(sPalette.mElevated) == TRUE) ?
            sPalette.mElevated : CLR_INVALID;
    }

    applyModernAppearanceToChildren(sPreviousFont);
    RedrawWindow(XPR_NULL, XPR_NULL, RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);
}

BOOL CModernDialog::OnEraseBkgnd(CDC *aDC)
{
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        CRect sClientRect;
        GetClientRect(&sClientRect);
        aDC->FillSolidRect(&sClientRect, sPalette.mCard);
        return TRUE;
    }
    return super::OnEraseBkgnd(aDC);
}

HBRUSH CModernDialog::OnCtlColor(CDC *aDC, CWnd *aWnd, UINT aCtlColor)
{
    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mHighContrast))
        return super::OnCtlColor(aDC, aWnd, aCtlColor);

    aDC->SetTextColor(
        XPR_IS_NOT_NULL(aWnd) && XPR_IS_FALSE(aWnd->IsWindowEnabled()) ?
        sPalette.mSecondaryText : sPalette.mText);

    if (aCtlColor == CTLCOLOR_EDIT || aCtlColor == CTLCOLOR_LISTBOX)
    {
        aDC->SetBkMode(OPAQUE);
        aDC->SetBkColor(sPalette.mElevated);
        if (XPR_IS_NOT_NULL(mModernWindowBrush.m_hObject))
            return (HBRUSH)mModernWindowBrush.GetSafeHandle();
    }
    else if (aCtlColor == CTLCOLOR_STATIC || aCtlColor == CTLCOLOR_BTN || aCtlColor == CTLCOLOR_DLG)
    {
        aDC->SetBkMode(TRANSPARENT);
        aDC->SetBkColor(sPalette.mCard);
        if (XPR_IS_NOT_NULL(mModernSurfaceBrush.m_hObject))
            return (HBRUSH)mModernSurfaceBrush.GetSafeHandle();
    }

    return super::OnCtlColor(aDC, aWnd, aCtlColor);
}

void CModernDialog::OnSettingChange(UINT aFlags, LPCTSTR aSection)
{
    super::OnSettingChange(aFlags, aSection);
    refreshModernAppearance();
}

void CModernDialog::OnSysColorChange(void)
{
    super::OnSysColorChange();
    refreshModernAppearance();
}

LRESULT CModernDialog::OnThemeChanged(WPARAM, LPARAM)
{
    refreshModernAppearance();
    return Default();
}

LRESULT CModernDialog::OnDpiChanged(WPARAM, LPARAM)
{
    refreshModernAppearance();
    return Default();
}

LRESULT CModernDialog::OnDpiChangedAfterParent(WPARAM, LPARAM)
{
    refreshModernAppearance();
    return Default();
}
