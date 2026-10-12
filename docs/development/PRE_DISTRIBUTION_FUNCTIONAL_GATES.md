# flyExplorer pre-distribution functional gates — updated 2026-10-12

This document records tests and remaining product functionality **before**
installer, signing, public release or redistribution. An accepted result
applies only to the tested SHA/binary, environment, procedure and scope.
See `CURRENT_STATUS.md`, `ARCHITECTURE.md`, `VERIFICATION_PROFILE.md`
and `AGENTS.md`. Later evidence below supersedes older failure checkpoints.

## Latest engineering evidence — current accessibility and private package audit

**Engineering-only product source:** `2a736d85b22859a770138e4b50926ac125d1a052`,
including filter color/icon classification and improved UI Automation
row/badge descriptions. [Central Windows GUI #38209842808](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38209842808)
**SUCCESS** on exact source `8902d494255b471911f092c3cdd4e978af2c4e56`
(the same compiled product; next commit added only the private audit
script). Release, window tabs, physical shortcuts, filter-preset keyboard
selection/save, accessible row and badge labels, and the entire GUI
regression all exited 0. The first CI attempt #38209461852 built Release
but encountered a transient WindowTab UIA row rebind; the wait-before-
physical-input harness was corrected before the accepted retest.

**DPI and Narrator boundary:** [read-only Windows desktop inventory
#38209100479](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38209100479)
reported 1024x768 and system DPI **96** in Explorer user session 2.
Actual 125/150/200% OS scaling therefore remains **NOT TESTED** on this
machine. The filter colors and badge categories now appear in UI
Automation names, but actual spoken Narrator behavior remains
**NOT TESTED**. Earlier matched light/dark 96-DPI pixels are accepted
in CURRENT_STATUS.md; those results are not substitute higher-scale tests.

**Fresh exact source/binary setup identity: PRIVATE PASS.**
[Windows owned audit #38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849)
used exact source `2a736d85b22859a770138e4b50926ac125d1a052`,
ran one clean Release/provenance/setup build, checked the current
438-file deterministic source ZIP, and verified an unsigned setup,
305-file runtime manifest and release identity all reference the same
source SHA. Private setup SHA-256:
`3861b937b122e7d997fe92d778798631f02b952228b9d0707de72b150aa9da37`;
source ZIP SHA-256:
`b08f01ad41b5c211282848c438c138e0587986a614ac8ebf4c8e839231dba01d`;
runtime manifest SHA-256:
`fb509b3f6a40ad962c18e10fcd323dab2e195df64884be7430d12304f59f25c7`.
The audit was **private engineering only**: no real installation,
registry mutation, signing, tag or public release. The test-owned package
and source ZIP were deleted on successful cleanup; hashes and stage
markers remain in the run log, not a durable downloadable release
asset. The existing tracked `packaging/RELEASE_IDENTITY.json` and
`packaging/SOURCE_BUNDLE_MANIFEST.json` still describe the earlier
`bc63c8b...` accepted artifact and **must not** be represented as
identities of the current product.

**Open distribution gates:** updated permanent provenance/source manifest
and retained matching artifacts for a finalized build, current setup's
owned `/TESTROOT` install/update/rollback/uninstall reacceptance,
current clean-machine production Program Files/HKLM lifecycle,
Authenticode signing/trust verification, public same-release-page
Corresponding Source availability, rightsholder clearance and final
publication authorization. The reserved release tag must not be created
or moved prematurely. User-deferred file-copy interruption receipts
and safe recovery remain out of scope.

## 1. Latest accepted Release, GUI and shortcuts

**Historical 2026-10-10 checkpoint:** `65dcb8d8eea4906b245eafcc7c571418aea93c63` (superseded by the current engineering section).

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

At this historical checkpoint, actual `run.bat` launch was not yet
accepted. Later [Windows run 38198360371](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38198360371)
**PASS** confirmed real `run.bat Release`, dual panes, a Unicode
file row and normal owned-process shutdown.

## 2. Shell context-menu compatibility — bounded PASS

Focused Windows run
[38054888667](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38054888667)
passed test-owned fixed-local-filesystem right-click, Shift+F10
isolated Shell popup, Escape cancellation, unchanged test file and
all six byte-identical legacy profile inputs. Source/binary was
`ac4916a7f506f2bf0bc97ff7d01f4b3d6aedc41a`. Git compared it
to current `65dcb8d`: only two GUI/source tests differ, so this is
the *same compiled product*, not a different release feature level.
**New same-parent bounded multi-selection acceptance (2026-10-11):**
product `2cb7396bc153a21f49ec7fa35850c72000009420`,
source/contract run
[38095921258](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38095921258)
PASS (163 product contracts), Release build
[38095991723](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38095991723)
PASS, owned right-click/single Shift+F10/**two-item Shift+F10**
popup and Escape cancellation
[38096316352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38096316352)
PASS with two test-file byte identities and six legacy profile
identities unchanged. Same SHA's prebuilt-Release **entire GUI**
run [38096428754](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38096428754)
PASS (WindowTab 14.9 s, shortcut 9.9 s, all 137.4 s).

The menu's isolated helper now accepts **up to 32 selected local
fixed-drive non-reparse items from the same parent**, with independent
path/duplicate/length validation on both sides of the pipe and
revalidated Shell PIDLs. For multiple selections, only the canonical
nonmutating `properties` verb is allowed for invocation; other
Shell verbs remain fail-closed. This is **menu display and cancellation
acceptance**, not proof that the Properties dialog was invoked,
used or closed. Windows clipboard Copy/Cut/Paste continue to use
the app's native guarded routes and were not re-accepted by
an external Explorer-interop test at this SHA. Such an interop
test explicitly clears the shared Windows clipboard and therefore
requires separate approval before execution.

**Actual clipboard interop now ACCEPTED for owned Win11 fixtures:**
compiled product SHA `96d6b5723773104baf4fa351ab37dd219481ccfa`,
test-only `e8c6b31fcc3c912b0e258e2c66e40e6b5b70526d`,
[Windows run 38099481287](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38099481287)
SUCCESS. Four real OS clipboard/file flows PASS: flyExplorer Copy
to Explorer paste, Explorer Copy to flyExplorer paste, flyExplorer
Cut to Explorer move, and Explorer Cut to flyExplorer move.
Exact test-owned Unicode file bytes and move/source disappearance
were checked; the registered `Preferred DropEffect` HGLOBAL was
read directly (copy 1/5, cut 2/2). The original six legacy
settings were byte-identical. **User-approved global clipboard was
cleared before and after the test and its previous contents were
not recoverable.** Two earlier tests on the same product were
harness failures from the binary-format/HGLOBAL reader, not accepted
file-operation failure evidence.

**Actual multi-item Properties now ACCEPTED:** product SHA
`96d6b5723773104baf4fa351ab37dd219481ccfa` (STA-fixed
Release build [38098503351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38098503351)),
test + documentation SHA
`636d09cda6b06d429e1c36587277766265e353e0`,
[Windows run 38099891312](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38099891312)
SUCCESS. Two owned sibling files, exact helper-owned native popup,
uniquely identified canonical terminal Properties item, and
helper-owned hit-test point were verified before native pointer
selection. The actual native Properties dialog appeared at
**435x587** pixels, was confirmed owned by the exact helper PID,
was closed by HWND-specific WM_CLOSE, and the helper settled.
Original file bytes and all six legacy profile identities remained
unchanged. The test saved a dialog screenshot; no separate
DPI/High Contrast/final-pixel acceptance was performed.
The independent Explorer OS Properties baseline
[38098254103](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38098254103)
also passed. Prior keyboard-path run
[38099074283](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38099074283)
failed without ever displaying a dialog, despite a zero helper
exit code: the accepted guarded native pointer method resolves that
**test input delivery** boundary without weakening the isolated
Shell verb allow-list.

**Still OPEN:** extension-specific verbs, removable/UNC targets,
provider Move/Delete/Recycle, provider-to-provider copy,
arbitrary third-party extensions and broader UI/accessibility/
provider environment acceptance.

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

**Latest accepted exact-boundary Windows verification (2026-10-10):**
source `3587d36d183493ca634fa01681681951bc48455f`,
preserved Release build run `38058015868` PASS. Owned GUI run
`38058327731` PASS: 1,305-entry smoke; **25,000-entry**
indexed type, size, modified-date sort PASS; **25,001-entry**
fail-closed refusal and no partial sort PASS, with original
profile bytes unchanged. Sample process RSS 148.7 MiB (25,000)
and 133.9 MiB (25,001 refusal); these are point samples, not
peak RSS or performance guarantees. Metadata requires one
Shell lookahead sentinel at the 25,000 bound.

**Metadata error/cancel acceptance:** product code remains identical
to `3587d36`; test-only SHA `84610ab4e73396a534899e4b1192e1a284a2978d`.
Windows run `38060310939` PASS after two prior **harness/environment**
failures, not product failures: source contract 9/9, test-owned
junction reparse metadata error -> whole indexed sort canceled
without partial projection, and immediate application close
after metadata sort request -> owned process exit 0,
original file bytes and protected profiles unchanged.
No new product build was needed after `3587d36`.

**Still OPEN:** scale beyond 25,000, measured peak/memory/performance
over long runs, removable/UNC/network/virtual-provider indexed
metadata, and broader cancellation/fault modes beyond the
accepted owned reparse and immediate-close cases.
The independent 100,000 sequential browse budget remains unverified
as a performance promise.
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
indexed property/content/provider search remain separate feature
tasks. Filter color/icon classification is implemented and accepted
for light/dark 96-DPI conditions. Windows
125/150/200% scaling, High Contrast, Narrator, Korean IME,
third-party providers and long-duration errors require distinct
acceptance evidence.

Production signing, installer/Program Files/HKLM lifecycle,
clean-machine install/update/rollback, rightsholder clearance,
matching-source public distribution and release publication are
**OUT OF SCOPE** for this stage and must not be initiated.
