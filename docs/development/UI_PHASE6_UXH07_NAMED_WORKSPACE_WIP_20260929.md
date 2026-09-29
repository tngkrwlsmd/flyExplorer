# UXH-07 named workspaces: unmerged scoped work (2026-09-29)

Branch: fix/uxh07-named-workspaces-20260928.
Baseline main: 463f6ffd5bef6c78e3fdcf97dc51d6cb68038122.
STATUS: LOCAL SCOPED ACCEPTED after final 2026-09-29 verification.
NOT MERGED OR PUBLISHED; uncommitted local code/document changes.
Earlier WIP/open-gate sections are preserved as historical failures;
the latest final-acceptance section at the end supersedes them.

Current product branch adds optional View > Workspaces
Save As and Open in New Window native commands. The
existing main-session serializer creates named UTF-16
.fxworkspace files with schema version 1. Open checks
the schema, file size <=1 MiB, pane count and first tab
presence; it creates a separate temp conf_dir session
with global hotkeys disabled and launches a new window.

REAL OWNED GUI EVIDENCE: logs/uxh07-two-named-real-gui.log.
On an isolated 1x2 two-folder fixture, actual native
Save and Open dialogs wrote and opened the first file
in a distinct owned child with both folders restored.
Physical Ctrl+T then added a tab, and a second separately
named snapshot with different serialized bytes reopened
in its own distinct owned child with 2/1 tab counts.
The original window remained unchanged; the private
child and parent exited normally. The six original
user settings retained identical SHA256 hashes.
Activation of both native dialogs was from a test-owned
WM_COMMAND, NOT physical navigation through the menu.

OPEN ACCEPTANCE GATES (do not merge until resolved):
1. A successful opened child currently leaves copies
   of user settings and tab paths in its temporary
   isolated folder after normal exit. Implement safe
   owned-marker cleanup without touching other files.
2. Native menu physical mouse/keyboard selection, new
   labels localized and compatible with old language
   packs are not yet verified.
3. Negative real GUI file-open tests for malformed
   schema, missing tabs and oversize inputs are pending.
4. Only main snapshot and a copied config are staged;
   toolbar and bookmark inheritance requires an
   explicit product decision and scoped tests.
5. Real other DPI, High Contrast and spoken-reader
   environment checks remain NOT TESTED.

Existing incremental Release-x64-Unicode build log:
logs/uxh07-new-named-workspace-release-build.log.
New source contract and accepted owned tests are
branch-only and do not alter the accepted main product.
Other isolated UXH-06 and WinUI 3 branches are untouched.
No manual GitHub Actions were executed.


## Latest 2026-09-29 continuation results

**Still WIP, do not merge.** Native lifecycle now uses an exact
owner-marked TEMP/fxw????.tmp directory with a marker locked by
the live child, bounded 24-hour orphan reclamation on a later
startup, reparse-point rejection, an explicit allowable filename
list and nonrecursive cleanup. Existing toolbar/coolbar,
bookmarks, dialogs and saved-scope settings are copied privately
when present. The normal-exit cleanup and actual file copies
were verified on two separate owned child processes using two
different named workspace files and actual native save/open
dialogs. Source adds warnings for bad file size/type, pane count,
first/subsequent missing folders and unreasonable tab selection.

Real logs uxh07-post-cleanup-native-multiple.log confirm both
owned children cleaned their distinct temporary configuration
folders after normal exit. Logs uxh07-physical-old-language-menu-v3.log
and uxh07-physical-pointer-old-pack.log confirm real native
keyboard mnemonic and physical pointer submenu actions after
checking exact live menu command IDs. For pointer tests, the
parent View menu was opened using physical Alt+V, not by an
end-to-end mouse-only traversal. After staging the updated
Korean.xml through the canonical language copy, log
uxh07-physical-korean-keyboard.log confirms both real keyboard
actions again. Each accepted owned test preserved the original
six configuration SHA256 values and exited normally.

The LATEST C++ change extends path and selected-index checks
to every serialized tab, with a bound of 64 tabs per pane.
Its current compiled Release x64 executable SHA256 is:
6022C8375990E6F13E2692E31BF12312798869AEBCAC4158510A4E7435A97DCA
The prior two-snapshot positive GUI results were observed
before that last extra validation edit and do not count as
a full final-binary positive retest.

