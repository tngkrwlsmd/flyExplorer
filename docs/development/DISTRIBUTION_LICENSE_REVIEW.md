# Distribution and license review — current release gate

This document records engineering evidence, not legal advice.

## Current product

The canonical product is the WinUI 3 application in app/winui plus src/base.
Retired MFC dependency findings are no longer part of the current runtime
inventory unless a component is reintroduced.

Release uses a self-contained Windows App SDK payload and tracked distribution
materials under packaging/licenses/.

## Latest package evidence and current freshness

Remote Windows Task #435 (`37306799266`) accepted package candidate
`00f90c30800fb66f88184211442f6eeb05a950b7`. Its clean Release runtime was
built from candidate `1862231b271e9bb71d5adbf53439fe0d49b60af4`; the
provenance snapshot was generated and checked against that exact build before
the same runtime was packaged and exercised through bounded `/TESTROOT` clean
install, repair, update, rollback and uninstall.

The accepted runtime has 305 files, including 288 exact NuGet byte matches and
17 product/generated files. The setup payload has 326 files. The accepted
runtime manifest SHA-256 is
`40f0f12797c6731f823dd3e438b09fc575a78a54f9962c14fb572e5d70dfdcc5`.
Clean-install, update and rollback launch/shutdown probes all observed normal
process exit.

This closes the stale current-product unsigned package/provenance gate that was
previously represented only by #382. It remains engineering evidence for an
unsigned, test-owned install path; it does not certify production signing,
clean-machine machine-wide deployment, GPL source delivery or rightsholder
clearance. A later fresh Release rebuild is a new byte set and must regenerate
provenance rather than reusing this digest.

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
4. Production signing remains open. The release path still requires signed
   payload/setup verification and a clean-machine Program Files/HKLM
   install/update/rollback lifecycle check.

Tracked license, notice and provenance materials improve engineering evidence
but do not by themselves clear public redistribution.

Current source-of-truth details are maintained in
packaging/SOURCE_DISTRIBUTION.md, packaging/RIGHTSHOLDER_REVIEW.md,
packaging/SIGNING.md and packaging/README.md.

Status: OPEN / NOT CLEARED FOR PUBLIC BINARY DISTRIBUTION.
