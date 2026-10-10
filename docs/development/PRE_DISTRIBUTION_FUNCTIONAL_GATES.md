# flyExplorer pre-distribution functional gates — 2026-10-10

Scope: complete safe product functionality and real-world validation
**before** signing, installer deployment, rights review or public
redistribution. None of those latter operations is authorized here.
Always consult live main, AGENTS.md, CURRENT_STATUS.md and
VERIFICATION_PROFILE.md. Evidence applies only to exact source SHA,
configuration, environment, tested scope and producing run.

## 1. Current Windows source, launcher, Release and GUI

- `a310951872ee5ddb720966498510605f8aea4b6e`: central registered
  `desktop-a` source run `38044463555` **PASS** — policy plus
  structure 4, product 152, harness 20, infrastructure 30.
- On the same SHA, Remote Shell `38044362154` established Windows
  `fly.bat help`, invalid build/clean rejection and missing-build
  `run.bat Release` behavior. The later source stage was blocked
  only by SYSTEM's missing Python PATH; official user-session source
  succeeded. Disposable checkout was deleted.
- Central registered `gui` `38044629405` subsequently **PASSED**,
  including Release build and `gui-all-Release` on the baseline
  `a310951872ee5ddb720966498510605f8aea4b6e`.
- New Ctrl+L address-focus / Ctrl+F quick-search-focus candidate
  `f3d06ff9463f1b462ca3fb1c30675bd6dd742b12` is **NOT
  ACCEPTED**: central GUI run `38047230115` had `release-build=PASS`
  but `gui-all-Release=FAIL`, first error
  `cleanup close did not restore ready tab A` in the existing
  `test_v7_window_tabs_gui.py`. Session restoration in a separate
  child, the owned process exit 0 and protected profile identity
  checks passed. Read-only inspection of the preserved failed GUI
  snapshot confirmed the surviving `Nested` tab and test-owned
  `Left\\Nested` address. It did not capture Back button state or
  app status at the failing instant. Product vs harness/cancellation
  classification remains open; the candidate's new keyboard GUI test
  was not reached. The separate upload-artifact step failed because
  GitHub Actions artifact storage quota was exhausted, but the failure
  evidence remains on the Windows VM. Do not manufacture an acceptance
  claim or rerun unchanged tests without a diagnosed correction.
- A positive `run.bat` launch with a complete matching runtime, as
  opposed to its missing-build guard, is separately **NOT TESTED**.
  Functional UIA and matched visual pixel acceptance are distinct.

## 2. Physical removable and SMB operations — BLOCKED BY ENVIRONMENT

The central VM inventory reported **0** removable logical drives,
**0** mapped network drives and **0** non-special SMB shares.
Code support is not a substitute for hardware/transport evidence.

With separately authorized test-owned disposable media/share, check
physical USB copy/move/metadata sort, collision/cancel and recycle-only
failures (never permanent-delete fallback); check direct UNC and mapped
remote-drive browse, copy/move, sort, disconnected/error paths, cleanup
and bytes before/after. No real user documents, personal SMB shares,
global clipboard or real Recycle Bin contents may be changed.
Loopback administrative shares, if ever tested, are only supplemental
UNC evidence and are not remote SMB certification.

## 3. Explorer-level function backlog — OPEN

- Keyboard usability improvement (2026-10-10): Ctrl+L now focuses the
  existing address editor and Ctrl+F focuses the existing quick-search
  field without starting a file mutation or launching an unsolicited
  search. The focused Windows GUI regression uses
  `python -X utf8 tools/winui/run_checks.py gui --area shortcuts --configuration Release`.
  These shortcuts remain **pending actual GUI acceptance**. The first
  producing GUI run `38047230115` failed in preexisting WindowTab
  cleanup before exercising them; its successful Release build alone
  does not certify physical input.
- User-configurable shortcuts remain **OPEN**: add a bounded private,
  atomic settings schema, collision checks, preserved default F5
  refresh/F6 pane focus/Ctrl+Shift+N semantics and no silent OS-reserved
  key remaps. Require native/source tests, owned keyboard GUI, and matched
  visual review of actual focus/pixels before final acceptance.
- Context menus/provider commands: inventory the remaining safe verbs
  and test explicit supported virtual/file-system targets before
  widening capabilities. Provider Move/Delete/Recycle and arbitrary
  provider writes must remain fail-closed until separately proven.
- Indexed property/content search and optional filter rule
  color/icon classifications: independently specify bounded product
  behavior and cancellation; no silent filesystem traversal fallback.
  New colors/icons require pixel-level review.

These are candidate logical units, **not** implemented features.

## 4. Above-20,000 global sort/filter — PARTIAL

**Already accepted:** lightweight indexed name sort and name/mask
filter on an owned 20,500-file folder, run `37211942616`,
integrated revision `582560f89afe8c9c53bbc23791cdbd5d3335c014`,
with matched Dark visual inspection.

**Remaining:** full-folder type/size/modified-date ordering beyond
`kMaxCompleteModelEntries=20000`. Current refusal is intentional.
Implement a bounded metadata-index approach preserving the separate
100,000-entry browse ceiling, 1,024-entry/8 MiB Shell reply budget,
2,048-item resident window, stable logical identity, cancellation,
stale-result rejection and complete deterministic ordering. Start
with inexpensive native/source contracts; use one actual owned
20,500-item metadata-sort GUI/visual fixture only after the new
lower-layer contract converges. Do not claim arbitrary 100,000-item
performance or third-party provider support.

## Excluded release gates

Production signing, installer generation/publication, clean-machine
Program Files/HKLM lifecycle, rightsholder clearance, matching public
source release and release-tag publication remain OUT OF SCOPE. No
test here converts those gates into PASS.
