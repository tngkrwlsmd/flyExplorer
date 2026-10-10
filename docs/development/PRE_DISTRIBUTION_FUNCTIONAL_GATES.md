# flyExplorer pre-distribution functional gates — 2026-10-10

This document records tests and remaining product functionality **before**
installer, signing, public release or redistribution. An accepted result
applies only to the tested SHA/binary, environment, procedure and scope.
See `CURRENT_STATUS.md`, `ARCHITECTURE.md`, `VERIFICATION_PROFILE.md`
and `AGENTS.md`. Later evidence below supersedes older failure checkpoints.

## 1. Latest accepted Release, GUI and shortcuts

**Current main:** `65dcb8d8eea4906b245eafcc7c571418aea93c63`.

- Registered Windows `desktop-a` `gui` run
  [38053505865](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38053505865)
  **SUCCESS**: policy/source, Release build, WindowTab restore, real
  physical-keyboard shortcuts, and complete functional GUI PASS
  (focused WindowTab 16.2 seconds, shortcuts 9.4 seconds, all 124.7 seconds).
- Source run
  [38053376198](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38053376198)
  **SUCCESS**: 4 structure, 163 product-source, 20 harness and
  30 infrastructure contracts. On the earlier `ac4916a` revision
  the theme fixture expected exact `schema=2` bytes but the product
  had correctly started writing `schema=3`. The test-only correction
  in `65dcb8d` fixed this deterministic harness mismatch.
- **Accepted bounded user-defined Ctrl focus bindings:** the two
  address/search actions can independently choose Ctrl+L/E/F/K,
  with duplicate choices rejected, an atomic private `schema=3`
  save, legacy schema-1/2 reading and default reset. Fixed
  F5/F6, pane/window-tab and filesystem operation commands
  are not remappable. More general Explorer verb accelerator
  customization remains **OPEN**.
- Actual app-window Dark visual review
  [38056561878](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38056561878):
  matched 1296x736 before/after opening Workspace settings,
  showing both shortcut selectors and Save/Reset with no visible
  clipping or overlap.

**Historical resolved defects:** `f3d06ff` WindowTab history readiness
failed in `38047230115`; the navigation chrome update was later
accepted on main by `38048875845`. `ac4916a` source/Release
built successfully but an obsolete preference-schema expectation
failed GUI run `38050952226`; later `65dcb8d` is accepted.
Neither older failure describes the latest main acceptance.

A positive launch through `run.bat` against the full matching runtime
has still **NOT** been separately proven. Earlier `38044362154`
validated `fly.bat` command guards and missing-build behavior.

## 2. Shell context-menu compatibility — bounded PASS

Focused Windows run
[38054888667](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38054888667)
passed test-owned fixed-local-filesystem right-click, Shift+F10
isolated Shell popup, Escape cancellation, unchanged test file and
all six byte-identical legacy profile inputs. Source/binary was
`ac4916a7f506f2bf0bc97ff7d01f4b3d6aedc41a`. Git compared it
to current `65dcb8d`: only two GUI/source tests differ, so this is
the *same compiled product*, not a different release feature level.
Arbitrary external verbs, multiple selection, removable/UNC targets,
provider moves/deletes/recycle, provider-to-provider copy and
third-party Shell extensions remain unverified or intentionally blocked.

## 3. Large-folder metadata indexing — bounded PASS

Focused Windows run
[38055029443](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38055029443)
used the identical preserved `ac4916a` Release binary and passed
a **1,305-entry** size/date/type smoke followed by an owned
**20,500-entry** fixture with indexed name sort/filter and global
**size, modified date and type sorting**. The winning indexed type
row was `bench-17000.aaa`; test process exited 0 and the six
original legacy settings stayed unchanged.

Read-only actual-app screenshots reviewed in
[38056349169](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38056349169)
were both 960x519 Dark: the two-pane layout and headers remained
visible, no obvious new clipping was found and the after image
displayed `bench-17000.aaa` first and 20,500 total entries.

The current implementation adds a local **fixed-drive-only**
metadata index bounded by `kMaxIndexedMetadataEntries=25000`
and `kMaxIndexedMetadataPathUnits=12*1024*1024`, while preserving
the full resident metadata bound of 20,000 and the separate
100,000 sequential browse bound. Missing/stale metadata fails
closed rather than presenting a partially sorted result.

**Still OPEN:** acceptance at the *25,000-item limit* and larger
scenarios, sustained performance/cancel/fault coverage, and
global metadata indexing for removable/UNC/mapped-network/
arbitrary virtual-provider locations. The 25,000 upper bound
is a code ceiling, **not** a proven 25,000-file workload.
100,000 is only a sequential browsing safety bound.

## 4. Real USB and remote SMB — blocked by environment

The central Windows VM had **zero removable volumes**, **zero
mapped network volumes** and **zero non-special SMB shares** in
read-only inventory. No USB or actual remote SMB acceptance is
claimed. With separate authorization and test-owned disposable
media/share, require copy/move/metadata sort, collisions,
cancellation, offline and recycle-only failure behavior,
file-byte verification and cleanup. Loopback administrative UNC
is not a substitute for an independent SMB endpoint.
Never modify user data or protected legacy configuration.

## 5. Remaining Explorer features and distribution boundary

Broader arbitrary accelerator editing, safe/provider context verbs,
indexed property/content/provider search and visual filter rule
color/icon classification remain separate feature tasks. Windows
125/150/200% scaling, High Contrast, Narrator, Korean IME,
third-party providers and long-duration errors require distinct
acceptance evidence.

Production signing, installer/Program Files/HKLM lifecycle,
clean-machine install/update/rollback, rightsholder clearance,
matching-source public distribution and release publication are
**OUT OF SCOPE** for this stage and must not be initiated.
