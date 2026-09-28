# 2026-09-28 ? Native MFC scrollbar inventory and AddressBar/modal overlap

Scope: the existing MFC UI, independent of the unmerged Phase 5 WinUI 3
experiment. Tested source baseline: main 8f8e3ea plus scoped changes.

## Full src/fxfile source inventory

The header, implementation and resource scan counts source files containing
references, NOT the number of actual scrollable HWND instances.

| Class or scrollbar reference | Source files | Reviewed handling |
| --- | ---: | --- |
| ListCtrlEx | 5 | Existing modern vertical/horizontal overlays on ExplorerCtrl, FileScrapCtrl and SearchResultCtrl. |
| TreeCtrlEx | 4 | Existing overlay/cleanup path for FolderCtrl and configuration tree. |
| CListCtrl | 22 | Most are direct dialog lists. CModernDialog, CResizingDialog and CfgDlg each use the shared child-theme helper; raw list controls previously lacked generic overlay installation. |
| CTreeCtrl | 9 | Dialog children use shared handling; CfgMainDlg uses TreeCtrlEx. |
| CListBox | 4 | Modern dialogs include shortcuts, group editor and IconList in FilterSetDlg. |
| CScrollBar | 13 | Includes native range/message helpers and WindowScroller. BookmarkSetWnd's custom viewport lacked an overlay, now installed and removed. The separate PicConvOptDlg numeric option slider is not a list viewport. |
| WS_VSCROLL or WS_HSCROLL | 10 | Includes explicit native styles, window classes, resource templates and existing primary list/tree handling. |

ModernUI::applyDialogControlTheme now attaches the shared click-through
native overlay to potential-scrolling SysListView32, SysTreeView32,
ListBox and scrollable Edit children. A WM_NCDESTROY subclass removes
the attachment, including in resizing and configuration dialogs. Light
and High Contrast use ordinary system scrolling instead. The custom
BookmarkSetWnd now attaches, refreshes and removes its own scrollbar
overlay. Main list/tree wrappers keep their pre-existing implementation.
Standalone option sliders and Windows scrollbar message helpers were
reviewed but are not forcibly replaced by a popup viewport overlay.

## Verified address-bar and modal overlap defect

Before the fix, the actual test-owned Windows GUI showed the address
dropdown still open when the ColumnSet modal had appeared. Its native
ComboLBox is a desktop-rooted popup: GA_ROOTOWNER identifies neither
the expected MainFrame nor its true activation owner. Relying on
GA_ROOTOWNER alone incorrectly suppressed the ordinary address
scrollbar and was rejected.

The final popup API receives the real MFC host HWND from AddressBar.
Only its opt-in topmost overlay tests its real host activation and
enabled state; all other overlays preserve the original non-topmost
z-order. Owner WM_ENABLE/activation resynchronizes the temporary popup.
CModernDialog closes any owned native open ComboBox dropdown on
initialization, and ColumnSetDlg explicitly owns the MainFrame.
In addition to dismissing the native popup, ColumnSetDlg now checks its
active AddressBar screen rectangle and its monitor's usable workspace.
When space permits, its native modal is placed just below the address
row with a DPI-scaled gap; small monitors retain default placement
instead of moving the modal off-screen.
Native combo hide, HWND destroy and AddressBar cleanup remove its
temporary topmost overlay. The column dialog reapplies the shared
palette and overlay after dynamically populating its direct list,
preserving Light and High Contrast fallback.

## Actual connected Windows 11 evidence (96 DPI)

- Incremental Release-x64-Unicode/x64 product build: PASS.
- Source invariants, existing UI-02 scrollbar tests, header/address
  tests and new source coverage tests: PASS.
- Test-owned Dark: one visible modern address overlay before
  ColumnSet, no open address dropdown or remaining address overlay
  after modal activation; modal list dark sample ratio 0.907 with a
  visible native-scrollbar dark overlay; mouse arrow input moved the
  modal list top item 0 to 1.
- Test-owned Light: no dark address overlay, no lingering address popup
  after modal activation; list dark sample ratio 0.03 and no dark list
  overlay; native scrollbar mouse input moved the top item 0 to 1.
- Both test-owned modes also passed a separate geometric no-overlap
  assertion when monitor workspace permits. At actual 96 DPI the
  address bar bottom was 321 px and the modal top was 331 px, a
  verified 10-pixel gap; the modal remained scrollable in each mode.
- Both test-owned processes exited 0; SHA256 values for all six
  original user configuration files remained unchanged.
- Native product functional regression: 17 passed, 0 failed.
- Runtime test: build/test_ui02_modal_scrollbar_runtime.py.
  Source audit contract: build/test_ui02_scrollbar_coverage.py.
- Neither GitHub Actions nor installer changes were performed.

These runtime samples do not prove actual 125/150/200% DPI, OS High
Contrast, every standalone slider skin or every individual dialog
layout. The source inventory and generic coverage are not substituted
for unexecuted screen-level tests. This does not merge the separate
experimental WinUI 3 productization branch into main.
