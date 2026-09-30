# Native source boundary

`src/base` contains UI-independent native code used by the canonical WinUI
application.

Former MFC application source now lives under `../legacy/mfc/src`. The canonical
`src` tree intentionally contains only the shared `base` core used by
`app/winui`.

New product features should not add dependencies from `app/winui` back into the
legacy MFC application directories. If a small native primitive is still needed
by WinUI, extract it into `src/base` with a focused contract instead.
