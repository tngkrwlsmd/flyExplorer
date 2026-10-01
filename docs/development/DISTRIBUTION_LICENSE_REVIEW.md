# Distribution license review — open checkpoint (2026-09-24; WinUI M2.7 update 2026-10-01)

## WinUI M2.7 current-payload update (2026-10-01)

The canonical product is now the WinUI 3 tree under `app/winui` plus `src/base`; the old MFC dependency inventory below is historical context. A current-tree search found no `GFL`, `XnView`, `libxml2`, `iconv`, `libcurl`, or `MinGW` references in those active source paths, and the verified `out/winui/Release` payload contains no GFL/XnView-named artifact. Therefore the earlier statement that GFL is active applies to the retired MFC product, not the current M2.7 WinUI payload. Keep the GFL notice in `CREDITS` as historical/legal provenance until ownership decides how to curate notices; do not infer new GFL redistribution rights.

Current Release packaging directly carries Windows App SDK 2.5.1 self-contained files and `Microsoft.Web.WebView2.Core` 1.0.3719.77. The WebView2 license requires binary redistributions to reproduce its copyright notice, conditions, and disclaimer in documentation and/or other distribution materials. M2.7 now has an explicit notice path: `packaging/licenses/` tracks the full GPLv3 text plus a hash-based provenance snapshot, and `packaging/licenses/nuget/` retains every license/NOTICE/ThirdPartyNotices file found in the ten package/version sets that supplied hash-matched runtime files, plus the top-level Windows App SDK 2.5.1 terms. The installer additionally places the repository root `LICENSE` and `CREDITS` under its installed `licenses/` directory.

A hash audit of the exact Release runtime before distribution materials accounts for all **305** files: **17** are flyExplorer/generated files and **288** are exact matches to current NuGet package files. The rebuilt setup contains **325** payload files total (305 runtime + 20 distribution materials), and the bounded installed lifecycle verified the license/provenance files are installed and removed with the manifest-bounded product payload while user settings remain preserved. The current setup SHA-256 is `2833B2F6DE2975675FA75F1AB29C927D96DA4AE88BFC2148E89ADA701F90B214`.

The Windows App SDK 2.5.1 license expressly permits redistribution of files binplaced by its NuGet package, subject to its distribution requirements. This is positive evidence for the self-contained runtime strategy. The prior missing-notice packaging gap is now addressed, but public redistribution remains **NOT CLEARED** pending final application/rightsholder review and a legal compatibility/obligation review of the complete current payload. In addition, the application is GPLv3-or-later while the current setup contains object code but no Corresponding Source or source-access offer. GPLv3 section 6 requires an applicable source-delivery mechanism when object code is conveyed. The connected `tngkrwlsmd/flyExplorer` GitHub repository is currently private, so its clone URL is not treated as public source access for installer recipients. `packaging/SOURCE_DISTRIBUTION.md` records this as an explicit release gate and outlines the evidence required before a public binary release. A separate current-Release source audit found 32 compiled repository source files: all trace through Git history to the `YoungMin Jeon` author identity (including the two M2.7-renamed predecessor paths), while the root GPL notice names `Leon Lee` as copyright holder and there is no root CLA/CONTRIBUTING/AUTHORS/COPYRIGHT agreement file. Git authorship does not establish ownership or relicensing authority, so `packaging/RIGHTSHOLDER_REVIEW.md` keeps that relationship and the 2026 contribution grant as explicit human-confirmation gates. Do not treat notice delivery, clean packaging, or successful installer tests as legal approval.

## Source of truth and observed conflict

- Root `LICENSE` identifies the application source as GNU GPL version 3 or
  later. This document does **not** alter the rightsholder's terms.
- The former installer-facing `dist/license.txt` and legacy HTML help
  described the application as freeware while forbidding modification and
  restricting commercial redistribution. These representations contradicted
  the root application's GPL notice. They have been replaced with explicit
  references to the root license, **not** a new license grant.
- The current `CREDITS` still preserves third-party and historical notices.
  Its GFL SDK notice has restrictive redistribution language, but current
  canonical WinUI source and Release payload evidence show no active GFL/XnView
  component. Preserve that provenance until notice ownership is curated; do not
  use the historical GFL text either to block or to grant rights for components
  that are not present in the current payload.

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

## Owner's current use decision (2026-09-24)

The owner currently intends **personal, local use only**, not a public
combined installer or a relicensing effort. Preserve root `LICENSE` and
the vendor notices in `CREDITS` without suggesting that this choice
grants new commercial or public redistribution rights. The GFL SDK remains
an active part of image handling. The old network updater and dedicated
vendored libcurl were removed, so libcurl no longer belongs to the active
bundled-dependency audit. Revisit this section only if distribution plans
change or new third-party components are incorporated.

## Outstanding tasks before public distribution

- Identify current copyright/rightsholders and confirm that the repository
  application license notice applies to all modified application files.
- Obtain current GFL SDK redistribution rights, including the program's
  built-in thumbnail, image-viewer and image-converter usage, and assess
  compatibility of distribution terms for a combined installer.
- Inventory exact bundled libxml2, iconv, MinGW and other third-party
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
