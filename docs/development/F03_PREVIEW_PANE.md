# F03 — bounded local Preview pane development boundary

## Status (2026-10-14)

**Phase 1 source groundwork only.** `src/base/file_preview_policy.h` holds
a pure candidate screen, with portable C++17 assertions in
`tests/winui/native_preview_policy.cpp` and a source contract registered
in the shell family of `tools/winui/run_checks.py`. This is **not** a
functional preview feature, file-reading implementation, Windows compile
acceptance, GUI acceptance or pixel review.

## Intended behavior

An explicit opt-in read-only Preview pane for the currently selected
single item of the **active pane and WindowTab**. Keep flyExplorer's two
independent file panes. Preview and the existing Details pane must have
a coherent responsive layout: neither may silently squeeze both file lists
into overlapping columns. Prefer a mutually exclusive right-side mode at
small widths; preserve each mode's own toggle and state, with explicit
switching semantics.

Supported first phase: bounded *local regular files* `.txt`, `.md`,
`.log` (displayed as inert text) and `.png`, `.jpg`, `.jpeg`,
`.bmp` (decoded raster, without shell extension/preview handlers).
Unsupported, empty selection, multiple selection, virtual Shell entry,
UNC, disconnected drive, reparse-point path and unstable/unknown size
display a localized safe placeholder rather than launching handlers.
SVG, HTML, executable formats, PDFs, archives, web content and active
preview handlers remain OUT OF SCOPE.

## Two independent security boundaries

1. **Cheap UI-independent candidate decision (implemented):**
   `previewpolicy::screen` requires filesystem, known fixed-local drive,
   regular file, no advertised reparse point, known size and canonical
   absolute drive path without `.`/`..`, slash mixing, ADS or device
   prefixes. Text is limited to **256 KiB**, image encoded data to
   **12 MiB**, with a separate **16,777,216-pixel** decode cap.
   The screen only decides whether a request MAY be submitted; its
   caller-supplied flags and path are not proof that a file is safe.
2. **Authoritative worker/handle validation (NOT IMPLEMENTED):**
   run file access outside the XAML thread in a bounded, cancellable
   worker or existing isolated helper. Require handle-based local fixed
   volume validation; reject reparse/junction traversal of *all*
   components, not just the leaf; reject directories/device/provider
   files; verify file identity, attributes and size on the opened
   handle, and cap the actual read. Prevent TOCTOU substitution; enforce
   bounded time, no output on partial/error/timeout. Validate decoded
   image dimensions and allocation before returning a pixel buffer.
   User-controlled text remains inert (no HTML/link/script execution),
   UTF decoding is bounded and malformed/binary inputs fail closed.

## Lifetime and ownership

A dedicated PreviewController/worker owns request creation, timeout,
cancellation, buffer limits and completion. It must not add a new
state machine to MainWindow. WindowTab/PanTab+side selection and current
navigation route, rendered path/identity and request generation must
match on completion; close, selection churn, pane switching, disabling
preview and window shutdown invalidate prior work. No provider/Shell,
disk open, raster decode or active preview-handler DLL executes on the
WinUI/XAML thread. File contents must not be persisted or logged.

## Incremental acceptance plan

1. **Phase 1:** conservative native candidate screen + tested bounds
   (current stage; local portable C++17 probe and source contracts).
2. **Phase 2:** separately test-owned worker/decoder with forged extension,
   huge encoded/decoded size, UNC, symlinks/junctions, short reads, binary
   text, malformed UTF, cancellation and stale selection regression.
3. **Phase 3:** WinUI presentation, opt-in toggle, placeholders, dual-pane
   layout, UIA text and keyboard focus. Capture actual test-owned
   **BEFORE** and matched **AFTER** pixels at light/dark, narrow/default
   widths and supported actual DPI. Inspect screenshots, fix visual
   defects and repeat the affected checks.
4. **Final scope:** source, native build, functional owned GUI process
   exit, original pixel inspection, current exact-main central acceptance.
   High Contrast, 125/150/200% OS scaling and Narrator speech remain
   explicitly **untested** until independently measured.

Do not mark F03 complete merely because a format's extension passes
`screen`; preview bytes, lifetime, UI and visual review are later gates.
