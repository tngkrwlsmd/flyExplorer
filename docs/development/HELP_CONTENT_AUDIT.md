# HTML Help content inventory and acceptance plan — 2026-09-24

## Current authority and evidence

- **Current source-backed user guide:** `docs/htmlhelp/Html/current_development.htm`.
  Referenced by `Html/start.htm` and both CHM TOC (`flyExplorer.hhc`)
  and index (`flyExplorer.hhk`). Its source-grounded claims cover active
  Windows 10/11 x64 development scope, current address/pane/tab/basic
  commands and the actual appearance theme-mode setting options.
- **Scope warning:** source-level existence and intentional behavior do not
  demonstrate full end-to-end Windows runtime, accessibility or visual
  acceptance. Do not reproduce a historical screenshot as current.
- **Legacy reference:** the original help still holds 74 HTML source
  pages from before the new current guide. Updated modern/current
  source pages include `Html/start.htm`,
  `Html/flyExplorer/requirements.htm` and `Html/license.htm`.
  Other old pages remain historical unless separately checked.
  The current source page brings the help count to **75 HTML pages**.
- **Removed:** four dead root-level HTML frameset and stylesheet assets
  that referred to a former developer's machine. This did not delete
  `Html/style.css` or the CHM source indexes.

## First-pass remediation of misleading entry points

- Added historical warning banners and current-guide links to
  `Html/ui/ui.htm` (old screenshot), `Html/shortkey.htm`
  (user-customizable, legacy shortcut table), `Html/whatsnews.htm`
  (old release notes), `Html/config/config.htm`, `Html/menu/menu.htm`,
  `Html/function/function.htm` and `Html/flyExplorer/overview.htm`.
- `Html/support.htm` no longer implies an old support website or
  email remains operated. Its historical claims remain recoverable through
  Git history instead of being actively recommended to users.
- The previous about-page warning remains; its historic author text
  is not erased. Past releases' installed `dist/history.txt` are
  retained as historical records rather than recast as current release notes.

## Remaining detailed-topic update work

| Area | Remaining verification requirement | State |
| --- | --- | --- |
| `Html/config/` (31 HTML pages) | Map actual 2.0.4-dev settings tree, names, persistent values and control behavior; repair old screenshots and OS claims | ENTRY PAGE FLAGGED / DETAILED AUDIT OPEN |
| `Html/function/` (24 HTML pages) | Source- and runtime-check file operations, rename, sync, split, image conversion and risk warnings | ENTRY PAGE FLAGGED / DETAILED AUDIT OPEN |
| `Html/menu/` (9 HTML pages) | Compare current localized menus, disabled/enabled behavior and keyboard accelerators | ENTRY PAGE FLAGGED / DETAILED AUDIT OPEN |
| `Html/ui/`, legacy `whatsnews` and `shortkey` | Verify real x64 screen, default/custom shortcuts and split-pane/tab navigation | HISTORICAL LABEL ADDED / WINDOWS RETEST OPEN |
| `Html/flyExplorer/` overview/about | Confirm current features and replace stale third-party contact or compatibility references | PARTIAL LABEL / DETAILED AUDIT OPEN |
| `Html/support.htm` and `Html/license.htm` | Do not invent support SLA or additional license rights; complete third-party distribution review | SUPPORT REPHRASED / LEGAL VERIFICATION OPEN |

## Acceptance criteria before claiming fully current help

1. Run `python build/rebuild_htmlhelp.py --check` from a current checkout,
   then regenerate `fxfile.chm` using an installed Windows HTML Help
   Workshop `hhc.exe`. Inspect linked topics, Korean rendering and
   back/forward/index/keyword navigation in the actual CHM.
2. Capture screenshots or equivalent runtime evidence of the exact x64
   revision: current pane/tab, toolbar/menu, settings System/Light/Dark,
   Windows High Contrast and shortcuts/settings effects.
3. Compare every detailed legacy help page to the observed UI/source
   and replace descriptions/screen captures only where verified.
4. Validate the packaged help file and installer without altering
   unrelated product sources; do not run GitHub Actions without separate
   per-run user authorization. Public redistribution remains gated by
   `DISTRIBUTION_LICENSE_REVIEW.md`.

**Verification status:** first-pass repository source/topic consistency
reviewed; full detailed-page verification, Windows compiler, installed
help browsing and UI visual acceptance: NOT TESTED.

## Retired automatic update (2026-09-24)

Automatic update checking and its download/status controls are intentionally
absent from the current product. Detailed historical screenshots/settings
pages that mention the old updater are reference-only and must not
be presented as existing features. No new network updater is planned by
this work unit. All other outstanding per-page runtime checks above remain
open.
