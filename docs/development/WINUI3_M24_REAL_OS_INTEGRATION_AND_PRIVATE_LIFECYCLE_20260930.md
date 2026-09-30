# M2.4 actual Windows integration and scoped two-version lifecycle (2026-09-30)

Scope: separate migration/winui3-full-shell-20260929 WinUI 3 preview only. Preserve original MFC main, real six original MFC configurations and every unrelated user file. This follow-up updates the earlier WINUI3_M24_SCOPED_WINDOWS_INTEGRATION_20260930.md report. It does NOT establish full MFC parity or production installer certification.

## Real Windows global clipboard: approved destructive clearing

The owner explicitly authorized global clipboard initialization. New `test_owned_explorer_clipboard_gui.py` requires `--apply-clear-clipboard`, creates synthetic files only, starts exact owned private-profile WinUI PID, identifies a new real Windows Explorer HWND that did not exist before the test and checks its exact owned LocationURL. It never automates an existing Explorer window. Real Windows CF_HDROP/Preferred DropEffect, file bytes and source preservation/removal are checked. The global clipboard is explicitly cleared again in finally, and its original contents intentionally are NOT restored.

The first sequential 4-direction test passed 3/4 before the last cut/paste timed out; that fourth direction independently passed. The harness was corrected to wait for real native transfer completion and directory watcher settling, and a new actual single-session GUI then passed all FOUR directions: WinUI->Explorer Copy, Explorer->WinUI Copy, WinUI->Explorer Cut and Explorer->WinUI Cut, including exact file bytes, move semantics and original six configuration hashes. Evidence: `logs/m24/20260930-four-directions-after-native-watcher-waits-debug.log`. Other delayed-rendered third-party clipboard formats and multi-parent mixed-source paste remain untested.

## Real Windows registered icons and actual image thumbnails

The OS-installed TXT and PNG association icon buffers are returned from a bounded disposable exact sibling Shell helper using SHGetFileInfoW with SHGFI_ICON and encoded BGRA, never invoking registered association providers on the WinUI STA. Direct actual Debug AND Release helper probes returned two different valid 1024-byte icons; actual WinUI Debug rendered the registered icon in its accessible file row. The background metadata fetch now recovers up to two individual extensions if a batched lookup misses registered type data; this was motivated by one intermittent full Release GUI failure, whose exact cause was not independently proven. After the bounded change, the newer revision actual full Release GUI passed (log `logs/winui-scoped/20260930-095439-gui-Release.log`); do not discard the initial failing log.

The new shell_thumbnail_core requests up to four eligible local fixed-drive images per folder from an exact owned one-shot helper. An isolated COM STA calls IShellItemImageFactory for images <=32MB with no reparse ancestry, 1800ms per image timeout and bounded 16..128px BGRA reply. The existing native route/epoch check prevents stale results from overwriting a newly selected folder. A real synthetic 64x64 multicolor PNG returned an exact THMB 64x64 payload; an actual owned Debug WinUI file row displayed an accessible Windows Shell image thumbnail. Evidence: `logs/m24/20260930-owned-winui-real-png-thumbnail-debug-fixed.log`. Image types .png/.jpg/.jpeg/.bmp/.webp are permitted, but not all have been verified; no full gallery cache or virtualized many-thousand-thumbnail promise.

## Isolated external Shell context menu

Both WinUI panes now have a separate explicit Shell menu action in addition to existing app-owned file-operation menu items. An exact owned helper subprocess reads only one selected, validated local fixed-drive item through a private pipe and uses real IContextMenu/IContextMenu2/3 to display provider menu popups. Built-in destructive and copy/move verbs are intentionally rejected and missing or noncanonical provider verbs are refused rather than silently using unvalidated operations. Timeout: 45s; this is a fault boundary, NOT a security sandbox.

The exact native helper exposed 20 installed context-menu entries on an owned real TXT file without modification. A real Debug WinUI GUI selected an owned file, launched the isolated real popup in the exact child PID, used ESC only and confirmed original file bytes and MFC settings untouched. Evidence: `logs/m24/20260930-test-owned-WinUI-native-context-popup-debug.log`. Actual third-party provider command execution, ownership in untrusted processes and crash recovery of arbitrary installed third-party extensions remain uncertified.

## Known unresolved issue: isolated context-menu UIA automation

