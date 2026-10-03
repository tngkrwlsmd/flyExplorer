# Windows 11 Explorer visual benchmark — captured 2026-10-01, product update 2026-10-03

This document preserves the measured Explorer baseline that still informs the
current product. Earlier per-version review narratives were removed; Git history
contains those checkpoints.

## Captured Explorer baseline

Reference conditions: Windows 11 File Explorer, 972x720 window, 96 DPI, Dark
theme.

Observed reference densities included approximately:
- Details rows around 24 px item height / 28 px pitch;
- List rows around 32 px;
- Explorer Medium icons using a tighter variable-height layout than flyExplorer;
- Explorer Large Icons, remeasured on 2026-10-03 with an owned fixture, at about
  105x131 px per UIA item with roughly 118x132 px pitch.

These are comparison measurements, not mandatory pixel contracts.

## Current flyExplorer decisions

- WinUI 3 custom title bar and Mica.
- Functional top-level Window TabView rather than a decorative title strip.
- Independent dual-pane model retained inside every Window Tab.
- Details/List/Small/Medium/Large view modes.
- Current Medium view uses roughly 92x92 cells in 96x96 slots with 12 px,
  two-line labels; Small uses roughly 160x32.
- Large Icons uses a 112x128 item in a 120x132 wrap slot, a 64 px visual target
  and a centered two-line label. This follows the measured Explorer Large Icons
  proportions while remaining slightly regularized for dual-pane readability.
- Medium and Large remain density-guided Explorer references rather than strict
  pixel clones.
- Shell icons/thumbnails use bounded isolated helper paths. PDF remains
  icon-only unless a future explicitly reviewed thumbnail-provider scope is
  added.
- Path-specific Known Folder artwork remains open.

## v7 ownership and persistence — implemented

The 2026-10-01 design hierarchy is now product code:

    Window
    └── WindowTab[]
        ├── LeftPane -> PaneTab[]
        └── RightPane -> PaneTab[]

Window Tab state includes split/active-pane ownership and private session schema
v2 persists Window Tabs, pane tabs, paths, view/sort/column state and bounded
filesystem history. Real restart acceptance verified two independent Window
Tabs and Back/history/split restoration.

The former pre-v7 ownership note is superseded by the implemented v7 model.

## Current remaining visual/environment gaps

- Optional Known Folder-specific artwork: not implemented.
- Actual 125/150/200% DPI: not certified in the current remote environment.
- High Contrast ON and human Narrator/Korean IME: not certified.
- Medium view is intentionally not a pixel clone of Explorer.
