# Fluent UI System Icons source

Source: https://github.com/microsoft/fluentui-system-icons

The files in this directory are the vendored Microsoft Fluent artwork source for flyExplorer application-command chrome.

- License: MIT, copied from the upstream repository.
- `toolbar_manifest.json` is the machine-readable frame/command/source contract. It currently contains 23 runtime Fluent commands: all 21 Main Toolbar commands enabled by default plus optional History and Settings.
- `build/generate_fluent_toolbar_assets.py` uses Python standard-library code only. It performs no network access and deterministically converts the audited SVG subset into theme-neutral 1-bit mask include files.
- Prefer official 16px Regular SVGs for the small toolbar and 20px Regular SVGs for the large toolbar. For the few upstream glyphs without a 16px Regular source, the audited 20px source is deterministically scaled into the 16px design cell.
- `src/fxfile/gui/FluentCommandIcons.*` owns the shared command-ID lookup/runtime HICON adapter. Main Toolbar and app-owned BCMenu use the same command artwork; settings navigation overlays only strong semantic matches.
- Runtime applies `ThemePalette.mText` or the appropriate secondary/disabled text color, so the same source follows System/Light/Dark without unrelated light/dark icon copies.
- `COMMAND_ICON_MAP.md` records the existing toolbar command/frame contract and remaining legacy artwork debt.
- Do not replace Windows Shell file/folder icons with these assets.
- Do not make normal builds download assets from the network.
- Existing 16px/22px, 51-frame bitmap resources and image indexes remain the persistence/fallback contract for non-migrated frames.
- `config_tree.bmp` remains the 33-frame fallback contract; selected application-navigation frames are overlaid at runtime with semantic Fluent glyphs outside High Contrast.
- Files named `generated_toolbar_masks_*.inc` are generated artifacts. Do not hand-edit them; use `python build/generate_fluent_toolbar_assets.py --write`.
