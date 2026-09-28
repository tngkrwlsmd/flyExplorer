//
// Copyright (c) 2013 Leon Lee author. All rights reserved.
//
//   homepage: http://www.flychk.com
//   e-mail:   mailto:flychk@flychk.com
//
// Use of this source code is governed by a GPLv3 license that can be
// found in the LICENSE file.

#include "stdafx.h"
#include "StatusBar.h"
#include "StatusBarObserver.h"

#include "ModernUI.h"

#ifdef _DEBUG
#define new DEBUG_NEW
#endif

namespace
{
const xpr_sint_t kPaneGap = 2;
const xpr_sint_t kTextPadding = 4;
const xpr_sint_t kSeparatorInset = 3;
const xpr_sint_t kVerticalPadding = 2;
const xpr_sint_t kTopBorder = 1;
const xpr_sint_t kMinimumHeight = 18;

const xpr_tchar_t kClassName[] = XPR_STRING_LITERAL("StatusBar");
} // namespace anonymous

struct StatusBar::PaneItem
{
public:
    PaneItem(void)
    {
        mPaneId    = 0;
        mData      = XPR_NULL;
        mSize          = 0;
        mMinSize       = 0;
        mLogicalSize   = 0;
        mLogicalMinSize = 0;
        mDynamicSize   = XPR_FALSE;
        mDynamicOffset = 0;
        mIcon          = XPR_NULL;

        mPaneRect      = CRect(0, 0, 0, 0);
    }

public:
    xpr_size_t    mPaneId;
    xpr::string   mText;
    void         *mData;
    xpr_size_t    mSize;
    xpr_size_t    mMinSize;
    xpr_size_t    mLogicalSize;
    xpr_size_t    mLogicalMinSize;
    xpr_bool_t    mDynamicSize;
    xpr_sint_t    mDynamicOffset;
    HICON         mIcon;

    CRect         mPaneRect;
};

StatusBar::StatusBar(void)
    : mObserver(XPR_NULL)
{
    registerWindowClass();
}

StatusBar::~StatusBar(void)
{
}

