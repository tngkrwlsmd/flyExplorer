# M23 — same-app local Copy acceptance boundary (2026-10-28)

## Product completion decision

**Accepted for the explicitly tested local Windows 11 same-app Copy scope:** file and folder Copy between two flyExplorer panes; modal Skip, Cancel, Keep Both; single and mixed selection; duplicate names; late arrival of a competing file or folder; and the three final safety areas below. **This is not a certification of every Shell provider, Move operation, file type, filesystem or Windows accessibility setting.**

This document is a finite acceptance ledger, not an invitation to create a new regression case after every successful test. The source of truth for exact historical requests and results remains `CURRENT_STATUS.md` and the linked control-plane result JSONs.

| Core acceptance area | Actual verified evidence | Limit |
| --- | --- | --- |
| File/folder type mismatch | [Physical Windows GUI + 20/20 source](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-m23-type-folder-file-20261028.json); folder **source** colliding with existing destination **file**, Keep Both, all original and renamed copy bytes preserved | Opposite file-source versus folder-destination is not tested |
| Source path replaced while modal is open | [Physical Windows GUI + 21/21 source](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-m23-source-renamed-contract-fix-20261028.json); the test-owned original source file is renamed before approval, the stale-path transfer reports failure, and the pre-existing destination bytes remain intact with no new copy | Does not certify the source's externally changed contents or every source disappearance error |
| Pending dialog and context invalidation | [Physical Windows GUI + 23/23 source](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/results/windows-vm/fly-m23-dialog-close-20261028.json) proves normal owner-window close with a pending collision performs **no transfer**. An affected [source contract](../../tests/winui/test_outbound_drag_contract.py) checks the six `sameContext` fields (WindowTab identity, side, tab, route, visible filesystem folder, visible Shell folder), post-dialog token validation, and pending reset on close | **Changing an actual tab/path while the dialog remains open was not physically executed.** Its rejection is currently a *source-level* guarantee only, not an independently certified real-GUI scenario |

## Accepted earlier and not repeated

Existing exact-source/physical-GUI evidence already covers local same-app right→left file Copy, nested folder Copy, mixed file/folder selection, one and two same-name conflicts, collision Cancel/Skip All/Keep Both, and second-name file or folder collisions appearing while the dialog is displayed. See [latest status](CURRENT_STATUS.md). Never rerun these accepted cases without a changed dependency or relevant failure.

## Explicit non-blocking boundaries

- Actual same-name **file source onto an existing folder** (reverse cross-type case), actual tab/path switch during modal, Move, cross-volume, removable/SMB/UNC, provider-specific Shell operations, large batches, and screenshot/pixel/Narrator/high-DPI certification remain unaccepted. They are **different functional/environment scopes**, not automatically required follow-up tests for this bounded local-Copy acceptance.
- User-excluded G03/G04/G05 and stopped G07 remain excluded and must not be restarted implicitly.
- Tests used only disposable, uniquely owned fixture files and a known Release executable with SHA-256 `749B73500F806D7636E391F3176AAFBECF80A0B72ABD3F4B44CFEC3AC58AFFD5`. No product C++ change or new build was introduced for these regression checks.

## Next development selection

Continue **a different prioritized product feature or an actually reported regression**, not an endless M23 collision-test matrix. Reopen an unaccepted scope above only when explicitly selected as a new feature requirement or tied to a reproduced defect. Never convert source-only evidence into GUI success.
