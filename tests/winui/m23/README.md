# Clipboard/session native fixture

The m23 directory name is retained for compatibility. This fixture validates
the current UI-independent clipboard encoding and private session contracts used
by the WinUI product.

Private session schema v2 now persists Window Tab, pane/tab, view/sort/column
and bounded filesystem history state while remaining able to read legacy v1.
All automated fixtures use disposable owned paths and private profile state.

Real global clipboard and other OS-global actions remain separate explicit
gates. Owned same-app physical pointer drag is now part of the Release GUI
acceptance and uses only disposable test-owned paths. Current GUI acceptance is
orchestrated by tools/winui/run_checks.py.