xpr_bool_t StatusBar::registerWindowClass(void)
{
    WNDCLASS sWndClass = {0};
    HINSTANCE sInstance = AfxGetInstanceHandle();

    //Check weather the class is registerd already
    if (::GetClassInfo(sInstance, kClassName, &sWndClass) == XPR_FALSE)
    {
        //If not then we have to register the new class
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

    return XPR_TRUE;
}

xpr_bool_t StatusBar::Create(CWnd *aParentWnd, const RECT &aRect, xpr_uint_t aId, DWORD aStyle)
{
    return CWnd::Create(kClassName, XPR_NULL, aStyle, aRect, aParentWnd, aId);
}

xpr_bool_t StatusBar::Create(CWnd *aParentWnd, xpr_uint_t aId, const RECT &aRect)
{
    DWORD sStyle = 0;
    sStyle |= WS_VISIBLE;
    sStyle |= WS_CHILD;
    sStyle |= WS_CLIPSIBLINGS;
    sStyle |= WS_CLIPCHILDREN;

    return Create(aParentWnd, aRect, aId, sStyle);
}

BEGIN_MESSAGE_MAP(StatusBar, super)
    ON_WM_CREATE()
    ON_WM_DESTROY()
    ON_WM_SIZE()
    ON_WM_PAINT()
    ON_WM_ERASEBKGND()
    ON_WM_SETTINGCHANGE()
    ON_MESSAGE(WM_DPICHANGED, OnDpiChanged)
    ON_MESSAGE(WM_THEMECHANGED, OnThemeChanged)
    ON_WM_LBUTTONDBLCLK()
    ON_WM_CONTEXTMENU()
    ON_MESSAGE(WM_SETTEXT, OnSetText)
END_MESSAGE_MAP()

xpr_sint_t StatusBar::OnCreate(LPCREATESTRUCT aCreateStruct)
{
    if (super::OnCreate(aCreateStruct) == -1)
        return -1;

    if (XPR_IS_NULL(mFont.m_hObject))
        createFont();

    return 0;
}

void StatusBar::PreSubclassWindow(void)
{
    if (XPR_IS_NULL(mFont.m_hObject))
        createFont();

    super::PreSubclassWindow();
}

void StatusBar::OnDestroy(void)
{
    removeAllPanes();

    super::OnDestroy();

    destroyFont();
}

void StatusBar::setObserver(StatusBarObserver *aObserver)
{
    mObserver = aObserver;
}

xpr_size_t StatusBar::addPane(xpr_size_t aPaneId, const xpr_tchar_t *aText, HICON aIcon, void *aData)
{
    return insertPane(InvalidIndex, aPaneId, aText, aIcon, aData);
}

xpr_size_t StatusBar::insertPane(xpr_size_t aIndex, xpr_size_t aPaneId, const xpr_tchar_t *aText, HICON aIcon, void *aData)
{
    if (aIndex != InvalidIndex && !FXFILE_STL_IS_INDEXABLE(aIndex, mPaneDeque))
        return InvalidIndex;

    PaneItem *sPaneItem = new PaneItem;
    if (XPR_IS_NULL(sPaneItem))
        return InvalidIndex;

    if (XPR_IS_NOT_NULL(aText))
        sPaneItem->mText = aText;

    sPaneItem->mPaneId = aPaneId;
    sPaneItem->mData   = aData;
    sPaneItem->mIcon   = aIcon;

    return insertPaneItem(aIndex, sPaneItem);
}

xpr_size_t StatusBar::insertPaneItem(xpr_size_t aIndex, PaneItem *aPaneItem)
{
    if (XPR_IS_NULL(aPaneItem))
        return InvalidIndex;

    if (aIndex == InvalidIndex)
    {
        mPaneDeque.push_back(aPaneItem);
        aIndex = (xpr_sint_t)mPaneDeque.size() - 1;
    }
    else
    {
        mPaneDeque.insert(mPaneDeque.begin() + aIndex, aPaneItem);
    }

    recalcLayout();

    return aIndex;
}

xpr_bool_t StatusBar::setPaneSize(xpr_size_t aIndex, xpr_size_t aSize, xpr_size_t aMinSize)
{
    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    sPaneItem->mLogicalSize    = aSize;
    sPaneItem->mLogicalMinSize = aMinSize;
    sPaneItem->mDynamicSize    = XPR_FALSE;
    sPaneItem->mDynamicOffset  = 0;
    sPaneItem->mSize           = static_cast<xpr_size_t>(max(0, scaleMetric(static_cast<xpr_sint_t>(aSize))));
    sPaneItem->mMinSize        = static_cast<xpr_size_t>(max(0, scaleMetric(static_cast<xpr_sint_t>(aMinSize))));

    recalcLayout();

    return XPR_TRUE;
}

xpr_bool_t StatusBar::setPaneText(xpr_size_t aIndex, const xpr_tchar_t *aText)
{
    if (XPR_IS_NULL(aText))
        return XPR_FALSE;

    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    if (sPaneItem->mText == aText)
        return XPR_TRUE;

    sPaneItem->mText = aText;

    recalcLayout();

    return XPR_TRUE;
}

void StatusBar::announceAccessibleStatus(const xpr_tchar_t *aText)
{
    if (XPR_IS_NULL(aText) || !::IsWindow(m_hWnd))
        return;
    // WM_SETTEXT is overridden by this class to replace visual pane 0.
    // Call only the native default procedure to store the accessibility
    // name without altering either already-rendered status pane.
    ::DefWindowProc(m_hWnd, WM_SETTEXT, 0,
        reinterpret_cast<LPARAM>(aText));
    ::NotifyWinEvent(EVENT_OBJECT_NAMECHANGE,
        m_hWnd, OBJID_CLIENT, CHILDID_SELF);
}

xpr_bool_t StatusBar::setDynamicPaneText(xpr_sint_t aIndex, const xpr_tchar_t *aText, xpr_sint_t aOffset)
{
    if (XPR_IS_NULL(aText))
        return XPR_FALSE;

    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    sPaneItem->mText          = aText;
    sPaneItem->mDynamicSize   = XPR_TRUE;
    sPaneItem->mDynamicOffset = aOffset;

    updateDynamicPaneSize(sPaneItem);
    recalcLayout();

    return XPR_TRUE;
}

xpr_bool_t StatusBar::setPaneIcon(xpr_size_t aIndex, HICON aIcon)
{
    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    sPaneItem->mIcon = aIcon;

    recalcLayout();

    return XPR_TRUE;
}

xpr_bool_t StatusBar::setPaneData(xpr_size_t aIndex, void *aData)
{
    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    sPaneItem->mData = aData;

    return XPR_TRUE;
}

xpr_size_t StatusBar::getPaneCount(void) const
{
    return mPaneDeque.size();
}

StatusBar::PaneItem *StatusBar::getPaneItem(xpr_size_t aPane) const
{
    if (FXFILE_STL_IS_INDEXABLE(aPane, mPaneDeque))
        return mPaneDeque[aPane];

    return XPR_NULL;
}

xpr_bool_t StatusBar::getPaneText(xpr_size_t aIndex, xpr_tchar_t *aText, xpr_size_t aMaxLen) const
{
    if (XPR_IS_NULL(aText) || aMaxLen == 0)
        return XPR_FALSE;

    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_FALSE;

    if (sPaneItem->mText.length() > aMaxLen)
        return XPR_FALSE;

    _tcscpy(aText, sPaneItem->mText.c_str());

    return XPR_TRUE;
}

void *StatusBar::getPaneData(xpr_size_t aIndex) const
{
    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_NULL;

    return sPaneItem->mData;
}

xpr_bool_t StatusBar::getPaneRect(xpr_size_t aIndex, RECT *aRect) const
{
    if (XPR_IS_NULL(aRect))
        return XPR_FALSE;

    PaneItem *sPaneItem = getPaneItem(aIndex);
    if (XPR_IS_NULL(sPaneItem))
        return XPR_NULL;

    *aRect = sPaneItem->mPaneRect;

    return XPR_TRUE;
}

xpr_sint_t StatusBar::getDefaultHeight(void)
{
    CClientDC sClientDC(this);

    CFont *sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(mFont.m_hObject))
        sOldFont = sClientDC.SelectObject(&mFont);

    CSize sText = sClientDC.GetTextExtent(XPR_STRING_LITERAL("TEST"));

    if (XPR_IS_NOT_NULL(sOldFont))
        sClientDC.SelectObject(sOldFont);

    const xpr_sint_t sVerticalPadding = scaleMetric(kVerticalPadding);
    const xpr_sint_t sTopBorder = max(1, scaleMetric(kTopBorder));
    const xpr_sint_t sMinimumHeight = scaleMetric(kMinimumHeight);

    return max(sMinimumHeight, sText.cy + (sVerticalPadding * 2) + sTopBorder);
}

