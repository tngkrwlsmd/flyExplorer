# Distribution license review — open checkpoint (2026-09-24)

## Source of truth and observed conflict

- Root `LICENSE` identifies the application source as GNU GPL version 3 or
  later. This document does **not** alter the rightsholder's terms.
- The former installer-facing `dist/license.txt` and legacy HTML help
  described the application as freeware while forbidding modification and
  restricting commercial redistribution. These representations contradicted
  the root application's GPL notice. They have been replaced with explicit
  references to the root license, **not** a new license grant.
- The active `CREDITS` contains third-party notices that must be preserved
  where applicable. In particular, the bundled GFL SDK notice describes
  restrictions on use and redistribution, so source-code GPL language alone
  cannot establish that a combined installer may be published.

## Local installer notice changes

The installer license screen uses `dist/license.txt`; the actual installer
also installs `third_party_notices.txt` by copying current `CREDITS`.
The installed HTML help license source links to the application's GPL notice
and clearly distinguishes third-party conditions.

Historical `dist/history.txt` and source-file attributions are retained.
The vendored NSIS `COPYING` and active third-party runtime/source notices
are not removed or rewritten.

## HTML Help source and installer generation

The old tracked `dist/fxfile.chm` was an out-of-date compiled copy and is
no longer authoritative. `build/rebuild_htmlhelp.py --check` validates
source/index/package contracts without modifying the tree, whereas
`--build` needs Microsoft HTML Help Workshop and regenerates the installer
CHM from the tracked help sources. The new landing page separates current
development claims from historical topic pages. A missing compiler aborts
packaging rather than reusing an old binary. Windows CHM compiler/installer
results are NOT TESTED; this change does not resolve third-party rights.

## Outstanding tasks before public distribution

- Identify current copyright/rightsholders and confirm that the repository
  application license notice applies to all modified application files.
- Obtain current GFL SDK redistribution rights, including the program's
  built-in thumbnail, image-viewer and image-converter usage, and assess
  compatibility of distribution terms for a combined installer.
- Inventory exact bundled libxml2, iconv, libcurl, MinGW and other third-party
  binaries; verify versions, original license texts, provenance, applicable
  notice/source obligations and any architecture-specific requirements.
- Review whether the root repository should carry the complete GPL license
  text alongside its current short notice; do not silently invent missing
  copyright permissions or compatibility.
- Run local Windows help generation, x64/product and release/package/installer
  checks in expressly authorized validation scope before release.

**Status:** Documentation conflict corrected for the application; bundled
public redistribution and legal compatibility: NOT VERIFIED. Nothing in this
cleanup asserts the current installer is legally cleared for publication.
