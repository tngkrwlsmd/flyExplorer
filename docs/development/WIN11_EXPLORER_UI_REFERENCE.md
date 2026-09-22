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
- A new SVG rasterizer dependency: the canonical Fluent SVG set and command/frame mapping are established first. Runtime bitmap replacement waits until a converter can be pinned with verified license, deterministic 16/22-pixel output, offline Windows developer availability, and no normal-build network dependency.

## Fluent asset prototype

`src/fxfile/res/fluent/` contains the Microsoft MIT license, a representative canonical SVG source set for Back/Forward/Up/Search/Cut/Copy/Paste/New Folder/Settings, and `COMMAND_ICON_MAP.md` mapping those semantics onto existing flyExplorer command/frame contracts.
The SVG sources are registered in canonical `fxfile.gyp`, but the runtime toolbar bitmap contract remains unchanged until a deterministic rasterization step is selected and verified against the existing 16/22-pixel 51-frame invariants.

## Implemented convergence checkpoint

- Dark settings checkbox/radio labels now use a ThemePalette-backed paint adapter only in Dark/non-High-Contrast; native button input/check/keyboard semantics remain intact.
- Dark AddressBar controls reset the Explorer visual-style association so the existing palette adapters own the complete surface; Light/High Contrast retain the documented native association path.
- App-owned BCMenu submenu arrows use the system-installed Segoe Fluent Icons `ChevronRightSmall` glyph (U+E970) when available and a geometry fallback otherwise.
- Popup shared metrics were tightened from the earlier oversized legacy proportions; shell-owned IContextMenu rendering/routing remains untouched.
- The representative Fluent SVG set is still a source/provenance and mapping foundation, not yet a runtime toolbar replacement.
- Dark settings ComboBox drop-down ListBox handles reset the Explorer visual-style association after `CB_SHOWDROPDOWN`, allowing the existing palette CTLCOLOR path to own list text/background while preserving native dropdown/keyboard behavior.
