# Native menu and toolbar Customize appearance audit (2026-09-29)

**Publication context:** The “local uncommitted” wording below documents the original acceptance snapshot and earlier exact EXE. Later, the same source was freshly rebuilt and its separate real native menu/wheel GUI test passed; the new EXE SHA256 and combined UXH-07 prepublication verification are recorded in [UXH07_PUSH_VERIFICATION_20260929.md](UXH07_PUSH_VERIFICATION_20260929.md). This remains a scoped feature-branch checkpoint, not a product-wide UI certification.


Scope: LOCAL uncommitted branch fix/uxh07-named-workspaces-20260928 at HEAD 7cc0b46. Not merged or published. User screenshots are the reported examples, not evidence of wider OS acceptance.

## Confirmed defects and corrections

1. The canonical Korean.xml contained literal ?? placeholders for the Workspaces submenu and Save As/Open labels. All three now contain proper Korean text with unchanged W/S/O mnemonics. The resulting x64 language file matches the source and a full canonical Korean XML scan found no remaining double-question String values.
2. BCMenu::drawSubmenuChevron used a 12-DIP Segoe icon font and a small/thin fallback with secondary foreground. It now draws one font-independent two-segment > glyph with a two-DIP DPI-scaled stroke, five-DIP half-height, primary text contrast and explicit system colors in Windows High Contrast. Native menu ownership and command routing were not changed.
3. Windows-created toolbar TB_CUSTOMIZE uses CCustomizeDialog, which bypasses the normal CModernDialog child theme traversal. Previously the two ListBoxes received an Explorer theme only, not the shared dark scrollbar compositor, and the native parent labels/background/buttons lacked the full palette bridge. These native controls now use the existing shared dialog theme and dark scrollbar implementation, with light/high-contrast fallback.

The canonical source invariant was updated from the old icon-font requirement to a stronger single native two-stroke chevron check. The new focused source regression tests cover localization, chevrons and native Customize theme/scrollbar enrollment: 3/3 PASS.

## Exact verified build and real Windows GUI

Final x64 executable SHA256: C0FF584E685E7DEEF6E3844AC7F0A55E2AA541DE0235B66F1BA7859826E64E79.
Local local_ci.bat x64 exited 0: release compile/link, warnings policy and source preflight PASS; native functional tests 17 passed / 0 failed. Overall result PASS_WITH_SKIPS because automatic smoke declined to change pre-existing user HKCU settings. The command-process environment alone supplied missing ProgramFiles(x86) and TMP, without changing global OS settings.

Two isolated real Windows 11 GUI runs on that compiled binary showed repaired Korean submenu and larger single chevrons. Actual native toolbar customization showed BOTH dark ListBox scrollbar regions (sample pixels 35,35,35). A real physical mouse wheel scrolled the left native ListBox top index from 0 to 9; the dark scrollbar remained visible. Both app processes exited 0, test-owned fixtures were removed and all six original user config SHA256 hashes stayed identical.

Ignored local evidence:
- logs/ui-legacy-owned-first-real-gui.log
- logs/ui-legacy-owned-real-wheel-gui.log
- logs/ui-legacy-owned-workspaces-menu.png
- logs/ui-legacy-owned-toolbar-customize.png
- logs/ui-legacy-owned-toolbar-scrolled.png
- logs/ui-legacy-menu-toolbar-local-ci-fixed.log

## Wider source audit and remaining limitations

Inventory: 24 direct CWnd/CDialog base declarations in product headers. Several are internal message-sink utilities, not visual dialogs. CfgDlg, CfgMainDlg, DriveDetailDlg, TitleDlg, CResizingDialog, CColourPopupXP, CToolBarPopup and tab/status bar components already show their own ModernUI integration; do not assume they are broken or blindly replace their framework base. FolderPane, TabPane and CWindowScroller merit isolated composition/scrollbar GUI review where their individual implementation files do not reference ModernUI; parent-owned theming may be sufficient, so these are CANDIDATES, NOT confirmed defects. Windows-managed Shell/context menus and popup overflow indicators are separate ownership paths; do not globally skin them with undocumented hooks.

This audit does NOT certify every application dialog or popup, real 125/150/200 DPI, operating-system High Contrast, spoken accessibility, fully mouse-only top-level View navigation, all native menu-overflow scroll cases or a clean machine install. Evaluate any newly reported screen against concrete window class, DPI, theme, input, and final pixels before changes. No GitHub Actions, push, merge, other-worktree edit or user-profile modification occurred.