xpr_size_t StatusBar::IdToIndex(xpr_size_t aPaneId) const
{
    xpr_size_t i;
    PaneItem *sPaneItem;
    PaneDeque::const_iterator sIterator;

    sIterator = mPaneDeque.begin();
    for (i = 0; sIterator != mPaneDeque.end(); ++i, ++sIterator)
    {
        sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        if (sPaneItem->mPaneId == aPaneId)
        {
            return i;
        }
    }

    return InvalidIndex;
}

xpr_bool_t StatusBar::removePane(xpr_size_t aIndex)
{
    if (!FXFILE_STL_IS_INDEXABLE(aIndex, mPaneDeque))
        return XPR_FALSE;

    if (XPR_IS_NOT_NULL(mObserver))
    {
        mObserver->onStatusBarRemove(*this, aIndex);
    }

    PaneDeque::iterator sIterator = mPaneDeque.begin() + aIndex;

    PaneItem *sPaneItem = *sIterator;
    XPR_SAFE_DELETE(sPaneItem);

    mPaneDeque.erase(sIterator);

    recalcLayout();

    if (XPR_IS_NOT_NULL(mObserver))
    {
        mObserver->onStatusBarRemoved(*this);
    }

    return XPR_TRUE;
}

void StatusBar::removeAllPanes(void)
{
    xpr_size_t i;
    PaneItem *sPaneItem;
    PaneDeque::iterator sIterator;

    sIterator = mPaneDeque.begin();
    for (i = 0; sIterator != mPaneDeque.end(); ++sIterator, ++i)
    {
        sPaneItem = *sIterator;

        if (XPR_IS_NOT_NULL(mObserver))
        {
            mObserver->onStatusBarRemove(*this, i);
        }

        XPR_SAFE_DELETE(sPaneItem);
    }

    mPaneDeque.clear();

    recalcLayout();

    if (XPR_IS_NOT_NULL(mObserver))
    {
        mObserver->onStatusBarRemoveAll(*this);
    }
}

