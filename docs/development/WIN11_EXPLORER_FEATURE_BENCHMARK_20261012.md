# Windows 11 File Explorer feature benchmark — 2026-10-12

## Purpose, reference and evidence limits

Identify feature additions that close practical Windows 11 File Explorer gaps
without discarding flyExplorer's two independent file panes or violating
its bounded Shell/file-safety architecture. This is a **feature and source
comparison**, not a newly conducted on-device pixel or human-interaction
acceptance run.

- flyExplorer source baseline: `main` `de110978b6dd37c8e611f73701e8012954a9b894`
  (documentation update on unchanged WinUI product), reviewed:
  `MainWindow.xaml[.cpp/.h]`, `NavigationSidebar.xaml`, `FileToolbar.xaml`,
  controllers, `CURRENT_STATUS.md`, `PRE_DISTRIBUTION_FUNCTIONAL_GATES.md`,
  and the retained [2026-10-01 visual benchmark](WINUI_EXPLORER_VISUAL_BENCHMARK_20261001.md).
- Explorer reference: Microsoft's published Windows 11 support and 24H2/25H2
  feature descriptions, plus clearly identified August/September 2026
  **Insider/Release Preview** announcements. Preview-channel changes are **not**
  presented as universally shipped to all Windows 11 users.
- Confidence: an existing app control/handler is positive implementation
  evidence; a missing dedicated element in reviewed XAML is a candidate
  **feature-surface gap**, not proof that every underlying OS capability or
  hidden code path is absent. Confirm each candidate with a focused product
  behavior test before claiming a definite defect.
- This document is a **proposed roadmap**, not approval to modify actual user
  files, globally change Windows preferences, install new dependencies,
  publish releases, or bypass required acceptance gates.

## Existing capabilities — do not reimplement

| Area | Current evidence |
| --- | --- |
| Tabs and navigation | Top-level Window Tabs plus independent left/right PaneTabs, Back/Forward/Up, breadcrumb/address bar, session restore, per-tab view/sort; `ARCHITECTURE.md`, `MainWindow.xaml` |
| File views | Details/List/Small/Medium/Large Icons, existing column sort, isolated icons/thumbnails; `FileToolbar.xaml`, prior measured visual benchmark |
| Basic mutations | New Folder, Rename, Copy/Cut/Paste, cross-pane Copy/Move, guarded Recycle, cancellation and progress; `FileToolbar.xaml`, `m21_commands.cpp`, `CURRENT_STATUS.md` |
| Search and filters | Bounded traversal plus eligible Windows Search indexed filename mode; criteria, saved presets, search-scope recent list; styled named file-mask presets; `MainWindow.xaml`, `SearchController` |
| Bookmarks and Shell | Private folder bookmarks, limited isolated native Shell context menu and accepted Properties path, clipboard/drag interoperability in tested scopes; `PRE_DISTRIBUTION_FUNCTIONAL_GATES.md` |
| Accessibility already checked | 96-DPI light/High-Contrast *scoped* pixels, keyboard/UIA filter semantics and real two-beolsik `한글` save. Narrator spoken output and actual 125/150/200% OS DPI **remain open**; `CURRENT_STATUS.md` |

**Do not confuse** `FileDetailController`'s icon/thumbnail enrichment with a
visible Explorer-style Details or Preview pane. The existing sidebar has
fixed Home, This PC and six Known Folder buttons, not a visible expandable
folder `TreeView`. Search-scope history is not an automatic recent-**file**
Home feed.

## Feature candidates

Priority is a project recommendation based on frequency, dual-pane value,
public-API feasibility and safety risk; it is **not** a Microsoft ranking.
Sizes are relative effort estimates (S/M/L), not engineering schedules.
"Unseen" means the dedicated surface was not found in the reviewed current
XAML/handlers and requires focused confirmation before implementation.

### P1 — next practical user-facing additions

