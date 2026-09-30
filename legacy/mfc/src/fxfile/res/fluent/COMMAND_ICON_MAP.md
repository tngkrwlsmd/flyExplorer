# Fluent command-icon mapping inventory

This inventory maps the existing flyExplorer main-toolbar command/image contract to Microsoft Fluent UI System Icons. Runtime frame indexes remain unchanged.

The runtime Fluent registry currently covers 23 commands. That includes all 21 commands enabled by default in the Main Toolbar plus the optional History and Settings commands. The historical 16/22-pixel, 51-frame bitmap strips remain the fallback and persistence/index contract for every non-migrated frame.

| Current frame | Command | Fluent source | Status |
| ---: | --- | --- | --- |
| 0 | `ID_GO_BACK` | `Arrow Left Regular` | runtime Fluent mask |
| 1 | `ID_GO_FORWARD` | `Arrow Right Regular` | runtime Fluent mask |
| 2 | `ID_GO_UP` | `Arrow Up Regular` | runtime Fluent mask |
| 3 | `ID_GO_HISTORY` | `History Regular` | runtime Fluent mask |
| 7 | `ID_VIEW_FOLDER_TREE_SHOW` | `Folder Open Regular` | runtime Fluent mask |
| 8 | `ID_TOOL_FILE_SEARCH` | `Search Regular` | runtime Fluent mask |
| 10 | `ID_GO_BOOKMARK` | `Star Regular` | runtime Fluent mask |
| 11 | `ID_GO_DRIVE` | `Hard Drive Regular` | runtime Fluent mask |
| 12 | `ID_EDIT_CUT` | `Cut Regular` | runtime Fluent mask |
| 13 | `ID_EDIT_COPY` | `Copy Regular` | runtime Fluent mask |
| 14 | `ID_EDIT_PASTE` | `Clipboard Paste Regular` | runtime Fluent mask |
| 18 | `ID_FILE_RENAME` | `Rename Regular` | runtime Fluent mask |
| 19 | `ID_FILE_DELETE` | `Delete Regular` | runtime Fluent mask |
| 20 | `ID_FILE_PROPERTY` | `Document Settings Regular` | runtime Fluent mask |
| 21 | `ID_WINDOW_SPLIT` | `Window Multiple Regular` | runtime Fluent mask |
| 26 | `ID_VIEW_STYLE` | `Apps List Regular` | runtime Fluent mask |
| 27 | `ID_TOOL_EMPTY_RECYCLEBIN` | `Bin Recycle Regular` | runtime Fluent mask |
| 28 | `ID_APP_ABOUT` | `Info Regular` | runtime Fluent mask |
| 29 | `ID_EDIT_UNDO` | `Arrow Undo Regular` | runtime Fluent mask |
| 31 | `ID_TOOL_CMD` | `Window Console Regular` | runtime Fluent mask |
| 37 | `ID_FILE_NEW_FOLDER` | `Folder Add Regular` | runtime Fluent mask |
| 38 | `ID_TOOL_OPTION` | `Settings Regular` | runtime Fluent mask |
| 43 | `ID_GO_WORKING_FOLDER` | `Folder Regular` | runtime Fluent mask |

## Remaining legacy main-toolbar artwork

The following non-default or specialized frames remain on the historical bitmap strips until their semantics are reviewed: working-folder slots 0-4, folder move/copy, attribute/time, split variants, split equal/swap, file-scrap view, print, picture viewer, file view/edit and the other non-command/reserved frames.

## Rules

- Preserve the existing command IDs and image indexes during artwork migration.
- Do not replace Shell-owned file/folder icons with Fluent application-command artwork.
- Prefer Regular glyphs for neutral commands. Use Filled only when an actual active/selected semantic state needs it.
- Prefer official 16px Regular SVGs for the 16px toolbar and official 20px Regular SVGs for the 22px large-toolbar cell. Where upstream has no 16px variant, the audited 20px source is deterministically scaled into the 16px design cell.
- `toolbar_manifest.json` is the canonical command/frame/SVG mapping. Generated masks must stay byte-for-byte reproducible from the manifest and vendored SVGs.
- `FluentCommandIcons` is the shared runtime adapter used by Main Toolbar, BCMenu and selected settings-tree navigation glyphs.
- Generated masks are theme-neutral; runtime applies ThemePalette text/secondary-text colors while existing custom draw owns hover/pressed surfaces.
- Do not reorder the historical 51-frame strip or hand-edit generated Fluent masks independently.
- No network download is allowed during normal builds.
