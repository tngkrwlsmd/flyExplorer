# PX06 — cancelable scoped search and honest result status (2026-10-28)

## New product behavior

The existing bounded Search pane adds an explicit accessible **검색 취소** button. It begins disabled, enables only after `SearchController::start` succeeds, and disables on cancel, completion, invalid criteria, or closing the Search panel. A cancellation calls the existing controller's ticket/epoch invalidation and worker cancellation flag. It immediately clears the visible result ListView, path-to-selection mapping and Locate button; any late completion with a superseded ticket returns `Ignored` before it can repopulate results or change controls. Rejected new search criteria also clear old displayed rows.

The Search pane now shows an accessible `SearchActiveScopeText` line naming the submitted **direct traversal versus Windows index** and exact requested scope. On completion it separately tells the user whether bounded traversal/content/result limits may have omitted entries or only indexed entries were considered. When the index is unavailable it explicitly states that no implicit direct-traversal fallback occurred. Search remains read-only, scope-bound and subject to the previous 20,000-item/depth-32/1,000-result and content I/O limits.

This is a **targeted usability improvement**, not a new Windows Search provider, whole-PC search, OneDrive search or a performance benchmark.

## Verification (exact source)

- **Product/test source SHA:** [`1b152d8222e3681e6f3a701aef922dd4e75de709`](https://github.com/tngkrwlsmd/flyExplorer/commit/1b152d8222e3681e6f3a701aef922dd4e75de709). Changed only `MainWindow.xaml`, `MainWindow.xaml.h`, `m19_features.cpp` and `test_search_controller_contract.py` relative to the preceding PX02 acceptance SHA `cf01b89f0915085cde248db932c40b51e4484a5f`.
- **Windows focused source:** [`fly-px06-search-cancel-source-20261028`](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-px06-search-cancel-source-20261028.json): `ok=true`, exit code 0, **11/11 PASS**, original Windows checkout remained clean, isolated worktree removed. The new source contract checks cancellation ticket/epoch ordering, stale result-list clearing, source-context preservation, active mode/scope summary, and partial/index-only states. Previous search source contracts remain present and were exercised in the same focused file.
- **Actual Windows Release compile:** [central run #40688186038](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40688186038) at that exact SHA: `runner-health PASS`, **Release build PASS EXIT=0**, `CENTRAL_CI_DIAGNOSTIC_PASS ... NOT_FINAL_ACCEPTANCE=1`. Compiled workspace retired by bounded CI storage policy. The central workflow uses `release-build-only` to avoid repeating previously identified unrelated global source test failures.

## Unaccepted scope

**A physical test clicking Cancel while the actual worker is in flight has not yet been executed.** Thus no real-GUI cancel acceptance, exact pointer/keyboard visibility certification, screenshot/pixel matching, or screen reader/DPI checks are claimed. A future focused owned-fixture GUI scenario can establish in-flight cancel, complete removal of results, absence of late results, and unchanged user files/profile. Do not mark the full PX06 or Windows Search parity complete on this source/build evidence.

Previously accepted PX02/PX01/M23 GUI acceptance was not rerun. Excluded G03–G05 and stopped G07 remain excluded.
