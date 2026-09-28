# Phase 6 UXH-04: compact command rows ? in-progress branch evidence

**STATUS: NOT ACCEPTED / NOT MERGED TO MAIN.** This evidence belongs
only to local branch `fix/uxh04-optin-temporary-compact-20260928`, based on main
`68fe5cbe86694e23c853b802e29c3841a1d4e236`.
Separate WinUI 3 experimental worktree and user files remain untouched.

## 1. Actual isolated Windows 11 baseline (96 DPI)

Owned desktop process with **copies of all six original configuration
files**; no user settings or display configuration were changed.
At a real outer 750x550 window:

| Native profile | ReBarWindow32 height | Geometry observed |
| --- | ---: | --- |
| Previously saved user toolbar layout copied into test | 141 px | Four physical visual rows: 21-px menubar + three 40-px toolbar rows |
| Fresh toolbar *layout* in owned copied profile, after normal initial startup/resize | 101 px | Same native band count 4, with drive and bookmark sharing one 40-px row |

The observed difference is **40 vertical pixels**, potentially available
to native tab/file-list content without deleting commands. Actual UIA
enumerated 34 visible accessible buttons in the saved profile and 35
in fresh-profile layout, but this is **not proof of identical command
reachability**; exact chevron and tooltip accessibility require
separate direct acceptance.

Baseline private screenshots/logs:
`logs/uxh04-saved-owned-baseline.log` and
`logs/uxh04-fresh-owned-baseline.log`.
Both baseline owned processes exited normally and original six
configuration hashes were unchanged.

## 2. Draft, opt-in change (not product-ready)

Prototype introduces a checkable menu command under **View > Tools**,
a candidate explicit reversible temporary compaction of adjacent
Drive/Bookmark ReBar bands. It uses the previously validated native
ideal-width/header measurement approach; does not delete toolbar
commands or force-reset the default/saved layout. The draft preserves
native original band width/style fields for restore and overrides
serialized temporary band values with their captured originals.
It also adds a Korean menu-string entry and a source-contract test.

Scoped Release-x64-Unicode x64 incremental **build exit 0**;
`build/test_ui_uxh04_compact_command_contract.py` **PASS**.
Built product SHA256 `3884C5DE305213F6384B5A7B4B482FEBC642A4E0E44B51E8C1A8709D63774522`.

**Do not claim the temporary restore/persistence implementation is
validated:** the target GUI did not successfully enter the compact
state, so real end-to-end restoration and saving while compact were
not exercised.

## 3. Distinguishing actual-GUI failure and next mandatory gate

The actual user-input test launched the **saved** layout at 750px,
pressed Alt+V with owned-window focus, opened its native Tools submenu,
verified the exact native command ID **33049** at popup position 16
with a real GetMenuItemRect result, and physically clicked the real
menu entry. **The native rebar stayed 141px**, not the requested
101px. That fails the core acceptance gate.
The test-owned program exited 0, the original six configuration
hashes were identical, and the isolated stored coolbar bytes
matched their pre-launch copy on this *unsuccessful* attempt.

The older owner-drawn native MFC menu exposes empty UI Automation
names even when real native menu item IDs and click rectangles
exist; the test was corrected to use real native menu IDs/rects,
rather than guessing or synthesizing WM_COMMAND.
Accessibility name for these native menus remains an independent
problem requiring real investigation; do not mark a screen reader PASS.

**Next distinguishing investigation, not yet executed:** while the
submenu is open, read MF_GRAYED state of ID 33049 and the actual
native ideal widths/header offsets of both bands; verify whether
the existing 48-DIP fit reserve disables explicit compaction
at the measured 750px width. The earlier fresh layout showed
approximately 433px Drive + 262px Bookmark visual child widths;
these are NOT independently verified equivalent to current saved
native `cxIdeal + cxHeader` values. If the fit rule is too
conservative, allow only a proven-safe user-triggered fit with
both toolbars/chevrons visible and no overlap. Distinguish a
disabled menu command from a dispatch failure **before** changing
the product, and accept only a real physical pointer interaction.

After fixing the actual cause, acceptance must cover saved/fresh
750 and wide widths, physical enable/disable/restore, exact
command reachability/chevrons/tooltips, no unrelated toolbar reset,
saving while temporarily compact with original saved layout
restored on a later launch, keyboard menu route, dark/light,
source invariants, UI-05 compaction guards, Release build,
native function tests, owned clean exits and original six hashes.
High Contrast and actual >96 DPI are separate NOT TESTED gates.

**Branch handling:** preserve this candidate **locally only**; do not
push or merge UXH-04 to main until all scoped real GUI and regression
gates pass. Existing main UXH-01/02/03 remain untouched.
