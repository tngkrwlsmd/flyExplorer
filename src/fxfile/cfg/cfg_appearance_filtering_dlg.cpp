//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "cfg_appearance_filtering_dlg.h"

#include "../img_list_manager.h"
#include "../option.h"
#include "../gui/ModernUI.h"
#include "../resource.h"

#include <cmath>  // WCAG relative luminance, display-only filter text contrast

#include "filter_set_dlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cfg
{
namespace
{
double ListColorLinearChannel(BYTE aChannel)
{
    const double sChannel = static_cast<double>(aChannel) / 255.0;
    return sChannel <= 0.04045 ?
        sChannel / 12.92 :
        std::pow((sChannel + 0.055) / 1.055, 2.4);
}

double ListColorLuminance(COLORREF aColor)
{
    return 0.2126 * ListColorLinearChannel(GetRValue(aColor)) +
           0.7152 * ListColorLinearChannel(GetGValue(aColor)) +
           0.0722 * ListColorLinearChannel(GetBValue(aColor));
}

COLORREF ResolveVisibleFilterTextColor(
    COLORREF aConfiguredColor,
    COLORREF aBackground,
    const ui::ThemePalette &aPalette)
{
    // The saved per-filter color is data, not a theme foreground.
    // Never modify the model just to make one theme legible.
    if (XPR_IS_TRUE(aPalette.mHighContrast))
        return aPalette.mText;

    const double sForeground = ListColorLuminance(aConfiguredColor);
    const double sBackground = ListColorLuminance(aBackground);
    const double sContrast =
        (max(sForeground, sBackground) + 0.05) /
        (min(sForeground, sBackground) + 0.05);

    // Pale custom colors on a Light elevated row (or black on Dark) can
    // be indistinguishable. Use the current palette text only for
    // insufficient on-screen contrast; keep the persisted custom color.
    return sContrast >= 4.5 ?
        aConfiguredColor : aPalette.mText;
}

COLORREF MutedFilterSelectionColor(
    const ui::ThemePalette &aPalette, xpr_bool_t aFocused)
{
    // Selected filtering rules should be discoverable, not a solid blue
    // highlight. High Contrast continues to use the native list renderer.
    const xpr_sint_t sWeight = XPR_IS_TRUE(aFocused) ? 12 : 6;
    const COLORREF sBase = aPalette.mElevated;
    const COLORREF sAccent = aPalette.mSelection;
    return RGB(
        (GetRValue(sBase) * (100 - sWeight) +
            GetRValue(sAccent) * sWeight) / 100,
        (GetGValue(sBase) * (100 - sWeight) +
            GetGValue(sAccent) * sWeight) / 100,
        (GetBValue(sBase) * (100 - sWeight) +
            GetBValue(sAccent) * sWeight) / 100);
}

xpr_bool_t DrawMutedFilterSelection(
    CListCtrl &aList, NMLVCUSTOMDRAW &aDraw, const FilterItem &aFilter,
    const ui::ThemePalette &aPalette)
{
    // Keep native selection state, keyboard navigation and accessibility.
    // Draw only the selected pixels. Never toggle LVIS_SELECTED in paint.
    const xpr_sint_t sIndex =
        static_cast<xpr_sint_t>(aDraw.nmcd.dwItemSpec);
    CRect sRow;
    CRect sLabel;
    CRect sIcon;
    CRect sExtensions;
    if (aList.GetItemRect(sIndex, &sRow, LVIR_BOUNDS) == FALSE ||
        aList.GetItemRect(sIndex, &sLabel, LVIR_LABEL) == FALSE ||
        aList.GetSubItemRect(sIndex, 1, LVIR_BOUNDS, sExtensions) == FALSE)
        return XPR_FALSE;

    const xpr_bool_t sHaveIconRect =
        aList.GetItemRect(sIndex, &sIcon, LVIR_ICON) != FALSE ?
        XPR_TRUE : XPR_FALSE;

    CRect sClient;
    aList.GetClientRect(&sClient);
    CRect sSelected(sRow);
    sSelected.right = max(sSelected.right, sExtensions.right);
    sSelected.IntersectRect(sSelected, sClient);
    if (sSelected.IsRectEmpty())
        return XPR_FALSE;

    const xpr_bool_t sFocused =
        ::GetFocus() == aList.GetSafeHwnd() ? XPR_TRUE : XPR_FALSE;
    const COLORREF sFill = MutedFilterSelectionColor(
        aPalette, sFocused);
    const COLORREF sText = ResolveVisibleFilterTextColor(
        aFilter.mColor, sFill, aPalette);
    HDC sDC = aDraw.nmcd.hdc;
    const int sSaved = ::SaveDC(sDC);
    if (sSaved == 0)
        return XPR_FALSE;

    ::IntersectClipRect(
        sDC, sSelected.left, sSelected.top,
        sSelected.right, sSelected.bottom);
    HBRUSH sBrush = ::CreateSolidBrush(sFill);
    if (sBrush != NULL)
    {
        ::FillRect(sDC, &sSelected, sBrush);
        ::DeleteObject(sBrush);
    }
    const HFONT sFont = reinterpret_cast<HFONT>(
        aList.SendMessage(WM_GETFONT));
    if (sFont != NULL)
        ::SelectObject(sDC, sFont);
    ::SetBkMode(sDC, TRANSPARENT);
    ::SetTextColor(sDC, sText);

    const xpr_sint_t sInset = max(
        3, ui::ModernUI::scaleForWindow(4, aList.GetSafeHwnd()));
    CImageList *sImages = aList.GetImageList(LVSIL_SMALL);
    if (sImages != NULL && aFilter.mIconIndex >= 0 &&
        XPR_IS_TRUE(sHaveIconRect))
    {
        CDC *sPaintDC = CDC::FromHandle(sDC);
        sImages->Draw(
            sPaintDC, aFilter.mIconIndex,
            CPoint(sIcon.left, sIcon.top), ILD_TRANSPARENT);
    }

    // Use native label/subitem coordinates even when horizontally scrolled.
    sLabel.right = min(sExtensions.left, sLabel.right);
    sLabel.right = max(sLabel.left, sLabel.right - sInset);
    sExtensions.left += sInset;
    sExtensions.right -= sInset;
    const xpr_uint_t sFormat =
        DT_SINGLELINE | DT_VCENTER | DT_END_ELLIPSIS | DT_NOPREFIX | DT_LEFT;
    if (sLabel.right > sLabel.left)
        ::DrawText(sDC, aFilter.mName.c_str(), -1, &sLabel, sFormat);
    if (sExtensions.right > sExtensions.left)
        ::DrawText(sDC, aFilter.mExts.c_str(), -1, &sExtensions, sFormat);

    // A thin neutral focus cue replaces the native bright highlight.
    if (XPR_IS_TRUE(sFocused) &&
        (aDraw.nmcd.uItemState & CDIS_FOCUS) != 0)
    {
        CRect sOutline(sSelected);
        sOutline.DeflateRect(0, 0, 1, 1);
        HBRUSH sBorder = ::CreateSolidBrush(aPalette.mBorder);
        if (sBorder != NULL)
        {
            ::FrameRect(sDC, &sOutline, sBorder);
            ::DeleteObject(sBorder);
        }
    }
    ::RestoreDC(sDC, sSaved);
    return XPR_TRUE;
}

} // namespace

CfgAppearanceFilteringDlg::CfgAppearanceFilteringDlg(void)
    : super(IDD_CFG_APPEARANCE_FILTERING, XPR_NULL)
{
}

void CfgAppearanceFilteringDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_CFG_FILTER_LIST, mListCtrl);
}

