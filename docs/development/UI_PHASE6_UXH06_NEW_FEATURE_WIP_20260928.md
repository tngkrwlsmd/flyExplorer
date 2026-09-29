# UXH-06 new search-scope UI: unmerged implementation evidence

**LATER VALIDATED POST-UXH-07 INTEGRATION (2026-09-29):** This file is the preserved historical WIP status from the UXH-06 feature branch. The actual latest combined x64 binary and owned GUI have now passed the previously pending normal-exit recent persistence, physical selection, clear, restart and real opted-out search not recording. See [UXH-06 final integration acceptance and current limitations](UXH06_MAIN_MERGE_ACCEPTANCE_20260929.md). Older WIP/PENDING paragraphs below apply only to the source branch's 2026-09-28 checkpoint.


2026-09-28. **WORK IN PROGRESS ? NOT MERGED TO MAIN.**
UXH-06's earlier feasibility review found that the old native
search location edit could preserve 165 typed characters in
a 240px field, but offered no verified complete-path display
and no demonstrated automatic recent-location persistence.

New scoped feature on branch
fix/uxh06-recent-search-location-20260928:

- A keyboard-focusable READ-ONLY multiline native edit displays
  the entire selected/typed scope only when the user requests
  Full scope. Native selection/copy works without touching
  the user's clipboard on open. Search engine unchanged.
- A separate native recent-location dropdown reuses bounded
  DlgState serialization. The Remember checkbox is unchecked
  whenever Search opens; only **explicitly opted-in**
  filesystem directory searches with exactly one included
  directory and no exclusions are eligible for persistence.
  History has at most eight case-insensitively unique entries.
- Picking a recent entry feeds the existing custom native
  location edit. Clear deletes ONLY this new recent list
  and its persisted serialization on normal close; existing
  named multi-scope groups are not modified. Older installed
  language packs use the shipped English fallback; updated
  source Korean.xml contains native labels.

**Passed:** Incremental Release-x64-Unicode build with the
product change, one actual owned 96-DPI GUI run with a private
165-char folder: Full scope preview exposed all 165 chars,
checkbox was physically enabled, a real valid search
populated exactly one opt-in recent entry, existing saved
scope combobox and current-folder command were still
present, original six user-config hashes unchanged.
Full ignored logs: logs/uxh06-new-product-release-build.log
and logs/uxh06-real-native-initial-features.log.

**Pending acceptance:** Actual new-Korean-pack GUI;
owned normal-exit persistent reload; actual recent selection,
Clear and clean restart; explicit opt-out not recording;
Dark/Light and keyboard navigation, related GUI regression.
One attempted extended GUI acceptance exited early because
the remote testing environment reported **no active input
desktop** to the Python physical-pointer driver; the
test-owned process was cleaned up, original settings
remained unchanged, and the failure is not evidence
of a product defect. Do not merge until these tests pass.

Real 125/150/200% DPI and High Contrast remain NOT TESTED
on this 96-DPI user desktop. Do not change the user's
global display settings. The separate Phase 5 WinUI
experiment was not touched. Do not manually trigger
GitHub Actions.