A real native empty workspace triggered the expected
Invalid workspace file size or type warning on the latest
compiled source. Six-case invalid-file automation did NOT
complete: the test-side posted WM_COMMAND/IDOK did not
dismiss this native warning, and a second test retry
confirmed that the same warning remained visible.
This is a test harness dismissal blocker, not proof that
other input validation failed. The remaining malformed
schema, empty/missing tab, bad split, absent real folder,
oversize, wrong extension and negative child-spawn checks
remain unaccepted. A focus-confirmed real Enter or actual
test-owned dialog button click should replace the attempted
posted command before repeating the batch.

Before main: rerun full two-snapshot save/open with the
latest executable; finish every real negative case and
ensure original foreground tabs and six hashes unchanged;
test owned synthetic aged crash-orphan cleanup and a
live locked/reparse negative guard; complete a fully
mouse-only top-level View menu traversal if required.
Standalone full screen-reader spoken output, actual
125/150/200 DPI and Windows High Contrast are NOT TESTED.
UXH-06 remains a separate untouched WIP branch and
WinUI 3 is in its original independent worktree.
Do not assert any unperformed acceptance result.


## Final 2026-09-29 continued review: real negative and isolated safety

STATUS: LOCAL WIP ONLY; no main merge or remote push.
This section supersedes earlier pending-test descriptions but
preserves their original failures. Tested current compiled
Release-x64-Unicode executable SHA256: 5D4F23F4ADC29F124450E8ED551CE4CA995166382BBA2E3802CF863FCE304D4A.

TEST FIXTURE FIX: Earlier synthetic bad-row replacement did
not change the serialized value. The revised test checks every
mutation against the actual saved schema before GUI input.
The accidentally spawned owned child was identified by its
parent and exclusively locked private workspace marker and
closed without touching unrelated user processes.

REAL NATIVE FILE ERRORS: logs/uxh07-final-reason-revision-negative.log
records six invalid inputs rejected with real native warnings:
empty, wrong schema, zero-row pane, missing first tab,
nonexistent folder and oversized file. The real test-owned
affirmative UIA control was distinguished from the
titlebar Close button, and invoked by physical mouse
or owned-foreground physical Enter when necessary.
The previous posted WM_COMMAND/IDOK failure remains
historical evidence, not a product PASS. All six
original user configuration SHA256 values remained
unchanged, current pane stayed intact, and the owned
process exited normally.

LATEST POSITIVE GUI: logs/uxh07-reasoned-second-workspace-real-gui.log
verifies two distinct named saved files opened into
separate owned native child processes with 1x2 and
2/1 per-pane tabs; the original window was unchanged.
Both child private configurations used marker protection,
copied toolbars, and were deleted after normal exit.
The original six user settings remained unchanged.
Earlier Korean/legacy real keyboard menu access and
physical submenu mouse selection remain valid for
unchanged menu paths; a mouse-only path all the
way from the top-level View menu remains unverified.

ISOLATED REAL-APP ORPHAN SAFETY: The owned runtime test
build/test_ui_uxh07_orphan_isolated_runtime.py overrides
TEMP/TMP/APPDATA in its exclusively private environment.
logs/uxh07-isolated-orphan-final-retested.log proves
the real app deleted a synthetic marked 72-hour orphan,
preserved an exclusively locked live-session marker,
ignored a test-owned junction and preserved its external
test-owned sentinel. The GUI-owned app exited normally,
all synthetic test fixtures were removed and six
original settings hashes stayed identical. Earlier
test-only failures were a mistyped path index and
selecting a non-main test-owned HWND; these were
corrected, not recorded as product failures.

STILL BLOCKING: An intermittent real second-workspace
launch failed with Could not protect isolated workspace
session, as documented in
logs/uxh07-latest-second-prespawn-diagnostic.log.
The reason is not established. A subsequent scoped
Release revision reports a numeric marker-failure
code if the failure recurs, and its complete
two-workspace real GUI run passed; that success is
not a root-cause fix or repeatability proof.
Wrong-extension selection through the native dialog
and any required fully mouse-only top-level menu
traversal are not yet accepted. Real other DPI,
High Contrast and screen-reader speech remain
separate untested UXH-05 environmental work.

Current-source tests: Release build PASS, scoped
source contract PASS, source invariants PASS,
Korean translation XML PASS, both test harnesses
compile, native functional 17 PASS / 0 FAIL,
six-case real negative GUI PASS, two named
positive GUI PASS, controlled orphan safety PASS.
Keep this branch local and unmerged until the
outstanding reliability and acceptance gates
are resolved. UXH-06 and the WinUI 3 experimental
worktree remain untouched; no manual GitHub
Actions were triggered.