| ID | Explorer benchmark and proposed flyExplorer addition | Current comparison | Size | Target boundary |
| --- | --- | --- | --- | --- |
| F01 | **View/Show controls**: show hidden items, show/hide filename extensions, row selection checkboxes; optional Compact spacing, pane-specific and persisted | Sort and five views exist; no file-row selection-checkmark or these dedicated view switches found | M | Pane view state + presentation; never change OS-global Explorer preferences |
| F02 | **Read-only Details pane**: selected item name, type, location, size, dates and limited safe properties; fold/collapse independently per workspace | Existing sort metadata, Shell visuals and an isolated Properties dialog are **not** a visible Details pane | M | FileMetadata/FileDetail request and UI projection; stale-selection and slow-path cancellation |
| F03 | **Preview pane**: opt-in image/text preview for bounded local files with safe placeholders for other formats | File-list thumbnails are present, but no selected-file Preview pane or toggle found | L | New focused preview controller/helper; no arbitrary preview-handler DLL in UI process |
| F04 | **Expandable navigation tree** for This PC drives and filesystem folders, with lazy expansion and explicit active-pane target | Fixed sidebar buttons and navigable PaneTabs exist; no expandable folder tree found | L | Navigation sidebar + ShellNavigationController; provider/UNC boundaries |
| F05 | **Group by** type/date/name/size where a complete sortable model exists, with collapsible section headings | Asc/desc sort exists; group headers/groups not found | M/L | Native file-list grouping/projection; no falsely global grouping across incomplete pages |
| F06 | **Small tab/address gestures**: middle-click folder/breadcrumb opens new *pane-local* tab; test quoted-path/UNC paste and address suggestions | Tabs and editable breadcrumb path exist; dedicated middle-click/quoted-path/suggestion behavior is not evidenced | S/M | ShellNavigationController + Tab/pane identity; keep focus and route tokens correct |

### P2 — distinct follow-up logical units

| ID | Explorer benchmark and proposed flyExplorer addition | Current comparison | Size | Caution |
| --- | --- | --- | --- | --- |
| F07 | **Home dashboard**: user-controlled recently opened files, frequent folders and pinned favorites with section expand/collapse | Home entry, bookmarks and *search scopes* exist; automatic recent-file/frequent-folder dashboard not evidenced | M | Default private or opt-in; clear history and no legacy-profile import |
| F08 | **Archive support**: list/extract ZIP first, then reviewed 7z/TAR support; safe destination/collision controls | No native archive UI/handler found in reviewed app | L | Reject path traversal, symlinks and decompression bombs; bounded worker, provenance/license review |
| F09 | **Open with / Windows Share** explicit commands where supported, with OS ownership and selected-item validation | Standard open, clipboard and limited Shell context popup exist; dedicated full Open-with/Share surfaces not found | M/L | No unrestricted shell extension verb execution; provider/read-only constraints |
| F10 | **Fast contextual action menu**: expose safe built-in commands in a clear menu, enable only valid actions; optional local app-menu visibility customization | Isolated native popup/Properties has bounded scope, not full Windows command compatibility | M | Keep command allowlist and exact owned process boundaries |
| F11 | **Inline, fast search interaction**: suggestion/result dropdown and easy return to the selected file's folder | Strong search engine/presets exist; main search is a multi-row panel and quick-search box | M | Preserve query bounds and cancellation; never silently fall back from indexed mode |
| F12 | **Photo Gallery view** over explicitly chosen local folders, grouped by capture date with image previews | Medium/Large icon views exist; no cross-folder Gallery collection surfaced | L | User-chosen sources, no unattended scan of personal libraries |
| F13 | **New item menu**: at least text-file creation and new folder, with template/provider validation | New Folder exists; generalized New-item/template menu not found | S/M | Validate exact path, collision and no overwrites |
| F14 | **Per-location view defaults** and remembered column/group/display settings | PaneTab view/sort/columns are persisted per session; durable defaults per filesystem location not established | M | Explicit opt-in/private persistence and bounded storage |
| F15 | **Cloud provider state**: available/offline/sync badges, limited provider metadata and cloud Home items | Some virtual Shell and native icon support exists, but broad third-party/cloud parity not accepted | L | Do not fabricate sync state; provider isolation and permission tests |
| F16 | **Additional document thumbnails/previews**, e.g. PDF, only with a reviewed trustworthy OS/provider integration | Current benchmark explicitly describes PDF as icon-only | L | Risk-gated separate provider preview scope; no arbitrary in-process handlers |

### P3 — monitor but do not make blocking parity targets

| ID | Reference | Decision |
| --- | --- | --- |
| F17 | Redesigned **customizable context menu** described by Microsoft on 2026-08-17 as rolling out to **Insiders** | Track the public API/interaction pattern; do not clone private Explorer settings, inject extension DLLs or assume GA |
| F18 | File Explorer **AI actions**, document summarization and image edits on eligible hardware/cloud subscription | Defer; hardware, policy, license, privacy and actual user value must justify any integration |

## F01-A implementation checkpoint — source/Release PASS; GUI/visual OPEN

- **Candidate product/source SHA:** `e147efb6bfe7d4f6176da6c8954a5910ce00a2c8`,
  isolated branch `feat/f01-list-display-20261012`, not merged into `main`.
