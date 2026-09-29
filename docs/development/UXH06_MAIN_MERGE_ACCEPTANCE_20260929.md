# UXH-06 scoped main-integration acceptance — 2026-09-29


**POST-MERGE UPDATE:** UXH-06 was integrated at `2331c27`, then included in the UI-02 superseding merge; the last independently tested code-bearing main commit before this documentation-only sync was `f074a6b`. On the subsequently **rebuilt original root checkout**, native **17/0 PASS_WITH_SKIPS**, 25/25 combined contracts and test-owned full recent search/restart/clear/opt-out GUI passed. Exact ROOT EXE SHA256: `41D51B87E74C839C33124F22F63AC0C7379B61E0F32A12196D1459649AF81BAC`. The older `1EDC...` temporary candidate hash and references to unfinished UI-02 below are valid only for that earlier historical revision. [Current consolidation](BRANCH_AND_RELEASE_STATUS_20260929.md).


This document records the merge candidate based on **main 4507c1f** and original local feature commit **a0c97d6**, validated in a separate temporary worktree, not in the user's live flyExplorer profile.

## Final actual acceptance

- The clean three-way UXH-06 integration into current `main` had **no merge conflicts**. Existing current-workspace UXH-07 implementation and native scrollbar ModernUI code were retained.
- Canonical `local_ci.bat x64` **exit 0** with current merged sources: Release x64 Unicode build and warnings policy PASS; native functional regression **17 passed / 0 failed**, overall **PASS WITH SKIPS**. The standard HKCU runtime smoke was explicitly **SKIPPED** to protect the existing real user profile. The exact tested integrated executable SHA256 was `1EDC8616E732B4E5DB277773A6D57D071960B2C74B2786EB5F01DB6778AFC8EE`.
- The three original UXH-06 source contracts PASS on the actually staged new `bin/x64/Languages/Korean.xml` after canonical build. An initial contract run in the *new empty worktree*, before any build deployed its Korean.xml, failed solely because that generated staging file did not yet exist; after build the same test passed. Do not misstate this initial prebuild failure as a localized product defect.
- The updated **actual 96-DPI owned Windows GUI** `test_ui_uxh06_recent_scope_runtime.py --search --feature` PASS with a test-created **182-character scope path**. Native read-only full-scope control preserved the whole path. Physically enabling the initially unchecked Remember checkbox and successfully searching the owned directory stored exactly one recent entry. After normal app exit and a separate restart, the recent item was present; physically choosing it restored the exact long path. Clear removed the new recent list; another normal restart kept it empty and Remember unchecked. The extended harness then ran a genuinely valid new file search **without opting in**; the list remained empty during the search and after yet another owned normal restart. Existing native current-folder command stayed available.
- The six **original** Windows user `%APPDATA%\fxfile\conf` config SHA256 values were exactly identical after each owned test. All GUI operations ran through synthetic owned appdata/config/fixture paths and test-owned launched processes, not the original user's active file manager. Physical Windows GUI automation was available in this run.
- Current `main` ModernUI native scrollbar source checks PASS (19 tests), but the separate physical tree-horizontal scrollbar regression is **under investigation** and must not be misreported as resolved by UXH-06. No native main-window or scrollbar code changed in this UXH-06 merge.

## Evidence and remaining scope

Local ignored logs, under the disposable integration worktree `logs/integration-20260929`: `uxh06-merge-current-source-local-ci-x64.log`, `uxh06-merge-postbuild-contract.log`, `uxh06-owned-extended-real-gui.log`, and `uxh06-extended-opt-out-added-real-owned-gui.log`. The complete full-profile checksum records and source/binary hashes should be preserved in the original repository's ignored `logs/merge-20260929` before removing this temporary worktree.

Actual physical Korean-language presentation with a separately installed old translation pack, Windows 125/150/200% display configurations, real OS High Contrast and Narrator are **not** certified by this scoped 96-DPI English-or-user-localized GUI test. The feature does not change file search semantics or other named search scope groups.

The unrelated old **UI-02** branch's separate cross-thread worker/dark popup compositor must not be merged blindly: current `main` already implements a dedicated ModernUI dark overlay with modal hooks and High Contrast cleanup. That branch's source overlaps native ListCtrlEx/TreeCtrlEx, so it requires independent regression assessment and a non-duplicative resolution.