## 2026-09-29 further local verification (supersedes final-ready claims)

Branch HEAD remains 7cc0b46; the following targeted product,
test-harness and diagnostic changes are UNCOMMITTED and UNMERGED.
Final locally compiled Release-x64-Unicode executable SHA256:
A06A04236D06EC36E4107B280D0E57A4E8F1CF614DD02409DAFA411F9B6B43E2.
Do not promote the prior 5D4F23F4 binary's tests to this revision.

An actual repeat of the prior binary reproduced the intermittent
SECOND workspace refusal with native error 1 (ownedDir safety check);
another run and subsequent successful runs did not. The
workspace_session ownership guard now reports narrower reason codes
11..17, but three actual diagnostic-binary repetitions did not
reproduce the failure. NO ROOT CAUSE OR RELIABILITY FIX IS CLAIMED.

A real malformed odd-byte UTF-16 fixture previously produced no
expected warning and the test-owned parent exited nonzero. The
loader now checks UTF-16 byte count and BOM BEFORE the legacy parser.
On the FINAL executable, eight actual native GUI rejection cases
passed: empty, wrong schema, invalid rows, missing first tab,
nonexistent folder, oversize, truncated UTF-16 and wrong extension.
No invalid child spawned; all six original settings hashes matched.
Evidence: logs/uxh07-A06-final-eight-negative.log.

Final-binary first-parent real GUI Save/Open again accepted TWO
separately named files and their 1x2 and 2/1 pane-tab layouts,
including exact owned child marker and copied customization.
The original parent exited normally. In a NEW owned process using
the SAME copied profile, native Last Tabs correctly restored 2/1.
However, reopening the first named file after that restart
FAILED acceptance: real native file dialog foreground and physical
Open-button activation were confirmed, the dialog closed, but
no persistent owned child or product warning was observed.
The files remained on disk, the new parent exited 0 and original
six hashes matched. Separate native Enter and pointer attempts
showed the same outcome. Added user-visible errors to the prior
silent TEMP/name/directory failure branches; they did not appear
in the final controlled restart. Do NOT assert whether the file
dialog canceled, an owned child briefly exited, or a different
path failed without further distinguishing evidence.
Evidence: logs/uxh07-silent-temp-restart-distinction.log.

Final-binary controlled isolated TEMP GUI safety PASSED:
72-hour marked orphan removed; exclusively locked live marker,
test-owned junction and its outside sentinel preserved; test-owned
fixtures removed and six original SHA256 values unchanged.
Evidence: logs/uxh07-A06-final-orphan.log.
Source invariants PASS, scoped contract 3/3 PASS and native
functional 17/0 PASS for the final build. Targeted Release
compile/link exit 0 with SEVEN MSB8029 warnings. The default
local_ci.bat x64 was attempted but its warning policy FAILED
on the earlier in-session revision; it was NOT a clean CI PASS
for this final checkout. The existing bin/x64/build-revision.txt
still records e84d893, not this uncommitted source revision.
No revision-matched canonical CI/marker acceptance is claimed.

REMAINING BLOCKERS: reproduce and identify intermittent owner-dir
refusal; distinguish canceled file-dialog selection versus brief
child exit after parent restart; secure repeatable successful
reopen of both names after restart; resolve or separately scope
the existing MSB8029 strict-CI warning/marker mismatch.
Actual other-DPI, High Contrast and screen-reader listening remain
independent environment gates. Preserve main-window.png untracked;
do not merge, push or run GitHub Actions without separate approval.

## Final scoped local acceptance (2026-09-29)

This LATEST section supersedes all prior WIP/pending/failure
assessments above without deleting the original negative
diagnostics. Branch `fix/uxh07-named-workspaces-20260928`
is LOCAL, unmerged and uncommitted at HEAD `7cc0b46`.
Final exact Release x64 executable SHA256:
`0873F600E45DC26BEF98948BF2B6DADBC013C1DC11633B614EED5B75BA2F091C`.

