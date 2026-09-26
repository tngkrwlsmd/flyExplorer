// Copyright (c) 2026 flyExplorer contributors.
#include "gui/rebar/ToolbarLayoutDamage.h"
#include "functional_test_groups.h"

namespace fxfile { namespace tests {
namespace {
bool covers(const RECT &damage, const RECT &rect)
{
    return ::IsRectEmpty(&rect) ||
        (damage.left <= rect.left && damage.top <= rect.top &&
         damage.right >= rect.right && damage.bottom >= rect.bottom);
}
}

bool testToolbarLayoutDamage(void)
{
    // Actual UI-09 sequence: paint at 36px, MFC reinserts at 22px, native
    // invalidation covers only 22px. Pixels at y=22..25 from the old icon
    // must belong to the next update region too. Exercise scaled coordinates
    // without claiming this substitutes for per-monitor DPI visual testing.
    const int dpis[] = {96, 120, 144, 192};
    for (int dpi : dpis)
    {
        const RECT oldItem = {0, 0, MulDiv(83, dpi, 96), MulDiv(36, dpi, 96)};
        const RECT newItem = {0, 0, oldItem.right, MulDiv(22, dpi, 96)};
        const std::vector<RECT> before(1, oldItem), after(1, newItem);
        const RECT damage = ui::toolbarLayoutDamage(before, after);
        if (!covers(damage, oldItem) || !covers(damage, newItem)) return false;
        const RECT unchanged = ui::toolbarLayoutDamage(after, after);
        if (!::IsRectEmpty(&unchanged)) return false;

        // Insertion, removal, wrapping and movement must damage vacated
        // positions as well as destinations, in either direction.
        const RECT moved = {100, 40, 180, 76};
        const std::vector<RECT> wrapped = {newItem, moved};
        const std::vector<std::vector<RECT>> layouts = {{}, before, after, wrapped};
        for (const auto &a : layouts)
        for (const auto &b : layouts)
        {
            const RECT change = ui::toolbarLayoutDamage(a, b);
            for (std::size_t i = 0; i < a.size(); ++i)
                if ((i >= b.size() || !::EqualRect(&a[i], &b[i])) &&
                    !covers(change, a[i])) return false;
            for (std::size_t i = 0; i < b.size(); ++i)
                if ((i >= a.size() || !::EqualRect(&a[i], &b[i])) &&
                    !covers(change, b[i])) return false;
        }
    }
    // A far-away unchanged item must not cause blanket invalidation.
    const std::vector<RECT> a = {{0, 0, 83, 36}, {500, 80, 580, 116}};
    const std::vector<RECT> b = {{0, 0, 83, 22}, {500, 80, 580, 116}};
    const RECT damage = ui::toolbarLayoutDamage(a, b);
    return damage.right == 83 && damage.bottom == 36;
}
} }
