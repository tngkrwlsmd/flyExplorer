# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

## Current product

The canonical product is the WinUI 3 application in app/winui plus src/base.
Retired MFC dependency findings are no longer part of the current runtime
inventory unless a component is reintroduced.

Release uses a self-contained Windows App SDK payload and tracked distribution
materials under packaging/licenses/.

## Current package freshness

The latest tracked setup/provenance snapshot was generated on 2026-10-01,
before the v7 Window Tab/session product checkpoint. It remains useful as
historical packaging evidence but is not a package of the current product.
Before any release claim, rebuild from the current Release runtime and rerun
payload provenance/lifecycle checks.

## Open public-distribution gates

Public binary redistribution is not cleared because:
1. The root application license is GPLv3-or-later; a GPLv3 section 6 compliant
   Corresponding Source delivery mechanism must accompany object-code
   conveyance.
2. The repository is private, so repository access is not assumed to satisfy
