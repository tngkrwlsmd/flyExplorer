# F03 — bounded local Preview pane development boundary

## Status (2026-10-14)

**Phase 1 policy and partial phase 2 safe open, bounded reader and
one-shot helper entry.** `file_preview_policy.h` screens candidates,
`file_preview_safe_open.h/.cpp` validates each local component and retains
opened ancestor handles, and `file_preview_reader.h/.cpp` reads bounded bytes.
`file_preview_worker_wire.h` defines a separate versioned/bounded request and
reply protocol. `file_preview_worker.cpp` runs one request in the existing
`FlyShellIsolationHelper --preview-read` mode. The helper is built in
Release, but **no production parent supervisor currently calls this mode**.
The one-shot worker has no GUI, persistence, Shell extension, web content or
image decoder. Blocking filesystem work stays out of the XAML thread.
This is a fault boundary, **not** a security sandbox.

**MSVC Release compile accepted:** [registered central Windows run
#38518993733](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518993733)
reported `PASS release-build` at exact source SHA
`93c8a435cb5de505d02ac1927ceb30e0f572bd09`, including actual
`file_preview_reader.cpp` translation-unit compilation.

**Verified focused native handle-read behavior:** [owned Windows
run #38520021060](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38520021060)
completed **SUCCESS** with exact source SHA
`62a4f632d302bce59839b3b4109a1380c55e5b5a` after an isolated
MSVC compile of `src/base/file_preview_reader.cpp` with
`tests/winui/native_preview_reader.cpp`. The test-owned, regular local files
exercised correct UTF-8 and opaque image bytes, mismatched opened path and
size, invalid UTF-8, cancellation, deadline, oversized text, invalid handle
and directory rejection. The producing log recorded
`F03_NATIVE_HANDLE_READ_AND_FAILURE_CONTRACT=PASS`,
`F03_NATIVE_VERIFIED_HANDLE_ACCEPTANCE=PASS`, and owned scratch cleanup
PASS. The *actual compiled behavior* of this handle-only primitive is now
**accepted within those bounded fixture cases**, not as an isolated helper
service or a shippable preview feature.

**Earlier harness failures correctly classified:** [#38518452445](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518452445)
(PowerShell 5.1 parser),
[#38518550162](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518550162)
(SYSTEM session did not expose `python`),
[#38518696504](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518696504)
and diagnostic [#38519687206](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38519687206)
(truncated `call "` batch serialization from unparenthesized PowerShell
array string expressions). The native test helper now parenthesizes each
concatenated array element, checks serialized commands before execution and
retains a bounded developer-command setup log on failure. These earlier
failed runs never executed the C++ assertions and must not be recorded as
product regressions.
## Phase 2 one-shot preview helper wire — bounded acceptance evidence

- **Exact code SHA:** `d0d5b6a987ef8ae1c73e2aa0f5ceacb20c37f0ec`.
  Private request/reply headers are 28/24 bytes, version 1, with UTF-16
  path length/checksum and capped body sizes (256 KiB text, 12 MiB image).
  The helper checks canonical path, extension and size before opening;
  all actual file access remains in the child. It responds with empty
  bodies on errors. No raw file contents are written to logs.
- **Actual MSVC native entry test:** [owned run #38526086984](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526086984)
  **SUCCESS**: `F03_NATIVE_WORKER_WIRE_BOUNDS=PASS`, existing safe-open
  and read tests PASS, owned cleanup PASS. The fixture uses anonymous
  pipes with `runOne` invoked in another thread of the *same process*;
  it verifies valid text, bad checksum, wrong kind, excess length,
  missing TXT, UNC, and error replies. It does **not** prove real
  CreateProcess/job supervision or kill-on-timeout handling.
  Prior runs [#38525652361](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38525652361)
  and [#38525878610](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38525878610)
  failed this newly added test: the negative missing-file fixture used
  `.missing` (unsupported extension) instead of `.missing.txt`,
  so the correct earlier format rejection was mismatched against the
  later unsafe-file status. Test fixture corrected; product behavior
  unchanged.
- **Exact source suite:** [central #38526337158](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526337158)
  **SUCCESS** at this SHA: policy, structure 4, product source 199,
  harness 20, infrastructure 30.
- **Exact Release build:** [central #38526567823](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526567823)
  **SUCCESS** with `scope=release` at this SHA. The tracked
  `app/winui/build.cmd` invokes `helper/build.cmd` first and requires
  the resulting helper executable before staging the app; the tracked
  helper project links the new worker, reader and safe-open code. This
  establishes compile/link/staging integration, **not** actual parent
  launch/response/timeout/shutdown acceptance.
- **Next acceptance gate:** add an owned-process PreviewController/
  supervisor using existing job-bound helper patterns, exact process and
  pipe handles, non-blocking UI dispatch, one active request per owning
  pane/tab identity, fast cancellation/kill-on-timeout and stale-result
  rejection. Validate the real `--preview-read` child with malformed,
  oversized, slow and canceled requests before wiring any UI.

## Phase 2 safe-open acceptance evidence (bounded)

- [MSVC owned native run #38522342210](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38522342210):
  PASS at SHA `b6c7c268354493f48ac94d22c77156f87d101fd8` for guarded
  nested-file open/read, rejected UNC/ADS/traversal/changed-size/cancelled
  input and actual **file and ancestor-directory symbolic link** rejection
  (both symlink creation probes succeeded, not skipped). Cleanup PASS.
- [Corrected native run #38523226489](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523226489):
  PASS at SHA `aca6bc779de2408a3eccc73ba63c5a1e205f3a39`. The test
  fixes dangling `wstring_view` fixtures by retaining path storage and
  deleting the temporary-string helper overload. The safe opener now
  copies the candidate path *before* policy screening; path allocation
  exceptions are caught instead of crossing a `noexcept` boundary.
- [Final corrected source suite #38523664886](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523664886):
  PASS at SHA `8ecd748a126f58b9c81f88ad026fe8a434a4d77a`, scope
  `source`: policy, structure 4, product-source 196, harness 20 and
  infrastructure 30 all passed. The prior run
  [#38523399332](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523399332)
  failed because one static test still searched for `screen(candidate)`
  after the code was refactored to `screen(stable)`; the test was
  corrected without weakening the owned-path requirement.
- **Release validation at this code SHA:** [central run #38523831041](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523831041)
  subsequently completed **SUCCESS**: `file_preview_safe_open.cpp`
  was included in the app Release build. Exact-SHA evidence is limited
  to this original worker-free code revision.

The opener walks canonical drive paths component by component, opening
directories using `FILE_FLAG_OPEN_REPARSE_POINT`, verifying opened-handle
final DOS paths, reparse/offline/directory attributes, volume serial, regular
file size and fixed-local drive, and retaining ancestor handles through the
file read to reduce rename/reparse swaps. It refuses unsafe paths rather
than following them. It does **not** yet isolate blocking OS calls or
provide a bounded wire, worker termination, pixel decoder, or stale
PaneTab/WindowTab result rejection. Those remain explicit gates.

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
2. **Authoritative worker/handle validation (PARTIALLY IMPLEMENTED):**
   The `readVerifiedHandle` primitive checks an already-opened file
   handle, final path/volume, reparse/directory flags, file size and changed
   metadata, performs bounded reads with cooperative cancellation and strict
   inert UTF-8 validation. It is currently called only in a test executable.
   A production safe opener must run outside the XAML thread in a bounded,
   cancellable worker or existing isolated helper. Require handle-based local fixed
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
