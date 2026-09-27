# Native Windows UI evidence workflow (2026-09-27)

This is an opt-in **local evidence collector**, not proof of visual PASS.
It runs separately from the active local_ci.bat x64 build and manually
restricted GitHub Actions.

## Prerequisites and isolation

1. On an interactive, unlocked Windows PC, run local_ci.bat x64, inspect the
   result and start the newly built bin/x64/fxfile.exe. The probe rejects a
   missing build-revision.txt or revision mismatch with checkout HEAD.
   Skipped startup checks remain NOT TESTED.
2. Start flyExplorer with a separate test configuration and **synthetic**
   folders/bookmarks. The --synthetic-fixture flag is acknowledgement, not
   proof of isolation. Captures can expose visible personal file names.
   Never commit captures or upload unreviewed private screen contents.
3. Install test-only dependencies on that machine:
   py -m pip install Pillow psutil pywinauto
4. For UI-02 use a single-pane test layout with exactly one visible target
   list/tree and overflowing synthetic contents. Use --window-title to
   disambiguate visible settings/search dialogs for snapshots.

## Capture and compare

From the repository root after starting the current binary:

~~~powershell
py -m unittest discover -s build -p "test_visual_ui_probe.py" -v

py build\visual_ui_probe.py ui02 --synthetic-fixture --label UI02_dark_list --control list --orientation vertical
py build\visual_ui_probe.py ui02 --synthetic-fixture --label UI02_dark_tree --control tree --orientation horizontal

py build\visual_ui_probe.py snapshot --synthetic-fixture --label UI09_dark_after
py build\visual_ui_probe.py snapshot --synthetic-fixture --label UI10_filter_light --window-title "localized dialog title"

py build\visual_ui_probe.py compare baseline.png current.png --output logs\visual-ui\ui09-diff.png
~~~

The probe saves screenshots and manifest.json to local logs/visual-ui.
Existing gitignore rules exclude the log directory. UI-02 captures twelve
pressed frames plus native scrollbar/drag geometry, actual thumb movement,
source revision, executable SHA-256 and DPI. Missing thumb motion produces
INCONCLUSIVE_NO_THUMB_MOVEMENT.
The manifest also records initial_bright_ratio, drag_bright_ratios and
possible_native_brightening_frames. This threshold is a **heuristic triage**
for suspected reappearance of an OS-bright scrollbar during thumb tracking,
not a validated image classifier and never sufficient to assign FAIL/PASS. Comparison returns REVIEW_REQUIRED or
NO_DIFFERENCE_NOT_VISUAL_PASS. Neither establishes visual PASS.

## Revision-matched acceptance cases

| Case | Windows action and required evidence |
| --- | --- |
| UI-01 | Create multiple settings pages and apply Light/Dark/System while changing General → Appearance → Filtering without reopening. Selected title and actually visible page must agree. |
| UI-02 | Capture file-list vertical and tree horizontal/vertical scrollbars during Dark native thumb tracking; compare Light/System/High Contrast. Verify arrows, junction, wheel, keyboard and real thumb drag. Current post-native overlay is not a proven final-pixel owner. |
| UI-03/04/10 | Inspect search edit/dropdown/button, reorder labels and focused/unfocused filter selection under Light/Dark/High Contrast. |
| UI-05/07/08 | Compare fresh and saved command band arrangements, chevrons, tab close/plus, split panes, shared vs independent trees and layout persistence. |
| UI-06 | On a small work area inspect app popup and chevron overflow, keyboard and submenus; differentiate OS-owned outer border. |
| UI-09 | With synthetic bookmarks apply Light ↔ Dark/System. Compare same-theme screenshots at fixed window geometry for fragments under icons/text; reopening is not acceptance. |
| UI-11/12/13/14 | Distinguish fresh 280-DIP name/225-DIP date defaults from saved user widths. Inspect long tree-name tooltip, adaptive contents area and header/focus in narrow/wide layouts. |

Keep fixture, executable/revision, window size, theme and DPI identical
for a pixel comparison. Expand to 100/125/150/200% DPI and High Contrast
but record only combinations actually run. A screenshot cannot independently
establish responsiveness, keyboard behavior, accessibility or drag/drop PASS.

## Remaining blocker

No Windows device is currently connected to this chat. The latest product
revision has no new Windows build or final-pixel runtime evidence from this
checkpoint. This tool enables a connected Windows agent to collect evidence
later; until then unresolved cases remain OPEN or SOURCE UPDATED / RETEST OPEN.
Record findings in the existing UI audit and preserve ERROR_HISTORY chronology.
Do not dispatch hosted Actions implicitly.
