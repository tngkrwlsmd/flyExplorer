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

## 2. Historical first WIP checkpoint (superseded; not product-ready)

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

## 3. Historical initial GUI failure (diagnosis now completed below)

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


## 4. Confirmed native fit root cause and improved draft

Test-owned **in-process** native diagnostics showed both multiline
settings off, both bands visible, adjacent indexes 2 and 3 of 4,
bookmark style 641 including BREAK and USECHEVRON. Native drive
cxIdeal=421, bookmark cxIdeal=572; the respective calculated full
widths including headers/insets were **446px + 597px = 1043px**.
The old command demanded that sum fit within an available **686px**
at 750px window width or **1036px** at 1100px width, disabling the
real menu command at BOTH window sizes. All temporary product-side
diagnostics were removed after verifying these actual values.

The corrected opt-in algorithm requires two eligible visible
nonwrapping chevron-enabled adjacent native bands and reserves
48 DIP of chrome while allocating at least 180 scaled px Drive
and 200 scaled px Bookmark. It permits the native existing
chevron to display overflowing bookmarks instead of demanding
that every button fit side-by-side. It leaves the automatic
fresh-profile layout policy unchanged, does not remove commands,
and does not overwrite the persisted band arrangement.

Actual owned Windows 11 96-DPI **Dark**: clicking the real,
enabled native View > Tools > Compact menu item (ID 33049) reduced
the toolbar rebar from **141px to 101px**; physically selecting
it again restored **141px**. A separate **Light** run passed the
same pointer compact/restore sequence. Closing a separate owned
process with compact mode still active wrote the **exact same
copied original coolbar configuration bytes** as before launch.
All successful GUI sessions exited normally and the six original
user configuration files remained hash-identical.

## 5. Verified owner-drawn Bookmark chevron

The legacy rebar overflow is **not** a conventional Win32 #32768
menu, so the first external automation's class assumption
incorrectly classified the existing UI as missing. After a real
click on the right-edge chevron in the 750px compact layout,
the corrected owned GUI test observed an independent native
**Afx** popup HWND with actual geometry (790,197,870,294),
a live native child ToolbarWindow32 at (791,198,869,293),
and named UI Automation CheckBox entries including Korean
My Documents/Music/Pictures/Videos. The popup screenshot and
full child/UIA inspection remain LOCAL only under ignored logs.
The popup was dismissed without invoking potentially
user-configured bookmark targets. Thus the popup and its
accessible entries are observed, but actually invoking **every**
overflow bookmark remains NOT TESTED.

## 6. Remaining critical keyboard blocker ? do not merge

The owner-drawn Tools submenu exposes command 33049 by native
ID/rectangle, but a direct new J mnemonic did NOT apply
compaction. The standard GetMenuStringW result is empty for
this owner-drawn item; presence of a J label in resources
must NOT be mistaken for working keyboard access.

A second physical keyboard-only experiment used END/UP/UP/ENTER
after opening the submenu. It still left the rebar at **141px**,
and this experiment altered only the test-owned copied
coolbar serialization, consistent with selecting some other
toolbar operation. The actual dispatched command has NOT
been established. This attempt failed its own test and does
NOT establish a keyboard route or saved-layout preservation
for keyboard actions. Do NOT repeat blind positional Enter.
A safe follow-up must first observe the exact highlighted
native ID 33049 using menu state before any Enter, and
only then test actual keyboard activation. Otherwise dismiss
the menu with Escape without modifying the copied profile.
Preserve the user profile and baseline main throughout.

## 7. Other successfully completed scoped gates

- Updated candidate incremental x64 Release-x64-Unicode build PASS.
- Source invariants, existing UI-05 fresh-profile negative
  compaction guards, new UXH-04 command source contract PASS.
- Native functional regressions **17 PASS, 0 FAIL**.
- Fresh-profile default retained its measured 101px rebar at
  both actual 750px and 1100px; originals untouched.
- Last tested candidate Release executable SHA256
  \`8CF631B0B057E371F833A21104241CCA2630DE9A2AA891787868F34732EB8AE8\`.
- Dark/Light pointer, existing custom bookmark chevron popup,
  and test-owned save-while-compact PASS.
- Keyboard submenu dispatch **FAILED**, therefore UXH-04
  remains **UNMERGED and local only**. This cannot count as
  a complete UI/UX change or an approved product release.

Key local-only logs: uxh04-fixed-real-menu-exercise.log,
uxh04-final-retry-light.log, uxh04-final-retry-save.log,
uxh04-scoped-final-chevron.log,
uxh04-scoped-final-keyboard.log,
uxh04-scoped-source-invariants.log,
uxh04-scoped-source-ui05.log,
uxh04-scoped-source-command.log,
uxh04-scoped-source-native.log.
Actual other DPI, Windows High Contrast, physical screen-reader
listening, and per-item activation in every overflow popup
remain independently NOT TESTED. No GitHub Actions runs.
