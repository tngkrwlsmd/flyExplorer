# Windows VM Runner retirement and central request routing

Status: 2026-10-10. The repository-scoped `flyExplorer` GitHub Actions Runner was unregistered and its login scheduled task was removed. The `personal-control-plane` Windows service is now the sole VM GitHub Runner.

## Verified archive inventory

The retired VM runner was `DESKTOP-FJM09OG` at `C:\actions-runner\flyExplorer` (runner package 2.337.0). The directory was intentionally **not deleted**. A read-only inventory established:

- `C:\dev\flyExplorer`: Git checkout at `387efa622f6a9ce6685e3bffb98299df0503de3c`; no tracked changes or untracked files.
- `C:\actions-runner\flyExplorer\_work\flyExplorer\flyExplorer`: Git checkout at `dd658b14eebd4b79138a4efbc262077b0fe30f58`; no tracked changes. Its two untracked entries were `__evidence_repo/` and `__evidence_tooling/`, the evidence checkout and source-tooling checkout produced by the old workflow.
- **Preserved Git evidence**: branch `evidence/remote-windows`, especially `runs/<run-id>/manifest.json`, `remote-result.json` and allowlisted `markers.json`. This is the independent, non-secret archive and remains distinct from product `main`. Original Actions run logs remain attached to historical runs, subject to GitHub retention.
- The old `control/remote-shell` branch and former workflow files remain recoverable through Git history even after decommissioning; no request transcript needs to be copied into `main`.

Runner credentials (`.credentials*`, `.runner`, tokens), environment settings, diagnostic logs, `_diag`, `_temp`, binaries, generated builds, caches and unchecked screenshots are **not** repository archive inputs. No claim is made that unreviewed local logs or transient desktop material were backed up. Do not delete the retained VM directory without a separate inventory and removal decision.

## Where Windows work goes now

**The authoritative execution entry point is `tngkrwlsmd/personal-control-plane`.** This source repository no longer owns a Windows self-hosted Runner, Remote Windows Task, or Windows VM Build workflow.

| Prior invocation | Current request |
| --- | --- |
| Windows VM Build `source` | Central Registered Projects CI, `desktop-a`, `source` |
| Windows VM Build `release` | Central Registered Projects CI, `desktop-a`, `release` |
| Windows VM Build `release-gui` | Central Registered Projects CI, `desktop-a`, `gui` |
| Windows VM Build `full` | **No exact equivalent**. Debug+Release full-suite acceptance requires a separately approved and explicitly specified central Remote Shell job; a central `gui` PASS does not certify Debug or the old `full` scope. |
| Remote Windows Task diagnostic/development command | `personal-control-plane` Remote Shell request, target `windows-vm`, against an explicitly checked source ref/working directory |
| Remote Windows Task evidence publishing | Existing Git branch `evidence/remote-windows` for historical bounded data; current central GUI failures produce limited private Actions artifacts, retained for one day |

Start a central **manual** CI request with a full 40-character commit SHA that belongs to `flyExplorer/main`. For example, after verifying the current main SHA:

```powershell
gh workflow run central-flyexplorer-ci.yml --repo tngkrwlsmd/personal-control-plane --ref main -f project_id=desktop-a -f commit_sha=<40-character-main-SHA> -f scope=release
```

Select `scope=source`, `release`, `gui` or `gui-probe` deliberately. This sends a request to central CI and does **not** assert completion. Observe the central Actions run and the originating commit status; use `gui` for the required final GUI functional gate. The GUI worker needs an unlocked logged-in Windows desktop. Screenshots/pixel acceptance remain a separate gate when UI visuals change.

For one-off Windows machine operations and focused debugging, use `personal-control-plane/requests/remote-shell/request.json` (or the explicit central Remote Shell manual dispatch) with its existing lease, revision and idle-slot restoration rules. Do not re-create a `flyExplorer` Runner, copy a privileged token into this repository, or dispatch source-PR code directly to the SYSTEM service.

## Recheck before retiring anything else

Use current `main` and central Actions status as the live baseline. Keep the separate evidence branch. Retain the old VM directory until recovery requirements, privacy review and any independently valuable local artifacts have been resolved.
