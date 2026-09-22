# Fluent command-icon mapping inventory

This inventory maps the existing flyExplorer main-toolbar command/image contract to Microsoft Fluent UI System Icons candidates. It does **not** change runtime frame indexes yet.

The current bitmap strips remain canonical until deterministic SVG rasterization is implemented and verified against the existing 16/22-pixel, 51-frame resource contract.

| Current frame | Command | Fluent candidate | Status |
| ---: | --- | --- | --- |
| 0 | `ID_GO_BACK` | `Arrow Left 20 Regular` | vendored prototype |
| 1 | `ID_GO_FORWARD` | `Arrow Right 20 Regular` | vendored prototype |
| 2 | `ID_GO_UP` | `Arrow Up 20 Regular` | vendored prototype |
| 3 | `ID_GO_HISTORY` | `History 20 Regular` | mapping verified upstream; not vendored yet |
| 7 | `ID_VIEW_FOLDER_TREE_SHOW` | `Folder Open 20 Regular` | mapping verified upstream; semantic review before rasterization |
| 8 | `ID_TOOL_FILE_SEARCH` | `Search 20 Regular` | vendored prototype |
| 10 | `ID_GO_BOOKMARK` | `Star 20 Regular` | mapping verified upstream; not vendored yet |
| 11 | `ID_GO_DRIVE` | `Hard Drive 20 Regular` | mapping verified upstream; not vendored yet |
| 12 | `ID_EDIT_CUT` | `Cut 20 Regular` | vendored prototype |
| 13 | `ID_EDIT_COPY` | `Copy 20 Regular` | vendored prototype |
| 14 | `ID_EDIT_PASTE` | `Clipboard Paste 20 Regular` | vendored prototype |
| 18 | `ID_FILE_RENAME` | `Rename 20 Regular` | mapping verified upstream; not vendored yet |
| 19 | `ID_FILE_DELETE` | `Delete 20 Regular` | mapping verified upstream; not vendored yet |
| 20 | `ID_FILE_PROPERTY` | `Info 20 Regular` | candidate; semantic review required |
| 21 | `ID_WINDOW_SPLIT` | `Window Multiple 20 Regular` | candidate; semantic review required |
| 26 | `ID_VIEW_STYLE` | `Apps List 20 Regular` | candidate; semantic review required |
| 27 | `ID_TOOL_EMPTY_RECYCLEBIN` | `Recycle 20 Regular` | mapping verified upstream; not vendored yet |
| 31 | `ID_TOOL_CMD` | `Window Console 20 Regular` | mapping verified upstream; not vendored yet |
| 32 | `ID_FILE_PRINT` | `Document Print 20 Regular` | mapping verified upstream; not vendored yet |
| 36 | `ID_VIEW_PICVIEWER` | `Image 20 Regular` | mapping verified upstream; not vendored yet |
| 37 | `ID_FILE_NEW_FOLDER` | `Folder Add 20 Regular` | vendored prototype |
| 38 | `ID_TOOL_OPTION` | `Settings 20 Regular` | vendored prototype |
| 41 | `ID_FILE_VIEW` | `Document 20 Regular` | mapping verified upstream; semantic review required |
| 42 | `ID_FILE_EDIT` | `Document Edit 20 Regular` | mapping verified upstream; not vendored yet |
| 43 | `ID_GO_WORKING_FOLDER` | `Folder 20 Regular` | candidate; working-folder state needs review |

## Rules

- Preserve the existing command IDs and image indexes during artwork migration.
- Do not replace Shell-owned file/folder icons with Fluent application-command artwork.
- Prefer Regular glyphs for neutral commands. Use Filled only when an actual active/selected semantic state needs it.
- Generate both 16px and 22px legacy strip cells from the same canonical SVG mapping; do not hand-edit hot/cold strips independently.
- Theme color should be applied at rasterization/runtime composition rather than by maintaining separate unrelated artwork drawings.
- No network download is allowed during normal builds.
