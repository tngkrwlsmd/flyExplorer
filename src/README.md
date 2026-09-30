# Native source boundary

`src/base` contains UI-independent native code used by the canonical WinUI
application.

The canonical `src` tree intentionally contains only the shared `base` core used
by `app/winui`. The former MFC application source is not present in the current
tree and is recoverable only from Git revision `cbffb48`.

New product features must remain independent of the retired MFC application.
If a historical native primitive is still needed by WinUI, recover only the
required behavior from Git history and implement/extract it into `src/base`
with a focused contract.