void StatusBar::OnSize(xpr_uint_t aType, xpr_sint_t cx, xpr_sint_t cy)
{
    super::OnSize(aType, cx, cy);

    recalcLayout();
}

void StatusBar::recalcLayout(xpr_bool_t aRedraw)
{
    CRect sClientRect;
    GetClientRect(&sClientRect);

    const xpr_sint_t sWidth  = sClientRect.Width();
    const xpr_sint_t sHeight = sClientRect.Height();

    if (sWidth <= 0 || sHeight <= 0)
        return;

    const xpr_size_t sPaneCount = mPaneDeque.size();
    if (sPaneCount == 0)
        return;

    const xpr_sint_t sGap = scaleMetric(kPaneGap);
    const xpr_sint_t sTopBorder = max(1, scaleMetric(kTopBorder));
    const xpr_sint_t sWidthWithoutGap =
        sWidth - (((xpr_sint_t)sPaneCount - 1) * sGap);

    xpr_sint_t sTotalFixedSize = 0;
    PaneItem *sPaneItem;
    PaneDeque::iterator sIterator;

    sIterator = mPaneDeque.begin() + 1;
    for (; sIterator != mPaneDeque.end(); ++sIterator)
    {
        sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        sTotalFixedSize += (xpr_sint_t)sPaneItem->mSize;
    }

    xpr_sint_t sFirstPaneSize = sWidthWithoutGap - sTotalFixedSize;

    xpr_sint_t sLeft = 0;
    const xpr_sint_t sTop = sTopBorder;
    const xpr_sint_t sBottom = sClientRect.bottom;
    xpr_size_t i;

    sIterator = mPaneDeque.begin();
    for (i = 0; sIterator != mPaneDeque.end(); ++sIterator, ++i)
    {
        sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        sPaneItem->mPaneRect.SetRectEmpty();

        sPaneItem->mPaneRect.left   = sLeft;
        sPaneItem->mPaneRect.right  = sLeft;
        sPaneItem->mPaneRect.top    = sTop;
        sPaneItem->mPaneRect.bottom = sBottom;

        if (i != 0)
        {
            sPaneItem->mPaneRect.right = sLeft + (xpr_sint_t)sPaneItem->mSize;
        }
        else
        {
            if (sFirstPaneSize < (xpr_sint_t)sPaneItem->mMinSize)
                sFirstPaneSize = (xpr_sint_t)sPaneItem->mMinSize;

            sPaneItem->mPaneRect.right = sLeft + sFirstPaneSize;
        }

        sLeft = sPaneItem->mPaneRect.right + sGap;
    }

    if (XPR_IS_TRUE(aRedraw))
        Invalidate(XPR_FALSE);
}

