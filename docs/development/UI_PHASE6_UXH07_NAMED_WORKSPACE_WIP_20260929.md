# UXH-07 named workspaces: unmerged scoped work (2026-09-29)

Branch: fix/uxh07-named-workspaces-20260928.
Baseline main: 463f6ffd5bef6c78e3fdcf97dc51d6cb68038122.
STATUS: WIP. NOT MERGED, NOT PUBLISHED AS A FINISHED FEATURE.
The earlier open-gate list is historical; see the latest continuation
section at the end for newly resolved items and still-blocking tests.

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