- The View menu has **selection checkboxes** and **compact Details/List row
  spacing** toggles for the active pane. The state is isolated per
  WindowTab/pane, defaults OFF, and is not saved across process restart.
  Rendering reprojects native-path selection without changing
  Shell enumeration, transfer, filters, sorting or system preferences.
- **Exact-source owned Windows acceptance: PASS for focused Python source
  contract + x64 Release build** in
  [central Remote Shell 38251419251](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38251419251).
  A non-elevated interactive-user test task ran the tests/build, the wrapper
  checked the exact SHA and returned `F01B_SOURCE_AND_RELEASE=PASS`;
  `F01B_OWNED_CLEANUP=PASS`. Earlier failed attempts were SYSTEM Python
  PATH or PowerShell test harness issues and are not product defects.
- **2026-10-13 owned GUI attempt: NOT ACCEPTED (focus environment/harness gate).**
  Candidate code remains the accepted product `e147efb6...`; focused GUI
  harness revisions `cb1b5a1a94b34a5834760a97efe1583bf320e383` and
  `4d79c195c8d08ae97f2dd193fbc39ab01f650781` add a test-owned
  View-menu, checkbox, compact-spacing and selection-retention probe.
  [Remote Shell 38312506917](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38312506917)
  reached its `gui` stage after source checks, Release build and
  test syntax preflight. The GUI worker exited 1 at the existing guarded
  physical-input precondition: `Refusing physical input: foreground belongs
  to a user window`. The bounded log does not establish which F01 assertion,
  if any, ran before this failure. This is **not** product GUI PASS or a
  proven product defect; do not disable the focus guard or rerun unchanged.
  The exact-owned scheduled task and scratch fixture cleanup completed
  (`F01C_OWNED_CLEANUP=PASS`), and the central Remote Shell slot was
  restored idle in control commit `011aef222f5a81886e0eea17d3b1c38913352ae1`.
  Next: read-only inspect the actual unlocked interactive desktop/focus owner;
  change the proven environment or harness precondition before attempting
  a new acceptance run.
- **Still OPEN:** actual new-control functional GUI interaction; keyboard/UIA
  selection semantics and left/right/window-tab rehydration; matched
  before/after product screenshot inspection in light/dark, split/narrow and
  appropriate High Contrast states; actual 125/150/200% DPI and Narrator speech
  if the environment permits. Do not call F01-A UI acceptance PASS or merge
  solely from a successful build.
- **Deferred F01 work:** filesystem hidden-item enumeration and
  filename-extension display semantics, and durable private preference/session
  persistence. These are separate change/verification boundaries.

## F01-B candidate — view-only file extension visibility (2026-10-13)

- Branch: `feat/f01-list-display-20261012` (not merged to `main`).
  **View → 파일 확장명 표시** defaults to checked and is independently
  toggled for each WindowTab/pane. The checkbox state is memory-only.
- Hiding extensions affects only rendered filenames of filesystem *files*.
  Dotfiles, dotted folder names, non-filesystem Shell objects, and trailing
  dots remain intact. `archive.tar.gz` displays `archive.tar`.
  The full original filename remains in automation narration and all
  native path identities, filtering, sorting, selection, rename and transfer.
- The C++ presenter has compile-time guards for representative names,
  Korean Unicode, virtual items and edge cases.
- **Exact product-source contract + Windows x64 Release build: PASS** on
  `c200c512b75c83fd7d674fd0287cd01af0c4a5bf` in
  [central Remote Shell 38315864755](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38315864755).
  Wrapper results: `F01D_EXACT_SOURCE` matches, `F01D_RESULT_STATUS=PASS
  STAGE=complete`, `F01D_SOURCE_AND_RELEASE=PASS`, and
  `F01D_OWNED_CLEANUP=PASS`. The shared Remote Shell request was returned
  idle in control commit `4db7f19f0ad94f4fa1da64838840745933ab3ac6`.
  This is **not** an actual GUI/visual acceptance result.
- **GUI/visual still NOT ACCEPTED.** The focused owned GUI harness now
  includes display-only extension hide/restore, UIA original-filename and
  selection identity checks, plus a capture marker. This follow-up harness
  revision is separate from the exactly built product source above and
  remains unexecuted on the inaccessible foreground desktop.
  The 2026-10-13 read-only Windows focus probe,
  [38315380764](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38315380764),
  saw exactly one Explorer user session but `GetForegroundWindow()==NULL`
  from that interactive-session task. Desktop lock/input availability cannot
  be inferred more precisely; do not circumvent owned foreground guards.
  Owned diagnostic task/files were cleaned and the Remote Shell slot
  returned idle in control commit `1256f38cdffe26b892fac799d4544c21210b500c`.
- F01 hidden-file enumeration and durable preference/session persistence are
  later independent units.

