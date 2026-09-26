//
// Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "main_coolbar.h"

#include "option.h"
#include "main_frame.h"
#include "explorer_view.h"
#include "conf_dir.h"
#include "ctrl_id.h"
#include "gui/ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace fxfile
{
class RebarInfo : public REBARINFO
{
public:
    RebarInfo(void)
    {
        memset(this, 0, sizeof(REBARINFO));
        cbSize = sizeof(REBARINFO);
    }
};

class RebarBandInfo : public REBARBANDINFO
{
public:
    RebarBandInfo(void)
    {
        memset(this, 0, sizeof(REBARBANDINFO));
        cbSize = sizeof(REBARBANDINFO);
    }
};

// A registered message cannot overlap an existing MFC/extension WM_APP ID.
static const UINT sDeferredCompactMessage =
    ::RegisterWindowMessage(XPR_STRING_LITERAL(
        "flyExplorer.DeferredCoolbarCompaction.v2"));

BEGIN_MESSAGE_MAP(MainCoolBar, CSizableReBar)
    ON_REGISTERED_MESSAGE(sDeferredCompactMessage, OnDeferredCompact)
    ON_WM_SIZE()
    ON_WM_SYSCOLORCHANGE()
    ON_WM_WINDOWPOSCHANGED()
    ON_WM_DESTROY()
END_MESSAGE_MAP()

MainCoolBar::MainCoolBar(void)
    : mDefaultCompactPending(XPR_FALSE)
    , mDefaultCompactPosted(XPR_FALSE)
{
}

MainCoolBar::~MainCoolBar(void)
{
}

xpr_bool_t MainCoolBar::createBands(void)
{
    DWORD sStyle;
    DWORD sExStyle;

    mMainToolBar.SetObserver(dynamic_cast<CToolBarEx::Observer *>(this));
    mDriveToolBar.SetObserver(dynamic_cast<CToolBarEx::Observer *>(this));
    mBookmarkToolBar.SetObserver(dynamic_cast<CToolBarEx::Observer *>(this));

    sStyle = WS_CHILD | WS_VISIBLE | CBRS_ALIGN_TOP | CBRS_FLYBY;
    sExStyle = TBSTYLE_EX_DRAWDDARROWS;
    if (mMainToolBar.Create(this, sStyle, AFX_IDW_TOOLBAR, sExStyle) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to create main toolbar\n"));
        return -1;      // fail to create
    }

    sStyle = WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN | CBRS_TOOLTIPS | CBRS_SIZE_DYNAMIC | CBRS_FLYBY | CBRS_ALIGN_TOP;
    sExStyle = TBSTYLE_EX_DRAWDDARROWS;
    if (mDriveToolBar.Create(this, sStyle, AFX_IDW_DRIVE_BAR, sExStyle) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to create drive toolBar\n"));
        return XPR_FALSE; // failed to create
    }

    sStyle = WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS | WS_CLIPCHILDREN | CBRS_TOOLTIPS | CBRS_SIZE_DYNAMIC | CBRS_FLYBY | CBRS_ALIGN_TOP;
    sExStyle = TBSTYLE_EX_DRAWDDARROWS;
    if (mBookmarkToolBar.Create(this, sStyle, AFX_IDW_BOOKMARK_BAR, sExStyle) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to create bookmark toolBar\n"));
        return XPR_FALSE; // failed to create
    }

    sStyle = RBBS_BREAK | RBBS_USECHEVRON;
    if (AddBar(&mMainToolBar, XPR_NULL, XPR_NULL, sStyle, XPR_STRING_LITERAL("&Toolbar"), false) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to add rebar\n"));
        return XPR_FALSE;
    }

    sStyle = RBBS_BREAK | RBBS_USECHEVRON;
    if (AddBar(&mDriveToolBar, XPR_NULL, XPR_NULL, sStyle, XPR_STRING_LITERAL("&Drivebar"), false) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to add rebar\n"));
        return XPR_FALSE;
    }

    // Sharing the drive row can constrain bookmark width during the
    // first toolbar AutoSize and expose clipped wrapped button content.
    // Give the bookmark band its own row; chevrons still preserve access
    // on narrow windows. Existing bookmarks and toolbar commands remain.
    sStyle = RBBS_BREAK | RBBS_USECHEVRON;
    if (AddBar(&mBookmarkToolBar, XPR_NULL, XPR_NULL, sStyle, XPR_STRING_LITERAL("&Bookmarkbar"), false) == XPR_FALSE)
    {
        XPR_TRACE(XPR_STRING_LITERAL("Failed to add rebar\n"));
        return XPR_FALSE;
    }

    mMainToolBar.Init();

    mMainToolBar.UpdateToolbarSize();
    mDriveToolBar.UpdateToolbarSize();
    mBookmarkToolBar.UpdateToolbarSize();

    const xpr_bool_t sSavedCoolBar = loadStateFile();

    // Dynamic Creation
    if (XPR_IS_FALSE(gOpt->mMain.mDriveBar))
    {
        setBandVisible(AFX_IDW_DRIVE_BAR, XPR_FALSE);
    }
    else
    {
        mDriveToolBar.setShortText(gOpt->mMain.mDriveBarShortText);
        mDriveToolBar.createDriveBar();
    }

    if (isBandVislble(AFX_IDW_BOOKMARK_BAR) == XPR_TRUE)
        mBookmarkToolBar.createBookmarkBar();

    setWrapable(AFX_IDW_BOOKMARK_BAR, gOpt->mMain.mBookmarkBarMultiLine);
    setWrapable(AFX_IDW_DRIVE_BAR,    gOpt->mMain.mDriveBarMultiLine);

    // UI-05: keep the three isolated initial rows while the native bars
    // acquire their actual geometry. Schedule *one* asynchronous fit check
    // only on a fresh profile. No layout changes are made from WM_SIZE.
    mDefaultCompactPending =
        XPR_IS_FALSE(sSavedCoolBar) &&
        XPR_IS_FALSE(gOpt->mMain.mDriveBarMultiLine) &&
        XPR_IS_FALSE(gOpt->mMain.mBookmarkBarMultiLine) ?
        XPR_TRUE : XPR_FALSE;
    if (XPR_IS_TRUE(mDefaultCompactPending) &&
        sDeferredCompactMessage != 0)
    {
        CRect sClient;
        GetClientRect(&sClient);
        if (sClient.Width() > 0 &&
            PostMessage(sDeferredCompactMessage))
            mDefaultCompactPosted = XPR_TRUE;
    }

    return 0;
}

void MainCoolBar::OnDestroy(void) 
{
    saveStateFile();

    CSizableReBar::OnDestroy();
}

void MainCoolBar::OnSize(xpr_uint_t nType, xpr_sint_t cx, xpr_sint_t cy)
{
    CSizableReBar::OnSize(nType, cx, cy);

    xpr_sint_t i;
    xpr_sint_t sCount;
    CToolBarEx *sToolBar;
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();
    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_CHILD;

    sCount = sReBarCtrl.GetBandCount();
    for (i = 0; i < sCount; ++i)
    {
        sReBarCtrl.GetBandInfo(i, &sRebarBandInfo);

        sToolBar = DYNAMIC_DOWNCAST(CToolBarEx, CWnd::FromHandle(sRebarBandInfo.hwndChild));
        if (XPR_IS_NOT_NULL(sToolBar))
        {
            if (XPR_TEST_BITS(sToolBar->GetStyle(), TBSTYLE_WRAPABLE))
            {
                sToolBar->UpdateToolbarSize();
            }
        }
    }

    // UI-05: a nonzero size is the earliest valid cue to enqueue the
    // one-shot fit check. Never run SetBandInfo/RecalcLayout synchronously
    // inside OnSize (that can re-enter OnSize via Rebar notifications).
    if (cx > 0 && sDeferredCompactMessage != 0 &&
        XPR_IS_TRUE(mDefaultCompactPending) &&
        XPR_IS_FALSE(mDefaultCompactPosted))
    {
        if (PostMessage(sDeferredCompactMessage))
            mDefaultCompactPosted = XPR_TRUE;
    }
}

LRESULT MainCoolBar::OnDeferredCompact(WPARAM, LPARAM)
{
    mDefaultCompactPosted = XPR_FALSE;
    if (XPR_IS_FALSE(mDefaultCompactPending) || !::IsWindow(m_hWnd))
        return 0;

    CReBarCtrl &sBands = GetReBarCtrl();
    const xpr_sint_t sDrive = sBands.IDToIndex(AFX_IDW_DRIVE_BAR);
    const xpr_sint_t sBookmark = sBands.IDToIndex(AFX_IDW_BOOKMARK_BAR);
    if (sDrive < 0 || sBookmark != sDrive + 1 ||
        XPR_IS_FALSE(isBandVislble(AFX_IDW_DRIVE_BAR)) ||
        XPR_IS_FALSE(isBandVislble(AFX_IDW_BOOKMARK_BAR)) ||
        XPR_IS_TRUE(gOpt->mMain.mDriveBarMultiLine) ||
        XPR_IS_TRUE(gOpt->mMain.mBookmarkBarMultiLine))
    {
        mDefaultCompactPending = XPR_FALSE;
        return 0;
    }

    RebarBandInfo sDriveBand;
    RebarBandInfo sBookmarkBand;
    sDriveBand.fMask = RBBIM_IDEALSIZE;
    sBookmarkBand.fMask = RBBIM_IDEALSIZE | RBBIM_STYLE;
    if (XPR_IS_FALSE(sBands.GetBandInfo(sDrive, &sDriveBand)) ||
        XPR_IS_FALSE(sBands.GetBandInfo(sBookmark, &sBookmarkBand)))
    {
        mDefaultCompactPending = XPR_FALSE;
        return 0;
    }

    // A zero ideal size means a toolbar has not completed its native
    // AutoSize. Leave the default layout alone; a later WM_SIZE may
    // enqueue one more attempt when actual dimensions become available.
    if (sDriveBand.cxIdeal == 0 || sBookmarkBand.cxIdeal == 0)
        return 0;

    // Attempt at most once after both native bars are measured; if the
    // first usable frame is narrow, retain separate rows permanently.
    mDefaultCompactPending = XPR_FALSE;
    CRect sClient;
    sBands.GetClientRect(&sClient);
    const xpr_sint_t sSlack =
        ui::ModernUI::scaleForWindow(48, GetSafeHwnd());
    const xpr_sint_t sAvailable =
        max(0, sClient.Width() - sSlack);
    if (sDriveBand.cxIdeal >= static_cast<UINT>(sAvailable) ||
        sBookmarkBand.cxIdeal >=
            static_cast<UINT>(sAvailable) - sDriveBand.cxIdeal)
        return 0;

    // The handler is a posted message, never a child of WM_SIZE.
    // The pending bit is already clear before this can emit new size
    // notifications. All saved or user-selected row layouts are preserved.
    sBookmarkBand.fStyle &= ~RBBS_BREAK;
    if (sBands.SetBandInfo(sBookmark, &sBookmarkBand))
    {
        CFrameWnd *sFrame = GetParentFrame();
        if (sFrame != NULL)
            sFrame->RecalcLayout();
    }
    return 0;
}

xpr_sint_t MainCoolBar::getToolbarText(void) const
{
    return mMainToolBar.GetTextType();
}

void MainCoolBar::setToolbarText(xpr_sint_t aText)
{
    mMainToolBar.SetTextType(aText);
}

void MainCoolBar::setToobarIcon(xpr_sint_t aIcon)
{
    mMainToolBar.SetIconType(aIcon);
}

xpr_sint_t MainCoolBar::getToolbarIcon(void) const
{
    return mMainToolBar.GetIconType();
}

void MainCoolBar::setBandVisible(xpr_uint_t aBandId, xpr_bool_t aVisible)
{
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    xpr_sint_t sBandIndex = sReBarCtrl.IDToIndex(aBandId);

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_STYLE;
    sReBarCtrl.GetBandInfo(sBandIndex, &sRebarBandInfo);

    if (XPR_IS_TRUE(aVisible)) sRebarBandInfo.fStyle &= ~RBBS_HIDDEN;
    else                       sRebarBandInfo.fStyle |= RBBS_HIDDEN;

    if (XPR_IS_TRUE(aVisible))
    {
        if (aBandId == AFX_IDW_DRIVE_BAR)
        {
            mDriveToolBar.createDriveBar();
        }

        if (aBandId == AFX_IDW_BOOKMARK_BAR)
        {
            mBookmarkToolBar.createBookmarkBar();
        }
    }

    sReBarCtrl.SetBandInfo(sBandIndex, &sRebarBandInfo);

    if (XPR_IS_FALSE(aVisible))
    {
        if (aBandId == AFX_IDW_DRIVE_BAR)
            mDriveToolBar.destroyDriveBar();

        if (aBandId == AFX_IDW_BOOKMARK_BAR)
            mBookmarkToolBar.destroyBookmarkBar();
    }
}

xpr_bool_t MainCoolBar::isBandVislble(xpr_uint_t aBandId)
{
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    xpr_sint_t sBandIndex = sReBarCtrl.IDToIndex(aBandId);

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_STYLE;
    sReBarCtrl.GetBandInfo(sBandIndex, &sRebarBandInfo);

    return (sRebarBandInfo.fStyle & RBBS_HIDDEN) ? XPR_FALSE : XPR_TRUE;
}

xpr_bool_t MainCoolBar::isWrapable(xpr_uint_t aBandId)
{
    xpr_bool_t sResult = XPR_FALSE;

    CReBarCtrl &sReBarCtrl = GetReBarCtrl();
    xpr_sint_t sBandIndex = sReBarCtrl.IDToIndex(aBandId);

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_CHILD;
    if (sReBarCtrl.GetBandInfo(sBandIndex, &sRebarBandInfo))
    {
        xpr_tchar_t sClassName[MAX_CLASS_NAME + 1] = {0};
        GetClassName(sRebarBandInfo.hwndChild, sClassName, MAX_CLASS_NAME);
        if (_tcsicmp(sClassName, XPR_STRING_LITERAL("ToolbarWindow32")) == 0)
        {
            CToolBarEx *sToolBar = (CToolBarEx *)CWnd::FromHandle(sRebarBandInfo.hwndChild);
            if (XPR_IS_NOT_NULL(sToolBar) && XPR_IS_NOT_NULL(sToolBar->m_hWnd) && sToolBar->GetStyle() & TBSTYLE_WRAPABLE)
                sResult = XPR_TRUE;
        }
    }

    return sResult;
}

void MainCoolBar::setWrapable(xpr_uint_t aBandId, xpr_bool_t aWrapable)
{
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    xpr_sint_t sBandIndex = sReBarCtrl.IDToIndex(aBandId);

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_CHILD | RBBIM_STYLE;
    if (sReBarCtrl.GetBandInfo(sBandIndex, &sRebarBandInfo) == XPR_TRUE)
    {
        xpr_tchar_t sClassName[MAX_CLASS_NAME + 1] = {0};
        GetClassName(sRebarBandInfo.hwndChild, sClassName, MAX_CLASS_NAME);
        if (_tcsicmp(sClassName, XPR_STRING_LITERAL("ToolbarWindow32")) == 0)
        {
            CToolBarEx *sToolBar = (CToolBarEx *)CWnd::FromHandle(sRebarBandInfo.hwndChild);
            if (XPR_IS_NOT_NULL(sToolBar) && XPR_IS_NOT_NULL(sToolBar->m_hWnd))
            {
                sRebarBandInfo.fMask &= ~RBBIM_CHILD;
                sRebarBandInfo.fMask |= RBBIM_IDEALSIZE;

                // Also correct stored same-row layouts from the previous
                // shared-band default. A saved BREAK flag otherwise
                // overrides the new-band construction at startup.
                if (aBandId == AFX_IDW_BOOKMARK_BAR &&
                    XPR_IS_TRUE(aWrapable))
                    sRebarBandInfo.fStyle |= RBBS_BREAK;

                if (XPR_IS_TRUE(aWrapable))
                {
                    sToolBar->ModifyStyle(0, TBSTYLE_WRAPABLE);

                    sRebarBandInfo.fStyle &= ~RBBS_USECHEVRON;
                    sRebarBandInfo.cxIdeal = 0;
                }
                else
                {
                    sToolBar->ModifyStyle(TBSTYLE_WRAPABLE, 0);

                    if (aBandId == AFX_IDW_BOOKMARK_BAR)
                    {
                        // A toolbar can retain per-button TBSTATE_WRAP bits
                        // after its window-level wrap style is removed.
                        // Clearing only TBSTYLE_WRAPABLE leaves a partial
                        // native second row visible below our 40-DIP band.
                        // Do not change this state in user-enabled multiline
                        // mode; chevrons handle nonwrapping overflow.
                        CToolBarCtrl &sBookmarkCtrl =
                            sToolBar->GetToolBarCtrl();
                        const xpr_sint_t sButtonCount =
                            sBookmarkCtrl.GetButtonCount();
                        for (xpr_sint_t i = 0; i < sButtonCount; ++i)
                        {
                            TBBUTTONINFO sButton = {0};
                            sButton.cbSize = sizeof(sButton);
                            sButton.dwMask = TBIF_BYINDEX | TBIF_STATE;
                            if (sBookmarkCtrl.GetButtonInfo(i, &sButton) >= 0 &&
                                (sButton.fsState & TBSTATE_WRAP) != 0)
                            {
                                sButton.fsState &= ~TBSTATE_WRAP;
                                sBookmarkCtrl.SetButtonInfo(i, &sButton);
                            }
                        }
                    }

                    CSize sToolBarHorzMinSize;
                    sToolBarHorzMinSize = sToolBar->CalcDynamicLayout(-1, 0);

                    sRebarBandInfo.cxIdeal = sToolBarHorzMinSize.cx;
                    sRebarBandInfo.fStyle |= RBBS_USECHEVRON;
                }

                sReBarCtrl.SetBandInfo(sBandIndex, &sRebarBandInfo);

                sToolBar->UpdateToolbarSize();    // CReBarCtrl update
                GetParentFrame()->RecalcLayout(); // CSizableReBar update

                if (aBandId == AFX_IDW_BOOKMARK_BAR) gOpt->mMain.mBookmarkBarMultiLine = aWrapable;
                if (aBandId == AFX_IDW_DRIVE_BAR)    gOpt->mMain.mDriveBarMultiLine    = aWrapable;
            }
        }
    }
}

void MainCoolBar::onUpdatedToolbarSize(CToolBarEx &theToolBar)
{
    CToolBarCtrl &sToolBarCtrl = theToolBar.GetToolBarCtrl();
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    xpr_sint_t sBandIndex = sReBarCtrl.IDToIndex((xpr_uint_t)theToolBar.GetDlgCtrlID());
    if (sBandIndex < 0)
        return;

    // Calculate desired height and ideal width of the bar whether TBSTYLE_WRAPABLE or not
    xpr_sint_t sFirstTop = 0;

    DWORD sStyle = theToolBar.GetStyle();

    CRect sItemRect;
    xpr_sint_t i;
    xpr_sint_t cyChild = 0;
    xpr_sint_t cxIdeal = 0;
    xpr_sint_t sCount = sToolBarCtrl.GetButtonCount();
    for (i = 0; i < sCount; ++i)
    {
        if (sToolBarCtrl.GetItemRect(i, sItemRect) == XPR_TRUE)
        {
            if (i == 0)
                sFirstTop = sItemRect.top;

            cxIdeal += sItemRect.Width();

            if (XPR_TEST_BITS(sStyle, TBSTYLE_WRAPABLE))
                cyChild = max(cyChild, sItemRect.bottom - sFirstTop);
            else
                cyChild = max(cyChild, sItemRect.Height());
        }
    }

    // Modify parent band info accordingly. A single-row band uses the shared
    // command-bar height so main/drive/bookmark surfaces align vertically,
    // while wrapped toolbars retain their larger native calculated height.
    // RBBIM_CHILDSIZE also consumes cyMaxChild and cyIntegral. Both
    // were previously uninitialized stack data; in the nonwrapping case
    // that can permit an inconsistent/partially exposed second row.
    REBARBANDINFO sRebarBandInfo = {0};
    sRebarBandInfo.cbSize     = sizeof(sRebarBandInfo);
    sRebarBandInfo.fMask      = RBBIM_CHILDSIZE | RBBIM_IDEALSIZE;
    sRebarBandInfo.cxIdeal    = cxIdeal;
    sRebarBandInfo.cxMinChild = 0;
    sRebarBandInfo.cyMinChild = max(
        cyChild,
        ui::ModernUI::getCommandBarHeight(theToolBar.GetSafeHwnd()));
    sRebarBandInfo.cyMaxChild = sRebarBandInfo.cyMinChild;
    VERIFY(sReBarCtrl.SetBandInfo(sBandIndex, &sRebarBandInfo));
}

void MainCoolBar::OnSysColorChange(void) 
{
    CSizableReBar::OnSysColorChange();

}

void MainCoolBar::OnWindowPosChanged(WINDOWPOS FAR* lpwndpos) 
{
    CSizableReBar::OnWindowPosChanged(lpwndpos);

    //xpr_uint_t iBand = IDToIndex(AFX_IDW_MENUBAR);

    //RebarBandInfo sRebarBandInfo;
    //sRebarBandInfo.fMask = RBBIM_CHILDSIZE;
    //GetBandInfo(iBand, &sRebarBandInfo);

    //sRebarBandInfo.cyMinChild = m_wndMenuBar.CalcFixedLayout(XPR_TRUE, XPR_FALSE).cy;
    //SetBandInfo(iBand, &sRebarBandInfo);
}

void MainCoolBar::loadState(void)
{
    //// CSizableReBar
    //CSizableReBar::LoadState(XPR_STRING_LITERAL("FrameWnd"), XPR_STRING_LITERAL("MainCoolBar"));

    //RebarBandInfo sRebarBandInfo;
    //sRebarBandInfo.fMask = RBBIM_STYLE;
    //GetBandInfo(0, &sRebarBandInfo);

    //m_bLock = (sRebarBandInfo.fStyle & RBBS_NOGRIPPER) ? XPR_TRUE : XPR_FALSE;

    //// toolbar
    //mMainToolBar.LoadState(XPR_STRING_LITERAL("FrameWnd"), XPR_STRING_LITERAL("MainToolBar"));
}

void MainCoolBar::saveState(void)
{
    //// CSizableReBar
    //CSizableReBar::SaveState(XPR_STRING_LITERAL("FrameWnd"), XPR_STRING_LITERAL("MainCoolBar"));

    //// toolbar
    //mMainToolBar.SaveState(XPR_STRING_LITERAL("FrameWnd"), XPR_STRING_LITERAL("MainToolBar"));
}

xpr_bool_t MainCoolBar::loadStateFile(void)
{
    xpr_bool_t sSavedCoolBar = XPR_FALSE;
    // CSizableReBar
    {
        xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
        ConfDir::instance().getLoadPath(ConfDir::TypeCoolBar, sPath, XPR_MAX_PATH);

        sSavedCoolBar = loadStateFile(sPath);
    }

    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_STYLE;
    sReBarCtrl.GetBandInfo(0, &sRebarBandInfo);

    if ((sRebarBandInfo.fStyle & RBBS_NOGRIPPER) == RBBS_NOGRIPPER)
        Lock();

    // toolbar
    {
        xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
        ConfDir::instance().getLoadPath(ConfDir::TypeToolBar, sPath, XPR_MAX_PATH);

        if (mMainToolBar.load(sPath) == XPR_FALSE)
            mMainToolBar.SetDefaultButtons();
    }

    // The persisted coolbar file predates the Win11 command metrics and can
    // restore narrow child extents after the toolbars have already calculated
    // their modern sizes. Recalculate every toolbar after state restore so old
    // band geometry cannot clip or crowd the current icon/button layout.
    mMainToolBar.UpdateToolbarSize();
    mDriveToolBar.UpdateToolbarSize();
    mBookmarkToolBar.UpdateToolbarSize();
    return sSavedCoolBar;
}

void MainCoolBar::saveStateFile(void)
{
    // CSizableReBar
    {
        xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
        ConfDir::instance().getSavePath(ConfDir::TypeCoolBar, sPath, XPR_MAX_PATH);

        saveStateFile(sPath);
    }

    // toolbar
    {
        xpr_tchar_t sPath[XPR_MAX_PATH + 1] = {0};
        ConfDir::instance().getSavePath(ConfDir::TypeToolBar, sPath, XPR_MAX_PATH);

        mMainToolBar.save(sPath);
    }
}

#pragma pack(push, 1)

typedef struct CoolBarStateHeader
{
    xpr_sint32_t cbSize;
    xpr_uint32_t nBandCount;
} CoolBarStateHeader;

typedef struct CoolBarState
{
    xpr_sint32_t cbSize;
    xpr_uint32_t wID;
    xpr_uint32_t cx;
    xpr_uint32_t fStyle;
    xpr_uint32_t cxMinChild;
} CoolBarState;

#pragma pack(pop)

xpr_bool_t MainCoolBar::loadStateFile(const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aPath))
        return XPR_FALSE;

    xpr_rcode_t sRcode;
    xpr_ssize_t sReadSize;
    xpr::FileIo sFileIo;

    sRcode = sFileIo.open(aPath, xpr::FileIo::OpenModeReadOnly);
    if (XPR_RCODE_IS_ERROR(sRcode))
        return XPR_FALSE;

    CoolBarStateHeader sCoolBarStateHeader;
    sCoolBarStateHeader.cbSize = sizeof(sCoolBarStateHeader);
    sRcode = sFileIo.read(&sCoolBarStateHeader, sCoolBarStateHeader.cbSize, &sReadSize);
    if (XPR_RCODE_IS_ERROR(sRcode))
        return XPR_FALSE;

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_STYLE | RBBIM_SIZE | RBBIM_ID | RBBIM_CHILDSIZE;

    xpr_sint_t i;
    xpr_sint_t sCount;
    CoolBarState sCoolBarState;
    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    sCount = (xpr_sint_t)sCoolBarStateHeader.nBandCount;
    for (i = 0; i < sCount; ++i)
    {
        sRcode = sFileIo.read(&sCoolBarState, sizeof(sCoolBarState), &sReadSize);
        if (XPR_RCODE_IS_ERROR(sRcode))
            break;

        sReBarCtrl.MoveBand(sReBarCtrl.IDToIndex(sCoolBarState.wID), i);

        sReBarCtrl.GetBandInfo(i, &sRebarBandInfo);
        sRebarBandInfo.fStyle     = sCoolBarState.fStyle;
        sRebarBandInfo.cx         = sCoolBarState.cx;
        sRebarBandInfo.cxMinChild = sCoolBarState.cxMinChild;
        sReBarCtrl.SetBandInfo(i, &sRebarBandInfo);
    }

    sFileIo.close();

    return XPR_TRUE;
}

