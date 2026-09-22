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

## Fluent asset prototype

`src/fxfile/res/fluent/` contains the first canonical upstream SVG sample and its Microsoft MIT license.
The runtime toolbar bitmap contract remains unchanged until a deterministic rasterization step is selected and verified against the existing 16/22-pixel frame/index invariants.
