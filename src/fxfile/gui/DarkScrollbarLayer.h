// Copyright (c) 2026 flyExplorer contributors. GPLv3.
//
// UI-02: keep Windows' native scrollbar input/range/accessibility while an
// independently pumped, click-through owned popup owns the final Dark pixels.
#ifndef __FXFILE_GUI_DARK_SCROLLBAR_LAYER_H__
#define __FXFILE_GUI_DARK_SCROLLBAR_LAYER_H__ 1
#pragma once

#include "ModernUI.h"

namespace fxfile
{
namespace ui
{
class DarkScrollbarLayer
{
public:
    // Calls from the control's owning UI thread, never from WM_NCPAINT.
    // In Light/System-light and High Contrast, do not register this HWND.
    static void enable(HWND aControl, const ThemePalette &aPalette);
    static void disable(HWND aControl);
};
}
}
#endif // __FXFILE_GUI_DARK_SCROLLBAR_LAYER_H__
