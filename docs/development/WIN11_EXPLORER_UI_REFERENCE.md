# Windows 11 Explorer reference policy

Windows 11 File Explorer is flyExplorer's primary reference for shell chrome,
navigation/address/search hierarchy, tabs, file-list state treatment and
general Fluent density.

## Allowed reference sources

1. Actual Windows 11 File Explorer under matched test conditions.
2. Microsoft Windows App design guidance and documented APIs.
3. Windows UI Kit and WinUI 3 Gallery for public component behavior.
4. Public Fluent UI System Icons and system-provided iconography where
   licensing/runtime availability permits.

Private Explorer APIs, undocumented implementation details, binary resource
extraction and private theme strings are not product dependencies.

## flyExplorer-specific departures

flyExplorer intentionally preserves:
- dual independent panes;
- pane-local folder tabs inside each Window Tab;
- denser icon layout where appropriate for dual-pane use;
- bounded isolated Shell-provider behavior rather than unrestricted in-process
  Explorer extension behavior.

Similarity to Explorer is subordinate to reliability, accessibility, dual-pane
usability and documented public APIs.
