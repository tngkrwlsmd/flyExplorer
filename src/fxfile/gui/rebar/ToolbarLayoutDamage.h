// Copyright (c) 2026 flyExplorer contributors.
#ifndef FXFILE_TOOLBAR_LAYOUT_DAMAGE_H
#define FXFILE_TOOLBAR_LAYOUT_DAMAGE_H

#include <windows.h>
#include <cstddef>
#include <vector>

namespace fxfile { namespace ui {

// Geometry is in toolbar client coordinates. A resized/moved/removed item
// damages its OLD pixels as well as its new footprint. Unchanged items do
// not enlarge the damage. The native control still invalidates state-only
// changes (hot, enabled, checked, etc.).
inline RECT toolbarLayoutDamage(
    const std::vector<RECT> &before, const std::vector<RECT> &after)
{
    RECT damage = {0, 0, 0, 0};
    const std::size_t count = before.size() > after.size() ? before.size() : after.size();
    const RECT empty = {0, 0, 0, 0};
    for (std::size_t i = 0; i < count; ++i)
    {
        const RECT &oldRect = i < before.size() ? before[i] : empty;
        const RECT &newRect = i < after.size() ? after[i] : empty;
        if (!::EqualRect(&oldRect, &newRect))
        {
            ::UnionRect(&damage, &damage, &oldRect);
            ::UnionRect(&damage, &damage, &newRect);
        }
    }
    return damage;
}

} }
#endif
