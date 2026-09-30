# Local Git and C:\dev cleanup (2026-09-29)

This report records cleanup performed on the connected Windows 11 developer machine, NOT a change to remote project history.

## Worktrees and remote branches

- Preserved `C:\dev\flyExplorer` at local UXH-07 branch `fix/uxh07-named-workspaces-20260928`, HEAD `7cc0b46`, with its existing 19 uncommitted changes including `main-window.png`. No reset, checkout, original-file cleanup or registry action.
- Preserved `C:\dev\flyExplorer-winui3-migration` at `migration/winui3-full-shell-20260929`, base HEAD `7ceeab5`, including all staged but uncommitted M0/M1/M1.5 work.
- Removed only the CLEAN former `C:\dev\flyExplorer-phase5` worktree. Its exact source commit remains accessible from the real remote `origin/experiments/phase5-productization-20260928` and the migration's shared base.
- Verified directly against the real remote: only `origin/main` and `origin/experiments/phase5-productization-20260928` exist. Pruned **21 stale local remote-tracking refs**. No remote branch was deleted; both remaining branches contain nonredundant project/recovery history.
- Removed **five redundant local Phase5 branches** only after verifying that each exact commit is reachable from the preserved Phase5 productization branch. Rollback refs: `refs/archive/cleanup-20260929/*`. The unique local Phase4, UI-02, UXH-06, active UXH-07, main and WinUI migration branches remain.

## Preserved data and reproducibility

- The old Phase5 folder held about 1.45 GiB of logs and NuGet data. Moved its pinned NuGet *package* cache atomically (1,956 files, ~1.06 GiB) into `logs/phase6-winui/nuget-packages` in the CURRENT migration worktree; verified file count, byte count and package SHA256. Unneeded duplicate NuGet HTTP download cache was not retained.
- Archived **394 historical evidence files**, including local Phase5 logs and its clean upstream Windows App SDK sample checkout, to ignored local archive `logs/cleanup-20260929/phase5-unique-evidence-20260929.zip` (4.55 MiB). Every archive entry's CRC and SHA256 were checked. ZIP SHA256: `B544924575F8D162192314844AF3C0CF0C90C7A0CF94E038EAED30FBB9CD2651`.
- `experiments/phase6_winui_shell/build.cmd` no longer references the removed Phase5 directory. After removal, an independent migration Debug x64 build succeeded using its own pinned cache. Built EXE SHA256: `12A80CFC1C7C2276C850498A260707C4627D1A3BD1434F8F94D371FDAD3DF980`.
- Observed C: free space grew from ~42.51 GiB to ~47.74 GiB. Only two flyExplorer worktree directories remain directly under `C:\dev`.

Full local rollback/evidence indexes are under ignored `logs/cleanup-20260929`: before/after refs, archived branch OIDs, evidence ZIP manifest with 394 SHA256 entries, NuGet relocation manifest and post-removal build log. The ZIP is **local-only**, not remotely backed up. No force reset, hosted Actions, push, merge, remote deletion or Git author impersonation occurred.

To recreate the OLD clean historical Phase5 source in the future, create a fresh worktree from the retained `origin/experiments/phase5-productization-20260928`. The previous compiled outputs and duplicate NuGet HTTP cache were deliberately disposable; restore local-only historical test evidence from the ZIP only when needed.

## 2026-09-30 follow-up: Phase5 tracked source retirement

- Removed the remaining tracked local `experiments/phase5_winui3` and `experiments/phase5_island_bridge` trees from the active migration branch. Their combined size was negligible; this is architecture cleanup, not disk reclamation.
- Removed the Phase5-only MFC address/island test and optional package test. Replaced them with a retirement/native-package regression contract.
- Removed the `FLYEXP_PHASE5_INCLUDE_WINUI` branch from `dist/copy.bat`; native MFC staging remains transactional and unchanged in purpose.
- Compared the migration MFC sources against protected `C:\devlyExplorer` and restored the five files whose only differences were the test-island adapter. The protected main worktree itself was not edited.
- Historical Phase5 documents, `origin/experiments/phase5-productization-20260928`, and the verified evidence ZIP described above remain the recovery path. No remote branch was deleted.