void MainCoolBar::saveStateFile(const xpr_tchar_t *aPath)
{
    if (XPR_IS_NULL(aPath))
        return;

    xpr_rcode_t sRcode;
    xpr_ssize_t sWrittenSize;
    xpr_sint_t  sOpenMode;
    xpr::FileIo sFileIo;

    sOpenMode = xpr::FileIo::OpenModeCreate | xpr::FileIo::OpenModeTruncate | xpr::FileIo::OpenModeWriteOnly;
    sRcode = sFileIo.open(aPath, sOpenMode);
    if (XPR_RCODE_IS_ERROR(sRcode))
        return;

    CReBarCtrl &sReBarCtrl = GetReBarCtrl();

    RebarBandInfo sRebarBandInfo;
    sRebarBandInfo.fMask = RBBIM_STYLE | RBBIM_SIZE | RBBIM_ID | RBBIM_CHILDSIZE;

    xpr_sint_t i;
    xpr_sint_t sCount;
    sCount = sReBarCtrl.GetBandCount();

    CoolBarStateHeader sCoolBarStateHeader;
    sCoolBarStateHeader.cbSize = sizeof(sCoolBarStateHeader);
    sCoolBarStateHeader.nBandCount = sCount;

    sRcode = sFileIo.write(&sCoolBarStateHeader, sCoolBarStateHeader.cbSize, &sWrittenSize);
    if (XPR_RCODE_IS_ERROR(sRcode))
        return;

    CoolBarState sCoolBarState;
    sCoolBarState.cbSize = sizeof(sCoolBarState);

    for (i = 0; i < sCount; ++i)
    {
        sReBarCtrl.GetBandInfo(i, &sRebarBandInfo);

        sCoolBarState.wID        = sRebarBandInfo.wID;
        sCoolBarState.cx         = sRebarBandInfo.cx;
        sCoolBarState.fStyle     = sRebarBandInfo.fStyle;
        sCoolBarState.cxMinChild = sRebarBandInfo.cxMinChild;
        sRcode = sFileIo.write(&sCoolBarState, sCoolBarState.cbSize, &sWrittenSize);
        if (XPR_RCODE_IS_ERROR(sRcode))
            break;
    }

    sFileIo.close();
}
} // namespace fxfile
