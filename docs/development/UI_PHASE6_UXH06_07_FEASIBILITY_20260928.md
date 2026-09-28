# Phase 6 UXH-06/07 native feature-overlap review

Reviewed 2026-09-28, baseline main cd96de0bc8fba13a7cfeee4e5f9da9a6dc30c7c5.
STATUS: FEASIBILITY REVIEW COMPLETE. NO NEW PRODUCT FEATURE IMPLEMENTED.
The original user settings were not changed. This is not a
new Release build or a complete DPI/accessibility certification.

## UXH-06 ? search scope and path presentation

Existing code reviewed: src/fxfile/search_dlg.cpp, search_loc_dlg.cpp,
search_loc_edit_dlg.cpp, cmd_search.cpp and conf_dir.cpp.

| Feature | Current code evidence |
| --- | --- |
| Editable search location | Native ComboBoxEx, filesystem autocomplete, full editable scope and multi-path parsing |
| Reuse current folder | Existing search-visible command and native current-folder button |
| Saved named scope groups | Existing manage/add/edit dialog; separate fxfile-search_dir.conf reads and writes named multi-location include/subfolder definitions |
| Temporary custom scopes | In-dialog custom path choices; no separate persistent typed-recent-location feature established |
| Search name query history | Existing saved search-name combo in DlgState, not proof of persisted location history |

Actual isolated Windows 11 native GUI test, 96 DPI:
An owned synthetic group was installed through a private UTF-16
search-dir file. The real owner-drawn location combo had 10
entries in this owned profile. Its exact label was NOT read:
the owner-drawn external text APIs were not reliable here.
Physical keyboard input supplied a 165-character synthetic
folder path to the 240px-wide native location edit. The
complete value remained byte-for-byte equal after Home and End,
and the existing current-folder button was visible. This
shows data retention, NOT a completely visible long path,
working horizontal-scroll animations or a passed full-path tooltip.
Accepted test log: logs/uxh06-owned-scope-feasibility.log.

One earlier external diagnostic tried retrieving an owner-drawn
label via cross-process CBEM_GETITEMW; it was unsafe and the
dedicated owned test process was force-stopped. This was an
invalid diagnostic, not a reproduced normal-product hang.
That call was removed from the final accepted harness; its
negative history is retained only in ignored local logs.
The accepted final process exited normally and original
user configuration hashes were identical.

New persistent recent locations would overlap existing saved
named groups and require explicit retention/deletion privacy
rules; no user demand was established. A display-only
expandable full scope or accessible tooltip has a plausible
narrow-field use but needs an independently verified
long path, semicolon/Shell folder, keyboard and spoken-reader
acceptance scenario before product implementation.
UXH-06 REVIEW COMPLETE; IMPLEMENTATION DEFERRED.

## UXH-07 ? multi-pane saved state versus named workspaces

Reviewed option.h/option.cpp, cfg_general_startup_dlg.cpp,
explorer_view.cpp, main_frame.cpp, bookmarks and working folders.

Existing main profile contains pane row/column count, ratios,
per-view selected tabs, tab folder paths, histories and layouts.
Each view independently supports startup None, Explicit Folder,
Last Folder and Last Tabs. Actual multi-tab saves occur
when that view chooses Last Tabs. Existing working-folder slots
and bookmarks provide additional one-action folder navigation.
A separately named, multiple workspace-snapshot manager was
not identified in these inspected canonical source/schema
paths; that is not proof of its absence in every extension.

Actual isolated Windows 11 native GUI test, 96 DPI:
The owned test main profile specified 1x2 and distinct
synthetic saved folder paths with Last Tabs for both views.
Two real native TabCtrl windows initially showed one
matching owned folder each. A physical Ctrl+T made two
tabs in the active view and left one in the other.
A normal exit serialized row=1, column=2 and both
pane-specific tab groups. A second distinct owned
process reusing the SAME private configuration
restored the same 1x2 layout and 2/1 tab counts.
Accepted test log: logs/uxh07-owned-session-feasibility.log.

This proved split counts, pane-specific paths, tabs,
native Ctrl+T and exit/relaunch consistency; it did
NOT measure saved splitter ratio in physical pixels,
different DPI, Shell virtual folders, or a multi-named
workspace switch. A separate named snapshot library
would need a new snapshot selection and storage format,
partial restore safety and clear replace/merge semantics.
No concrete repeat-workflow demand was established.
UXH-07 REVIEW COMPLETE; NEW NAMED PRESETS DEFERRED.

## Test ownership, boundaries and next decisions

Both tests used the released existing native executable,
private owned temporary folder fixtures, a fresh synthetic
main session file and copies of six original settings.
The six original SHA256 values remained identical after
each successful test, and final owned processes exited 0.
Test harness: build/test_ui_uxh06_07_feasibility_runtime.py.
Full evidence and temporary paths remain in ignored local
logs, not in published Git. No existing user bookmark,
personal search path or original session was executed.
No product C++ code or user configuration format changed.

A separate UXH-06 feature may be scoped only when real
users demonstrate that the narrow field makes active
scope interpretation difficult; preserve existing
search engine and current folder/named group features.
A multiple-named UXH-07 workspace may be scoped only
when last-session restore, working folders and bookmarks
are insufficient for a documented repeated workflow.

Independent remaining work: UXH-05 spoken-reader/F6 and
Tab traversal, actual 125/150/200 DPI and High Contrast,
plus separate Phase 5 WinUI 3 PRI and synchronization
productization. These remain NOT TESTED here.
No GitHub Actions were manually executed.
