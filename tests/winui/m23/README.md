# Clipboard/session native fixture

The m23 directory name is retained for compatibility. This fixture validates
the current UI-independent clipboard encoding and private session contracts used
by the WinUI product.

Private session schema v4 persists Window Tab, per-folder-tab sort, pane display
options, view/column and bounded filesystem history state. The 41 native checks
include legacy v1 round-trip plus independently constructed v2/v3 wire fixtures,
checking inherited pane sort, selected tabs, history and display defaults/flags.
All automated fixtures use disposable owned paths and private profile state.

Real global clipboard and other OS-global actions remain separate explicit
gates. Owned same-app physical pointer drag is now part of the Release GUI
acceptance and uses only disposable test-owned paths. Current GUI acceptance is
orchestrated by tools/winui/run_checks.py.
