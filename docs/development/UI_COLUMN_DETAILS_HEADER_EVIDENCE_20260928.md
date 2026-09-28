# 2026-09-28 ? Native column selection: dark header and width controls

Scope: current MFC ColumnSetDlg, not the optional WinUI 3 experiment.
Root cause: this dialog uses a raw CListCtrl. Shared dark-list painting
changed SysListView32 item backgrounds and scrollbars but did not
subclass its independent native SysHeader32. The column header therefore
remained a bright OS control, unlike ExplorerCtrl's existing reusable
FlatHeaderCtrl. The selected-width numeric Edit was only 31x14 dialog
units, and its default unfocused border was the subdued separator color.
Small column boundaries had no intentional visual drag affordance.

## Limited product fix

- ColumnSetDlg holds its own lifetime-managed FlatHeaderCtrl member and
  subclasses the native list header after inserting its columns. It
  reuses the existing ModernUI palette and DPI-aware native header
  layout rather than replacing pointer-driven column sizing.
- A default-OFF FlatHeaderCtrl option renders a more distinct
  separator and three tiny resize-grip cues; enabled only in this
  column dialog. SysHeader32 keeps hit testing and HDS_FULLDRAG.
  High Contrast bypasses the added decorative grip marks.
- The selected column width Edit is 48x16 dialog units rather than
  31x14, has a native client edge, and displays a nearby px unit
  label. ModernUI's shared edit-frame painter can apply one optional
  emphasis property: secondary-text contrast when unfocused and the
  existing focus color when focused. The property is removed during
  WM_NCDESTROY. Other dialog fields keep their prior styling.
- Existing list selection, actual column metadata, ownership,
  native scrollbar and address-row non-overlap code is retained.

## Actual connected Windows 11 x64, 96 DPI evidence

- Release-x64-Unicode product incremental build succeeded after code
  changes, then a separate resource-only incremental build succeeded
  after adding the px label; tests used the final rebuilt binary.
- Both independent test-owned Dark and Light modal GUI runs passed:
  the actual header interior dark-sample ratio was 0.925 in Dark
  and 0.035 in Light, so the header switches visibly with the theme.
  The rendered numeric field width was 84 physical pixels, with the
  client-edge style and emphasis property observed on its HWND.
- Actual mouse drag of the native header's first divider changed
  native column width from 170 px to 192 px in BOTH modes.
  This exercises native hit-testing, not a simulated data setter.
- Clicking a real column row displayed stored width 280 in the
  numeric Edit. Actual physical Ctrl+A and typing changed its
  displayed value to 128 in both modes. Cross-process reading used
  WM_GETTEXT, rather than GetWindowTextW, which does not retrieve
  another process's Edit contents.
- Original modal/address non-overlap remained valid in both modes,
  and a native list scrollbar click advanced the first visible row
  from 0 to 1; both owned runs exited normally. All six original
  user-config file SHA256 values remained unchanged.
- Dedicated source contracts: build/test_ui_column_header_contract.py;
  interactive geometry, header, pointer and numeric field regression:
  build/test_ui02_modal_scrollbar_runtime.py. Test screenshots and
  full logs were kept in local ignored logs, not committed.
- Existing source invariants and MFC native regression were checked
  separately; this change does not import the separate WinUI branch.

## Unverified bounds

The physical 96-DPI test covers this column modal and its current
real-list fixture, not every legacy raw-list dialog. Other real DPI
settings (125%, 150%, 200%), a real Windows High Contrast session,
screen-reader announcements and every keyboard layout have NOT been
validated as part of this patch. No installer or release packaging
test was performed here.
