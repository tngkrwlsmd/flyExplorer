// Copyright (c) 2026 flyExplorer contributors. GPLv3.
//
// UI-02: a native scrollbar's modal thumb-tracking loop can paint after the
// owner returns and defer its posted repaint requests until button release.
// An owned, layered and click-through popup has independent final-pixel
// ownership. A single dedicated GUI thread pumps these small windows; it
// never sends scroll commands, subclasses native controls or blocks their UI.
#include "stdafx.h"
#include "DarkScrollbarLayer.h"

#include <map>
#include <mutex>
#include <process.h>
#include <oleacc.h>

namespace fxfile
{
namespace ui
{
namespace
{
const wchar_t kLayerClass[] = L"flyExplorer.DarkScrollbarLayer.v1";

COLORREF mixColor(COLORREF aBase, COLORREF aText, int aPercent)
{
    return RGB(
        (GetRValue(aBase) * (100 - aPercent) + GetRValue(aText) * aPercent) / 100,
        (GetGValue(aBase) * (100 - aPercent) + GetGValue(aText) * aPercent) / 100,
        (GetBValue(aBase) * (100 - aPercent) + GetBValue(aText) * aPercent) / 100);
}

bool equalRect(const RECT &a, const RECT &b)
{
    return ::EqualRect(&a, &b) != FALSE;
}

bool equalPalette(const ThemePalette &a, const ThemePalette &b)
{
    return a.mSurface == b.mSurface && a.mChrome == b.mChrome &&
           a.mText == b.mText && a.mSecondaryText == b.mSecondaryText &&
           a.mPressed == b.mPressed;
}

struct LayerWindow
{
    LayerWindow()
        : mHwnd(NULL), mOwner(NULL), mShown(false), mValid(false),
          mVertical(false), mCorner(false), mLastValid(0)
    {
        ::ZeroMemory(&mRect, sizeof(mRect));
        ::ZeroMemory(&mInfo, sizeof(mInfo));
        ::ZeroMemory(&mPalette, sizeof(mPalette));
    }

