# M2.4 scoped Windows integration and release gates (2026-09-30)

Worktree: migration/winui3-full-shell-20260929. This evidence belongs to the independent WinUI 3 preview, not the protected MFC main product.

## 1. Windows Explorer file clipboard

The existing cross-UI native clipboard core implements bounded UTF-16 CF_HDROP and Preferred DropEffect, validates paths and reuses native Shell transfer. This turn added `experiments/phase6_winui_shell/manual_owned_clipboard_probe.py` with four manually triggered WinUI-to-Explorer and Explorer-to-WinUI copy/cut scenarios, real file-content checks and original six-user-settings checks. It requires an actual interactive human console and initially EMPTY global clipboard. The current user clipboard was populated at read-only format-count preflight; actual clipboard mutation and all four real interoperability flows remain NOT TESTED. There is no proven way to losslessly snapshot every arbitrary global user clipboard format. Do not clear/overwrite it from unattended tests.

## 2. File list and large folder

New `src/base/shell_assoc_type_core.*` makes a bounded 2.5-second registered filename-extension type lookup via exact owned FlyShellIsolationHelper.exe process, avoiding Shell association handlers on the WinUI UI thread. The preview now displays generic Segoe Fluent file/folder glyphs and individual name/type/size/modified columns with independent adjustable name-column widths. The actual native Debug helper returned installed Korean names for .txt/.png; the owned integrated Debug GUI actually verified installed file type, live width adjustment and original workflows in `logs/winui-scoped/20260930-075012-gui-Debug.log`.

Generic glyphs are NOT installed type-specific Windows icons or thumbnails; other three column widths remain fixed. A synthetic 1,100-file owned folder failed to open in actual WinUI Debug; the exact native one-shot helper returned all 1,100 items (1,038,279 reply bytes) in ~0.07s. The exact cause was the supervisor treating a fast helper exit as EOF while unread bytes remained in its reply pipe. The bounded receiver now drains pending data after child exit only while making positive read progress; an empty pipe with a truncated response still fails. After the correction and new Debug compilation, actual isolated WinUI opened an owned 1,100-file folder, rendered its first row in 2.4 seconds, completed descending name sorting and preserved all six original user settings. Evidence: `logs/m23/20260930-owned-1100-after-drain-fix.log`. This is a bounded 1,100-item subset, not tens-of-thousands scale or streaming virtualization.

## 3. Actual test-owned Recycle Bin

A unique test-owned WinUI Debug file was moved to the actual OS Recycle Bin after real GUI confirmation. Initial Python automation used an ineffective InvokeVerb and, without modifying other items, recovered the exact sole owned item via installed locale FolderItemVerb.DoIt and checked original bytes. The corrected guarded `test_owned_recycle_gui.py` explicitly requires an initially empty bin and matches both unique item filename and original deletion path before restoring. A fresh second test confirmed WinUI actual recycle, Windows actual restore, an empty Bin and all original six user settings unchanged; log `logs/m23/20260930-owned-recycle-doit-retest.log`. One-item success is not bulk Recycle Bin/collision certification.

## 4. Windows integration and default-product cutover matrix

| Gate | Scoped evidence and remaining work |
|---|---|
| Basic two-pane/tabs, create/rename/copy/move/collision/session | Latest revised x64 Debug + Release test-owned integrated GUI both PASS, six MFC profile hashes unchanged |
| Windows Explorer real file clipboard | Human-controlled empty clipboard and four actual directions still pending |
| Recycle Bin actual single owned file | Debug owned real delete/restore PASS; multi-item/restore collision not tested |
| Windows registered file type, list column accessibility | Actual helper .txt/.png Korean OS type, accessible per-pane name-column resize and generic file/folder glyphs PASS on revised Debug + Release full GUI; real association icons, thumbnails and all-column resize still missing |
| Large folder | initial 1,100 failure fixed; new actual Debug and Release 1,100-item navigation and descending sort passed; first-list renders 2.4s and 0.98s respectively; >1,200 paging still missing |
| OS DPI, High Contrast, keyboard/IME, Narrator | Read-only actual 96 DPI (100%)/High Contrast OFF; owned Release UIA file-list and slider accessible names PASS. Other DPI, enabled HCM, IME and Narrator remain NOT TESTED |
| Third-party Shell context menu/provider | Basic app-owned menu only; isolated third-party context extensions/SMB still missing |
| Installed x64 preview, update/rollback, whole MFC parity | 20 hashed Release files including validated Assets/resources copied and launched with exact owned EXE and registered type PASS; real clean installation/update/rollback and full MFC parity remain NOT IMPLEMENTED/NOT TESTED |

Do not silently change the original MFC main binary, the user configuration, clipboard, unowned Recycle Bin contents, registry associations or installer. No default WinUI product cutover until owner-approved parity, reliability and OS integration gates pass.

## Verified final evidence for this independent preview

- Official source preflight PASS, 119 source tests with 118 PASS and one supported environmental SKIP. Both new x64 Debug and Release WinUI binaries actually compiled from the revised migration source.
- Latest compiled full test-owned Debug GUI: `logs/winui-scoped/20260930-081358-gui-Debug.log` PASS. Latest compiled full test-owned Release GUI: `logs/winui-scoped/20260930-081016-gui-Release.log` PASS; actual read-only DPI 96/100%, High Contrast OFF and accessible row/slider names recorded.
- Exact owned 1,100 child stress after pipe-drain correction: Debug `logs/m23/20260930-owned-1100-after-drain-fix.log` (first render ~2.4 sec), Release `logs/m23/20260930-owned-release-1100.log` (~0.98 sec), both actual navigation and descending sort PASS; 1,200+ pagination and network/virtual scalability remain outside coverage.
- Noninstalled private copied Release preview: `logs/m23/20260930-private-copied-release-retake.log`: 20 hashed resource/runtime/Assets files copied, exact owned EXE launched, installed file-type label displayed, real MFC original setting hashes unchanged. Not signed, not installed, no update/rollback exercise.
- Actual one-item synthetic WinUI Debug Recycle Bin + exact restored original: `logs/m23/20260930-owned-recycle-doit-retest.log` PASS. The system/global OS clipboard had user content and was not overwritten; four manual WinUI-Explorer copy/cut directions remain NOT TESTED.
- Actual extension-specific Windows file icons/thumbnails, fully adjustable four columns, third-party Shell context extension isolation, 125/150/200% DPI, OS High Contrast ON, keyboard-only/IME/Narrator, credentialed providers, signed install/update/rollback and whole-MFC parity are NOT IMPLEMENTED or NOT TESTED. Do not promote this preview to default.
