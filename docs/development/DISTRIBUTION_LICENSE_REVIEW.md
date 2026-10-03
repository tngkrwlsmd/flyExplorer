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

Public binary redistribution remains not cleared. Current tracked engineering
evidence identifies these separate gates:

1. The root application license is GPLv3-or-later. Object-code conveyance needs
   a GPLv3 section 6 compliant Corresponding Source delivery mechanism.
   The repository is private, so its normal clone access is not treated as
   public recipient source availability.
2. A current release needs an exact binary-to-source identity from the source
   actually packaged, plus clear source-access directions or another selected
   GPLv3 section 6 mechanism. A tracked GPL text alone does not establish
   Corresponding Source availability.
3. Rightsholder/contribution-grant authority still requires human confirmation.
   Git author metadata does not by itself establish copyright ownership,
   assignment, work-for-hire status or relicensing authority. See
   packaging/RIGHTSHOLDER_REVIEW.md.
4. The tracked installer/provenance snapshot predates v7. It must be rebuilt
   from the current Release runtime before it can represent the current product.
5. Production signing remains open. The release path still requires signed
   payload/setup verification and a clean-machine Program Files/HKLM
   install/update/rollback lifecycle check.

Tracked license, notice and provenance materials improve engineering evidence
but do not by themselves clear public redistribution.

Current source-of-truth details are maintained in
packaging/SOURCE_DISTRIBUTION.md, packaging/RIGHTSHOLDER_REVIEW.md,
packaging/SIGNING.md and packaging/README.md.

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.