    HWND mHwnd;
    HWND mOwner;
    bool mShown;
    bool mValid;
    bool mVertical;
    bool mCorner;
    DWORD mLastValid;
    RECT mRect;                 // The owned popup's screen coordinates.
    SCROLLBARINFO mInfo;        // Snapshot of the actual native scroll state.
    ThemePalette mPalette;     // From the owning control's theme transition.
};

void paintLayer(HDC aDC, const LayerWindow &aLayer)
{
    const int sWidth = aLayer.mRect.right - aLayer.mRect.left;
    const int sHeight = aLayer.mRect.bottom - aLayer.mRect.top;
    if (sWidth <= 0 || sHeight <= 0)
        return;

    const ThemePalette &sPalette = aLayer.mPalette;
    RECT sRect = {0, 0, sWidth, sHeight};
    HBRUSH sBack = ::CreateSolidBrush(sPalette.mSurface);
    if (sBack != NULL)
    {
        ::FillRect(aDC, &sRect, sBack);
        ::DeleteObject(sBack);
    }
    if (!aLayer.mValid || aLayer.mCorner)
        return;

    const SCROLLBARINFO &sInfo = aLayer.mInfo;
    const int sExtent = aLayer.mVertical ? sHeight : sWidth;
    const int sButton = min(max(sInfo.dxyLineButton, 0), sExtent / 2);

    if (sButton > 0)
    {
        // A narrow native arrow target retains its original hit testing:
        // only the presentation is drawn above it.
        HPEN sPen = ::CreatePen(PS_SOLID, 1, sPalette.mSecondaryText);
        HGDIOBJ sOldPen = sPen != NULL ? ::SelectObject(aDC, sPen) : NULL;
        for (int sIndex = 0; sIndex != 2; ++sIndex)
        {
            RECT sArrow = sRect;
            if (aLayer.mVertical)
            {
                if (sIndex == 0) sArrow.bottom = sButton;
                else sArrow.top = sHeight - sButton;
            }
            else
            {
                if (sIndex == 0) sArrow.right = sButton;
                else sArrow.left = sWidth - sButton;
            }
            HBRUSH sButtonBrush = ::CreateSolidBrush(sPalette.mChrome);
            if (sButtonBrush != NULL)
            {
                ::FillRect(aDC, &sArrow, sButtonBrush);
                ::DeleteObject(sButtonBrush);
            }
            const int sStateIndex =
                aLayer.mVertical ? (sIndex == 0 ? 1 : 5) :
                                   (sIndex == 0 ? 5 : 1);
            if (sOldPen == NULL ||
                (sInfo.rgstate[sStateIndex] & STATE_SYSTEM_UNAVAILABLE) != 0)
                continue;
            const int x = (sArrow.left + sArrow.right) / 2;
            const int y = (sArrow.top + sArrow.bottom) / 2;
            const int d = max(1, min(sArrow.right - sArrow.left,
                                     sArrow.bottom - sArrow.top) / 6);
            const int direction = sIndex == 0 ? -1 : 1;
            if (aLayer.mVertical)
            {
                ::MoveToEx(aDC, x - d, y - direction, NULL);
                ::LineTo(aDC, x, y + direction * d);
                ::LineTo(aDC, x + d, y - direction);
            }
            else
            {
                ::MoveToEx(aDC, x - direction, y - d, NULL);
                ::LineTo(aDC, x + direction * d, y);
                ::LineTo(aDC, x - direction, y + d);
            }
        }
        if (sOldPen != NULL)
            ::SelectObject(aDC, sOldPen);
        if (sPen != NULL)
            ::DeleteObject(sPen);
    }

    if ((sInfo.rgstate[3] &
         (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) != 0 ||
        sInfo.xyThumbBottom <= sInfo.xyThumbTop)
        return;
    RECT sThumb = sRect;
    const int sInset = max(2, min(sWidth, sHeight) / 6);
    if (aLayer.mVertical)
    {
        sThumb.top = sInfo.xyThumbTop;
        sThumb.bottom = sInfo.xyThumbBottom;
        sThumb.left += sInset;
        sThumb.right -= sInset;
    }
    else
    {
        sThumb.left = sInfo.xyThumbTop;
        sThumb.right = sInfo.xyThumbBottom;
        sThumb.top += sInset;
        sThumb.bottom -= sInset;
    }
    sThumb.left = max(1, sThumb.left);
    sThumb.top = max(1, sThumb.top);
    sThumb.right = min(sWidth - 1, sThumb.right);
    sThumb.bottom = min(sHeight - 1, sThumb.bottom);
    if (sThumb.left >= sThumb.right || sThumb.top >= sThumb.bottom)
        return;

    // Never make the pressed thumb itself a bright native-looking rectangle.
    const int sBlend =
        (sInfo.rgstate[3] & STATE_SYSTEM_PRESSED) != 0 ? 58 : 46;
    HBRUSH sThumbBrush = ::CreateSolidBrush(
        mixColor(sPalette.mSurface, sPalette.mText, sBlend));
    if (sThumbBrush != NULL)
    {
        HGDIOBJ sOldBrush = ::SelectObject(aDC, sThumbBrush);
        HGDIOBJ sOldPen = ::SelectObject(aDC, ::GetStockObject(NULL_PEN));
        ::RoundRect(aDC, sThumb.left, sThumb.top,
                    sThumb.right, sThumb.bottom, 6, 6);
        ::SelectObject(aDC, sOldPen);
        ::SelectObject(aDC, sOldBrush);
        ::DeleteObject(sThumbBrush);
    }
}

LRESULT CALLBACK layerProc(HWND aHwnd, UINT aMsg, WPARAM aWParam, LPARAM aLParam)
{
    if (aMsg == WM_NCHITTEST)
        return HTTRANSPARENT;
    if (aMsg == WM_MOUSEACTIVATE)
        return MA_NOACTIVATE;
    if (aMsg == WM_ERASEBKGND)
        return 1;
    if (aMsg == WM_PAINT)
    {
        PAINTSTRUCT sPaint = {0};
        HDC sDC = ::BeginPaint(aHwnd, &sPaint);
        LayerWindow *sLayer = reinterpret_cast<LayerWindow *>(
            ::GetWindowLongPtr(aHwnd, GWLP_USERDATA));
        if (sDC != NULL && sLayer != NULL)
            paintLayer(sDC, *sLayer);
        if (sDC != NULL)
            ::EndPaint(aHwnd, &sPaint);
        return 0;
    }
    return ::DefWindowProc(aHwnd, aMsg, aWParam, aLParam);
}

void hideLayer(LayerWindow &aLayer)
{
    if (aLayer.mHwnd != NULL && ::IsWindow(aLayer.mHwnd) &&
        aLayer.mShown)
        ::ShowWindow(aLayer.mHwnd, SW_HIDE);
    aLayer.mShown = false;
}

void destroyLayer(LayerWindow &aLayer)
{
    if (aLayer.mHwnd != NULL && ::IsWindow(aLayer.mHwnd))
        ::DestroyWindow(aLayer.mHwnd); // Only on its owning worker thread.
    aLayer.mHwnd = NULL;
    aLayer.mOwner = NULL;
    aLayer.mShown = false;
    aLayer.mValid = false;
}

bool ensureLayer(LayerWindow &aLayer, HWND aOwner)
{
    if (aLayer.mHwnd != NULL && ::IsWindow(aLayer.mHwnd) &&
        aLayer.mOwner == aOwner)
        return true;
    destroyLayer(aLayer);
    aLayer.mOwner = aOwner;
    HWND sHwnd = ::CreateWindowEx(
        WS_EX_LAYERED | WS_EX_TRANSPARENT |
        WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
        kLayerClass, XPR_STRING_LITERAL(""), WS_POPUP,
        0, 0, 1, 1, aOwner, NULL, ::GetModuleHandle(NULL), NULL);
    if (sHwnd == NULL)
        return false;
    aLayer.mHwnd = sHwnd;
    ::SetWindowLongPtr(sHwnd, GWLP_USERDATA,
                       reinterpret_cast<LONG_PTR>(&aLayer));
    if (::SetLayeredWindowAttributes(sHwnd, 0, 255, LWA_ALPHA) == FALSE)
    {
        destroyLayer(aLayer);
        return false;
    }
    return true;
}

bool canDisplay(HWND aTarget, HWND &aOwner)
{
    if (::IsWindow(aTarget) == FALSE || ::IsWindowVisible(aTarget) == FALSE)
        return false;
    aOwner = ::GetAncestor(aTarget, GA_ROOT);
    if (aOwner == NULL || ::IsIconic(aOwner))
        return false;
    HWND sForeground = ::GetForegroundWindow();
    return sForeground != NULL &&
           ::GetAncestor(sForeground, GA_ROOT) == aOwner;
}

bool highContrast(void)
{
    HIGHCONTRAST sInfo = {sizeof(HIGHCONTRAST)};
    return ::SystemParametersInfo(
        SPI_GETHIGHCONTRAST, sizeof(sInfo), &sInfo, 0) != FALSE &&
        (sInfo.dwFlags & HCF_HIGHCONTRASTON) != 0;
}

void placeLayer(LayerWindow &aLayer, HWND aOwner, const RECT &aRect,
                const ThemePalette &aPalette,
                const SCROLLBARINFO *aInfo)
{
    const bool sGeometryChanged = !equalRect(aRect, aLayer.mRect);
    const bool sThemeChanged = !equalPalette(aPalette, aLayer.mPalette);
    bool sStateChanged = aLayer.mValid != (aInfo != NULL);
    if (aInfo != NULL && aLayer.mValid)
    {
        const SCROLLBARINFO &sOld = aLayer.mInfo;
        sStateChanged = sOld.xyThumbTop != aInfo->xyThumbTop ||
            sOld.xyThumbBottom != aInfo->xyThumbBottom ||
            sOld.dxyLineButton != aInfo->dxyLineButton ||
            ::memcmp(sOld.rgstate, aInfo->rgstate,
                     sizeof(sOld.rgstate)) != 0;
    }
    if (!ensureLayer(aLayer, aOwner))
        return;
    aLayer.mRect = aRect;
    aLayer.mPalette = aPalette;
    aLayer.mValid = aInfo != NULL;
    if (aInfo != NULL)
        aLayer.mInfo = *aInfo;
    const int sWidth = aRect.right - aRect.left;
    const int sHeight = aRect.bottom - aRect.top;
    if (sWidth <= 0 || sHeight <= 0)
    {
        hideLayer(aLayer);
        return;
    }
    if (!aLayer.mShown || sGeometryChanged)
    {
        // Owned popup: above this application, never TOPMOST over other apps.
        ::SetWindowPos(aLayer.mHwnd, HWND_TOP,
            aRect.left, aRect.top, sWidth, sHeight,
            SWP_NOACTIVATE | SWP_SHOWWINDOW);
        aLayer.mShown = true;
    }
    if (sGeometryChanged || sStateChanged || sThemeChanged)
        ::InvalidateRect(aLayer.mHwnd, NULL, FALSE);
}

struct TargetLayers
{
    TargetLayers()
    {
        mBars[0].mVertical = true;
        mBars[1].mVertical = false;
        mCorner.mCorner = true;
    }
    LayerWindow mBars[2];
    LayerWindow mCorner;

    void destroy()
    {
        destroyLayer(mBars[0]);
        destroyLayer(mBars[1]);
        destroyLayer(mCorner);
    }
    void hide()
    {
        hideLayer(mBars[0]);
        hideLayer(mBars[1]);
        hideLayer(mCorner);
    }
};

void updateBar(HWND aTarget, HWND aOwner, bool aVertical,
               const ThemePalette &aPalette, LayerWindow &aLayer)
{
    const DWORD sStyle = static_cast<DWORD>(
        ::GetWindowLongPtr(aTarget, GWL_STYLE));
    if ((sStyle & (aVertical ? WS_VSCROLL : WS_HSCROLL)) == 0)
    {
        hideLayer(aLayer);
        return;
    }
    SCROLLBARINFO sInfo = {0};
    sInfo.cbSize = sizeof(sInfo);
    if (::GetScrollBarInfo(
            aTarget, aVertical ? OBJID_VSCROLL : OBJID_HSCROLL,
            &sInfo) == FALSE)
    {
        // GetScrollBarInfo can briefly fail in native thumb tracking;
        // keep the last opaque Dark popup for a bounded 400 ms rather
        // than letting the OS-white scrollbar show through for a frame.
        if (aLayer.mShown && aLayer.mLastValid != 0 &&
            ::GetTickCount() - aLayer.mLastValid < 400)
            return;
        hideLayer(aLayer);
        return;
    }
    if ((sInfo.rgstate[0] &
         (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) != 0 ||
        sInfo.rcScrollBar.right <= sInfo.rcScrollBar.left ||
        sInfo.rcScrollBar.bottom <= sInfo.rcScrollBar.top)
    {
        hideLayer(aLayer);
        return;
    }
    aLayer.mLastValid = ::GetTickCount();
    placeLayer(aLayer, aOwner, sInfo.rcScrollBar, aPalette, &sInfo);
}

class LayerManager
{
public:
    LayerManager()
        : mWake(::CreateEvent(NULL, FALSE, FALSE, NULL)), mStarted(false)
    {
    }

    void enable(HWND aWindow, const ThemePalette &aPalette)
    {
        if (::IsWindow(aWindow) == FALSE || mWake == NULL)
            return;
        {
            std::lock_guard<std::mutex> sGuard(mMutex);
            mTargets[aWindow] = aPalette;
            if (!mStarted)
            {
                const uintptr_t sThread = ::_beginthreadex(
                    NULL, 0, &LayerManager::threadMain, this, 0, NULL);
                if (sThread != 0)
                {
                    // This one process-lifetime GUI worker is not joined from
                    // a native control's WM_DESTROY (which may be in tracking).
                    ::CloseHandle(reinterpret_cast<HANDLE>(sThread));
                    mStarted = true;
                }
            }
        }
        ::SetEvent(mWake);
    }

    void disable(HWND aWindow)
    {
        if (mWake == NULL)
            return;
        {
            std::lock_guard<std::mutex> sGuard(mMutex);
            mTargets.erase(aWindow);
        }
        ::SetEvent(mWake);
    }

private:
    static unsigned __stdcall threadMain(void *aSelf)
    {
        reinterpret_cast<LayerManager *>(aSelf)->run();
        return 0;
    }

    void run()
    {
        WNDCLASS sClass = {0};
        sClass.lpfnWndProc = layerProc;
        sClass.hInstance = ::GetModuleHandle(NULL);
        sClass.lpszClassName = kLayerClass;
        if (::RegisterClass(&sClass) == 0 &&
            ::GetLastError() != ERROR_CLASS_ALREADY_EXISTS)
            return;

        std::map<HWND, TargetLayers> sLayers;
        for (;;)
        {
            MSG sMsg;
            while (::PeekMessage(&sMsg, NULL, 0, 0, PM_REMOVE))
            {
                if (sMsg.message != WM_QUIT)
                {
                    ::TranslateMessage(&sMsg);
                    ::DispatchMessage(&sMsg);
                }
            }
            std::map<HWND, ThemePalette> sCurrent;
            {
                std::lock_guard<std::mutex> sGuard(mMutex);
                sCurrent = mTargets;
            }
            for (std::map<HWND, TargetLayers>::iterator sIt =
                     sLayers.begin(); sIt != sLayers.end(); )
            {
                if (sCurrent.find(sIt->first) == sCurrent.end())
                {
                    sIt->second.destroy();
                    sLayers.erase(sIt++);
                }
                else
                    ++sIt;
            }

            const bool sHighContrast = highContrast();
            bool sAnyShown = false;
            for (std::map<HWND, ThemePalette>::const_iterator sIt =
                     sCurrent.begin(); sIt != sCurrent.end(); ++sIt)
            {
                TargetLayers &sTarget = sLayers[sIt->first];
                HWND sOwner = NULL;
                if (sHighContrast || !canDisplay(sIt->first, sOwner))
                {
                    sTarget.hide();
                    continue;
                }
                updateBar(sIt->first, sOwner, true,
                          sIt->second, sTarget.mBars[0]);
                updateBar(sIt->first, sOwner, false,
                          sIt->second, sTarget.mBars[1]);
                LayerWindow &sV = sTarget.mBars[0];
                LayerWindow &sH = sTarget.mBars[1];
                if (sV.mShown && sH.mShown)
                {
                    RECT sCorner = {
                        sV.mRect.left, sH.mRect.top,
                        sV.mRect.right, sH.mRect.bottom
                    };
                    if (sCorner.right > sCorner.left &&
                        sCorner.bottom > sCorner.top)
                        placeLayer(sTarget.mCorner, sOwner,
                                   sCorner, sIt->second, NULL);
                    else
                        hideLayer(sTarget.mCorner);
                }
                else
                    hideLayer(sTarget.mCorner);
                sAnyShown = sAnyShown ||
                    sV.mShown || sH.mShown;
            }
            // The worker owns the compositor popup HWNDs, never the native
            // input loop. Poll at 32 ms only during real mouse tracking;
            // an inactive app waits 200 ms or indefinitely with no targets.
            const DWORD sDelay = sCurrent.empty() ? INFINITE :
                (sAnyShown && (::GetAsyncKeyState(VK_LBUTTON) & 0x8000) ?
                    32 : (sAnyShown ? 100 : 200));
            ::MsgWaitForMultipleObjects(
                1, &mWake, FALSE, sDelay, QS_ALLINPUT);
        }
    }

    std::mutex mMutex;
    std::map<HWND, ThemePalette> mTargets;
    HANDLE mWake;
    bool mStarted;
};

LayerManager &manager()
{
    // Deliberately process-scoped: do not join a worker from a native
    // WM_DESTROY/modal thumb-tracking stack. The OS releases its one event
    // and thread when the application process exits.
    static LayerManager *sManager = new LayerManager;
    return *sManager;
}
} // namespace

void DarkScrollbarLayer::enable(HWND aControl, const ThemePalette &aPalette)
{
    if (aPalette.mDark && !aPalette.mHighContrast)
        manager().enable(aControl, aPalette);
    else
        manager().disable(aControl);
}

void DarkScrollbarLayer::disable(HWND aControl)
{
    manager().disable(aControl);
}
} // namespace ui
} // namespace fxfile
