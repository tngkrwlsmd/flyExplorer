# Fluent UI System Icons toolbar source

Source: https://github.com/microsoft/fluentui-system-icons

The files in this directory are a deliberately small vendored subset used as
the canonical Microsoft Fluent artwork source for flyExplorer application
chrome.

- License: MIT, copied from the upstream repository.
- Representative Main Toolbar commands have official 16px Regular sources for
  the small toolbar and 20px Regular sources for the large toolbar.
- `toolbar_manifest.json` is the machine-readable frame/command/source
  contract for the representative runtime migration.
- `build/generate_fluent_toolbar_assets.py` uses Python standard-library code
  only. It performs no network access and deterministically converts the
  audited SVG subset into generated theme-neutral 1-bit mask include files.
- Runtime code applies `ThemePalette.mText` to those masks, so the same
  canonical SVG source follows System/Light/Dark/High Contrast instead of
  maintaining unrelated light/dark artwork.
- `COMMAND_ICON_MAP.md` records the existing toolbar command/frame contract
  and the remaining legacy artwork debt.
- Do not replace Windows Shell file/folder icons with these assets.
- Do not make normal builds download assets from the network.
- Existing 16px/22px, 51-frame bitmap resources and image indexes remain
  canonical for non-migrated frames and persisted toolbar customization.
- Files named `generated_toolbar_masks_*.inc` are generated artifacts. Do not
  hand-edit them; use `python build/generate_fluent_toolbar_assets.py --write`.
