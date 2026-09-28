# UXH-07 named workspaces: unmerged scoped work (2026-09-29)

Branch: fix/uxh07-named-workspaces-20260928.
Baseline main: 463f6ffd5bef6c78e3fdcf97dc51d6cb68038122.
STATUS: WIP. NOT MERGED, NOT PUBLISHED AS A FINISHED FEATURE.

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