void StatusBar::OnPaint(void)
{
    CPaintDC sPaintDC(this);

    CRect sClientRect;
    GetClientRect(&sClientRect);
    if (sClientRect.IsRectEmpty())
        return;

    const fxfile::ui::ThemePalette sPalette = fxfile::ui::ModernUI::getPalette();
    const COLORREF sBackgroundColor =
        XPR_IS_TRUE(sPalette.mHighContrast) ?
        sPalette.mWindow :
        sPalette.mChrome;
    const COLORREF sSeparatorColor =
        XPR_IS_TRUE(sPalette.mHighContrast) ? sPalette.mBorder : sPalette.mSeparator;

    CDC sMemDC;
    sMemDC.CreateCompatibleDC(&sPaintDC);
    sMemDC.SetBkMode(TRANSPARENT);
    sMemDC.SetTextColor(sPalette.mText);

    CBitmap sBitmap;
    sBitmap.CreateCompatibleBitmap(&sPaintDC, sClientRect.Width(), sClientRect.Height());

    CBitmap *sOldBitmap = sMemDC.SelectObject(&sBitmap);
    sMemDC.FillSolidRect(&sClientRect, sBackgroundColor);

    const xpr_sint_t sLineWidth = max(1, scaleMetric(1));
    const xpr_sint_t sTextPadding = scaleMetric(kTextPadding);
    const xpr_sint_t sSeparatorInset = scaleMetric(kSeparatorInset);

    CPen sSeparatorPen(PS_SOLID, sLineWidth, sSeparatorColor);
    CPen *sOldPen = sMemDC.SelectObject(&sSeparatorPen);
    CFont *sOldFont = XPR_NULL;
    if (XPR_IS_NOT_NULL(mFont.m_hObject))
        sOldFont = sMemDC.SelectObject(&mFont);

    sMemDC.MoveTo(0, 0);
    sMemDC.LineTo(sClientRect.right, 0);

    xpr_sint_t i;
    PaneDeque::iterator sIterator;
    PaneItem *sPaneItem;
    CRect sPaneRect;

    sIterator = mPaneDeque.begin();
    for (i = 0; sIterator != mPaneDeque.end(); ++sIterator, ++i)
    {
        sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        sPaneRect = sPaneItem->mPaneRect;

        CRect sPaneTextRect(sPaneRect);
        if (i > 0)
        {
            sMemDC.MoveTo(sPaneRect.left, sPaneRect.top + sSeparatorInset);
            sMemDC.LineTo(sPaneRect.left, max(sPaneRect.top + sSeparatorInset, sPaneRect.bottom - sSeparatorInset));

            sPaneTextRect.DeflateRect(sLineWidth + sTextPadding, 0, sTextPadding, 0);
        }
        else
        {
            sPaneTextRect.DeflateRect(sTextPadding, 0, sTextPadding, 0);
        }

        sMemDC.DrawText(
            sPaneItem->mText.c_str(),
            (xpr_sint_t)sPaneItem->mText.length(),
            sPaneTextRect,
            DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_END_ELLIPSIS);
    }

    if (XPR_IS_NOT_NULL(sOldFont))
        sMemDC.SelectObject(sOldFont);
    sMemDC.SelectObject(sOldPen);

    sPaintDC.BitBlt(0, 0, sClientRect.Width(), sClientRect.Height(), &sMemDC, 0, 0, SRCCOPY);

    sMemDC.SelectObject(sOldBitmap);
}

xpr_bool_t StatusBar::OnEraseBkgnd(CDC *aDC)
{
    return XPR_TRUE;
    return super::OnEraseBkgnd(aDC);
}

void StatusBar::createFont(void)
{
    LOGFONT sLogFont = {0};
    if (XPR_IS_TRUE(fxfile::ui::ModernUI::getUIFont(sLogFont, GetSafeHwnd())))
    {
        if (mFont.CreateFontIndirect(&sLogFont) == XPR_FALSE)
            mFont.CreateStockObject(DEFAULT_GUI_FONT);
    }
    else
    {
        mFont.CreateStockObject(DEFAULT_GUI_FONT);
        if (XPR_IS_NOT_NULL(mFont.m_hObject))
            ::GetObject(mFont.m_hObject, sizeof(sLogFont), &sLogFont);
    }

    if (XPR_IS_NOT_NULL(mFont.m_hObject))
        SetFont(&mFont, XPR_TRUE);

    sLogFont.lfWeight = FW_BOLD;
    if (mBoldFont.CreateFontIndirect(&sLogFont) == XPR_FALSE)
        mBoldFont.CreateStockObject(DEFAULT_GUI_FONT);
}

void StatusBar::recreateFont(void)
{
    destroyFont();
    createFont();
}

void StatusBar::destroyFont(void)
{
    if (XPR_IS_NOT_NULL(mFont.m_hObject)) mFont.DeleteObject();
    if (XPR_IS_NOT_NULL(mBoldFont.m_hObject)) mBoldFont.DeleteObject();
}

xpr_sint_t StatusBar::scaleMetric(xpr_sint_t aValue) const
{
    return fxfile::ui::ModernUI::scaleForWindow(aValue, GetSafeHwnd());
}