The native exact owned helper enumerated 20 installed context-menu entries on a synthetic TXT item and the earlier real Debug owned GUI opened the exact isolated Shell popup and safely closed it with ESC. These are direct but bounded execution observations, not proof that every GUI invocation path is reliable. A later, more restrictive owned-window UIA right-click harness, `experiments/phase6_winui_shell/test_owned_context_menu_gui.py`, reported `Owned Shell menu launch item absent` when resolving the app-owned flyout item; it logged an owned menu containing only the system entry in `logs/m24/20260930-final-owned-context-uiA-popup-diagnostic.log`. This did not change the test source file or any original MFC configuration. It remains **OPEN: determine whether flyout invocation/selection or pywinauto UIA re-resolution is at fault**; do not report the newer GUI harness as PASS or claim all shell extensions work. The diagnostic harness is committed for reproducibility but excluded from the automated PASS gate; a fresh exact owned-process GUI reproduction is required before closing this issue.

## Accessibility: actual connected desktop and honest VM/manual gates

Connected remote PC: one actual 1280x768 monitor, 96 DPI/100% Windows scale, High Contrast OFF. Actual owned Debug GUI was resized (only its own HWND) to 960x634, 1100x680 and 1240x710. At all three sizes, nine UIA control names and a real Korean file row were checked. Actual Tab key focus advanced with exact owned window foreground verified. System-wide scale/High Contrast were read-only before and after; no global OS setting changed, six MFC configs preserved. Evidence: `logs/m24/20260930-owned-current-DPI-keyboard-UIA-layout-debug.log`.

For real OS scale 125/150/200% (DPI120/144/192), High Contrast ON and spoken Narrator / real Korean IME composition, `manual_accessibility_matrix.py` is ready. It REQUIRES separately controlled Windows VM and interactive human, checks real OS DPI/HCM then prompts a person to confirm actual spoken Narrator and Korean composition. It has NOT been executed; merely resizing an app window or enumerating UIA does not certify those cases. No changes to the active user's global OS accessibility settings have been attempted.

## Genuine two-different-Release unpackaged private install, update, rollback and cleanup

Before new feature builds, the 20 real prior Release runtime/resources (including Assets and sibling helper) were copied to `logs/m24/lifecycle-owned-prior-v1/v1` with exact SHA256 manifest; the actual prior helper lacked the newer visual protocol. After the new Release built successfully, `test_owned_release_lifecycle.py` verified a DIFFERENT new EXE hash; staged an ignored private `installed` directory; launched real v1 with synthetic file and private APPDATA; switched to real v2 and launched; restored exact v1 SHA256 and launched; removed only the marker-verified test-owned installed directory. Every step passed, with six real MFC configs identical. Evidence: `logs/m24/20260930-two-real-builds-private-install-update-rollback.log`.

This is ACTUAL two-build UNPACKAGED file-based private preview lifecycle, not a signed NSIS/MSI/MSIX, new clean-machine Windows App SDK prerequisite setup, OS-wide registration, user program replacement, distribution channel or production rollback. Existing independent WinUI template sets WindowsPackageType=None; NSIS compiler was absent on this workstation. Signed/registered clean VM installation and release approval remain blocked until a dedicated VM, signing and explicit install scope are available. Do not install to the user's real product directory to simulate this.

## Distinct proof, remaining release gates

| Item | Proof | Not yet certified |
|---|---|---|
| Explorer real clipboard | One real WinUI/Explorer 4/4 GUI PASS, user-approved clear, all six config hashes unchanged | Arbitrary formats and mixed-parent clipboard selection |
| Registered OS icons | Distinct actual native TXT/PNG icons and owned WinUI Debug render; newer Release full integrated GUI PASS | Every association/icon state and very large folders |
| Real PNG thumbnail | Native THMB 64x64 and actual WinUI Debug image PASS | >4 thumbnails per folder, cache and all permitted formats |
| Isolated context menu | Native real 20 entries, actual WinUI popup+ESC PASS | Unknown third-party verb execution and robust fault recovery |
| Current OS accessibility | DPI96/HCM OFF, 3 owned sizes, 9 UIA names, real Tab key input PASS | Actual DPI125/150/200, HCM ON, Narrator and Korean IME need separate VM/human |
| Two genuine Release version lifecycle | Real v1 install/v2 update/v1 exact rollback/test-only uninstall PASS | Signed, OS-registered production installer, fresh machine/prerequisites |
| Overall | Static/native/compiled GUI evidence recorded per revision | Physical drag, entire MFC parity, network providers and approved product cutover |

All logs and old compiled v1 snapshot remain in ignored logs for exact recovery and must not be silently treated as source-controlled release artifacts.
