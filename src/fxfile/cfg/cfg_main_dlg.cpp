//
// Copyright (c) 2001-2014 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "cfg_main_dlg.h"

#include "../gui/ModernUI.h"

#include "../resource.h"
#include "../option_manager.h"

#include "conf_dir.h"
#include "cfg_general_dlg.h"
#include "cfg_general_startup_dlg.h"
#include "cfg_appearance_dlg.h"
#include "cfg_appearance_layout_dlg.h"
#include "cfg_appearance_font_dlg.h"
#include "cfg_appearance_color_dlg.h"
#include "cfg_appearance_file_list_dlg.h"
#include "cfg_appearance_folder_layout_dlg.h"
#include "cfg_appearance_filtering_dlg.h"
#include "cfg_appearance_thumbnail_dlg.h"
#include "cfg_appearance_history_dlg.h"
#include "cfg_appearance_size_format_dlg.h"
#include "cfg_appearance_folder_tree_dlg.h"
#include "cfg_appearance_tab_dlg.h"
#include "cfg_appearance_language_dlg.h"
#include "cfg_func_dlg.h"
#include "cfg_func_bookmark_dlg.h"
#include "cfg_func_rename_dlg.h"
#include "cfg_func_refresh_dlg.h"
#include "cfg_func_drag_dlg.h"
#include "cfg_func_program_ass_dlg.h"
#include "cfg_func_file_scrap_dlg.h"
#include "cfg_func_file_op_dlg.h"
#include "cfg_adv_dlg.h"
#include "cfg_adv_conf_dir_dlg.h"
#include "cfg_adv_hotkey_dlg.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
namespace cfg
{
namespace
{
const UINT_PTR kModernCfgButtonSubclassId = 0x46474346; // 'FGCF'

LRESULT CALLBACK ModernCfgButtonSubclassProc(
    HWND aHwnd,
    UINT aMessage,
    WPARAM,
    LPARAM,
    UINT_PTR aSubclassId,
    DWORD_PTR)
{
    switch (aMessage)
    {
        case WM_MOUSEMOVE:
        {
            TRACKMOUSEEVENT sTrack = {0};
            sTrack.cbSize = sizeof(sTrack);
            sTrack.dwFlags = TME_LEAVE;
            sTrack.hwndTrack = aHwnd;
            ::TrackMouseEvent(&sTrack);
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;
        }

        case WM_MOUSELEAVE:
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;

        case WM_PAINT:
        {
            const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
            if (XPR_IS_TRUE(sPalette.mHighContrast))
                break;

            PAINTSTRUCT sPaint = {0};
            HDC sDC = ::BeginPaint(aHwnd, &sPaint);
            if (XPR_IS_NULL(sDC))
                return 0;

            RECT sRect = {0};
            ::GetClientRect(aHwnd, &sRect);

            POINT sCursor = {0};
            ::GetCursorPos(&sCursor);
            RECT sWindowRect = {0};
            ::GetWindowRect(aHwnd, &sWindowRect);
            const xpr_bool_t sHot =
                ::PtInRect(&sWindowRect, sCursor) != FALSE ?
                XPR_TRUE :
                XPR_FALSE;

            const LRESULT sState = ::SendMessage(aHwnd, BM_GETSTATE, 0, 0);
            const xpr_bool_t sPressed =
                (sState & BST_PUSHED) != 0 ? XPR_TRUE : XPR_FALSE;
            const xpr_bool_t sFocused =
                (::GetFocus() == aHwnd) ? XPR_TRUE : XPR_FALSE;
            const xpr_bool_t sEnabled =
                ::IsWindowEnabled(aHwnd) != FALSE ? XPR_TRUE : XPR_FALSE;
            const xpr_bool_t sPrimary =
                ::GetDlgCtrlID(aHwnd) == IDOK ? XPR_TRUE : XPR_FALSE;

            COLORREF sFill = sPalette.mElevated;
            COLORREF sText = sPalette.mText;
            COLORREF sBorder = sPalette.mBorder;

            if (XPR_IS_FALSE(sEnabled))
            {
                sFill = sPalette.mCard;
                sText = sPalette.mSecondaryText;
            }
            else if (XPR_IS_TRUE(sPressed))
            {
                sFill = sPalette.mPressed;
            }
            else if (XPR_IS_TRUE(sPrimary))
            {
                sFill = sPalette.mSelection;
                sText = sPalette.mSelectionText;
                sBorder = sPalette.mSelection;
            }
            else if (XPR_IS_TRUE(sHot))
            {
                sFill = sPalette.mHover;
            }

            if (XPR_IS_TRUE(sFocused))
                sBorder = sPalette.mFocus;

            HBRUSH sBrush = ::CreateSolidBrush(sFill);
            HPEN sPen = ::CreatePen(PS_SOLID, 1, sBorder);
            HGDIOBJ sOldBrush = ::SelectObject(sDC, sBrush);
            HGDIOBJ sOldPen = ::SelectObject(sDC, sPen);

            const xpr_sint_t sRadius =
                ui::ModernUI::getControlCornerRadius(aHwnd);
            ::RoundRect(
                sDC,
                sRect.left,
                sRect.top,
                sRect.right,
                sRect.bottom,
                sRadius * 2,
                sRadius * 2);

            ::SelectObject(sDC, sOldPen);
            ::SelectObject(sDC, sOldBrush);
            ::DeleteObject(sPen);
            ::DeleteObject(sBrush);

            xpr_tchar_t sLabel[128] = {0};
            ::GetWindowText(aHwnd, sLabel, XPR_COUNT_OF(sLabel));
            HFONT sFont = reinterpret_cast<HFONT>(
                ::SendMessage(aHwnd, WM_GETFONT, 0, 0));
            HGDIOBJ sOldFont = XPR_NULL;
            if (XPR_IS_NOT_NULL(sFont))
                sOldFont = ::SelectObject(sDC, sFont);

            ::SetBkMode(sDC, TRANSPARENT);
            ::SetTextColor(sDC, sText);
            ::DrawText(
                sDC,
                sLabel,
                -1,
                &sRect,
                DT_CENTER | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);

            if (XPR_IS_NOT_NULL(sOldFont))
                ::SelectObject(sDC, sOldFont);

            ::EndPaint(aHwnd, &sPaint);
            return 0;
        }

        case WM_ENABLE:
        case WM_SETFOCUS:
        case WM_KILLFOCUS:
            ::InvalidateRect(aHwnd, XPR_NULL, FALSE);
            break;

        case WM_NCDESTROY:
            ::RemoveWindowSubclass(
                aHwnd,
                ModernCfgButtonSubclassProc,
                aSubclassId);
            break;

        default:
            break;
    }

    return ::DefSubclassProc(aHwnd, aMessage, aWParam, aLParam);
}

void InstallModernCfgButton(HWND aHwnd)
{
    if (XPR_IS_NULL(aHwnd) || ::IsWindow(aHwnd) == FALSE)
        return;

    ::SetWindowSubclass(
        aHwnd,
        ModernCfgButtonSubclassProc,
        kModernCfgButtonSubclassId,
        0);
}
} // namespace

xpr_sint_t CfgMainDlg::mLastShowCfg = 0;

CfgMainDlg::CfgMainDlg(xpr_sint_t aInitShowCfg)
    : super(IDD_CFG_MAIN, XPR_NULL)
    , mInitShowCfg(aInitShowCfg)
    , mShowCfg(-1)
    , mChanging(XPR_FALSE)
    , mSurfaceColor(CLR_INVALID)
    , mWindowColor(CLR_INVALID)
{
    if (mInitShowCfg == -1)
        mInitShowCfg = mLastShowCfg;
}

void CfgMainDlg::DoDataExchange(CDataExchange* pDX)
{
    super::DoDataExchange(pDX);
    DDX_Control(pDX, IDC_CFG_TREE, mTreeCtrl);
}

BEGIN_MESSAGE_MAP(CfgMainDlg, super)
    ON_WM_CTLCOLOR()
    ON_WM_DESTROY()
    ON_WM_ERASEBKGND()
    ON_WM_SETTINGCHANGE()
    ON_WM_SYSCOLORCHANGE()
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_NOTIFY(TVN_SELCHANGED, IDC_CFG_TREE, OnSelchangedTree)
    ON_NOTIFY(NM_CUSTOMDRAW, IDC_CFG_TREE, OnTreeCustomDraw)
    ON_BN_CLICKED(IDC_CFG_DEFAULT, OnDefault)
    ON_BN_CLICKED(IDC_CFG_APPLY,   OnApply)
END_MESSAGE_MAP()

xpr_bool_t CfgMainDlg::OnInitDialog(void) 
{
    super::OnInitDialog();

    refreshModernAppearance();
    mTreeCtrl.enableVistaEnhanced(XPR_TRUE);

    // Use a roomy, borderless navigation row similar to Windows 11 settings
    // surfaces while preserving the existing tree hierarchy and icons.
    const xpr_sint_t sModernItemHeight =
        ui::ModernUI::getSettingsNavRowHeight(GetSafeHwnd());
    if (mTreeCtrl.GetItemHeight() < sModernItemHeight)
        mTreeCtrl.SetItemHeight(sModernItemHeight);
    mTreeCtrl.SetIndent(ui::ModernUI::scaleForWindow(20, GetSafeHwnd()));

    CBitmap sBitmap;
    sBitmap.LoadBitmap(IDB_CONFIG_TREE);
    mImgList.Create(16, 16, ILC_COLORDDB | ILC_MASK, 18, 18);
    mImgList.Add(&sBitmap, RGB(255,0,255));
    sBitmap.DeleteObject();

    mTreeCtrl.SetImageList(&mImgList, TVSIL_NORMAL);

    InstallModernCfgButton(GetDlgItem(IDOK)->GetSafeHwnd());
    InstallModernCfgButton(GetDlgItem(IDCANCEL)->GetSafeHwnd());
    InstallModernCfgButton(GetDlgItem(IDC_CFG_APPLY)->GetSafeHwnd());
    InstallModernCfgButton(GetDlgItem(IDC_CFG_DEFAULT)->GetSafeHwnd());

    refreshModernAppearance();

    // copy config
    gOpt->copyConfig(mNewConfig);

    // initialize configuration dialog
    xpr_sint_t sIndex;
    sIndex = addCfgItem( 0,     -1, new CfgGeneralDlg,                gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.general")));
    /*    */ addCfgItem(31, sIndex, new CfgGeneralStartupDlg,         gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.general.startup")));
    sIndex = addCfgItem(18,     -1, new CfgAppearanceDlg,             gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance")));
    /*    */ addCfgItem(29, sIndex, new CfgAppearanceLayoutDlg,       gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.layout")));
    /*    */ addCfgItem(30, sIndex, new CfgAppearanceFontDlg,         gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.font")));
    /*    */ addCfgItem(28, sIndex, new CfgAppearanceColorDlg,        gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.color")));
    /*    */ addCfgItem(12, sIndex, new CfgAppearanceFileListDlg,     gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.file_list")));
    /*    */ addCfgItem(20, sIndex, new CfgAppearanceFolderLayoutDlg, gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.folder_layout")));
    /*    */ addCfgItem(11, sIndex, new CfgAppearanceFilteringDlg,    gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.filtering")));
    /*    */ addCfgItem( 5, sIndex, new CfgAppearanceThumbnailDlg,    gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.thumbnail")));
    /*    */ addCfgItem(25, sIndex, new CfgAppearanceHistoryDlg,      gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.history")));
    /*    */ addCfgItem(22, sIndex, new CfgAppearanceSizeFormatDlg,   gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.size_format")));
    /*    */ addCfgItem( 3, sIndex, new CfgAppearanceFolderTreeDlg,   gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.folder_tree")));
    /*    */ addCfgItem(32, sIndex, new CfgAppearanceTabDlg,          gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.tab")));
    /*    */ addCfgItem(27, sIndex, new CfgAppearanceLanguageDlg,     gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.appearance.language")));
    sIndex = addCfgItem(17,     -1, new CfgFuncDlg,                   gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function")));
    /*    */ addCfgItem(13, sIndex, new CfgFuncBookmarkDlg,           gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.bookmark")));
    /*    */ addCfgItem( 7, sIndex, new CfgFuncRenameDlg,             gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.rename")));
    /*    */ addCfgItem(14, sIndex, new CfgFuncRefreshDlg,            gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.refresh")));
    /*    */ addCfgItem( 8, sIndex, new CfgFuncDragDlg,               gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.drag_drop")));
    /*    */ addCfgItem(21, sIndex, new CfgFuncProgramAssDlg,         gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.program_ass")));
    /*    */ addCfgItem(16, sIndex, new CfgFuncFileScrapDlg,          gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.file_scrap")));
    /*    */ addCfgItem(26, sIndex, new CfgFuncFileOpDlg,             gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.function.file_operation")));
    sIndex = addCfgItem( 6,     -1, new CfgAdvDlg,                    gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.advanced")));
    /*    */ addCfgItem(23, sIndex, new CfgAdvConfDirDlg,             gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.advanced.conf_dir")));
    /*    */ addCfgItem(24, sIndex, new CfgAdvHotKeyDlg,              gApp.loadString(XPR_STRING_LITERAL("popup.cfg.tree.advanced.global_hotkey")));

    if (!FXFILE_STL_IS_INDEXABLE(mInitShowCfg, mCfgDeque))
        mInitShowCfg = 0;

    // expand all
    HTREEITEM sTreeItem = mTreeCtrl.GetRootItem();
    while (sTreeItem != XPR_NULL)
    {
        if (mTreeCtrl.ItemHasChildren(sTreeItem) == XPR_TRUE)
            mTreeCtrl.Expand(sTreeItem, TVE_EXPAND);

        sTreeItem = mTreeCtrl.GetNextSiblingItem(sTreeItem);
    }

    mTreeCtrl.SelectItem(mCfgDeque[mInitShowCfg]->mTreeItem);
    mTreeCtrl.EnsureVisible(mCfgDeque[mInitShowCfg]->mTreeItem);

    GetDlgItem(IDC_CFG_APPLY)->EnableWindow(XPR_FALSE);
    mCfgDeque[mInitShowCfg]->mModified = XPR_FALSE;

    SetWindowText(gApp.loadString(XPR_STRING_LITERAL("popup.cfg.title")));
    SetDlgItemText(IDC_CFG_DEFAULT, gApp.loadString(XPR_STRING_LITERAL("popup.cfg.button.default")));
    SetDlgItemText(IDC_CFG_APPLY,   gApp.loadString(XPR_STRING_LITERAL("popup.cfg.button.apply")));
    SetDlgItemText(IDOK,            gApp.loadString(XPR_STRING_LITERAL("popup.common.button.ok")));
    SetDlgItemText(IDCANCEL,        gApp.loadString(XPR_STRING_LITERAL("popup.common.button.cancel")));

    return XPR_TRUE;
}

xpr_sint_t CfgMainDlg::addCfgItem(xpr_sint_t aImage, xpr_sint_t aParent, CfgDlg *aCfgDlg, const xpr_tchar_t *aText)
{
    CfgItem *sCfgItem = new CfgItem;
    if (sCfgItem == XPR_NULL)
        return -1;

    if (!FXFILE_STL_IS_INDEXABLE(aParent, mCfgDeque))
        aParent = -1;

    HTREEITEM sParentTreeItem = TVI_ROOT;
    if (aParent != -1)
        sParentTreeItem = mCfgDeque[aParent]->mTreeItem;

    sCfgItem->mTreeItem = mTreeCtrl.InsertItem(aText, aImage, aImage, sParentTreeItem);
    sCfgItem->mText     = aText;
    sCfgItem->mImage    = aImage;
    sCfgItem->mParent   = aParent;
    sCfgItem->mCfgDlg   = aCfgDlg;
    sCfgItem->mModified = XPR_FALSE;

    mCfgDeque.push_back(sCfgItem);

    return (xpr_sint_t)mCfgDeque.size() - 1;
}

xpr_bool_t CfgMainDlg::showCfg(xpr_sint_t aCfgIndex)
{
    if (!FXFILE_STL_IS_INDEXABLE(aCfgIndex, mCfgDeque))
        return XPR_FALSE;

    CfgItem *sCfgItem = mCfgDeque[aCfgIndex];

    // hide
    if (mShowCfg != -1)
    {
        if (FXFILE_STL_IS_INDEXABLE(mShowCfg, mCfgDeque))
        {
            CfgItem *sOldCfgItem = mCfgDeque[mShowCfg];

            if (sOldCfgItem->mCfgDlg->m_hWnd != XPR_NULL)
                sOldCfgItem->mCfgDlg->ShowWindow(SW_HIDE);
        }
    }

    // show
    if (sCfgItem->mCfgDlg->m_hWnd == XPR_NULL)
    {
        sCfgItem->mCfgDlg->setObserver(dynamic_cast<CfgDlgObserver *>(this));
        sCfgItem->mCfgDlg->Create(aCfgIndex, this);
        sCfgItem->mCfgDlg->onInit(mNewConfig);

        CRect sDescRect;
        GetDlgItem(IDC_CFG_DESC)->GetWindowRect(&sDescRect);
        ScreenToClient(&sDescRect);

        const xpr_sint_t y =
            sDescRect.bottom + ui::ModernUI::scaleForWindow(10, GetSafeHwnd());

        sCfgItem->mCfgDlg->SetWindowPos(XPR_NULL, sDescRect.left, y, 0, 0, SWP_NOSIZE);
        ui::ModernUI::applyRoundedWindowRegion(
            sCfgItem->mCfgDlg->GetSafeHwnd(),
            8);
    }

    sCfgItem->mCfgDlg->ShowWindow(SW_SHOW);

    // description (e.g. Configuration > Function > Bookmark)
    xpr::string sDesc;
    xpr_sint_t sParent = sCfgItem->mParent;

    sDesc += gApp.loadString(XPR_STRING_LITERAL("popup.cfg.title"));

    xpr_size_t sInsertPos = sDesc.length();
    while (sParent != -1)
    {
        if (!FXFILE_STL_IS_INDEXABLE(sParent, mCfgDeque))
            break;

        sDesc.insert(sInsertPos, mCfgDeque[sParent]->mText);
        sDesc.insert(sInsertPos, XPR_STRING_LITERAL(" > "));

        sParent = mCfgDeque[sParent]->mParent;
    }

    sDesc += XPR_STRING_LITERAL(" > ");
    sDesc += sCfgItem->mText;

    SetDlgItemText(IDC_CFG_DESC, sDesc.c_str());

    UpdateWindow();

    return XPR_TRUE;
}

void CfgMainDlg::applyModernAppearanceToChild(CWnd *aWnd, HFONT aPreviousFont)
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
         _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0) ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_TRUE(sStandardFontControl) && XPR_IS_NOT_NULL(mUIFont.m_hObject))
    {
        HFONT sCurrentFont = reinterpret_cast<HFONT>(
            aWnd->SendMessage(WM_GETFONT, 0, 0));
        if (XPR_IS_NULL(sCurrentFont) || sCurrentFont == aPreviousFont)
            aWnd->SetFont(&mUIFont, XPR_FALSE);
    }

    if (_tcsicmp(sClassName, XPR_STRING_LITERAL("Edit")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBox")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("ComboBoxEx32")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("ListBox")) == 0 ||
        _tcsicmp(sClassName, XPR_STRING_LITERAL("SysTreeView32")) == 0)
    {
        ui::ModernUI::applyExplorerControlTheme(aWnd->GetSafeHwnd());
    }

    CWnd *sChild = aWnd->GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CfgMainDlg::applyModernAppearanceToChildren(HFONT aPreviousFont)
{
    CWnd *sChild = GetWindow(GW_CHILD);
    while (XPR_IS_NOT_NULL(sChild))
    {
        applyModernAppearanceToChild(sChild, aPreviousFont);
        sChild = sChild->GetNextWindow();
    }
}

void CfgMainDlg::refreshModernAppearance(void)
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

        LOGFONT sHeaderLogFont = sLogFont;
        sHeaderLogFont.lfWeight = FW_SEMIBOLD;
        if (XPR_IS_NOT_NULL(mHeaderFont.m_hObject))
            mHeaderFont.DeleteObject();
        mHeaderFont.CreateFontIndirect(&sHeaderLogFont);
    }

    if (mSurfaceColor != sPalette.mElevated)
    {
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            mSurfaceBrush.DeleteObject();
        if (mSurfaceBrush.CreateSolidBrush(sPalette.mElevated) == XPR_TRUE)
            mSurfaceColor = sPalette.mElevated;
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

    CWnd *sDescWnd = GetDlgItem(IDC_CFG_DESC);
    if (XPR_IS_NOT_NULL(sDescWnd) && XPR_IS_NOT_NULL(mHeaderFont.m_hObject))
        sDescWnd->SetFont(&mHeaderFont, XPR_FALSE);

    if (::IsWindow(mTreeCtrl.GetSafeHwnd()) == XPR_TRUE)
    {
        mTreeCtrl.SetBkColor(sPalette.mCard);
        mTreeCtrl.SetTextColor(sPalette.mText);
        mTreeCtrl.SetLineColor(
            XPR_IS_TRUE(sPalette.mHighContrast) ?
            CLR_DEFAULT :
            sPalette.mSeparator);

        if (XPR_IS_NOT_NULL(mImgList.m_hImageList))
            mImgList.SetBkColor(sPalette.mCard);

        ui::ModernUI::applyRoundedWindowRegion(
            mTreeCtrl.GetSafeHwnd(),
            8);
    }

    RedrawWindow(
        XPR_NULL,
        XPR_NULL,
        RDW_INVALIDATE | RDW_ERASE | RDW_FRAME | RDW_ALLCHILDREN);
}

xpr_bool_t CfgMainDlg::OnEraseBkgnd(CDC *aDC)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();
    if (XPR_IS_FALSE(sPalette.mHighContrast))
    {
        CRect sClientRect;
        GetClientRect(&sClientRect);
        aDC->FillSolidRect(&sClientRect, sPalette.mWindow);
        return XPR_TRUE;
    }

    return super::OnEraseBkgnd(aDC);
}

void CfgMainDlg::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    super::OnSettingChange(aFlags, aSection);
    refreshModernAppearance();
}

void CfgMainDlg::OnSysColorChange(void)
{
    super::OnSysColorChange();
    refreshModernAppearance();
}

LRESULT CfgMainDlg::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    return Default();
}

LRESULT CfgMainDlg::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    refreshModernAppearance();
    return Default();
}

void CfgMainDlg::OnDestroy(void)
{
    super::OnDestroy();

    DELETE_OBJECT(mUIFont);
    DELETE_OBJECT(mHeaderFont);
    DELETE_OBJECT(mSurfaceBrush);
    DELETE_OBJECT(mWindowBrush);

    CfgItem *sCfgItem;
    CfgDeque::iterator sIterator;

    sIterator = mCfgDeque.begin();
    for (; sIterator != mCfgDeque.end(); ++sIterator)
    {
        sCfgItem = *sIterator;
        if (sCfgItem == XPR_NULL)
            continue;

        if (sCfgItem->mCfgDlg->m_hWnd != XPR_NULL)
            sCfgItem->mCfgDlg->DestroyWindow();

        XPR_SAFE_DELETE(sCfgItem->mCfgDlg);
        XPR_SAFE_DELETE(sCfgItem);
    }

    mCfgDeque.clear();
}

void CfgMainDlg::showCfgByTree(xpr_sint_t aCfgIndex)
{
    if (!FXFILE_STL_IS_INDEXABLE(aCfgIndex, mCfgDeque))
        return;

    mChanging = XPR_TRUE;

    showCfg(aCfgIndex);

    mChanging = XPR_FALSE;
}

void CfgMainDlg::OnOK(void) 
{
    OnApply();

    super::OnOK();
}

void CfgMainDlg::OnCancel(void) 
{
    super::OnCancel();
}

void CfgMainDlg::onSetModified(CfgDlg &aCfgDlg, xpr_bool_t aModified)
{
    if (mChanging == XPR_TRUE)
        return;

    xpr_size_t sCfgIndex = aCfgDlg.getCfgIndex();

    onSetModified(sCfgIndex, aModified);
}

void CfgMainDlg::onSetModified(xpr_size_t aCfgIndex, xpr_bool_t aModified)
{
    if (mChanging == XPR_TRUE)
        return;

    xpr_size_t sCount = mCfgDeque.size();
    if (FXFILE_STL_IS_INDEXABLE(aCfgIndex, mCfgDeque))
    {
        mCfgDeque[aCfgIndex]->mModified = aModified;

        xpr_size_t i;
        CfgItem *sCfgItem;
        CfgDeque::iterator sIterator;
        xpr_bool_t sEnable = XPR_FALSE;

        sIterator = mCfgDeque.begin();
        for (i = 0; sIterator != mCfgDeque.end(); ++sIterator, ++i)
        {
            sCfgItem = *sIterator;
            if (sCfgItem == XPR_NULL)
                continue;

            if (sCfgItem->mModified == XPR_TRUE)
            {
                sEnable = XPR_TRUE;
                break;
            }
        }

        GetDlgItem(IDC_CFG_APPLY)->EnableWindow(sEnable);
    }
}

xpr_bool_t CfgMainDlg::onIsModified(CfgDlg &aCfgDlg)
{
    xpr_size_t sCfgIndex = aCfgDlg.getCfgIndex();

    if (!FXFILE_STL_IS_INDEXABLE(sCfgIndex, mCfgDeque))
        return 0;

    return mCfgDeque[sCfgIndex]->mModified;
}

void CfgMainDlg::OnSelchangedTree(NMHDR* pNMHDR, LRESULT* pResult) 
{
    NM_TREEVIEW* pNMTreeView = (NM_TREEVIEW*)pNMHDR;
    *pResult = 0;

    HTREEITEM sTreeItem = pNMTreeView->itemNew.hItem;

    xpr_sint_t i;
    CfgItem *sCfgItem;
    CfgDeque::iterator sIterator;

    sIterator = mCfgDeque.begin();
    for (i = 0; sIterator != mCfgDeque.end(); ++sIterator, ++i)
    {
        sCfgItem = *sIterator;
        if (sCfgItem == XPR_NULL)
            continue;

        if (sTreeItem == sCfgItem->mTreeItem)
        {
            showCfgByTree(i);
            break;
        }
    }

    mShowCfg = i;
    mLastShowCfg = mShowCfg;
}

void CfgMainDlg::OnTreeCustomDraw(NMHDR* pNMHDR, LRESULT* pResult)
{
    NMTVCUSTOMDRAW *sCustomDraw =
        reinterpret_cast<NMTVCUSTOMDRAW *>(pNMHDR);
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();

    if (XPR_IS_TRUE(sPalette.mHighContrast))
    {
        *pResult = CDRF_DODEFAULT;
        return;
    }

    switch (sCustomDraw->nmcd.dwDrawStage)
    {
        case CDDS_PREPAINT:
            *pResult = CDRF_NOTIFYITEMDRAW;
            return;

        case CDDS_ITEMPREPAINT:
        {
            const UINT sState = sCustomDraw->nmcd.uItemState;
            const xpr_bool_t sSelected =
                (sState & CDIS_SELECTED) != 0 ? XPR_TRUE : XPR_FALSE;
            const xpr_bool_t sHot =
                (sState & CDIS_HOT) != 0 ? XPR_TRUE : XPR_FALSE;
            const xpr_bool_t sFocused =
                (::GetFocus() == mTreeCtrl.GetSafeHwnd()) ? XPR_TRUE : XPR_FALSE;

            sCustomDraw->clrText = sPalette.mText;
            sCustomDraw->clrTextBk = sPalette.mCard;

            if (XPR_IS_TRUE(sSelected))
            {
                sCustomDraw->clrTextBk =
                    XPR_IS_TRUE(sFocused) ?
                    sPalette.mPressed :
                    sPalette.mInactiveSelection;
                sCustomDraw->clrText = sPalette.mText;
            }
            else if (XPR_IS_TRUE(sHot))
            {
                sCustomDraw->clrTextBk = sPalette.mHover;
            }

            *pResult = CDRF_DODEFAULT;
            return;
        }

        default:
            *pResult = CDRF_DODEFAULT;
            return;
    }
}


HBRUSH CfgMainDlg::OnCtlColor(CDC* pDC, CWnd* pWnd, xpr_uint_t nCtlColor)
{
    const ui::ThemePalette sPalette = ui::ModernUI::getPalette();

    if (XPR_IS_TRUE(sPalette.mHighContrast))
        return super::OnCtlColor(pDC, pWnd, nCtlColor);

    pDC->SetTextColor(
        XPR_IS_NOT_NULL(pWnd) && XPR_IS_FALSE(pWnd->IsWindowEnabled()) ?
        sPalette.mSecondaryText :
        sPalette.mText);

    if (nCtlColor == CTLCOLOR_EDIT || nCtlColor == CTLCOLOR_LISTBOX)
    {
        pDC->SetBkMode(OPAQUE);
        pDC->SetBkColor(sPalette.mElevated);
        if (XPR_IS_NOT_NULL(mSurfaceBrush.m_hObject))
            return (HBRUSH)mSurfaceBrush.GetSafeHandle();
    }

    if (nCtlColor == CTLCOLOR_STATIC ||
        nCtlColor == CTLCOLOR_BTN ||
        nCtlColor == CTLCOLOR_DLG)
    {
        pDC->SetBkMode(TRANSPARENT);
        pDC->SetBkColor(sPalette.mWindow);
        if (XPR_IS_NOT_NULL(mWindowBrush.m_hObject))
            return (HBRUSH)mWindowBrush.GetSafeHandle();
    }

    return super::OnCtlColor(pDC, pWnd, nCtlColor);
}

void CfgMainDlg::OnDefault(void)
{
    const xpr_tchar_t *sMsg = gApp.loadString(XPR_STRING_LITERAL("popup.cfg.msg.confirm_default"));
    xpr_sint_t sMsgId = MessageBox(sMsg, XPR_NULL, MB_OK | MB_ICONWARNING | MB_YESNO);
    if (sMsgId != IDYES)
        return;

    ConfDir &sConfDir = ConfDir::instance();
    OptionManager &sOptionManager = OptionManager::instance();

    // save configuration path to save configuration files
    sConfDir.save();

    // initialize default option and save one
    sOptionManager.initDefaultConfigOption();

    // save default option
    sOptionManager.saveConfigOption();

    // copy default option
    gOpt->copyConfig(mNewConfig);

    // notify default option
    gOpt->notifyConfig();

    xpr_sint_t i;
    CfgItem *sCfgItem;
    CfgDeque::iterator sIterator;

    sIterator = mCfgDeque.begin();
    for (i = 0; sIterator != mCfgDeque.end(); ++sIterator, ++i)
    {
        sCfgItem = *sIterator;
        if (sCfgItem == XPR_NULL)
            continue;

        if (sCfgItem->mCfgDlg != XPR_NULL && sCfgItem->mCfgDlg->m_hWnd != XPR_NULL)
            sCfgItem->mCfgDlg->DestroyWindow();

        onSetModified(i, XPR_TRUE);
    }

    mTreeCtrl.SelectItem(mCfgDeque[0]->mTreeItem);
    showCfg(0);

    GetDlgItem(IDC_CFG_APPLY)->EnableWindow(XPR_FALSE);

    sMsg = gApp.loadString(XPR_STRING_LITERAL("popup.cfg.msg.default_ok"));
    MessageBox(sMsg, XPR_NULL, MB_OK | MB_ICONINFORMATION);
}

void CfgMainDlg::OnApply(void)
{
    CWaitCursor sWaitCursor;

    CfgItem *sCfgItem;
    CfgDeque::iterator sIterator;

    sIterator = mCfgDeque.begin();
    for (; sIterator != mCfgDeque.end(); ++sIterator)
    {
        sCfgItem = *sIterator;
        if (sCfgItem == XPR_NULL)
            continue;

        if (sCfgItem->mModified == XPR_TRUE && sCfgItem->mCfgDlg != XPR_NULL && sCfgItem->mCfgDlg->m_hWnd != XPR_NULL)
        {
            sCfgItem->mCfgDlg->onApply(mNewConfig);

            sCfgItem->mModified = XPR_FALSE;
        }
    }

    ConfDir &sConfDir = ConfDir::instance();
    OptionManager &sOptionManager = OptionManager::instance();

    // save configuration path to save configuration files
    sConfDir.save();

    // set new option
    gOpt->setConfig(mNewConfig);

    // save new option
    sOptionManager.saveConfigOption();

    // notify new option
    gOpt->notifyConfig();

    GetDlgItem(IDC_CFG_APPLY)->EnableWindow(XPR_FALSE);
}
} // namespace cfg
} // namespace fxfile