## Recommended execution order

1. **F01 — display options.** Small self-contained visible improvement;
   add source contract + per-pane persistence + keyboard/UIA + actual BEFORE/AFTER
   captures including light/dark, focused row and split widths.
2. **F06 — tab/address gestures.** Low-to-medium cost and frequent navigation
   value; check new-tab ownership, navigation history, middle-click routing and
   Korean/UNC/quoted input without relaxing namespace restrictions.
3. **F02 — Details pane.** Reuse existing metadata/visual lifecycle through a
   small owner rather than adding a new state machine to MainWindow.
   Add slow-UNC/provider timeout, selection-churn and close tests.
4. **F03 — Preview pane.** Start with bounded/test-owned TXT and raster-image
   preview. Provider-supplied, web-downloaded or active content is **not**
   silently executed; test cancellation, large files, theme and DPI.
5. **F05 — group presentation.** Implement only when its backing model is
   complete and sortable; test the 20,000/25,000-entry distinct bounds and
   resident-window paging. Preserve selection and keyboard interaction.
6. **F04 — expandable tree.** Build lazy filesystem navigation after tab
   addressing and selection contracts are stable; support rooted local
   folders first and keep network/provider expansion separate.

Subsequently evaluate F07/F08/F09 according to demand. Each row is a
**separate logical unit**; do not bundle major Shell, archive, refactor and
layout changes into one untestable patch.

## Acceptance rules before marking a feature complete

- Start with **latest main HEAD, recent commits, recent central CI and
  `CURRENT_STATUS.md`**. Reuse valid unchanged build/test evidence.
- Preserve the two-pane/PaneTab ownership, input -> event -> model ->
  projection path, exact route/selection tokens, helper cancellation,
  bounded worker lifetimes and no blocking Shell work on the XAML thread.
- Use project-owned synthetic fixtures; do not manipulate real user folders,
  the global clipboard, Windows default apps or global Explorer preferences
  merely to benchmark a feature.
- For **every composited UI change**, capture actual current-product BEFORE,
  changed-product AFTER under matched OS/build, DPI, theme, window dimensions,
  fixture and state; inspect the pixels and fix regressions. Functional GUI
  and VISUAL ACCEPTANCE are independent. Do not promote source/UIA PASS to
  Narrator speech, High Contrast or OS-scale PASS.
- Central Windows acceptance uses `tngkrwlsmd/personal-control-plane`,
  registered `desktop-a`, trusted exact main SHA and explicit scope.
  `gui` is Release+functional GUI, **not** full Debug or visual QA.
- **Existing open environment gates are prerequisites for final broader
  accessibility certification**, not new feature proposals:
  actual OS 125/150/200% scaling and verified spoken Narrator content/audio.

## Official reference links (verified 2026-10-12)

- [Microsoft Support — File Explorer in Windows](https://support.microsoft.com/ko-kr/windows/experience/fileexplorer/file-explorer-in-windows)
  — Quick Access, view modes, Share, Hidden/extension/checkbox options.
- [Microsoft Support — Screen reader navigation in File Explorer](https://support.microsoft.com/en-us/accessibility/windows/use-a-screen-reader-to-explore-and-navigate-file-explorer-in-windows)
  — tabs, navigation/content/Details pane and F6/keyboard flow.
- [Microsoft Support — September 2023 Windows configuration update](https://support.microsoft.com/en-us/servicing/os/configuration-updates/2023/08/september-26-2023-windows-configuration-update)
  — Gallery, Details pane and native additional archive reading.
- [Microsoft Learn — Windows 11 24H2](https://learn.microsoft.com/en-us/windows/whats-new/whats-new-windows-11-version-24h2)
  — 7z/TAR compression and labeled modern context commands.
- [Microsoft Learn — Windows 11 25H2](https://learn.microsoft.com/en-us/windows/whats-new/whats-new-windows-11-version-25H2)
  — Explorer tabs restored at logon, archive extraction performance,
  optional AI actions (hardware/license-dependent).
- [Windows Insider Blog — 2026-08-17 File Explorer and context-menu improvements](https://blogs.windows.com/windows-insider/2026/08/17/improving-file-explorer-context-menu-faster-simpler-and-more-customizable/)
  — performance, quoting, middle-click, Home, Details and **Insider**
  customization (not assumed generally available).
- [Windows Insider Blog — 2026-09-10 Release Preview](https://blogs.windows.com/windows-insider/2026/09/10/announcing-windows-11-release-preview-builds-26100-9539-26200-9539/)
  — file-preview security behavior, Home section state and Details pane
  refinements; staged rollout, not universal availability.
