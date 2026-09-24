# Windows 11 Explorer UI reference policy

flyExplorer keeps its MFC/Win32 file-manager behavior while converging visually on the current Windows 11 File Explorer.

## Source priority

1. Microsoft public design assets.
2. Documented Windows APIs.
3. Windows system theme, font, color and DPI metrics.
4. Documented Win32/MFC control customization.
5. Minimal custom drawing only where the earlier layers do not provide the required result.

Private Explorer APIs, undocumented dark-theme strings, and resource extraction from Windows binaries are not implementation dependencies.

## Official sources reviewed on 2026-09-22

- Fluent UI System Icons: https://github.com/microsoft/fluentui-system-icons
  - Microsoft-maintained public icon collection.
  - SVG package currently declares MIT license.
  - flyExplorer may vendor only the required SVG source files and the matching license; the build must not require a network download.
- Segoe Fluent Icons: https://learn.microsoft.com/windows/apps/design/iconography/segoe-fluent-icons-font
  - Recommended Windows 11 symbol font.
  - It is not installed by default on Windows 10.
  - Use only as an optional system-provided glyph source with a fallback; do not vendor the font file.
- SetWindowTheme: https://learn.microsoft.com/windows/win32/api/uxtheme/nf-uxtheme-setwindowtheme
  - Documented way to apply a different visual-style association such as Explorer.
  - Association is not equivalent to app Dark ownership.
- DWM window attributes: https://learn.microsoft.com/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
  - DWMWA_USE_IMMERSIVE_DARK_MODE and DWMWA_WINDOW_CORNER_PREFERENCE are suitable for top-level non-client integration on supported Windows.
  - DWMWA_SYSTEMBACKDROP_TYPE is supported from Windows 11 build 22621 and must retain an older-Windows fallback.
- Windows system backdrops: https://learn.microsoft.com/windows/apps/develop/ui/system-backdrops
  - Mica is intended as a long-lived window foundation; Acrylic is intended for transient surfaces.
  - flyExplorer does not add a Windows App SDK/XAML dependency merely to decorate an otherwise opaque MFC window.
- High Contrast: https://learn.microsoft.com/windows/win32/controls/supporting-high-contrast-themes
  - System colors and accessibility rendering take precedence over custom Light/Dark presentation.

## Current adoption decisions

### Adopt now

- Fluent UI System Icons as the canonical future source for application-command artwork.
- System typography and DPI-aware metrics.
- Documented DWM frame dark/corner attributes already present in ModernUI.
- Documented SetWindowTheme where native control ownership remains useful.
- System-provided Segoe Fluent Icons only for small symbol-glyph prototypes with a geometry fallback.

### Keep behind fallback

- Any Windows 11-only DWM feature.
- Segoe Fluent Icons because Windows 10 does not include it by default.

### Not adopted in this checkpoint

- Windows App SDK / WinUI XAML Islands: too much runtime/build surface for the current MFC modernization checkpoint.
- Mica/Acrylic as a blanket fix: opaque MFC content means it does not solve button/menu/text theming by itself.
- Explorer private implementation/resource reuse: unsupported and intentionally outside project policy.
- A new third-party SVG rasterizer dependency: not adopted. The repository already uses the standard-library-only `build/generate_fluent_toolbar_assets.py` to generate deterministic 16/22-pixel masks from a deliberately limited vendored SVG subset, with unsupported SVG syntax rejected. It requires no network access.

## Fluent asset pipeline (implemented)

`src/fxfile/res/fluent/` contains the vendored Microsoft MIT license, 16/20-pixel Regular SVG source files and `toolbar_manifest.json` for 23 runtime command IDs. `COMMAND_ICON_MAP.md` documents the mapping. Canonical `fxfile.gyp` registers the assets and generated output. The offline deterministic Python generator emits 16/22-pixel theme-neutral mask fragments, whose reproducibility is checked by source invariants. `FluentCommandIcons` uses them at runtime for all 21 default main-toolbar commands plus optional History/Settings and corresponding app-owned menu/settings overlays. The original 51-frame bitmap/index contract remains for non-migrated items, persisted indices and legacy/High Contrast fallback.

## Implemented convergence checkpoint

- Dark settings checkbox/radio labels now use a ThemePalette-backed paint adapter only in Dark/non-High-Contrast; native button input/check/keyboard semantics remain intact.
- Dark AddressBar controls reset the Explorer visual-style association so the existing palette adapters own the complete surface; Light/High Contrast retain the documented native association path.
- App-owned BCMenu submenu arrows use the system-installed Segoe Fluent Icons `ChevronRightSmall` glyph (U+E970) when available and a geometry fallback otherwise.
- Popup shared metrics were tightened from the earlier oversized legacy proportions; shell-owned IContextMenu rendering/routing remains untouched.
- The Fluent SVG/manifest pipeline is now an active runtime replacement for 23 command IDs: all 21 Main Toolbar commands enabled by default plus optional History and Settings. Main Toolbar and app-owned BCMenu share `FluentCommandIcons`; settings navigation overlays 17 strong semantic matches while preserving the historical bitmap fallback and High Contrast path.
- Dark settings ComboBox drop-down ListBox handles reset the Explorer visual-style association after `CB_SHOWDROPDOWN`, allowing the existing palette CTLCOLOR path to own list text/background while preserving native dropdown/keyboard behavior.

## Current supported-Windows rendering status (2026-09-24)

`6b18c58f` adds `WinAppEx::osWinModern` so supported Windows 10/11 no
longer enters XP-only presentation branches, while `IsWinXPOrLater()`
preserves legacy API-capability checks. The source invariant now guards the
classification and capability mapping. Local x64 build/functional evidence
for the change is recorded as PASS WITH SKIPS, not matching post-fix
interactive Dark/Light/High Contrast visual evidence. Keep the issue open
until rebuilt Windows screenshots verify the original acceptance case;
see `docs/development/ERROR_HISTORY.md`.
