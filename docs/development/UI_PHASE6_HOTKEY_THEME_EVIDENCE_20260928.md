# Phase 6 UXH-01 ? native hotkey control dark appearance

Baseline: main 72a84476fa79e3b6d0193f4e0e9aa64e781d2ac8, branch
fix/uxh01-native-hotkey-dark-20260928, real Windows 11 x64
single-monitor 96-DPI desktop. Opt-in WinUI experiment untouched.

## Root cause and narrowly scoped product fix

A CHotKeyCtrl uses msctls_hotkey32, not the native Edit class.
CModernDialog's existing CTLCOLOR_EDIT and generic Edit subclass
do not own the hotkey class's painted background. On the actual
Dark owned GUI before this patch, its interior dark sample ratio
was 0.025 initially and 0.013 after actual Ctrl+2 keyboard input:
it stayed bright in an otherwise dark bookmark dialog.

ModernUI::applyDialogControlTheme now recognizes msctls_hotkey32
and attaches the shared DialogHotKeySubclassProc. Dark mode alone
renders the client background with the shared elevated palette,
native-hotkey contents from HKM_GETHOTKEY, modifier labels,
localized Win32 GetKeyNameTextW and a visible focus border.
Normal native HKM, keyboard, and WM_GETFONT behavior is preserved
by DefSubclassProc; custom painting does not replace HWND/input.
High Contrast and Light deliberately retain the standard native
painting path. The subclass removes itself on WM_NCDESTROY.
CfgDlg and CModernDialog both use the shared child-theme path,
but their other real hotkey screens need separate GUI acceptance.

## Actual release and owned GUI verification

- Product incremental Release-x64-Unicode x64 build: EXIT 0.
- Source contract: build/test_ui_hotkey_theme_contract.py PASS.
- Native source invariants: PASS.
- Existing native functional regressions: 17 PASS, 0 FAIL.
- Actual owned bookmark dialog Dark: initial dark ratio 1.000,
  physical Ctrl+2 accepted as 0x0232; repainted dark ratio 0.933.
- Actual owned bookmark dialog Light: initial dark ratio 0.004,
  physical Ctrl+2 accepted as 0x0232; repainted dark ratio 0.013.
- All test-owned app instances exited 0. Original user config
  file SHA256 hashes for all six files unchanged.
- Final tested Release binary SHA256:
  28DB8CD52E9FBF716BE5150508EDCEFE397431ED6E84D14945814AF810D8BE63.

Screenshots and full logs remain LOCAL only in ignored logs,
including hotkey-dark-before/after and hotkey-light-before/after.
No changes were committed to original bookmark data.

Not claimed: actual global hotkey settings and accelerator table
individual GUI acceptance, real Win32 High Contrast, 125/150/200%
DPI, Korean modifier label localization, real screen-reader run,
or a clean-machine installer. These remain independently open.