void StatusBar::updateDynamicPaneSize(PaneItem *aPaneItem)
{
    if (XPR_IS_NULL(aPaneItem))
        return;

    xpr_size_t sSize = 0;

    if (aPaneItem->mText.empty() == XPR_FALSE)
    {
        CClientDC sClientDC(this);
        CFont *sOldFont = XPR_NULL;
        if (XPR_IS_NOT_NULL(mFont.m_hObject))
            sOldFont = sClientDC.SelectObject(&mFont);

        SIZE sTextExtent = {0};
        ::GetTextExtentPoint32(
            sClientDC.m_hDC,
            aPaneItem->mText.c_str(),
            (xpr_sint_t)aPaneItem->mText.length(),
            &sTextExtent);

        if (XPR_IS_NOT_NULL(sOldFont))
            sClientDC.SelectObject(sOldFont);

        const xpr_sint_t sTextPadding = scaleMetric(kTextPadding);
        const xpr_sint_t sOffset = scaleMetric(aPaneItem->mDynamicOffset);
        const xpr_sint_t sSeparatorWidth = max(1, scaleMetric(1));

        sSize = static_cast<xpr_size_t>(
            max(0, sTextExtent.cx + sOffset + (sTextPadding * 2) + sSeparatorWidth));
    }

    if (aPaneItem->mMinSize != 0)
        sSize = max(sSize, aPaneItem->mMinSize);

    aPaneItem->mSize = sSize;
}

void StatusBar::refreshMetrics(void)
{
    PaneDeque::iterator sIterator = mPaneDeque.begin();
    for (; sIterator != mPaneDeque.end(); ++sIterator)
    {
        PaneItem *sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        sPaneItem->mMinSize = static_cast<xpr_size_t>(
            max(0, scaleMetric(static_cast<xpr_sint_t>(sPaneItem->mLogicalMinSize))));

        if (XPR_IS_TRUE(sPaneItem->mDynamicSize))
        {
            updateDynamicPaneSize(sPaneItem);
        }
        else
        {
            sPaneItem->mSize = static_cast<xpr_size_t>(
                max(0, scaleMetric(static_cast<xpr_sint_t>(sPaneItem->mLogicalSize))));
        }
    }
}

void StatusBar::OnSettingChange(xpr_uint_t aFlags, const xpr_tchar_t *aSection)
{
    recreateFont();
    refreshMetrics();
    recalcLayout();
    Invalidate(XPR_FALSE);

    super::OnSettingChange(aFlags, aSection);
}

LRESULT StatusBar::OnDpiChanged(WPARAM aWParam, LPARAM aLParam)
{
    recreateFont();
    refreshMetrics();
    recalcLayout();
    Invalidate(XPR_FALSE);
    return 0;
}

LRESULT StatusBar::OnThemeChanged(WPARAM aWParam, LPARAM aLParam)
{
    Invalidate(XPR_FALSE);
    return 0;
}

xpr_size_t StatusBar::hitTest(const POINT &aPoint) const
{
    xpr_size_t i;
    PaneItem *sPaneItem;
    PaneDeque::const_iterator sIterator;

    sIterator = mPaneDeque.begin();
    for (i = 0; sIterator != mPaneDeque.end(); ++i, ++sIterator)
    {
        sPaneItem = *sIterator;
        if (XPR_IS_NULL(sPaneItem))
            continue;

        if (sPaneItem->mPaneRect.PtInRect(aPoint) == XPR_TRUE)
            return i;
    }

    return InvalidIndex;
}

void StatusBar::OnLButtonDblClk(xpr_uint_t aFlags, CPoint aPoint)
{
    if (XPR_IS_NOT_NULL(mObserver))
    {
        xpr_size_t sIndex = hitTest(aPoint);

        mObserver->onStatusBarDoubleClicked(*this, sIndex);
    }

    super::OnLButtonDblClk(aFlags, aPoint);
}

void StatusBar::OnContextMenu(CWnd *aWnd, CPoint aPoint)
{
    CPoint sClientPoint(aPoint);
    ScreenToClient(&sClientPoint);

    if (XPR_IS_NOT_NULL(mObserver))
    {
        xpr_size_t aIndex = hitTest(sClientPoint);

        mObserver->onStatuBarContextMenu(*this, aIndex, aPoint);
        return;
    }

    super::OnContextMenu(aWnd, aPoint);
}

LRESULT StatusBar::OnSetText(WPARAM aWParam, LPARAM aLParam)
{
    const xpr_tchar_t *sText = (const xpr_tchar_t *)aLParam;

    setPaneText(0, sText);

    return XPR_TRUE;
}
