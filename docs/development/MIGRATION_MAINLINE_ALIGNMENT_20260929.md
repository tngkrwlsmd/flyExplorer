# Migration/mainline alignment - current branch snapshot (2026-09-29)

This document updates **branch ownership and compatibility planning** only. The two source commit hashes below are last separately verified **code-bearing** baselines immediately before this documentation-only sync; documentation-only commits will advance Git tips without changing compiled source. The migration branch is NOT merged/rebased with the current native product, and this documentation-only change does NOT certify a new combined build, WinUI production replacement or a new M1.8 GUI run.

## Actual current branches and recovery refs

As verified from the connected Windows machine after UXH-07, UXH-06 and UI-02 consolidation, there are **exactly two local and two remote branches**, each checked out in its own worktree:

| Branch / location | Verified source revision | Role |
| --- | --- | --- |
| `main` in `C:/dev/flyExplorer` | `f074a6b1651dae6e9a1603465078310822a8f761` | Actual default MFC product with UXH-07 named workspaces, UXH-06 opt-in recent search scopes, and existing ModernUI dark native scrollbar support (old separate UI-02 renderer superseded). |
| `migration/winui3-full-shell-20260929` in `C:/dev/flyExplorer-winui3-migration` | `eb7ee1a335484d88128bfcf117a4f857fbee4c60` | Independently tested, non-default WinUI 3 M1.8 preview; no new mainline source merge. |

Old local UXH-07, UXH-06, UI-02, and Phase 4 branch names were deleted following merges or explicit supersession; old remote UXH-07 and Phase 5 names were also removed. Their unique historical commits remain protected by **local archive refs**, not active branches or new remote refs. Do not delete local archive refs during branch cleanup. The user's original untracked `C:/dev/flyExplorer/main-window.png` was protected, not added or rewritten.

## Separate evidence, NOT interchangeable

- Native `main` `f074a6b`, rebuilt at the actual original root `C:/dev/flyExplorer`: Release x64 canonical `local_ci.bat x64` exit 0, **17 native PASS / 0 FAIL, overall PASS WITH SKIPS** (real existing HKCU runtime smoke deliberately skipped). Combined source contracts **25/25 PASS** and **actual owned root** UXH-06 recent-search and **Dark** UI-02 scrollbar GUI PASS. Additional isolated merged-candidate actual **Light/Dark primary and modal scrollbar** GUI PASS. The root final binary SHA256 is `41D51B87E74C839C33124F22F63AC0C7379B61E0F32A12196D1459649AF81BAC`, NOT the earlier temporary-candidate binary hash. All six original user-setting hashes and the user's untracked screenshot were unchanged. The full original-root evidence is retained locally (ignored) under `C:/dev/flyExplorer/logs/merge-20260929/accepted-uxh06-ui02-20260929/`.
- Migration **eb7ee1a M1.8** remains the last independently verified WinUI preview revision: real owned Debug COM-hang recovery, exhausted helper timeout and actionable UX, invalid **local-loopback** UNC error, owned local Shell namespace change-notification path, real Release GUI and paired native helper/Job checks; source architecture contracts **14/14 PASS**. Original user settings were protected. Full unchanged binary/log/source manifest is ignored locally at `C:/dev/flyExplorer-winui3-migration/logs/m18/evidence-manifest.json`; the tracked detailed evidence is [M1.8 Shell stability](WINUI3_M18_SHELL_STABILITY_20260929.md).

The two branch test suites were **not run on a single merged source tree**. The historical M1.8 local evidence manifest also hashed tracked status and project documentation at the earlier eb7ee1a code-bearing revision; those **historical documentation hashes are expected to differ** after these documentation-only updates. The unchanged historic binary/log and source-code results are revision-scoped, not a new M1.8 test run. Do not extrapolate current main workspace/recent-search feature coverage, accessibility, real external provider behavior or finished file-operation parity to the WinUI preview.

## Required migration reconciliation (still OPEN)

1. Inventory the **current** native main UXH-07 named-workspace schema, save/restore contracts and settings safety, UXH-06 opt-in recent-search persistence and current MFC ModernUI UI-02 fallback behavior. Compare actual newer mainline code to the earlier migration fork. Avoid replacing independently verified M1.8 process ownership, helper protocol and watcher safety with stale older MFC code.
2. Perform a **separately scoped integration** of the new mainline native contracts into the migration branch, resolving any source, policy, status/index or schema conflicts deliberately; keep default `main` unchanged until complete product parity is proven.
3. On the NEW combined revision, rerun relevant canonical MFC native/build contracts, named-workspace/recent-search owned GUI, and WinUI paired Debug/Release/helper/Job/normal/owned-fault GUI, plus original six-settings hash checks. The current historical results above cannot certify that future revision.
4. Real physical other-DPI/OS High Contrast/Narrator, actual faulty external third-party Shell extensions, slow/offline/authenticated network SMB and genuine virtual external-provider events remain additional acceptance work, not claims of M1.8 success.

No hosted GitHub Actions, merge of migration into main, file deletion beyond previous branch cleanup, or product rollout is implied by this status reconciliation. For ongoing work, verify current Git refs and the latest real evidence rather than promoting past logs to a new revision.
