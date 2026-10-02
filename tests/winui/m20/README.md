# Native explorer state fixture

The m20 directory name is retained for compatibility. Its current purpose is to
compile and validate the same UI-independent explorer_ui_state model used by the
WinUI application.

The fixture covers independent pane/tab state, stable routes, stale-result
rejection, active-pane/split behavior and bounded workspace reset semantics.
It manipulates disposable native values only and does not certify the GUI.

Run it through the canonical source/full orchestration rather than relying on
old milestone commands or deleted migration reports.
