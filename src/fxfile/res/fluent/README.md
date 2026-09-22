# Fluent UI System Icons prototype

Source: https://github.com/microsoft/fluentui-system-icons

The files in this directory are a deliberately small vendored subset used to establish a canonical Microsoft Fluent artwork source for flyExplorer application chrome.

- License: MIT, copied from the upstream repository.
- First source prototype: `ic_fluent_settings_16_regular.svg`.
- Representative 20px command sources are vendored for Back/Forward/Up/Search/Cut/Copy/Paste/New Folder/Settings.
- `COMMAND_ICON_MAP.md` maps current toolbar commands/frame indexes to Fluent candidates without changing runtime image indexes.
- Do not replace Windows Shell file/folder icons with these assets.
- Do not make normal builds download assets from the network.
- Existing toolbar bitmap frame/index contracts stay canonical until deterministic SVG rasterization is introduced and validated.