BEGIN_MESSAGE_MAP(CfgAppearanceFilteringDlg, super)
    ON_WM_DESTROY()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_BN_CLICKED(IDC_CFG_FILTER_ADD,              OnListAdd)
    ON_BN_CLICKED(IDC_CFG_FILTER_MODIFY,           OnListModify)
    ON_BN_CLICKED(IDC_CFG_FILTER_DELETE,           OnListDelete)
    ON_BN_CLICKED(IDC_CFG_FILTER_ITEM_UP,          OnItemUp)
    ON_BN_CLICKED(IDC_CFG_FILTER_ITEM_DOWN,        OnItemDown)
    ON_BN_CLICKED(IDC_CFG_FILTER_DEFAULT,          OnDefault)
    ON_NOTIFY(NM_CUSTOMDRAW,    IDC_CFG_FILTER_LIST, OnCustomDrawList)
    ON_NOTIFY(LVN_GETDISPINFO,  IDC_CFG_FILTER_LIST, OnGetdispinfoList)
    ON_NOTIFY(LVN_DELETEITEM,   IDC_CFG_FILTER_LIST, OnDeleteitemList)
    ON_NOTIFY(LVN_ITEMACTIVATE, IDC_CFG_FILTER_LIST, OnItemActivateList)
END_MESSAGE_MAP()