CONFIRMED PRODUCT ROOT CAUSE: earlier native Save/Open
intermittently displayed `Could not protect isolated workspace
session` (generic reason 1; focused reason 14). The
`workspace_session::ownedDir` guard required a four-hex
`fxw????.tmp` leaf, but 240 test-owned REAL Windows
`GetTempFileNameW` calls generated 3-digit names such as
`fxw18F.tmp`. The native API does not always zero-pad to
four digits. The owner guard now accepts ONLY `fxw` plus
1-4 hexadecimal digits plus `.tmp` under the exact TEMP
root. Orphan enumeration now uses `fxw*.tmp` but actual
deletion still requires the exact valid owner marker,
exclusive lock, stale age, direct allowlist, and reparse
and nonrecursive checks. The isolated real-product orphan
GUI test now uses a 3-hex 72-hour stale folder, a 4-hex
exclusively locked live folder, and a test-owned reparse
junction and external sentinel.

CONFIRMED TEST-HARNESS FALSE FAILURE: earlier tests saw
the native dialog close and reported no new owned child
after a normal parent restart. Temporary opt-in LOCAL
native tracing proved `DoModal==IDOK`, actual child
`CreateProcess` success, and child still alive at 1.3 s.
The restart-only watcher incorrectly used `"fxw" in argv`
where `argv` is a list of full command-line tokens.
The corrected watcher validates the concrete
`--conf_dir` path with the strict owned 1-4 hex regex.
It then accepted both separately named files after
normal original parent exit, new parent startup and
Last Tabs 2/1 restoration. All temporary product trace
hooks and diagnostic waiting were REMOVED before the
final clean build; only test-owned failure diagnostics
remain in the test harness.

Malformed UTF-16 robustness: an earlier odd-byte
truncation did not produce an expected rejection.
Before passing the file to the legacy config parser,
the product now validates even byte length and UTF-16
BOM. On the FINAL executable, real native GUI tests
rejected eight owned invalid inputs: empty, wrong
schema, invalid row count, missing first tab, missing
folder, oversize, odd-byte truncated UTF-16 and
wrong extension. No invalid child spawned; original
parent tabs and all six original user config hashes
remained unchanged. Log:
`logs/uxh07-clean-ci-final-eight-invalid.log`.

FINAL ACCEPTED VERIFICATION ON THIS BINARY:
- `local_ci.bat x64` exit 0, warning policy PASS, source
  preflight PASS, Release-x64-Unicode Rebuild PASS,
  native product functional 17 passed / 0 failed,
  overall PASS_WITH_SKIPS due to existing HKCU state
  protecting the official runtime smoke. The remote
  shell lacked `ProgramFiles(x86)` and `TMP`; setting
  only these process-local variables corrected the
  earlier path failure and spurious MSB8029 warnings.
  Log: `logs/uxh07-canonical-local-ci-clean-env.log`.
- Scoped UXH-07 contract 3/3 PASS, eight malformed
  real native file-dialog cases PASS.
- Real physical keyboard Save/Open menu path for BOTH
  named files, 1x2/2/1 per-pane tab restoration,
  normal parent restart and reopen of BOTH saved names,
  original Last Tabs not replaced, private children
  normally exited and owned configs removed: PASS.
  Log: `logs/uxh07-clean-ci-final-restart-real-gui.log`.
- A SECOND independent real GUI repetition on the SAME
  final binary also passed: physical-pointer Workspaces
  submenu Save/Open for both named files, normal parent
  restart and reopening BOTH snapshots, unchanged six
  original setting hashes and normal owned exits.
  The top-level View menu was opened using physical
  Alt+V, not a full mouse-only top-level traversal.
  Log: `logs/uxh07-clean-ci-final-repeat-pointer-restart.log`.
- Test-owned isolated 3-hex stale recovery, 4-hex live
  marker preservation, ignored junction and preserved
  external sentinel, owned process exit 0, all synthetic
  fixtures removed: PASS.
  Log: `logs/uxh07-clean-ci-final-orphan-variable-hex.log`.
- All accepted GUI tests preserved the original six
  user configuration SHA256 hashes.

REMAINING EXPLICIT LIMITS, NOT THIS SCOPED CORE FAILURE:
fully mouse-only top-level View menu traversal,
real 125/150/200 DPI, OS High Contrast, spoken
screen-reader verification, official HKCU-sensitive
runtime smoke, hosted CI, clean-machine package and
installer were NOT TESTED. The local binary's
`build-revision.txt` equals HEAD `7cc0b46`
but does not identify the still-uncommitted changes.
`main-window.png` is pre-existing untracked user
material and was not modified. No GitHub push,
merge, release or GitHub Actions run occurred.
