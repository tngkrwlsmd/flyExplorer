# AddressBar drop-down: Dark background and native scrollbar overlay

Date: 2026-09-28. Scope: existing MFC AddressBar on main, NOT
the optional experimental WinUI 3 address field.

## Confirmed cause and minimal change

The nested ComboBoxEx32 uses CBS_OWNERDRAWFIXED. Its native item
drawing uses a bright system background despite the address edit/chrome
dark palette; merely theming the popup list and setting CTLCOLOR did not
correct this. Dark-only item drawing now obtains native CBEM_GETITEM
text/image/indentation and uses the existing ModernUI palette, retaining
the existing ComboBoxEx item identities, Shell images, keyboard handling
and native list. Light mode and OS High Contrast bypass custom painting.

The existing UI-02 click-through layered dark scrollbar compositor is
reused for the native ComboLBox, not substituted for its scrolling HWND.
On this Windows host ComboLBox's early overlay was composed behind the
native popup; a scoped opt-in compositor flag raises ONLY this temporary
popup overlay. It is destroyed on list hide, NC destroy and AddressBar
shutdown. Other list/tree overlays retain their original z-order.

## Actual local verification on connected Windows 11 at 96 DPI

- Release-x64-Unicode x64 product incremental build: PASS.
- Source invariants and native header/address + UI-02 scrollbar source
  regressions, including dedicated popup cleanup contracts: PASS.
- Default native functional tests: 17 passed, 0 failed.
- Test-owned synthetic Dark popup: screenshot interior dark sample ratio
  0.898 (previous bright sample 0.029), Shell icons and indentation intact.
- The real popup scrollbar has a correctly raised dark layered visual;
  observed sampled right-edge dark ratio 0.519, including native thumb.
- Real pointer click on the native scrollbar arrow, through the
  click-through layered popup, moved list top index 11 to 10.
- Closing the popup hid/destroyed the temporary topmost scrollbar visual.
- Test-owned Light popup: dark sample ratio 0.007, no dark overlays;
  native scrollbar pointer click also moved top index 11 to 10.
- Both owned runs exited 0; all six original user config SHA256 values
  remained unchanged. Original untracked main-window.png was preserved.

Screenshot probes and full logs remain local and ignored, not committed.
Tests do NOT establish actual 125/150/200% DPI or OS High Contrast runtime
acceptance. The fix does NOT import any Phase 5 WinUI experimental code.