xpr_bool_t CfgAppearanceFilteringDlg::OnInitDialog(void) 
{
    super::OnInitDialog();

    // disable apply button event
    addIgnoreApply(IDC_CFG_FILTER_ADD);
    addIgnoreApply(IDC_CFG_FILTER_MODIFY);
    addIgnoreApply(IDC_CFG_FILTER_DELETE);
    addIgnoreApply(IDC_CFG_FILTER_ITEM_UP);
    addIgnoreApply(IDC_CFG_FILTER_ITEM_DOWN);
    addIgnoreApply(IDC_CFG_FILTER_DEFAULT);

    mListCtrl.SetExtendedStyle(mListCtrl.GetExtendedStyle() | LVS_EX_FULLROWSELECT);
    mListCtrl.InsertColumn(0, gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.list.column.name")),      LVCFMT_LEFT, 100, -1);
    mListCtrl.InsertColumn(1, gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.list.column.extension")), LVCFMT_LEFT, 245, -1);

    mListCtrl.SetImageList(&SingletonManager::get<ImgListManager>().mCustomImgList16, LVSIL_SMALL);

    // The initial dark-border decision needs its own local palette. Native
    // list text/background colors are handled by refreshFilteringListColors.
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_TRUE(sPalette.mDark) &&
        XPR_IS_FALSE(sPalette.mHighContrast))
    {
        mListCtrl.ModifyStyle(WS_BORDER, 0);
        mListCtrl.ModifyStyleEx(
            WS_EX_CLIENTEDGE,
            0,
            SWP_FRAMECHANGED);
    }

    HWND sHeaderHwnd = ListView_GetHeader(mListCtrl.GetSafeHwnd());
    if (XPR_IS_NOT_NULL(sHeaderHwnd) &&
        XPR_IS_NULL(mHeaderCtrl.m_hWnd) &&
        mHeaderCtrl.SubclassWindow(sHeaderHwnd) != FALSE)
    {
        mHeaderCtrl.initHeader(XPR_FALSE);
    }

    refreshFilteringListColors();

    xpr_tchar_t sText[0xff] = {0};
    _stprintf(sText, gApp.loadFormatString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.label.max_filter"), XPR_STRING_LITERAL("%d")), MAX_FILTER);
    SetDlgItemText(IDC_CFG_FILTER_LABEL_MAX_FILTER, sText);

    SetDlgItemText(IDC_CFG_FILTER_LABEL_LIST,       gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.label.list")));
    SetDlgItemText(IDC_CFG_FILTER_DEFAULT,          gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.default")));
    SetDlgItemText(IDC_CFG_FILTER_ITEM_UP,          gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.move_up")));
    SetDlgItemText(IDC_CFG_FILTER_ITEM_DOWN,        gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.move_down")));
    SetDlgItemText(IDC_CFG_FILTER_ADD,              gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.add")));
    SetDlgItemText(IDC_CFG_FILTER_MODIFY,           gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.modify")));
    SetDlgItemText(IDC_CFG_FILTER_DELETE,           gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.button.delete")));

    return XPR_TRUE;
}

void CfgAppearanceFilteringDlg::refreshFilteringListColors(void)
{
    if (::IsWindow(mListCtrl.GetSafeHwnd()) == FALSE)
        return;

    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    const COLORREF sBackground =
        XPR_IS_TRUE(sPalette.mHighContrast) ?
        sPalette.mWindow : sPalette.mElevated;

    // The inherited settings-theme refresh re-associates child controls,
    // but it must also refresh native ListView text/background values.
    mListCtrl.SetBkColor(sBackground);
    mListCtrl.SetTextBkColor(sBackground);
    mListCtrl.SetTextColor(sPalette.mText);
    mListCtrl.RedrawWindow(
        XPR_NULL,
        XPR_NULL,
        RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN);

    if (::IsWindow(mHeaderCtrl.GetSafeHwnd()) != FALSE)
        mHeaderCtrl.Invalidate(XPR_FALSE);
}

void CfgAppearanceFilteringDlg::OnSettingChange(
    xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    super::OnSettingChange(aFlags, aSection);
    refreshFilteringListColors();
}

void CfgAppearanceFilteringDlg::OnSysColorChange(void)
{
    super::OnSysColorChange();
    refreshFilteringListColors();
}

LRESULT CfgAppearanceFilteringDlg::OnThemeChanged(
    WPARAM aWParam, LPARAM aLParam)
{
    const LRESULT sResult = super::OnThemeChanged(aWParam, aLParam);
    refreshFilteringListColors();
    return sResult;
}

void CfgAppearanceFilteringDlg::OnDestroy(void)
{
    mImageList.DeleteImageList();

    super::OnDestroy();
}

void CfgAppearanceFilteringDlg::onInit(const Option::Config &aConfig)
{
    FileFilterMgr &sFileFilterMgr = FileFilterMgr::instance();

    FilterItem *sFilterItem;
    FilterItem *sFilterItem2;

    xpr_sint_t i;
    xpr_sint_t sIndex;
    xpr_sint_t sCount;
    LVITEM sLvItem = {0};

    sIndex = 0;

    sCount = sFileFilterMgr.getCount();
    for (i = 0; i < sCount; ++i)
    {
        sFilterItem = sFileFilterMgr.getFilter(i);
        if (sFilterItem == XPR_NULL)
            continue;

        sFilterItem2 = new FilterItem;
        *sFilterItem2 = *sFilterItem;

        addFilterItem(sFilterItem2);

        sIndex++;
    }
}

void CfgAppearanceFilteringDlg::onApply(Option::Config &aConfig)
{
    FileFilterMgr &sFileFilterMgr = FileFilterMgr::instance();

    xpr_sint_t i;
    xpr_sint_t sCount;
    FilterItem *sFilterItem;
    FilterItem *sFilterItem2;

    sFileFilterMgr.clear();

    sCount = mListCtrl.GetItemCount();
    for (i = 0; i < sCount; ++i)
    {
        sFilterItem = (FilterItem *)mListCtrl.GetItemData(i);
        if (sFilterItem == XPR_NULL)
            continue;

        sFilterItem2 = new FilterItem;
        *sFilterItem2 = *sFilterItem;

        sFileFilterMgr.addFilter(sFilterItem2);
    }
}

void CfgAppearanceFilteringDlg::OnGetdispinfoList(NMHDR* pNMHDR, LRESULT* pResult)
{
    LV_DISPINFO* pDispInfo = (LV_DISPINFO*)pNMHDR;
    *pResult = 0;

    LPLVITEM sLvItem = &pDispInfo->item;

    FilterItem *sFilterItem = (FilterItem *)sLvItem->lParam;
    if (sFilterItem == XPR_NULL)
        return;

    if (XPR_TEST_BITS(sLvItem->mask, LVIF_TEXT))
    {
        switch (sLvItem->iSubItem)
        {
        case 0: _tcscpy(sLvItem->pszText, sFilterItem->mName.c_str()); break;
        case 1: _tcscpy(sLvItem->pszText, sFilterItem->mExts.c_str()); break;
        }
    }

    if (XPR_TEST_BITS(sLvItem->mask, LVIF_IMAGE))
    {
        sLvItem->iImage = sFilterItem->mIconIndex;
    }
}

void CfgAppearanceFilteringDlg::OnCustomDrawList(NMHDR* pNMHDR, LRESULT* pResult) 
{
    NMLVCUSTOMDRAW* pLVCD = reinterpret_cast<NMLVCUSTOMDRAW *>(pNMHDR);
    *pResult = CDRF_DODEFAULT;

    if (pLVCD->nmcd.dwDrawStage == CDDS_PREPAINT)
    {
        *pResult = CDRF_NOTIFYITEMDRAW;
    }
    else if (pLVCD->nmcd.dwDrawStage == CDDS_ITEMPREPAINT)
    {
        const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
        const COLORREF sListBackground =
            XPR_IS_TRUE(sPalette.mHighContrast) ?
            sPalette.mWindow :
            sPalette.mElevated;

        pLVCD->clrTextBk = sListBackground;

        FilterItem *sFilterItem = (FilterItem *)pLVCD->nmcd.lItemlParam;
        COLORREF sFilterTextColor =
            XPR_IS_NOT_NULL(sFilterItem) ?
            sFilterItem->mColor :
            sPalette.mText;

        // Per-filter RGB is user data and may have been chosen for
        // the opposite theme. Contrast-check against the *actual* row
        // background every paint, rather than special-casing only black
        // in Dark mode (which left white/pale text invisible in Light).
        sFilterTextColor = ResolveVisibleFilterTextColor(
            sFilterTextColor, sListBackground, sPalette);

        // Native ListView selection ignores clrTextBk and repaints a strong
        // blue highlight. In normal themes, draw subtle rows ourselves while
        // retaining native selection state and the High Contrast OS renderer.
        if ((pLVCD->nmcd.uItemState & CDIS_SELECTED) != 0 &&
            XPR_IS_FALSE(sPalette.mHighContrast) &&
            XPR_IS_NOT_NULL(sFilterItem) &&
            XPR_IS_TRUE(DrawMutedFilterSelection(
                mListCtrl, *pLVCD, *sFilterItem, sPalette)))
        {
            *pResult = CDRF_SKIPDEFAULT;
            return;
        }

        if ((pLVCD->nmcd.uItemState & CDIS_SELECTED) != 0)
        {
            const xpr_bool_t sFocused =
                (::GetFocus() == mListCtrl.GetSafeHwnd()) ?
                XPR_TRUE :
                XPR_FALSE;
            // An unfocused selected row has a neutral, pale inactive
            // background in Light mode. COLOR_HIGHLIGHTTEXT (usually white)
            // belongs only on the *active* highlight, not that surface.
            pLVCD->clrText =
                XPR_IS_TRUE(sFocused) ?
                sPalette.mSelectionText :
                sPalette.mText;
            pLVCD->clrTextBk =
                XPR_IS_TRUE(sFocused) ?
                sPalette.mSelection :
                sPalette.mInactiveSelection;
        }
        else
        {
            pLVCD->clrText = sFilterTextColor;
        }

        *pResult = CDRF_DODEFAULT;
    }
}

void CfgAppearanceFilteringDlg::OnListAdd(void) 
{
    xpr_sint_t i;
    xpr_sint_t sCount;
    FilterItem *sFilterItem;

    sCount = mListCtrl.GetItemCount();
    if (sCount >= MAX_FILTER)
    {
        xpr_tchar_t sMsg[0xff] = {0};
        _stprintf(sMsg, gApp.loadFormatString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.msg.excess_max_count"), XPR_STRING_LITERAL("%d")), MAX_FILTER);
        MessageBox(sMsg, XPR_NULL, MB_OK | MB_ICONSTOP);
        return;
    }

    FilterSetDlg sDlg;

    for (i = 0; i < sCount; ++i)
    {
        sFilterItem = (FilterItem *)mListCtrl.GetItemData(i);
        if (sFilterItem == XPR_NULL)
            continue;

        sDlg.addName(sFilterItem->mName.c_str());
    }

    if (sDlg.DoModal() != IDOK)
        return;

    sFilterItem = new FilterItem;
    *sFilterItem = *sDlg.getFilter();

    xpr_sint_t sIndex;
    sIndex = addFilterItem(sFilterItem);

    selectItem(sIndex);

    setModified();
}

void CfgAppearanceFilteringDlg::OnListModify(void) 
{
    xpr_sint_t i;
    xpr_sint_t sIndex;
    xpr_sint_t sCount;
    FilterItem *sFilterItem;
    FilterItem *sFilterItem2;

    sIndex = mListCtrl.GetSelectionMark();
    if (sIndex < 0)
        return;

    sFilterItem = (FilterItem *)mListCtrl.GetItemData(sIndex);
    if (sFilterItem == XPR_NULL)
        return;

    FilterSetDlg sDlg(sFilterItem);

    sCount = mListCtrl.GetItemCount();
    for (i = 0; i < sCount; ++i)
    {
        if (i == sIndex)
            continue;

        sFilterItem2 = (FilterItem *)mListCtrl.GetItemData(i);
        if (sFilterItem2 == XPR_NULL)
            continue;

        sDlg.addName(sFilterItem2->mName.c_str());
    }

    if (sDlg.DoModal() != IDOK)
        return;

    *sFilterItem = *sDlg.getFilter();

    mListCtrl.Invalidate(XPR_FALSE);
    mListCtrl.UpdateWindow();

    selectItem(sIndex);

    setModified();
}

void CfgAppearanceFilteringDlg::OnListDelete(void) 
{
    xpr_sint_t sIndex = mListCtrl.GetSelectionMark();
    if (sIndex < 0)
        return;

    if (sIndex == 0 || sIndex == 1)
        return;

    const xpr_tchar_t *sMsg = gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.msg.confirm_delete"));
    xpr_sint_t sMsgId = MessageBox(sMsg, XPR_NULL, MB_YESNO | MB_ICONQUESTION | MB_DEFBUTTON2);
    if (sMsgId == IDNO)
        return;

    mListCtrl.DeleteItem(sIndex);

    xpr_sint_t sCount = mListCtrl.GetItemCount();
    if (sIndex == sCount)
        sIndex = sCount-1;

    selectItem(sIndex);

    setModified();
}

void CfgAppearanceFilteringDlg::OnItemUp(void) 
{
    xpr_sint_t sIndex = mListCtrl.GetSelectionMark();
    if (sIndex < 0)
        return;

    if (sIndex == 0 || sIndex == 1 || sIndex == 2)
        return;

    mListCtrl.SetRedraw(XPR_FALSE);

    FilterItem *sFilterItem = (FilterItem *)mListCtrl.GetItemData(sIndex);
    mListCtrl.SetItemData(sIndex, 0);
    mListCtrl.DeleteItem(sIndex);
    sIndex--;

    insertFilterItem(sIndex, sFilterItem);
    selectItem(sIndex);

    mListCtrl.SetRedraw();

    setModified();
}

void CfgAppearanceFilteringDlg::OnItemDown(void) 
{
    xpr_sint_t sIndex = mListCtrl.GetSelectionMark();
    if (sIndex < 0)
        return;

    xpr_sint_t sCount = mListCtrl.GetItemCount();
    if (sIndex == 0 || sIndex == 1 || sIndex == (sCount-1))
        return;

    mListCtrl.SetRedraw(XPR_FALSE);

    FilterItem *sFilterItem = (FilterItem *)mListCtrl.GetItemData(sIndex);
    mListCtrl.SetItemData(sIndex, 0);
    mListCtrl.DeleteItem(sIndex);
    sIndex++;

    insertFilterItem(sIndex, sFilterItem);
    selectItem(sIndex);

    mListCtrl.SetRedraw();

    setModified();
}

xpr_sint_t CfgAppearanceFilteringDlg::insertFilterItem(xpr_sint_t aIndex, FilterItem *aFilterItem)
{
    LVITEM sLvItem = {0};
    sLvItem.mask     = LVIF_TEXT | LVIF_IMAGE | LVIF_PARAM;
    sLvItem.iItem    = aIndex;
    sLvItem.iSubItem = 0;
    sLvItem.iImage   = I_IMAGECALLBACK;
    sLvItem.pszText  = LPSTR_TEXTCALLBACK;
    sLvItem.lParam   = (LPARAM)aFilterItem;

    return mListCtrl.InsertItem(&sLvItem);
}

xpr_sint_t CfgAppearanceFilteringDlg::addFilterItem(FilterItem *aFilterItem)
{
    xpr_sint_t sIndex;
    sIndex = mListCtrl.GetItemCount();

    return insertFilterItem(sIndex, aFilterItem);
}

void CfgAppearanceFilteringDlg::selectItem(xpr_sint_t aIndex)
{
    if (aIndex < 0 || aIndex >= mListCtrl.GetItemCount())
        return;

    // LVS_SINGLESEL is a user-interaction contract; programmatic state writes
    // can otherwise leave stale selected rows behind after reorder/default
    // operations. Clear selection/focus explicitly before selecting one row.
    mListCtrl.SetItemState(
        -1,
        0,
        LVIS_FOCUSED | LVIS_SELECTED);
    mListCtrl.SetFocus();
    mListCtrl.EnsureVisible(aIndex, XPR_TRUE);
    mListCtrl.SetSelectionMark(aIndex);
    mListCtrl.SetItemState(
        aIndex,
        LVIS_FOCUSED | LVIS_SELECTED,
        LVIS_FOCUSED | LVIS_SELECTED);
}

void CfgAppearanceFilteringDlg::OnDeleteitemList(NMHDR* pNMHDR, LRESULT* pResult) 
{
    NM_LISTVIEW* pNMListView = (NM_LISTVIEW*)pNMHDR;
    *pResult = 0;

    FilterItem *sFilterItem = (FilterItem *)pNMListView->lParam;
    XPR_SAFE_DELETE(sFilterItem);
}

void CfgAppearanceFilteringDlg::OnItemActivateList(NMHDR* pNMHDR, LRESULT* pResult)
{
    NM_LISTVIEW* pNMListView = (NM_LISTVIEW*)pNMHDR;
    *pResult = 0;

    OnListModify();
}

xpr_bool_t CfgAppearanceFilteringDlg::PreTranslateMessage(MSG* pMsg) 
{
    if (pMsg->message == WM_KEYDOWN && pMsg->hwnd == GetDlgItem(IDC_CFG_FILTER_LIST)->m_hWnd)
    {
        switch (pMsg->wParam)
        {
        case VK_UP:
            if (GetKeyState(VK_CONTROL) < 0)
            {
                OnItemUp();
                return XPR_TRUE;
            }
            break;

        case VK_DOWN:
            if (GetKeyState(VK_CONTROL) < 0)
            {
                OnItemDown();
                return XPR_TRUE;
            }
            break;

        case VK_INSERT:
            OnListAdd();
            return XPR_TRUE;
            break;

        case VK_RETURN:
            if (GetKeyState(VK_CONTROL) < 0)
            {
                OnListModify();
                return XPR_TRUE;
            }
            break;

        case VK_DELETE:
            OnListDelete();
            return XPR_TRUE;
            break;
        }
    }

    return super::PreTranslateMessage(pMsg);
}

void CfgAppearanceFilteringDlg::OnDefault(void)
{
    const xpr_tchar_t *sMsg = gApp.loadString(XPR_STRING_LITERAL("popup.cfg.body.appearance.filter.msg.confirm_init"));
    xpr_sint_t sMsgId = MessageBox(sMsg, XPR_NULL, MB_YESNO | MB_ICONQUESTION);
    if (sMsgId == IDNO)
        return;

    CWaitCursor sWaitCursor;

    mListCtrl.DeleteAllItems();

    FileFilter sFileFilter;
    sFileFilter.initDefault();

    xpr_sint_t i, sCount;
    FilterItem *sFilterItem;
    FilterItem *sFilterItem2;

    sCount = sFileFilter.getCount();
    for (i = 0; i < sCount; ++i)
    {
        sFilterItem = sFileFilter.getFilter(i);

        sFilterItem2 = new FilterItem;
        *sFilterItem2 = *sFilterItem;

        addFilterItem(sFilterItem2);
    }

    if (mListCtrl.GetItemCount() > 0)
        selectItem(0);

    mListCtrl.Invalidate(XPR_FALSE);
    mListCtrl.UpdateWindow();

    setModified();
}
} // namespace cfg
} // namespace fxfile
