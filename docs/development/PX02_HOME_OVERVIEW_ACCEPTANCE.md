# PX02 unified Home overview — scoped acceptance (2026-10-28)

## Later scoped viewport/visual acceptance (2026-10-29)

[Home compact viewport review](PX02_HOME_VISUAL_REVIEW_20261029.md) records a separately observed restore/shrink clipping defect, its bounded layout fix, exact tested blobs and incremental Release, actual Light/Dark screens, Dark bookmark focus, and normal-exit/data-preservation evidence. It preserves the original functional acceptance below; only that documented screen slice is newly accepted. Populated history, other displays and whole-product visual acceptance remain outside scope.

## Shipped behavior

The Home command on the main navigation bar and the sidebar now opens **one bounded top-of-pane Home overview**, rather than silently navigating to the user's home folder. A dedicated **사용자 폴더 열기** button preserves the old destination. The overview combines:

- Saved flyExplorer **bookmarks** (up to four visible shortcut tiles, with total count and the existing bookmark manager for the complete list).
- **Recently opened files** (up to four preview tiles using the existing guarded asynchronous default-app opener).
- **Frequently visited folders** (up to four preview tiles using the existing folder navigation).

Each tile is checked against the **current** bookmark/history model before navigation or open, not a stale row number. The overview is closed when a separate management panel is opened or a folder is navigated. Existing bookmark changes, accepted native navigations, successful file openings, and recent-history changes refresh the overview when visible.

**Privacy:** session activity remains OFF by default. The Home panel neither reads Explorer activity nor scans private files, Shell/cloud providers or the user's library automatically. The user must explicitly enable the existing session activity checkbox to populate recent/frequent lists. OFF, ON with no entries, and ON with entries have separate accessible states. Opt-out clears all activity, and app exit discards the in-memory history. Bookmark persistence stays in the preexisting private bookmark store; Home does not enable persistent activity tracking.

The Home overview is a **bounded application panel**, not a full recreation of Windows Explorer Home's Quick access, cloud recommendations, OneDrive status or all Home navigation affordances.

## Evidence

- **Focused Windows source and compatibility:** [owned Windows result](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-px02-unified-home-source-20261028.json), at flyExplorer source `1b8989e1cc051c74fdd2564f97a5e35b25e0b3ec`: `PX02_HOME_SOURCE=5/5 PASS`, `PX02_RECENT_ACTIVITY_COMPAT=5/5 PASS`, and `PX02_OWNED_WORKSPACE_REMOVED=True`. Later changes only named the XAML Home action buttons, added GUI runner/test routing, and corrected test-only UIA visibility assumptions; product navigation/model C++ behavior was unchanged.
- **Exact Windows Release and GUI:** [central CI #40684241689](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40684241689) on the final pre-documentation main source `66b2c6a4f3f10762855f21e83ea66aae7f86d8e2`: `runner-health PASS`, `gui-dependencies PASS`, `release-build PASS EXIT=0`, `functional-px02-home-overview PASS EXIT=0`, diagnostic `NOT_FINAL_ACCEPTANCE=1`. CI compiled from exact trusted source, used the one isolated GUI oracle only, and retired its owned 3.2GB build workspace.
- **Actual accepted GUI markers:** the [retained, read-only Windows GUI log](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-px02-home-accepted-gui-log-20261028.json) proves `PX02_HOME_DEFAULT_PRIVACY_OFF=PASS`, `PX02_HOME_BOOKMARK_AGGREGATED=PASS`, `PX02_HOME_SESSION_OPT_IN_EMPTY=PASS`, `PX02_HOME_OPTED_IN_EMPTY_NO_BACKFILL=PASS`, `PX02_HOME_BOOKMARK_NAVIGATION=PASS`, `PX02_HOME_APP_NORMAL_EXIT True`, `PX02_HOME_LEGACY_PROFILE_UNCHANGED True`, `PX02_HOME_OWNED_FILE_PRESERVED True`, and `PX02_HOME_OWNED_WORKSPACE_REMOVED=True`.
- **Failed attempts retained honestly:** earlier [GUI #40682261369](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40682261369) compiled successfully but its test incorrectly required a collapsed UIA panel to be present; [GUI #40683182855](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40683182855) confirmed visible Home and bookmark/default-OFF behavior, then failed by querying an unexposed StackPanel rather than the visible management checkbox. Only the owned UIA oracle was corrected to use actual accessible controls; neither failed run is counted as a GUI pass.

## Explicitly outside acceptance

The accepted scenario does **not** exercise populated session-history tiles, high-DPI/Narrator/screenshot visual parity, external/cloud providers, Windows Explorer full Home equivalence, permanent recent-history persistence, cross-user history, or private library scans. The broader source/policy/Release suite retains its independently observed unrelated historical global source failures; a scoped GUI/Release pass does not override them.

This local unified-Home feature slice is **complete within the evidence above**. Do not rerun its successful GUI or multiply opt-in permutations automatically. Next prioritized different feature area: PX06 search-scope/result usability, or a separately reproduced product regression. Excluded G03–G05 and stopped G07 remain untouched.
