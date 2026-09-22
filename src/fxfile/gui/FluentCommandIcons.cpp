//
// Copyright (c) 2026 flyExplorer contributors.
//
// Shared Microsoft Fluent command-icon runtime adapter.
//

#include "stdafx.h"
#include "FluentCommandIcons.h"

#include "../resource.h"

namespace fxfile
{
namespace ui
{
namespace
{
const COLORREF kMaskColor = RGB(255, 0, 255);

const xpr_uint_t kCommandIds[] =
{
    ID_GO_BACK,
    ID_GO_FORWARD,
    ID_GO_UP,
    ID_TOOL_FILE_SEARCH,
    ID_EDIT_CUT,
    ID_EDIT_COPY,
    ID_EDIT_PASTE,
    ID_FILE_NEW_FOLDER,
    ID_TOOL_OPTION,
};

const xpr_byte_t kSmallMasks[][32] =
{
#include "../res/fluent/generated_toolbar_masks_small.inc"
};

const xpr_byte_t kLargeMasks[][61] =
{
#include "../res/fluent/generated_toolbar_masks_large.inc"
};

xpr_sint_t findCommandIndex(xpr_uint_t aCommandId)
{
    for (xpr_size_t i = 0; i < XPR_COUNT_OF(kCommandIds); ++i)
    {
        if (kCommandIds[i] == aCommandId)
            return static_cast<xpr_sint_t>(i);
    }

    return -1;
}

HICON createMaskIcon(
    const xpr_byte_t *aMask,
    xpr_sint_t aCellSize,
    COLORREF aColor)
{
    if (XPR_IS_NULL(aMask) || (aCellSize != 16 && aCellSize != 22))
        return XPR_NULL;

    HDC sScreenDcHandle = ::GetDC(XPR_NULL);
    if (XPR_IS_NULL(sScreenDcHandle))
        return XPR_NULL;

    CDC *sScreenDc = CDC::FromHandle(sScreenDcHandle);
    CDC sMemoryDc;
    CBitmap sBitmap;

    const xpr_bool_t sReady =
        sMemoryDc.CreateCompatibleDC(sScreenDc) != FALSE &&
        sBitmap.CreateCompatibleBitmap(sScreenDc, aCellSize, aCellSize) != FALSE ?
        XPR_TRUE :
        XPR_FALSE;

    if (XPR_IS_FALSE(sReady))
    {
        ::ReleaseDC(XPR_NULL, sScreenDcHandle);
        return XPR_NULL;
    }

    CBitmap *sOldBitmap = sMemoryDc.SelectObject(&sBitmap);
    sMemoryDc.FillSolidRect(0, 0, aCellSize, aCellSize, kMaskColor);

    const xpr_sint_t sPixelCount = aCellSize * aCellSize;
    for (xpr_sint_t i = 0; i < sPixelCount; ++i)
    {
        if ((aMask[i / 8] & (0x80 >> (i % 8))) == 0)
            continue;

        sMemoryDc.SetPixelV(i % aCellSize, i / aCellSize, aColor);
    }

    sMemoryDc.SelectObject(sOldBitmap);
    ::ReleaseDC(XPR_NULL, sScreenDcHandle);

    CImageList sImageList;
    if (sImageList.Create(
            aCellSize,
            aCellSize,
            ILC_COLOR32 | ILC_MASK,
            1,
            1) == FALSE)
    {
        return XPR_NULL;
    }

    if (sImageList.Add(&sBitmap, kMaskColor) < 0)
        return XPR_NULL;

    return sImageList.ExtractIcon(0);
}
} // namespace anonymous

xpr_bool_t FluentCommandIcons::hasCommand(xpr_uint_t aCommandId)
{
    return findCommandIndex(aCommandId) >= 0 ? XPR_TRUE : XPR_FALSE;
}

HICON FluentCommandIcons::createIcon(
    xpr_uint_t aCommandId,
    xpr_sint_t aCellSize,
    COLORREF aColor)
{
    const xpr_sint_t sIndex = findCommandIndex(aCommandId);
    if (sIndex < 0)
        return XPR_NULL;

    const xpr_byte_t *sMask =
        aCellSize == 16 ?
        kSmallMasks[sIndex] :
        kLargeMasks[sIndex];

    return createMaskIcon(sMask, aCellSize, aColor);
}
} // namespace ui
} // namespace fxfile
